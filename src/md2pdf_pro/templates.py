"""Template management for MD2PDF Pro."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"
USER_TEMPLATE_DIR = Path.home() / ".md2pdf" / "templates"


class BuiltinTemplate(str, Enum):
    """Built-in Pandoc templates."""

    DEFAULT = "default"
    ACADEMIC = "academic"
    REPORT = "report"
    MINIMAL = "minimal"


@dataclass
class TemplateInfo:
    """Template information."""

    name: str
    path: Path
    is_builtin: bool
    description: str = ""


def list_templates() -> list[TemplateInfo]:
    """List all available templates.

    Returns:
        List of available templates
    """
    templates: list[TemplateInfo] = []

    # Built-in templates
    if TEMPLATE_DIR.exists():
        for template_file in TEMPLATE_DIR.glob("*.latex"):
            templates.append(
                TemplateInfo(
                    name=template_file.stem,
                    path=template_file,
                    is_builtin=True,
                    description=f"Built-in template: {template_file.stem}",
                )
            )

    # User templates
    if USER_TEMPLATE_DIR.exists():
        for template_file in USER_TEMPLATE_DIR.glob("*.latex"):
            templates.append(
                TemplateInfo(
                    name=template_file.stem,
                    path=template_file,
                    is_builtin=False,
                    description=f"User template: {template_file.stem}",
                )
            )

    return templates


def get_template(name: str) -> Path | None:
    """Get template path by name.

    Args:
        name: Template name

    Returns:
        Path to template if found, None otherwise
    """
    # Check builtin
    builtin_path = TEMPLATE_DIR / f"{name}.latex"
    if builtin_path.exists():
        return builtin_path

    # Check user templates
    user_path = USER_TEMPLATE_DIR / f"{name}.latex"
    if user_path.exists():
        return user_path

    return None


def validate_template(path: Path) -> bool:
    """Validate a template file.

    Args:
        path: Path to template file

    Returns:
        True if valid
    """
    if not path.exists():
        return False

    if path.suffix != ".latex":
        return False

    # Basic content check
    content = path.read_text(encoding="utf-8")
    return "$if" in content or "$for" in content or "$pagestyle" in content


def ensure_user_template_dir() -> Path:
    """Ensure user template directory exists.

    Returns:
        Path to user template directory
    """
    USER_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    return USER_TEMPLATE_DIR
