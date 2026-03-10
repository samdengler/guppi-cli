"""Skill management commands"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from giturlparse import parse as parse_git_url

from guppi.discovery import get_sources_dir, find_tool, find_all_tools, discover_all_tools, is_valid_source
from guppi.templates import load_and_render_template, sanitize_tool_name, tool_name_to_package

app = typer.Typer(help="Manage GUPPI skills")

CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"

# Create subcommand for source management
source_app = typer.Typer(help="Manage skill sources")
app.add_typer(source_app, name="source")


def _sync_skill_md(name: str):
    """Find SKILL.md from an installed guppi-<name> package and copy to ~/.claude/skills/."""
    full_name = name if name.startswith("guppi-") else f"guppi-{name}"
    package_name = full_name.replace("-", "_")
    short_name = name.removeprefix("guppi-")

    # Get uv tool directory
    try:
        result = subprocess.run(
            ["uv", "tool", "dir"],
            capture_output=True, text=True, check=True,
        )
        uv_tool_dir = Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        typer.echo("Warning: Could not find uv tool directory, skipping SKILL.md registration", err=True)
        return

    tool_env = uv_tool_dir / full_name
    if not tool_env.exists():
        return

    # Search for SKILL.md in the installed package
    skill_md = None
    for site_packages in tool_env.rglob("site-packages"):
        candidate = site_packages / package_name / "SKILL.md"
        if candidate.exists():
            skill_md = candidate
            break

    if not skill_md:
        typer.echo(f"Note: No SKILL.md found in {full_name} package", err=True)
        return

    # Copy to ~/.claude/skills/<name>/SKILL.md
    dest_dir = CLAUDE_SKILLS_DIR / short_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    shutil.copy2(skill_md, dest)
    typer.echo(f"✓ Registered skill '{short_name}' for Claude Code at {dest}")


def _remove_skill_md(name: str):
    """Remove a skill's SKILL.md from ~/.claude/skills/."""
    short_name = name.removeprefix("guppi-")
    skill_dir = CLAUDE_SKILLS_DIR / short_name
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
        typer.echo(f"✓ Removed skill '{short_name}' from Claude Code")


@source_app.command("add")
def source_add(
    name: Annotated[str, typer.Argument(help="Name for this source")],
    url: Annotated[str, typer.Argument(help="Git URL or local path")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
):
    """
    Add a skill source.

    Supports GitHub browser URLs with branches:
        https://github.com/owner/repo/tree/my-branch

    Examples:
        guppi skills source add guppi-skills https://github.com/samdengler/guppi-skills
        guppi skills source add guppi-skills https://github.com/samdengler/guppi-skills/tree/dev
        guppi skills source add local-skills /path/to/local/skills
        guppi skills source add guppi-skills <url> --yes  # Overwrite without prompting
    """
    sources_dir = get_sources_dir()
    dest_path = sources_dir / name

    if dest_path.exists():
        if not yes:
            typer.echo(f"Source '{name}' already exists at {dest_path}")
            confirm = typer.confirm("Do you want to replace it?")
            if not confirm:
                typer.echo("Aborted.")
                raise typer.Exit(0)

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

    local_path = Path(url)
    if local_path.exists() and local_path.is_dir():
        try:
            dest_path.symlink_to(local_path.resolve())
            typer.echo(f"✓ Linked local source '{name}' → {local_path}")
        except Exception as e:
            typer.echo(f"Error creating symlink: {e}", err=True)
            raise typer.Exit(1)
    else:
        try:
            parsed = parse_git_url(url)
            branch = parsed.branch if parsed.valid else None
            clone_url = url.split("/tree/")[0] if branch else url

            cmd = ["git", "clone"]
            if branch:
                cmd += ["--branch", branch]
            cmd += [clone_url, str(dest_path)]

            subprocess.run(cmd, check=True, capture_output=True, text=True)

            msg = f"✓ Cloned source '{name}' to {dest_path}"
            if branch:
                msg += f" (branch: {branch})"
            typer.echo(msg)
        except subprocess.CalledProcessError as e:
            typer.echo(f"Error cloning repository: {e.stderr}", err=True)
            raise typer.Exit(1)
        except FileNotFoundError:
            typer.echo("Error: 'git' command not found", err=True)
            raise typer.Exit(1)


@source_app.command("list")
def source_list(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all skill sources.

    Shows configured sources with their paths and types (git/local).
    """
    sources_dir = get_sources_dir()

    if not sources_dir.exists():
        typer.echo("No sources configured")
        typer.echo("\nAdd sources with: guppi skills source add <name> <url>")
        return

    sources = []
    for source_path in sources_dir.iterdir():
        if not source_path.is_dir():
            continue

        name = source_path.name

        if source_path.is_symlink():
            source_type = "local"
            target = source_path.resolve()
            location = str(target)
            branch = None
        elif (source_path / ".git").exists():
            source_type = "git"
            try:
                result = subprocess.run(
                    ["git", "-C", str(source_path), "remote", "get-url", "origin"],
                    capture_output=True, text=True, check=True,
                )
                location = result.stdout.strip()
            except subprocess.CalledProcessError:
                location = str(source_path)
            try:
                result = subprocess.run(
                    ["git", "-C", str(source_path), "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True, text=True, check=True,
                )
                branch = result.stdout.strip()
            except subprocess.CalledProcessError:
                branch = None
        else:
            source_type = "unknown"
            location = str(source_path)
            branch = None

        sources.append({
            "name": name,
            "type": source_type,
            "location": location,
            "branch": branch,
        })

    if not sources:
        typer.echo("No sources configured")
        typer.echo("\nAdd sources with: guppi skills source add <name> <url>")
        return

    sources.sort(key=lambda x: x["name"])

    if json_output:
        import json
        for source in sources:
            source["local_path"] = str((sources_dir / source["name"]).resolve())
        typer.echo(json.dumps(sources, indent=2))
        return

    typer.echo("Skill sources:\n")
    max_name = max(len(s["name"]) for s in sources)
    max_type = max(len(s["type"]) for s in sources)
    max_branch = max((len(s["branch"] or "") for s in sources), default=0)
    max_branch = max(max_branch, len("Branch"))

    typer.echo(f"{'Name':<{max_name}}  {'Type':<{max_type}}  {'Branch':<{max_branch}}  Location")
    typer.echo("-" * (max_name + max_type + max_branch + 60))

    for source in sources:
        branch_display = source["branch"] or "-"
        typer.echo(f"{source['name']:<{max_name}}  {source['type']:<{max_type}}  {branch_display:<{max_branch}}  {source['location']}")

    typer.echo(f"\nTotal: {len(sources)} source(s) configured")


@source_app.command("init")
def source_init(
    directory: Annotated[str, typer.Argument(help="Directory to initialize (defaults to current directory)")] = ".",
    name: Annotated[str | None, typer.Option("--name", help="Name for the source (defaults to directory basename)")] = None,
    description: Annotated[str, typer.Option("--description", help="Description of the source")] = "A GUPPI skill source",
    git: Annotated[bool, typer.Option("--git/--no-git", help="Initialize as git repository")] = True,
):
    """
    Initialize a directory as a GUPPI skill source.

    Creates the basic structure for a skill source including pyproject.toml
    with [tool.guppi.source] metadata, README.md, and .gitignore.

    Examples:
        guppi skills source init                          # Init current directory
        guppi skills source init ~/my-skills              # Init specific directory
        guppi skills source init . --name my-skills       # Init with custom name
    """
    directory = os.path.expanduser(directory)
    directory = os.path.abspath(directory)
    target_path = Path(directory)

    if not name:
        name = target_path.name

    name = re.sub(r'[^a-zA-Z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')

    if not target_path.exists():
        typer.echo(f"Creating directory: {target_path}")
        target_path.mkdir(parents=True, exist_ok=True)

    is_valid, source_meta = is_valid_source(target_path)
    if is_valid:
        typer.echo(f"Error: {target_path} is already a GUPPI skill source", err=True)
        if source_meta:
            typer.echo(f"  Source name: {source_meta.get('name', 'unknown')}", err=True)
        raise typer.Exit(1)

    if target_path.exists() and any(target_path.iterdir()):
        typer.echo(f"Warning: Directory '{target_path}' is not empty")
        confirm = typer.confirm("Continue initializing in this directory?")
        if not confirm:
            typer.echo("Aborted")
            raise typer.Exit(0)

    typer.echo(f"Initializing GUPPI skill source '{name}'...")

    pyproject_content = load_and_render_template(
        "source/pyproject.toml",
        name=name,
        description=description,
    )
    (target_path / "pyproject.toml").write_text(pyproject_content)

    readme_content = load_and_render_template(
        "source/README.md",
        name=name,
        description=description,
    )
    (target_path / "README.md").write_text(readme_content)

    gitignore_content = load_and_render_template("source/gitignore")
    (target_path / ".gitignore").write_text(gitignore_content)

    if git:
        try:
            git_dir = target_path / ".git"
            if not git_dir.exists():
                subprocess.run(["git", "init"], cwd=target_path, check=True, capture_output=True)
                subprocess.run(["git", "add", "."], cwd=target_path, check=True, capture_output=True)
                subprocess.run(
                    ["git", "commit", "-m", "Initialize GUPPI skill source"],
                    cwd=target_path, check=True, capture_output=True,
                )
                typer.echo("✓ Initialized git repository")
        except subprocess.CalledProcessError as e:
            typer.echo(f"Warning: Git initialization failed: {e}", err=True)
        except FileNotFoundError:
            typer.echo("Warning: 'git' command not found, skipping git initialization", err=True)

    typer.echo(f"\n✓ Initialized GUPPI skill source '{name}' at {target_path}")
    typer.echo("\nNext steps:")
    typer.echo("  1. Add skills to this source (each skill in its own directory)")
    typer.echo("  2. Each skill needs a pyproject.toml with [tool.guppi] metadata")
    typer.echo(f"  3. Add this source to GUPPI: guppi skills source add {name} {target_path}")
    typer.echo("\nSee the README.md for more details.")


@source_app.command("update")
def source_update(
    name: Annotated[str | None, typer.Argument(help="Specific source to update (updates all if not provided)")] = None,
):
    """
    Update skill sources (git pull).

    Updates git repositories in ~/.guppi/sources/.
    If no name is provided, updates all sources.

    Examples:
        guppi skills source update                # Update all sources
        guppi skills source update guppi-skills   # Update specific source
    """
    sources_dir = get_sources_dir()

    if name:
        source_path = sources_dir / name
        if not source_path.exists():
            typer.echo(f"Error: Source '{name}' not found", err=True)
            raise typer.Exit(1)
        sources_to_update = [(name, source_path)]
    else:
        sources_to_update = [
            (path.name, path)
            for path in sources_dir.iterdir()
            if path.is_dir()
        ]
        if not sources_to_update:
            typer.echo("No sources to update")
            return

    updated = 0
    skipped = 0
    errors = 0

    for source_name, path in sources_to_update:
        if path.is_symlink():
            typer.echo(f"⊘ Skipping '{source_name}' (local source)")
            skipped += 1
            continue

        git_dir = path / ".git"
        if not git_dir.exists():
            typer.echo(f"⊘ Skipping '{source_name}' (not a git repository)")
            skipped += 1
            continue

        typer.echo(f"Updating '{source_name}'...")
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=path, check=True, capture_output=True, text=True,
            )
            if "Already up to date" in result.stdout:
                typer.echo("  ✓ Already up to date")
            else:
                typer.echo("  ✓ Updated")
            updated += 1
        except subprocess.CalledProcessError as e:
            typer.echo(f"  ✗ Error: {e.stderr}", err=True)
            errors += 1

    typer.echo()
    typer.echo(f"Updated: {updated}, Skipped: {skipped}, Errors: {errors}")


@app.command("update")
def skill_update(
    name: Annotated[str | None, typer.Argument(help="Specific skill to update (updates all if not provided)")] = None,
):
    """
    Update installed GUPPI skills.

    Updates skills that were installed via 'guppi skills install'.
    Uses 'uv tool upgrade' to update to the latest version.

    Examples:
        guppi skills update              # Update all installed guppi-* skills
        guppi skills update spiker       # Update specific skill
    """
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error listing installed skills: {e.stderr}", err=True)
        raise typer.Exit(1)

    installed_skills = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("guppi-"):
            skill_name = line.split()[0] if line.split() else line
            installed_skills.append(skill_name)

    if not installed_skills:
        typer.echo("No GUPPI skills installed")
        typer.echo("Install skills with: guppi skills install <name>")
        return

    if name:
        if not name.startswith("guppi-"):
            name = f"guppi-{name}"
        if name not in installed_skills:
            typer.echo(f"Error: Skill '{name}' is not installed", err=True)
            raise typer.Exit(1)
        skills_to_update = [name]
    else:
        skills_to_update = installed_skills

    updated = 0
    up_to_date = 0
    errors = 0

    for skill_name in skills_to_update:
        typer.echo(f"Updating '{skill_name}'...")
        try:
            result = subprocess.run(
                ["uv", "tool", "upgrade", skill_name],
                capture_output=True, text=True, check=True,
            )
            output = result.stdout + result.stderr
            if "Nothing to upgrade" in output or "already installed" in output:
                typer.echo("  ✓ Already up to date")
                up_to_date += 1
            else:
                typer.echo("  ✓ Updated")
                updated += 1
            # Re-sync SKILL.md after upgrade
            _sync_skill_md(skill_name)
        except subprocess.CalledProcessError as e:
            typer.echo(f"  ✗ Error: {e.stderr}", err=True)
            errors += 1

    typer.echo()
    typer.echo(f"Updated: {updated}, Up-to-date: {up_to_date}, Errors: {errors}")


@app.command("search")
def search(
    query: Annotated[str | None, typer.Argument(help="Search query (optional - shows all if not provided)")] = None,
):
    """
    Search for available skills in all sources.

    Examples:
        guppi skills search          # List all available skills
        guppi skills search spiker   # Search for skills matching 'spiker'
    """
    from guppi.ui import format_tool_search_table

    tools = discover_all_tools()

    if not tools:
        typer.echo("No skills found in sources")
        typer.echo("Add a source with: guppi skills source add <name> <url>")
        return

    if query:
        query_lower = query.lower()
        tools = [
            t for t in tools
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]
        if not tools:
            typer.echo(f"No skills found matching '{query}'")
            return

    format_tool_search_table(tools)


@app.command("list")
def list_skills(
    query: Annotated[str | None, typer.Argument(help="Search query to filter skills (optional)")] = None,
):
    """
    List installed GUPPI skills.

    Shows all skills that are currently installed and available.
    Optionally filter by name or description.

    Examples:
        guppi skills list              # List all installed skills
        guppi skills list spiker       # Filter skills matching 'spiker'
    """
    import tomllib
    from guppi.ui import format_tool_list_table
    from guppi.discovery import discover_all_tools

    available_tools = {tool.name: tool for tool in discover_all_tools()}

    try:
        tool_dir_result = subprocess.run(
            ["uv", "tool", "dir"],
            capture_output=True, text=True, check=True,
        )
        uv_tool_dir = Path(tool_dir_result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        uv_tool_dir = None

    installed = []

    path_env = subprocess.run(
        ["printenv", "PATH"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    path_dirs = [Path(p) for p in path_env.split(":") if p]

    seen = set()
    for path_dir in path_dirs:
        if not path_dir.exists():
            continue

        try:
            for item in path_dir.iterdir():
                if item.name.startswith("guppi-") and item.is_file():
                    if item.stat().st_mode & 0o111:
                        tool_name = item.name.replace("guppi-", "")
                        if tool_name not in seen:
                            source = None
                            description = None
                            if tool_name in available_tools:
                                source = available_tools[tool_name].source
                                description = available_tools[tool_name].description

                            if not source and uv_tool_dir:
                                receipt_path = uv_tool_dir / item.name / "uv-receipt.toml"
                                if receipt_path.exists():
                                    try:
                                        with open(receipt_path, "rb") as f:
                                            receipt = tomllib.load(f)
                                        requirements = receipt.get("tool", {}).get("requirements", [])
                                        for req in requirements:
                                            if req.get("editable"):
                                                editable_path = Path(req["editable"])
                                                for tname, tool in available_tools.items():
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
                                "description": description or "No description available",
                            })
                            seen.add(tool_name)
        except PermissionError:
            continue

    if query:
        query_lower = query.lower()
        installed = [
            t for t in installed
            if query_lower in t["name"].lower() or query_lower in t["description"].lower()
        ]
        if not installed:
            typer.echo(f"No installed skills found matching '{query}'")
            return

    format_tool_list_table(installed)


@app.command("install")
def install(
    name: Annotated[str, typer.Argument(help="Name of the skill to install")],
    from_path: Annotated[str | None, typer.Option("--from", help="GitHub repo or local path (optional if skill is in sources)")] = None,
    source: Annotated[str | None, typer.Option("--source", help="Source name to install from (required if skill exists in multiple sources)")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
):
    """
    Install a GUPPI skill.

    Installs the CLI tool via uv and registers SKILL.md for Claude Code discovery.

    Examples:
        guppi skills install spiker                        # Install from sources
        guppi skills install spiker --source guppi-skills  # Install from specific source
        guppi skills install spiker --from ~/dev/spiker    # Install from local path
        guppi skills install spiker --yes                  # Reinstall without prompting
    """
    if from_path:
        _install_from_path(name, from_path, yes)
        return

    typer.echo(f"Looking for '{name}' in sources...")

    all_matches = find_all_tools(name)

    if not all_matches:
        typer.echo(f"Error: Skill '{name}' not found in any source", err=True)
        typer.echo("Try: guppi skills search", err=True)
        typer.echo(f"Or: guppi skills install {name} --from <path>", err=True)
        raise typer.Exit(1)

    if len(all_matches) > 1 and not source:
        typer.echo(f"Error: Skill '{name}' found in multiple sources:", err=True)
        for match in all_matches:
            typer.echo(f"  - {match.source}", err=True)
        typer.echo(f"\nPlease specify a source:", err=True)
        typer.echo(f"  guppi skills install {name} --source <source-name>", err=True)
        raise typer.Exit(1)

    tool = find_tool(name, source)

    if not tool:
        if source:
            typer.echo(f"Error: Skill '{name}' not found in source '{source}'", err=True)
        else:
            typer.echo(f"Error: Skill '{name}' not found", err=True)
        raise typer.Exit(1)

    typer.echo(f"Found '{name}' in source '{tool.source}'")
    _install_from_path(name, str(tool.path), yes)


def _install_from_path(name: str, from_path: str, yes: bool = False):
    """Helper to install a skill from a given path."""
    if not name.startswith("guppi-"):
        full_name = f"guppi-{name}"
    else:
        full_name = name

    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True, text=True, check=True,
        )
        installed_tools = [
            line.split()[0] for line in result.stdout.strip().split("\n")
            if line and not line.startswith(" ") and not line.startswith("-")
        ]

        is_installed = full_name in installed_tools

        if is_installed:
            if not yes:
                typer.echo(f"Skill '{full_name}' is already installed")
                confirm = typer.confirm("Do you want to reinstall it?")
                if not confirm:
                    typer.echo("Aborted.")
                    raise typer.Exit(0)
    except subprocess.CalledProcessError:
        pass

    typer.echo(f"Installing skill '{name}' from {from_path}...")

    if Path(from_path).exists():
        cmd = ["uv", "tool", "install", "--editable", from_path]
    else:
        cmd = ["uv", "tool", "install", f"git+{from_path}"]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        typer.echo(result.stdout)
        typer.echo(f"✓ Skill '{name}' installed successfully!")
        # Register SKILL.md for Claude Code discovery
        _sync_skill_md(name)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error installing skill: {e.stderr}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)


@app.command("uninstall")
def skill_uninstall(
    name: Annotated[str, typer.Argument(help="Name of the skill to uninstall")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
):
    """
    Uninstall a GUPPI skill.

    Removes the CLI tool via uv and unregisters from Claude Code discovery.

    Examples:
        guppi skills uninstall spiker              # Uninstall with confirmation
        guppi skills uninstall spiker --yes        # Skip confirmation
        guppi skills uninstall guppi-spiker        # Works with full name
    """
    if not name.startswith("guppi-"):
        full_name = f"guppi-{name}"
    else:
        full_name = name

    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error listing installed skills: {e.stderr}", err=True)
        raise typer.Exit(1)

    installed_tools = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("guppi-"):
            tool_name = line.split()[0] if line.split() else line
            installed_tools.append(tool_name)

    if full_name not in installed_tools:
        typer.echo(f"Error: Skill '{full_name}' is not installed", err=True)
        typer.echo("Run 'guppi skills list' to see installed skills")
        raise typer.Exit(1)

    if not yes:
        typer.echo(f"This will uninstall: {full_name}")
        confirm = typer.confirm("Are you sure?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit(0)

    typer.echo(f"Uninstalling {full_name}...")

    try:
        result = subprocess.run(
            ["uv", "tool", "uninstall", full_name],
            check=True, capture_output=True, text=True,
        )
        output = result.stdout.strip() + result.stderr.strip()
        if output:
            typer.echo(output)

        # Remove SKILL.md from Claude Code
        _remove_skill_md(full_name)

        typer.echo(f"\n✓ {full_name} uninstalled successfully!")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error uninstalling {full_name}: {e.stderr}", err=True)
        raise typer.Exit(1)
