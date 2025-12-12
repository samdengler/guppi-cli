"""Pytest configuration and shared fixtures for GUPPI CLI tests"""
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def tmp_path_factory_session(tmp_path_factory):
    """Provide access to tmp_path_factory for creating temporary directories"""
    return tmp_path_factory


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test isolation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_guppi_home(temp_dir: Path, monkeypatch) -> Path:
    """Mock ~/.guppi directory for testing"""
    guppi_home = temp_dir / ".guppi"
    guppi_home.mkdir(parents=True)

    # Create standard subdirectories
    (guppi_home / "tools").mkdir()
    (guppi_home / "tools" / "sources").mkdir()

    # Mock the home directory
    monkeypatch.setenv("HOME", str(temp_dir))

    return guppi_home


@pytest.fixture
def sample_pyproject_toml() -> str:
    """Sample pyproject.toml content with [tool.guppi] metadata"""
    return """[project]
name = "guppi-example"
version = "0.1.0"
description = "Example GUPPI tool"

[tool.guppi]
name = "example"
description = "Example tool for testing"
"""


@pytest.fixture
def sample_source_pyproject_toml() -> str:
    """Sample pyproject.toml content with [tool.guppi.source] metadata"""
    return """[tool.guppi.source]
name = "test-source"
description = "Test tool source"
version = "1.0.0"
"""


@pytest.fixture
def mock_tool_directory(temp_dir: Path, sample_pyproject_toml: str) -> Path:
    """Create a mock tool directory with pyproject.toml"""
    tool_dir = temp_dir / "guppi-example"
    tool_dir.mkdir()

    pyproject = tool_dir / "pyproject.toml"
    pyproject.write_text(sample_pyproject_toml)

    return tool_dir


@pytest.fixture
def mock_source_directory(temp_dir: Path, sample_source_pyproject_toml: str) -> Path:
    """Create a mock source directory with pyproject.toml"""
    source_dir = temp_dir / "test-source"
    source_dir.mkdir()

    pyproject = source_dir / "pyproject.toml"
    pyproject.write_text(sample_source_pyproject_toml)

    return source_dir
