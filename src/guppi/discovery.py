"""Tool discovery and metadata management"""

from pathlib import Path
from typing import Optional
import tomllib


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
