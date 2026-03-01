"""Unit tests for config module."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from md2pdf_pro.config import (
    FontConfig,
    LoggingConfig,
    LogLevel,
    MermaidConfig,
    MermaidFormat,
    MermaidTheme,
    OutputConfig,
    PandocConfig,
    PdfEngine,
    ProcessingConfig,
    ProjectConfig,
    get_default_config_path,
    init_config,
)


def test_project_config_defaults():
    """Test ProjectConfig default values."""
    config = ProjectConfig()

    assert config.version == "1.0.1"
    assert config.mermaid.theme == MermaidTheme.DEFAULT
    assert config.mermaid.format == MermaidFormat.PDF
    assert config.mermaid.width == 1200
    assert config.pandoc.pdf_engine == PdfEngine.TECTONIC
    assert config.processing.max_workers == 8
    assert config.output.output_dir == Path("./output")
    assert config.logging.level == LogLevel.INFO
    assert config.input_patterns == ["*.md", "*.markdown"]


def test_project_config_from_yaml(temp_dir):
    """Test loading configuration from YAML file."""
    config_path = temp_dir / "config.yaml"
    config_content = """
version: 1.0.0
mermaid:
  theme: dark
  format: svg
  width: 1000
pandoc:
  pdf_engine: xelatex
  highlight_style: monokai
processing:
  max_workers: 4
output:
  output_dir: ./build
"""
    config_path.write_text(config_content, encoding="utf-8")

    config = ProjectConfig.from_yaml(config_path)

    assert config.version == "1.0.0"
    assert config.mermaid.theme == MermaidTheme.DARK
    assert config.mermaid.format == MermaidFormat.SVG
    assert config.mermaid.width == 1000
    assert config.pandoc.pdf_engine == PdfEngine.XELATEX
    assert config.pandoc.highlight_style == "monokai"
    assert config.processing.max_workers == 4
    assert config.output.output_dir == Path("./build")


def test_project_config_to_yaml(temp_dir):
    """Test saving configuration to YAML file."""
    config = ProjectConfig()
    config.version = "1.0.2"
    config.mermaid.theme = MermaidTheme.FOREST
    config.processing.max_workers = 6

    config_path = temp_dir / "output_config.yaml"
    config.to_yaml(config_path)

    # Read back and verify
    loaded_config = ProjectConfig.from_yaml(config_path)
    assert loaded_config.version == "1.0.2"
    assert loaded_config.mermaid.theme == MermaidTheme.FOREST
    assert loaded_config.processing.max_workers == 6


def test_project_config_from_env():
    """Test loading configuration from environment variables."""
    # Set environment variables
    os.environ["MD2PDF_PDF_ENGINE"] = "lualatex"
    os.environ["MD2PDF_MAX_WORKERS"] = "12"
    os.environ["MD2PDF_OUTPUT_DIR"] = "./env_output"
    os.environ["MD2PDF_LOG_LEVEL"] = "DEBUG"

    try:
        config = ProjectConfig.from_env()
        assert config.pandoc.pdf_engine == PdfEngine.LUALATEX
        assert config.processing.max_workers == 12
        assert config.output.output_dir == Path("./env_output")
        assert config.logging.level == LogLevel.DEBUG
    finally:
        # Clean up
        for key in [
            "MD2PDF_PDF_ENGINE",
            "MD2PDF_MAX_WORKERS",
            "MD2PDF_OUTPUT_DIR",
            "MD2PDF_LOG_LEVEL",
        ]:
            if key in os.environ:
                del os.environ[key]


def test_project_config_merge_with_args():
    """Test merging configuration with command-line arguments."""
    config = ProjectConfig()
    args = {
        "pdf_engine": "xelatex",
        "max_workers": 10,
        "output_dir": "./args_output",
        "template": "./template.tex",
        "theme": "forest",
    }

    merged_config = config.merge_with_args(args)

    assert merged_config.pandoc.pdf_engine == PdfEngine.XELATEX
    assert merged_config.processing.max_workers == 10
    assert merged_config.output.output_dir == Path("./args_output")
    assert merged_config.pandoc.template == Path("./template.tex")
    assert merged_config.mermaid.theme == MermaidTheme.FOREST


def test_get_default_config_path():
    """Test get_default_config_path function."""
    path = get_default_config_path()
    assert isinstance(path, Path)
    assert path.name in ["md2pdf.yaml", ".md2pdf.yaml"]


def test_init_config_with_existing_file(temp_dir):
    """Test init_config with existing config file."""
    config_path = temp_dir / "md2pdf.yaml"
    config_content = """
version: 1.0.0
mermaid:
  theme: dark
"""
    config_path.write_text(config_content, encoding="utf-8")

    config = init_config(config_path)
    assert config.version == "1.0.0"
    assert config.mermaid.theme == MermaidTheme.DARK


def test_init_config_with_new_file(temp_dir):
    """Test init_config with new config file."""
    config_path = temp_dir / "new_config.yaml"
    config = init_config(config_path)

    assert config.version == "1.0.1"
    assert config_path.exists()


def test_init_config_without_path():
    """Test init_config without path."""
    config = init_config()
    assert isinstance(config, ProjectConfig)
    assert config.version == "1.0.1"


def test_config_validation():
    """Test configuration validation."""
    # Test invalid theme
    with pytest.raises(ValueError):
        MermaidConfig(theme="invalid_theme")

    # Test invalid PDF engine
    with pytest.raises(ValueError):
        PandocConfig(pdf_engine="invalid_engine")

    # Test invalid log level
    with pytest.raises(ValueError):
        LoggingConfig(level="invalid_level")


def test_config_edge_cases():
    """Test configuration edge cases."""
    # Test minimal config
    minimal_config = ProjectConfig(
        version="1.0.0",
        mermaid=MermaidConfig(),
        pandoc=PandocConfig(),
        processing=ProcessingConfig(),
        font=FontConfig(),
        output=OutputConfig(),
        logging=LoggingConfig(),
    )
    assert minimal_config.version == "1.0.0"

    # Test with None values
    config_with_none = ProjectConfig(
        pandoc=PandocConfig(template=None),
        logging=LoggingConfig(file=None),
    )
    assert config_with_none.pandoc.template is None
    assert config_with_none.logging.file is None


def test_font_config_defaults():
    """Test FontConfig default values."""
    font_config = FontConfig()
    assert font_config.cjk_primary == "PingFang SC"
    assert "STHeiti" in font_config.cjk_fallback
    assert font_config.latin_primary == "Times New Roman"
    assert font_config.monospace == "Menlo"
    assert font_config.geometry_margin == "2.5cm"


def test_processing_config_defaults():
    """Test ProcessingConfig default values."""
    processing_config = ProcessingConfig()
    assert processing_config.max_workers == 8
    assert processing_config.batch_size == 50
    assert processing_config.timeout == 300
    assert processing_config.retry_attempts == 3
    assert processing_config.retry_backoff == 2.0
    assert processing_config.cpu_threshold == 80
    assert processing_config.memory_limit == 4096
