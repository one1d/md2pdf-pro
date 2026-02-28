# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-02-28

### Added
- Add emoji and icon support in Markdown (+emoji extension)

### Fixed
- Handle directory output (use input filename inside directory)
- Ensure output always has .pdf extension
- Change default font to Times New Roman (cross-platform)
- Update author to Guoqin Chen
- Fix hardcoded version in code

## [1.0.1] - 2026-02-28

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-02-28

### Fixed
- Add `timeout` field to PandocConfig for better conversion control
- Replace deprecated `asyncio.coroutine` with `Awaitable[None]`
- Add return type annotations to watcher.py callbacks
- Fix Task type generic in watcher.py
- Exclude docs/ from ruff linting

### Documentation
- Add bilingual CONFIG.md (Chinese/English)

## [1.0.0] - 2026-02-27

### Added
- Initial release
- Batch Markdown to PDF conversion using Pandoc + Tectonic + Mermaid-CLI
- CLI commands: convert, batch, watch, init, config-show, doctor
- Configuration via YAML files
- Mermaid diagram preprocessing
- File watching for automatic conversion
