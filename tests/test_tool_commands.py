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
        assert "Total: 1 tool(s) found" in result.output
        assert "demo" in result.output
        assert "other" not in result.output


class TestToolList:
    """Tests for listing installed tools"""

    def test_list_no_installed_tools(self, temp_dir):
        """No executables found should show helpful guidance"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            # Mock both uv tool dir and printenv PATH calls
            mock_run.side_effect = [
                SimpleNamespace(stdout=str(temp_dir / "uv_tools"), stderr="", returncode=0),  # uv tool dir
                SimpleNamespace(stdout=str(temp_dir), stderr="", returncode=0),  # printenv PATH
            ]
            
            with patch("guppi.commands.tool.discover_all_tools", return_value=[]):
                result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No tools installed" in result.output
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0] == (
            (["uv", "tool", "dir"],),
            {"capture_output": True, "text": True, "check": True}
        )
        assert mock_run.call_args_list[1] == (
            (["printenv", "PATH"],),
            {"capture_output": True, "text": True, "check": True}
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
            # Mock both uv tool dir and printenv PATH calls
            mock_run.side_effect = [
                SimpleNamespace(stdout=str(temp_dir / "uv_tools"), stderr="", returncode=0),  # uv tool dir
                SimpleNamespace(stdout=str(path_dir), stderr="", returncode=0),  # printenv PATH
            ]
            
            with patch("guppi.commands.tool.discover_all_tools", return_value=[]):
                result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output
        assert "noexec" not in result.output
        assert mock_run.call_count == 2


class TestSourceUpdate:
    """Tests for tool source update command"""

    def test_source_update_specific_source_success(self, temp_dir):
        """Test updating a specific git source"""
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        source_dir = sources_dir / "test-source"
        source_dir.mkdir()
        (source_dir / ".git").mkdir()
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            with patch("guppi.commands.tool.subprocess.run") as mock_run:
                mock_run.return_value = SimpleNamespace(
                    stdout="Updated 5 files",
                    stderr="",
                    returncode=0
                )
                
                result = runner.invoke(app, ["source", "update", "test-source"])
                
                assert result.exit_code == 0
                assert "Updating 'test-source'..." in result.output
                assert "✓ Updated" in result.output
                mock_run.assert_called_once_with(
                    ["git", "pull"],
                    cwd=source_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )

    def test_source_update_already_up_to_date(self, temp_dir):
        """Test updating when source is already up to date"""
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        source_dir = sources_dir / "test-source"
        source_dir.mkdir()
        (source_dir / ".git").mkdir()
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            with patch("guppi.commands.tool.subprocess.run") as mock_run:
                mock_run.return_value = SimpleNamespace(
                    stdout="Already up to date",
                    stderr="",
                    returncode=0
                )
                
                result = runner.invoke(app, ["source", "update", "test-source"])
                
                assert result.exit_code == 0
                assert "✓ Already up to date" in result.output

    def test_source_update_nonexistent_source(self, temp_dir):
        """Test updating a source that doesn't exist"""
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            result = runner.invoke(app, ["source", "update", "nonexistent"])
            
            assert result.exit_code == 1
            assert "Error: Source 'nonexistent' not found" in result.output

    def test_source_update_skips_symlink(self, temp_dir):
        """Test that update skips symlinked (local) sources"""
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        # Create actual directory and symlink to it
        actual_dir = temp_dir / "actual"
        actual_dir.mkdir()
        
        source_link = sources_dir / "local-source"
        source_link.symlink_to(actual_dir)
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            result = runner.invoke(app, ["source", "update", "local-source"])
            
            assert result.exit_code == 0
            assert "⊘ Skipping 'local-source' (local source)" in result.output

    def test_source_update_skips_non_git(self, temp_dir):
        """Test that update skips non-git directories"""
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        source_dir = sources_dir / "non-git"
        source_dir.mkdir()
        # Don't create .git directory
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            result = runner.invoke(app, ["source", "update", "non-git"])
            
            assert result.exit_code == 0
            assert "⊘ Skipping 'non-git' (not a git repository)" in result.output

    def test_source_update_all_sources(self, temp_dir):
        """Test updating all sources"""
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        # Create multiple sources
        for name in ["source1", "source2"]:
            source_dir = sources_dir / name
            source_dir.mkdir()
            (source_dir / ".git").mkdir()
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            with patch("guppi.commands.tool.subprocess.run") as mock_run:
                mock_run.return_value = SimpleNamespace(
                    stdout="Updated",
                    stderr="",
                    returncode=0
                )
                
                result = runner.invoke(app, ["source", "update"])
                
                assert result.exit_code == 0
                assert "Updating 'source1'..." in result.output
                assert "Updating 'source2'..." in result.output
                assert mock_run.call_count == 2

    def test_source_update_git_error(self, temp_dir):
        """Test handling git pull errors"""
        import subprocess
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        source_dir = sources_dir / "test-source"
        source_dir.mkdir()
        (source_dir / ".git").mkdir()
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            with patch("guppi.commands.tool.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    returncode=1,
                    cmd=["git", "pull"],
                    stderr="Network error"
                )
                
                result = runner.invoke(app, ["source", "update", "test-source"])
                
                assert result.exit_code == 0  # Command succeeds but reports error
                assert "✗ Error: Network error" in result.output

    def test_source_update_no_sources(self, temp_dir):
        """Test updating when no sources exist"""
        sources_dir = temp_dir / "sources"
        sources_dir.mkdir()
        
        with patch("guppi.commands.tool.get_sources_dir") as mock_get_sources:
            mock_get_sources.return_value = sources_dir
            
            result = runner.invoke(app, ["source", "update"])
            
            assert result.exit_code == 0
            assert "No sources to update" in result.output


class TestToolUpdate:
    """Tests for tool update command"""

    def test_tool_update_specific_tool_success(self):
        """Test updating a specific installed tool"""
        # Mock uv tool list to show installed tools
        list_result = SimpleNamespace(
            stdout="guppi-dummy v1.0.0\nguppi-beads v0.2.0\n",
            stderr="",
            returncode=0
        )
        
        # Mock uv tool upgrade showing update
        upgrade_result = SimpleNamespace(
            stdout="Updated guppi-dummy from 1.0.0 to 1.1.0\n",
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = [list_result, upgrade_result]
            
            result = runner.invoke(app, ["update", "dummy"])
            
            assert result.exit_code == 0
            assert "Updating 'guppi-dummy'..." in result.output
            assert "✓ Updated" in result.output
            assert mock_run.call_count == 2
            
            # Verify uv tool upgrade was called
            upgrade_call = mock_run.call_args_list[1]
            assert upgrade_call[0][0] == ["uv", "tool", "upgrade", "guppi-dummy"]

    def test_tool_update_already_up_to_date(self):
        """Test updating when tool is already up to date"""
        list_result = SimpleNamespace(
            stdout="guppi-dummy v1.0.0\n",
            stderr="",
            returncode=0
        )
        
        upgrade_result = SimpleNamespace(
            stdout="Nothing to upgrade for guppi-dummy\n",
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = [list_result, upgrade_result]
            
            result = runner.invoke(app, ["update", "dummy"])
            
            assert result.exit_code == 0
            assert "✓ Already up to date" in result.output

    def test_tool_update_tool_not_installed(self):
        """Test updating a tool that isn't installed"""
        list_result = SimpleNamespace(
            stdout="guppi-dummy v1.0.0\n",
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.return_value = list_result
            
            result = runner.invoke(app, ["update", "nonexistent"])
            
            assert result.exit_code == 1
            assert "Error: Tool 'guppi-nonexistent' is not installed" in result.output

    def test_tool_update_all_tools(self):
        """Test updating all installed tools"""
        list_result = SimpleNamespace(
            stdout="guppi-dummy v1.0.0\nguppi-beads v0.2.0\n",
            stderr="",
            returncode=0
        )
        
        upgrade_result1 = SimpleNamespace(
            stdout="Updated guppi-dummy\n",
            stderr="",
            returncode=0
        )
        
        upgrade_result2 = SimpleNamespace(
            stdout="Nothing to upgrade\n",
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = [list_result, upgrade_result1, upgrade_result2]
            
            result = runner.invoke(app, ["update"])
            
            assert result.exit_code == 0
            assert "Updating 'guppi-dummy'..." in result.output
            assert "Updating 'guppi-beads'..." in result.output
            assert "Updated: 1" in result.output
            assert "Up-to-date: 1" in result.output

    def test_tool_update_no_tools_installed(self):
        """Test updating when no guppi tools are installed"""
        list_result = SimpleNamespace(
            stdout="other-tool v1.0.0\n",  # Non-guppi tool
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.return_value = list_result
            
            result = runner.invoke(app, ["update"])
            
            assert result.exit_code == 0
            assert "No GUPPI tools installed" in result.output

    def test_tool_update_uv_not_found(self):
        """Test when uv command is not available"""
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = runner.invoke(app, ["update"])
            
            assert result.exit_code == 1
            assert "Error: 'uv' command not found" in result.output

    def test_tool_update_upgrade_error(self):
        """Test handling upgrade errors"""
        import subprocess
        
        list_result = SimpleNamespace(
            stdout="guppi-dummy v1.0.0\n",
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = [
                list_result,
                subprocess.CalledProcessError(
                    returncode=1,
                    cmd=["uv", "tool", "upgrade", "guppi-dummy"],
                    stderr="Network error"
                )
            ]
            
            result = runner.invoke(app, ["update", "dummy"])
            
            assert result.exit_code == 0  # Command succeeds but reports error
            assert "✗ Error: Network error" in result.output
            assert "Errors: 1" in result.output

    def test_tool_update_adds_guppi_prefix(self):
        """Test that tool name without guppi- prefix gets it added"""
        list_result = SimpleNamespace(
            stdout="guppi-dummy v1.0.0\n",
            stderr="",
            returncode=0
        )
        
        upgrade_result = SimpleNamespace(
            stdout="Updated\n",
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = [list_result, upgrade_result]
            
            # Call with just "dummy", should update "guppi-dummy"
            result = runner.invoke(app, ["update", "dummy"])
            
            assert result.exit_code == 0
            upgrade_call = mock_run.call_args_list[1]
            assert "guppi-dummy" in upgrade_call[0][0]

    def test_tool_update_filters_non_guppi_tools(self):
        """Test that only guppi-* tools are updated"""
        list_result = SimpleNamespace(
            stdout="guppi-dummy v1.0.0\nother-tool v1.0.0\nguppi-beads v0.2.0\n",
            stderr="",
            returncode=0
        )
        
        upgrade_result = SimpleNamespace(
            stdout="Updated\n",
            stderr="",
            returncode=0
        )
        
        with patch("guppi.commands.tool.subprocess.run") as mock_run:
            mock_run.side_effect = [list_result, upgrade_result, upgrade_result]
            
            result = runner.invoke(app, ["update"])
            
            assert result.exit_code == 0
            # Should only update 2 guppi tools, not other-tool
            assert mock_run.call_count == 3  # 1 list + 2 upgrades
            assert "guppi-dummy" in result.output
            assert "guppi-beads" in result.output
            assert "other-tool" not in result.output
