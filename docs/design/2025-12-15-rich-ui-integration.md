# Rich Library UI Integration

**Issue**: guppi-cli-6wd  
**Status**: Design  
**Date**: 2025-12-15

## Overview

Integrate the [Rich](https://rich.readthedocs.io/) library to enhance GUPPI CLI's visual presentation with formatted tables, styled panels, and improved help screens.

## Motivation

Current CLI output is plain text which:
- Lacks visual hierarchy and structure
- Makes it difficult to scan long lists of tools
- Doesn't provide clear visual separation between sections
- Looks dated compared to modern CLI tools

Rich provides:
- Beautiful tables with customizable borders
- Styled panels with rounded corners
- Syntax highlighting and color theming
- Better terminal compatibility

## Goals

1. **Add rich as a core dependency** - Available throughout the project
2. **Enhance `guppi tool search`** - Display results in a formatted table
3. **Enhance `guppi tool list`** - Display installed tools in a styled panel
4. **Enhance main help screen** - Display help in a styled panel

## Non-Goals

- Replace all typer.echo() calls with rich (incremental adoption)
- Add extensive color schemes (keep it simple)
- Support non-terminal output formats (JSON, etc.) - rich auto-detects

## Technical Design

### Dependency Addition

```bash
uv add rich
```

Add to `pyproject.toml` dependencies:
```toml
[project]
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
]
```

### 1. Tool Search Enhancement

**Current**: Plain text list output
```
dummy (0.1.0) - Example dummy tool for testing GUPPI
beads (1.0.0) - Issue tracking system
```

**Proposed**: Rich table with rounded corners

```python
from rich.console import Console
from rich.table import Table

def search_tools(query: str = None):
    console = Console()
    table = Table(
        title="Available Tools",
        box=rich.box.ROUNDED,  # Rounded corners
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("Tool", style="green", no_wrap=True)
    table.add_column("Version", style="yellow")
    table.add_column("Description", style="white")
    
    for tool in discovered_tools:
        table.add_row(tool.name, tool.version, tool.description)
    
    console.print(table)
```

**Visual Example**:
```
╭─────────────────── Available Tools ───────────────────╮
│ Tool  │ Version │ Description                         │
├───────┼─────────┼─────────────────────────────────────┤
│ dummy │ 0.1.0   │ Example dummy tool for testing      │
│ beads │ 1.0.0   │ Issue tracking system               │
╰───────┴─────────┴─────────────────────────────────────╯
```

### 2. Tool List Enhancement

**Current**: Plain text list of installed tools
```
Installed tools:
  guppi-dummy (0.1.0)
  guppi-beads (1.0.0)
```

**Proposed**: Styled panel with rounded box

```python
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def list_tools():
    console = Console()
    
    # Build tool list
    tool_text = Text()
    for tool in installed_tools:
        tool_text.append(f"• {tool.name} ", style="green bold")
        tool_text.append(f"({tool.version})\n", style="dim")
    
    panel = Panel(
        tool_text,
        title="Installed Tools",
        border_style="cyan",
        box=rich.box.ROUNDED,
        padding=(1, 2)
    )
    
    console.print(panel)
```

**Visual Example**:
```
╭─────────── Installed Tools ───────────╮
│                                       │
│  • guppi-dummy (0.1.0)                │
│  • guppi-beads (1.0.0)                │
│                                       │
╰───────────────────────────────────────╯
```

### 3. Main Help Screen Enhancement

**Current**: Typer's default help output

**Proposed**: Styled panel with welcome message and styled sections

```python
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def show_help():
    console = Console()
    
    # Welcome panel
    welcome = Panel(
        "[bold cyan]GUPPI[/] - General Use Personal Program Interface\n"
        "A plugin framework for composing deterministic tools",
        border_style="cyan",
        box=rich.box.ROUNDED,
        padding=(1, 2)
    )
    
    console.print(welcome)
    
    # Then show regular typer help
    # (typer help is still useful for command listing)
```

## Implementation Plan

### Phase 1: Dependency Setup
1. Add rich to dependencies via `uv add rich`
2. Update pyproject.toml
3. Test installation

### Phase 2: Tool Search
1. Create helper module `src/guppi/ui.py` for rich formatting
2. Implement `format_tool_search_table(tools)` function
3. Update `search` command in `commands/tool.py`
4. Add tests

### Phase 3: Tool List
1. Implement `format_tool_list_panel(tools)` function
2. Update `list` command in `commands/tool.py`
3. Add tests

### Phase 4: Main Help
1. Implement custom help formatter
2. Update `cli.py` main callback
3. Keep typer's command listing, add styled header

## Testing Strategy

- **Visual testing**: Manual testing in terminal to verify appearance
- **Unit tests**: Test data formatting logic (without actual rendering)
- **CI testing**: Ensure rich doesn't break in non-TTY environments

## Alternative Considered

**Click + Rich**: Stay with typer (which uses Click) and add rich manually - this is the chosen approach.

**Textual**: Too heavy for CLI output formatting, better suited for TUI apps.

## Success Criteria

- [ ] Rich added as dependency
- [ ] `guppi tool search` shows formatted table with rounded corners
- [ ] `guppi tool list` shows styled panel with rounded box
- [ ] Main help screen has styled welcome panel
- [ ] Tests pass in both TTY and non-TTY environments
- [ ] No breaking changes to existing commands

## References

- [Rich Documentation](https://rich.readthedocs.io/)
- [Rich Tables](https://rich.readthedocs.io/en/stable/tables.html)
- [Rich Panels](https://rich.readthedocs.io/en/stable/panel.html)
- [Typer + Rich Integration](https://typer.tiangolo.com/tutorial/printing/)
