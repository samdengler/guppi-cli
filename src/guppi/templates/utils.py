"""Template loading and rendering utilities for GUPPI CLI"""
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
