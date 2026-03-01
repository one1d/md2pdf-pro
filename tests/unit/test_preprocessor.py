"""Unit tests for preprocessor module."""

from __future__ import annotations

import subprocess

import pytest
from md2pdf_pro.config import MermaidConfig, MermaidFormat, MermaidTheme
from md2pdf_pro.preprocessor import (
    MERMAID_PATTERN,
    MermaidError,
    MermaidNotFoundError,
    MermaidPreprocessor,
    MermaidRenderError,
    compute_hash,
    diagram_line_matches,
)


@pytest.fixture
def mermaid_config():
    """Create a MermaidConfig instance."""
    return MermaidConfig(
        theme=MermaidTheme.DEFAULT,
        format=MermaidFormat.PDF,
        width=1200,
        background="white",
    )


@pytest.fixture
def preprocessor(mermaid_config, temp_dir):
    """Create a MermaidPreprocessor instance with temp output dir."""
    mermaid_config.output_dir = temp_dir / "mermaid_cache"
    return MermaidPreprocessor(mermaid_config)


def test_mermaid_pattern():
    """Test Mermaid code block pattern matching."""
    test_content = """# Test

```mermaid
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
```

Some text here.
"""
    matches = list(MERMAID_PATTERN.finditer(test_content))
    assert len(matches) == 1
    assert "flowchart TD" in matches[0].group(1)


def test_compute_hash():
    """Test compute_hash function."""
    content1 = "flowchart TD\n    A --> B"
    content2 = "flowchart TD\n    B --> A"
    hash1 = compute_hash(content1)
    hash2 = compute_hash(content2)
    assert len(hash1) == 16
    assert hash1 != hash2
    # Same content should produce same hash
    assert compute_hash(content1) == hash1


def test_diagram_line_matches():
    """Test diagram_line_matches function."""
    assert diagram_line_matches("flowchart TD", "flowchart")
    assert diagram_line_matches("graph TD", "flowchart")  # Alias
    assert diagram_line_matches("sequenceDiagram", "sequencediagram")
    assert diagram_line_matches("classDiagram", "classdiagram")
    assert diagram_line_matches("stateDiagram", "statediagram")
    assert diagram_line_matches("state A", "statediagram")  # Alternative syntax
    assert not diagram_line_matches("flowchart TD", "sequencediagram")


def test_is_available(mocker, preprocessor):
    """Test is_available method."""
    # Test when mmdc is available
    mocker.patch(
        "subprocess.run", return_value=type("obj", (object,), {"returncode": 0})
    )
    assert preprocessor.is_available()

    # Test when mmdc is not available (FileNotFoundError)
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)
    preprocessor._mmdc_available = None  # Reset cache
    assert not preprocessor.is_available()

    # Test when mmdc times out
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("mmdc", 5))
    preprocessor._mmdc_available = None  # Reset cache
    assert not preprocessor.is_available()


async def test_process_no_mermaid(preprocessor):
    """Test process method with no Mermaid code blocks."""
    content = "# Test\n\nSome text here."
    result, files = await preprocessor.process(content, "test_file")
    assert result == content
    assert len(files) == 0


async def test_process_with_mermaid(mocker, preprocessor, temp_dir):
    """Test process method with Mermaid code blocks."""
    # Mock is_available to return True
    preprocessor._mmdc_available = True

    # Mock _render_mermaid to do nothing (just pretend it worked)
    mock_render = mocker.patch.object(preprocessor, "_render_mermaid")

    # Create a test output file that will be detected as existing
    test_output = temp_dir / "test_output.pdf"
    test_output.write_text("", encoding="utf-8")

    # Mock the output file path creation to return our test file
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Create test content
    test_content = """# Test

```mermaid
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
```
"""

    result, files = await preprocessor.process(test_content, "test_file")

    assert len(files) == 1
    assert "\\includegraphics" in result  # LaTeX image reference


async def test_process_with_svg_format(mocker, preprocessor, temp_dir):
    """Test process method with SVG format."""
    # Change format to SVG
    preprocessor.config.format = MermaidFormat.SVG

    # Mock is_available to return True
    preprocessor._mmdc_available = True

    # Mock _render_mermaid to do nothing (just pretend it worked)
    mock_render = mocker.patch.object(preprocessor, "_render_mermaid")

    # Mock the output file path creation to return our test file
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Create test content
    test_content = """# Test

```mermaid
flowchart TD
    A[Start] --> B{Decision}
```
"""

    result, files = await preprocessor.process(test_content, "test_file")

    assert len(files) == 1
    assert "![]" in result  # Markdown image reference


async def test_process_mermaid_not_found(preprocessor):
    """Test process method when mermaid-cli is not found."""
    # Mock is_available to return False
    preprocessor._mmdc_available = False

    test_content = """# Test

```mermaid
flowchart TD
    A[Start] --> B{Decision}
```
"""

    result, files = await preprocessor.process(test_content, "test_file")

    # Should keep original code block
    assert "```mermaid" in result
    assert len(files) == 0


async def test_process_render_error(mocker, preprocessor):
    """Test process method when rendering fails."""
    # Mock is_available to return True
    preprocessor._mmdc_available = True

    # Mock subprocess.run to simulate error
    mocker.patch(
        "subprocess.run",
        return_value=type(
            "obj",
            (object,),
            {"returncode": 1, "stderr": "Error: Invalid Mermaid code", "stdout": ""},
        ),
    )

    test_content = """# Test

```mermaid
invalid mermaid code
```
"""

    result, files = await preprocessor.process(test_content, "test_file")

    # Should keep original code block
    assert "```mermaid" in result
    assert len(files) == 0


async def test_process_output_not_created(mocker, preprocessor):
    """Test process method when output file is not created."""
    # Mock is_available to return True
    preprocessor._mmdc_available = True

    # Mock subprocess.run to return success but not create file
    mocker.patch(
        "subprocess.run",
        return_value=type(
            "obj", (object,), {"returncode": 0, "stderr": "", "stdout": ""}
        ),
    )

    test_content = """# Test

```mermaid
flowchart TD
    A[Start] --> B{Decision}
```
"""

    result, files = await preprocessor.process(test_content, "test_file")

    # Should keep original code block
    assert "```mermaid" in result
    assert len(files) == 0


def test_clear_cache(preprocessor, temp_dir):
    """Test clear_cache method."""
    # Create some test files in the cache directory
    cache_dir = preprocessor.output_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Create test files
    (cache_dir / "test1.pdf").write_text("", encoding="utf-8")
    (cache_dir / "test2.svg").write_text("", encoding="utf-8")

    # Clear cache
    count = preprocessor.clear_cache()

    assert count == 2
    assert not any(cache_dir.iterdir())


def test_build_command(preprocessor, temp_dir):
    """Test _build_command method."""
    input_path = temp_dir / "test.mmd"
    output_path = temp_dir / "test.pdf"

    cmd = preprocessor._build_command(input_path, output_path)

    assert cmd[0] == "mmdc"
    assert "-i" in cmd
    assert str(input_path) in cmd
    assert "-o" in cmd
    assert str(output_path) in cmd
    assert "-w" in cmd
    assert "1200" in cmd
    assert "-b" in cmd
    assert "white" in cmd
    assert "--pdfFit" in cmd


def test_build_command_with_theme(preprocessor, temp_dir):
    """Test _build_command method with custom theme."""
    preprocessor.config.theme = MermaidTheme.DARK
    input_path = temp_dir / "test.mmd"
    output_path = temp_dir / "test.pdf"

    cmd = preprocessor._build_command(input_path, output_path)

    assert "-t" in cmd
    assert "dark" in cmd


def test_build_command_with_svg(preprocessor, temp_dir):
    """Test _build_command method with SVG format."""
    preprocessor.config.format = MermaidFormat.SVG
    input_path = temp_dir / "test.mmd"
    output_path = temp_dir / "test.svg"

    cmd = preprocessor._build_command(input_path, output_path)

    assert "--pdfFit" not in cmd


def test_mermaid_errors():
    """Test Mermaid error classes."""
    with pytest.raises(MermaidError):
        raise MermaidError("Test error")

    with pytest.raises(MermaidNotFoundError):
        raise MermaidNotFoundError("Mermaid not found")

    with pytest.raises(MermaidRenderError):
        raise MermaidRenderError("Render error")

    # Test that specific errors are subclasses of MermaidError
    assert issubclass(MermaidNotFoundError, MermaidError)
    assert issubclass(MermaidRenderError, MermaidError)
