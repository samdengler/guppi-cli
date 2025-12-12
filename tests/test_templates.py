"""Tests for template loading and rendering utilities"""
import pytest
from pathlib import Path

from guppi.templates import load_template, render_template, load_and_render_template


class TestLoadTemplate:
    """Tests for load_template function"""

    def test_load_source_pyproject_template(self):
        """Test loading source pyproject.toml template"""
        content = load_template("source/pyproject.toml")
        assert "[tool.guppi.source]" in content
        assert 'name = "{name}"' in content
        assert 'description = "{description}"' in content
        assert 'version = "1.0.0"' in content

    def test_load_source_readme_template(self):
        """Test loading source README.md template"""
        content = load_template("source/README.md")
        assert "# {name}" in content
        assert "{description}" in content
        assert "GUPPI Tool Source" in content
        assert "Adding Tools" in content

    def test_load_source_gitignore_template(self):
        """Test loading source .gitignore template"""
        content = load_template("source/gitignore")
        assert "__pycache__/" in content
        assert "*.py[cod]" in content
        assert "venv/" in content
        assert ".vscode/" in content

    def test_load_nonexistent_template_raises_error(self):
        """Test that loading nonexistent template raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_template("nonexistent/template.txt")


class TestRenderTemplate:
    """Tests for render_template function"""

    def test_render_simple_template(self):
        """Test rendering simple template with variables"""
        template = "Hello, {name}!"
        result = render_template(template, name="World")
        assert result == "Hello, World!"

    def test_render_multiple_variables(self):
        """Test rendering template with multiple variables"""
        template = "{greeting}, {name}! You are {age} years old."
        result = render_template(template, greeting="Hi", name="Alice", age=30)
        assert result == "Hi, Alice! You are 30 years old."

    def test_render_template_with_repeated_variable(self):
        """Test rendering template with same variable used multiple times"""
        template = "{name} loves {name}!"
        result = render_template(template, name="Python")
        assert result == "Python loves Python!"

    def test_render_template_missing_variable_raises_error(self):
        """Test that missing variable raises KeyError"""
        template = "Hello, {name}!"
        with pytest.raises(KeyError):
            render_template(template)


class TestLoadAndRenderTemplate:
    """Tests for load_and_render_template convenience function"""

    def test_load_and_render_source_pyproject(self):
        """Test loading and rendering source pyproject.toml"""
        result = load_and_render_template(
            "source/pyproject.toml",
            name="test-source",
            description="Test tool source"
        )
        assert "[tool.guppi.source]" in result
        assert 'name = "test-source"' in result
        assert 'description = "Test tool source"' in result
        assert 'version = "1.0.0"' in result
        # Ensure no template variables remain
        assert "{name}" not in result
        assert "{description}" not in result

    def test_load_and_render_source_readme(self):
        """Test loading and rendering source README.md"""
        result = load_and_render_template(
            "source/README.md",
            name="my-tools",
            description="My personal GUPPI tools"
        )
        assert "# my-tools" in result
        assert "My personal GUPPI tools" in result
        assert "GUPPI Tool Source" in result
        # Ensure no template variables remain
        assert "{name}" not in result
        assert "{description}" not in result

    def test_load_and_render_gitignore_no_variables(self):
        """Test loading gitignore which has no template variables"""
        result = load_and_render_template("source/gitignore")
        assert "__pycache__/" in result
        assert "venv/" in result
        # Should work even with no variables provided
        assert "{" not in result  # No unrendered placeholders
