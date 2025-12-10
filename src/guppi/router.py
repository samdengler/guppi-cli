"""Tool routing logic for GUPPI"""

import sys
import subprocess
import typer


def route_to_tool(tool: str, tool_args: list[str]) -> int:
    """
    Route a command to an installed tool.
    
    Args:
        tool: Name of the tool to route to
        tool_args: Arguments to pass to the tool
    
    Returns:
        Exit code from the tool
    """
    tool_cmd = f"guppi-{tool}"
    
    try:
        result = subprocess.run([tool_cmd] + tool_args)
        return result.returncode
    except FileNotFoundError:
        typer.echo(f"Error: Tool '{tool}' not found", err=True)
        typer.echo(f"Install it with: guppi tool install {tool} --from <path>", err=True)
        return 1
