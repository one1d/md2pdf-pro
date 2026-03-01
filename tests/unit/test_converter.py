"""Unit tests for converter module."""

from __future__ import annotations

import asyncio
import subprocess

# Import TimeoutError from builtins
from builtins import TimeoutError
from pathlib import Path

import pytest

from md2pdf_pro.config import FontConfig, MathEngine, PandocConfig, PdfEngine
from md2pdf_pro.converter import (
    ConversionResult,
    PandocConversionError,
    PandocEngine,
    PandocError,
    PandocNotFoundError,
    PandocTimeoutError,
    check_dependencies,
)


@pytest.fixture
def pandoc_config():
    """Create a PandocConfig instance."""
    return PandocConfig(
        pdf_engine=PdfEngine.TECTONIC,
        highlight_style="tango",
        math_engine=MathEngine.MATHSPEC,
        standalone=True,
        toc=False,
        toc_depth=3,
        timeout=300,
        extensions="+emoji",
    )


@pytest.fixture
def font_config():
    """Create a FontConfig instance."""
    return FontConfig(
        cjk_primary="PingFang SC",
        latin_primary="Times New Roman",
        monospace="Menlo",
        geometry_margin="2.5cm",
    )


@pytest.fixture
def pandoc_engine(pandoc_config, font_config):
    """Create a PandocEngine instance."""
    return PandocEngine(pandoc_config, font_config)


def test_conversion_result():
    """Test ConversionResult dataclass."""
    # Test success case
    success_result = ConversionResult(
        success=True,
        output_path=Path("output.pdf"),
        duration_ms=123.45,
    )
    assert success_result.success is True
    assert success_result.output_path == Path("output.pdf")
    assert success_result.error is None
    assert success_result.error_code is None
    assert success_result.duration_ms == 123.45

    # Test failure case
    failure_result = ConversionResult(
        success=False,
        error="Conversion failed",
        error_code=1,
        duration_ms=99.99,
    )
    assert failure_result.success is False
    assert failure_result.output_path is None
    assert failure_result.error == "Conversion failed"
    assert failure_result.error_code == 1
    assert failure_result.duration_ms == 99.99


def test_pandoc_errors():
    """Test Pandoc error classes."""
    with pytest.raises(PandocError):
        raise PandocError("Test error")

    with pytest.raises(PandocNotFoundError):
        raise PandocNotFoundError("Pandoc not found")

    with pytest.raises(PandocConversionError):
        raise PandocConversionError("Conversion error")

    with pytest.raises(PandocTimeoutError):
        raise PandocTimeoutError("Timeout error")

    # Test that specific errors are subclasses of PandocError
    assert issubclass(PandocNotFoundError, PandocError)
    assert issubclass(PandocConversionError, PandocError)
    assert issubclass(PandocTimeoutError, PandocError)


def test_is_available(mocker, pandoc_engine):
    """Test is_available method."""
    # Test when pandoc is available
    mocker.patch(
        "subprocess.run", return_value=type("obj", (object,), {"returncode": 0})
    )
    assert pandoc_engine.is_available()

    # Test when pandoc is not available (FileNotFoundError)
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)
    pandoc_engine._pandoc_available = None  # Reset cache
    assert not pandoc_engine.is_available()

    # Test when pandoc times out
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pandoc", 5))
    pandoc_engine._pandoc_available = None  # Reset cache
    assert not pandoc_engine.is_available()


def test_version(mocker, pandoc_engine):
    """Test version property."""
    # Test when pandoc is available
    mock_result = type(
        "obj",
        (object,),
        {"returncode": 0, "stdout": "pandoc 3.1.12\nCompiled with pandoc-types 1.23\n"},
    )
    mocker.patch("subprocess.run", return_value=mock_result)
    assert pandoc_engine.version == "pandoc 3.1.12"

    # Test when pandoc is not available
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)
    pandoc_engine._pandoc_version = None  # Reset cache
    assert pandoc_engine.version is None


async def test_convert_success(mocker, pandoc_engine, temp_dir):
    """Test convert method with successful conversion."""
    # Mock is_available to return True
    pandoc_engine._pandoc_available = True

    # Create test files
    input_file = temp_dir / "test.md"
    input_file.write_text("# Test\n\nHello World", encoding="utf-8")
    output_file = temp_dir / "output.pdf"

    # Mock asyncio.create_subprocess_exec
    async def mock_communicate():
        return (b"", b"")

    mock_process = type(
        "obj",
        (object,),
        {
            "communicate": mock_communicate,
            "returncode": 0,
            "kill": lambda: None,
            "wait": lambda: None,
        },
    )
    mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)

    result = await pandoc_engine.convert(input_file, output_file)

    assert result.success is True
    assert result.output_path == output_file
    assert result.error is None
    assert result.error_code is None
    assert result.duration_ms > 0


async def test_convert_timeout(mocker, pandoc_engine, temp_dir):
    """Test convert method with timeout."""
    # Mock is_available to return True
    pandoc_engine._pandoc_available = True

    # Create test files
    input_file = temp_dir / "test.md"
    input_file.write_text("# Test\n\nHello World", encoding="utf-8")
    output_file = temp_dir / "output.pdf"

    # Mock asyncio.create_subprocess_exec
    async def mock_communicate():
        await asyncio.sleep(10)
        return (b"", b"")

    async def mock_wait():
        return None

    mock_process = type(
        "obj",
        (object,),
        {
            "communicate": mock_communicate,
            "returncode": 0,
            "kill": lambda: None,
            "wait": mock_wait,
        },
    )
    mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)

    # Mock asyncio.wait_for to raise TimeoutError
    mocker.patch("asyncio.wait_for", side_effect=TimeoutError)

    result = await pandoc_engine.convert(input_file, output_file, timeout=1)

    assert result.success is False
    assert result.output_path is None
    # 错误信息是 "Conversion timed out"，所以应该检查 "timed out" 或 "timeout"
    assert "timed out" in result.error
    assert result.error_code == -1


async def test_convert_failure(mocker, pandoc_engine, temp_dir):
    """Test convert method with conversion failure."""
    # Mock is_available to return True
    pandoc_engine._pandoc_available = True

    # Create test files
    input_file = temp_dir / "test.md"
    input_file.write_text("# Test\n\nHello World", encoding="utf-8")
    output_file = temp_dir / "output.pdf"

    # Mock asyncio.create_subprocess_exec
    async def mock_communicate():
        return (b"", b"Error: Invalid markdown")

    mock_process = type(
        "obj",
        (object,),
        {
            "communicate": mock_communicate,
            "returncode": 1,
            "kill": lambda: None,
            "wait": lambda: None,
        },
    )
    mocker.patch("asyncio.create_subprocess_exec", return_value=mock_process)

    result = await pandoc_engine.convert(input_file, output_file)

    assert result.success is False
    assert result.output_path is None
    assert "Error: Invalid markdown" in result.error
    assert result.error_code == 1


async def test_convert_pandoc_not_found(pandoc_engine, temp_dir):
    """Test convert method when pandoc is not found."""
    # Mock is_available to return False
    pandoc_engine._pandoc_available = False

    # Create test files
    input_file = temp_dir / "test.md"
    input_file.write_text("# Test\n\nHello World", encoding="utf-8")
    output_file = temp_dir / "output.pdf"

    with pytest.raises(PandocNotFoundError):
        await pandoc_engine.convert(input_file, output_file)


async def test_convert_file_not_found(mocker, pandoc_engine, temp_dir):
    """Test convert method with non-existent input file."""
    # Mock is_available to return True
    pandoc_engine._pandoc_available = True

    # Non-existent input file
    input_file = temp_dir / "non_existent.md"
    output_file = temp_dir / "output.pdf"

    # Mock asyncio.create_subprocess_exec to raise FileNotFoundError
    mocker.patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError)

    result = await pandoc_engine.convert(input_file, output_file)

    assert result.success is False
    assert result.output_path is None
    assert "not found" in result.error.lower()
    assert result.error_code == -2


async def test_convert_generic_error(mocker, pandoc_engine, temp_dir):
    """Test convert method with generic error."""
    # Mock is_available to return True
    pandoc_engine._pandoc_available = True

    # Create test files
    input_file = temp_dir / "test.md"
    input_file.write_text("# Test\n\nHello World", encoding="utf-8")
    output_file = temp_dir / "output.pdf"

    # Mock asyncio.create_subprocess_exec to raise generic exception
    mocker.patch(
        "asyncio.create_subprocess_exec", side_effect=Exception("Generic error")
    )

    result = await pandoc_engine.convert(input_file, output_file)

    assert result.success is False
    assert result.output_path is None
    assert "Generic error" in result.error
    assert result.error_code == -99


def test_build_args(pandoc_engine, temp_dir):
    """Test _build_args method."""
    input_file = temp_dir / "test.md"
    output_file = temp_dir / "output.pdf"
    metadata = {"title": "Test Document", "author": "Test Author"}

    args = pandoc_engine._build_args(input_file, output_file, metadata)

    assert str(input_file) in args
    assert "-o" in args
    assert str(output_file) in args
    assert "--standalone" in args
    assert "--pdf-engine=tectonic" in args
    assert "--highlight-style=tango" in args
    assert "-fmarkdown+emoji" in args
    assert "-V" in args
    assert "CJKmainfont=PingFang SC" in args
    assert "mainfont=Times New Roman" in args
    assert "monofont=Menlo" in args
    assert "geometry:margin=2.5cm" in args
    assert "-M" in args
    assert "title=Test Document" in args
    assert "author=Test Author" in args


def test_build_args_with_toc(pandoc_engine, temp_dir):
    """Test _build_args method with TOC enabled."""
    # Enable TOC
    pandoc_engine.config.toc = True
    pandoc_engine.config.toc_depth = 2

    input_file = temp_dir / "test.md"
    output_file = temp_dir / "output.pdf"

    args = pandoc_engine._build_args(input_file, output_file)

    assert "--toc" in args
    assert "--toc-depth=2" in args


def test_build_args_with_template(pandoc_engine, temp_dir):
    """Test _build_args method with template."""
    # Set template
    template_file = temp_dir / "template.tex"
    pandoc_engine.config.template = template_file

    input_file = temp_dir / "test.md"
    output_file = temp_dir / "output.pdf"

    args = pandoc_engine._build_args(input_file, output_file)

    assert "--template" in args
    assert str(template_file) in args


def test_get_font_args(pandoc_engine):
    """Test _get_font_args method."""
    font_args = pandoc_engine._get_font_args()

    assert len(font_args) == 8  # 4 font settings × 2 elements each
    assert "-V" in font_args
    assert "CJKmainfont=PingFang SC" in font_args
    assert "mainfont=Times New Roman" in font_args
    assert "monofont=Menlo" in font_args
    assert "geometry:margin=2.5cm" in font_args


def test_check_dependencies(mocker):
    """Test check_dependencies function."""

    # Mock subprocess.run for all dependencies
    def mock_run(cmd, **kwargs):
        if cmd[0] == "pandoc":
            return type("obj", (object,), {"returncode": 0})
        elif cmd[0] == "tectonic":
            return type("obj", (object,), {"returncode": 0})
        elif cmd[0] == "xelatex":
            return type("obj", (object,), {"returncode": 1})
        return type("obj", (object,), {"returncode": 1})

    mocker.patch("subprocess.run", side_effect=mock_run)

    deps = check_dependencies()

    assert deps["pandoc"] is True
    assert deps["tectonic"] is True
    assert deps["xelatex"] is False


def test_check_dependencies_not_found(mocker):
    """Test check_dependencies function when dependencies are not found."""
    # Mock subprocess.run to raise FileNotFoundError for all
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)

    deps = check_dependencies()

    assert deps["pandoc"] is False
    assert deps["tectonic"] is False
    assert deps["xelatex"] is False
