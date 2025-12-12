# Tool Source Init Command - Design

## Overview

The `guppi tool source init` command initializes a directory to serve as a guppi-tool source. This enables developers to create their own tool repositories that follow the GUPPI convention.

## Command Signature

```bash
guppi tool source init [DIRECTORY] [OPTIONS]
```

**Arguments:**
- `DIRECTORY` (optional): Path to initialize (defaults to current directory)

**Options:**
- `--name TEXT`: Name for the source (defaults to directory basename)
- `--description TEXT`: Description of the source
- `--git/--no-git`: Initialize as git repository (default: --git)
- `--template TEXT`: Template to use: "minimal" or "example" (default: "minimal")

## Behavior

### 1. Directory Creation/Validation
- If DIRECTORY not provided, use current directory
- If DIRECTORY provided, resolve it:
  - Expand `~` to user home directory
  - Convert to absolute path
  - Create if it doesn't exist
- If DIRECTORY exists but not empty, warn and ask for confirmation
- If already a guppi source (has `pyproject.toml` with `[tool.guppi.source]`), exit with error

**Path Resolution:**
```python
import os
from pathlib import Path

directory = directory or "."
directory = os.path.expanduser(directory)  # Handle ~
directory = os.path.abspath(directory)     # Make absolute
target_path = Path(directory)
```

### 2. Minimal Template

Creates the basic structure:

```
<source-name>/
├── pyproject.toml         # Source metadata
├── README.md              # Basic documentation
└── .gitignore             # Ignores Python artifacts
```

**`pyproject.toml` format:**
```toml
[tool.guppi.source]
name = "my-tools"
description = "My personal GUPPI tools"
version = "1.0.0"
```

**`README.md` template:**
```markdown
# {name}

{description}

## GUPPI Tool Source

This is a GUPPI tool source. Tools are organized as subdirectories,
each containing a `pyproject.toml` with `[tool.guppi]` metadata.

## Adding Tools

Create a new tool directory:

```bash
mkdir my-tool
cd my-tool
# Create pyproject.toml with [tool.guppi] section
```

See https://github.com/samdengler/guppi-cli for more information.
```

**`.gitignore`:**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
```

### 3. Example Template

Includes minimal template PLUS an example tool:

```
<source-name>/
├── pyproject.toml
├── README.md
├── .gitignore
└── example-tool/
    ├── pyproject.toml
    ├── README.md
    └── src/
        └── guppi_example/
            ├── __init__.py
            └── cli.py
```

**example-tool/pyproject.toml:**
```toml
[project]
name = "guppi-example"
version = "0.1.0"
description = "Example GUPPI tool"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
]

[project.scripts]
guppi-example = "guppi_example.cli:app"

[tool.guppi]
name = "example"
description = "Example tool demonstrating GUPPI integration"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/guppi_example"]
```

**example-tool/src/guppi_example/cli.py:**
```python
"""Example GUPPI tool"""
import typer

app = typer.Typer(help="Example GUPPI tool")

@app.command()
def hello(name: str = typer.Argument("world")):
    """Say hello"""
    typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
```

### 4. Git Initialization

If `--git` (default):
- Run `git init`
- Create initial commit with message: "Initialize GUPPI tool source"
- Add all created files

If `--no-git`:
- Skip git operations

### 5. Post-Initialization

Display success message with next steps:

```
✓ Initialized GUPPI tool source '{name}' at {path}

Next steps:
  1. Add tools to this source (each tool in its own directory)
  2. Each tool needs a pyproject.toml with [tool.guppi] metadata
  3. Add this source to GUPPI: guppi tool source add {name} {path}

Example tool structure:
  {path}/my-tool/
    ├── pyproject.toml    # Must include [tool.guppi] section
    ├── README.md
    └── src/
        └── guppi_my_tool/
            └── cli.py

See the README.md for more details.
```

## Source Management Integration

### Directory Structure
```
~/.guppi/
└── tools/
    ├── installed.toml        # Tracking installed tools with source info
    ├── sources.toml          # Source registry (remote & local)
    └── sources/              # Git clones of remote tool sources
        ├── community-tools/
        └── other-tools/
```

### Adding Sources

**Note:** Full design for `guppi tool source add` and related commands (list, update, remove) 
is documented in a separate design doc (to be created).

**Remote source (git clone):**
```bash
guppi tool source add community-tools https://github.com/user/guppi-tools
# Clones into ~/.guppi/tools/sources/community-tools
```

**Local source (path reference):**
```bash
guppi tool source add my-tools /Users/me/dev/guppi-tools
# Stores path in ~/.guppi/tools/sources.toml, no copy/symlink
```

**sources.toml format:**
```toml
[sources.community-tools]
type = "git"
url = "https://github.com/user/guppi-tools"
path = "/Users/me/.guppi/tools/sources/community-tools"

[sources.my-tools]
type = "local"
path = "/Users/me/dev/guppi-tools"
```

## Implementation Plan

### File Structure
```
src/guppi/
├── commands/
│   └── tool.py              # Add init command to source_app
└── templates/
    ├── source/
    │   ├── pyproject.toml   # Source metadata template
    │   ├── README.md        # Source README template
    │   └── gitignore        # Python .gitignore
    └── example-tool/
        ├── pyproject.toml   # Example tool metadata
        ├── README.md        # Example tool README
        └── src/
            └── guppi_example/
                ├── __init__.py
                └── cli.py
```

### New Function
```python
@source_app.command("init")
def source_init(
    directory: str = typer.Argument(None, help="Directory to initialize (defaults to current directory)"),
    name: str = typer.Option(None, "--name", help="Name for this source"),
    description: str = typer.Option(None, "--description", help="Description of this source"),
    git: bool = typer.Option(True, "--git/--no-git", help="Initialize as git repository"),
    template: str = typer.Option("minimal", "--template", help="Template: minimal or example"),
):
    """Initialize a directory as a GUPPI tool source"""
    # Implementation here
```

### Template Loading

Templates are stored in `src/guppi/templates/` and loaded using `importlib.resources`:

```python
from importlib.resources import files
from pathlib import Path

def load_template(template_path: str) -> str:
    """Load a template file from the templates directory"""
    template_files = files("guppi.templates")
    return (template_files / template_path).read_text()

def render_template(template_content: str, **kwargs) -> str:
    """Simple template rendering using str.format"""
    return template_content.format(**kwargs)
```

## Edge Cases

1. **Directory already exists and not empty**
   - Prompt: "Directory is not empty. Continue? [y/N]"
   - If no, exit cleanly

2. **Already a GUPPI source**
   - Check for `pyproject.toml` with `[tool.guppi.source]` section
   - Error: "This directory is already a GUPPI tool source"

3. **No git installed**
   - If `--git` and git not found, warn but continue
   - "Warning: git not found, skipping git initialization"

4. **Invalid name characters**
   - Sanitize name to be filesystem-safe
   - Allow: a-z, A-Z, 0-9, dash, underscore
   - Convert spaces to dashes

5. **Permission errors**
   - Catch and report clearly
   - "Error: Permission denied creating directory"

## Testing Considerations

- Test with current directory (no argument)
- Test with specific directory path
- Test both templates (minimal, example)
- Test git init success/failure
- Test directory already exists scenarios
- Test invalid directory names

## Integration with Discovery

### Tool Discovery Changes

Update `discover_tools_in_path()` in `discovery.py` to skip source metadata:

```python
guppi_meta = data.get("tool", {}).get("guppi", {})
if not guppi_meta:
    continue

# Skip source metadata pyproject.toml (has [tool.guppi.source], not [tool.guppi])
if "source" in guppi_meta and "name" not in guppi_meta:
    continue

# Extract tool metadata
name = guppi_meta.get("name", item.name)
description = guppi_meta.get("description", "No description")
```

This ensures that when scanning a source directory:
- Tool pyproject.toml files with `[tool.guppi]` are discovered
- Source root pyproject.toml with `[tool.guppi.source]` is skipped
- Single-tool sources with both sections are supported (has both `source` and `name`)

### Source Validation

Add validation helper in `discovery.py`:

```python
CURRENT_SCHEMA_VERSION = "1.0.0"

def is_valid_source(path: Path) -> tuple[bool, Optional[dict]]:
    """Check if directory has valid [tool.guppi.source] metadata.
    
    Returns:
        (is_valid, source_metadata or None)
    """
    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return (False, None)
    
    try:
        data = tomllib.loads(pyproject.read_text())
        source_meta = data.get("tool", {}).get("guppi", {}).get("source", {})
        if source_meta:
            # Validate schema version
            schema_version = source_meta.get("version", CURRENT_SCHEMA_VERSION)
            if not is_compatible_schema(schema_version):
                # Log warning but don't fail - be lenient
                pass
            return (True, source_meta)
    except Exception:
        pass
    
    return (False, None)

def is_compatible_schema(version: str) -> bool:
    """Check if source schema version is compatible with CLI.
    
    Args:
        version: Schema version from [tool.guppi.source]
    
    Returns:
        True if compatible, False otherwise
    """
    # For now, only 1.0.0 exists
    # Future: parse semver and check compatibility
    return version == "1.0.0"
```

**Schema Version:**
- The `version` field in `[tool.guppi.source]` indicates the schema version of the tool source
- **Optional** - if not present, CLI assumes latest version (currently "1.0.0")
- Used for future compatibility when source structure changes
- CLI should be forward-compatible with older schema versions

**Validation Policy:**
- **On source add**: Validate and error if `[tool.guppi.source]` missing
- **During scan**: Be lenient, log warning if metadata missing but still discover tools
- This allows both formal sources (with metadata) and informal tool directories

## Future Enhancements

- `--license` option to add LICENSE file
- `--github` option to create repo and push
- Interactive mode with prompts
- Validate source after creation
- Add pre-commit hooks template
- Support custom templates from URLs
