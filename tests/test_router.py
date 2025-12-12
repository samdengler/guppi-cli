"""Tests for router.py - tool routing logic"""
import pytest
from unittest.mock import patch, MagicMock
from guppi.router import route_to_tool


class TestRouteToTool:
    """Tests for route_to_tool function"""

    def test_route_to_tool_success(self):
        """Test routing to a tool that exists and succeeds"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            exit_code = route_to_tool("dummy", ["arg1", "arg2"])

            assert exit_code == 0
            mock_run.assert_called_once_with(["guppi-dummy", "arg1", "arg2"])

    def test_route_to_tool_with_failure_exit_code(self):
        """Test routing to a tool that runs but returns non-zero exit code"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 42
            mock_run.return_value = mock_result

            exit_code = route_to_tool("failing-tool", ["--fail"])

            assert exit_code == 42
            mock_run.assert_called_once_with(["guppi-failing-tool", "--fail"])

    def test_route_to_tool_not_found(self):
        """Test routing to a tool that doesn't exist"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with patch("guppi.router.typer.echo") as mock_echo:
                exit_code = route_to_tool("nonexistent", [])

                assert exit_code == 1
                # Verify error messages were displayed
                assert mock_echo.call_count == 2
                # First call should be error about tool not found
                assert "Tool 'nonexistent' not found" in mock_echo.call_args_list[0][0][0]
                # Second call should be install suggestion
                assert "guppi tool install nonexistent" in mock_echo.call_args_list[1][0][0]

    def test_route_to_tool_with_no_args(self):
        """Test routing to a tool with no arguments"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            exit_code = route_to_tool("simple", [])

            assert exit_code == 0
            mock_run.assert_called_once_with(["guppi-simple"])

    def test_route_to_tool_with_many_args(self):
        """Test routing to a tool with many arguments"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            args = ["--flag1", "value1", "--flag2", "value2", "positional"]
            exit_code = route_to_tool("complex", args)

            assert exit_code == 0
            mock_run.assert_called_once_with(
                ["guppi-complex", "--flag1", "value1", "--flag2", "value2", "positional"]
            )

    def test_route_to_tool_constructs_correct_command_name(self):
        """Test that tool name is correctly prefixed with 'guppi-'"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            route_to_tool("my-tool", [])

            # Verify the command is 'guppi-my-tool', not 'my-tool'
            called_cmd = mock_run.call_args[0][0]
            assert called_cmd[0] == "guppi-my-tool"

    def test_route_to_tool_preserves_arg_order(self):
        """Test that arguments are passed in the correct order"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            args = ["first", "second", "third"]
            route_to_tool("test", args)

            called_cmd = mock_run.call_args[0][0]
            assert called_cmd == ["guppi-test", "first", "second", "third"]

    def test_route_to_tool_with_special_characters_in_args(self):
        """Test routing with arguments containing special characters"""
        with patch("guppi.router.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            args = ["--message", "Hello, World!", "--path", "/tmp/test file.txt"]
            exit_code = route_to_tool("echo", args)

            assert exit_code == 0
            called_cmd = mock_run.call_args[0][0]
            assert called_cmd == ["guppi-echo", "--message", "Hello, World!", "--path", "/tmp/test file.txt"]

    def test_route_to_tool_returns_exact_exit_code(self):
        """Test that exact exit codes are preserved"""
        test_codes = [0, 1, 2, 127, 255]

        for expected_code in test_codes:
            with patch("guppi.router.subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = expected_code
                mock_run.return_value = mock_result

                actual_code = route_to_tool("test", [])
                assert actual_code == expected_code
