# GUPPI CLI — Agent Instructions

## Project Overview

**GUPPI** (General Use Personal Program Interface) - A Python-based plugin framework for composing deterministic tools. Ultra-lean MVP with Homebrew-style tool management.

**Key Features:**
- Command routing to tools via `guppi-*` executables
- Homebrew-inspired source management (add, update, discover)
- Convention over configuration: tools self-describe via `[tool.guppi]` in pyproject.toml
- Tool installation via uv (global CLI tools)

## Tech Stack

- **Language**: Python 3.11+
- **CLI Framework**: Typer
- **Package Manager**: uv (for tool installation)
- **Storage**: Git-based (sources in `~/.guppi/sources/`)
- **Testing**: Python standard testing

## Project Structure

```
src/guppi/
├── cli.py              # Main entry point, routing logic
├── agents.py           # Agent target registry (Claude, Kiro)
├── commands/           # Subcommands (skill.py, init.py, upgrade.py)
├── router.py           # Tool routing to guppi-* executables
├── discovery.py        # Tool discovery from sources
└── __version__.py      # Version constant
```

## Dependency Management

This project uses **uv** for dependency management:

```bash
# Add production dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name

# Sync all dependencies (install/update to match lock file)
uv sync --dev

# Run commands without activating venv
uv run -- guppi <command>
uv run -- pytest

# Run tests
uv run -- pytest              # Run all tests
uv run -- pytest tests/test_specific.py  # Run specific test file
uv run -- pytest -v           # Verbose output
uv run -- pytest --cov        # With coverage report

# Install GUPPI globally for testing
uv tool install --editable .
guppi <command>               # Test globally installed version
```

**Rules:**
- ✅ Always use `uv add` to add dependencies (NOT manual pyproject.toml edits)
- ✅ Run `uv sync --dev` after pulling changes
- ✅ Test both `uv run -- guppi` (local) and globally installed `guppi` command

## Code Style

- New commands go in `commands/` directory (modular pattern)
- Use subprocess for external commands (uv, git)
- Always commit `.beads/issues.jsonl` with code changes

## Releases

For version releases, follow the procedure in [RELEASE.md](RELEASE.md):
- Semantic versioning (major/minor/patch)
- Update both `pyproject.toml` and `src/guppi/__version__.py`
- Create git tag and GitHub release with `gh` CLI

## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**
```bash
bd ready --json
```

**Create new issues:**
```bash
bd create "Issue title" -t bug|feature|task -p 0-4 --json
bd create "Issue title" -p 1 --deps discovered-from:bd-123 --json
bd create "Subtask" --parent <epic-id> --json  # Hierarchical subtask (gets ID like epic-id.1)
```

**Claim and update:**
```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**
```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`
6. **Commit together**: Always commit the `.beads/issues.jsonl` file together with the code changes so issue state stays in sync with code state

### Auto-Sync

bd automatically syncs with git:
- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### MCP Server (Recommended)

If using Claude, Kiro, or other MCP-compatible clients, install the beads MCP server:

```bash
pip install beads-mcp
```

Add to MCP config (e.g., `~/.config/claude/config.json` or `.kiro/agents/<name>.json`):
```json
{
  "beads": {
    "command": "beads-mcp",
    "args": []
  }
}
```

Then use `mcp__beads__*` functions instead of CLI commands.

### Managing AI-Generated Planning Documents

**Recommended approach:**
- Create a `history/` directory in the project root
- Store ALL AI-generated planning/design docs in `history/`
- Keep the repository root clean and focused on permanent project files

### CLI Help

Run `bd <command> --help` to see all available flags for any command.

## Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic bd use
- ✅ New commands in `commands/` directory
- ✅ Test with global install: `uv tool install --editable .`
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ✅ Store AI planning docs in `history/` directory
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT commit `.beads/beads.db` (JSONL only)
- ❌ Do NOT clutter repo root with planning documents
