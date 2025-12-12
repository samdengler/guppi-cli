# GUPPI CLI - MVP Design

**General Use Personal Program Interface**

*Inspired by the Bobiverse GUPPI - a plugin-based framework for composing deterministic tools*

## Vision

GUPPI is a Python-based CLI framework that provides a unified interface for installing, managing, and running pluggable tools. Rather than being a monolithic application, GUPPI is a extensible platform where capabilities are added through independent tool packages.

## Core Principles

1. **Plugin Architecture**: Tools are independent Python packages, not hardcoded features
2. **Deterministic Tools**: Each tool has well-defined inputs/outputs
3. **Easy Installation**: Simple `guppi tool install <name>` using uv under the hood
4. **Composable**: Tools can be used independently or orchestrated together (future)
5. **Extensible**: New tools can be added without modifying core GUPPI

## MVP Scope

**What's IN the MVP:**
- ✅ Core GUPPI CLI framework (Python + Typer)
- ✅ Tool registry and discovery system
- ✅ Tool installation/management commands
- ✅ Command routing to installed tools
- ✅ Example tool structure (scaffold only)

**What's OUT of the MVP:**
- ❌ No actual tool implementations yet
- ❌ No conversational/AI layer (future feature)
- ❌ No cross-tool orchestration (future feature)

## Architecture Overview

### Repository Structure

Two separate repositories:

**1. guppi-cli** (Core Framework - THIS REPO)
```
guppi-cli/
├── src/guppi/
│   ├── __init__.py
│   ├── cli.py           # Main Typer CLI app
│   ├── registry.py      # Tool discovery/management
│   ├── router.py        # Route commands to tools
│   └── config.py        # User config management
├── tests/
├── pyproject.toml       # GUPPI core package
└── README.md
```

**2. guppi-tools** (Tool Collection - SEPARATE REPO)
```
guppi-tools/
├── pyproject.toml       # Registry of available tools
├── beads/               # Example: beads integration
│   ├── pyproject.toml
│   └── src/guppi_beads/
│       ├── __init__.py
│       └── cli.py
├── notes/               # Example: notes tool
│   ├── pyproject.toml
│   └── src/guppi_notes/
└── README.md
```

### User Experience

**Install GUPPI:**
```bash
uv tool install guppi --from github.com/user/guppi-cli
```

**Install a tool:**
```bash
# User runs this:
guppi tool install beads

# GUPPI internally executes:
# uv tool install beads --from github.com/user/guppi-tools --subdirectory beads
```

**Use a tool:**
```bash
guppi beads create "Fix the bug"
guppi beads list --status open
guppi notes add "Important insight"
```

**Manage tools:**
```bash
guppi tool list              # Show installed tools
guppi tool search            # Browse available tools
guppi tool uninstall beads   # Remove a tool
```

## Technical Stack

- **Language**: Python 3.11+
- **CLI Framework**: Typer (modern Python CLI)
- **Package Manager**: uv (for tool installation)
- **Config Format**: TOML (pyproject.toml for registry and config)
- **Testing**: pytest

## Tool Interface Contract

Each tool is a Python package with:

1. **Entry Point**: Exposes CLI via Typer app
2. **Metadata**: `pyproject.toml` with tool description, version, dependencies
3. **Namespace**: Package name `guppi_<toolname>` to avoid conflicts
4. **Registration**: Listed in `guppi-tools/pyproject.toml` registry

**Example Tool Structure:**
```python
# guppi-tools/beads/src/guppi_beads/cli.py
import typer

app = typer.Typer()

@app.command()
def create(title: str):
    """Create a new beads issue"""
    # Implementation
    typer.echo(f"Created: {title}")

@app.command()
def list():
    """List beads issues"""
    # Implementation
    pass
```

**Tool Registry (guppi-tools/pyproject.toml):**
```toml
[project]
name = "guppi-tools"

[tool.guppi.registry]
tools = [
    { name = "beads", subdirectory = "beads", description = "Issue tracking with beads" },
    { name = "notes", subdirectory = "notes", description = "Personal knowledge base" },
]
```

## MVP Implementation Plan

### Phase 1: Core Framework (2-3 days)

**Goal**: Basic GUPPI CLI that can list and discover tools

**Tasks:**
1. Set up Python project with uv and pyproject.toml
2. Create basic Typer CLI structure (`guppi --help`)
3. Implement config system (~/.guppi/config.toml)
4. Build tool registry reader (parse guppi-tools/pyproject.toml)
5. Add `guppi tool list` and `guppi tool search` commands

**Deliverable**: `guppi tool search` shows available tools from registry

### Phase 2: Tool Installation (2-3 days)

**Goal**: Install and uninstall tools via uv

**Tasks:**
1. Implement `guppi tool install <name>` (wraps uv commands)
2. Track installed tools in user config
3. Implement `guppi tool uninstall <name>`
4. Add validation and error handling
5. Create helpful CLI output and feedback

**Deliverable**: Can install/uninstall tools successfully

### Phase 3: Command Routing (2-3 days)

**Goal**: Route commands to installed tools

**Tasks:**
1. Build command router that detects tool prefixes
2. Implement subprocess execution for tool commands
3. Handle tool discovery and validation
4. Add error handling for missing tools
5. Pass through all arguments to tool commands

**Deliverable**: `guppi beads list` routes to installed beads tool

### Phase 4: Example Tool Scaffolds (1-2 days)

**Goal**: Create guppi-tools repo with example structures

**Tasks:**
1. Create guppi-tools repository
2. Add top-level pyproject.toml with registry
3. Create example tool directory structures
4. Add documentation for tool developers
5. Test end-to-end installation flow

**Deliverable**: Working example that others can use as template

## Success Criteria

MVP is complete when:
1. ✅ GUPPI can discover tools from registry
2. ✅ Users can install/uninstall tools via `guppi tool install`
3. ✅ Commands route correctly to installed tools
4. ✅ Clear error messages for missing tools
5. ✅ Example tool structure exists for developers

## Out of Scope (Future Features)

- ❌ Conversational AI interface
- ❌ Cross-tool orchestration
- ❌ Actual tool implementations (beads, notes, etc.)
- ❌ Tool discovery from multiple registries
- ❌ Tool versioning and updates
- ❌ MCP server integration

## Next Steps

1. Review and validate this design
2. Update bd epic with revised scope
3. Create new task breakdown in bd
4. Begin Phase 1 implementation

---

**Design Date**: December 9, 2025  
**Status**: Ready for Review  
**Architecture**: Python + Typer + uv plugin system
