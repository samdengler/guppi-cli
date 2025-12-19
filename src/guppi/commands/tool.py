"""Tool management commands"""

import os
import re
import subprocess
import shutil
from pathlib import Path
import typer

from guppi.discovery import get_sources_dir, find_tool, find_all_tools, discover_all_tools, is_valid_source
from guppi.templates import load_and_render_template, sanitize_tool_name, tool_name_to_package

app = typer.Typer(help="Manage GUPPI tools")

# Create subcommand for source management
source_app = typer.Typer(help="Manage tool sources")
app.add_typer(source_app, name="source")


@source_app.command("add")
def source_add(
    name: str = typer.Argument(..., help="Name for this source"),
    url: str = typer.Argument(..., help="Git URL or local path"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Add a tool source.
    
    Examples:
        guppi tool source add guppi-tools https://github.com/samdengler/guppi-tools
        guppi tool source add local-tools /path/to/local/tools
        guppi tool source add guppi-tools <url> --yes  # Overwrite without prompting
    """
    sources_dir = get_sources_dir()
    dest_path = sources_dir / name
    
    if dest_path.exists():
        # Confirmation prompt (unless --yes)
        if not yes:
            typer.echo(f"Source '{name}' already exists at {dest_path}")
            confirm = typer.confirm("Do you want to replace it?")
            if not confirm:
                typer.echo("Aborted.")
                raise typer.Exit(0)
        
        # Remove existing source
        try:
            if dest_path.is_symlink():
                dest_path.unlink()
            else:
                shutil.rmtree(dest_path)
            typer.echo(f"Removed existing source '{name}'")
        except Exception as e:
            typer.echo(f"Error removing existing source: {e}", err=True)
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
    
    typer.echo(f"{'Name':<{max_name}}  {'Type':<{max_type}}  Location")
    typer.echo("-" * (max_name + max_type + 60))
    
    for source in sources:
        typer.echo(f"{source['name']:<{max_name}}  {source['type']:<{max_type}}  {source['location']}")
    
    typer.echo(f"\nTotal: {len(sources)} source(s) configured")


@source_app.command("init")
def source_init(
    directory: str = typer.Argument(".", help="Directory to initialize (defaults to current directory)"),
    name: str = typer.Option(None, "--name", help="Name for the source (defaults to directory basename)"),
    description: str = typer.Option("A GUPPI tool source", "--description", help="Description of the source"),
    git: bool = typer.Option(True, "--git/--no-git", help="Initialize as git repository"),
    template: str = typer.Option("minimal", "--template", help="Template to use: 'minimal' or 'example'"),
):
    """
    Initialize a directory as a GUPPI tool source.

    Creates the basic structure for a tool source including pyproject.toml
    with [tool.guppi.source] metadata, README.md, and .gitignore.

    Examples:
        guppi tool source init                          # Init current directory
        guppi tool source init ~/my-tools               # Init specific directory
        guppi tool source init . --name my-tools        # Init with custom name
        guppi tool source init --template example       # Init with example tool
    """
    # Resolve directory path
    directory = os.path.expanduser(directory)  # Expand ~
    directory = os.path.abspath(directory)      # Make absolute
    target_path = Path(directory)

    # Determine source name
    if not name:
        name = target_path.name

    # Sanitize name (replace spaces and special chars with dashes)
    name = re.sub(r'[^a-zA-Z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)  # Collapse multiple dashes
    name = name.strip('-')  # Remove leading/trailing dashes

    # Create directory if it doesn't exist
    if not target_path.exists():
        typer.echo(f"Creating directory: {target_path}")
        target_path.mkdir(parents=True, exist_ok=True)

    # Check if already a valid source
    is_valid, source_meta = is_valid_source(target_path)
    if is_valid:
        typer.echo(f"Error: {target_path} is already a GUPPI tool source", err=True)
        if source_meta:
            typer.echo(f"  Source name: {source_meta.get('name', 'unknown')}", err=True)
        raise typer.Exit(1)

    # Check if directory is non-empty
    if target_path.exists() and any(target_path.iterdir()):
        typer.echo(f"Warning: Directory '{target_path}' is not empty")
        confirm = typer.confirm("Continue initializing in this directory?")
        if not confirm:
            typer.echo("Aborted")
            raise typer.Exit(0)

    # Create pyproject.toml from template
    typer.echo(f"Initializing GUPPI tool source '{name}'...")

    pyproject_content = load_and_render_template(
        "source/pyproject.toml",
        name=name,
        description=description
    )
    (target_path / "pyproject.toml").write_text(pyproject_content)

    # Create README.md from template
    readme_content = load_and_render_template(
        "source/README.md",
        name=name,
        description=description
    )
    (target_path / "README.md").write_text(readme_content)

    # Create .gitignore from template
    gitignore_content = load_and_render_template("source/gitignore")
    (target_path / ".gitignore").write_text(gitignore_content)

    # If template is "example", create example tool
    if template == "example":
        typer.echo("Creating example tool...")
        example_dir = target_path / "example-tool"
        example_dir.mkdir(exist_ok=True)

        # Create example tool pyproject.toml
        example_pyproject = load_and_render_template(
            "tool/pyproject.toml",
            tool_name="example",
            tool_name_underscore="example",
            description="Example GUPPI tool"
        )
        (example_dir / "pyproject.toml").write_text(example_pyproject)

        # Create example tool README.md
        example_readme = load_and_render_template(
            "tool/README.md",
            tool_name="example",
            description="Example GUPPI tool"
        )
        (example_dir / "README.md").write_text(example_readme)

        # Create .gitignore
        gitignore_content = load_and_render_template("tool/gitignore")
        (example_dir / ".gitignore").write_text(gitignore_content)

        # Create example tool source structure
        src_dir = example_dir / "src" / "guppi_example"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py
        example_init = load_and_render_template(
            "tool/src/guppi_TOOLNAME/__init__.py",
            tool_name="example"
        )
        (src_dir / "__init__.py").write_text(example_init)

        # Create cli.py
        example_cli = load_and_render_template(
            "tool/src/guppi_TOOLNAME/cli.py",
            tool_name="example",
            tool_name_underscore="example",
            description="Example GUPPI tool"
        )
        (src_dir / "cli.py").write_text(example_cli)

    # Git initialization
    if git:
        try:
            # Check if already a git repo
            git_dir = target_path / ".git"
            if not git_dir.exists():
                subprocess.run(["git", "init"], cwd=target_path, check=True, capture_output=True)
                subprocess.run(["git", "add", "."], cwd=target_path, check=True, capture_output=True)
                subprocess.run(
                    ["git", "commit", "-m", "Initialize GUPPI tool source"],
                    cwd=target_path,
                    check=True,
                    capture_output=True
                )
                typer.echo("✓ Initialized git repository")
        except subprocess.CalledProcessError as e:
            typer.echo(f"Warning: Git initialization failed: {e}", err=True)
        except FileNotFoundError:
            typer.echo("Warning: 'git' command not found, skipping git initialization", err=True)

    # Display success message
    typer.echo(f"\n✓ Initialized GUPPI tool source '{name}' at {target_path}")
    typer.echo("\nNext steps:")
    typer.echo("  1. Add tools to this source (each tool in its own directory)")
    typer.echo("  2. Each tool needs a pyproject.toml with [tool.guppi] metadata")
    typer.echo(f"  3. Add this source to GUPPI: guppi tool source add {name} {target_path}")

    if template == "example":
        typer.echo("\n📦 Example tool created in 'example-tool/' directory")
        typer.echo("   Install it with: guppi tool install example --from example-tool/")

    typer.echo("\nSee the README.md for more details.")


@app.command("init")
def tool_init(
    source_directory: str = typer.Argument(..., help="GUPPI source directory where the tool will be created"),
    tool_name: str = typer.Argument(..., help="Name for the tool"),
    description: str = typer.Option("A GUPPI tool", "--description", help="Description of the tool"),
    git: bool = typer.Option(True, "--git/--no-git", help="Initialize as git repository"),
    template: str = typer.Option("minimal", "--template", help="Template to use: 'minimal' or 'example'"),
):
    """
    Initialize a new GUPPI tool within a source directory.

    Creates a complete tool structure with pyproject.toml, CLI scaffolding,
    and package structure ready for development and installation.

    Examples:
        guppi tool init . my-tool                         # Create tool in current source
        guppi tool init ~/guppi-tools my-awesome-tool     # Create in specific source
        guppi tool init . demo --template example         # Create with example template
        guppi tool init . quick-tool --no-git             # Create without git init
    """
    # Validate and resolve source directory path
    source_directory = os.path.expanduser(source_directory)
    source_directory = os.path.abspath(source_directory)
    source_path = Path(source_directory)

    # Check source directory exists
    if not source_path.exists():
        typer.echo(f"Error: Source directory does not exist: {source_path}", err=True)
        raise typer.Exit(1)

    # Validate it's a GUPPI source
    is_valid, source_meta = is_valid_source(source_path)
    if not is_valid:
        typer.echo(f"Error: Not a valid GUPPI source: {source_path}", err=True)
        typer.echo(f"Initialize with: guppi tool source init {source_path}", err=True)
        raise typer.Exit(1)

    # Sanitize tool name
    tool_name_sanitized = sanitize_tool_name(tool_name)
    if not tool_name_sanitized:
        typer.echo(f"Error: Tool name '{tool_name}' is invalid after sanitization", err=True)
        raise typer.Exit(1)

    if tool_name != tool_name_sanitized:
        typer.echo(f"Tool name sanitized: '{tool_name}' → '{tool_name_sanitized}'")

    tool_name = tool_name_sanitized
    tool_name_underscore = tool_name_to_package(tool_name)

    # Create tool directory
    tool_dir = source_path / tool_name
    if tool_dir.exists():
        typer.echo(f"Error: Tool directory already exists: {tool_dir}", err=True)
        typer.echo("Remove it first or choose a different name.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Initializing GUPPI tool '{tool_name}'...")

    try:
        # Create tool directory structure
        tool_dir.mkdir(parents=True, exist_ok=True)
        src_dir = tool_dir / "src" / f"guppi_{tool_name_underscore}"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Create pyproject.toml
        pyproject_content = load_and_render_template(
            "tool/pyproject.toml",
            tool_name=tool_name,
            tool_name_underscore=tool_name_underscore,
            description=description
        )
        (tool_dir / "pyproject.toml").write_text(pyproject_content)

        # Create README.md
        readme_content = load_and_render_template(
            "tool/README.md",
            tool_name=tool_name,
            description=description
        )
        (tool_dir / "README.md").write_text(readme_content)

        # Create .gitignore
        gitignore_content = load_and_render_template("tool/gitignore")
        (tool_dir / ".gitignore").write_text(gitignore_content)

        # Create __init__.py
        init_content = load_and_render_template(
            "tool/src/guppi_TOOLNAME/__init__.py",
            tool_name=tool_name
        )
        (src_dir / "__init__.py").write_text(init_content)

        # Create cli.py from template
        cli_content = load_and_render_template(
            "tool/src/guppi_TOOLNAME/cli.py",
            tool_name=tool_name,
            tool_name_underscore=tool_name_underscore,
            description=description
        )
        (src_dir / "cli.py").write_text(cli_content)

        # Git initialization
        if git:
            try:
                subprocess.run(["git", "init"], cwd=tool_dir, check=True, capture_output=True)
                subprocess.run(["git", "add", "."], cwd=tool_dir, check=True, capture_output=True)
                subprocess.run(
                    ["git", "commit", "-m", f"Initialize GUPPI tool {tool_name}"],
                    cwd=tool_dir,
                    check=True,
                    capture_output=True
                )
                typer.echo("✓ Initialized git repository")
            except subprocess.CalledProcessError as e:
                typer.echo(f"Warning: Git initialization failed: {e}", err=True)
            except FileNotFoundError:
                typer.echo("Warning: 'git' command not found, skipping git initialization", err=True)

    except Exception as e:
        # Clean up on failure
        if tool_dir.exists():
            shutil.rmtree(tool_dir)
        typer.echo(f"Error: Failed to initialize tool: {e}", err=True)
        raise typer.Exit(1)

    # Display success message
    typer.echo(f"\n✓ Initialized GUPPI tool '{tool_name}' at {tool_dir}")
    typer.echo("\nNext steps:")
    typer.echo(f"  1. Edit src/guppi_{tool_name_underscore}/cli.py to implement your tool")
    typer.echo(f"  2. Install locally to test: guppi tool install {tool_name} --from {tool_dir}")
    typer.echo(f"  3. Run your tool: guppi {tool_name} --help")
    typer.echo("\nSee README.md for development instructions.")


@source_app.command("update")
def source_update(
    name: str = typer.Argument(None, help="Specific source to update (updates all if not provided)"),
):
    """
    Update tool sources (git pull).
    
    Updates git repositories in ~/.guppi/sources/.
    If no name is provided, updates all sources.
    
    Examples:
        guppi tool source update                # Update all sources
        guppi tool source update guppi-tools    # Update specific source
    """
    sources_dir = get_sources_dir()
    
    if name:
        # Update specific source
        source_path = sources_dir / name
        if not source_path.exists():
            typer.echo(f"Error: Source '{name}' not found", err=True)
            raise typer.Exit(1)
        
        sources_to_update = [(name, source_path)]
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
    
    for source_name, path in sources_to_update:
        # Skip symlinks (local sources)
        if path.is_symlink():
            typer.echo(f"⊘ Skipping '{source_name}' (local source)")
            skipped += 1
            continue
        
        # Check if it's a git repo
        git_dir = path / ".git"
        if not git_dir.exists():
            typer.echo(f"⊘ Skipping '{source_name}' (not a git repository)")
            skipped += 1
            continue
        
        typer.echo(f"Updating '{source_name}'...")
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


@app.command("update")
def tool_update(
    name: str = typer.Argument(None, help="Specific tool to update (updates all if not provided)"),
):
    """
    Update installed GUPPI tools.
    
    Updates tools that were installed via 'guppi tool install'.
    Uses 'uv tool upgrade' to update to the latest version.
    
    Examples:
        guppi tool update              # Update all installed guppi-* tools
        guppi tool update guppi-dummy  # Update specific tool
    """
    # Get list of installed guppi tools
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error listing installed tools: {e.stderr}", err=True)
        raise typer.Exit(1)
    
    # Parse installed tools and filter for guppi-* tools
    installed_tools = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("guppi-"):
            # Extract tool name (first word)
            tool_name = line.split()[0] if line.split() else line
            installed_tools.append(tool_name)
    
    if not installed_tools:
        typer.echo("No GUPPI tools installed")
        typer.echo("Install tools with: guppi tool install <name>")
        return
    
    # Determine which tools to update
    if name:
        # Update specific tool
        if not name.startswith("guppi-"):
            name = f"guppi-{name}"
        
        if name not in installed_tools:
            typer.echo(f"Error: Tool '{name}' is not installed", err=True)
            raise typer.Exit(1)
        
        tools_to_update = [name]
    else:
        # Update all tools
        tools_to_update = installed_tools
    
    # Update each tool
    updated = 0
    up_to_date = 0
    errors = 0
    
    for tool_name in tools_to_update:
        typer.echo(f"Updating '{tool_name}'...")
        try:
            result = subprocess.run(
                ["uv", "tool", "upgrade", tool_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check if anything was updated
            output = result.stdout + result.stderr
            if "Nothing to upgrade" in output or "already installed" in output:
                typer.echo(f"  ✓ Already up to date")
                up_to_date += 1
            else:
                typer.echo(f"  ✓ Updated")
                updated += 1
        except subprocess.CalledProcessError as e:
            typer.echo(f"  ✗ Error: {e.stderr}", err=True)
            errors += 1
    
    # Summary
    typer.echo()
    typer.echo(f"Updated: {updated}, Up-to-date: {up_to_date}, Errors: {errors}")


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
    from guppi.ui import format_tool_search_table
    
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
    
    # Display results with rich formatting
    format_tool_search_table(tools)


@app.command("list")
def list_tools(
    query: str = typer.Argument(None, help="Search query to filter tools (optional)"),
):
    """
    List installed GUPPI tools.
    
    Shows all tools that are currently installed and available for routing.
    Optionally filter by name or description.
    
    Examples:
        guppi tool list              # List all installed tools
        guppi tool list greeter      # Filter tools matching 'greeter'
    """
    import tomllib
    from guppi.ui import format_tool_list_table
    from guppi.discovery import discover_all_tools
    
    # Get list of available tools from sources to match metadata
    available_tools = {tool.name: tool for tool in discover_all_tools()}
    
    # Get uv tool directory
    try:
        tool_dir_result = subprocess.run(
            ["uv", "tool", "dir"],
            capture_output=True,
            text=True,
            check=True
        )
        uv_tool_dir = Path(tool_dir_result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        uv_tool_dir = None
    
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
                            # Try to get metadata from available tools
                            source = None
                            description = None
                            if tool_name in available_tools:
                                source = available_tools[tool_name].source
                                description = available_tools[tool_name].description
                            
                            # Try to get source from uv receipt if not in available tools
                            if not source and uv_tool_dir:
                                receipt_path = uv_tool_dir / item.name / "uv-receipt.toml"
                                if receipt_path.exists():
                                    try:
                                        with open(receipt_path, "rb") as f:
                                            receipt = tomllib.load(f)
                                        # Check if it's editable install
                                        requirements = receipt.get("tool", {}).get("requirements", [])
                                        for req in requirements:
                                            if req.get("editable"):
                                                editable_path = Path(req["editable"])
                                                # Check if it's in a known source
                                                for name, tool in available_tools.items():
                                                    if tool.path.resolve() == editable_path.resolve():
                                                        source = tool.source
                                                        description = tool.description
                                                        break
                                    except Exception:
                                        pass
                            
                            installed.append({
                                "name": tool_name,
                                "path": str(item),
                                "source": source or "unknown",
                                "description": description or "No description available"
                            })
                            seen.add(tool_name)
        except PermissionError:
            continue
    
    # Filter by query if provided
    if query:
        query_lower = query.lower()
        installed = [
            t for t in installed
            if query_lower in t["name"].lower() or query_lower in t["description"].lower()
        ]
        
        if not installed:
            typer.echo(f"No installed tools found matching '{query}'")
            return
    
    # Display with rich formatting
    format_tool_list_table(installed)


@app.command("install")
def install(
    name: str = typer.Argument(..., help="Name of the tool to install"),
    from_path: str = typer.Option(None, "--from", help="GitHub repo or local path (optional if tool is in sources)"),
    source: str = typer.Option(None, "--source", help="Source name to install from (required if tool exists in multiple sources)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Install a GUPPI tool.
    
    Examples:
        guppi tool install dummy                      # Install from sources
        guppi tool install dummy --source guppi-tools # Install from specific source
        guppi tool install dummy --from ~/dev/dummy   # Install from local path
        guppi tool install dummy --yes                # Reinstall without prompting
    """
    # If --from is provided, use it directly
    if from_path:
        _install_from_path(name, from_path, yes)
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
    _install_from_path(name, str(tool.path), yes)


def _install_from_path(name: str, from_path: str, yes: bool = False):
    """Helper to install a tool from a given path"""
    # Normalize tool name
    if not name.startswith("guppi-"):
        full_name = f"guppi-{name}"
    else:
        full_name = name
    
    # Check if tool is already installed
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        installed_tools = [line.split()[0] for line in result.stdout.strip().split("\n") if line and not line.startswith(" ") and not line.startswith("-")]
        
        is_installed = full_name in installed_tools
        
        if is_installed:
            # Confirmation prompt (unless --yes)
            if not yes:
                typer.echo(f"Tool '{full_name}' is already installed")
                confirm = typer.confirm("Do you want to reinstall it?")
                if not confirm:
                    typer.echo("Aborted.")
                    raise typer.Exit(0)
    except subprocess.CalledProcessError:
        # If uv tool list fails, continue with installation
        pass
    
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


@app.command("uninstall")
def tool_uninstall(
    name: str = typer.Argument(..., help="Name of the tool to uninstall"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Uninstall a GUPPI tool.
    
    Removes a tool that was installed via 'guppi tool install'.
    Uses 'uv tool uninstall' to remove the tool from the system.
    
    Examples:
        guppi tool uninstall dummy                  # Uninstall with confirmation
        guppi tool uninstall dummy --yes            # Skip confirmation
        guppi tool uninstall guppi-dummy            # Works with full name
    """
    # Normalize tool name
    if not name.startswith("guppi-"):
        full_name = f"guppi-{name}"
    else:
        full_name = name
    
    # Get list of installed tools
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error listing installed tools: {e.stderr}", err=True)
        raise typer.Exit(1)
    
    # Parse installed tools
    installed_tools = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("guppi-"):
            tool_name = line.split()[0] if line.split() else line
            installed_tools.append(tool_name)
    
    # Validate tool is installed
    if full_name not in installed_tools:
        typer.echo(f"Error: Tool '{full_name}' is not installed", err=True)
        typer.echo("Run 'guppi tool list' to see installed tools")
        raise typer.Exit(1)
    
    # Confirmation prompt (unless --yes)
    if not yes:
        typer.echo(f"This will uninstall: {full_name}")
        confirm = typer.confirm("Are you sure?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit(0)
    
    # Uninstall the tool
    typer.echo(f"Uninstalling {full_name}...")
    
    try:
        result = subprocess.run(
            ["uv", "tool", "uninstall", full_name],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Display output from uv if any
        output = result.stdout.strip() + result.stderr.strip()
        if output:
            typer.echo(output)
        
        typer.echo(f"\n✓ {full_name} uninstalled successfully!")
        
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error uninstalling {full_name}: {e.stderr}", err=True)
        raise typer.Exit(1)
