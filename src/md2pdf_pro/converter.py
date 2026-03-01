"""Pandoc conversion engine for MD2PDF Pro.

This module provides async wrapper for Pandoc PDF conversion,
including parameter building, subprocess management, and error handling.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from md2pdf_pro.config import (
    FontConfig,
    PandocConfig,
    PdfCompression,
    PdfMetadataConfig,
    WatermarkConfig,
)
from md2pdf_pro.errors import ConversionError, DependencyError, ErrorCode

# Error class aliases for backwards compatibility
PandocConversionError = ConversionError
PandocError = ConversionError
PandocNotFoundError = DependencyError
PandocTimeoutError = ConversionError

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a Pandoc conversion."""

    success: bool
    output_path: Path | None = None
    error: str | None = None
    error_code: int | None = None
    duration_ms: float = 0.0


class PandocEngine:
    """Async Pandoc PDF conversion engine.

    This class provides:
    - Async subprocess execution
    - Configurable conversion parameters
    - Timeout handling
    - Error capture and reporting
    """

    def __init__(
        self,
        config: PandocConfig,
        font_config: FontConfig | None = None,
    ):
        """Initialize Pandoc engine.

        Args:
            config: Pandoc configuration
            font_config: Optional font configuration
        """
        self.config = config
        self.font_config = font_config or FontConfig()
        self._pandoc_available: bool | None = None
        self._pandoc_version: str | None = None

    @property
    def version(self) -> str | None:
        """Get Pandoc version."""
        if self._pandoc_version is None:
            try:
                result = subprocess.run(
                    ["pandoc", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    self._pandoc_version = result.stdout.split("\n")[0].strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        return self._pandoc_version

    def is_available(self) -> bool:
        """Check if Pandoc is available.

        Returns:
            True if Pandoc is installed
        """
        if self._pandoc_available is None:
            try:
                result = subprocess.run(
                    ["pandoc", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._pandoc_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._pandoc_available = False
        return self._pandoc_available

    async def convert(
        self,
        input_file: Path,
        output_file: Path,
        metadata: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> ConversionResult:
        """Convert Markdown to PDF using Pandoc.

        Args:
            input_file: Input Markdown file path
            output_file: Output PDF file path
            metadata: Optional metadata dictionary
            timeout: Optional timeout in seconds

        Returns:
            ConversionResult with success status and details

        Raises:
            DependencyError: If pandoc is not found
            ConversionError: If conversion fails
        """
        if not self.is_available():
            raise DependencyError(
                "pandoc command not found. Please install Pandoc: "
                "https://pandoc.org/installing.html",
                ErrorCode.DEPENDENCY_MISSING,
                {"dependency": "pandoc"},
            )

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Build command arguments
        args = self._build_args(input_file, output_file, metadata)

        # Set timeout
        timeout = timeout or self.config.timeout or 300

        # Execute asynchronously
        start_time = asyncio.get_event_loop().time()

        try:
            process = await asyncio.create_subprocess_exec(
                "pandoc",
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                raise ConversionError(
                    "Conversion timed out",
                    ErrorCode.CONVERSION_TIMEOUT,
                    {
                        "input_file": str(input_file),
                        "output_file": str(output_file),
                        "timeout": timeout,
                    },
                )

            duration = (asyncio.get_event_loop().time() - start_time) * 1000

            if process.returncode == 0:
                return ConversionResult(
                    success=True,
                    output_path=output_file,
                    duration_ms=duration,
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise ConversionError(
                    f"Pandoc conversion failed: {error_msg}",
                    ErrorCode.CONVERSION_FAILED,
                    {
                        "input_file": str(input_file),
                        "output_file": str(output_file),
                        "error_code": process.returncode,
                    },
                )

        except FileNotFoundError:
            raise DependencyError(
                "pandoc command not found",
                ErrorCode.DEPENDENCY_MISSING,
                {"dependency": "pandoc"},
            )
        except (DependencyError, ConversionError):
            raise
        except Exception as e:
            raise ConversionError(
                f"An error occurred during conversion: {str(e)}",
                ErrorCode.CONVERSION_FAILED,
                {
                    "input_file": str(input_file),
                    "output_file": str(output_file),
                },
                e,
            )

    def _build_args(
        self,
        input_file: Path,
        output_file: Path,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Build Pandoc command arguments.

        Args:
            input_file: Input file path
            output_file: Output file path
            metadata: Optional metadata

        Returns:
            List of command arguments
        """
        args: list[str] = [
            str(input_file),
            "-o",
            str(output_file),
            "--standalone" if self.config.standalone else "",
            f"--pdf-engine={self.config.pdf_engine.value}",
            f"--highlight-style={self.config.highlight_style}",
            f"-fmarkdown{self.config.extensions}",
        ]

        # Add template if specified
        if self.config.template:
            args.extend(["--template", str(self.config.template)])

        # Table of contents
        if self.config.toc:
            args.extend(["--toc", f"--toc-depth={self.config.toc_depth}"])

        # Math engine
        if self.config.math_engine.value == "mathspec":
            args.extend(["-V", "mathspec=true"])

        # Add font configuration
        args.extend(self._get_font_args())

        # Add extra variables
        for key, value in self.config.extra_vars.items():
            args.extend(["-V", f"{key}={value}"])

        # Add metadata
        if metadata:
            for key, value in metadata.items():
                args.extend(["-M", f"{key}={value}"])

        # Filter out empty strings
        args = [arg for arg in args if arg]

        return args

    def _get_font_args(self) -> list[str]:
        """Get font-related Pandoc arguments.

        Returns:
            List of font argument pairs
        """
        args: list[str] = []

        # CJK main font
        args.extend(
            [
                "-V",
                f"CJKmainfont={self.font_config.cjk_primary}",
            ]
        )

        # Latin main font
        args.extend(
            [
                "-V",
                f"mainfont={self.font_config.latin_primary}",
            ]
        )

        # Monospace font
        args.extend(
            [
                "-V",
                f"monofont={self.font_config.monospace}",
            ]
        )

        # Geometry (page margins)
        args.extend(
            [
                "-V",
                f"geometry:margin={self.font_config.geometry_margin}",
            ]
        )

        return args


def check_dependencies() -> dict[str, bool]:
    """Check if required dependencies are available.

    Returns:
        Dictionary mapping dependency name to availability
    """
    deps = {
        "pandoc": False,
        "tectonic": False,
        "xelatex": False,
    }

    # Check Pandoc
    try:
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            timeout=5,
        )
        deps["pandoc"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check PDF engines
    for engine in ["tectonic", "xelatex"]:
        try:
            result = subprocess.run(
                [engine, "--version"],
                capture_output=True,
                timeout=5,
            )
            deps[engine] = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return deps


def optimize_pdf(
    input_path: Path,
    output_path: Path,
    compression: PdfCompression = PdfCompression.SCREEN,
    metadata: PdfMetadataConfig | None = None,
    watermark: WatermarkConfig | None = None,
) -> bool:
    """Optimize PDF using Ghostscript.

    Returns True if optimization was applied, False if gs not available.
    """
    # Check if ghostscript is available
    try:
        result = subprocess.run(
            ["gs", "--version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False
    except FileNotFoundError:
        return False

    # Build gs command
    args = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.5",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
    ]

    # Compression settings
    if compression == PdfCompression.NONE:
        args.extend(["-dPDFSETTINGS=/default"])
    elif compression == PdfCompression.SCREEN:
        args.extend(["-dPDFSETTINGS=/screen"])
    elif compression == PdfCompression.EBOOK:
        args.extend(["-dPDFSETTINGS=/ebook"])
    elif compression == PdfCompression.PRINT:
        args.extend(["-dPDFSETTINGS=/printer"])
    elif compression == PdfCompression.PREPRESS:
        args.extend(["-dPDFSETTINGS=/prepress"])

    args.append(str(input_path))

    try:
        result = subprocess.run(args, capture_output=True, timeout=120)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
