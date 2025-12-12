"""Integration tests for guppi tool source init command"""
import pytest
from pathlib import Path
from typer.testing import CliRunner

from guppi.commands.tool import source_app


runner = CliRunner()


class TestSourceInit:
    """Integration tests for source init command"""

    def test_init_minimal_in_temp_directory(self, temp_dir):
        """Test initializing minimal source in a temporary directory"""
        result = runner.invoke(source_app, ["init", str(temp_dir), "--name", "test-source"])

        assert result.exit_code == 0
        assert "Initialized GUPPI tool source 'test-source'" in result.stdout

        # Check files were created
        assert (temp_dir / "pyproject.toml").exists()
        assert (temp_dir / "README.md").exists()
        assert (temp_dir / ".gitignore").exists()

        # Verify content
        pyproject_content = (temp_dir / "pyproject.toml").read_text()
        assert "[tool.guppi.source]" in pyproject_content
        assert 'name = "test-source"' in pyproject_content

    def test_init_with_description(self, temp_dir):
        """Test initializing source with custom description"""
        result = runner.invoke(
            source_app,
            ["init", str(temp_dir), "--name", "my-tools", "--description", "My personal tools"]
        )

        assert result.exit_code == 0

        pyproject_content = (temp_dir / "pyproject.toml").read_text()
        assert 'description = "My personal tools"' in pyproject_content

    def test_init_current_directory(self, temp_dir, monkeypatch):
        """Test initializing source in current directory"""
        # Change to temp directory
        monkeypatch.chdir(temp_dir)

        result = runner.invoke(source_app, ["init", "--name", "test-source"])

        assert result.exit_code == 0
        assert (temp_dir / "pyproject.toml").exists()

    def test_init_uses_directory_name_if_no_name(self, temp_dir):
        """Test that directory name is used if --name not provided"""
        source_dir = temp_dir / "my-awesome-tools"
        source_dir.mkdir()

        result = runner.invoke(source_app, ["init", str(source_dir)])

        assert result.exit_code == 0

        pyproject_content = (source_dir / "pyproject.toml").read_text()
        assert 'name = "my-awesome-tools"' in pyproject_content

    def test_init_sanitizes_name(self, temp_dir):
        """Test that invalid characters in name are sanitized"""
        result = runner.invoke(
            source_app,
            ["init", str(temp_dir), "--name", "my tools & stuff!"]
        )

        assert result.exit_code == 0

        pyproject_content = (temp_dir / "pyproject.toml").read_text()
        # Should have spaces converted to dashes, special chars removed
        assert 'name = "my-tools-stuff"' in pyproject_content

    def test_init_non_empty_directory_prompts_user(self, temp_dir):
        """Test that initializing non-empty directory prompts for confirmation"""
        # Create a file to make directory non-empty
        (temp_dir / "existing.txt").write_text("existing file")

        # Simulate user saying "no"
        result = runner.invoke(
            source_app,
            ["init", str(temp_dir), "--name", "test"],
            input="n\n"
        )

        assert result.exit_code == 0
        assert "Aborted" in result.stdout
        # pyproject.toml should NOT be created
        assert not (temp_dir / "pyproject.toml").exists()

    def test_init_non_empty_directory_user_confirms(self, temp_dir):
        """Test that user can confirm initialization in non-empty directory"""
        # Create a file to make directory non-empty
        (temp_dir / "existing.txt").write_text("existing file")

        # Simulate user saying "yes"
        result = runner.invoke(
            source_app,
            ["init", str(temp_dir), "--name", "test"],
            input="y\n"
        )

        assert result.exit_code == 0
        # Should proceed with initialization
        assert (temp_dir / "pyproject.toml").exists()

    def test_init_already_valid_source_errors(self, temp_dir, sample_source_pyproject_toml):
        """Test that initializing already-valid source directory errors"""
        # Make it a valid source first
        (temp_dir / "pyproject.toml").write_text(sample_source_pyproject_toml)

        result = runner.invoke(source_app, ["init", str(temp_dir), "--name", "test"])

        assert result.exit_code == 1
        assert "already a GUPPI tool source" in result.output

    def test_init_with_no_git(self, temp_dir):
        """Test initializing without git initialization"""
        result = runner.invoke(
            source_app,
            ["init", str(temp_dir), "--name", "test", "--no-git"]
        )

        assert result.exit_code == 0
        assert (temp_dir / "pyproject.toml").exists()
        # .git directory should NOT exist
        assert not (temp_dir / ".git").exists()

    def test_init_with_git_creates_repo(self, temp_dir):
        """Test that git initialization creates repository"""
        result = runner.invoke(
            source_app,
            ["init", str(temp_dir), "--name", "test", "--git"]
        )

        assert result.exit_code == 0
        # .git directory should exist
        assert (temp_dir / ".git").exists()

    def test_init_creates_directory_if_not_exists(self, temp_dir):
        """Test that init creates directory if it doesn't exist"""
        new_dir = temp_dir / "new-source"
        assert not new_dir.exists()

        result = runner.invoke(source_app, ["init", str(new_dir), "--name", "test"])

        assert result.exit_code == 0
        assert new_dir.exists()
        assert (new_dir / "pyproject.toml").exists()

    def test_init_expands_tilde_in_path(self, temp_dir, monkeypatch):
        """Test that ~ is expanded in directory path"""
        # Mock home directory
        monkeypatch.setenv("HOME", str(temp_dir))

        result = runner.invoke(
            source_app,
            ["init", "~/test-source", "--name", "test"]
        )

        assert result.exit_code == 0
        expected_path = temp_dir / "test-source"
        assert expected_path.exists()
        assert (expected_path / "pyproject.toml").exists()

    def test_init_shows_next_steps(self, temp_dir):
        """Test that success message shows helpful next steps"""
        result = runner.invoke(source_app, ["init", str(temp_dir), "--name", "test"])

        assert result.exit_code == 0
        assert "Next steps:" in result.stdout
        assert "Add tools to this source" in result.stdout
        assert "guppi tool source add" in result.stdout

    def test_init_creates_valid_toml_file(self, temp_dir):
        """Test that created pyproject.toml is valid TOML"""
        import tomllib

        result = runner.invoke(source_app, ["init", str(temp_dir), "--name", "test"])

        assert result.exit_code == 0

        # Should be parseable as TOML
        pyproject_path = temp_dir / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Check structure
        assert "tool" in data
        assert "guppi" in data["tool"]
        assert "source" in data["tool"]["guppi"]
        assert data["tool"]["guppi"]["source"]["name"] == "test"
        assert data["tool"]["guppi"]["source"]["version"] == "1.0.0"
