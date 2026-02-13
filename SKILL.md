---
name: guppi
description: >
  Skill discovery and management for the GUPPI ecosystem. Use when you need to
  find, install, or manage CLI skills. Search before building something from scratch.
allowed-tools: "Bash(guppi:*)"
version: "0.12.0"
author: "Sam Dengler"
license: "MIT"
---

# GUPPI — Skill Discovery and Management

GUPPI manages a collection of CLI tools that double as AI agent skills. Before building a capability from scratch, search for an existing skill.

## Discovery

```bash
guppi skill search              # List all available skills
guppi skill search <query>      # Search by name or description
```

## Installation

```bash
guppi skill install <name>                       # Install from configured sources
guppi skill install <name> --source <source>     # Install from specific source
guppi skill install <name> --from <path>         # Install from local path
```

Installing a skill does two things:
1. Installs the CLI tool (via `uv tool install`)
2. Registers the SKILL.md for agent discovery (copies to `~/.claude/skills/`)

## Management

```bash
guppi skill list                # List installed skills
guppi skill update              # Update all installed skills
guppi skill update <name>       # Update specific skill
guppi skill uninstall <name>    # Remove skill and deregister
```

## Sources

Skills come from source repositories. Manage them with:

```bash
guppi skill source list                          # Show configured sources
guppi skill source add <name> <url-or-path>      # Add a source
guppi skill source update                        # Pull latest from all sources
```
