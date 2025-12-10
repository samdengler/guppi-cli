"""Tool management commands"""

import subprocess
from pathlib import Path
import typer

app = typer.Typer(help="Manage GUPPI tools")


@app.command("install")
def install(
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


@app.command("list")
def list_tools():
    """
    List installed GUPPI tools.
    """
    # TODO: Implement tool discovery
    typer.echo("Tool listing not yet implemented")
    raise typer.Exit(1)
