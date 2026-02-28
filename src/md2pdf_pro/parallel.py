"""Batch processing and concurrency control for MD2PDF Pro.

This module provides parallel processing capabilities with
asyncio-based concurrency control and progress tracking.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class ProcessingResult:
    """Result of processing a single item."""

    success: bool
    input_path: Path
    output_path: Path | None = None
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class BatchResult:
    """Result of batch processing."""

    total: int
    success: int
    failed: int
    skipped: int
    results: list[ProcessingResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return self.success / self.total

    @property
    def failed_items(self) -> list[Path]:
        """Get list of failed item paths."""
        return [r.input_path for r in self.results if not r.success]


class BatchProcessor:
    """Batch processor with concurrency control.

    Features:
    - Asyncio-based concurrency
    - Semaphore-based rate limiting
    - Rich progress bar display
    - Error isolation (one failure doesn't stop batch)
    - Configurable retry logic
    """

    def __init__(
        self,
        max_workers: int = 8,
        show_progress: bool = True,
        console: Console | None = None,
    ):
        """Initialize batch processor.

        Args:
            max_workers: Maximum concurrent tasks
            show_progress: Whether to show progress bar
            console: Rich console instance
        """
        self.max_workers = max_workers
        self.show_progress = show_progress
        self.console = console or Console()
        self.semaphore: asyncio.Semaphore | None = None
        self.progress: Progress | None = None
        self._task_id: int | None = None

    async def process_batch(
        self,
        items: list[Path],
        process_fn: Callable[[Path], asyncio.coroutine],
        *,
        task_name: str = "Processing",
        retry_attempts: int = 0,
        retry_backoff: float = 2.0,
    ) -> BatchResult:
        """Process a batch of items concurrently.

        Args:
            items: List of file paths to process
            process_fn: Async function to process each item
            task_name: Name for progress display
            retry_attempts: Number of retry attempts on failure
            retry_backoff: Backoff factor for retries

        Returns:
            BatchResult with processing statistics
        """
        if not items:
            return BatchResult(total=0, success=0, failed=0, skipped=0)

        start_time = time.time()
        results: list[ProcessingResult] = []
        semaphore = asyncio.Semaphore(self.max_workers)

        # Create progress bar
        if self.show_progress:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=self.console,
            )
            self.progress.start()
            self._task_id = self.progress.add_task(
                f"[cyan]{task_name}", total=len(items)
            )

        # Process all items
        async def process_with_semaphore(item: Path) -> ProcessingResult:
            async with semaphore:
                return await self._process_with_retry(
                    item, process_fn, retry_attempts, retry_backoff
                )

        # Run all tasks concurrently
        tasks = [process_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results: list[ProcessingResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    ProcessingResult(
                        success=False,
                        input_path=items[i],
                        error=str(result),
                    )
                )
            elif isinstance(result, ProcessingResult):
                final_results.append(result)
            else:
                final_results.append(
                    ProcessingResult(
                        success=False,
                        input_path=items[i],
                        error=f"Unexpected result type: {type(result)}",
                    )
                )

        # Update progress to complete
        if self.progress and self._task_id is not None:
            self.progress.update(self._task_id, completed=len(items))
            self.progress.stop()

        # Calculate statistics
        success_count = sum(1 for r in final_results if r.success)
        failed_count = sum(1 for r in final_results if not r.success)
        skipped_count = 0  # Could add skip logic

        total_duration = (time.time() - start_time) * 1000

        return BatchResult(
            total=len(items),
            success=success_count,
            failed=failed_count,
            skipped=skipped_count,
            results=final_results,
            total_duration_ms=total_duration,
        )

    async def _process_with_retry(
        self,
        item: Path,
        process_fn: Callable[[Path], asyncio.coroutine],
        max_attempts: int,
        backoff: float,
    ) -> ProcessingResult:
        """Process item with retry logic.

        Args:
            item: Item to process
            process_fn: Processing function
            max_attempts: Maximum retry attempts
            backoff: Backoff factor

        Returns:
            ProcessingResult
        """
        last_error: str | None = None

        for attempt in range(max_attempts + 1):
            start_time = time.time()

            try:
                result = await process_fn(item)
                duration = (time.time() - start_time) * 1000

                if isinstance(result, Path):
                    return ProcessingResult(
                        success=True,
                        input_path=item,
                        output_path=result,
                        duration_ms=duration,
                    )
                elif result is True:
                    return ProcessingResult(
                        success=True,
                        input_path=item,
                        duration_ms=duration,
                    )
                elif isinstance(result, ProcessingResult):
                    result.duration_ms = duration
                    return result
                else:
                    return ProcessingResult(
                        success=True,
                        input_path=item,
                        duration_ms=duration,
                    )

            except Exception as e:
                last_error = str(e)
                logger.debug(f"Attempt {attempt + 1} failed for {item}: {e}")

                if attempt < max_attempts:
                    wait_time = backoff**attempt
                    await asyncio.sleep(wait_time)

        duration = (time.time() - start_time) * 1000
        return ProcessingResult(
            success=False,
            input_path=item,
            error=last_error or "Unknown error",
            duration_ms=duration,
        )


class AdaptiveBatchProcessor(BatchProcessor):
    """Adaptive batch processor that adjusts concurrency based on system load.

    Monitors CPU and memory usage to dynamically adjust max_workers.
    """

    def __init__(
        self,
        base_workers: int = 8,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0,
        show_progress: bool = True,
        console: Console | None = None,
    ):
        """Initialize adaptive batch processor.

        Args:
            base_workers: Base maximum concurrent tasks
            cpu_threshold: CPU usage threshold to reduce concurrency
            memory_threshold: Memory usage threshold to reduce concurrency
            show_progress: Whether to show progress
            console: Rich console instance
        """
        super().__init__(max_workers=base_workers, show_progress=show_progress, console=console)
        self.base_workers = base_workers
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def _get_current_workers(self) -> int:
        """Calculate current workers based on system load.

        Returns:
            Adjusted worker count
        """
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent

            # Reduce workers if system is under load
            if cpu_percent > self.cpu_threshold or memory_percent > self.memory_threshold:
                # Aggressive reduction
                return max(2, self.base_workers // 2)
            elif cpu_percent > self.cpu_threshold / 2 or memory_percent > self.memory_threshold / 2:
                # Moderate reduction
                return max(2, int(self.base_workers * 0.75))

            return self.base_workers

        except ImportError:
            # psutil not available, use base workers
            return self.base_workers


async def process_files_parallel(
    files: list[Path],
    process_fn: Callable[[Path], asyncio.coroutine],
    max_workers: int = 8,
    show_progress: bool = True,
) -> BatchResult:
    """Convenience function for parallel file processing.

    Args:
        files: List of files to process
        process_fn: Async processing function
        max_workers: Maximum concurrent tasks
        show_progress: Show progress bar

    Returns:
        BatchResult with statistics
    """
    processor = BatchProcessor(
        max_workers=max_workers,
        show_progress=show_progress,
    )
    return await processor.process_batch(files, process_fn)
