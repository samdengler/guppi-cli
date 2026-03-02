"""Tool routing logic for GUPPI"""

import sys
import subprocess
import typer

from guppi.discovery import find_tool


def route_to_tool(tool: str, tool_args: list[str]) -> int:
    """
    Route a command to an installed tool.

    Args:
        tool: Name of the tool to route to
        tool_args: Arguments to pass to the tool

    Returns:
        Exit code from the tool
    """
    # Look up tool in discovered sources
    metadata = find_tool(tool)
    resolved_name = metadata.name if metadata else tool
    tool_cmd = f"guppi-{resolved_name}"

    try:
        result = subprocess.run([tool_cmd] + tool_args)
        return result.returncode
    except FileNotFoundError:
        if metadata:
            typer.echo(
                f"Error: Skill '{tool}' found in source '{metadata.source}' but not installed",
                err=True,
            )
            typer.echo(f"Install with: guppi skill install {tool}", err=True)
        else:
            typer.echo(f"Error: Skill '{tool}' not found", err=True)
            typer.echo("Search available skills with: guppi skill search", err=True)
        return 1
