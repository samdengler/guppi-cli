"""Tests for commands/update.py - GUPPI CLI update functionality"""
from types import SimpleNamespace

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from guppi.commands.update import app, update
from guppi.__version__ import __version__


runner = CliRunner()


class TestUpdateCommand:
    """Tests for update command"""

    def test_update_callback_noop_when_subcommand(self):
        """Callback should return immediately if a subcommand is invoked"""
        ctx = SimpleNamespace(invoked_subcommand="dummy")

        with patch("guppi.commands.update.subprocess.run") as mock_run:
            result = update(ctx)

        assert result is None
        mock_run.assert_not_called()

    def test_update_success(self):
        """Test successful update with version change"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Updated guppi from 1.0.0 to 1.1.0"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = runner.invoke(app, [])

            assert result.exit_code == 0
            assert f"Current version: {__version__}" in result.output
            assert "Checking for updates..." in result.output
            assert "guppi updated successfully!" in result.output
            assert "Run 'guppi --version' to see the new version" in result.output
            mock_run.assert_called_once_with(
                ["uv", "tool", "upgrade", "guppi"],
                check=True,
                capture_output=True,
                text=True
            )

    def test_update_already_up_to_date(self):
        """Test update when already at latest version"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Nothing to upgrade"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = runner.invoke(app, [])

            assert result.exit_code == 0
            assert f"Current version: {__version__}" in result.output
            assert f"guppi is already up-to-date (version {__version__})" in result.output
            assert "guppi updated successfully!" not in result.output

    def test_update_shows_current_version(self):
        """Test that update shows current version before upgrading"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Nothing to update"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = runner.invoke(app, [])

            assert f"Current version: {__version__}" in result.output
            assert "Checking for updates..." in result.output

    def test_update_uv_not_found(self):
        """Test update when uv command is not found"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = runner.invoke(app, [])

            assert result.exit_code == 1
            assert "Error: 'uv' command not found" in result.output
            assert "Please install uv first" in result.output

    def test_update_subprocess_error(self):
        """Test update when subprocess fails"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["uv", "tool", "upgrade", "guppi"],
                stderr="Network error"
            )

            result = runner.invoke(app, [])

            assert result.exit_code == 1
            assert "Error updating guppi" in result.output

    def test_update_with_output_in_stderr(self):
        """Test update with output in stderr (some tools output to stderr)"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = "Updated guppi from 1.0.0 to 1.1.0"
            mock_run.return_value = mock_result

            result = runner.invoke(app, [])

            assert result.exit_code == 0
            assert "guppi updated successfully!" in result.output

    def test_update_displays_uv_output(self):
        """Test that update displays output from uv"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Downloading guppi 1.2.0\nInstalling guppi 1.2.0"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = runner.invoke(app, [])

            assert result.exit_code == 0
            assert "Downloading guppi 1.2.0" in result.output
            assert "Installing guppi 1.2.0" in result.output
            assert "guppi updated successfully!" in result.output

    def test_update_with_empty_output(self):
        """Test update with empty output but successful completion"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = runner.invoke(app, [])

            assert result.exit_code == 0
            assert "guppi updated successfully!" in result.output

    def test_update_uses_uv_tool_update(self):
        """Test that update uses correct uv command"""
        with patch("guppi.commands.update.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Nothing to update"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            runner.invoke(app, [])

            # Verify exact command
            call_args = mock_run.call_args
            assert call_args[0][0] == ["uv", "tool", "upgrade", "guppi"]
            assert call_args[1]["check"] is True
            assert call_args[1]["capture_output"] is True
            assert call_args[1]["text"] is True

    def test_update_help_shows_description(self):
        """Test that --help shows update description"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Update guppi CLI" in result.output


# Import subprocess for the test
import subprocess
