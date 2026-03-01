"""Unit tests for template system."""

from __future__ import annotations

from md2pdf_pro.templates import (
    BuiltinTemplate,
    get_template,
    list_templates,
    validate_template,
)


class TestBuiltinTemplate:
    """Tests for BuiltinTemplate enum."""

    def test_template_values(self):
        """Test template values."""
        assert BuiltinTemplate.DEFAULT.value == "default"
        assert BuiltinTemplate.ACADEMIC.value == "academic"
        assert BuiltinTemplate.REPORT.value == "report"
        assert BuiltinTemplate.MINIMAL.value == "minimal"


class TestListTemplates:
    """Tests for list_templates function."""

    def test_returns_list(self):
        """Test that list_templates returns a list."""
        templates = list_templates()
        assert isinstance(templates, list)

    def test_contains_default(self):
        """Test that default template is listed."""
        templates = list_templates()
        names = [t.name for t in templates]
        assert "default" in names


class TestGetTemplate:
    """Tests for get_template function."""

    def test_get_default_template(self):
        """Test getting default template."""
        path = get_template("default")
        assert path is not None
        assert path.exists()


class TestValidateTemplate:
    """Tests for validate_template function."""

    def test_validate_nonexistent(self):
        """Test validating nonexistent file."""
        from pathlib import Path

        result = validate_template(Path("/nonexistent/template.latex"))
        assert result is False
