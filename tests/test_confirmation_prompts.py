"""Tests for confirmation prompts on destructive operations"""

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from guppi.commands.tool import app

runner = CliRunner()


class TestToolInstallConfirmation:
    """Tests for tool install confirmation prompts"""

    def test_install_prompts_if_already_installed(self, temp_dir):
        """Installing an already-installed tool should prompt for confirmation"""
        tool_dir = temp_dir / "mytool"
        tool_dir.mkdir()

        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            # First call is uv tool list (returns tool as installed)
            mock_run.side_effect = [
                SimpleNamespace(stdout="guppi-mytool v1.0.0\n- guppi-mytool", stderr="", returncode=0),
            ]

            # Decline the reinstall
            result = runner.invoke(app, ["install", "mytool", "--from", str(tool_dir)], input="n\n")

            assert result.exit_code == 0
            assert "already installed" in result.output
            assert "Aborted" in result.output
            # Should only call uv tool list, not install
            assert mock_run.call_count == 1

    def test_install_accepts_reinstall_prompt(self, temp_dir):
        """Accepting the reinstall prompt should proceed with installation"""
        tool_dir = temp_dir / "mytool"
        tool_dir.mkdir()

        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            # First call is uv tool list, second is install
            mock_run.side_effect = [
                SimpleNamespace(stdout="guppi-mytool v1.0.0\n- guppi-mytool", stderr="", returncode=0),
                SimpleNamespace(stdout="Installed", stderr="", returncode=0),
            ]

            # Accept the reinstall
            result = runner.invoke(app, ["install", "mytool", "--from", str(tool_dir)], input="y\n")

            assert result.exit_code == 0
            assert "already installed" in result.output
            assert "Tool 'mytool' installed successfully" in result.output
            assert mock_run.call_count == 2

    def test_install_with_yes_flag_skips_prompt(self, temp_dir):
        """Using --yes flag should skip the confirmation prompt"""
        tool_dir = temp_dir / "mytool"
        tool_dir.mkdir()

        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = [
                SimpleNamespace(stdout="guppi-mytool v1.0.0\n- guppi-mytool", stderr="", returncode=0),
                SimpleNamespace(stdout="Installed", stderr="", returncode=0),
            ]

            result = runner.invoke(app, ["install", "mytool", "--from", str(tool_dir), "--yes"])

            assert result.exit_code == 0
            assert "already installed" not in result.output
            assert "Tool 'mytool' installed successfully" in result.output
            assert mock_run.call_count == 2

    def test_install_new_tool_no_prompt(self, temp_dir):
        """Installing a new tool should not prompt"""
        tool_dir = temp_dir / "mytool"
        tool_dir.mkdir()

        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            # uv tool list returns empty (tool not installed)
            mock_run.side_effect = [
                SimpleNamespace(stdout="", stderr="", returncode=0),
                SimpleNamespace(stdout="Installed", stderr="", returncode=0),
            ]

            result = runner.invoke(app, ["install", "mytool", "--from", str(tool_dir)])

            assert result.exit_code == 0
            assert "already installed" not in result.output
            assert "Aborted" not in result.output
            assert "Tool 'mytool' installed successfully" in result.output


class TestSourceAddConfirmation:
    """Tests for source add confirmation prompts"""

    def test_source_add_prompts_if_exists(self, temp_dir):
        """Adding a source that already exists should prompt for confirmation"""
        sources_dir = temp_dir / ".guppi" / "sources"
        sources_dir.mkdir(parents=True)
        existing_source = sources_dir / "mysource"
        existing_source.mkdir()

        new_url = "https://github.com/example/repo"

        with (
            patch("guppi.commands.tool.get_sources_dir", return_value=sources_dir),
            patch("guppi.commands.tool.subprocess.run") as mock_run,
        ):
            mock_run.return_value = SimpleNamespace(stdout="", stderr="", returncode=0)

            # Decline the replacement
            result = runner.invoke(app, ["source", "add", "mysource", new_url], input="n\n")

            assert result.exit_code == 0
            assert "already exists" in result.output
            assert "Aborted" in result.output
            # Should not have called git clone
            mock_run.assert_not_called()

    def test_source_add_accepts_replacement_prompt(self, temp_dir):
        """Accepting the replacement prompt should replace the source"""
        sources_dir = temp_dir / ".guppi" / "sources"
        sources_dir.mkdir(parents=True)
        existing_source = sources_dir / "mysource"
        existing_source.mkdir()

        new_url = "https://github.com/example/repo"

        with (
            patch("guppi.commands.tool.get_sources_dir", return_value=sources_dir),
            patch("guppi.commands.tool.subprocess.run") as mock_run,
        ):
            mock_run.return_value = SimpleNamespace(stdout="", stderr="", returncode=0)

            # Accept the replacement
            result = runner.invoke(app, ["source", "add", "mysource", new_url], input="y\n")

            assert result.exit_code == 0
            assert "already exists" in result.output
            assert "Removed existing source" in result.output
            # Should have called git clone
            mock_run.assert_called_once()

    def test_source_add_with_yes_flag_skips_prompt(self, temp_dir):
        """Using --yes flag should skip the confirmation prompt"""
        sources_dir = temp_dir / ".guppi" / "sources"
        sources_dir.mkdir(parents=True)
        existing_source = sources_dir / "mysource"
        existing_source.mkdir()

        new_url = "https://github.com/example/repo"

        with (
            patch("guppi.commands.tool.get_sources_dir", return_value=sources_dir),
            patch("guppi.commands.tool.subprocess.run") as mock_run,
        ):
            mock_run.return_value = SimpleNamespace(stdout="", stderr="", returncode=0)

            result = runner.invoke(app, ["source", "add", "mysource", new_url, "--yes"])

            assert result.exit_code == 0
            assert "already exists" not in result.output
            assert "Removed existing source" in result.output
            # Should have called git clone
            mock_run.assert_called_once()

    def test_source_add_new_source_no_prompt(self, temp_dir):
        """Adding a new source should not prompt"""
        sources_dir = temp_dir / ".guppi" / "sources"
        sources_dir.mkdir(parents=True)

        new_url = "https://github.com/example/repo"

        with (
            patch("guppi.commands.tool.get_sources_dir", return_value=sources_dir),
            patch("guppi.commands.tool.subprocess.run") as mock_run,
        ):
            mock_run.return_value = SimpleNamespace(stdout="", stderr="", returncode=0)

            result = runner.invoke(app, ["source", "add", "newsource", new_url])

            assert result.exit_code == 0
            assert "already exists" not in result.output
            assert "Aborted" not in result.output
            # Should have called git clone
            mock_run.assert_called_once()
