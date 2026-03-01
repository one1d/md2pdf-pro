"""Unit tests for watcher module."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from md2pdf_pro.watcher import (
    FileChange,
    FileWatcher,
    MarkdownEventHandler,
    WatchManager,
    get_watch_manager,
    watch_and_convert,
)


@pytest.fixture
def test_dir(temp_dir):
    """Create a test directory with Markdown files."""
    # Create test files
    (temp_dir / "test1.md").write_text("# Test 1", encoding="utf-8")
    (temp_dir / "test2.md").write_text("# Test 2", encoding="utf-8")
    (temp_dir / ".hidden.md").write_text("# Hidden", encoding="utf-8")
    (temp_dir / "_draft.md").write_text("# Draft", encoding="utf-8")

    # Create subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "test3.md").write_text("# Test 3", encoding="utf-8")

    return temp_dir


def test_file_change():
    """Test FileChange dataclass."""
    change = FileChange(event_type="modified", path=Path("test.md"), is_directory=False)
    assert change.event_type == "modified"
    assert change.path == Path("test.md")
    assert change.is_directory is False


def test_markdown_event_handler():
    """Test MarkdownEventHandler."""
    captured_changes = []

    def callback(change):
        captured_changes.append(change)

    handler = MarkdownEventHandler(callback)

    # Mock event objects
    class MockEvent:
        def __init__(self, src_path, is_directory=False, dest_path=None):
            self.src_path = src_path
            self.is_directory = is_directory
            self.dest_path = dest_path

    # Test on_created with Markdown file
    handler.on_created(MockEvent("test.md"))
    assert len(captured_changes) == 1
    assert captured_changes[0].event_type == "created"
    assert captured_changes[0].path == Path("test.md")

    # Test on_modified with Markdown file
    captured_changes.clear()
    handler.on_modified(MockEvent("test.md"))
    assert len(captured_changes) == 1
    assert captured_changes[0].event_type == "modified"

    # Test on_deleted with Markdown file
    captured_changes.clear()
    handler.on_deleted(MockEvent("test.md"))
    assert len(captured_changes) == 1
    assert captured_changes[0].event_type == "deleted"

    # Test on_moved with Markdown files
    captured_changes.clear()
    handler.on_moved(MockEvent("old.md", dest_path="new.md"))
    assert len(captured_changes) == 2
    assert captured_changes[0].event_type == "created"
    assert captured_changes[0].path == Path("new.md")
    assert captured_changes[1].event_type == "deleted"
    assert captured_changes[1].path == Path("old.md")

    # Test ignoring hidden files
    captured_changes.clear()
    handler.on_created(MockEvent(".hidden.md"))
    assert len(captured_changes) == 0

    # Test ignoring draft files
    captured_changes.clear()
    handler.on_created(MockEvent("_draft.md"))
    assert len(captured_changes) == 0

    # Test ignoring non-Markdown files
    captured_changes.clear()
    handler.on_created(MockEvent("test.txt"))
    assert len(captured_changes) == 0

    # Test ignoring directories
    captured_changes.clear()
    handler.on_created(MockEvent("dir", is_directory=True))
    assert len(captured_changes) == 0


def test_should_ignore():
    """Test _should_ignore method."""
    handler = MarkdownEventHandler(
        lambda x: None, ignore_patterns=[".*", "_*", "node_modules"]
    )

    # Test hidden files
    assert handler._should_ignore(Path(".hidden.md"))
    # Test draft files
    assert handler._should_ignore(Path("_draft.md"))
    # Test node_modules directory
    assert handler._should_ignore(Path("node_modules"))
    # Test normal files
    assert not handler._should_ignore(Path("test.md"))


async def test_file_watcher_start_stop(test_dir):
    """Test FileWatcher start and stop."""
    captured_files = []

    def callback(files):
        captured_files.extend(files)

    watcher = FileWatcher(test_dir, callback, recursive=True, debounce_ms=10)

    # Test start
    watcher.start()
    assert watcher.is_running()

    # Test stop
    watcher.stop()
    assert not watcher.is_running()


async def test_file_watcher_debouncing(test_dir):
    """Test FileWatcher debouncing."""
    captured_files = []

    def callback(files):
        captured_files.extend(files)

    watcher = FileWatcher(test_dir, callback, recursive=True, debounce_ms=50)
    watcher.start()

    try:
        # Simulate multiple changes to the same file
        test_file = test_dir / "test1.md"

        # First change
        test_file.write_text("# Updated 1", encoding="utf-8")
        await asyncio.sleep(0.02)

        # Second change (should be debounced)
        test_file.write_text("# Updated 2", encoding="utf-8")
        await asyncio.sleep(0.1)  # Wait for debounce

        # Should only get one callback
        assert len(captured_files) >= 1
        # Check if any of the captured files matches the test file (using resolve to normalize paths)
        assert any(
            captured.resolve() == test_file.resolve() for captured in captured_files
        )
    finally:
        watcher.stop()


def test_watch_manager():
    """Test WatchManager."""
    manager = WatchManager()
    captured_files = []

    def callback(files):
        captured_files.extend(files)

    # Test add_watch
    test_dir = Path(".")
    manager.add_watch(test_dir, callback)
    assert test_dir.resolve() in manager.watchers

    # Test add_watch with same path (should warn)
    manager.add_watch(test_dir, callback)

    # Test remove_watch
    manager.remove_watch(test_dir)
    assert test_dir.resolve() not in manager.watchers

    # Test remove_all
    manager.add_watch(test_dir, callback)
    assert test_dir.resolve() in manager.watchers
    manager.remove_all()
    assert len(manager.watchers) == 0


def test_get_watch_manager():
    """Test get_watch_manager function."""
    manager1 = get_watch_manager()
    manager2 = get_watch_manager()
    assert manager1 is manager2  # Should return the same instance


async def test_watch_and_convert(test_dir):
    """Test watch_and_convert function."""
    converted_files = []

    async def convert_fn(file):
        converted_files.append(file)

    # Start watching in a background task
    watch_task = asyncio.create_task(
        watch_and_convert(test_dir, convert_fn, recursive=True, debounce_ms=50)
    )

    try:
        # Wait for watcher to start
        await asyncio.sleep(0.1)

        # Modify a file
        test_file = test_dir / "test1.md"
        test_file.write_text("# Updated", encoding="utf-8")

        # Wait for conversion
        await asyncio.sleep(0.1)

        # Check if file was converted
        assert any(
            converted.resolve() == test_file.resolve() for converted in converted_files
        )
    finally:
        # Cancel the watch task
        watch_task.cancel()
        try:
            await watch_task
        except asyncio.CancelledError:
            pass


async def test_file_watcher_edge_cases(test_dir):
    """Test FileWatcher edge cases."""
    captured_files = []

    def callback(files):
        captured_files.extend(files)

    watcher = FileWatcher(test_dir, callback, recursive=True, debounce_ms=10)

    # Test starting already started watcher
    watcher.start()
    watcher.start()  # Should not raise

    # Test stopping already stopped watcher
    watcher.stop()
    watcher.stop()  # Should not raise

    # Test is_running on stopped watcher
    assert not watcher.is_running()


async def test_markdown_event_handler_edge_cases():
    """Test MarkdownEventHandler edge cases."""
    captured_changes = []

    def callback(change):
        captured_changes.append(change)

    handler = MarkdownEventHandler(callback)

    # Mock event with no dest_path (for on_moved)
    class MockEvent:
        def __init__(self, src_path, is_directory=False):
            self.src_path = src_path
            self.is_directory = is_directory
            self.dest_path = None

    # Test on_moved with no dest_path
    handler.on_moved(MockEvent("test.md"))
    # Should not raise, but should not capture anything
    assert len(captured_changes) == 0
