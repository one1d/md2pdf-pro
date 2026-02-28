---
name: project-conventions
description: Enforce project-specific code conventions for md2pdf-pro
disable-model-invocation: true
---

# Project Conventions for md2pdf-pro

This skill ensures all code changes follow the project's coding standards.

## Linting Rules

Always run these checks after any Edit or Write operations:

```bash
# Ruff check
ruff check src/

# MyPy strict type checking
mypy src/ --strict

# Black format check
black --check src/
```

## Testing Rules

All new code must include tests:

```bash
# Run tests with coverage
pytest --cov=src --cov-report=term-missing
```

## Forbidden Patterns

NEVER use in code:
- Type suppression: `as any`, `@ts-ignore`, `@ts-expect-error`
- Empty catch blocks: `except: pass` or `except Exception: {}`
- TODO without issue reference: `# TODO` (must be `# TODO(#issue)`)

## Code Style

- Use Pydantic v2 models
- Use asyncio for async operations
- Use Rich for CLI output
- Use Typer for CLI framework

## Pre-commit Checklist

Before any commit, verify:
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes
- [ ] `pytest` passes
- [ ] No forbidden patterns introduced
