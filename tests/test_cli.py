from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.cli import main


@pytest.fixture()
def backlog_dir(tmp_path: Path) -> Path:
    bd = tmp_path / "backlog"
    bd.mkdir()
    return bd


@pytest.fixture(autouse=True)
def _patch_backlog_dir(backlog_dir: Path):
    with patch("src.yaml_store.get_backlog_dir", return_value=backlog_dir):
        yield


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestAdd:
    def test_add_basic(self, runner: CliRunner, backlog_dir: Path):
        result = runner.invoke(main, ["add", "Fix auth leak", "--priority", "P1", "--category", "security"])
        assert result.exit_code == 0
        assert "fix-auth-leak" in result.output
        assert (backlog_dir / "fix-auth-leak.yaml").exists()

    def test_add_default_priority(self, runner: CliRunner):
        result = runner.invoke(main, ["add", "Some task", "--category", "feature"])
        assert result.exit_code == 0
        assert "some-task" in result.output

    def test_add_with_description(self, runner: CliRunner):
        result = runner.invoke(main, ["add", "My task", "--category", "docs", "--description", "Details here"])
        assert result.exit_code == 0

    def test_add_slug_collision(self, runner: CliRunner, backlog_dir: Path):
        """Adding two items with the same title should create unique IDs."""
        runner.invoke(main, ["add", "Duplicate", "--category", "feature"])
        result = runner.invoke(main, ["add", "Duplicate", "--category", "feature"])
        assert result.exit_code == 0
        assert "duplicate-2" in result.output
        assert (backlog_dir / "duplicate.yaml").exists()
        assert (backlog_dir / "duplicate-2.yaml").exists()

    def test_add_with_sprint(self, runner: CliRunner):
        result = runner.invoke(main, ["add", "Sprint task", "--category", "feature", "--sprint", "3"])
        assert result.exit_code == 0


class TestList:
    def test_list_empty(self, runner: CliRunner):
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "No items" in result.output

    def test_list_shows_items(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--priority", "P1", "--category", "feature"])
        runner.invoke(main, ["add", "Task B", "--priority", "P2", "--category", "docs"])
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "task-a" in result.output
        assert "task-b" in result.output

    def test_list_filter_by_status(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--category", "feature"])
        runner.invoke(main, ["move", "task-a", "--status", "doing"])
        result = runner.invoke(main, ["list", "--status", "doing"])
        assert "task-a" in result.output
        result2 = runner.invoke(main, ["list", "--status", "done"])
        assert "task-a" not in result2.output

    def test_list_filter_by_priority(self, runner: CliRunner):
        runner.invoke(main, ["add", "Urgent", "--priority", "P1", "--category", "feature"])
        runner.invoke(main, ["add", "Chill", "--priority", "P3", "--category", "feature"])
        result = runner.invoke(main, ["list", "--priority", "P1"])
        assert "urgent" in result.output
        assert "chill" not in result.output

    def test_list_filter_by_category(self, runner: CliRunner):
        runner.invoke(main, ["add", "Sec item", "--category", "security"])
        runner.invoke(main, ["add", "Doc item", "--category", "docs"])
        result = runner.invoke(main, ["list", "--category", "security"])
        assert "sec-item" in result.output
        assert "doc-item" not in result.output

    def test_list_filter_by_sprint(self, runner: CliRunner):
        runner.invoke(main, ["add", "Sprint 2 task", "--category", "feature", "--sprint", "2"])
        runner.invoke(main, ["add", "No sprint", "--category", "feature"])
        result = runner.invoke(main, ["list", "--sprint", "2"])
        assert "sprint-2-task" in result.output
        assert "no-sprint" not in result.output


class TestMove:
    def test_move_status(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--category", "feature"])
        result = runner.invoke(main, ["move", "task-a", "--status", "doing"])
        assert result.exit_code == 0
        assert "doing" in result.output

    def test_move_nonexistent(self, runner: CliRunner):
        result = runner.invoke(main, ["move", "nope", "--status", "doing"])
        assert result.exit_code != 0


class TestShow:
    def test_show_item(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--priority", "P1", "--category", "security"])
        result = runner.invoke(main, ["show", "task-a"])
        assert result.exit_code == 0
        assert "Task A" in result.output
        assert "P1" in result.output
        assert "security" in result.output

    def test_show_nonexistent(self, runner: CliRunner):
        result = runner.invoke(main, ["show", "nope"])
        assert result.exit_code != 0


class TestServe:
    def test_serve_placeholder(self, runner: CliRunner):
        result = runner.invoke(main, ["serve"])
        assert result.exit_code == 0
        assert "Sprint 2" in result.output
