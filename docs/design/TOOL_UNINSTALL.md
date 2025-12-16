# GUPPI Tool Uninstall Command Design

## Overview

Design for `guppi tool uninstall` command that removes installed GUPPI tools from the system. This command mirrors `guppi tool install` and provides a clean way to remove tools installed via `uv tool install`.

**Note**: The existing `guppi uninstall` command removes the GUPPI CLI itself, whereas `guppi tool uninstall` removes individual GUPPI tools (like `guppi-dummy`, `guppi-greeter`, etc.).

## Command Signature

```bash
guppi tool uninstall <name> [OPTIONS]
```

### Arguments

1. **name** (required): Name of the tool to uninstall
   - Can be provided with or without `guppi-` prefix
   - Examples: `dummy`, `guppi-dummy`, `greeter`, `guppi-greeter`
   - Tool must be currently installed via `uv tool`

### Options

- `--yes, -y`: Skip confirmation prompt (useful for automation)
- `--keep-data`: Keep tool data/configuration in `~/.guppi/` (if tool stores data there)

## Behavior

### 1. Tool Name Normalization

```python
# Allow both "dummy" and "guppi-dummy" formats
if not name.startswith("guppi-"):
    full_name = f"guppi-{name}"
else:
    full_name = name
```

### 2. Validation

Check if the tool is actually installed:

```python
# Get list of installed uv tools
result = subprocess.run(
    ["uv", "tool", "list"],
    capture_output=True,
    text=True,
    check=True
)

# Parse output to find guppi tools
installed_tools = []
for line in result.stdout.splitlines():
    line = line.strip()
    if line.startswith("guppi-"):
        tool_name = line.split()[0]
        installed_tools.append(tool_name)

# Validate tool is installed
if full_name not in installed_tools:
    error(f"Tool '{full_name}' is not installed")
    echo("Run 'guppi tool list' to see installed tools")
    exit(1)
```

### 3. Confirmation (unless --yes)

```python
if not yes:
    echo(f"This will uninstall: {full_name}")
    confirm = typer.confirm("Are you sure?")
    if not confirm:
        echo("Aborted.")
        exit(0)
```

### 4. Uninstallation

```python
echo(f"Uninstalling {full_name}...")

try:
    result = subprocess.run(
        ["uv", "tool", "uninstall", full_name],
        check=True,
        capture_output=True,
        text=True
    )
    
    # Display output from uv
    output = result.stdout.strip() + result.stderr.strip()
    if output:
        echo(output)
    
    echo(f"✓ {full_name} uninstalled successfully!")
    
except subprocess.CalledProcessError as e:
    error(f"Error uninstalling {full_name}: {e.stderr}")
    exit(1)
```

### 5. Data Cleanup (optional, future enhancement)

If `--keep-data` is NOT specified, optionally clean up tool data:

```python
# Check if tool had data directory
tool_data_dir = get_guppi_home() / "tools" / name
if tool_data_dir.exists() and not keep_data:
    confirm = typer.confirm(
        f"Remove tool data at {tool_data_dir}?",
        default=False
    )
    if confirm:
        shutil.rmtree(tool_data_dir)
        echo(f"✓ Removed tool data")
```

**Note**: This is a future enhancement. Most tools don't store data in `~/.guppi/tools/`, but if they did, we could offer to clean it up.

## Examples

```bash
# Uninstall a tool (with confirmation)
guppi tool uninstall dummy

# Uninstall without confirmation
guppi tool uninstall dummy --yes

# Uninstall with full name
guppi tool uninstall guppi-dummy

# Uninstall but keep any tool data
guppi tool uninstall dummy --keep-data
```

## Error Handling

### Tool Not Found

```
Error: Tool 'guppi-dummy' is not installed
Run 'guppi tool list' to see installed tools
```

### UV Not Available

```
Error: 'uv' command not found. Please install uv first.
```

### Uninstall Failed

```
Error uninstalling guppi-dummy: <stderr from uv>
```

## Integration with Existing Commands

### Related Commands

1. **`guppi tool install`**: Installs tools (opposite of uninstall)
2. **`guppi tool list`**: Shows installed tools (useful before/after uninstall)
3. **`guppi tool update`**: Updates tools (complementary to install/uninstall lifecycle)
4. **`guppi uninstall`**: Removes GUPPI CLI itself (different scope)

### Workflow Integration

```bash
# Typical tool lifecycle
guppi tool install dummy      # Install
guppi dummy                   # Use tool
guppi tool update dummy       # Update to latest
guppi tool uninstall dummy    # Remove when no longer needed
```

## Implementation

Add to `src/guppi/commands/tool.py`:

```python
@app.command("uninstall")
def tool_uninstall(
    name: str = typer.Argument(..., help="Name of the tool to uninstall"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    keep_data: bool = typer.Option(False, "--keep-data", help="Keep tool data/configuration"),
):
    """
    Uninstall a GUPPI tool.
    
    Removes a tool that was installed via 'guppi tool install'.
    Uses 'uv tool uninstall' to remove the tool from the system.
    
    Examples:
        guppi tool uninstall dummy                  # Uninstall with confirmation
        guppi tool uninstall dummy --yes            # Skip confirmation
        guppi tool uninstall guppi-dummy            # Works with full name
        guppi tool uninstall dummy --keep-data      # Keep tool configuration
    """
    # Normalize tool name
    if not name.startswith("guppi-"):
        full_name = f"guppi-{name}"
    else:
        full_name = name
    
    # Get list of installed tools
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            check=True
        )
    except FileNotFoundError:
        typer.echo("Error: 'uv' command not found. Please install uv first.", err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error listing installed tools: {e.stderr}", err=True)
        raise typer.Exit(1)
    
    # Parse installed tools
    installed_tools = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("guppi-"):
            tool_name = line.split()[0] if line.split() else line
            installed_tools.append(tool_name)
    
    # Validate tool is installed
    if full_name not in installed_tools:
        typer.echo(f"Error: Tool '{full_name}' is not installed", err=True)
        typer.echo("Run 'guppi tool list' to see installed tools")
        raise typer.Exit(1)
    
    # Confirmation prompt (unless --yes)
    if not yes:
        typer.echo(f"This will uninstall: {full_name}")
        confirm = typer.confirm("Are you sure?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit(0)
    
    # Uninstall the tool
    typer.echo(f"Uninstalling {full_name}...")
    
    try:
        result = subprocess.run(
            ["uv", "tool", "uninstall", full_name],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Display output from uv if any
        output = result.stdout.strip() + result.stderr.strip()
        if output:
            typer.echo(output)
        
        typer.echo(f"\n✓ {full_name} uninstalled successfully!")
        
        # Future enhancement: Clean up tool data
        # This would require tools to follow a convention for storing data
        # For now, we just uninstall the executable
        
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error uninstalling {full_name}: {e.stderr}", err=True)
        raise typer.Exit(1)
```

## Testing Strategy

### Manual Testing

1. **Basic uninstall**:
   ```bash
   guppi tool install dummy
   guppi tool list              # Verify installed
   guppi tool uninstall dummy
   guppi tool list              # Verify removed
   ```

2. **Confirmation prompt**:
   ```bash
   guppi tool install dummy
   guppi tool uninstall dummy   # Should prompt
   # Answer 'n' to abort
   guppi tool list              # Should still be installed
   guppi tool uninstall dummy --yes  # Should skip prompt
   ```

3. **Name variations**:
   ```bash
   guppi tool install dummy
   guppi tool uninstall guppi-dummy  # With prefix
   ```

4. **Error cases**:
   ```bash
   guppi tool uninstall nonexistent  # Should error
   ```

### Automated Testing

```python
def test_tool_uninstall():
    """Test basic tool uninstall"""
    # Setup: Install a tool
    runner.invoke(app, ["tool", "install", "dummy", "--from", test_source])
    
    # Uninstall with --yes flag
    result = runner.invoke(app, ["tool", "uninstall", "dummy", "--yes"])
    assert result.exit_code == 0
    assert "uninstalled successfully" in result.stdout
    
    # Verify removed
    result = runner.invoke(app, ["tool", "list"])
    assert "dummy" not in result.stdout

def test_tool_uninstall_not_installed():
    """Test uninstalling a tool that isn't installed"""
    result = runner.invoke(app, ["tool", "uninstall", "nonexistent", "--yes"])
    assert result.exit_code == 1
    assert "not installed" in result.stdout

def test_tool_uninstall_name_variants():
    """Test uninstall with different name formats"""
    # Setup
    runner.invoke(app, ["tool", "install", "dummy", "--from", test_source])
    
    # Uninstall with full name
    result = runner.invoke(app, ["tool", "uninstall", "guppi-dummy", "--yes"])
    assert result.exit_code == 0
```

## Future Enhancements

1. **Batch Uninstall**: Support uninstalling multiple tools at once
   ```bash
   guppi tool uninstall dummy greeter calculator --yes
   ```

2. **Data Cleanup**: Implement `--keep-data` flag with actual data directory cleanup
   - Define convention: `~/.guppi/tools/<tool-name>/`
   - Detect and offer to clean up
   - Show data size before cleanup

3. **Uninstall All**: Add option to uninstall all GUPPI tools
   ```bash
   guppi tool uninstall --all --yes
   ```

4. **Dependencies**: If tools depend on each other, warn before uninstalling
   ```bash
   Warning: Tool 'guppi-utils' is used by 'guppi-builder'
   Continue with uninstall? [y/N]
   ```

5. **Dry Run**: Show what would be uninstalled without actually doing it
   ```bash
   guppi tool uninstall dummy --dry-run
   ```

## Open Questions

1. **Should we track tool installation source?**
   - Could help with reinstallation: "Use `guppi tool install dummy --source guppi-tools` to reinstall"
   - Would require persistent state (file in `~/.guppi/installed.json`?)

2. **Should uninstall handle editable installs differently?**
   - Tools installed with `--editable` flag are symlinked
   - Currently, `uv tool uninstall` handles this, but should we warn?

3. **What about tools installed from local paths?**
   - Should we track the source path for potential reinstall?
   - "To reinstall: `guppi tool install dummy --from ~/dev/guppi-tools/dummy`"

## References

- `guppi tool install` - [tool.py#L687-740](../src/guppi/commands/tool.py)
- `guppi tool list` - [tool.py#L654-685](../src/guppi/commands/tool.py)
- `guppi uninstall` (CLI) - [uninstall.py](../src/guppi/commands/uninstall.py)
- uv tool documentation - https://docs.astral.sh/uv/guides/tools/
