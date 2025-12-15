# GUPPI

**General Use Personal Program Interface**

A plugin framework for composing deterministic tools through a unified CLI.

## Disclaimer

This project is built for my personal use and assistance. You are welcome to fork it for your own purposes, but please note that it is **unsupported** and provided as-is. Use at your own risk.

## Ultra-Lean MVP

This is the minimal viable version that proves the plugin architecture works.

### Installation

**For Users:**
```bash
# Install as a global CLI tool
uv tool install guppi-cli --from git+https://github.com/samdengler/guppi-cli
```

**For Development:**
```bash
# Install in editable mode for local development
uv pip install -e .

# Or with pip
pip install -e .
```

### Usage

```bash
# Route commands to tools
guppi <tool> <command> [args...]

# Example with dummy tool
guppi dummy hello world

# Update the guppi CLI itself
guppi update

# Manage tool sources
guppi tool source add guppi-tools https://github.com/samdengler/guppi-tools
guppi tool source list
guppi tool source init <directory>       # Initialize a new tool source
guppi tool source update                 # Update all sources
guppi tool source update guppi-tools     # Update specific source

# Create new tools
guppi tool init <source-dir> <tool-name>                    # Create a new tool
guppi tool init <source-dir> <tool-name> --template example # Create with example template

# Discover and install tools from sources
guppi tool search                        # List all available tools
guppi tool install <name>                # Install a tool
guppi tool list                          # List installed tools
guppi tool update                        # Update all installed tools
guppi tool update <name>                 # Update specific tool
guppi tool uninstall <name>              # Uninstall a tool
```

### How It Works

GUPPI routes commands to tools by:
1. Taking the first argument as the tool name
2. Looking for an executable named `guppi-<tool>`
3. Passing remaining arguments to that tool

### Tools

Tools are separate executables that follow the naming convention `guppi-<toolname>`.

See the [guppi-tools](https://github.com/samdengler/guppi-tools) repository for available tools.

### Creating Your Own Tools

GUPPI makes it easy to create new tools with the `guppi tool init` command.

#### Quick Start

```bash
# 1. Initialize a tool source (if you don't have one)
guppi tool source init ~/my-guppi-tools --name my-tools

# 2. Create a new tool
guppi tool init ~/my-guppi-tools my-awesome-tool

# 3. Implement your tool
cd ~/my-guppi-tools/my-awesome-tool
# Edit src/guppi_my_awesome_tool/cli.py

# 4. Install and test
guppi tool install my-awesome-tool --from ~/my-guppi-tools/my-awesome-tool
guppi my-awesome-tool --help
```

#### Tool Templates

**Minimal template** (default): Basic structure with a simple hello command
```bash
guppi tool init ~/my-tools simple-tool
```

**Example template**: Extended template with multiple commands and best practices
```bash
guppi tool init ~/my-tools feature-tool --template example
```

#### Tool Structure

The `guppi tool init` command creates a complete Python package:

```
my-tool/
├── pyproject.toml       # Package metadata with [tool.guppi] configuration
├── README.md            # Tool documentation
├── .gitignore           # Python .gitignore
└── src/
    └── guppi_my_tool/
        ├── __init__.py  # Package init with version
        └── cli.py       # Typer CLI entry point
```

#### Tool Naming

- Tool names are automatically sanitized (lowercase, hyphens)
- Example: "My Cool Tool" becomes "my-cool-tool"
- Package names use underscores: `guppi_my_cool_tool`
- Entry points use hyphens: `guppi-my-cool-tool`

## What's Next

This is an ultra-lean MVP. Future iterations will add:
- Tool installation management
- Tool registry and discovery
- Configuration system
- Better error handling
- Tool versioning

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/samdengler/guppi-cli.git
cd guppi-cli

# Install in editable mode
uv pip install -e .
```

### Testing

```bash
# Test the CLI
guppi dummy test
```

## Inspiration

This project is inspired by [GUPPI from the Bobiverse series](https://bobiverse.fandom.com/wiki/GUPPI).
