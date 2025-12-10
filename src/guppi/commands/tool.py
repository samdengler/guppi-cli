"""Tool management commands"""

import subprocess
from pathlib import Path
import typer

from guppi.discovery import get_sources_dir, find_tool

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


@app.command("update")
def update(
    source: str = typer.Argument(None, help="Specific source to update (updates all if not provided)"),
):
    """
    Update tool sources.
    
    Examples:
        guppi tool update              # Update all sources
        guppi tool update guppi-tools  # Update specific source
    """
    sources_dir = get_sources_dir()
    
    if source:
        # Update specific source
        source_path = sources_dir / source
        if not source_path.exists():
            typer.echo(f"Error: Source '{source}' not found", err=True)
            raise typer.Exit(1)
        
        sources_to_update = [(source, source_path)]
    else:
        # Update all sources
        sources_to_update = [
            (path.name, path) 
            for path in sources_dir.iterdir() 
            if path.is_dir()
        ]
        
        if not sources_to_update:
            typer.echo("No sources to update")
            return
    
    # Update each source
    updated = 0
    skipped = 0
    errors = 0
    
    for name, path in sources_to_update:
        # Skip symlinks (local sources)
        if path.is_symlink():
            typer.echo(f"⊘ Skipping '{name}' (local source)")
            skipped += 1
            continue
        
        # Check if it's a git repo
        git_dir = path / ".git"
        if not git_dir.exists():
            typer.echo(f"⊘ Skipping '{name}' (not a git repository)")
            skipped += 1
            continue
        
        typer.echo(f"Updating '{name}'...")
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Check if anything was updated
            if "Already up to date" in result.stdout:
                typer.echo(f"  ✓ Already up to date")
            else:
                typer.echo(f"  ✓ Updated")
            updated += 1
        except subprocess.CalledProcessError as e:
            typer.echo(f"  ✗ Error: {e.stderr}", err=True)
            errors += 1
    
    # Summary
    typer.echo()
    typer.echo(f"Updated: {updated}, Skipped: {skipped}, Errors: {errors}")


@app.command("install")
def install(
    name: str = typer.Argument(..., help="Name of the tool to install"),
    from_path: str = typer.Option(None, "--from", help="GitHub repo or local path (optional if tool is in sources)"),
):
    """
    Install a GUPPI tool.
    
    Examples:
        guppi tool install dummy                      # Install from sources
        guppi tool install dummy --from ~/dev/dummy   # Install from local path
    """
    # If --from is provided, use it directly
    if from_path:
        _install_from_path(name, from_path)
        return
    
    # Otherwise, look up tool in sources
    typer.echo(f"Looking for '{name}' in sources...")
    tool = find_tool(name)
    
    if not tool:
        typer.echo(f"Error: Tool '{name}' not found in any source", err=True)
        typer.echo(f"Try: guppi tool search", err=True)
        typer.echo(f"Or: guppi tool install {name} --from <path>", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Found '{name}' in source '{tool.source}'")
    _install_from_path(name, str(tool.path))


def _install_from_path(name: str, from_path: str):
    """Helper to install a tool from a given path"""
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
