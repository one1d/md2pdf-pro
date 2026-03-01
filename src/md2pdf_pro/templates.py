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
    CHINESE_JOURNAL = "chinese_journal"


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


def get_chinese_journal_params(
    journal_title: str = "",
    article_title: str = "",
    subtitle: str = "",
    author: str = "",
    affiliation: str = "",
    email: str = "",
    abstract: str = "",
    keywords: str = "",
    abstract_en: str = "",
    keywords_en: str = "",
    doi: str = "",
    article_id: str = "",
    journal_vol: str = "",
    journal_issue: str = "",
    journal_year: str = "",
    journal_date: str = "",
) -> dict[str, str]:
    """Generate template variables for Chinese journal template.

    Args:
        journal_title: Journal name (期刊名称)
        article_title: Article title (文章标题)
        subtitle: Subtitle (副标题)
        author: Author names (作者)
        affiliation: Author affiliations (单位)
        email: Email address (邮箱)
        abstract: Chinese abstract (摘要)
        keywords: Chinese keywords (关键词)
        abstract_en: English abstract
        keywords_en: English keywords
        doi: DOI number
        article_id: Article ID (文章编号)
        journal_vol: Volume number (卷号)
        journal_issue: Issue number (期号)
        journal_year: Publication year (年份)
        journal_date: Publication date (日期)

    Returns:
        Dictionary of template variables
    """
    params: dict[str, str] = {}

    if journal_title:
        params["journal-title"] = journal_title
    if article_title:
        params["title"] = article_title
    if subtitle:
        params["subtitle"] = subtitle
    if author:
        params["author"] = author
    if affiliation:
        params["affiliation"] = affiliation
    if email:
        params["email"] = email
    if abstract:
        params["abstract"] = abstract
    if keywords:
        params["keywords"] = keywords
    if abstract_en:
        params["abstract-en"] = abstract_en
    if keywords_en:
        params["keywords-en"] = keywords_en
    if doi:
        params["doi"] = doi
    if article_id:
        params["article-id"] = article_id
    if journal_vol:
        params["journal-vol"] = journal_vol
    if journal_issue:
        params["journal-issue"] = journal_issue
    if journal_year:
        params["journal-year"] = journal_year
    if journal_date:
        params["journal-date"] = journal_date

    return params
