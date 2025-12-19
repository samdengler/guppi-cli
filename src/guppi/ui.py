"""Rich UI formatting helpers for GUPPI CLI"""

from typing import List, Dict
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


def shorten_path(path: str) -> str:
    """
    Shorten a file path for display.
    
    - Replaces home directory with ~
    - Shows relative path if in current directory
    - Returns full path otherwise
    
    Args:
        path: Full path to shorten
    
    Returns:
        Shortened path string
    """
    path_obj = Path(path)
    home = Path.home()
    cwd = Path.cwd()
    
    # Try home directory replacement
    try:
        rel_to_home = path_obj.relative_to(home)
        return f"~/{rel_to_home}"
    except ValueError:
        pass
    
    # Try current directory relative
    try:
        rel_to_cwd = path_obj.relative_to(cwd)
        return str(rel_to_cwd)
    except ValueError:
        pass
    
    # Return full path as fallback
    return str(path_obj)


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
        title="[bold cyan]Available Tools[/bold cyan]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
        title_style="bold cyan"
    )
    
    # Consistent column styling
    table.add_column("Tool", style="bold green", no_wrap=True, width=20)
    table.add_column("Source", style="blue", width=15)
    table.add_column("Description", overflow="fold")
    table.add_column("Location", style="dim", width=30)
    
    for tool in sorted(tools, key=lambda t: t.name):
        source = tool.source or "[dim]unknown[/dim]"
        location = shorten_path(tool.source_location) if tool.source_location else "[dim]unknown[/dim]"
        description = tool.description or "[dim]No description[/dim]"
        table.add_row(tool.name, source, description, location)
    
    console.print(table)
    console.print(f"\n[dim cyan]Total: {len(tools)} tool(s) found[/dim cyan]")


def format_tool_list_table(installed_tools: List[Dict[str, str]]) -> None:
    """
    Display installed tools in a formatted table with rounded corners.
    
    Args:
        installed_tools: List of dicts with 'name', 'path', 'source', and 'description' keys
    """
    console = Console()
    
    if not installed_tools:
        console.print("[yellow]No tools installed[/yellow]")
        console.print("\n[dim]Install tools with:[/dim] [cyan]guppi tool install <name>[/cyan]")
        return
    
    table = Table(
        title="[bold green]Installed Tools[/bold green]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style="green",
        title_style="bold green"
    )
    
    # Consistent column styling - matches search table order
    table.add_column("Tool", style="bold green", no_wrap=True, width=20)
    table.add_column("Source", style="blue", width=15)
    table.add_column("Description", overflow="fold")
    table.add_column("Location", style="dim", width=30)
    
    for tool in sorted(installed_tools, key=lambda x: x["name"]):
        # Shorten path for display
        path = shorten_path(tool["path"])
        source = tool.get("source", "unknown")
        # Mark unknown sources with dim styling
        if source == "unknown":
            source = "[dim]unknown[/dim]"
        description = tool.get("description", "No description available")
        if description == "No description available":
            description = "[dim]No description available[/dim]"
        table.add_row(tool["name"], source, description, path)
    
    console.print(table)
    console.print(f"\n[dim green]Total: {len(installed_tools)} tool(s) installed[/dim green]")


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
