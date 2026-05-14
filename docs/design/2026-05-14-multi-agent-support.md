# Multi-Agent Support: Claude Code + Kiro

**Date**: 2026-05-14  
**Author**: Sam Dengler  
**Status**: Proposal  
**Branch**: `kiro`

## Problem

GUPPI's skill registration is hardcoded to Claude Code (`~/.claude/skills/`). Users on Kiro (or both) get no agent discovery without manual workarounds.

## Discovery Mechanisms Compared

| Aspect | Claude Code | Kiro |
|--------|-------------|------|
| Skills directory | `~/.claude/skills/<name>/SKILL.md` | `~/.kiro/skills/<name>/SKILL.md` |
| Workspace skills | — | `.kiro/skills/**/SKILL.md` |
| Skill format | YAML frontmatter (name, description) | YAML frontmatter (name, description) |
| Loading | Eager (always in context) | Progressive (metadata first, content on demand) |
| Steering/instructions | `CLAUDE.md` | `.kiro/steering/**/*.md`, `AGENTS.md` |
| Legacy paths | — | `.amazonq/` fallback |
| Permission syntax | `allowed-tools: "Bash(guppi:*)"` | `allowedTools` in agent JSON |

**Key insight**: The SKILL.md format is identical. Only the destination directory differs.

## Proposed Changes

### Phase 1: Multi-target registration (minimal change)

Replace the hardcoded `CLAUDE_SKILLS_DIR` with a registry of agent targets.

```python
# src/guppi/agents.py (new file)
from pathlib import Path

AGENT_TARGETS = {
    "claude": Path.home() / ".claude" / "skills",
    "kiro": Path.home() / ".kiro" / "skills",
}

def get_active_targets() -> dict[str, Path]:
    """Return targets where the parent config directory exists."""
    return {
        name: path
        for name, path in AGENT_TARGETS.items()
        if path.parent.exists()  # ~/.claude or ~/.kiro exists
    }
```

Then `_sync_skill_md` and `_remove_skill_md` iterate over active targets:

```python
def _sync_skill_md(name: str):
    ...
    for agent_name, skills_dir in get_active_targets().items():
        dest_dir = skills_dir / short_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_md, dest_dir / "SKILL.md")
        typer.echo(f"✓ Registered '{short_name}' for {agent_name} at {dest_dir}")
```

**Why auto-detect**: If `~/.claude` exists, register there. If `~/.kiro` exists, register there. Both can coexist. No user configuration needed.

### Phase 2: Update `guppi init`

Same pattern — register GUPPI's own SKILL.md to all detected agents:

```python
def init():
    """Register GUPPI with AI agents for skill discovery."""
    targets = get_active_targets()
    if not targets:
        typer.echo("No supported agents detected (~/.claude or ~/.kiro)")
        typer.echo("Install Claude Code or Kiro CLI first.")
        raise typer.Exit(1)

    for agent_name, skills_dir in targets.items():
        dest_dir = skills_dir / "guppi"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_md, dest_dir / "SKILL.md")
        typer.echo(f"✓ Registered GUPPI for {agent_name}")
```

### Phase 3: Update user-facing messages

Replace all "Claude Code" references in output strings with the actual agent name(s) being targeted. The SKILL.md docs and README can mention both.

### Phase 4 (optional): `--agent` flag

For explicit control:

```bash
guppi init --agent kiro          # Only register for Kiro
guppi skills install spiker --agent claude  # Only register for Claude
```

Default remains auto-detect.

## Files to Change

| File | Change |
|------|--------|
| `src/guppi/agents.py` | **New** — agent target registry |
| `src/guppi/commands/skill.py` | Replace `CLAUDE_SKILLS_DIR` with `get_active_targets()` loop |
| `src/guppi/commands/init.py` | Same |
| `SKILL.md` | Remove `allowed-tools` (Claude-specific) or keep as informational |
| `CLAUDE.md` | Keep as-is (Claude Code reads it) |
| `.kiro/steering/guppi.md` | **New** — Kiro equivalent of CLAUDE.md |
| `tests/` | Update mocks to test multi-target behavior |

## What Stays the Same

- SKILL.md frontmatter format (already compatible)
- `uv tool install/uninstall` mechanics
- Source management (git clone, discovery)
- Tool routing
- The pyproject.toml `[tool.guppi]` metadata schema

## Migration Path for Existing Users

No breaking changes. Existing `~/.claude/skills/` registrations continue working. Running `guppi init` or `guppi skills install` after this change will additionally register for Kiro if `~/.kiro` exists.

## Open Questions

1. Should `guppi init` create `~/.kiro/skills/` even if `~/.kiro` doesn't exist yet? (Proposed: no — require the agent to be installed first.)
2. Should we add a `guppi agents` command to show which agents are detected and their registration status?
3. The `allowed-tools: "Bash(guppi:*)"` frontmatter field is Claude-specific. Kiro ignores unknown frontmatter fields, so it's harmless but noisy. Remove or keep?
