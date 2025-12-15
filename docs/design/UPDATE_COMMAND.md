# Update Command Design

**Status**: Draft  
**Created**: 2025-12-15  
**Updated**: 2025-12-15  
**Author**: AI Assistant

## Overview

Design for GUPPI's update commands with clear separation of concerns:
- `guppi update` - Update the guppi CLI itself
- `guppi tool source update [name]` - Update tool sources (git pull)
- Future: `guppi tool update [name]` - Update installed tools

## Current State

Currently, GUPPI has update functionality:
- `guppi upgrade` - Upgrades the guppi CLI itself (uses `uv tool upgrade`)
- No source update command yet

### Issues with Current Approach

1. **Inconsistent naming**: `upgrade` instead of `update`
2. **Missing functionality**: No way to update tool sources
3. **Future expansion unclear**: Where would tool updates go?

## Proposed Solution

Create a clear, hierarchical command structure:

### Command Structure

```bash
# Update the CLI itself
guppi update                    # Update guppi CLI to latest version
guppi update --check            # Check for CLI updates without applying
guppi update --dry-run          # Show what would be updated
guppi update --json             # Machine-readable output

# Update tool sources (git pull)
guppi tool source update        # Update all tool sources
guppi tool source update <name> # Update specific source
guppi tool source update --check      # Check which sources have updates
guppi tool source update --dry-run    # Show what would be updated
guppi tool source update --json       # Machine-readable output

# Future: Update installed tools
guppi tool update               # Update all installed guppi-* tools
guppi tool update <name>        # Update specific tool
```

### Design Rationale

**Clear separation of concerns:**
- `guppi update` - Self-contained, updates the CLI binary/package
- `guppi tool source update` - Manages git repositories in `~/.guppi/sources/`
- `guppi tool update` (future) - Updates installed tool packages

**Advantages:**
1. **Intuitive hierarchy**: Each command owns its domain
2. **Consistent naming**: Everything uses "update"
3. **Extensible**: Natural place for future tool update functionality
4. **Predictable**: Users know where to look for what they need

## Implementation Plan

### 1. CLI Update Command

Create `src/guppi/commands/update.py`:

```python
"""Update the guppi CLI itself"""

import subprocess
import typer
from typing import Optional

app = typer.Typer(help="Update the guppi CLI")

@app.callback(invoke_without_command=True)
def update(
    ctx: typer.Context,
    check: bool = typer.Option(False, "--check", help="Check for updates only"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be updated"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
):
    """
    Update the guppi CLI to the latest version.
    
    Uses 'uv tool upgrade guppi' to update the installed CLI.
    """
    # Implementation here
    pass
```

### 2. Source Update Subcommand

Add to `src/guppi/commands/tool.py`:

```python
@source_app.command("update")
def source_update(
    name: Optional[str] = typer.Argument(None, help="Source name to update (updates all if not specified)"),
    check: bool = typer.Option(False, "--check", help="Check for updates only"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be updated"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
):
    """
    Update tool sources (git pull).
    
    Updates git repositories in ~/.guppi/sources/.
    If no name is provided, updates all sources.
    """
    # Implementation here
    pass
```

### 3. Command Hierarchy

| Command | Purpose | Implementation |
|---------|---------|----------------|
| `guppi update` | Update CLI itself | `commands/update.py` |
| `guppi tool source update` | Update all sources | `commands/tool.py` (source subcommand) |
| `guppi tool source update <name>` | Update specific source | `commands/tool.py` (source subcommand) |
| `guppi tool update` (future) | Update all installed tools | Future implementation |
| `guppi tool update <name>` (future) | Update specific tool | Future implementation |

### 4. Core Functions

```python
# In commands/update.py
def update_cli(dry_run: bool = False, check: bool = False) -> UpdateResult:
    """Update guppi CLI using uv tool upgrade"""
    if check:
        # Check if updates available
        # Compare installed version with PyPI version
        pass
    
    if dry_run:
        return UpdateResult(
            component="guppi",
            status="would-update",
            message="Would update guppi CLI"
        )
    
    result = subprocess.run(
        ["uv", "tool", "upgrade", "guppi"],
        capture_output=True,
        text=True,
    )
    
    # Parse result and return UpdateResult
    pass

# In commands/tool.py (source subcommand)
def update_source(name: str, dry_run: bool = False, check: bool = False) -> UpdateResult:
    """Update specific git-based source"""
    source_path = Path.home() / ".guppi" / "sources" / name
    
    if not source_path.exists():
        return UpdateResult(
            component=name,
            status="error",
            message=f"Source '{name}' not found"
        )
    
    if check:
        # Run git fetch and check if updates available
        pass
    
    if dry_run:
        # Show what would be pulled
        pass
    
    # Run git pull
    result = subprocess.run(
        ["git", "-C", str(source_path), "pull"],
        capture_output=True,
        text=True,
    )
    
    # Parse result and return UpdateResult
    pass

def update_all_sources(dry_run: bool = False, check: bool = False) -> List[UpdateResult]:
    """Update all git-based tool sources"""
    sources_dir = Path.home() / ".guppi" / "sources"
    results = []
    
    for source_path in sources_dir.iterdir():
        if source_path.is_dir() and (source_path / ".git").exists():
            result = update_source(source_path.name, dry_run, check)
            results.append(result)
    
    return results

class UpdateResult:
    """Result of an update operation"""
    component: str
    status: Literal["updated", "up-to-date", "error", "would-update"]
    message: str
    old_version: Optional[str] = None
    new_version: Optional[str] = None
```

### 5. UI/UX Design

#### CLI Update (`guppi update`)

**Default (Interactive) Mode:**
```
Checking for updates...
✓ Updated guppi CLI from 0.4.0 to 0.5.0
```

**Already up-to-date:**
```
✓ guppi CLI is already up-to-date (0.5.0)
```

**JSON Mode:**
```json
{
  "component": "guppi",
  "status": "updated",
  "old_version": "0.4.0",
  "new_version": "0.5.0"
}
```

#### Source Update (`guppi tool source update`)

**Update all sources:**
```
Updating tool sources...

┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Source       ┃ Status     ┃ Changes                 ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ guppi-tools  │ Updated    │ abc1234 → def5678       │
│ local-source │ Up-to-date │ No changes              │
└──────────────┴────────────┴─────────────────────────┘

✓ Updated 1 source
✓ 1 source already up-to-date
```

**Update specific source:**
```
Updating source 'guppi-tools'...
✓ Updated guppi-tools (abc1234 → def5678)
```

**JSON Mode:**
```json
{
  "sources": [
    {
      "name": "guppi-tools",
      "status": "updated",
      "old_commit": "abc1234",
      "new_commit": "def5678"
    },
    {
      "name": "local-source",
      "status": "up-to-date"
    }
  ],
  "summary": {
    "updated": 1,
    "up_to_date": 1,
    "errors": 0
  }
}
```

### 6. Future: Tool Update Implementation

When implementing `guppi tool update` for installed tools:

```python
def get_installed_guppi_tools() -> List[str]:
    """Get list of installed guppi-* tools using uv tool list"""
    result = subprocess.run(
        ["uv", "tool", "list"],
        capture_output=True,
        text=True,
        check=True
    )
    # Parse output to find guppi-* tools
    tools = []
    for line in result.stdout.splitlines():
        if line.startswith("guppi-"):
            tool_name = line.split()[0]
            tools.append(tool_name)
    return tools

def update_installed_tool(name: str, dry_run: bool = False) -> UpdateResult:
    """Update a specific installed tool using uv tool upgrade"""
    if dry_run:
        return UpdateResult(
            component=name,
            status="would-update",
            message=f"Would update {name}"
        )
    
    result = subprocess.run(
        ["uv", "tool", "upgrade", name],
        capture_output=True,
        text=True,
    )
    
    # Parse result to determine if updated or already up-to-date
    # Return appropriate UpdateResult
    pass
```

This would enable:
```bash
guppi tool update              # Update all installed guppi-* tools
guppi tool update guppi-dummy  # Update specific tool
```

## Migration Strategy

### Phase 1: Implement new structure
1. Rename `upgrade` command to `update` in `src/guppi/commands/update.py`
2. Add `source update` subcommand to `src/guppi/commands/tool.py`
3. Update CLI registration in `cli.py`
4. Keep `upgrade` as a deprecated alias initially

### Phase 2: Documentation update
1. Update README.md with new commands
2. Update help text
3. Add migration notice for `upgrade` → `update`

### Phase 3: Deprecation (future release)
1. Add deprecation warning to `guppi upgrade`
2. Plan removal timeline for alias

## Testing Strategy

### Unit Tests
- Test CLI update function with mocked `uv` calls
- Test source update function with mocked `git` calls
- Test dry-run mode for both commands
- Test error handling (network failures, missing sources, etc.)

### Integration Tests
- Test full update workflow with real git repos (use test fixtures)
- Test JSON output parsing
- Test update detection (check mode)

### Smoke Tests
```bash
# CLI update
guppi update
guppi update --check
guppi update --dry-run
guppi update --json

# Source updates
guppi tool source update
guppi tool source update guppi-tools
guppi tool source update --check
guppi tool source update --dry-run
guppi tool source update --json
```

## Open Questions

1. **Version Detection**: How to get current guppi version programmatically?
   - Option A: Parse `uv tool list` output
   - Option B: Use `__version__` from installed package
   - **Recommendation**: Option B (more reliable)

2. **Source Update Conflicts**: How to handle git merge conflicts?
   - **Recommendation**: Fail with clear error message, suggest manual resolution

3. **Update All**: Should there be a command to update everything at once?
   - **Future consideration**: Could add `guppi update --all` that updates CLI, then sources
   - **Current recommendation**: Keep separate for clarity

## Dependencies

- Existing: `subprocess`, `typer`, `rich` (already in use)
- New: None

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing `upgrade` users | Keep as deprecated alias initially |
| Network failures during git pull | Clear error messages, retry suggestions |
| Git conflicts in sources | Fail gracefully with manual resolution instructions |
| Version detection failures | Graceful degradation, show "unknown" |

## Success Criteria

1. Users can update CLI with simple `guppi update` command
2. Users can update sources with `guppi tool source update [name]`
3. Clear, informative output showing what was updated
4. JSON mode works for scripting
5. Dry-run mode accurately predicts changes
6. Zero regressions for existing functionality
7. Test coverage > 80%
8. Consistent naming (all commands use "update")

## Future Enhancements

1. **Tool updates**: `guppi tool update [name]` for updating installed tools
2. **Batch updates**: `guppi update --all` to update CLI + sources in one command
3. **Update scheduling**: Automatic update checks on startup
4. **Rollback support**: `guppi update --rollback` to revert updates
5. **Parallel updates**: Update multiple sources concurrently
6. **Update history**: Track what was updated when
7. **Source update all**: Update all sources with progress bars

## References

- [uv tool management](https://github.com/astral-sh/uv)
- [Rich progress bars](https://rich.readthedocs.io/en/stable/progress.html)
- [Homebrew update command](https://docs.brew.sh/Manpage#update-options) (inspiration)
