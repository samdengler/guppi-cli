# GUPPI

**General Use Personal Program Interface**

A plugin framework for composing deterministic tools through a unified CLI.

## Disclaimer

This project is built for my personal use and assistance. You are welcome to fork it for your own purposes, but please note that it is **unsupported** and provided as-is. Use at your own risk.

## Ultra-Lean MVP

This is the minimal viable version that proves the plugin architecture works.

### Installation

```bash
# Install GUPPI core
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
```

### How It Works

GUPPI routes commands to tools by:
1. Taking the first argument as the tool name
2. Looking for an executable named `guppi-<tool>`
3. Passing remaining arguments to that tool

### Tools

Tools are separate executables that follow the naming convention `guppi-<toolname>`.

See the [guppi-tools](https://github.com/samdengler/guppi-tools) repository for available tools.

## What's Next

This is an ultra-lean MVP. Future iterations will add:
- Tool installation management
- Tool registry and discovery
- Configuration system
- Better error handling
- Tool versioning

## Development

```bash
# Install in development mode
uv pip install -e .

# Test
guppi dummy test
```

## Inspiration

This project is inspired by [GUPPI from the Bobiverse series](https://bobiverse.fandom.com/wiki/GUPPI).
