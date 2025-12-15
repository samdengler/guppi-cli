# GUPPI Tool Init Command Design

## Overview

Design for `guppi tool init` command that mirrors the existing `guppi tool source init` pattern. This command initializes a new GUPPI tool within a specified source directory.

## Command Signature

```bash
guppi tool init <source-directory> [tool-name] [OPTIONS]
```

### Arguments

1. **source-directory** (required): The GUPPI source directory where the tool will be created
   - Can be absolute path, relative path, or `~` expanded path
   - Must be a valid GUPPI source (contains `pyproject.toml` with `[tool.guppi.source]`)

2. **tool-name** (optional): Name for the tool
   - Defaults to prompting user or using current directory name
   - Will be sanitized (lowercase, hyphens instead of spaces/special chars)
   - Used for:
     - Directory name within source
     - Package name (`guppi-{tool-name}`)
     - Entry point name (`guppi-{tool-name}`)

### Options

- `--description TEXT`: Description of the tool (defaults to "A GUPPI tool")
- `--git/--no-git`: Initialize as git repository (defaults to True)
- `--template [minimal|example]`: Template to use (defaults to "minimal")
  - `minimal`: Basic structure with minimal code
  - `example`: Includes example commands and best practices

## Behavior

### 1. Validation

```python
# Validate source directory
source_path = Path(source_directory).expanduser().resolve()
if not source_path.exists():
    error("Source directory does not exist: {source_path}")
    
is_valid, source_meta = is_valid_source(source_path)
if not is_valid:
    error("Not a valid GUPPI source: {source_path}")
    echo("Initialize with: guppi tool source init {source_path}")
```

### 2. Tool Directory Setup

```python
# Create tool directory
tool_dir = source_path / tool_name
if tool_dir.exists():
    error("Tool directory already exists: {tool_dir}")
    
tool_dir.mkdir(parents=True, exist_ok=True)
```

### 3. File Generation

Creates the following structure:

```
<source-directory>/
└── <tool-name>/
    ├── pyproject.toml       # [tool.guppi] metadata + package config
    ├── README.md            # Tool documentation
    ├── src/
    │   └── guppi_<tool_name>/
    │       ├── __init__.py  # Package init with version
    │       └── cli.py       # Typer CLI entry point
    └── .gitignore           # Python gitignore (if --git)
```

### 4. Template Content

#### pyproject.toml
```toml
[project]
name = "guppi-{tool-name}"
version = "0.1.0"
description = "{description}"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
]

[project.scripts]
guppi-{tool-name} = "guppi_{tool_name}.cli:app"

[tool.guppi]
name = "{tool-name}"
description = "{description}"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/guppi_{tool_name}"]
```

#### src/guppi_{tool_name}/__init__.py
```python
"""GUPPI {tool-name} tool"""

__version__ = "0.1.0"
```

#### src/guppi_{tool_name}/cli.py (minimal template)
```python
"""GUPPI {tool-name} tool CLI"""

import typer

app = typer.Typer(help="{description}")

@app.command()
def hello(name: str = typer.Argument("World", help="Name to greet")):
    """Say hello"""
    typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
```

#### src/guppi_{tool_name}/cli.py (example template)
```python
"""GUPPI {tool-name} tool CLI"""

import typer
from typing_extensions import Annotated

app = typer.Typer(help="{description}")

@app.command()
def hello(
    name: Annotated[str, typer.Argument(help="Name to greet")] = "World",
    excited: Annotated[bool, typer.Option("--excited", "-e", help="Add excitement")] = False,
):
    """Say hello with optional excitement"""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " 🎉"
    typer.echo(greeting)

@app.command()
def info():
    """Show tool information"""
    from guppi_{tool_name} import __version__
    typer.echo(f"GUPPI {tool-name} v{__version__}")
    typer.echo("{description}")

if __name__ == "__main__":
    app()
```

#### README.md
```markdown
# GUPPI {tool-name}

{description}

## Installation

```bash
guppi tool install {tool-name} --from <source-path>/{tool-name}
```

## Usage

```bash
guppi {tool-name} --help
```

## Development

This tool is part of a GUPPI source. To work on it locally:

```bash
cd <source-path>/{tool-name}
uv sync --dev
uv run guppi-{tool-name} --help
```
```

### 5. Git Initialization (if --git)

```python
if git and not (tool_dir / ".git").exists():
    subprocess.run(["git", "init"], cwd=tool_dir)
    subprocess.run(["git", "add", "."], cwd=tool_dir)
    subprocess.run(["git", "commit", "-m", "Initialize GUPPI tool: {tool-name}"], cwd=tool_dir)
```

### 6. Success Message

```
✓ Initialized GUPPI tool '{tool-name}' at {tool_dir}

Next steps:
  1. Edit src/guppi_{tool_name}/cli.py to implement your tool
  2. Install locally to test: guppi tool install {tool-name} --from {tool_dir}
  3. Run your tool: guppi {tool-name} --help

See README.md for development instructions.
```

## Examples

```bash
# Initialize minimal tool in current source
guppi tool init . my-tool

# Initialize in specific source directory
guppi tool init ~/guppi-tools my-awesome-tool

# Initialize with example template
guppi tool init ~/guppi-tools demo --template example --description "Demo tool"

# Initialize without git
guppi tool init ~/guppi-tools quick-tool --no-git
```

## Implementation Notes

### Code Location
- Add `init` command to existing `tool.py` command file
- Follows the pattern of other tool subcommands (install, uninstall, etc.)

### Template Files
Create new template directory structure:
```
src/guppi/templates/
├── tool/
│   ├── pyproject.toml
│   ├── README.md
│   ├── gitignore
│   └── src/
│       └── guppi_TOOLNAME/
│           ├── __init__.py
│           └── cli.py
└── tool-example/       # For --template example
    └── src/
        └── guppi_TOOLNAME/
            └── cli.py
```

### Template Variable Substitution
Use existing `load_and_render_template` utility:
- `{tool_name}`: Sanitized tool name (lowercase, hyphens)
- `{tool_name_underscore}`: Python package name (underscores)
- `{description}`: Tool description
- `{version}`: Initial version (0.1.0)

### Name Sanitization
```python
def sanitize_tool_name(name: str) -> str:
    """Convert tool name to lowercase with hyphens"""
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)  # Collapse multiple dashes
    name = name.strip('-')
    return name

def tool_name_to_package(name: str) -> str:
    """Convert tool name to Python package name"""
    return name.replace('-', '_')
```

## Error Handling

1. **Source directory doesn't exist**:
   ```
   Error: Source directory does not exist: /path/to/source
   ```

2. **Not a valid GUPPI source**:
   ```
   Error: Not a valid GUPPI source: /path/to/dir
   Hint: Initialize with: guppi tool source init /path/to/dir
   ```

3. **Tool already exists**:
   ```
   Error: Tool directory already exists: /path/to/source/tool-name
   Remove it first or choose a different name.
   ```

4. **Git command fails**:
   ```
   Warning: Git initialization failed: git: command not found
   ```

## Testing Checklist

- [ ] Initialize tool in valid source directory
- [ ] Initialize tool with custom description
- [ ] Initialize with example template
- [ ] Initialize without git (--no-git)
- [ ] Error: source directory doesn't exist
- [ ] Error: not a valid GUPPI source
- [ ] Error: tool already exists in source
- [ ] Verify generated pyproject.toml has correct metadata
- [ ] Verify tool can be installed with `guppi tool install`
- [ ] Verify tool runs after installation

## Future Enhancements

1. **Interactive prompts** if tool name not provided
2. **Additional templates**: web, api, data, etc.
3. **Dependency presets**: Add common dependencies based on template
4. **License selection**: Add LICENSE file based on option
5. **CI/CD templates**: Add GitHub Actions, etc.
