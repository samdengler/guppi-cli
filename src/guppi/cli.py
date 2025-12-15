"""GUPPI CLI - Plugin framework for composing tools"""

import sys
import typer

from guppi.commands import tool, upgrade, uninstall
from guppi.router import route_to_tool
from guppi.__version__ import __version__


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"guppi version {__version__}")
        raise typer.Exit()


# Create main app
app = typer.Typer(
    help="GUPPI - General Use Personal Program Interface",
    add_completion=False,
    no_args_is_help=True,
)

# Register subcommands
app.add_typer(tool.app, name="tool")
app.add_typer(upgrade.app, name="upgrade")
app.add_typer(uninstall.app, name="uninstall")


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """GUPPI - General Use Personal Program Interface"""
    pass


def main_entry():
    """
    Main entry point that handles both subcommands and tool routing.
    """
    # Check if we have args
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        
        # If it's a flag (starts with -) or a known subcommand, let Typer handle it
        if first_arg.startswith("-") or first_arg in ["tool", "upgrade", "uninstall"]:
            app()
            return
        
        # Otherwise, try to route to a tool
        tool_name = first_arg
        tool_args = sys.argv[2:]
        exit_code = route_to_tool(tool_name, tool_args)
        sys.exit(exit_code)
    else:
        # No args, show help
        app()


if __name__ == "__main__":
    main_entry()
