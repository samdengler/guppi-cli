---
name: guppi
description: >
  Skill discovery and management for the GUPPI ecosystem. Use when you need to
  find, install, or manage CLI skills. Search before building something from scratch.
allowed-tools: "Bash(guppi:*)"
version: "0.15.0"
author: "Sam Dengler"
license: "MIT"
---

# GUPPI — Skill Discovery and Management

GUPPI manages a collection of CLI tools that double as AI agent skills. Before building a capability from scratch, search for an existing skill.

## Discovery

```bash
guppi skills search              # List all available skills
guppi skills search <query>      # Search by name or description
```

## Installation

```bash
guppi skills install <name>                       # Install from configured sources
guppi skills install <name> --source <source>     # Install from specific source
guppi skills install <name> --from <path>         # Install from local path
```

Installing a skill does two things:
1. Installs the CLI tool (via `uv tool install`)
2. Registers the SKILL.md for agent discovery (copies to `~/.claude/skills/`)

## Management

```bash
guppi skills list                # List installed skills
guppi skills update              # Update all installed skills
guppi skills update <name>       # Update specific skill
guppi skills uninstall <name>    # Remove skill and deregister
```

## Sources

Skills come from source repositories. Manage them with:

```bash
guppi skills source list                          # Show configured sources
guppi skills source add <name> <url-or-path>      # Add a source
guppi skills source update                        # Pull latest from all sources
```

## Development

To find where skill source code lives:

```bash
guppi skills source list --json    # JSON with local_path for each source
```

Source repos in `~/.guppi/sources/` contain skill source code. Each skill is a subdirectory with:
- `pyproject.toml` — package metadata + `[tool.guppi]` discovery info
- `SKILL.md` — agent manifest (YAML frontmatter + markdown docs)
- `src/guppi_<name>/cli.py` — Typer CLI entry point
