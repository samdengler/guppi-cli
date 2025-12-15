"""Rich UI formatting helpers for GUPPI CLI"""

from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


def format_tool_search_table(tools: List) -> None:
    """
    Display tool search results in a formatted table with rounded corners.
    
    Args:
        tools: List of tool objects with name, version, source, and description
    """
    console = Console()
    
    if not tools:
        console.print("[yellow]No tools found[/yellow]")
        return
    
    table = Table(
        title="Available Tools",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("Tool", style="green", no_wrap=True)
    table.add_column("Source", style="magenta")
    table.add_column("Description", style="white")
    
    for tool in sorted(tools, key=lambda t: t.name):
        source = tool.source or "unknown"
        table.add_row(tool.name, source, tool.description)
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(tools)} tool(s) found[/dim]")


def format_tool_list_panel(installed_tools: List[Dict[str, str]]) -> None:
    """
    Display installed tools in a styled panel with rounded box.
    
    Args:
        installed_tools: List of dicts with 'name' and 'path' keys
    """
    console = Console()
    
    if not installed_tools:
        console.print("[yellow]No tools installed[/yellow]")
        console.print("\n[dim]Install tools with:[/dim] guppi tool install <name>")
        return
    
    # Build tool list text
    tool_text = Text()
    for tool in sorted(installed_tools, key=lambda x: x["name"]):
        tool_text.append(f"• {tool['name']}", style="green bold")
        tool_text.append(f"\n  {tool['path']}\n", style="dim")
    
    panel = Panel(
        tool_text,
        title="Installed Tools",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print(f"\n[dim]Total: {len(installed_tools)} tool(s) installed[/dim]")


def show_welcome_panel() -> None:
    """Display styled welcome panel for main help screen."""
    console = Console()
    
    welcome_text = (
        "[bold cyan]GUPPI[/bold cyan] - General Use Personal Program Interface\n"
        "[dim]A plugin framework for composing deterministic tools[/dim]"
    )
    
    panel = Panel(
        welcome_text,
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()  # Add spacing before regular help
