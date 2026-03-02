"""Command-line interface for MD2PDF Pro.

This module provides the CLI interface using Typer with Rich formatting.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from md2pdf_pro import __version__
from md2pdf_pro.config import (
    PdfCompression,
    ProjectConfig,
    get_default_config_path,
)
from md2pdf_pro.converter import PandocEngine, check_dependencies, optimize_pdf
from md2pdf_pro.parallel import BatchProcessor
from md2pdf_pro.preprocessor import MermaidPreprocessor
from md2pdf_pro.templates import get_chinese_journal_params

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


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"MD2PDF Pro v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
) -> None:
    """MD2PDF Pro - Batch Markdown to PDF Converter."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@app.command()
def convert(
    input_file: Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=False, help="Input Markdown file"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output PDF file (default: same name as input)"
    ),
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Configuration file"
    ),
    template: Path | None = typer.Option(
        None, "--template", "-t", help="Pandoc template"
    ),
    workers: int = typer.Option(
        8, "--workers", "-w", help="Number of concurrent workers"
    ),
    compression: PdfCompression = typer.Option(
        PdfCompression.SCREEN,
        "--compression",
        help="PDF compression level (none, web, screen, ebook, print, prepress)",
    ),
    author: str = typer.Option(
        "",
        "--author",
        help="PDF author",
    ),
    title: str = typer.Option(
        "",
        "--title",
        help="PDF title",
    ),
    watermark: bool = typer.Option(
        False,
        "--watermark",
        help="Enable watermark",
    ),
    watermark_text: str = typer.Option(
        "CONFIDENTIAL",
        "--watermark-text",
        help="Watermark text",
    ),
    # Chinese journal template options
    journal_title: str = typer.Option(
        "",
        "--journal-title",
        help="Chinese journal name",
    ),
    journal_vol: str = typer.Option(
        "",
        "--journal-vol",
        help="Journal volume number",
    ),
    journal_issue: str = typer.Option(
        "",
        "--journal-issue",
        help="Journal issue number",
    ),
    journal_year: str = typer.Option(
        "",
        "--journal-year",
        help="Publication year",
    ),
    article_doi: str = typer.Option(
        "",
        "--doi",
        help="Article DOI",
    ),
    affiliation: str = typer.Option(
        "",
        "--affiliation",
        help="Author affiliation",
    ),
    email: str = typer.Option(
        "",
        "--email",
        help="Author email",
    ),
) -> None:
    """Convert a Markdown file to PDF."""
    # Load configuration
    project_config = _load_config(config)

    # Chinese journal template parameters
    journal_params = get_chinese_journal_params(
        journal_title=journal_title,
        article_title=title,
        author=author,
        affiliation=affiliation,
        email=email,
        doi=article_doi,
        journal_vol=journal_vol,
        journal_issue=journal_issue,
        journal_year=journal_year,
    )

    # Apply journal template if specified
    if journal_title:
        # Get chinese_journal template if not already using custom template
        if not template:
            from md2pdf_pro.templates import get_template

            journal_template = get_template("chinese_journal")
            if journal_template:
                project_config.pandoc.template = journal_template

        project_config.pandoc.template_vars.update(journal_params)

    # Override with CLI arguments
    if template:
        project_config.pandoc.template = template
    project_config.processing.max_workers = workers

    # PDF optimization settings
    project_config.pdf.compression = compression
    if author:
        project_config.pdf.metadata.author = author
    if title:
        project_config.pdf.metadata.title = title
    if watermark:
        project_config.pdf.watermark.enabled = True
    if watermark_text:
        project_config.pdf.watermark.text = watermark_text

    # Set output path
    # 逻辑：如果未指定输出文件，则使用输入文件名（后缀改为.pdf）
    # 如果指定的是目录，则在目录中使用输入文件名
    # 如果指定的文件名没有.pdf后缀，则添加后缀
    if output is None:
        output = input_file.with_suffix(".pdf")
    elif output.is_dir():
        # If output is a directory, use input filename inside it
        output = output / f"{input_file.stem}.pdf"
    elif output.suffix.lower() != ".pdf":
        # Ensure output has .pdf extension
        output = output.with_suffix(".pdf")

    console.print(f"[cyan]Converting:[/cyan] {input_file.name}")

    # Run conversion
    try:
        asyncio.run(_convert_single(input_file, output, project_config))

        # Apply PDF optimization if enabled
        if project_config.output.optimize_pdf:
            temp_output = output
            optimized_output = output.with_suffix(".optimized.pdf")
            success = optimize_pdf(
                temp_output,
                optimized_output,
                compression=project_config.pdf.compression,
                metadata=project_config.pdf.metadata,
                watermark=project_config.pdf.watermark,
            )
            if success:
                # Replace original with optimized
                optimized_output.replace(temp_output)

        console.print(f"[green]✓[/green] PDF generated: {output}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    input_pattern: str = typer.Argument(
        ..., help="File pattern (e.g., '*.md', 'docs/*.md')"
    ),
    output_dir: Path = typer.Option(
        Path("./output"), "--output", "-o", help="Output directory"
    ),
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Configuration file"
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Process subdirectories"
    ),
    ignore: list[str] | None = typer.Option(
        None, "--ignore", "-i", help="Patterns to ignore"
    ),
    workers: int = typer.Option(
        8, "--workers", "-w", help="Number of concurrent workers"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be processed"
    ),
) -> None:
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
    directory: Path = typer.Argument(
        ..., exists=True, file_okay=False, dir_okay=True, help="Directory to watch"
    ),
    output_dir: Path = typer.Option(
        Path("./output"), "--output", "-o", help="Output directory"
    ),
    recursive: bool = typer.Option(
        True, "--recursive", "-r", help="Watch subdirectories"
    ),
    debounce: int = typer.Option(500, "--debounce", "-d", help="Debounce delay in ms"),
    workers: int = typer.Option(
        8, "--workers", "-w", help="Number of concurrent workers"
    ),
) -> None:
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
    path: Path = typer.Option(
        Path("md2pdf.yaml"), "--path", "-p", help="Config file path"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing config"
    ),
) -> None:
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
    config: Path | None = typer.Option(
        None, "--config", "-c", help="Configuration file"
    ),
) -> None:
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
) -> None:
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
        console.print(
            "\n[yellow]Auto-fix not implemented. Please install dependencies manually.[/yellow]"
        )


# Templates command group
templates_app = typer.Typer(help="Manage templates")
app.add_typer(templates_app, name="templates")


@templates_app.command("list")
def list_templates_cmd() -> None:
    """List available templates."""
    from md2pdf_pro.templates import (
        USER_TEMPLATE_DIR,
        list_templates,
    )

    templates = list_templates()

    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return

    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Description", style="white")

    for t in templates:
        template_type = "Built-in" if t.is_builtin else "User"
        table.add_row(
            t.name,
            template_type,
            t.description,
        )

    console.print(table)
    console.print(f"\n[dim]User templates: {USER_TEMPLATE_DIR}[/dim]")


@templates_app.command("path")
def template_path_cmd(name: str) -> None:
    """Show template path."""
    from md2pdf_pro.templates import get_template

    path = get_template(name)
    if path:
        console.print(f"[green]Template '{name}' found at:[/green]\n{path}")
    else:
        console.print(f"[red]Template '{name}' not found[/red]")
        raise typer.Exit(code=1)


@templates_app.command("init")
def init_template_cmd(
    name: str = typer.Argument(..., help="Template name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing"),
) -> None:
    """Initialize a user template from built-in template."""
    from md2pdf_pro.templates import (
        ensure_user_template_dir,
        get_template,
    )

    # Check if template exists
    source_path = get_template(name)
    if not source_path:
        console.print(f"[red]Template '{name}' not found[/red]")
        raise typer.Exit(code=1)

    # Ensure user template dir exists
    user_dir = ensure_user_template_dir()
    dest_path = user_dir / f"{name}.latex"

    if dest_path.exists() and not force:
        console.print(f"[yellow]Template already exists: {dest_path}[/yellow]")
        console.print("Use --force to overwrite")
        raise typer.Exit(code=1)

    # Copy template
    import shutil

    shutil.copy(source_path, dest_path)
    console.print(f"[green]Template copied to:[/green] {dest_path}")


# Plugins command group
plugins_app = typer.Typer(help="Manage plugins")
app.add_typer(plugins_app, name="plugins")


@plugins_app.command("list")
def list_plugins_cmd() -> None:
    """List available plugins."""
    from md2pdf_pro.plugins import (
        get_plugin_manager,
        register_builtin_plugins,
    )

    # Register and load plugins
    register_builtin_plugins()
    manager = get_plugin_manager()

    plugins = manager.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins found[/yellow]")
        return

    table = Table(title="Available Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    table.add_column("Status", style="yellow")

    for plugin in plugins:
        status = (
            "[green]Enabled[/green]"
            if manager.is_enabled(plugin.name)
            else "[dim]Disabled[/dim]"
        )
        table.add_row(
            plugin.name,
            plugin.version,
            plugin.description,
            status,
        )

    console.print(table)


@plugins_app.command("enable")
def enable_plugin_cmd(name: str) -> None:
    """Enable a plugin."""
    from md2pdf_pro.plugins import (
        get_plugin_manager,
        register_builtin_plugins,
    )

    register_builtin_plugins()
    manager = get_plugin_manager()

    if name not in manager._plugins:
        console.print(f"[red]Plugin '{name}' not found[/red]")
        raise typer.Exit(code=1)

    manager.enable(name)
    console.print(f"[green]Plugin '{name}' enabled[/green]")


@plugins_app.command("disable")
def disable_plugin_cmd(name: str) -> None:
    """Disable a plugin."""
    from md2pdf_pro.plugins import (
        get_plugin_manager,
        register_builtin_plugins,
    )

    register_builtin_plugins()
    manager = get_plugin_manager()

    if name not in manager._plugins:
        console.print(f"[red]Plugin '{name}' not found[/red]")
        raise typer.Exit(code=1)

    manager.disable(name)
    console.print(f"[yellow]Plugin '{name}' disabled[/yellow]")


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


async def _convert_single(
    input_file: Path, output_file: Path, config: ProjectConfig
) -> None:
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


async def _convert_batch(files: list[Path], config: ProjectConfig) -> Any:
    """Convert batch of files."""
    # Initialize components
    mermaid = MermaidPreprocessor(config.mermaid)
    engine = PandocEngine(config.pandoc, config.font)
    processor = BatchProcessor(
        max_workers=config.processing.max_workers,
        show_progress=True,
    )

    async def process_file(file: Path) -> Path:
        output_file = config.output.output_dir / f"{file.stem}.pdf"
        await _convert_single(file, output_file, config)
        return output_file

    return await processor.process_batch(files, process_file)


async def _watch_and_convert(
    directory: Path,
    config: ProjectConfig,
    recursive: bool,
    debounce_ms: int,
) -> None:
    """Watch and convert."""
    from md2pdf_pro.watcher import watch_and_convert

    async def convert_file(file: Path) -> None:
        output_file = config.output.output_dir / f"{file.stem}.pdf"
        await _convert_single(file, output_file, config)
        console.print(f"[green]✓[/green] Converted: {file.name}")

    await watch_and_convert(
        directory,
        convert_file,
        recursive=recursive,
        debounce_ms=debounce_ms,
    )


def _print_batch_results(results: Any) -> None:
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
