"""Initialize GUPPI for agent discovery"""

import shutil
from pathlib import Path

import typer

from guppi.agents import get_active_targets

app = typer.Typer(help="Initialize GUPPI")


@app.callback(invoke_without_command=True)
def init():
    """Register GUPPI with AI agents for skill discovery."""
    # Find bundled SKILL.md
    package_dir = Path(__file__).parent.parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        # Fallback: look in repo root (development mode)
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found in guppi package", err=True)
        raise typer.Exit(1)

    targets = get_active_targets()
    if not targets:
        typer.echo("No supported agents detected (~/.claude or ~/.kiro)", err=True)
        typer.echo("Install Claude Code or Kiro first.", err=True)
        raise typer.Exit(1)

    for agent_name, skills_dir in targets.items():
        dest_dir = skills_dir / "guppi"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_md, dest_dir / "SKILL.md")

    agents = " and ".join(targets.keys())
    typer.echo(f"✓ Registered GUPPI for {agents}")
    typer.echo("\nYour agent will now search for available skills before building from scratch.")
    typer.echo("Manage skills with: guppi skills --help")
