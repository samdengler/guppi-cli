"""Upgrade command for guppi CLI"""

import subprocess
import typer

from guppi.__version__ import __version__

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
        current_version = __version__
        typer.echo(f"Current version: {current_version}")
        typer.echo("Checking for updates...")
        
        result = subprocess.run(
            ["uv", "tool", "upgrade", "guppi"],
            check=True,
            capture_output=True,
            text=True
        )
        
        output = result.stdout.strip() + result.stderr.strip()
        
        # Check if already up-to-date
        if "Nothing to upgrade" in output or "Nothing to upgrade" in result.stdout:
            typer.echo(f"✓ guppi is already up-to-date (version {current_version})")
        else:
            # Show uv output which includes version changes
            if output:
                typer.echo(output)
            typer.echo("✓ guppi upgraded successfully!")
            typer.echo("\nRun 'guppi --version' to see the new version")
            
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error upgrading guppi: {e.stderr}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
