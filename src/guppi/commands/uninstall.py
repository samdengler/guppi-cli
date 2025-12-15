"""Uninstall command for guppi CLI"""

import subprocess
import typer

from guppi.__version__ import __version__
from guppi.discovery import get_guppi_home

app = typer.Typer(help="Uninstall guppi CLI")


@app.callback(invoke_without_command=True)
def uninstall(
    ctx: typer.Context,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Uninstall guppi CLI from the system.

    This removes the guppi CLI tool but preserves your .guppi directory
    with all sources and tool configurations.

    To reinstall: uv tool install guppi
    """
    if ctx.invoked_subcommand is not None:
        return

    # Show what will be preserved
    guppi_home = get_guppi_home()

    typer.echo(f"Current version: {__version__}")
    typer.echo("This will uninstall the guppi CLI tool.")
    typer.echo(f"Your configuration in {guppi_home} will be preserved.")
    typer.echo()

    # Confirmation prompt (unless --yes)
    if not yes:
        confirm = typer.confirm("Are you sure you want to uninstall guppi?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit(0)

    try:
        typer.echo("Uninstalling guppi...")

        result = subprocess.run(
            ["uv", "tool", "uninstall", "guppi"],
            check=True,
            capture_output=True,
            text=True
        )

        # Display output from uv if any
        output = result.stdout.strip() + result.stderr.strip()
        if output:
            typer.echo(output)

        typer.echo("\n✓ guppi CLI uninstalled successfully!")
        typer.echo(f"\nYour configuration is preserved at: {guppi_home}")
        typer.echo("\nTo reinstall:")
        typer.echo("  uv tool install guppi")

    except subprocess.CalledProcessError as e:
        typer.echo(f"Error uninstalling guppi: {e.stderr}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
