"""GUPPI CLI - Plugin framework for composing tools"""

import sys
import subprocess
from pathlib import Path
import typer

# Create main app WITHOUT trying to capture unknown commands
# We'll handle routing separately
app = typer.Typer(
    help="GUPPI - General Use Personal Program Interface",
    add_completion=False,
    no_args_is_help=True,
)

# Create 'tool' subcommand group
tool_app = typer.Typer(help="Manage GUPPI tools")
app.add_typer(tool_app, name="tool")


@tool_app.command("install")
def tool_install(
    name: str = typer.Argument(..., help="Name of the tool to install"),
    from_path: str = typer.Option(None, "--from", help="GitHub repo or local path"),
):
    """
    Install a GUPPI tool.
    
    Examples:
        guppi tool install dummy --from ../guppi-tools/dummy
        guppi tool install dummy --from github.com/user/guppi-tools --subdirectory dummy
    """
    if not from_path:
        typer.echo(f"Error: --from is required", err=True)
        typer.echo("Usage: guppi tool install <name> --from <path-or-repo>", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Installing tool '{name}' from {from_path}...")
    
    # Determine if it's a local path or remote repo
    if Path(from_path).exists():
        # Local path - use uv pip install
        cmd = ["uv", "pip", "install", "-e", from_path]
    else:
        # Remote repo - for now, just error out (we'll add this next)
        typer.echo(f"Error: Remote installation not yet implemented", err=True)
        typer.echo(f"Use a local path for now", err=True)
        raise typer.Exit(1)
    
    try:
        result = subprocess.run(cmd, check=True)
        typer.echo(f"✓ Tool '{name}' installed successfully!")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error installing tool: {e}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)


def main_entry():
    """
    Main entry point that handles both subcommands and tool routing.
    """
    # Check if we have args
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        
        # If it's a known subcommand, let Typer handle it
        if first_arg in ["tool"]:
            app()
            return
        
        # Otherwise, try to route to a tool
        tool = first_arg
        tool_args = sys.argv[2:]
        tool_cmd = f"guppi-{tool}"
        
        try:
            result = subprocess.run([tool_cmd] + tool_args)
            sys.exit(result.returncode)
        except FileNotFoundError:
            typer.echo(f"Error: Tool '{tool}' not found", err=True)
            typer.echo(f"Install it with: guppi tool install {tool} --from <path>", err=True)
            sys.exit(1)
    else:
        # No args, show help
        app()


if __name__ == "__main__":
    main_entry()
