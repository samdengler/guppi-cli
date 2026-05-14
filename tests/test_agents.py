"""Tests for guppi.agents module"""

from pathlib import Path
from unittest.mock import patch

from guppi.agents import get_active_targets, AGENT_TARGETS


class TestGetActiveTargets:
    def test_both_agents_present(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".kiro").mkdir()
        targets = {
            "Claude": tmp_path / ".claude" / "skills",
            "Kiro": tmp_path / ".kiro" / "skills",
        }
        with patch.dict("guppi.agents.AGENT_TARGETS", targets):
            result = get_active_targets()
        assert set(result.keys()) == {"Claude", "Kiro"}

    def test_only_claude_present(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        targets = {
            "Claude": tmp_path / ".claude" / "skills",
            "Kiro": tmp_path / ".kiro" / "skills",
        }
        with patch.dict("guppi.agents.AGENT_TARGETS", targets):
            result = get_active_targets()
        assert list(result.keys()) == ["Claude"]

    def test_only_kiro_present(self, tmp_path):
        (tmp_path / ".kiro").mkdir()
        targets = {
            "Claude": tmp_path / ".claude" / "skills",
            "Kiro": tmp_path / ".kiro" / "skills",
        }
        with patch.dict("guppi.agents.AGENT_TARGETS", targets):
            result = get_active_targets()
        assert list(result.keys()) == ["Kiro"]

    def test_no_agents_present(self, tmp_path):
        targets = {
            "Claude": tmp_path / ".claude" / "skills",
            "Kiro": tmp_path / ".kiro" / "skills",
        }
        with patch.dict("guppi.agents.AGENT_TARGETS", targets):
            result = get_active_targets()
        assert result == {}

    def test_returns_correct_paths(self, tmp_path):
        (tmp_path / ".kiro").mkdir()
        targets = {
            "Claude": tmp_path / ".claude" / "skills",
            "Kiro": tmp_path / ".kiro" / "skills",
        }
        with patch.dict("guppi.agents.AGENT_TARGETS", targets):
            result = get_active_targets()
        assert result["Kiro"] == tmp_path / ".kiro" / "skills"
