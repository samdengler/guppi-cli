"""Tests for tool uninstall command"""
import subprocess
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from guppi.commands.tool import app


runner = CliRunner()


class TestToolUninstall:
    """Tests for tool uninstall command"""

    def test_uninstall_basic_with_yes_flag(self):
        """Test basic uninstall with --yes flag (no confirmation)"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            # Mock uv tool list
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\nguppi-other v2.0.0\n"
            list_result.returncode = 0
            
            # Mock uv tool uninstall
            uninstall_result = MagicMock()
            uninstall_result.stdout = "Uninstalled guppi-dummy"
            uninstall_result.stderr = ""
            uninstall_result.returncode = 0
            
            mock_run.side_effect = [list_result, uninstall_result]
            
            result = runner.invoke(app, ["uninstall", "dummy", "--yes"])
            
            assert result.exit_code == 0
            assert "Uninstalling guppi-dummy" in result.output
            assert "uninstalled successfully" in result.output
            
            # Verify correct calls
            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                ["uv", "tool", "list"],
                capture_output=True,
                text=True,
                check=True
            )
            mock_run.assert_any_call(
                ["uv", "tool", "uninstall", "guppi-dummy"],
                check=True,
                capture_output=True,
                text=True
            )

    def test_uninstall_with_guppi_prefix(self):
        """Test uninstall accepts full tool name with guppi- prefix"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\n"
            list_result.returncode = 0
            
            uninstall_result = MagicMock()
            uninstall_result.stdout = ""
            uninstall_result.stderr = ""
            uninstall_result.returncode = 0
            
            mock_run.side_effect = [list_result, uninstall_result]
            
            result = runner.invoke(app, ["uninstall", "guppi-dummy", "--yes"])
            
            assert result.exit_code == 0
            assert "guppi-dummy" in result.output
            assert "uninstalled successfully" in result.output

    def test_uninstall_without_guppi_prefix(self):
        """Test uninstall normalizes name without guppi- prefix"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\n"
            list_result.returncode = 0
            
            uninstall_result = MagicMock()
            uninstall_result.stdout = ""
            uninstall_result.stderr = ""
            uninstall_result.returncode = 0
            
            mock_run.side_effect = [list_result, uninstall_result]
            
            result = runner.invoke(app, ["uninstall", "dummy", "--yes"])
            
            assert result.exit_code == 0
            # Should uninstall guppi-dummy even though we passed "dummy"
            mock_run.assert_any_call(
                ["uv", "tool", "uninstall", "guppi-dummy"],
                check=True,
                capture_output=True,
                text=True
            )

    def test_uninstall_tool_not_installed(self):
        """Test uninstall error when tool is not installed"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-other v1.0.0\n"
            list_result.returncode = 0
            mock_run.return_value = list_result
            
            result = runner.invoke(app, ["uninstall", "nonexistent", "--yes"])
            
            assert result.exit_code == 1
            assert "not installed" in result.output
            assert "guppi tool list" in result.output
            
            # Should only call list, not uninstall
            assert mock_run.call_count == 1

    def test_uninstall_confirmation_prompt_accepts(self):
        """Test confirmation prompt when --yes is not provided"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\n"
            list_result.returncode = 0
            
            uninstall_result = MagicMock()
            uninstall_result.stdout = ""
            uninstall_result.stderr = ""
            uninstall_result.returncode = 0
            
            mock_run.side_effect = [list_result, uninstall_result]
            
            # Simulate user confirming with 'y'
            result = runner.invoke(app, ["uninstall", "dummy"], input="y\n")
            
            assert result.exit_code == 0
            assert "This will uninstall: guppi-dummy" in result.output
            assert "Are you sure?" in result.output
            assert "uninstalled successfully" in result.output

    def test_uninstall_confirmation_prompt_declines(self):
        """Test confirmation prompt when user declines"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\n"
            list_result.returncode = 0
            mock_run.return_value = list_result
            
            # Simulate user declining with 'n'
            result = runner.invoke(app, ["uninstall", "dummy"], input="n\n")
            
            assert result.exit_code == 0
            assert "This will uninstall: guppi-dummy" in result.output
            assert "Aborted" in result.output
            
            # Should only call list, not uninstall (user declined)
            assert mock_run.call_count == 1

    def test_uninstall_uv_not_found(self):
        """Test error when uv command is not found"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = runner.invoke(app, ["uninstall", "dummy", "--yes"])
            
            assert result.exit_code == 1
            assert "uv" in result.output
            assert "not found" in result.output

    def test_uninstall_subprocess_error_on_list(self):
        """Test error when listing tools fails"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["uv", "tool", "list"],
                stderr="Permission denied"
            )
            
            result = runner.invoke(app, ["uninstall", "dummy", "--yes"])
            
            assert result.exit_code == 1
            assert "Error listing installed tools" in result.output

    def test_uninstall_subprocess_error_on_uninstall(self):
        """Test error when uninstall command fails"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\n"
            list_result.returncode = 0
            
            uninstall_error = subprocess.CalledProcessError(
                returncode=1,
                cmd=["uv", "tool", "uninstall", "guppi-dummy"],
                stderr="Failed to uninstall"
            )
            
            mock_run.side_effect = [list_result, uninstall_error]
            
            result = runner.invoke(app, ["uninstall", "dummy", "--yes"])
            
            assert result.exit_code == 1
            assert "Error uninstalling" in result.output

    def test_uninstall_displays_uv_output(self):
        """Test that uninstall displays output from uv"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\n"
            list_result.returncode = 0
            
            uninstall_result = MagicMock()
            uninstall_result.stdout = "Removing guppi-dummy executables"
            uninstall_result.stderr = "Cleanup complete"
            uninstall_result.returncode = 0
            
            mock_run.side_effect = [list_result, uninstall_result]
            
            result = runner.invoke(app, ["uninstall", "dummy", "--yes"])
            
            assert result.exit_code == 0
            assert "Removing guppi-dummy executables" in result.output
            assert "Cleanup complete" in result.output

    def test_uninstall_parses_tool_list_correctly(self):
        """Test that tool list parsing handles various formats"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            # Simulate various tool list formats
            list_result = MagicMock()
            list_result.stdout = """
guppi-dummy v1.0.0 (from git+https://...)
guppi-other v2.0.0
some-other-tool v1.0.0
guppi-third
"""
            list_result.returncode = 0
            
            uninstall_result = MagicMock()
            uninstall_result.stdout = ""
            uninstall_result.stderr = ""
            uninstall_result.returncode = 0
            
            mock_run.side_effect = [list_result, uninstall_result]
            
            result = runner.invoke(app, ["uninstall", "dummy", "--yes"])
            
            assert result.exit_code == 0
            # Should find guppi-dummy despite extra info in the line
            assert "uninstalled successfully" in result.output

    def test_uninstall_help_message(self):
        """Test that help message displays correctly"""
        result = runner.invoke(app, ["uninstall", "--help"])
        
        assert result.exit_code == 0
        assert "Uninstall a GUPPI tool" in result.output
        assert "--yes" in result.output
        assert "-y" in result.output
        assert "Skip confirmation prompt" in result.output
        assert "Examples:" in result.output

    def test_uninstall_short_yes_flag(self):
        """Test that -y short flag works the same as --yes"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            list_result = MagicMock()
            list_result.stdout = "guppi-dummy v1.0.0\n"
            list_result.returncode = 0
            
            uninstall_result = MagicMock()
            uninstall_result.stdout = ""
            uninstall_result.stderr = ""
            uninstall_result.returncode = 0
            
            mock_run.side_effect = [list_result, uninstall_result]
            
            result = runner.invoke(app, ["uninstall", "dummy", "-y"])
            
            assert result.exit_code == 0
            # Should not show confirmation prompt
            assert "Are you sure?" not in result.output
            assert "uninstalled successfully" in result.output
