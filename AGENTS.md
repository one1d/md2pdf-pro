# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-28  
**Branch:** main

## OVERVIEW

**MD2PDF Pro** — Batch Markdown to PDF converter using Pandoc + Tectonic + Mermaid-CLI.

**Status**: In Development - Core modules implemented

## STRUCTURE

```
./
├── src/md2pdf_pro/          # Source code
│   ├── __init__.py          # Package init
│   ├── config.py            # Pydantic config
│   ├── preprocessor.py      # Mermaid processing
│   ├── converter.py         # Pandoc engine
│   ├── parallel.py          # Batch processor
│   ├── watcher.py           # File watcher
│   └── cli.py              # CLI entry
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── pyproject.toml           # Project config
├── requirements.txt         # Dependencies
├── Makefile                # Build scripts
└── .gitignore
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| CLI entry | `src/md2pdf_pro/cli.py` | Main CLI commands |
| Config | `src/md2pdf_pro/config.py` | Pydantic models |
| Conversion | `src/md2pdf_pro/converter.py` | Pandoc async engine |
| Mermaid | `src/md2pdf_pro/preprocessor.py` | Diagram rendering |
| Batch | `src/md2pdf_pro/parallel.py` | Concurrency |
| Watch | `src/md2pdf_pro/watcher.py` | File monitoring |

## IMPLEMENTATION STATUS

| Module | Status | Lines |
|--------|--------|-------|
| config.py | ✅ Complete | ~250 |
| preprocessor.py | ✅ Complete | ~250 |
| converter.py | ✅ Complete | ~220 |
| parallel.py | ✅ Complete | ~200 |
| watcher.py | ✅ Complete | ~200 |
| cli.py | ✅ Complete | ~350 |

## CONVENTIONS

- **Language**: Python 3.11+
- **CLI**: Typer with Rich
- **Config**: Pydantic + YAML
- **Async**: asyncio
- **Testing**: pytest

## ANTI-PATTERNS

- No type suppression (`as any`)
- No empty catch blocks
- No shotgun debugging

## COMMANDS

```bash
# Install
pip install -e .

# Test
pytest

# Lint
ruff check src/
mypy src/

# Run
md2pdf convert file.md -o output/
md2pdf batch "*.md" -o output/
md2pdf watch ./docs -o output/
md2pdf doctor
```
