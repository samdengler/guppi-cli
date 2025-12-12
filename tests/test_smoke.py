"""Smoke tests to verify test infrastructure is working"""
import pytest


def test_smoke():
    """Basic smoke test to verify pytest is working"""
    assert True


def test_fixtures(temp_dir, mock_guppi_home):
    """Test that basic fixtures are available and working"""
    assert temp_dir.exists()
    assert mock_guppi_home.exists()
    assert (mock_guppi_home / "tools").exists()
    assert (mock_guppi_home / "tools" / "sources").exists()


def test_sample_tool_fixture(mock_tool_directory):
    """Test that mock tool directory fixture works"""
    assert mock_tool_directory.exists()
    assert (mock_tool_directory / "pyproject.toml").exists()
    content = (mock_tool_directory / "pyproject.toml").read_text()
    assert "[tool.guppi]" in content


def test_sample_source_fixture(mock_source_directory):
    """Test that mock source directory fixture works"""
    assert mock_source_directory.exists()
    assert (mock_source_directory / "pyproject.toml").exists()
    content = (mock_source_directory / "pyproject.toml").read_text()
    assert "[tool.guppi.source]" in content
