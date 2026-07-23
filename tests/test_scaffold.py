"""Tests for scaffold.py — init detection, config scaffolding, hooks install/merge."""

import json
from pathlib import Path

from agile_backlog import scaffold


class TestDetectProject:
    def test_python_project_with_pytest_and_ruff(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo"\ndependencies = []\n'
            '[project.optional-dependencies]\ndev = ["pytest>=8.0.0", "ruff>=0.8.0"]\n'
        )
        d = scaffold.detect_project(tmp_path)
        assert d["language"] == "python"
        assert d["test_command"] == "pytest tests/ -v"
        assert d["lint_command"] == "ruff check . && ruff format --check ."
        assert d["format_command"] == "ruff format ."
        assert d["cli_command"] == "agile-backlog"

    def test_python_project_with_venv_prefixes_commands(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["pytest", "ruff"]\n')
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        d = scaffold.detect_project(tmp_path)
        assert d["test_command"] == ".venv/bin/pytest tests/ -v"
        assert d["cli_command"] == ".venv/bin/agile-backlog"

    def test_node_project(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"name": "webapp", "scripts": {"test": "vitest", "lint": "eslint ."}})
        )
        d = scaffold.detect_project(tmp_path)
        assert d["language"] == "javascript"
        assert d["project_name"] == "webapp"
        assert d["test_command"] == "npm test"
        assert d["lint_command"] == "npm run lint"
        assert d["format_command"] is None

    def test_typescript_detected_via_tsconfig(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(json.dumps({"name": "webapp", "scripts": {}}))
        (tmp_path / "tsconfig.json").write_text("{}")
        assert scaffold.detect_project(tmp_path)["language"] == "typescript"

    def test_empty_project_falls_back_to_dirname(self, tmp_path: Path):
        d = scaffold.detect_project(tmp_path)
        assert d["project_name"] == tmp_path.name
        assert d["language"] is None
        assert d["test_command"] is None


VALUES = {
    "project_name": "demo",
    "language": "python",
    "test_command": "pytest tests/ -v",
    "lint_command": "ruff check .",
    "format_command": "ruff format .",
    "ci_command": "ruff check . && pytest tests/ -v",
    "cli_command": "agile-backlog",
}


class TestSprintConfig:
    def test_render_contains_values_and_placeholders(self):
        text = scaffold.render_sprint_config(VALUES)
        assert "project_name: demo" in text
        assert 'ci_command: "ruff check . && pytest tests/ -v"' in text
        assert "current_sprint: 1" in text
        assert 'show: "agile-backlog show {id}"' in text  # runtime placeholders survive rendering
        assert 'branch_pattern: "sprint{N}/main"' in text

    def test_scaffold_writes_once_and_respects_force(self, tmp_path: Path):
        assert scaffold.scaffold_sprint_config(tmp_path, VALUES) is True
        cfg = tmp_path / ".claude" / "sprint-config.yaml"
        assert cfg.exists()
        assert scaffold.scaffold_sprint_config(tmp_path, VALUES) is False  # idempotent
        cfg.write_text("current_sprint: 9\n")
        assert scaffold.scaffold_sprint_config(tmp_path, VALUES, force=True) is True
        assert "current_sprint: 1" in cfg.read_text()


class TestDirsAndGitignore:
    def test_ensure_doc_dirs_creates_then_noops(self, tmp_path: Path):
        created = scaffold.ensure_doc_dirs(tmp_path)
        assert "docs/sprints" in created
        assert (tmp_path / "docs" / "superpowers" / "plans").is_dir()
        assert scaffold.ensure_doc_dirs(tmp_path) == []

    def test_ensure_gitignore_appends_once(self, tmp_path: Path):
        (tmp_path / ".gitignore").write_text("*.pyc\n")
        assert scaffold.ensure_gitignore(tmp_path) is True
        assert scaffold.ensure_gitignore(tmp_path) is False
        content = (tmp_path / ".gitignore").read_text()
        assert content.count(".claude/context-logs/") == 1
        assert "*.pyc" in content

    def test_ensure_gitignore_creates_file(self, tmp_path: Path):
        assert scaffold.ensure_gitignore(tmp_path) is True
        assert (tmp_path / ".gitignore").read_text() == ".claude/context-logs/\n"


class TestHooks:
    def test_install_hooks_copies_script(self, tmp_path: Path):
        assert scaffold.install_hooks(tmp_path) is True
        dest = tmp_path / ".claude" / "hooks" / "post-tool-logger.sh"
        assert dest.exists()
        assert "PostToolUse hook" in dest.read_text()
        assert scaffold.install_hooks(tmp_path) is False  # idempotent
        assert scaffold.install_hooks(tmp_path, force=True) is True

    def test_merge_creates_settings_with_single_regex_matcher(self, tmp_path: Path):
        assert scaffold.merge_settings_hooks(tmp_path) is True
        settings = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
        entries = settings["hooks"]["PostToolUse"]
        assert len(entries) == 1
        assert entries[0]["matcher"] == "Read|Grep|Glob|Bash|WebFetch|Agent|Edit|Write|Skill"
        assert entries[0]["hooks"][0]["command"] == "bash .claude/hooks/post-tool-logger.sh"

    def test_merge_preserves_existing_settings(self, tmp_path: Path):
        path = tmp_path / ".claude" / "settings.local.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "permissions": {"allow": ["Bash(ls:*)"]},
                    "hooks": {
                        "PostToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": "bash lint.sh"}]}]
                    },
                }
            )
        )
        assert scaffold.merge_settings_hooks(tmp_path) is True
        settings = json.loads(path.read_text())
        assert settings["permissions"] == {"allow": ["Bash(ls:*)"]}
        assert len(settings["hooks"]["PostToolUse"]) == 2  # existing entry kept, ours appended

    def test_merge_detects_already_wired(self, tmp_path: Path):
        assert scaffold.merge_settings_hooks(tmp_path) is True
        assert scaffold.merge_settings_hooks(tmp_path) is False  # no duplicate entry
        settings = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
        assert len(settings["hooks"]["PostToolUse"]) == 1

    def test_merge_detects_per_tool_wiring(self, tmp_path: Path):
        path = tmp_path / ".claude" / "settings.local.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "matcher": "Read",
                                "hooks": [{"type": "command", "command": "bash .claude/hooks/post-tool-logger.sh"}],
                            }
                        ]
                    }
                }
            )
        )
        assert scaffold.merge_settings_hooks(tmp_path) is False  # existing per-tool style respected
