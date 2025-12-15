"""GUPPI {tool_name} tool CLI"""

import typer
from typing_extensions import Annotated

app = typer.Typer(help="{description}")

@app.command()
def hello(
    name: Annotated[str, typer.Argument(help="Name to greet")] = "World",
    excited: Annotated[bool, typer.Option("--excited", "-e", help="Add excitement")] = False,
):
    """Say hello with optional excitement"""
    greeting = f"Hello, {{name}}!"
    if excited:
        greeting += " 🎉"
    typer.echo(greeting)

@app.command()
def info():
    """Show tool information"""
    from guppi_{tool_name_underscore} import __version__
    typer.echo(f"GUPPI {tool_name} v{{__version__}}")
    typer.echo("{description}")

if __name__ == "__main__":
    app()
