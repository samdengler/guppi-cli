"""Tool management commands"""

import subprocess
from pathlib import Path
import typer

from guppi.discovery import get_sources_dir

app = typer.Typer(help="Manage GUPPI tools")

# Create subcommand for source management
source_app = typer.Typer(help="Manage tool sources")
app.add_typer(source_app, name="source")


@source_app.command("add")
def source_add(
    name: str = typer.Argument(..., help="Name for this source"),
    url: str = typer.Argument(..., help="Git URL or local path"),
):
    """
    Add a tool source.
    
    Examples:
        guppi tool source add guppi-tools https://github.com/samdengler/guppi-tools
        guppi tool source add local-tools /path/to/local/tools
    """
    sources_dir = get_sources_dir()
    dest_path = sources_dir / name
    
    if dest_path.exists():
        typer.echo(f"Error: Source '{name}' already exists at {dest_path}", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Adding source '{name}' from {url}...")
    
    # Check if it's a local path or git URL
    local_path = Path(url)
    if local_path.exists() and local_path.is_dir():
        # Local path - create symlink
        try:
            dest_path.symlink_to(local_path.resolve())
            typer.echo(f"✓ Linked local source '{name}' → {local_path}")
        except Exception as e:
            typer.echo(f"Error creating symlink: {e}", err=True)
            raise typer.Exit(1)
    else:
        # Assume it's a git URL - clone it
        try:
            result = subprocess.run(
                ["git", "clone", url, str(dest_path)],
                check=True,
                capture_output=True,
                text=True
            )
            typer.echo(f"✓ Cloned source '{name}' to {dest_path}")
        except subprocess.CalledProcessError as e:
            typer.echo(f"Error cloning repository: {e.stderr}", err=True)
            raise typer.Exit(1)
        except FileNotFoundError:
            typer.echo(f"Error: 'git' command not found", err=True)
            raise typer.Exit(1)


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
