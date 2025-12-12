"""Example GUPPI tool"""
import typer

app = typer.Typer(help="Example GUPPI tool")

@app.command()
def hello(name: str = typer.Argument("world")):
    """Say hello"""
    typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
