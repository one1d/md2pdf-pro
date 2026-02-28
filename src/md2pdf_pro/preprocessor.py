"""Mermaid diagram preprocessing for MD2PDF Pro.

This module handles detection, rendering, and caching of Mermaid diagrams
in Markdown files, converting them to PDF vector graphics.
"""

from __future__ import annotations

import hashlib
import logging
import re
import subprocess
import tempfile
from pathlib import Path

from md2pdf_pro.config import MermaidConfig, MermaidFormat, MermaidTheme

logger = logging.getLogger(__name__)

# Regex pattern for Mermaid code blocks
MERMAID_PATTERN = re.compile(
    r"```mermaid\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

# Supported diagram types
SUPPORTED_DIAGRAMS = {
    "flowchart",
    "graph",
    "sequencediagram",
    "classdiagram",
    "statediagram",
    "erdiagram",
    "gantt",
    "pie",
    "mindmap",
    "journey",
    "gitgraph",
    "requirement",
}


class MermaidError(Exception):
    """Base exception for Mermaid processing errors."""

    pass


class MermaidNotFoundError(MermaidError):
    """Raised when mmdc command is not found."""

    pass


class MermaidRenderError(MermaidError):
    """Raised when Mermaid rendering fails."""

    pass


class MermaidPreprocessor:
    """Mermaid diagram preprocessor.

    This class handles:
    - Detection of Mermaid code blocks in Markdown
    - Rendering diagrams to PDF/SVG using mmdc
    - Caching rendered diagrams to avoid re-rendering
    - Replacing code blocks with image references
    """

    def __init__(self, config: MermaidConfig):
        """Initialize Mermaid preprocessor.

        Args:
            config: Mermaid configuration
        """
        self.config = config
        self._output_dir = config.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._mmdc_available: bool | None = None

    @property
    def output_dir(self) -> Path:
        """Get output directory for rendered diagrams."""
        return self._output_dir

    def is_available(self) -> bool:
        """Check if mmdc command is available.

        Returns:
            True if mmdc is installed and working
        """
        if self._mmdc_available is None:
            try:
                result = subprocess.run(
                    ["mmdc", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._mmdc_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._mmdc_available = False

        return self._mmdc_available

    async def process(self, content: str, file_id: str) -> tuple[str, list[Path]]:
        """Process Mermaid code blocks in Markdown content.

        Args:
            content: Markdown content
            file_id: Unique identifier for the file

        Returns:
            Tuple of (processed content, list of generated diagram files)
        """
        matches = list(MERMAID_PATTERN.finditer(content))

        if not matches:
            return content, []

        generated_files: list[Path] = []
        new_content = content
        offset = 0

        for idx, match in enumerate(matches):
            mermaid_code = match.group(1)
            start_pos = match.start()
            end_pos = match.end()

            # Calculate content hash for caching
            code_hash = compute_hash(mermaid_code)

            # Determine output file path
            output_file = self._output_dir / f"{file_id}_{idx}_{code_hash}.{self.config.format.value}"

            # Render or get cached
            try:
                if not output_file.exists():
                    await self._render_mermaid(mermaid_code, output_file)

                generated_files.append(output_file)

                # Replace code block with image reference
                if self.config.format == MermaidFormat.PDF:
                    # For PDF, use LaTeX includegraphics or markdown image
                    image_ref = f"\\includegraphics[width={{\\linewidth}}]{{{output_file}}}\n\n"
                else:
                    image_ref = f"![]({output_file})\n"

                # Apply offset for next replacement
                new_content = (
                    new_content[: start_pos + offset]
                    + image_ref
                    + new_content[end_pos + offset :]
                )
                offset += len(image_ref) - (end_pos - start_pos)

            except MermaidError as e:
                logger.warning(f"Failed to render Mermaid diagram {idx}: {e}")
                # Keep original code block on error

        return new_content, generated_files

    async def _render_mermaid(
        self, code: str, output_path: Path
    ) -> None:
        """Render Mermaid code to PDF/SVG.

        Args:
            code: Mermaid diagram code
            output_path: Output file path
        """
        if not self.is_available():
            raise MermaidNotFoundError(
                "mmdc command not found. Please install mermaid-cli: "
                "npm install -g @mermaid-js/mermaid-cli"
            )

        # Create temporary input file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False, encoding="utf-8"
        ) as input_file:
            input_file.write(code)
            input_path = Path(input_file.name)

        try:
            # Build command
            cmd = self._build_command(input_path, output_path)

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise MermaidRenderError(f"Mermaid rendering failed: {error_msg}")

            if not output_path.exists():
                raise MermaidRenderError(f"Output file not created: {output_path}")

        finally:
            # Clean up input file
            input_path.unlink(missing_ok=True)

    def _build_command(
        self, input_path: Path, output_path: Path
    ) -> list[str]:
        """Build mmdc command arguments.

        Args:
            input_path: Input Mermaid file path
            output_path: Output file path

        Returns:
            Command argument list
        """
        cmd = [
            "mmdc",
            "-i", str(input_path),
            "-o", str(output_path),
            "-w", str(self.config.width),
            "-b", self.config.background,
        ]

        # Add theme if not default
        if self.config.theme != MermaidTheme.DEFAULT:
            cmd.extend(["-t", self.config.theme.value])

        # Add format-specific options
        if self.config.format == MermaidFormat.PDF:
            cmd.append("--pdfFit")

        return cmd

    def clear_cache(self) -> int:
        """Clear cached diagram files.

        Returns:
            Number of files deleted
        """
        count = 0
        if self._output_dir.exists():
            for file in self._output_dir.iterdir():
                if file.is_file():
                    file.unlink()
                    count += 1
        return count


def compute_hash(content: str) -> str:
    """Compute hash of content for caching.

    Args:
        content: Content to hash

    Returns:
        Hex digest of hash (first 16 characters)
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def diagram_line_matches(line: str, diagram_type: str) -> bool:
    """Check if first line matches diagram type.

    Args:
        line: First line of Mermaid code
        diagram_type: Diagram type to check

    Returns:
        True if line matches
    """
    # Handle aliases
    if diagram_type in ("flowchart", "graph"):
        return "flowchart" in line or line.startswith("graph")
    if diagram_type == "sequencediagram":
        return "sequencediagram" in line
    if diagram_type == "classdiagram":
        return "classdiagram" in line
    if diagram_type == "statediagram":
        return "statediagram" in line or "state" in line

    return diagram_type in line
