"""Tests for `agile-backlog init` — full setup, --config-only, idempotency."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from agile_backlog.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["pytest", "ruff"]\n')
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestInit:
    def test_full_init(self, runner: CliRunner, project: Path):
        result = runner.invoke(main, ["init", "--yes"])
        assert result.exit_code == 0
        assert (project / ".claude" / "sprint-config.yaml").exists()
        assert (project / ".claude" / "skills" / "sprint-start").is_dir()
        assert (project / ".claude" / "hooks" / "post-tool-logger.sh").exists()
        settings = json.loads((project / ".claude" / "settings.local.json").read_text())
        assert settings["hooks"]["PostToolUse"][0]["matcher"].startswith("Read|")
        assert (project / "docs" / "sprints").is_dir()
        assert ".claude/context-logs/" in (project / ".gitignore").read_text()
        assert "## Commands" in result.output  # printed CLAUDE.md block

    def test_config_only_skips_skills_and_hooks(self, runner: CliRunner, project: Path):
        result = runner.invoke(main, ["init", "--config-only", "--yes"])
        assert result.exit_code == 0
        assert (project / ".claude" / "sprint-config.yaml").exists()
        assert not (project / ".claude" / "skills").exists()
        assert not (project / ".claude" / "hooks").exists()
        assert not (project / ".claude" / "settings.local.json").exists()

    def test_init_is_idempotent(self, runner: CliRunner, project: Path):
        runner.invoke(main, ["init", "--yes"])
        marker = project / ".claude" / "sprint-config.yaml"
        marker.write_text(marker.read_text().replace("current_sprint: 1", "current_sprint: 7"))
        result = runner.invoke(main, ["init", "--yes"])
        assert result.exit_code == 0
        assert "current_sprint: 7" in marker.read_text()  # not clobbered without --force
        settings = json.loads((project / ".claude" / "settings.local.json").read_text())
        assert len(settings["hooks"]["PostToolUse"]) == 1  # no duplicate hook entry

    def test_detected_commands_land_in_config(self, runner: CliRunner, project: Path):
        runner.invoke(main, ["init", "--yes"])
        text = (project / ".claude" / "sprint-config.yaml").read_text()
        assert 'test_command: "pytest tests/ -v"' in text
        assert "language: python" in text


class TestInstallSkillsStillWorks:
    def test_install_skills_unchanged(self, runner: CliRunner, project: Path):
        result = runner.invoke(main, ["install-skills"])
        assert result.exit_code == 0
        assert "Installed" in result.output
        assert (project / ".claude" / "skills" / "cli-reference").is_dir()
