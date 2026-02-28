"""Command-line interface for MD2PDF Pro.

This module provides the CLI interface using Typer with Rich formatting.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from md2pdf_pro import __version__
from md2pdf_pro.config import (
    ProjectConfig,
    get_default_config_path,
)
from md2pdf_pro.converter import PandocEngine, check_dependencies
from md2pdf_pro.parallel import BatchProcessor
from md2pdf_pro.preprocessor import MermaidPreprocessor

# Initialize console
console = Console()

# Create Typer app
app = typer.Typer(
    name="md2pdf",
    help="MD2PDF Pro - Batch Markdown to PDF Converter",
    add_completion=False,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"MD2PDF Pro v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    version: bool = typer.Option(None, "--version", callback=version_callback, is_eager=True),
):
    """MD2PDF Pro - Batch Markdown to PDF Converter."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@app.command()
def convert(
    input_file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, help="Input Markdown file"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output PDF file (default: same name as input)"),
    config: Path | None = typer.Option(None, "--config", "-c", help="Configuration file"),
    template: Path | None = typer.Option(None, "--template", "-t", help="Pandoc template"),
    workers: int = typer.Option(8, "--workers", "-w", help="Number of concurrent workers"),
):
    """Convert a Markdown file to PDF."""
    # Load configuration
    project_config = _load_config(config)

    # Override with CLI arguments
    if template:
        project_config.pandoc.template = template
    project_config.processing.max_workers = workers

    # Set output path
    if output is None:
        output = input_file.with_suffix(".pdf")

    console.print(f"[cyan]Converting:[/cyan] {input_file.name}")

    # Run conversion
    try:
        asyncio.run(_convert_single(input_file, output, project_config))
        console.print(f"[green]✓[/green] PDF generated: {output}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    input_pattern: str = typer.Argument(..., help="File pattern (e.g., '*.md', 'docs/*.md')"),
    output_dir: Path = typer.Option(Path("./output"), "--output", "-o", help="Output directory"),
    config: Path | None = typer.Option(None, "--config", "-c", help="Configuration file"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Process subdirectories"),
    ignore: list[str] | None = typer.Option(None, "--ignore", "-i", help="Patterns to ignore"),
    workers: int = typer.Option(8, "--workers", "-w", help="Number of concurrent workers"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be processed"),
):
    """Convert multiple Markdown files to PDF."""
    # Load configuration
    project_config = _load_config(config)

    # Override with CLI arguments
    project_config.output.output_dir = output_dir
    project_config.processing.max_workers = workers

    # Find files
    files = _find_files(input_pattern, recursive, ignore)

    if not files:
        console.print("[yellow]No files found matching pattern[/yellow]")
        raise typer.Exit()

    # Show files to process
    console.print(f"[cyan]Found {len(files)} file(s)[/cyan]")

    if dry_run:
        for f in files:
            console.print(f"  - {f}")
        raise typer.Exit()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run batch conversion
    try:
        results = asyncio.run(_convert_batch(files, project_config))
        _print_batch_results(results)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def watch(
    directory: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True, help="Directory to watch"),
    output_dir: Path = typer.Option(Path("./output"), "--output", "-o", help="Output directory"),
    recursive: bool = typer.Option(True, "--recursive", "-r", help="Watch subdirectories"),
    debounce: int = typer.Option(500, "--debounce", "-d", help="Debounce delay in ms"),
    workers: int = typer.Option(8, "--workers", "-w", help="Number of concurrent workers"),
):
    """Watch directory for changes and convert automatically."""
    # Load configuration
    project_config = ProjectConfig()

    # Override with CLI arguments
    project_config.output.output_dir = output_dir
    project_config.processing.max_workers = workers

    console.print(f"[cyan]Watching:[/cyan] {directory}")
    console.print(f"[cyan]Output:[/cyan] {output_dir}")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")

    try:
        asyncio.run(_watch_and_convert(directory, project_config, recursive, debounce))
    except KeyboardInterrupt:
        console.print("\n[green]Stopped watching[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def init(
    path: Path = typer.Option(Path("md2pdf.yaml"), "--path", "-p", help="Config file path"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
):
    """Initialize configuration file."""
    if path.exists() and not force:
        console.print(f"[yellow]Config already exists: {path}[/yellow]")
        console.print("Use --force to overwrite")
        raise typer.Exit()

    config = ProjectConfig()
    config.to_yaml(path)

    console.print(f"[green]✓[/green] Config created: {path}")


@app.command()
def config_show(
    config: Path | None = typer.Option(None, "--config", "-c", help="Configuration file"),
):
    """Show current configuration."""
    project_config = _load_config(config)

    # Display configuration
    table = Table(title="MD2PDF Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("PDF Engine", project_config.pandoc.pdf_engine.value)
    table.add_row("Max Workers", str(project_config.processing.max_workers))
    table.add_row("Output Dir", str(project_config.output.output_dir))
    table.add_row("Temp Dir", str(project_config.output.temp_dir))
    table.add_row("Mermaid Theme", project_config.mermaid.theme.value)
    table.add_row("Log Level", project_config.logging.level.value)

    console.print(table)


@app.command()
def doctor(
    check: bool = typer.Option(True, "--check", help="Check dependencies"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues"),
):
    """Check system dependencies and environment."""
    console.print("[cyan]Checking dependencies...[/cyan]\n")

    # Check Python version
    import platform
    python_version = platform.python_version()
    console.print(f"[cyan]Python:[/cyan] {python_version}")

    # Check dependencies
    deps = check_dependencies()

    table = Table()
    table.add_column("Dependency", style="cyan")
    table.add_column("Status", style="green")

    for name, available in deps.items():
        status = "[green]✓ Installed[/green]" if available else "[red]✗ Not found[/red]"
        table.add_row(name, status)

    console.print(table)

    # Summary
    all_installed = all(deps.values())
    if all_installed:
        console.print("\n[green]✓ All dependencies installed[/green]")
    else:
        console.print("\n[red]✗ Some dependencies missing[/red]")
        console.print("[yellow]Install with:[/yellow]")
        console.print("  brew install pandoc tectonic graphviz librsvg node")
        console.print("  npm install -g @mermaid-js/mermaid-cli")

    if fix:
        console.print("\n[yellow]Auto-fix not implemented. Please install dependencies manually.[/yellow]")


def _load_config(config_path: Path | None) -> ProjectConfig:
    """Load project configuration."""
    if config_path and config_path.exists():
        return ProjectConfig.from_yaml(config_path)

    # Try default config
    default_path = get_default_config_path()
    if default_path.exists():
        return ProjectConfig.from_yaml(default_path)

    # Use defaults
    return ProjectConfig()


def _find_files(pattern: str, recursive: bool, ignore: list[str] | None) -> list[Path]:
    """Find files matching pattern."""
    base_path = Path(".")
    search_pattern = pattern

    # Handle glob patterns
    if "/" in pattern:
        parts = pattern.rsplit("/", 1)
        base_path = Path(parts[0])
        search_pattern = parts[1]

    files = []
    if recursive:
        for f in base_path.rglob(search_pattern):
            if f.is_file() and _should_process(f, ignore):
                files.append(f)
    else:
        for f in base_path.glob(search_pattern):
            if f.is_file() and _should_process(f, ignore):
                files.append(f)

    return sorted(files)


def _should_process(file: Path, ignore: list[str] | None) -> bool:
    """Check if file should be processed."""
    ignore_patterns = ignore or [".*", "_*"]

    for pattern in ignore_patterns:
        if file.name.startswith(pattern.replace("*", "")):
            return False
        if pattern in str(file):
            return False

    return file.suffix.lower() in (".md", ".markdown")


async def _convert_single(input_file: Path, output_file: Path, config: ProjectConfig):
    """Convert single file."""
    # Initialize components
    mermaid = MermaidPreprocessor(config.mermaid)
    engine = PandocEngine(config.pandoc, config.font)

    # Read input
    content = input_file.read_text(encoding="utf-8")

    # Process Mermaid
    file_id = input_file.stem
    processed_content, diagrams = await mermaid.process(content, file_id)

    # Write temp file
    config.output.temp_dir.mkdir(parents=True, exist_ok=True)
    temp_md = config.output.temp_dir / f"{input_file.stem}_processed.md"
    temp_md.write_text(processed_content, encoding="utf-8")

    # Convert to PDF
    result = await engine.convert(temp_md, output_file)

    if not result.success:
        raise RuntimeError(f"Conversion failed: {result.error}")

    # Clean up temp file
    if not config.output.preserve_temp:
        temp_md.unlink(missing_ok=True)


async def _convert_batch(files: list[Path], config: ProjectConfig):
    """Convert batch of files."""
    # Initialize components
    mermaid = MermaidPreprocessor(config.mermaid)
    engine = PandocEngine(config.pandoc, config.font)
    processor = BatchProcessor(
        max_workers=config.processing.max_workers,
        show_progress=True,
    )

    async def process_file(file: Path):
        output_file = config.output.output_dir / f"{file.stem}.pdf"
        await _convert_single(file, output_file, config)
        return output_file

    return await processor.process_batch(files, process_file)


async def _watch_and_convert(
    directory: Path,
    config: ProjectConfig,
    recursive: bool,
    debounce_ms: int,
):
    """Watch and convert."""
    from md2pdf_pro.watcher import watch_and_convert

    async def convert_file(file: Path):
        output_file = config.output.output_dir / f"{file.stem}.pdf"
        await _convert_single(file, output_file, config)
        console.print(f"[green]✓[/green] Converted: {file.name}")

    await watch_and_convert(
        directory,
        convert_file,
        recursive=recursive,
        debounce_ms=debounce_ms,
    )


def _print_batch_results(results) -> None:
    """Print batch conversion results."""
    console.print("\n[bold]Batch Complete[/bold]")
    console.print(f"  Success: [green]{results.success}[/green]")
    console.print(f"  Failed:  [red]{results.failed}[/red]")
    console.print(f"  Total:   {results.total}")
    console.print(f"  Duration: {results.total_duration_ms / 1000:.1f}s")

    if results.failed > 0:
        console.print("\n[red]Failed files:[/red]")
        for path in results.failed_items:
            console.print(f"  - {path}")


if __name__ == "__main__":
    app()
