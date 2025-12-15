"""Tests for commands/uninstall.py - GUPPI CLI uninstall functionality"""
import subprocess
from types import SimpleNamespace
from pathlib import Path

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from guppi.commands.uninstall import app, uninstall
from guppi.__version__ import __version__


runner = CliRunner()


class TestUninstallCommand:
    """Tests for uninstall command"""

    def test_uninstall_callback_noop_when_subcommand(self):
        """Callback should return immediately if a subcommand is invoked"""
        ctx = SimpleNamespace(invoked_subcommand="dummy")

        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            result = uninstall(ctx, yes=False)

        assert result is None
        mock_run.assert_not_called()

    def test_uninstall_success_with_yes_flag(self):
        """Test successful uninstall with --yes flag (skips confirmation)"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Uninstalled guppi"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                result = runner.invoke(app, ["--yes"])

                assert result.exit_code == 0
                assert f"Current version: {__version__}" in result.output
                assert "This will uninstall the guppi CLI tool" in result.output
                assert "Your configuration in /Users/test/.guppi will be preserved" in result.output
                assert "guppi CLI uninstalled successfully!" in result.output
                assert "Your configuration is preserved at: /Users/test/.guppi" in result.output
                assert "To reinstall:" in result.output
                assert "uv tool install guppi" in result.output
                mock_run.assert_called_once_with(
                    ["uv", "tool", "uninstall", "guppi"],
                    check=True,
                    capture_output=True,
                    text=True
                )

    def test_uninstall_with_confirmation_yes(self):
        """Test uninstall with user confirming yes"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Uninstalled guppi"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                # Simulate user typing "y"
                result = runner.invoke(app, [], input="y\n")

                assert result.exit_code == 0
                assert "Are you sure you want to uninstall guppi?" in result.output
                assert "guppi CLI uninstalled successfully!" in result.output
                mock_run.assert_called_once()

    def test_uninstall_with_confirmation_no(self):
        """Test uninstall with user declining confirmation"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                # Simulate user typing "n"
                result = runner.invoke(app, [], input="n\n")

                assert result.exit_code == 0
                assert "Are you sure you want to uninstall guppi?" in result.output
                assert "Aborted." in result.output
                assert "uninstalled successfully" not in result.output
                mock_run.assert_not_called()

    def test_uninstall_uv_not_found(self):
        """Test uninstall when uv command is not found"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                result = runner.invoke(app, ["--yes"])

                assert result.exit_code == 1
                assert "Error: 'uv' command not found" in result.output
                assert "Please install uv first" in result.output

    def test_uninstall_subprocess_error(self):
        """Test uninstall when subprocess fails"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["uv", "tool", "uninstall", "guppi"],
                stderr="Package not found"
            )

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                result = runner.invoke(app, ["--yes"])

                assert result.exit_code == 1
                assert "Error uninstalling guppi" in result.output

    def test_uninstall_displays_current_version(self):
        """Test that uninstall displays current version before uninstalling"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                result = runner.invoke(app, ["--yes"])

                assert f"Current version: {__version__}" in result.output

    def test_uninstall_displays_uv_output(self):
        """Test that uninstall displays output from uv"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Removed guppi from /path/to/bin"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                result = runner.invoke(app, ["--yes"])

                assert result.exit_code == 0
                assert "Removed guppi from /path/to/bin" in result.output

    def test_uninstall_uses_correct_uv_command(self):
        """Test that uninstall uses correct uv command"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                runner.invoke(app, ["--yes"])

                # Verify exact command
                call_args = mock_run.call_args
                assert call_args[0][0] == ["uv", "tool", "uninstall", "guppi"]
                assert call_args[1]["check"] is True
                assert call_args[1]["capture_output"] is True
                assert call_args[1]["text"] is True

    def test_uninstall_help_shows_description(self):
        """Test that --help shows uninstall description"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Uninstall guppi CLI" in result.output

    def test_uninstall_short_yes_flag(self):
        """Test that -y flag works as shorthand for --yes"""
        with patch("guppi.commands.uninstall.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            with patch("guppi.commands.uninstall.get_guppi_home") as mock_home:
                mock_home.return_value = Path("/Users/test/.guppi")

                result = runner.invoke(app, ["-y"])

                assert result.exit_code == 0
                # Should not show confirmation prompt
                assert "Are you sure" not in result.output
                assert "guppi CLI uninstalled successfully!" in result.output
                mock_run.assert_called_once()
