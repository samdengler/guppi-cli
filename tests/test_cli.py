"""Tests for cli.py - main entry point and routing"""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from guppi.cli import app, version_callback, main_entry
from guppi.__version__ import __version__


runner = CliRunner()


class TestVersionCallback:
    """Tests for version_callback function"""

    def test_version_callback_with_true(self):
        """Test version callback exits when value is True"""
        import typer as typer_module
        with pytest.raises(typer_module.Exit):
            with patch("guppi.cli.typer.echo") as mock_echo:
                version_callback(True)
                mock_echo.assert_called_once_with(f"guppi version {__version__}")

    def test_version_callback_with_false(self):
        """Test version callback does nothing when value is False"""
        with patch("guppi.cli.typer.echo") as mock_echo:
            result = version_callback(False)
            assert result is None
            mock_echo.assert_not_called()

    def test_version_callback_with_none(self):
        """Test version callback does nothing when value is None"""
        with patch("guppi.cli.typer.echo") as mock_echo:
            result = version_callback(None)
            assert result is None
            mock_echo.assert_not_called()


class TestMainApp:
    """Tests for main Typer app"""

    def test_app_no_args_shows_help(self):
        """Test that running with no args shows help"""
        result = runner.invoke(app, [])
        # Typer with no_args_is_help=True exits with code 0 when invoked
        # but the CLI runner may return different codes
        assert "GUPPI - General Use Personal Program Interface" in result.output
        assert "tool" in result.output
        assert "upgrade" in result.output

    def test_app_help_flag(self):
        """Test --help flag shows help"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "GUPPI - General Use Personal Program Interface" in result.output

    def test_app_version_flag(self):
        """Test --version flag shows version"""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert f"guppi version {__version__}" in result.output

    def test_app_version_short_flag(self):
        """Test -v flag shows version"""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert f"guppi version {__version__}" in result.output

    def test_app_has_tool_subcommand(self):
        """Test that 'tool' subcommand is available"""
        result = runner.invoke(app, ["tool", "--help"])
        assert result.exit_code == 0
        assert "Manage GUPPI tools" in result.output

    def test_app_has_upgrade_subcommand(self):
        """Test that 'upgrade' subcommand is available"""
        result = runner.invoke(app, ["upgrade", "--help"])
        assert result.exit_code == 0
        # Note: upgrade help text depends on upgrade.py


class TestMainEntry:
    """Tests for main_entry function"""

    def test_main_entry_no_args_shows_help(self):
        """Test main_entry with no args shows help"""
        with patch("sys.argv", ["guppi"]):
            with patch("guppi.cli.app") as mock_app:
                main_entry()
                mock_app.assert_called_once()

    def test_main_entry_with_help_flag(self):
        """Test main_entry with --help calls app"""
        with patch("sys.argv", ["guppi", "--help"]):
            with patch("guppi.cli.app") as mock_app:
                main_entry()
                mock_app.assert_called_once()

    def test_main_entry_with_version_flag(self):
        """Test main_entry with --version calls app"""
        with patch("sys.argv", ["guppi", "--version"]):
            with patch("guppi.cli.app") as mock_app:
                main_entry()
                mock_app.assert_called_once()

    def test_main_entry_with_tool_subcommand(self):
        """Test main_entry with 'tool' subcommand calls app"""
        with patch("sys.argv", ["guppi", "tool", "list"]):
            with patch("guppi.cli.app") as mock_app:
                main_entry()
                mock_app.assert_called_once()

    def test_main_entry_with_upgrade_subcommand(self):
        """Test main_entry with 'upgrade' subcommand calls app"""
        with patch("sys.argv", ["guppi", "upgrade"]):
            with patch("guppi.cli.app") as mock_app:
                main_entry()
                mock_app.assert_called_once()

    def test_main_entry_routes_to_tool(self):
        """Test main_entry routes to external tool when not a subcommand"""
        with patch("sys.argv", ["guppi", "dummy", "arg1", "arg2"]):
            with patch("guppi.cli.route_to_tool") as mock_route:
                mock_route.return_value = 0
                with patch("sys.exit") as mock_exit:
                    main_entry()
                    mock_route.assert_called_once_with("dummy", ["arg1", "arg2"])
                    mock_exit.assert_called_once_with(0)

    def test_main_entry_routes_to_tool_with_no_args(self):
        """Test main_entry routes to tool with no additional args"""
        with patch("sys.argv", ["guppi", "mytool"]):
            with patch("guppi.cli.route_to_tool") as mock_route:
                mock_route.return_value = 0
                with patch("sys.exit") as mock_exit:
                    main_entry()
                    mock_route.assert_called_once_with("mytool", [])
                    mock_exit.assert_called_once_with(0)

    def test_main_entry_routes_to_tool_with_exit_code(self):
        """Test main_entry preserves exit code from routed tool"""
        with patch("sys.argv", ["guppi", "failing", "--fail"]):
            with patch("guppi.cli.route_to_tool") as mock_route:
                mock_route.return_value = 42
                with patch("sys.exit") as mock_exit:
                    main_entry()
                    mock_route.assert_called_once_with("failing", ["--fail"])
                    mock_exit.assert_called_once_with(42)

    def test_main_entry_with_flag_starting_arg(self):
        """Test main_entry with flag-like first arg calls app"""
        with patch("sys.argv", ["guppi", "-h"]):
            with patch("guppi.cli.app") as mock_app:
                main_entry()
                mock_app.assert_called_once()

    def test_main_entry_distinguishes_subcommand_from_tool(self):
        """Test that 'tool' and 'upgrade' are treated as subcommands, not tools"""
        # Test 'tool' subcommand
        with patch("sys.argv", ["guppi", "tool", "list"]):
            with patch("guppi.cli.app") as mock_app:
                with patch("guppi.cli.route_to_tool") as mock_route:
                    main_entry()
                    mock_app.assert_called_once()
                    mock_route.assert_not_called()

        # Test 'upgrade' subcommand
        with patch("sys.argv", ["guppi", "upgrade"]):
            with patch("guppi.cli.app") as mock_app:
                with patch("guppi.cli.route_to_tool") as mock_route:
                    main_entry()
                    mock_app.assert_called_once()
                    mock_route.assert_not_called()

    def test_main_entry_with_tool_name_containing_dashes(self):
        """Test routing to tool names with dashes"""
        with patch("sys.argv", ["guppi", "my-cool-tool", "--option"]):
            with patch("guppi.cli.route_to_tool") as mock_route:
                mock_route.return_value = 0
                with patch("sys.exit") as mock_exit:
                    main_entry()
                    mock_route.assert_called_once_with("my-cool-tool", ["--option"])
                    mock_exit.assert_called_once_with(0)

    def test_main_entry_passes_all_args_to_tool(self):
        """Test that all args after tool name are passed to the tool"""
        with patch("sys.argv", ["guppi", "tool-name", "pos1", "--flag", "value", "pos2"]):
            with patch("guppi.cli.route_to_tool") as mock_route:
                mock_route.return_value = 0
                with patch("sys.exit"):
                    main_entry()
                    mock_route.assert_called_once_with(
                        "tool-name",
                        ["pos1", "--flag", "value", "pos2"]
                    )
