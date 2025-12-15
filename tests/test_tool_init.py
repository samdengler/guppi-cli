"""Integration tests for guppi tool init command"""
import pytest
from pathlib import Path
from typer.testing import CliRunner

from guppi.commands.tool import app


runner = CliRunner()


class TestToolInit:
    """Integration tests for tool init command"""

    def test_init_minimal_template(self, mock_source_directory):
        """Test initializing tool with minimal template"""
        result = runner.invoke(
            app,
            ["init", str(mock_source_directory), "my-tool", "--description", "My test tool"]
        )

        assert result.exit_code == 0
        assert "Initialized GUPPI tool 'my-tool'" in result.stdout

        tool_dir = mock_source_directory / "my-tool"
        assert tool_dir.exists()

        # Check all expected files were created
        assert (tool_dir / "pyproject.toml").exists()
        assert (tool_dir / "README.md").exists()
        assert (tool_dir / ".gitignore").exists()
        assert (tool_dir / "src" / "guppi_my_tool" / "__init__.py").exists()
        assert (tool_dir / "src" / "guppi_my_tool" / "cli.py").exists()

        # Verify pyproject.toml content
        pyproject_content = (tool_dir / "pyproject.toml").read_text()
        assert 'name = "guppi-my-tool"' in pyproject_content
        assert 'description = "My test tool"' in pyproject_content
        assert 'guppi-my-tool = "guppi_my_tool.cli:app"' in pyproject_content
        assert '[tool.guppi]' in pyproject_content
        assert 'name = "my-tool"' in pyproject_content

        # Verify CLI content (minimal template)
        cli_content = (tool_dir / "src" / "guppi_my_tool" / "cli.py").read_text()
        assert "import typer" in cli_content
        assert 'app = typer.Typer(help="My test tool")' in cli_content
        assert "def hello" in cli_content

        # Verify __init__.py
        init_content = (tool_dir / "src" / "guppi_my_tool" / "__init__.py").read_text()
        assert '__version__ = "0.1.0"' in init_content
        assert 'GUPPI my-tool tool' in init_content

    def test_init_example_template(self, mock_source_directory):
        """Test initializing tool with example template"""
        result = runner.invoke(
            app,
            [
                "init",
                str(mock_source_directory),
                "example-tool",
                "--description",
                "Example with features",
                "--template",
                "example"
            ]
        )

        assert result.exit_code == 0

        tool_dir = mock_source_directory / "example-tool"
        cli_content = (tool_dir / "src" / "guppi_example_tool" / "cli.py").read_text()

        # Example template should have more features
        assert "from typing_extensions import Annotated" in cli_content
        assert "def hello" in cli_content
        assert "def info" in cli_content
        assert "--excited" in cli_content

    def test_init_sanitizes_tool_name(self, mock_source_directory):
        """Test that tool name is sanitized properly"""
        result = runner.invoke(
            app,
            ["init", str(mock_source_directory), "My Tool Name!", "--description", "Test"]
        )

        assert result.exit_code == 0
        assert "Tool name sanitized: 'My Tool Name!' → 'my-tool-name'" in result.stdout

        # Check that sanitized name was used
        tool_dir = mock_source_directory / "my-tool-name"
        assert tool_dir.exists()
        assert (tool_dir / "src" / "guppi_my_tool_name").exists()

        pyproject_content = (tool_dir / "pyproject.toml").read_text()
        assert 'name = "guppi-my-tool-name"' in pyproject_content
        assert 'guppi-my-tool-name = "guppi_my_tool_name.cli:app"' in pyproject_content

    def test_init_with_default_description(self, mock_source_directory):
        """Test that default description is used when not provided"""
        result = runner.invoke(app, ["init", str(mock_source_directory), "test-tool"])

        assert result.exit_code == 0

        tool_dir = mock_source_directory / "test-tool"
        pyproject_content = (tool_dir / "pyproject.toml").read_text()
        assert 'description = "A GUPPI tool"' in pyproject_content

    def test_init_no_git(self, mock_source_directory):
        """Test initializing tool without git repository"""
        result = runner.invoke(
            app,
            ["init", str(mock_source_directory), "no-git-tool", "--no-git"]
        )

        assert result.exit_code == 0

        tool_dir = mock_source_directory / "no-git-tool"
        # Git directory should not exist
        assert not (tool_dir / ".git").exists()

    def test_init_with_git(self, mock_source_directory):
        """Test initializing tool with git repository (default)"""
        result = runner.invoke(
            app,
            ["init", str(mock_source_directory), "git-tool"]
        )

        assert result.exit_code == 0
        assert "Initialized git repository" in result.stdout

        tool_dir = mock_source_directory / "git-tool"
        # Git directory should exist
        assert (tool_dir / ".git").exists()

    def test_init_error_source_directory_not_exists(self, temp_dir):
        """Test error when source directory doesn't exist"""
        non_existent = temp_dir / "nonexistent"

        result = runner.invoke(app, ["init", str(non_existent), "my-tool"])

        assert result.exit_code == 1
        # Error messages go to stderr (err=True in typer.echo)
        output = result.stdout + result.stderr
        assert "Error: Source directory does not exist" in output

    def test_init_error_not_valid_source(self, temp_dir):
        """Test error when directory is not a valid GUPPI source"""
        # temp_dir exists but is not a valid GUPPI source
        result = runner.invoke(app, ["init", str(temp_dir), "my-tool"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error: Not a valid GUPPI source" in output
        assert "guppi tool source init" in output

    def test_init_error_tool_already_exists(self, mock_source_directory):
        """Test error when tool directory already exists"""
        # Create a tool first
        existing_tool = mock_source_directory / "existing-tool"
        existing_tool.mkdir()

        result = runner.invoke(app, ["init", str(mock_source_directory), "existing-tool"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error: Tool directory already exists" in output
        assert "Remove it first or choose a different name" in output

    def test_init_error_invalid_name_after_sanitization(self, mock_source_directory):
        """Test error when tool name becomes invalid after sanitization"""
        # Name that becomes empty after sanitization (using @@@ instead of --- to avoid Typer flag parsing)
        result = runner.invoke(app, ["init", str(mock_source_directory), "@@@"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error: Tool name '@@@' is invalid after sanitization" in output

    def test_init_creates_correct_package_structure(self, mock_source_directory):
        """Test that package structure is created correctly"""
        result = runner.invoke(app, ["init", str(mock_source_directory), "api-service"])

        assert result.exit_code == 0

        tool_dir = mock_source_directory / "api-service"
        package_dir = tool_dir / "src" / "guppi_api_service"

        # Check package structure
        assert package_dir.exists()
        assert package_dir.is_dir()
        assert (package_dir / "__init__.py").exists()
        assert (package_dir / "cli.py").exists()

        # Verify imports work correctly in cli.py
        cli_content = (package_dir / "cli.py").read_text()
        assert "import typer" in cli_content

    def test_init_readme_content(self, mock_source_directory):
        """Test that README.md has correct content"""
        result = runner.invoke(
            app,
            ["init", str(mock_source_directory), "readme-tool", "--description", "Tool for testing README"]
        )

        assert result.exit_code == 0

        tool_dir = mock_source_directory / "readme-tool"
        readme_content = (tool_dir / "README.md").read_text()

        # Check README contains expected sections
        assert "# GUPPI readme-tool" in readme_content
        assert "Tool for testing README" in readme_content
        assert "## Installation" in readme_content
        assert "## Usage" in readme_content
        assert "guppi readme-tool --help" in readme_content

    def test_init_gitignore_content(self, mock_source_directory):
        """Test that .gitignore has Python-specific content"""
        result = runner.invoke(app, ["init", str(mock_source_directory), "gitignore-tool"])

        assert result.exit_code == 0

        tool_dir = mock_source_directory / "gitignore-tool"
        gitignore_content = (tool_dir / ".gitignore").read_text()

        # Check for Python-specific entries
        assert "__pycache__/" in gitignore_content
        assert "*.py[cod]" in gitignore_content
        assert "venv/" in gitignore_content
        assert ".venv/" in gitignore_content

    def test_init_multiple_tools_in_same_source(self, mock_source_directory):
        """Test creating multiple tools in the same source directory"""
        # Create first tool
        result1 = runner.invoke(app, ["init", str(mock_source_directory), "tool-one"])
        assert result1.exit_code == 0

        # Create second tool
        result2 = runner.invoke(app, ["init", str(mock_source_directory), "tool-two"])
        assert result2.exit_code == 0

        # Both should exist
        assert (mock_source_directory / "tool-one").exists()
        assert (mock_source_directory / "tool-two").exists()

    def test_init_success_message_shows_next_steps(self, mock_source_directory):
        """Test that success message includes helpful next steps"""
        result = runner.invoke(app, ["init", str(mock_source_directory), "help-tool"])

        assert result.exit_code == 0
        assert "Next steps:" in result.stdout
        assert "Edit src/guppi_help_tool/cli.py" in result.stdout
        assert "guppi tool install help-tool" in result.stdout
        assert "guppi help-tool --help" in result.stdout

    def test_init_preserves_hyphens_in_name(self, mock_source_directory):
        """Test that hyphens in tool names are preserved"""
        result = runner.invoke(app, ["init", str(mock_source_directory), "my-cool-tool"])

        assert result.exit_code == 0

        tool_dir = mock_source_directory / "my-cool-tool"
        assert tool_dir.exists()

        # Package name should use underscores
        assert (tool_dir / "src" / "guppi_my_cool_tool").exists()

        pyproject_content = (tool_dir / "pyproject.toml").read_text()
        assert 'name = "guppi-my-cool-tool"' in pyproject_content
        assert 'name = "my-cool-tool"' in pyproject_content
        assert 'guppi-my-cool-tool = "guppi_my_cool_tool.cli:app"' in pyproject_content

    def test_init_version_in_init_file(self, mock_source_directory):
        """Test that __init__.py contains version"""
        result = runner.invoke(app, ["init", str(mock_source_directory), "version-tool"])

        assert result.exit_code == 0

        init_file = mock_source_directory / "version-tool" / "src" / "guppi_version_tool" / "__init__.py"
        init_content = init_file.read_text()

        assert "__version__" in init_content
        assert '"0.1.0"' in init_content
