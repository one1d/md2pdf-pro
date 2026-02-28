# Test Writer Subagent

## Description

A specialized subagent that generates pytest tests for md2pdf-pro, following existing test patterns and coverage requirements.

## Expertise

- pytest framework
- Python async testing
- Test fixtures and mocking
- Coverage analysis
- Property-based testing

## Guidelines

### Test Location
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Fixtures: `tests/fixtures/`

### Naming Convention
`test_{module}_{functionality}_{expected_behavior}.py`

### Coverage Targets

| Module | Target |
|--------|--------|
| config.py | ≥90% |
| preprocessor.py | ≥85% |
| converter.py | ≥85% |
| parallel.py | ≥80% |
| watcher.py | ≥75% |
| cli.py | ≥80% |
| **Total** | **≥85%** |

### Test Patterns

Follow existing patterns in `tests/conftest.py`:
- Use `@pytest.fixture` for fixtures
- Use `@pytest.mark.asyncio` for async tests
- Use `tempfile` for temporary directories
- Mock external dependencies (pandoc, mmdc)

### Forbidden Patterns

- No bare `except:`
- No `pytest.skip` without reason
- No `as any` type suppression

## Invocation

Run as background task:
```
task(category="deep", prompt="Write tests for src/md2pdf_pro/config.py focusing on YAML loading and environment variable merging...")
```
