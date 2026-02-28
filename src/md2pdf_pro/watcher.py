"""File watching and monitoring for MD2PDF Pro.

This module provides file system monitoring using watchdog,
with debouncing and automatic conversion triggering.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from watchdog.observers import Observer

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a file change event."""

    event_type: str  # created, modified, deleted
    path: Path
    is_directory: bool


class MarkdownEventHandler:
    """Watchdog event handler for Markdown files."""

    def __init__(
        self,
        callback: Callable[[FileChange], None],
        ignore_patterns: list[str] | None = None,
    ):
        """Initialize event handler.

        Args:
            callback: Function to call on file changes
            ignore_patterns: Patterns to ignore
        """
        self.callback = callback
        self.ignore_patterns = ignore_patterns or [".*", "_*"]

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        name = path.name
        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern.startswith("."):
                if name.startswith(pattern):
                    return True
            elif name == pattern:
                return True
        return False

    def on_created(self, event) -> None:
        """Handle file creation."""
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_ignore(path):
            return
        if path.suffix.lower() in (".md", ".markdown"):
            self.callback(FileChange(event_type="created", path=path, is_directory=False))

    def on_modified(self, event) -> None:
        """Handle file modification."""
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_ignore(path):
            return
        if path.suffix.lower() in (".md", ".markdown"):
            self.callback(FileChange(event_type="modified", path=path, is_directory=False))

    def on_deleted(self, event) -> None:
        """Handle file deletion."""
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_ignore(path):
            return
        if path.suffix.lower() in (".md", ".markdown"):
            self.callback(FileChange(event_type="deleted", path=path, is_directory=False))

    def on_moved(self, event) -> None:
        """Handle file move."""
        if event.is_directory:
            return
        # Treat moved files as deleted + created
        src_path = Path(event.src_path)
        dest_path = Path(event.dest_path)

        if not self._should_ignore(dest_path):
            if dest_path.suffix.lower() in (".md", ".markdown"):
                self.callback(FileChange(event_type="created", path=dest_path, is_directory=False))

        if not self._should_ignore(src_path):
            if src_path.suffix.lower() in (".md", ".markdown"):
                self.callback(FileChange(event_type="deleted", path=src_path, is_directory=False))


class FileWatcher:
    """File system watcher for Markdown files.

    Features:
    - Directory monitoring with recursive option
    - Debouncing to avoid rapid successive triggers
    - Event filtering (created, modified, deleted)
    - Graceful shutdown
    """

    def __init__(
        self,
        watch_path: Path,
        callback: Callable[[list[Path]], None],
        *,
        recursive: bool = True,
        debounce_ms: int = 500,
        ignore_patterns: list[str] | None = None,
    ):
        """Initialize file watcher.

        Args:
            watch_path: Path to watch
            callback: Function to call with changed files
            recursive: Watch subdirectories
            debounce_ms: Debounce delay in milliseconds
            ignore_patterns: Patterns to ignore
        """
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.recursive = recursive
        self.debounce_ms = debounce_ms
        self.ignore_patterns = ignore_patterns or [".*", "_*", "node_modules", "__pycache__"]

        self._observer: Observer | None = None
        self._pending_changes: dict[Path, asyncio.Task[None]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self) -> None:
        """Start watching for file changes."""
        if self._observer is not None:
            logger.warning("Watcher already started")
            return

        # Create event handler
        handler = MarkdownEventHandler(
            callback=self._handle_change,
            ignore_patterns=self.ignore_patterns,
        )

        # Create and start observer
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self.watch_path),
            recursive=self.recursive,
        )
        self._observer.start()

        logger.info(f"Started watching: {self.watch_path}")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

            # Cancel pending debounce tasks
            for task in self._pending_changes.values():
                if not task.done():
                    task.cancel()

            logger.info(f"Stopped watching: {self.watch_path}")

    def _handle_change(self, change: FileChange) -> None:
        """Handle file change with debouncing."""
        path = change.path

        # Cancel existing pending task for this path
        if path in self._pending_changes:
            self._pending_changes[path].cancel()

        # Schedule new debounced callback
        async def debounced_callback():
            await asyncio.sleep(self.debounce_ms / 1000)
            self.callback([path])
            self._pending_changes.pop(path, None)

        task = asyncio.create_task(debounced_callback())
        self._pending_changes[path] = task

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._observer is not None and self._observer.is_alive()


class WatchManager:
    """Manager for multiple file watchers."""

    def __init__(self):
        """Initialize watch manager."""
        self._watchers: dict[Path, FileWatcher] = {}

    def add_watch(
        self,
        path: Path,
        callback: Callable[[list[Path]], None],
        *,
        recursive: bool = True,
        debounce_ms: int = 500,
    ) -> None:
        """Add a watch for a path.

        Args:
            path: Path to watch
            callback: Callback function
            recursive: Watch subdirectories
            debounce_ms: Debounce delay
        """
        path = path.resolve()

        if path in self._watchers:
            logger.warning(f"Path already being watched: {path}")
            return

        watcher = FileWatcher(
            watch_path=path,
            callback=callback,
            recursive=recursive,
            debounce_ms=debounce_ms,
        )
        watcher.start()
        self._watchers[path] = watcher

    def remove_watch(self, path: Path) -> None:
        """Remove a watch.

        Args:
            path: Path to stop watching
        """
        path = path.resolve()

        if path in self._watchers:
            self._watchers[path].stop()
            del self._watchers[path]

    def remove_all(self) -> None:
        """Remove all watches."""
        for watcher in self._watchers.values():
            watcher.stop()
        self._watchers.clear()

    @property
    def watchers(self) -> dict[Path, FileWatcher]:
        """Get all active watchers."""
        return self._watchers.copy()


# Global watch manager instance
_watch_manager: WatchManager | None = None


def get_watch_manager() -> WatchManager:
    """Get global watch manager instance."""
    global _watch_manager
    if _watch_manager is None:
        _watch_manager = WatchManager()
    return _watch_manager


async def watch_and_convert(
    watch_path: Path,
    convert_fn: Callable[[Path], Awaitable[None]],
    *,
    recursive: bool = True,
    debounce_ms: int = 500,
) -> None:
    """Watch directory and convert files on change.

    Args:
        watch_path: Path to watch
        convert_fn: Async conversion function
        recursive: Watch subdirectories
        debounce_ms: Debounce delay
    """
    pending: set[Path] = set()

    async def process_pending() -> None:
        while pending:
            files = list(pending)
            pending.clear()

            for file in files:
                try:
                    await convert_fn(file)
                    logger.info(f"Converted: {file}")
                except Exception as e:
                    logger.error(f"Failed to convert {file}: {e}")

    def on_change(changes: list[Path]) -> None:
        for change in changes:
            pending.add(change)

        # Schedule processing
        asyncio.create_task(process_pending())

    manager = get_watch_manager()
    manager.add_watch(
        watch_path,
        on_change,
        recursive=recursive,
        debounce_ms=debounce_ms,
    )

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        manager.remove_all()
        raise
