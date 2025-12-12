"""Tests for tool discovery and metadata management"""
import pytest
from pathlib import Path
import tomllib

from guppi.discovery import (
    ToolMetadata,
    discover_tools_in_path,
    is_valid_source,
    is_compatible_schema,
    CURRENT_SCHEMA_VERSION,
)


class TestToolMetadata:
    """Tests for ToolMetadata class"""

    def test_create_tool_metadata(self):
        """Test creating ToolMetadata instance"""
        path = Path("/test/path")
        meta = ToolMetadata(
            name="test-tool",
            description="Test tool",
            path=path,
            source="test-source"
        )

        assert meta.name == "test-tool"
        assert meta.description == "Test tool"
        assert meta.path == path
        assert meta.source == "test-source"

    def test_tool_metadata_repr(self):
        """Test ToolMetadata string representation"""
        meta = ToolMetadata(
            name="test-tool",
            description="Test tool",
            path=Path("/test"),
            source="test-source"
        )

        repr_str = repr(meta)
        assert "test-tool" in repr_str
        assert "test-source" in repr_str


class TestDiscoverToolsInPath:
    """Tests for discover_tools_in_path function"""

    def test_discover_tools_with_valid_tool(self, temp_dir, sample_pyproject_toml):
        """Test discovering a valid tool"""
        # Create a tool directory
        tool_dir = temp_dir / "my-tool"
        tool_dir.mkdir()
        (tool_dir / "pyproject.toml").write_text(sample_pyproject_toml)

        # Discover tools
        tools = discover_tools_in_path(temp_dir, source_name="test-source")

        assert len(tools) == 1
        assert tools[0].name == "example"
        assert tools[0].description == "Example tool for testing"
        assert tools[0].path == tool_dir
        assert tools[0].source == "test-source"

    def test_discover_tools_skips_source_metadata(self, temp_dir, sample_source_pyproject_toml):
        """Test that source metadata is skipped during tool discovery"""
        # Create a source directory with source metadata
        source_dir = temp_dir / "source-dir"
        source_dir.mkdir()
        (source_dir / "pyproject.toml").write_text(sample_source_pyproject_toml)

        # Discover tools - should skip the source metadata
        tools = discover_tools_in_path(temp_dir)

        assert len(tools) == 0, "Source metadata should be skipped"

    def test_discover_tools_with_mixed_directories(self, temp_dir, sample_pyproject_toml, sample_source_pyproject_toml):
        """Test discovering tools with mix of tools and source metadata"""
        # Create tool directory
        tool_dir = temp_dir / "my-tool"
        tool_dir.mkdir()
        (tool_dir / "pyproject.toml").write_text(sample_pyproject_toml)

        # Create source metadata (should be skipped)
        source_dir = temp_dir / "source-metadata"
        source_dir.mkdir()
        (source_dir / "pyproject.toml").write_text(sample_source_pyproject_toml)

        # Create directory without pyproject.toml (should be skipped)
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        # Discover tools
        tools = discover_tools_in_path(temp_dir)

        assert len(tools) == 1
        assert tools[0].name == "example"

    def test_discover_tools_empty_directory(self, temp_dir):
        """Test discovering tools in empty directory"""
        tools = discover_tools_in_path(temp_dir)
        assert len(tools) == 0

    def test_discover_tools_nonexistent_path(self):
        """Test discovering tools in nonexistent path"""
        tools = discover_tools_in_path(Path("/nonexistent/path"))
        assert len(tools) == 0

    def test_discover_tools_invalid_toml(self, temp_dir):
        """Test discovering tools with invalid TOML file"""
        tool_dir = temp_dir / "bad-tool"
        tool_dir.mkdir()
        (tool_dir / "pyproject.toml").write_text("invalid [[ toml")

        # Should skip invalid files
        tools = discover_tools_in_path(temp_dir)
        assert len(tools) == 0

    def test_discover_tools_no_guppi_metadata(self, temp_dir):
        """Test discovering tools without [tool.guppi] metadata"""
        tool_dir = temp_dir / "non-guppi-tool"
        tool_dir.mkdir()
        (tool_dir / "pyproject.toml").write_text("""
[project]
name = "regular-tool"
version = "1.0.0"
""")

        # Should skip tools without [tool.guppi]
        tools = discover_tools_in_path(temp_dir)
        assert len(tools) == 0

    def test_discover_tools_uses_directory_name_if_no_name(self, temp_dir):
        """Test that directory name is used if tool.guppi.name is missing"""
        tool_dir = temp_dir / "my-directory"
        tool_dir.mkdir()
        (tool_dir / "pyproject.toml").write_text("""
[tool.guppi]
description = "Tool without explicit name"
""")

        tools = discover_tools_in_path(temp_dir)
        assert len(tools) == 1
        assert tools[0].name == "my-directory"

    def test_discover_tools_uses_default_description(self, temp_dir):
        """Test that default description is used if not provided"""
        tool_dir = temp_dir / "tool-no-desc"
        tool_dir.mkdir()
        (tool_dir / "pyproject.toml").write_text("""
[tool.guppi]
name = "test-tool"
""")

        tools = discover_tools_in_path(temp_dir)
        assert len(tools) == 1
        assert tools[0].description == "No description"


class TestIsValidSource:
    """Tests for is_valid_source function"""

    def test_valid_source(self, temp_dir, sample_source_pyproject_toml):
        """Test validating a valid source"""
        (temp_dir / "pyproject.toml").write_text(sample_source_pyproject_toml)

        is_valid, metadata = is_valid_source(temp_dir)

        assert is_valid is True
        assert metadata is not None
        assert metadata["name"] == "test-source"
        assert metadata["description"] == "Test tool source"
        assert metadata["version"] == "1.0.0"

    def test_invalid_source_no_pyproject(self, temp_dir):
        """Test validating directory without pyproject.toml"""
        is_valid, metadata = is_valid_source(temp_dir)

        assert is_valid is False
        assert metadata is None

    def test_invalid_source_no_guppi_metadata(self, temp_dir):
        """Test validating source without [tool.guppi.source] metadata"""
        (temp_dir / "pyproject.toml").write_text("""
[project]
name = "regular-project"
""")

        is_valid, metadata = is_valid_source(temp_dir)

        assert is_valid is False
        assert metadata is None

    def test_valid_source_no_version(self, temp_dir):
        """Test validating source without explicit version (should use default)"""
        (temp_dir / "pyproject.toml").write_text("""
[tool.guppi.source]
name = "test-source"
description = "Test source"
""")

        is_valid, metadata = is_valid_source(temp_dir)

        assert is_valid is True
        assert metadata is not None

    def test_invalid_toml_returns_false(self, temp_dir):
        """Test that invalid TOML returns False"""
        (temp_dir / "pyproject.toml").write_text("invalid [[ toml")

        is_valid, metadata = is_valid_source(temp_dir)

        assert is_valid is False
        assert metadata is None


class TestIsCompatibleSchema:
    """Tests for is_compatible_schema function"""

    def test_compatible_schema_1_0_0(self):
        """Test that version 1.0.0 is compatible"""
        assert is_compatible_schema("1.0.0") is True

    def test_incompatible_schema_2_0_0(self):
        """Test that version 2.0.0 is incompatible (for now)"""
        assert is_compatible_schema("2.0.0") is False

    def test_incompatible_schema_0_9_0(self):
        """Test that version 0.9.0 is incompatible"""
        assert is_compatible_schema("0.9.0") is False

    def test_current_schema_version_exists(self):
        """Test that CURRENT_SCHEMA_VERSION constant is defined"""
        assert CURRENT_SCHEMA_VERSION == "1.0.0"
