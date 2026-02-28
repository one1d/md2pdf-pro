"""Configuration management for MD2PDF Pro.

This module provides Pydantic-based configuration models for managing
application settings, including Mermaid rendering, Pandoc conversion,
processing options, and output configuration.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class MermaidTheme(str, Enum):
    """Mermaid diagram themes."""

    DEFAULT = "default"
    DARK = "dark"
    FOREST = "forest"
    NEUTRAL = "neutral"


class MermaidFormat(str, Enum):
    """Mermaid output format."""

    PDF = "pdf"
    SVG = "svg"


class MathEngine(str, Enum):
    """LaTeX math rendering engine."""

    MATHSPEC = "mathspec"
    KATEX = "katex"
    MATHJAX = "mathjax"


class PdfEngine(str, Enum):
    """PDF generation engine."""

    TECTONIC = "tectonic"
    XELATEX = "xelatex"
    LUALATEX = "lualatex"


class LogLevel(str, Enum):
    """Logging level."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class MermaidConfig(BaseModel):
    """Mermaid rendering configuration."""

    theme: MermaidTheme = Field(default=MermaidTheme.DEFAULT)
    format: MermaidFormat = Field(default=MermaidFormat.PDF)
    width: int = Field(default=1200)
    background: str = Field(default="white")
    cache_ttl: int = Field(default=86400)  # 24 hours
    output_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "md2pdf" / "mermaid")


class PandocConfig(BaseModel):
    """Pandoc conversion configuration."""

    pdf_engine: PdfEngine = Field(default=PdfEngine.TECTONIC)
    template: Path | None = None
    highlight_style: str = Field(default="tango")
    math_engine: MathEngine = Field(default=MathEngine.MATHSPEC)
    extra_vars: dict[str, Any] = Field(default_factory=dict)
    standalone: bool = True
    toc: bool = False
    toc_depth: int = Field(default=3)
    timeout: int = Field(default=300)  # seconds


class ProcessingConfig(BaseModel):
    """Processing configuration."""

    max_workers: int = Field(default=8)
    batch_size: int = Field(default=50)
    timeout: int = Field(default=300)  # seconds
    retry_attempts: int = Field(default=3)
    retry_backoff: float = Field(default=2.0)
    cpu_threshold: int = Field(default=80)  # percentage
    memory_limit: int = Field(default=4096)  # MB


class FontConfig(BaseModel):
    """Font configuration for PDF output."""

    cjk_primary: str = Field(default="PingFang SC")
    cjk_fallback: list[str] = Field(
        default_factory=lambda: [
            "STHeiti",
            "Noto Sans CJK SC",
            "WenQuanYi Micro Hei",
            "Microsoft YaHei",
        ]
    )
    latin_primary: str = Field(default="Times New Roman")
    monospace: str = Field(default="Menlo")
    geometry_margin: str = Field(default="2.5cm")


class OutputConfig(BaseModel):
    """Output configuration."""

    output_dir: Path = Field(default_factory=lambda: Path("./output"))
    temp_dir: Path = Field(default_factory=lambda: Path("/tmp/md2pdf"))
    naming_pattern: str = Field(default="{stem}.pdf")
    preserve_temp: bool = Field(default=False)
    optimize_pdf: bool = Field(default=True)
    create_subdirs: bool = Field(default=False)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(
        default="[%(levelname)s] %(message)s"
    )
    file: Path | None = None
    rotation: str = Field(default="daily")  # daily, size, none
    max_bytes: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=7)


class ProjectConfig(BaseModel):
    """Main project configuration."""

    version: str = Field(default="1.0.1")

    # Sub-configurations
    mermaid: MermaidConfig = Field(default_factory=MermaidConfig)
    pandoc: PandocConfig = Field(default_factory=PandocConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    font: FontConfig = Field(default_factory=FontConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # File patterns
    input_patterns: list[str] = Field(default_factory=lambda: ["*.md", "*.markdown"])
    ignore_patterns: list[str] = Field(
        default_factory=lambda: [
            ".*",
            "_*",
            "node_modules",
            ".git",
            "__pycache__",
        ]
    )

    class Config:
        """Pydantic config."""

        validate_assignment = True
        extra = "forbid"

    @classmethod
    def from_yaml(cls, path: Path | str) -> ProjectConfig:
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            ProjectConfig instance
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)

    def to_yaml(self, path: Path | str) -> None:
        """Save configuration to YAML file.

        Args:
            path: Path to save YAML configuration
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict, excluding None values
        data = self.model_dump(exclude_none=True, mode="json")

        with open(path, encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_env(cls) -> ProjectConfig:
        """Load configuration from environment variables.

        Environment variables take precedence over defaults.

        Returns:
            ProjectConfig instance
        """
        config = cls()

        # Override from environment
        if os.getenv("MD2PDF_PDF_ENGINE"):
            config.pandoc.pdf_engine = PdfEngine(os.getenv("MD2PDF_PDF_ENGINE"))

        if os.getenv("MD2PDF_MAX_WORKERS"):
            config.processing.max_workers = int(os.getenv("MD2PDF_MAX_WORKERS"))

        if os.getenv("MD2PDF_OUTPUT_DIR"):
            config.output.output_dir = Path(os.getenv("MD2PDF_OUTPUT_DIR"))

        if os.getenv("MD2PDF_LOG_LEVEL"):
            config.logging.level = LogLevel(os.getenv("MD2PDF_LOG_LEVEL"))

        return config

    def merge_with_args(self, args: dict[str, Any]) -> ProjectConfig:
        """Merge configuration with command-line arguments.

        Args:
            args: Dictionary of command-line arguments

        Returns:
            New ProjectConfig with merged settings
        """
        config = self.model_copy(deep=True)

        # Override with args
        if "pdf_engine" in args and args["pdf_engine"]:
            config.pandoc.pdf_engine = PdfEngine(args["pdf_engine"])

        if "max_workers" in args and args["max_workers"]:
            config.processing.max_workers = args["max_workers"]

        if "output_dir" in args and args["output_dir"]:
            config.output.output_dir = Path(args["output_dir"])

        if "template" in args and args["template"]:
            config.pandoc.template = Path(args["template"])

        if "theme" in args and args["theme"]:
            config.mermaid.theme = MermaidTheme(args["theme"])

        return config


def get_default_config_path() -> Path:
    """Get default configuration file path.

    Returns:
        Path to default config file
    """
    # Check multiple locations
    candidates = [
        Path.cwd() / "md2pdf.yaml",
        Path.cwd() / ".md2pdf.yaml",
        Path.home() / ".md2pdf" / "config.yaml",
    ]

    for path in candidates:
        if path.exists():
            return path

    return candidates[0]


def init_config(path: Path | str | None = None) -> ProjectConfig:
    """Initialize configuration.

    Args:
        path: Optional path to config file

    Returns:
        ProjectConfig instance
    """
    if path:
        path = Path(path)
        if path.exists():
            return ProjectConfig.from_yaml(path)

    # Create default config
    config = ProjectConfig()

    if path:
        config.to_yaml(path)

    return config
