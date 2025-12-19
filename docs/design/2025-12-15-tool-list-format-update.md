# Tool List Format Update Design

## Overview

Update `guppi tool list` to use the same table-based output format as `guppi tool search` for consistency and better readability.

## Current State

### `guppi tool search` Output
Uses a **table format** with `rich.table.Table`:
```
                  Available Tools                   
╭─────────┬─────────────┬──────────────────────────╮
│ Tool    │ Source      │ Description              │
├─────────┼─────────────┼──────────────────────────┤
│ greeter │ guppi-tools │ A friendly greeting tool │
╰─────────┴─────────────┴──────────────────────────╯

Total: 1 tool(s) found
```

### `guppi tool list` Output
Uses a **panel format** with `rich.panel.Panel`:
```
╭───────────────────────────────── Installed Tools ─────────────────────────────────╮
│                                                                                   │
│  • dummy                                                                          │
│    /Users/samdengler/src/guppi/guppi-cli/.venv/bin/guppi-dummy                    │
│  • greeter                                                                        │
│    /Users/samdengler/.local/bin/guppi-greeter                                     │
│                                                                                   │
│                                                                                   │
╰───────────────────────────────────────────────────────────────────────────────────╯

Total: 2 tool(s) installed
```

## Problem

The two commands have different visual formats:
- **`search`**: Clean table with columns, easy to scan
- **`list`**: Panel with bullet points, includes full paths (can be very long)

This inconsistency makes the CLI feel less polished and can confuse users.

## Proposed Solution

Update `guppi tool list` to use the same table format as `guppi tool search`.

### New Output Format

```
                    Installed Tools                    
╭──────────┬──────────────────────────────────────────╮
│ Tool     │ Location                                 │
├──────────┼──────────────────────────────────────────┤
│ dummy    │ .venv/bin/guppi-dummy                    │
│ greeter  │ ~/.local/bin/guppi-greeter               │
╰──────────┴──────────────────────────────────────────╯

Total: 2 tool(s) installed
```

### Key Changes

1. **Format**: Change from Panel to Table (same as `search`)
2. **Columns**: 
   - **Tool**: Tool name (without `guppi-` prefix)
   - **Location**: Shortened path to executable
3. **Path Display**: Shorten paths for readability:
   - Replace home directory with `~`
   - Show relative paths when in project directory
   - Full paths only when necessary
4. **Styling**: Match `search` command styling:
   - `box=box.ROUNDED`
   - `title="Installed Tools"`
   - `header_style="bold cyan"`
   - Green for tool names
   - Dim/white for paths

## Implementation

### 1. Update UI Function

Modify `format_tool_list_panel()` in [src/guppi/ui.py](../src/guppi/ui.py#L44-L78):

```python
def format_tool_list_table(installed_tools: List[Dict[str, str]]) -> None:
    """
    Display installed tools in a formatted table with rounded corners.
    
    Args:
        installed_tools: List of dicts with 'name' and 'path' keys
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
    table.add_column("Location", style="dim")
    
    for tool in sorted(installed_tools, key=lambda x: x["name"]):
        # Shorten path for display
        path = shorten_path(tool["path"])
        table.add_row(tool["name"], path)
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(installed_tools)} tool(s) installed[/dim]")


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
    from pathlib import Path
    import os
    
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
```

### 2. Update Command

Update the import in [src/guppi/commands/tool.py](../src/guppi/commands/tool.py#L641-L676):

```python
@app.command("list")
def list_tools():
    """
    List installed GUPPI tools.
    
    Shows all tools that are currently installed and available for routing.
    """
    from guppi.ui import format_tool_list_table  # Changed from format_tool_list_panel
    
    # ... existing code ...
    
    # Display with rich formatting
    format_tool_list_table(installed)  # Changed function name
```

### 3. Rename Function

To maintain consistency across the codebase:
- Rename `format_tool_list_panel()` → `format_tool_list_table()`
- Update all references

## Benefits

1. **Consistency**: Both `search` and `list` use the same visual format
2. **Readability**: Table format is easier to scan for tool names
3. **Compactness**: Shortened paths reduce clutter
4. **Professional**: Unified styling across the CLI

## Backwards Compatibility

This is a **cosmetic change only** - no functional changes to:
- Command arguments
- Return values
- Exit codes
- Tool detection logic

Users will simply see a different (improved) output format.

## Testing

Manual testing:
```bash
# Test with no tools
uv tool uninstall --all guppi-*
guppi tool list

# Test with one tool
guppi tool install greeter
guppi tool list

# Test with multiple tools
guppi tool install dummy
guppi tool list

# Compare with search
guppi tool search
```

Expected: Both commands should have similar visual appearance and table formatting.

## Future Enhancements

Potential future improvements (out of scope for this design):
1. Add "Version" column showing tool version
2. Add "Source" column showing where the tool was installed from
3. Add `--format json` option for programmatic use
4. Add color coding for local vs global installs

## Implementation Checklist

- [ ] Create `shorten_path()` helper function in `ui.py`
- [ ] Rename `format_tool_list_panel()` to `format_tool_list_table()`
- [ ] Update function to use Table instead of Panel
- [ ] Update import in `tool.py`
- [ ] Test with various scenarios (0, 1, multiple tools)
- [ ] Update any documentation that shows the old output format
