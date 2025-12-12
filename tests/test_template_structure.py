"""Tests for template directory structure validation"""
import pytest
from pathlib import Path
from importlib.resources import files


class TestSourceTemplateStructure:
    """Tests for source template directory structure"""

    def test_source_template_directory_exists(self):
        """Test that source template directory exists"""
        template_files = files("guppi.templates")
        source_dir = template_files / "source"
        assert source_dir.is_dir(), "source template directory should exist"

    def test_source_pyproject_template_exists(self):
        """Test that source pyproject.toml template exists"""
        template_files = files("guppi.templates")
        pyproject = template_files / "source" / "pyproject.toml"
        assert pyproject.is_file(), "source/pyproject.toml template should exist"

    def test_source_readme_template_exists(self):
        """Test that source README.md template exists"""
        template_files = files("guppi.templates")
        readme = template_files / "source" / "README.md"
        assert readme.is_file(), "source/README.md template should exist"

    def test_source_gitignore_template_exists(self):
        """Test that source gitignore template exists"""
        template_files = files("guppi.templates")
        gitignore = template_files / "source" / "gitignore"
        assert gitignore.is_file(), "source/gitignore template should exist"

    def test_source_pyproject_has_required_sections(self):
        """Test that source pyproject.toml has required TOML structure"""
        template_files = files("guppi.templates")
        pyproject = template_files / "source" / "pyproject.toml"
        content = pyproject.read_text()

        # Check for required sections
        assert "[tool.guppi.source]" in content
        assert "name =" in content
        assert "description =" in content
        assert "version =" in content

    def test_source_readme_has_required_sections(self):
        """Test that source README.md has required sections"""
        template_files = files("guppi.templates")
        readme = template_files / "source" / "README.md"
        content = readme.read_text()

        # Check for required sections
        assert "# {name}" in content or "#{name}" in content
        assert "GUPPI Tool Source" in content
        assert "Adding Tools" in content

    def test_source_gitignore_has_python_patterns(self):
        """Test that source gitignore includes Python patterns"""
        template_files = files("guppi.templates")
        gitignore = template_files / "source" / "gitignore"
        content = gitignore.read_text()

        # Check for common Python patterns
        assert "__pycache__" in content
        assert "*.py[cod]" in content or "*.pyc" in content
        assert "venv/" in content or "env/" in content


class TestExampleToolTemplateStructure:
    """Tests for example-tool template directory structure"""

    def test_example_tool_directory_exists(self):
        """Test that example-tool template directory exists"""
        template_files = files("guppi.templates")
        example_dir = template_files / "example-tool"
        assert example_dir.is_dir(), "example-tool template directory should exist"

    def test_example_tool_pyproject_exists(self):
        """Test that example-tool pyproject.toml exists"""
        template_files = files("guppi.templates")
        pyproject = template_files / "example-tool" / "pyproject.toml"
        assert pyproject.is_file(), "example-tool/pyproject.toml should exist"

    def test_example_tool_readme_exists(self):
        """Test that example-tool README.md exists"""
        template_files = files("guppi.templates")
        readme = template_files / "example-tool" / "README.md"
        assert readme.is_file(), "example-tool/README.md should exist"

    def test_example_tool_src_directory_exists(self):
        """Test that example-tool src directory exists"""
        template_files = files("guppi.templates")
        src_dir = template_files / "example-tool" / "src"
        assert src_dir.is_dir(), "example-tool/src directory should exist"

    def test_example_tool_package_directory_exists(self):
        """Test that example-tool package directory exists"""
        template_files = files("guppi.templates")
        pkg_dir = template_files / "example-tool" / "src" / "guppi_example"
        assert pkg_dir.is_dir(), "example-tool/src/guppi_example directory should exist"

    def test_example_tool_init_exists(self):
        """Test that example-tool __init__.py exists"""
        template_files = files("guppi.templates")
        init_file = template_files / "example-tool" / "src" / "guppi_example" / "__init__.py"
        assert init_file.is_file(), "example-tool/src/guppi_example/__init__.py should exist"

    def test_example_tool_cli_exists(self):
        """Test that example-tool cli.py exists"""
        template_files = files("guppi.templates")
        cli_file = template_files / "example-tool" / "src" / "guppi_example" / "cli.py"
        assert cli_file.is_file(), "example-tool/src/guppi_example/cli.py should exist"

    def test_example_tool_pyproject_has_guppi_metadata(self):
        """Test that example-tool pyproject.toml has [tool.guppi] metadata"""
        template_files = files("guppi.templates")
        pyproject = template_files / "example-tool" / "pyproject.toml"
        content = pyproject.read_text()

        # Check for GUPPI metadata
        assert "[tool.guppi]" in content
        assert "name =" in content
        assert "description =" in content

    def test_example_tool_pyproject_has_project_metadata(self):
        """Test that example-tool pyproject.toml has [project] metadata"""
        template_files = files("guppi.templates")
        pyproject = template_files / "example-tool" / "pyproject.toml"
        content = pyproject.read_text()

        # Check for project metadata
        assert "[project]" in content
        assert "name =" in content
        assert "version =" in content
        assert "dependencies =" in content

    def test_example_tool_cli_has_typer_app(self):
        """Test that example-tool cli.py uses typer"""
        template_files = files("guppi.templates")
        cli_file = template_files / "example-tool" / "src" / "guppi_example" / "cli.py"
        content = cli_file.read_text()

        # Check for typer usage
        assert "import typer" in content
        assert "app = typer.Typer" in content or "app=typer.Typer" in content
