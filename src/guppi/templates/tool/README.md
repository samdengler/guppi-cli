# GUPPI {tool_name}

{description}

## Installation

```bash
guppi tool install {tool_name} --from <source-path>/{tool_name}
```

## Usage

```bash
guppi {tool_name} --help
```

## Development

This tool is part of a GUPPI source. To work on it locally:

```bash
cd <source-path>/{tool_name}
uv sync --dev
uv run guppi-{tool_name} --help
```
