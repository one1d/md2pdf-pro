---
name: gen-test
description: Generate pytest tests for md2pdf-pro following existing patterns
user-invocable: true
---

# Generate Test Skill

This skill generates pytest tests following the project's existing patterns.

## Test Structure

Tests follow this structure (see `tests/conftest.py`):

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_markdown() -> str:
    """Sample Markdown content."""
    return """# Test Document..."""
```

## Test Location

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Fixtures: `tests/fixtures/`

## Test Naming

Follow pattern: `test_{module}_{functionality}_{expected_behavior}.py`

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_config.py -v
```

## Coverage Requirements

| Module | Target |
|--------|--------|
| config.py | ≥90% |
| preprocessor.py | ≥85% |
| converter.py | ≥85% |
| parallel.py | ≥80% |
| Total | ≥85% |

## Async Tests

Use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_convert():
    result = await engine.convert(input_file, output_file)
    assert result.success
```
