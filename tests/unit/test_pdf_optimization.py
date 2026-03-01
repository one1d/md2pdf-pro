"""Unit tests for PDF optimization features."""

from __future__ import annotations

import pytest

from md2pdf_pro.config import (
    PdfCompression,
    PdfMetadataConfig,
    PdfOptimizationConfig,
    WatermarkConfig,
    WatermarkPosition,
)


class TestPdfCompression:
    """Tests for PdfCompression enum."""

    def test_compression_values(self):
        """Test compression level values."""
        assert PdfCompression.NONE.value == "none"
        assert PdfCompression.WEB.value == "web"
        assert PdfCompression.SCREEN.value == "screen"
        assert PdfCompression.EBOOK.value == "ebook"
        assert PdfCompression.PRINT.value == "print"
        assert PdfCompression.PREPRESS.value == "prepress"


class TestWatermarkPosition:
    """Tests for WatermarkPosition enum."""

    def test_position_values(self):
        """Test watermark position values."""
        assert WatermarkPosition.CENTER.value == "center"
        assert WatermarkPosition.HEADER.value == "header"
        assert WatermarkPosition.FOOTER.value == "footer"


class TestPdfMetadataConfig:
    """Tests for PdfMetadataConfig."""

    def test_default_values(self):
        """Test default metadata values."""
        config = PdfMetadataConfig()
        assert config.title == ""
        assert config.author == ""
        assert config.subject == ""
        assert config.keywords == ""
        assert config.creator == "MD2PDF Pro"

    def test_custom_values(self):
        """Test custom metadata values."""
        config = PdfMetadataConfig(
            title="Test Document",
            author="John Doe",
            subject="Testing",
            keywords="test, pytest",
        )
        assert config.title == "Test Document"
        assert config.author == "John Doe"
        assert config.subject == "Testing"
        assert config.keywords == "test, pytest"


class TestWatermarkConfig:
    """Tests for WatermarkConfig."""

    def test_default_values(self):
        """Test default watermark values."""
        config = WatermarkConfig()
        assert config.enabled is False
        assert config.text == "CONFIDENTIAL"
        assert config.opacity == 0.3
        assert config.position == WatermarkPosition.CENTER
        assert config.angle == 45
        assert config.font_size == 48
        assert config.color == "gray"

    def test_custom_values(self):
        """Test custom watermark values."""
        config = WatermarkConfig(
            enabled=True,
            text="DRAFT",
            opacity=0.5,
            position=WatermarkPosition.HEADER,
            angle=30,
            font_size=36,
            color="red",
        )
        assert config.enabled is True
        assert config.text == "DRAFT"
        assert config.opacity == 0.5
        assert config.position == WatermarkPosition.HEADER
        assert config.angle == 30
        assert config.font_size == 36
        assert config.color == "red"

    def test_opacity_bounds(self):
        """Test opacity value bounds."""
        with pytest.raises(ValueError):
            WatermarkConfig(opacity=1.5)
        with pytest.raises(ValueError):
            WatermarkConfig(opacity=-0.1)

    def test_angle_bounds(self):
        """Test angle value bounds."""
        with pytest.raises(ValueError):
            WatermarkConfig(angle=200)
        with pytest.raises(ValueError):
            WatermarkConfig(angle=-200)


class TestPdfOptimizationConfig:
    """Tests for PdfOptimizationConfig."""

    def test_default_values(self):
        """Test default optimization values."""
        config = PdfOptimizationConfig()
        assert config.compression == PdfCompression.SCREEN
        assert isinstance(config.metadata, PdfMetadataConfig)
        assert isinstance(config.watermark, WatermarkConfig)

    def test_custom_values(self):
        """Test custom optimization values."""
        metadata = PdfMetadataConfig(title="Custom", author="Me")
        watermark = WatermarkConfig(enabled=True, text="TEST")
        config = PdfOptimizationConfig(
            compression=PdfCompression.PRINT,
            metadata=metadata,
            watermark=watermark,
        )
        assert config.compression == PdfCompression.PRINT
        assert config.metadata.title == "Custom"
        assert config.watermark.enabled is True
