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

