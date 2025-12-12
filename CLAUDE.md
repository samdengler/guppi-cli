# Claude Code Instructions for GUPPI CLI

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

## Coding Guidelines

### Project Structure
```
src/guppi/
├── cli.py              # Main entry point, routing logic
├── commands/           # Subcommands (tool.py, upgrade.py)
├── router.py           # Tool routing to guppi-* executables
├── discovery.py        # Tool discovery from sources
└── __version__.py      # Version constant
```

### Dependency Management

This project uses **uv** for dependency management:

```bash
# Add production dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name

# Sync all dependencies (install/update to match lock file)
uv sync

# Sync with dev dependencies
uv sync --dev

# Activate virtual environment (for local development)
source .venv/bin/activate

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
- ✅ Run `uv sync --dev` after pulling changes to ensure dependencies are up to date
- ✅ Use `source .venv/bin/activate` for local development, or `uv run --` for one-off commands
- ✅ Test both `uv run -- guppi` (local) and globally installed `guppi` command

### Code Style
- New commands go in `commands/` directory (modular pattern)
- Always use `--json` flag for programmatic bd operations
- Test both `uv run -- guppi` and global `guppi` command
- Use subprocess for external commands (uv, git)

### Git Workflow
- Always commit `.beads/issues.jsonl` with code changes
- Commit and push together to keep issue state in sync

## Issue Tracking with bd

**CRITICAL**: This project uses **bd (beads)** for ALL task tracking. Do NOT create markdown TODO lists or use TodoWrite tool.

### Essential Commands

```bash
# Find work
bd ready --json                    # Unblocked issues

# Create and manage
bd create "Title" -t bug|feature|task -p 0-4 --json
bd update <id> --status in_progress --json
bd close <id> --reason "Done" --json

# Always use --json for programmatic use
```

### Workflow

1. **Check ready work**: `bd ready --json`
2. **Claim task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Complete**: `bd close <id> --reason "Done" --json`
5. **Sync**: Changes auto-export to `.beads/issues.jsonl` (commit together with code)

For detailed workflows, see [AGENTS.md](AGENTS.md).

## Releases

For version releases, follow the procedure in [RELEASE.md](RELEASE.md):
- Semantic versioning (major/minor/patch)
- Update both `pyproject.toml` and `src/guppi/__version__.py`
- Create git tag and GitHub release with `gh` CLI

## Important Rules

- ✅ Use bd for ALL task tracking (NOT TodoWrite tool)
- ✅ New commands in `commands/` directory
- ✅ Test with global install: `uv tool install --editable .`
- ✅ Update version in both files for releases
- ✅ Reference [AGENTS.md](AGENTS.md) for detailed workflows
- ✅ Reference [RELEASE.md](RELEASE.md) for release procedures
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use TodoWrite tool
- ❌ Do NOT commit `.beads/beads.db` (JSONL only)
