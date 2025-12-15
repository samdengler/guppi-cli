"""Tests for template loading and rendering utilities"""
import pytest
from pathlib import Path

from guppi.templates import load_template, render_template, load_and_render_template, sanitize_tool_name, tool_name_to_package


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


class TestSanitizeToolName:
    """Tests for sanitize_tool_name function"""

    def test_sanitize_simple_name(self):
        """Test sanitizing a simple name"""
        assert sanitize_tool_name("MyTool") == "mytool"
        assert sanitize_tool_name("hello") == "hello"

    def test_sanitize_name_with_spaces(self):
        """Test sanitizing names with spaces"""
        assert sanitize_tool_name("My Tool") == "my-tool"
        assert sanitize_tool_name("API Service") == "api-service"

    def test_sanitize_name_with_underscores(self):
        """Test sanitizing names with underscores"""
        assert sanitize_tool_name("api_service") == "api-service"
        assert sanitize_tool_name("my_awesome_tool") == "my-awesome-tool"

    def test_sanitize_name_with_mixed_separators(self):
        """Test sanitizing names with mixed separators"""
        assert sanitize_tool_name("Tool-Name_123") == "tool-name-123"
        assert sanitize_tool_name("my tool_name-here") == "my-tool-name-here"

    def test_sanitize_name_with_special_characters(self):
        """Test sanitizing names with special characters"""
        assert sanitize_tool_name("my@tool!") == "my-tool"
        assert sanitize_tool_name("tool#123$") == "tool-123"
        assert sanitize_tool_name("api.service") == "api-service"

    def test_sanitize_name_collapses_multiple_hyphens(self):
        """Test that multiple consecutive hyphens are collapsed"""
        assert sanitize_tool_name("--Multiple---Hyphens--") == "multiple-hyphens"
        assert sanitize_tool_name("my----tool") == "my-tool"

    def test_sanitize_name_strips_leading_trailing_hyphens(self):
        """Test that leading and trailing hyphens are stripped"""
        assert sanitize_tool_name("-tool-") == "tool"
        assert sanitize_tool_name("---leading") == "leading"
        assert sanitize_tool_name("trailing---") == "trailing"

    def test_sanitize_preserves_existing_hyphens(self):
        """Test that existing hyphens are preserved"""
        assert sanitize_tool_name("my-tool") == "my-tool"
        assert sanitize_tool_name("api-service-v2") == "api-service-v2"

    def test_sanitize_preserves_numbers(self):
        """Test that numbers are preserved"""
        assert sanitize_tool_name("tool123") == "tool123"
        assert sanitize_tool_name("v2-api") == "v2-api"

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string"""
        assert sanitize_tool_name("") == ""
        assert sanitize_tool_name("---") == ""


class TestToolNameToPackage:
    """Tests for tool_name_to_package function"""

    def test_convert_simple_name(self):
        """Test converting simple hyphenated name"""
        assert tool_name_to_package("my-tool") == "my_tool"
        assert tool_name_to_package("api-service") == "api_service"

    def test_convert_name_with_multiple_hyphens(self):
        """Test converting name with multiple hyphens"""
        assert tool_name_to_package("my-awesome-tool") == "my_awesome_tool"
        assert tool_name_to_package("api-service-v2") == "api_service_v2"

    def test_convert_name_without_hyphens(self):
        """Test converting name without hyphens (no change expected)"""
        assert tool_name_to_package("mytool") == "mytool"
        assert tool_name_to_package("tool123") == "tool123"

    def test_convert_preserves_numbers(self):
        """Test that numbers are preserved"""
        assert tool_name_to_package("tool-123") == "tool_123"
        assert tool_name_to_package("v2-api") == "v2_api"

    def test_sanitize_and_convert_together(self):
        """Test sanitize and convert work together correctly"""
        name = "My Tool Name"
        sanitized = sanitize_tool_name(name)
        package = tool_name_to_package(sanitized)
        assert sanitized == "my-tool-name"
        assert package == "my_tool_name"

