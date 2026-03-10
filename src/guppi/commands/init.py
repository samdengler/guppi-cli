"""Initialize GUPPI for agent discovery"""

import shutil
from pathlib import Path

import typer

app = typer.Typer(help="Initialize GUPPI")

CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"


@app.callback(invoke_without_command=True)
def init():
    """Register GUPPI with Claude Code for skill discovery."""
    # Find bundled SKILL.md
    package_dir = Path(__file__).parent.parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        # Fallback: look in repo root (development mode)
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found in guppi package", err=True)
        raise typer.Exit(1)

    # Copy to ~/.claude/skills/guppi/SKILL.md
    dest_dir = CLAUDE_SKILLS_DIR / "guppi"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    shutil.copy2(skill_md, dest)

    typer.echo(f"✓ Registered GUPPI for Claude Code at {dest}")
    typer.echo("\nClaude will now search for available skills before building from scratch.")
    typer.echo("Manage skills with: guppi skills --help")
