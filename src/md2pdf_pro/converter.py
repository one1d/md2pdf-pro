"""Pandoc conversion engine for MD2PDF Pro.

This module provides async wrapper for Pandoc PDF conversion,
including parameter building, subprocess management, and error handling.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from md2pdf_pro.config import FontConfig, PandocConfig, PdfEngine

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a Pandoc conversion."""

    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    error_code: Optional[int] = None
    duration_ms: float = 0.0


class PandocError(Exception):
    """Base exception for Pandoc errors."""

    pass


class PandocNotFoundError(PandocError):
    """Raised when Pandoc command is not found."""

    pass


class PandocConversionError(PandocError):
    """Raised when Pandoc conversion fails."""

    pass


class PandocTimeoutError(PandocError):
    """Raised when Pandoc conversion times out."""

    pass


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
        font_config: Optional[FontConfig] = None,
    ):
        """Initialize Pandoc engine.

        Args:
            config: Pandoc configuration
            font_config: Optional font configuration
        """
        self.config = config
        self.font_config = font_config or FontConfig()
        self._pandoc_available: Optional[bool] = None
        self._pandoc_version: Optional[str] = None

    @property
    def version(self) -> Optional[str]:
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
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> ConversionResult:
        """Convert Markdown to PDF using Pandoc.

        Args:
            input_file: Input Markdown file path
            output_file: Output PDF file path
            metadata: Optional metadata dictionary
            timeout: Optional timeout in seconds

        Returns:
            ConversionResult with success status and details
        """
        if not self.is_available():
            raise PandocNotFoundError(
                "pandoc command not found. Please install Pandoc: "
                "https://pandoc.org/installing.html"
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
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration = (asyncio.get_event_loop().time() - start_time) * 1000
                return ConversionResult(
                    success=False,
                    error="Conversion timed out",
                    error_code=-1,
                    duration_ms=duration,
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
                return ConversionResult(
                    success=False,
                    error=error_msg,
                    error_code=process.returncode,
                    duration_ms=duration,
                )

        except FileNotFoundError:
            return ConversionResult(
                success=False,
                error="pandoc command not found",
                error_code=-2,
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                error=str(e),
                error_code=-99,
            )

    def _build_args(
        self,
        input_file: Path,
        output_file: Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Build Pandoc command arguments.

        Args:
            input_file: Input file path
            output_file: Output file path
            metadata: Optional metadata

        Returns:
            List of command arguments
        """
        args: List[str] = [
            str(input_file),
            "-o", str(output_file),
            "--standalone" if self.config.standalone else "",
            f"--pdf-engine={self.config.pdf_engine.value}",
            f"--highlight-style={self.config.highlight_style}",
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

    def _get_font_args(self) -> List[str]:
        """Get font-related Pandoc arguments.

        Returns:
            List of font argument pairs
        """
        args: List[str] = []

        # CJK main font
        args.extend([
            "-V", f"CJKmainfont={self.font_config.cjk_primary}",
        ])

        # Latin main font
        args.extend([
            "-V", f"mainfont={self.font_config.latin_primary}",
        ])

        # Monospace font
        args.extend([
            "-V", f"monofont={self.font_config.monospace}",
        ])

        # Geometry (page margins)
        args.extend([
            "-V", f"geometry:margin={self.font_config.geometry_margin}",
        ])

        return args


def check_dependencies() -> Dict[str, bool]:
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
