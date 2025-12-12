"""Tool discovery and metadata management"""

from pathlib import Path
from typing import Optional
import tomllib


# Schema version for tool sources
CURRENT_SCHEMA_VERSION = "1.0.0"


class ToolMetadata:
    """Metadata for a GUPPI tool"""
    
    def __init__(self, name: str, description: str, path: Path, source: Optional[str] = None):
        self.name = name
        self.description = description
        self.path = path
        self.source = source
    
    def __repr__(self):
        return f"ToolMetadata(name={self.name}, source={self.source})"


def get_guppi_home() -> Path:
    """Get the GUPPI home directory (~/.guppi)"""
    home = Path.home() / ".guppi"
    home.mkdir(exist_ok=True)
    return home


def get_sources_dir() -> Path:
    """Get the sources directory (~/.guppi/sources)"""
    sources = get_guppi_home() / "sources"
    sources.mkdir(exist_ok=True)
    return sources


def discover_tools_in_path(path: Path, source_name: Optional[str] = None) -> list[ToolMetadata]:
    """
    Discover tools in a given path by scanning for pyproject.toml files
    with [tool.guppi] metadata.
    
    Args:
        path: Directory to scan for tools
        source_name: Name of the source (for tracking)
    
    Returns:
        List of discovered tool metadata
    """
    tools = []
    
    if not path.exists():
        return tools
    
    # Look for subdirectories with pyproject.toml
    for item in path.iterdir():
        if not item.is_dir():
            continue
        
        pyproject = item / "pyproject.toml"
        if not pyproject.exists():
            continue
        
        # Try to parse the pyproject.toml
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            
            # Look for [tool.guppi] section
            guppi_meta = data.get("tool", {}).get("guppi", {})
            if not guppi_meta:
                continue

            # Skip source metadata pyproject.toml (has [tool.guppi.source], not [tool.guppi])
            # This allows:
            # - Tool metadata with [tool.guppi] and name -> discovered
            # - Source metadata with [tool.guppi.source] only -> skipped
            # - Single-tool sources with both sections -> discovered
            if "source" in guppi_meta and "name" not in guppi_meta:
                continue

            # Extract metadata
            name = guppi_meta.get("name", item.name)
            description = guppi_meta.get("description", "No description")
            
            tools.append(ToolMetadata(
                name=name,
                description=description,
                path=item,
                source=source_name
            ))
        except Exception:
            # Skip files we can't parse
            continue
    
    return tools


def discover_all_tools() -> list[ToolMetadata]:
    """
    Discover all tools from all sources in ~/.guppi/sources/
    
    Returns:
        List of all discovered tools
    """
    sources_dir = get_sources_dir()
    all_tools = []
    
    # Scan each source directory
    for source_path in sources_dir.iterdir():
        if not source_path.is_dir():
            continue
        
        source_name = source_path.name
        tools = discover_tools_in_path(source_path, source_name)
        all_tools.extend(tools)
    
    return all_tools


def find_tool(name: str, source: Optional[str] = None) -> Optional[ToolMetadata]:
    """
    Find a specific tool by name, optionally filtered by source.
    
    Args:
        name: Name of the tool to find
        source: Optional source name to filter by
    
    Returns:
        Tool metadata if found (and unique or source specified), None otherwise
    """
    all_tools = discover_all_tools()
    
    matches = [tool for tool in all_tools if tool.name == name]
    
    if not matches:
        return None
    
    # If source specified, filter by source
    if source:
        matches = [tool for tool in matches if tool.source == source]
        if not matches:
            return None
        return matches[0]
    
    # If multiple matches without source specification, return None
    # (caller should handle ambiguity)
    if len(matches) > 1:
        return None
    
    return matches[0]


def find_all_tools(name: str) -> list[ToolMetadata]:
    """
    Find all tools matching the given name across all sources.

    Args:
        name: Name of the tool to find

    Returns:
        List of all matching tool metadata
    """
    all_tools = discover_all_tools()
    return [tool for tool in all_tools if tool.name == name]


def is_valid_source(path: Path) -> tuple[bool, Optional[dict]]:
    """Check if directory has valid [tool.guppi.source] metadata.

    Args:
        path: Directory path to check

    Returns:
        Tuple of (is_valid, source_metadata or None)
        - is_valid: True if directory has valid source metadata
        - source_metadata: Dict with source metadata if valid, None otherwise

    Example:
        >>> is_valid, meta = is_valid_source(Path("/path/to/source"))
        >>> if is_valid:
        ...     print(f"Source: {meta['name']}")
    """
    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return (False, None)

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        source_meta = data.get("tool", {}).get("guppi", {}).get("source", {})
        if source_meta:
            # Validate schema version if present
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

    Note:
        Currently only version "1.0.0" exists.
        Future versions should parse semver and check compatibility.
    """
    # For now, only 1.0.0 exists
    # Future: parse semver and check compatibility
    return version == "1.0.0"
