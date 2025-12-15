"""Template loading and rendering utilities for GUPPI CLI"""
import re
from importlib.resources import files
from pathlib import Path


def load_template(template_path: str) -> str:
    """Load a template file from the templates directory.

    Args:
        template_path: Path relative to guppi.templates (e.g., "source/pyproject.toml")

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    template_files = files("guppi.templates")
    template_resource = template_files / template_path

    if not template_resource.is_file():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_resource.read_text()


def render_template(template_content: str, **kwargs) -> str:
    """Simple template rendering using str.format.

    Args:
        template_content: Template string with {variable} placeholders
        **kwargs: Variables to substitute in template

    Returns:
        Rendered template string

    Example:
        >>> template = "Hello, {name}!"
        >>> render_template(template, name="World")
        'Hello, World!'
    """
    return template_content.format(**kwargs)


def load_and_render_template(template_path: str, **kwargs) -> str:
    """Load and render a template in one step.

    Args:
        template_path: Path relative to guppi.templates
        **kwargs: Variables to substitute in template

    Returns:
        Rendered template string
    """
    template_content = load_template(template_path)
    return render_template(template_content, **kwargs)


def sanitize_tool_name(name: str) -> str:
    """Convert tool name to lowercase with hyphens.
    
    Sanitizes a tool name to be valid for GUPPI tool names:
    - Converts to lowercase
    - Replaces non-alphanumeric characters with hyphens
    - Collapses multiple hyphens into single hyphens
    - Strips leading/trailing hyphens
    
    Args:
        name: Raw tool name
        
    Returns:
        Sanitized tool name (lowercase with hyphens)
        
    Examples:
        >>> sanitize_tool_name("My Tool")
        'my-tool'
        >>> sanitize_tool_name("api_service")
        'api-service'
        >>> sanitize_tool_name("Tool-Name_123")
        'tool-name-123'
        >>> sanitize_tool_name("--Multiple---Hyphens--")
        'multiple-hyphens'
    """
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = re.sub(r'-+', '-', name)  # Collapse multiple hyphens
    name = name.strip('-')
    return name


def tool_name_to_package(name: str) -> str:
    """Convert tool name to Python package name.
    
    Converts a hyphenated tool name to a valid Python package name
    by replacing hyphens with underscores.
    
    Args:
        name: Tool name (should be sanitized first)
        
    Returns:
        Python package name (underscores instead of hyphens)
        
    Examples:
        >>> tool_name_to_package("my-tool")
        'my_tool'
        >>> tool_name_to_package("api-service")
        'api_service'
    """
    return name.replace('-', '_')

