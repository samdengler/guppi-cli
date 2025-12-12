"""Tool management commands"""

import os
import re
import subprocess
import shutil
from pathlib import Path
import typer

from guppi.discovery import get_sources_dir, find_tool, find_all_tools, discover_all_tools, is_valid_source
from guppi.templates import load_and_render_template

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


@source_app.command("list")
def source_list():
    """
    List all tool sources.
    
    Shows configured sources with their paths and types (git/local).
    """
    sources_dir = get_sources_dir()
    
    if not sources_dir.exists():
        typer.echo("No sources configured")
        typer.echo("\nAdd sources with: guppi tool source add <name> <url>")
        return
    
    # Collect source information
    sources = []
    for source_path in sources_dir.iterdir():
        if not source_path.is_dir():
            continue
        
        name = source_path.name
        
        # Check if it's a symlink (local) or git repo
        if source_path.is_symlink():
            source_type = "local"
            target = source_path.resolve()
            location = str(target)
        elif (source_path / ".git").exists():
            source_type = "git"
            # Try to get git remote URL
            try:
                result = subprocess.run(
                    ["git", "-C", str(source_path), "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                location = result.stdout.strip()
            except subprocess.CalledProcessError:
                location = str(source_path)
        else:
            source_type = "unknown"
            location = str(source_path)
        
        sources.append({
            "name": name,
            "type": source_type,
            "location": location
        })
    
    if not sources:
        typer.echo("No sources configured")
        typer.echo("\nAdd sources with: guppi tool source add <name> <url>")
        return
    
    # Sort by name
    sources.sort(key=lambda x: x["name"])
    
    # Display
    typer.echo("Tool sources:\n")
    max_name = max(len(s["name"]) for s in sources)
    max_type = max(len(s["type"]) for s in sources)
    
    typer.echo(f"{'NAME':<{max_name}}  {'TYPE':<{max_type}}  LOCATION")
    typer.echo("-" * (max_name + max_type + 60))
    
    for source in sources:
        typer.echo(f"{source['name']:<{max_name}}  {source['type']:<{max_type}}  {source['location']}")
    
    typer.echo(f"\nTotal: {len(sources)} source(s) configured")


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


@app.command("search")
def search(
    query: str = typer.Argument(None, help="Search query (optional - shows all if not provided)"),
):
    """
    Search for available tools in all sources.
    
    Examples:
        guppi tool search       # List all available tools
        guppi tool search beads # Search for tools matching 'beads'
    """
    typer.echo("Searching for tools...")
    tools = discover_all_tools()
    
    if not tools:
        typer.echo("No tools found in sources")
        typer.echo("Add a source with: guppi tool source add <name> <url>")
        return
    
    # Filter by query if provided
    if query:
        query_lower = query.lower()
        tools = [
            t for t in tools 
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]
        
        if not tools:
            typer.echo(f"No tools found matching '{query}'")
            return
    
    # Display results
    typer.echo(f"\nFound {len(tools)} tool(s):\n")
    
    # Find max widths for formatting
    max_name = max(len(t.name) for t in tools)
    max_source = max(len(t.source or "unknown") for t in tools)
    
    # Print header
    typer.echo(f"{'NAME':<{max_name}}  {'SOURCE':<{max_source}}  DESCRIPTION")
    typer.echo("-" * (max_name + max_source + 50))
    
    # Print tools
    for tool in sorted(tools, key=lambda t: t.name):
        source = tool.source or "unknown"
        typer.echo(f"{tool.name:<{max_name}}  {source:<{max_source}}  {tool.description}")


@app.command("list")
def list_tools():
    """
    List installed GUPPI tools.
    
    Shows all tools that are currently installed and available for routing.
    """
    typer.echo("Installed tools:\n")
    
    # Look for guppi-* executables in PATH
    installed = []
    
    # Get PATH directories
    path_env = subprocess.run(
        ["printenv", "PATH"],
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()
    
    path_dirs = [Path(p) for p in path_env.split(":") if p]
    
    # Search for guppi-* executables
    seen = set()
    for path_dir in path_dirs:
        if not path_dir.exists():
            continue
        
        try:
            for item in path_dir.iterdir():
                if item.name.startswith("guppi-") and item.is_file():
                    # Check if executable
                    if item.stat().st_mode & 0o111:  # Has execute permission
                        tool_name = item.name.replace("guppi-", "")
                        if tool_name not in seen:
                            installed.append({
                                "name": tool_name,
                                "path": str(item)
                            })
                            seen.add(tool_name)
        except PermissionError:
            continue
    
    if not installed:
        typer.echo("No tools installed")
        typer.echo("\nInstall tools with: guppi tool install <name>")
        return
    
    # Sort by name
    installed.sort(key=lambda x: x["name"])
    
    # Display
    max_name = max(len(t["name"]) for t in installed)
    typer.echo(f"{'NAME':<{max_name}}  EXECUTABLE")
    typer.echo("-" * (max_name + 50))
    
    for tool in installed:
        typer.echo(f"{tool['name']:<{max_name}}  {tool['path']}")
    
    typer.echo(f"\nTotal: {len(installed)} tool(s) installed")


@app.command("install")
def install(
    name: str = typer.Argument(..., help="Name of the tool to install"),
    from_path: str = typer.Option(None, "--from", help="GitHub repo or local path (optional if tool is in sources)"),
    source: str = typer.Option(None, "--source", help="Source name to install from (required if tool exists in multiple sources)"),
):
    """
    Install a GUPPI tool.
    
    Examples:
        guppi tool install dummy                      # Install from sources
        guppi tool install dummy --source guppi-tools # Install from specific source
        guppi tool install dummy --from ~/dev/dummy   # Install from local path
    """
    # If --from is provided, use it directly
    if from_path:
        _install_from_path(name, from_path)
        return
    
    # Otherwise, look up tool in sources
    typer.echo(f"Looking for '{name}' in sources...")
    
    # Check if tool exists in multiple sources
    all_matches = find_all_tools(name)
    
    if not all_matches:
        typer.echo(f"Error: Tool '{name}' not found in any source", err=True)
        typer.echo(f"Try: guppi tool search", err=True)
        typer.echo(f"Or: guppi tool install {name} --from <path>", err=True)
        raise typer.Exit(1)
    
    # If multiple matches and no source specified, require disambiguation
    if len(all_matches) > 1 and not source:
        typer.echo(f"Error: Tool '{name}' found in multiple sources:", err=True)
        for match in all_matches:
            typer.echo(f"  - {match.source}", err=True)
        typer.echo(f"\nPlease specify a source:", err=True)
        typer.echo(f"  guppi tool install {name} --source <source-name>", err=True)
        raise typer.Exit(1)
    
    # Find the tool (with optional source filter)
    tool = find_tool(name, source)
    
    if not tool:
        if source:
            typer.echo(f"Error: Tool '{name}' not found in source '{source}'", err=True)
        else:
            typer.echo(f"Error: Tool '{name}' not found", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"Found '{name}' in source '{tool.source}'")
    _install_from_path(name, str(tool.path))


def _install_from_path(name: str, from_path: str):
    """Helper to install a tool from a given path"""
    typer.echo(f"Installing tool '{name}' from {from_path}...")
    
    # Determine if it's a local path or remote repo
    if Path(from_path).exists():
        # Local path - use uv tool install with editable mode
        cmd = ["uv", "tool", "install", "--editable", from_path]
    else:
        # Remote repo - use uv tool install with git URL
        cmd = ["uv", "tool", "install", f"git+{from_path}"]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        typer.echo(result.stdout)
        typer.echo(f"✓ Tool '{name}' installed successfully!")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error installing tool: {e.stderr}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
