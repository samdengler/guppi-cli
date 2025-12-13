"""Tests for commands/tool.py - tool management commands"""
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from guppi.commands.tool import app
from guppi.discovery import ToolMetadata


runner = CliRunner()


class TestToolInstall:
    """Tests for tool install command"""

    def test_install_from_local_path_uses_uv_editable(self, temp_dir):
        """Installing with --from local path should use uv editable install"""
        tool_dir = temp_dir / "mytool"
        tool_dir.mkdir()

        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(stdout="installed", stderr="", returncode=0)

            result = runner.invoke(app, ["install", "mytool", "--from", str(tool_dir)])

            assert result.exit_code == 0
            assert "Tool 'mytool' installed successfully" in result.output
            mock_run.assert_called_once_with(
                ["uv", "tool", "install", "--editable", str(tool_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_install_from_remote_path_uses_git_plus(self):
        """Installing from non-existent path should use git+ syntax"""
        remote = "github.com/example/repo"
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(stdout="installed", stderr="", returncode=0)

            result = runner.invoke(app, ["install", "example", "--from", remote])

            assert result.exit_code == 0
            mock_run.assert_called_once_with(
                ["uv", "tool", "install", f"git+{remote}"],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_install_requires_source_when_ambiguous(self):
        """If a tool exists in multiple sources, require --source"""
        matches = [
            ToolMetadata("demo", "desc", Path("/tmp/a"), source="alpha"),
            ToolMetadata("demo", "desc", Path("/tmp/b"), source="beta"),
        ]
        with patch("guppi.commands.tool.find_all_tools", return_value=matches):
            result = runner.invoke(app, ["install", "demo"])

        assert result.exit_code == 1
        assert "multiple sources" in result.output
        assert "alpha" in result.output
        assert "beta" in result.output

    def test_install_with_source_uses_tool_path(self):
        """Installing with --source should install from the resolved tool path"""
        tool = ToolMetadata("demo", "desc", Path("/tools/demo"), source="alpha")
        with (
            patch("guppi.commands.tool.find_all_tools", return_value=[tool]),
            patch("guppi.commands.tool.find_tool", return_value=tool),
            patch("guppi.commands.tool._install_from_path") as mock_install,
        ):
            result = runner.invoke(app, ["install", "demo", "--source", "alpha"])

        assert result.exit_code == 0
        mock_install.assert_called_once_with("demo", str(tool.path))

    def test_install_not_found_in_sources(self):
        """Installing without matches should show helpful error"""
        with patch("guppi.commands.tool.find_all_tools", return_value=[]):
            result = runner.invoke(app, ["install", "missing"])

        assert result.exit_code == 1
        assert "not found in any source" in result.output
        assert "guppi tool search" in result.output


class TestToolSearch:
    """Tests for tool search command"""

    def test_search_no_tools(self):
        """No tools in sources should prompt to add a source"""
        with patch("guppi.commands.tool.discover_all_tools", return_value=[]):
            result = runner.invoke(app, ["search"])

        assert result.exit_code == 0
        assert "No tools found in sources" in result.output
        assert "Add a source" in result.output

    def test_search_filters_by_query(self):
        """Search with a query should filter to matching tools"""
        tools = [
            ToolMetadata("demo", "Demo tool", Path("/tmp/demo"), source="alpha"),
            ToolMetadata("other", "Other tool", Path("/tmp/other"), source="beta"),
        ]
        with patch("guppi.commands.tool.discover_all_tools", return_value=tools):
            result = runner.invoke(app, ["search", "dem"])

        assert result.exit_code == 0
        assert "Found 1 tool(s)" in result.output
        assert "demo" in result.output
        assert "other" not in result.output


class TestToolList:
    """Tests for listing installed tools"""

    def test_list_no_installed_tools(self, temp_dir):
        """No executables found should show helpful guidance"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(
                stdout=str(temp_dir), stderr="", returncode=0
            )

            result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No tools installed" in result.output
        mock_run.assert_called_once_with(
            ["printenv", "PATH"],
            capture_output=True,
            text=True,
            check=True,
        )

    def test_list_shows_executables(self, temp_dir):
        """Executable guppi-* files in PATH should be listed"""
        path_dir = temp_dir / "bin"
        path_dir.mkdir()

        tool_one = path_dir / "guppi-alpha"
        tool_one.write_text("#!/bin/sh\necho alpha")
        tool_one.chmod(0o755)

        tool_two = path_dir / "guppi-beta"
        tool_two.write_text("#!/bin/sh\necho beta")
        tool_two.chmod(0o755)

        non_exec = path_dir / "guppi-noexec"
        non_exec.write_text("echo noexec")

        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(
                stdout=str(path_dir), stderr="", returncode=0
            )

            result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output
        assert "noexec" not in result.output
        mock_run.assert_called_once_with(
            ["printenv", "PATH"],
            capture_output=True,
            text=True,
            check=True,
        )
