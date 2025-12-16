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
        title="Available Tools",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("Tool", style="green", no_wrap=True)
    table.add_column("Source", style="magenta")
    table.add_column("Location", style="dim")
    table.add_column("Description", style="white")
    
    for tool in sorted(tools, key=lambda t: t.name):
        source = tool.source or "unknown"
        location = shorten_path(tool.source_location) if tool.source_location else "unknown"
        table.add_row(tool.name, source, location, tool.description)
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(tools)} tool(s) found[/dim]")


def format_tool_list_table(installed_tools: List[Dict[str, str]]) -> None:
    """
    Display installed tools in a formatted table with rounded corners.
    
    Args:
        installed_tools: List of dicts with 'name', 'path', 'source', and 'description' keys
    """
    console = Console()
    
    if not installed_tools:
        console.print("[yellow]No tools installed[/yellow]")
        console.print("\n[dim]Install tools with:[/dim] guppi tool install <name>")
        return
    
    table = Table(
        title="Installed Tools",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("Tool", style="green", no_wrap=True)
    table.add_column("Source", style="magenta")
    table.add_column("Description", style="white")
    table.add_column("Location", style="dim")
    
    for tool in sorted(installed_tools, key=lambda x: x["name"]):
        # Shorten path for display
        path = shorten_path(tool["path"])
        source = tool.get("source", "unknown")
        description = tool.get("description", "No description available")
        table.add_row(tool["name"], source, description, path)
    
    console.print(table)
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
