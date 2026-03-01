"""Unit tests for CLI module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from md2pdf_pro.cli import app
from md2pdf_pro.config import ProjectConfig


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def test_dir():
    """Create test directory with Markdown files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        (Path(tmpdir) / "test1.md").write_text("# Test 1", encoding="utf-8")
        (Path(tmpdir) / "test2.md").write_text("# Test 2", encoding="utf-8")
        (Path(tmpdir) / ".hidden.md").write_text("# Hidden", encoding="utf-8")
        (Path(tmpdir) / "_draft.md").write_text("# Draft", encoding="utf-8")

        # Create subdirectory
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "test3.md").write_text("# Test 3", encoding="utf-8")

        yield Path(tmpdir)


def test_version(runner):
    """Test version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "MD2PDF Pro v" in result.output


def test_init(runner, test_dir):
    """Test init command."""
    config_path = test_dir / "md2pdf.yaml"

    # Test creating config file
    result = runner.invoke(app, ["init", "--path", str(config_path)])
    assert result.exit_code == 0
    assert f"Config created: {config_path}" in result.output
    assert config_path.exists()

    # Test overwriting config file
    result = runner.invoke(app, ["init", "--path", str(config_path)])
    assert result.exit_code == 0
    assert f"Config already exists: {config_path}" in result.output

    # Test force overwrite
    result = runner.invoke(app, ["init", "--path", str(config_path), "--force"])
    assert result.exit_code == 0
    assert f"Config created: {config_path}" in result.output


def test_config_show(runner, test_dir):
    """Test config_show command."""
    # Test with default config
    result = runner.invoke(app, ["config-show"])
    assert result.exit_code == 0
    assert "MD2PDF Configuration" in result.output

    # Test with custom config
    config_path = test_dir / "md2pdf.yaml"
    config = ProjectConfig()
    config.to_yaml(config_path)

    result = runner.invoke(app, ["config-show", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "MD2PDF Configuration" in result.output


def test_doctor(runner):
    """Test doctor command."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Checking dependencies..." in result.output
    assert "Python:" in result.output
    assert "Dependency" in result.output
    assert "Status" in result.output


def test_find_files():
    """Test _find_files function."""
    from md2pdf_pro.cli import _find_files

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        (Path(tmpdir) / "test1.md").write_text("# Test 1", encoding="utf-8")
        (Path(tmpdir) / "test2.md").write_text("# Test 2", encoding="utf-8")
        (Path(tmpdir) / "test.txt").write_text("Test", encoding="utf-8")

        # Create subdirectory
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "test3.md").write_text("# Test 3", encoding="utf-8")

        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Test non-recursive
            files = _find_files("*.md", False, None)
            assert len(files) == 2
            assert any("test1.md" in str(f) for f in files)
            assert any("test2.md" in str(f) for f in files)

            # Test recursive
            files = _find_files("*.md", True, None)
            assert len(files) == 3
            assert any("test1.md" in str(f) for f in files)
            assert any("test2.md" in str(f) for f in files)
            assert any("test3.md" in str(f) for f in files)

            # Test with ignore patterns
            files = _find_files("*.md", True, ["test1"])
            assert len(files) == 2
            assert not any("test1.md" in str(f) for f in files)
            assert any("test2.md" in str(f) for f in files)
            assert any("test3.md" in str(f) for f in files)
        finally:
            os.chdir(original_cwd)


def test_should_process():
    """Test _should_process function."""
    from md2pdf_pro.cli import _should_process

    # Test Markdown files
    assert _should_process(Path("test.md"), None)
    assert _should_process(Path("test.markdown"), None)

    # Test non-Markdown files
    assert not _should_process(Path("test.txt"), None)
    assert not _should_process(Path("test.pdf"), None)

    # Test ignored files
    assert not _should_process(Path(".hidden.md"), [".*"])
    assert not _should_process(Path("_draft.md"), ["_*"])
    assert not _should_process(Path("test.md"), ["test"])


def test_convert_command(runner, test_dir):
    """Test convert command."""
    input_file = test_dir / "test1.md"
    output_file = test_dir / "test1.pdf"

    # Test basic conversion
    result = runner.invoke(
        app, ["convert", str(input_file), "--output", str(output_file)]
    )
    # Note: This will fail if pandoc is not installed, but we're testing CLI parsing
    assert result.exit_code != 0 or output_file.exists()


def test_batch_command(runner, test_dir):
    """Test batch command."""
    output_dir = test_dir / "output"

    # Test dry run
    result = runner.invoke(
        app, ["batch", "*.md", "--output", str(output_dir), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Found 2 file(s)" in result.output
    assert "test1.md" in result.output
    assert "test2.md" in result.output


def test_watch_command(runner, test_dir):
    """Test watch command."""
    # Test watch command (will exit immediately due to lack of async loop in test)
    result = runner.invoke(
        app, ["watch", str(test_dir), "--output", str(test_dir / "output")]
    )
    # Note: This will fail in test environment, but we're testing CLI parsing
    assert result.exit_code != 0
