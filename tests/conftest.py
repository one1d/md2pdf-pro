"""Pytest configuration and fixtures for MD2PDF Pro."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Set test environment
os.environ["MD2PDF_TESTING"] = "1"


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown() -> str:
    """Sample Markdown content."""
    return """# Test Document

This is a test document with some content.

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Math

Inline math: $E = mc^2$

Block math:

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

## List

- Item 1
- Item 2
- Item 3
"""


@pytest.fixture
def sample_markdown_with_mermaid() -> str:
    """Sample Markdown with Mermaid diagram."""
    return """# Test with Mermaid

## Flowchart

```mermaid
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello Bob!
    B-->>A: Hi Alice!
```
"""


@pytest.fixture
def config_dict() -> dict:
    """Sample configuration dictionary."""
    return {
        "mermaid": {
            "theme": "default",
            "format": "pdf",
            "width": 1200,
            "background": "white",
        },
        "pandoc": {
            "pdf_engine": "tectonic",
            "highlight_style": "tango",
        },
        "processing": {
            "max_workers": 4,
            "timeout": 60,
        },
        "output": {
            "output_dir": "./output",
            "temp_dir": "/tmp/md2pdf_test",
        },
    }
