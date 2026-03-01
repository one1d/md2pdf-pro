"""Unit tests for parallel module."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from md2pdf_pro.parallel import (
    AdaptiveBatchProcessor,
    BatchProcessor,
    BatchResult,
    ProcessingResult,
    process_files_parallel,
)


@pytest.fixture
def test_files(temp_dir):
    """Create test files for processing."""
    files = []
    for i in range(5):
        file_path = temp_dir / f"test{i}.md"
        file_path.write_text(f"# Test {i}", encoding="utf-8")
        files.append(file_path)
    return files


def test_processing_result():
    """Test ProcessingResult dataclass."""
    # Test success case
    success_result = ProcessingResult(
        success=True,
        input_path=Path("input.md"),
        output_path=Path("output.pdf"),
        duration_ms=123.45,
    )
    assert success_result.success is True
    assert success_result.input_path == Path("input.md")
    assert success_result.output_path == Path("output.pdf")
    assert success_result.error is None
    assert success_result.duration_ms == 123.45

    # Test failure case
    failure_result = ProcessingResult(
        success=False,
        input_path=Path("input.md"),
        error="Processing failed",
        duration_ms=99.99,
    )
    assert failure_result.success is False
    assert failure_result.input_path == Path("input.md")
    assert failure_result.output_path is None
    assert failure_result.error == "Processing failed"
    assert failure_result.duration_ms == 99.99


def test_batch_result():
    """Test BatchResult dataclass."""
    # Create test results
    results = [
        ProcessingResult(success=True, input_path=Path("file1.md")),
        ProcessingResult(success=True, input_path=Path("file2.md")),
        ProcessingResult(success=False, input_path=Path("file3.md"), error="Error"),
    ]

    batch_result = BatchResult(
        total=3,
        success=2,
        failed=1,
        skipped=0,
        results=results,
        total_duration_ms=1000.0,
    )

    assert batch_result.total == 3
    assert batch_result.success == 2
    assert batch_result.failed == 1
    assert batch_result.skipped == 0
    assert batch_result.success_rate == 2 / 3
    assert len(batch_result.failed_items) == 1
    assert batch_result.failed_items[0] == Path("file3.md")
    assert batch_result.total_duration_ms == 1000.0


def test_batch_result_empty():
    """Test BatchResult with empty results."""
    batch_result = BatchResult(total=0, success=0, failed=0, skipped=0)
    assert batch_result.success_rate == 0.0
    assert batch_result.failed_items == []


async def test_process_batch_success(test_files):
    """Test process_batch with successful processing."""
    processor = BatchProcessor(max_workers=2, show_progress=False)

    # Create a simple process function that returns success
    async def process_fn(file):
        await asyncio.sleep(0.01)  # Simulate work
        return Path(f"{file.stem}.pdf")

    result = await processor.process_batch(test_files, process_fn)

    assert result.total == len(test_files)
    assert result.success == len(test_files)
    assert result.failed == 0
    assert result.skipped == 0
    assert len(result.results) == len(test_files)
    assert all(r.success for r in result.results)


async def test_process_batch_with_failures(test_files):
    """Test process_batch with some failures."""
    processor = BatchProcessor(max_workers=2, show_progress=False)

    # Create a process function that fails for even-indexed files
    async def process_fn(file):
        await asyncio.sleep(0.01)
        if int(file.stem[-1]) % 2 == 0:
            raise Exception(f"Error processing {file}")
        return Path(f"{file.stem}.pdf")

    result = await processor.process_batch(test_files, process_fn)

    assert result.total == len(test_files)
    assert result.success == 2  # Files 1, 3
    assert result.failed == 3  # Files 0, 2, 4
    assert result.skipped == 0
    assert len(result.results) == len(test_files)
    assert len(result.failed_items) == 3


async def test_process_batch_with_retry(test_files):
    """Test process_batch with retry logic."""
    processor = BatchProcessor(max_workers=2, show_progress=False)

    # Create a process function that fails on first attempt, succeeds on second
    attempt_count = {}

    async def process_fn(file):
        attempt_count[file] = attempt_count.get(file, 0) + 1
        if attempt_count[file] == 1:
            raise Exception(f"First attempt failed for {file}")
        return Path(f"{file.stem}.pdf")

    result = await processor.process_batch(
        test_files, process_fn, retry_attempts=1, retry_backoff=0.01
    )

    assert result.total == len(test_files)
    assert result.success == len(test_files)
    assert result.failed == 0
    # Each file should have been attempted twice
    assert all(count == 2 for count in attempt_count.values())


async def test_process_batch_empty():
    """Test process_batch with empty file list."""
    processor = BatchProcessor(max_workers=2, show_progress=False)

    async def process_fn(file):
        pass

    result = await processor.process_batch([], process_fn)

    assert result.total == 0
    assert result.success == 0
    assert result.failed == 0
    assert result.skipped == 0
    assert result.results == []


async def test_process_with_retry_return_types(test_files):
    """Test _process_with_retry with different return types."""
    processor = BatchProcessor(max_workers=2, show_progress=False)

    # Test with Path return type
    async def process_fn_path(file):
        return Path(f"{file.stem}.pdf")

    result = await processor._process_with_retry(
        test_files[0], process_fn_path, max_attempts=0, backoff=1.0
    )
    assert result.success is True
    assert result.output_path == Path(f"{test_files[0].stem}.pdf")

    # Test with True return type
    async def process_fn_true(file):
        return True

    result = await processor._process_with_retry(
        test_files[0], process_fn_true, max_attempts=0, backoff=1.0
    )
    assert result.success is True
    assert result.output_path is None

    # Test with ProcessingResult return type
    async def process_fn_result(file):
        return ProcessingResult(success=True, input_path=file)

    result = await processor._process_with_retry(
        test_files[0], process_fn_result, max_attempts=0, backoff=1.0
    )
    assert result.success is True
    assert result.input_path == test_files[0]

    # Test with None return type
    async def process_fn_none(file):
        return None

    result = await processor._process_with_retry(
        test_files[0], process_fn_none, max_attempts=0, backoff=1.0
    )
    assert result.success is True
    assert result.output_path is None


async def test_process_with_retry_max_attempts(test_files):
    """Test _process_with_retry with max attempts reached."""
    processor = BatchProcessor(max_workers=2, show_progress=False)

    # Create a process function that always fails
    async def process_fn(file):
        raise Exception(f"Always fails for {file}")

    result = await processor._process_with_retry(
        test_files[0], process_fn, max_attempts=2, backoff=0.01
    )

    assert result.success is False
    assert result.error == f"Always fails for {test_files[0]}"


async def test_process_files_parallel(test_files):
    """Test process_files_parallel convenience function."""

    # Create a simple process function
    async def process_fn(file):
        await asyncio.sleep(0.01)
        return Path(f"{file.stem}.pdf")

    result = await process_files_parallel(
        test_files, process_fn, max_workers=2, show_progress=False
    )

    assert result.total == len(test_files)
    assert result.success == len(test_files)
    assert result.failed == 0


def test_adaptive_batch_processor():
    """Test AdaptiveBatchProcessor initialization."""
    processor = AdaptiveBatchProcessor(
        base_workers=4, cpu_threshold=70.0, memory_threshold=80.0, show_progress=False
    )

    assert processor.max_workers == 4
    assert processor.base_workers == 4
    assert processor.cpu_threshold == 70.0
    assert processor.memory_threshold == 80.0


def test_adaptive_batch_processor_get_current_workers():
    """Test AdaptiveBatchProcessor._get_current_workers method."""
    processor = AdaptiveBatchProcessor(
        base_workers=8, cpu_threshold=80.0, memory_threshold=85.0, show_progress=False
    )

    # Test with psutil available
    try:
        import psutil

        # Mock psutil functions
        original_cpu_percent = psutil.cpu_percent
        original_virtual_memory = psutil.virtual_memory

        try:
            # Test normal load (below half threshold)
            psutil.cpu_percent = lambda interval=None: 30.0  # Below half threshold
            psutil.virtual_memory = lambda: type("obj", (object,), {"percent": 30.0})
            workers = processor._get_current_workers()
            assert workers == 8

            # Test moderate load (above half threshold)
            psutil.cpu_percent = (
                lambda interval=None: 45.0
            )  # Above half threshold (80/2=40)
            workers = processor._get_current_workers()
            assert workers == 6  # 8 * 0.75

            # Test high load (above threshold)
            psutil.cpu_percent = lambda interval=None: 85.0  # Above threshold
            workers = processor._get_current_workers()
            assert workers == 4  # 8 // 2

        finally:
            # Restore original functions
            psutil.cpu_percent = original_cpu_percent
            psutil.virtual_memory = original_virtual_memory
    except ImportError:
        # psutil not available, should return base workers
        workers = processor._get_current_workers()
        assert workers == 8


async def test_batch_processor_with_progress_bar(test_files):
    """Test BatchProcessor with progress bar enabled."""
    processor = BatchProcessor(max_workers=2, show_progress=True)

    async def process_fn(file):
        await asyncio.sleep(0.01)
        return Path(f"{file.stem}.pdf")

    result = await processor.process_batch(test_files, process_fn)

    assert result.total == len(test_files)
    assert result.success == len(test_files)
