"""Upgrade command for guppi CLI"""

import subprocess
import typer

app = typer.Typer(help="Upgrade guppi CLI")


@app.callback(invoke_without_command=True)
def upgrade(ctx: typer.Context):
    """
    Upgrade guppi CLI to the latest version.
    
    Uses uv to upgrade the guppi installation.
    """
    if ctx.invoked_subcommand is not None:
        return
    
    try:
        typer.echo("Upgrading guppi...")
        result = subprocess.run(
            ["uv", "tool", "upgrade", "guppi"],
            check=True,
            capture_output=True,
            text=True
        )
        typer.echo(result.stdout)
        typer.echo("✓ guppi upgraded successfully!")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error upgrading guppi: {e.stderr}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
