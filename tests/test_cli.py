import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from agile_backlog.cli import main


@pytest.fixture()
def backlog_dir(tmp_path: Path) -> Path:
    bd = tmp_path / "backlog"
    bd.mkdir()
    return bd


@pytest.fixture(autouse=True)
def _patch_backlog_dir(backlog_dir: Path):
    with patch("agile_backlog.yaml_store.get_backlog_dir", return_value=backlog_dir):
        yield


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestAdd:
    def test_add_basic(self, runner: CliRunner, backlog_dir: Path):
        result = runner.invoke(main, ["add", "Fix auth leak", "--priority", "P1", "--category", "bug"])
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
        runner.invoke(main, ["add", "Feature item", "--category", "feature"])
        runner.invoke(main, ["add", "Doc item", "--category", "docs"])
        result = runner.invoke(main, ["list", "--category", "feature"])
        assert "feature-item" in result.output
        assert "doc-item" not in result.output

    def test_list_filter_by_sprint(self, runner: CliRunner):
        runner.invoke(main, ["add", "Sprint 2 task", "--category", "feature", "--sprint", "2"])
        runner.invoke(main, ["add", "No sprint", "--category", "feature"])
        result = runner.invoke(main, ["list", "--sprint", "2"])
        assert "sprint-2-task" in result.output
        assert "no-sprint" not in result.output

    def test_list_shows_phase_and_sprint_columns(self, runner: CliRunner):
        runner.invoke(main, ["add", "Phased task", "--category", "feature", "--sprint", "5"])
        runner.invoke(main, ["move", "phased-task", "--status", "doing", "--phase", "build"])
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "Phase" in result.output
        assert "Sprint" in result.output
        assert "build" in result.output
        assert "5" in result.output

    def test_list_empty_phase_shows_dash(self, runner: CliRunner):
        runner.invoke(main, ["add", "Plain task", "--category", "feature"])
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        data_line = [line for line in lines if "plain-task" in line][0]
        assert "-" in data_line


class TestMove:
    def test_move_status(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--category", "feature"])
        result = runner.invoke(main, ["move", "task-a", "--status", "doing"])
        assert result.exit_code == 0
        assert "doing" in result.output

    def test_move_nonexistent(self, runner: CliRunner):
        result = runner.invoke(main, ["move", "nope", "--status", "doing"])
        assert result.exit_code != 0

    def test_move_with_phase(self, runner: CliRunner, backlog_dir: Path):
        runner.invoke(main, ["add", "Task Phase", "--category", "feature"])
        result = runner.invoke(main, ["move", "task-phase", "--status", "doing", "--phase", "plan"])
        assert result.exit_code == 0
        assert "doing" in result.output
        # Verify phase is persisted in the YAML file
        import yaml

        data = yaml.safe_load((backlog_dir / "task-phase.yaml").read_text())
        assert data["phase"] == "plan"

    def test_move_to_done_keeps_phase(self, runner: CliRunner, backlog_dir: Path):
        import yaml

        runner.invoke(main, ["add", "Task Phase2", "--category", "feature"])
        runner.invoke(main, ["move", "task-phase2", "--status", "doing", "--phase", "build"])
        runner.invoke(main, ["move", "task-phase2", "--status", "done"])
        data = yaml.safe_load((backlog_dir / "task-phase2.yaml").read_text())
        assert data["phase"] == "build"

    def test_move_to_backlog_clears_phase(self, runner: CliRunner, backlog_dir: Path):
        import yaml

        runner.invoke(main, ["add", "Task Phase3", "--category", "feature"])
        runner.invoke(main, ["move", "task-phase3", "--status", "doing", "--phase", "review"])
        runner.invoke(main, ["move", "task-phase3", "--status", "backlog"])
        data = yaml.safe_load((backlog_dir / "task-phase3.yaml").read_text())
        assert data["phase"] is None

    def test_move_multiple_ids(self, runner: CliRunner):
        """Move multiple items at once."""
        runner.invoke(main, ["add", "Alpha", "--category", "feature"])
        runner.invoke(main, ["add", "Beta", "--category", "feature"])
        runner.invoke(main, ["add", "Gamma", "--category", "feature"])
        result = runner.invoke(main, ["move", "alpha", "beta", "gamma", "--status", "doing"])
        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output
        assert "gamma" in result.output

    def test_move_with_sprint_flag(self, runner: CliRunner, backlog_dir: Path):
        """Move + set sprint in one call."""
        import yaml

        runner.invoke(main, ["add", "Task Sprint", "--category", "feature"])
        result = runner.invoke(main, ["move", "task-sprint", "--status", "doing", "--sprint", "5"])
        assert result.exit_code == 0
        data = yaml.safe_load((backlog_dir / "task-sprint.yaml").read_text())
        assert data["sprint_target"] == 5

    def test_move_bulk_partial_failure(self, runner: CliRunner):
        """One bad ID doesn't abort others."""
        runner.invoke(main, ["add", "Real item", "--category", "feature"])
        result = runner.invoke(main, ["move", "real-item", "fake-item", "--status", "doing"])
        assert result.exit_code == 1
        assert "real-item" in result.output
        assert "Moved" in result.output
        assert "fake-item" in result.output
        assert "not found" in result.output


class TestShow:
    def test_show_item(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--priority", "P1", "--category", "bug"])
        result = runner.invoke(main, ["show", "task-a"])
        assert result.exit_code == 0
        assert "Task A" in result.output
        assert "P1" in result.output
        assert "bug" in result.output

    def test_show_nonexistent(self, runner: CliRunner):
        result = runner.invoke(main, ["show", "nope"])
        assert result.exit_code != 0


class TestEdit:
    def test_edit_goal(self, runner, backlog_dir):
        runner.invoke(main, ["add", "Edit me", "--category", "feature"])
        result = runner.invoke(main, ["edit", "edit-me", "--goal", "Test goal"])
        assert result.exit_code == 0
        assert "Updated" in result.output
        show = runner.invoke(main, ["show", "edit-me"])
        assert "Test goal" in show.output

    def test_edit_complexity(self, runner, backlog_dir):
        runner.invoke(main, ["add", "Edit me", "--category", "feature"])
        result = runner.invoke(main, ["edit", "edit-me", "--complexity", "M"])
        assert result.exit_code == 0

    def test_edit_multiple_fields(self, runner, backlog_dir):
        runner.invoke(main, ["add", "Edit me", "--category", "feature"])
        result = runner.invoke(main, ["edit", "edit-me", "--goal", "My goal", "--priority", "P1", "--complexity", "L"])
        assert result.exit_code == 0
        show = runner.invoke(main, ["show", "edit-me"])
        assert "My goal" in show.output
        assert "P1" in show.output

    def test_edit_acceptance_criteria(self, runner, backlog_dir):
        runner.invoke(main, ["add", "Edit me", "--category", "feature"])
        result = runner.invoke(
            main,
            ["edit", "edit-me", "--acceptance-criteria", "Criterion 1", "--acceptance-criteria", "Criterion 2"],
        )
        assert result.exit_code == 0

    def test_edit_nonexistent(self, runner):
        result = runner.invoke(main, ["edit", "nope", "--goal", "test"])
        assert result.exit_code != 0

    def test_edit_multiple_ids(self, runner, backlog_dir):
        """Edit sprint on multiple items at once."""
        runner.invoke(main, ["add", "Item A", "--category", "feature"])
        runner.invoke(main, ["add", "Item B", "--category", "feature"])
        result = runner.invoke(main, ["edit", "item-a", "item-b", "--sprint", "7"])
        assert result.exit_code == 0
        assert "item-a" in result.output
        assert "item-b" in result.output

    def test_edit_bulk_partial_failure(self, runner):
        """One bad ID doesn't abort others."""
        runner.invoke(main, ["add", "Real edit", "--category", "feature"])
        result = runner.invoke(main, ["edit", "real-edit", "fake-edit", "--goal", "G"])
        assert result.exit_code == 1
        assert "real-edit" in result.output
        assert "Updated" in result.output
        assert "fake-edit" in result.output
        assert "not found" in result.output


class TestNote:
    def test_note_add(self, runner: CliRunner, backlog_dir: Path):
        runner.invoke(main, ["add", "Task A", "--category", "feature"])
        result = runner.invoke(main, ["note", "task-a", "Focus on filters first"])
        assert result.exit_code == 0
        assert "Note added to task-a" in result.output
        show = runner.invoke(main, ["show", "task-a"])
        assert "Focus on filters first" in show.output

    def test_note_flagged(self, runner: CliRunner, backlog_dir: Path):
        runner.invoke(main, ["add", "Task B", "--category", "feature"])
        result = runner.invoke(main, ["note", "task-b", "Needs review", "--flag"])
        assert result.exit_code == 0
        assert "[FLAGGED]" in result.output
        flagged_result = runner.invoke(main, ["flagged"])
        assert "task-b" in flagged_result.output
        assert "Needs review" in flagged_result.output

    def test_flagged_empty(self, runner: CliRunner):
        result = runner.invoke(main, ["flagged"])
        assert result.exit_code == 0
        assert "No flagged notes." in result.output

    def test_note_nonexistent_item(self, runner: CliRunner):
        result = runner.invoke(main, ["note", "nope", "some note"])
        assert result.exit_code != 0

    def test_resolve_notes(self, runner: CliRunner, backlog_dir: Path):
        runner.invoke(main, ["add", "Task C", "--category", "feature"])
        runner.invoke(main, ["note", "task-c", "Flagged note", "--flag"])
        # Verify it appears in flagged list before resolving
        flagged_result = runner.invoke(main, ["flagged"])
        assert "task-c" in flagged_result.output
        # Resolve notes
        runner.invoke(main, ["edit", "task-c", "--resolve-notes"])
        # Should no longer appear in flagged list
        flagged_after = runner.invoke(main, ["flagged"])
        assert "task-c" not in flagged_after.output


class TestServe:
    def test_serve_calls_run_app(self, runner: CliRunner, monkeypatch):
        """Verify serve calls run_app with correct defaults."""
        calls = []
        monkeypatch.setattr("agile_backlog.app.run_app", lambda **kw: calls.append(kw))
        result = runner.invoke(main, ["serve"])
        assert result.exit_code == 0
        assert len(calls) == 1
        assert calls[0]["host"] == "127.0.0.1"
        assert calls[0]["port"] == 8501
        assert calls[0]["reload"] is False

    def test_serve_without_nicegui(self, runner: CliRunner):
        """Serve shows helpful error when NiceGUI not installed."""
        with patch.dict("sys.modules", {"agile_backlog.app": None}):
            result = runner.invoke(main, ["serve"])
        assert result.exit_code != 0
        assert "agile-backlog[ui]" in result.output


class TestJsonOutput:
    def test_list_json(self, backlog_dir):
        """list --json returns valid JSON array with all fields."""
        runner = CliRunner()
        runner.invoke(main, ["add", "Test Item", "--category", "feature"])
        result = runner.invoke(main, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert "title" in data[0]
        assert "priority" in data[0]
        assert "comments" in data[0]  # ALL fields present

    def test_show_json(self, backlog_dir):
        """show --json returns valid JSON object with all fields."""
        runner = CliRunner()
        runner.invoke(main, ["add", "Test Item", "--category", "feature"])
        result = runner.invoke(main, ["show", "--json", "test-item"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert data["title"] == "Test Item"
        assert "acceptance_criteria" in data

    def test_flagged_json(self, backlog_dir):
        """flagged --json returns valid JSON."""
        runner = CliRunner()
        runner.invoke(main, ["add", "Test Item", "--category", "feature"])
        runner.invoke(main, ["note", "test-item", "check this", "--flag"])
        result = runner.invoke(main, ["flagged", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1


class TestMigrate:
    def test_migrate_dry_run(self, runner, backlog_dir):
        (backlog_dir / "old.yaml").write_text(
            yaml.dump(
                {
                    "title": "Old Item",
                    "status": "backlog",
                    "priority": "P2",
                    "category": "infra",
                    "agent_notes": [{"text": "note", "flagged": False, "resolved": False}],
                }
            )
        )
        result = runner.invoke(main, ["migrate", "--dry-run"])
        assert result.exit_code == 0
        assert "old" in result.output
        assert "category: infra" in result.output
        assert "agent_notes" in result.output
        # Verify file was NOT modified
        raw = yaml.safe_load((backlog_dir / "old.yaml").read_text())
        assert raw["category"] == "infra"

    def test_migrate_applies_changes(self, runner, backlog_dir):
        (backlog_dir / "old.yaml").write_text(
            yaml.dump(
                {
                    "title": "Old Item",
                    "status": "backlog",
                    "priority": "P2",
                    "category": "tech-debt",
                    "agent_notes": [{"text": "note", "flagged": False, "resolved": False}],
                }
            )
        )
        result = runner.invoke(main, ["migrate"])
        assert result.exit_code == 0
        # Verify file WAS modified
        raw = yaml.safe_load((backlog_dir / "old.yaml").read_text())
        assert raw["category"] == "chore"
        assert "comments" in raw
        assert "agent_notes" not in raw


class TestTagsFilter:
    def test_list_filter_by_tag(self, runner, backlog_dir):
        (backlog_dir / "a.yaml").write_text(
            yaml.dump(
                {
                    "title": "A",
                    "status": "backlog",
                    "priority": "P2",
                    "category": "feature",
                    "tags": ["ui", "planning"],
                }
            )
        )
        (backlog_dir / "b.yaml").write_text(
            yaml.dump(
                {
                    "title": "B",
                    "status": "backlog",
                    "priority": "P2",
                    "category": "feature",
                    "tags": ["cli"],
                }
            )
        )
        result = runner.invoke(main, ["list", "--tags", "ui"])
        assert "A" in result.output
        assert "B" not in result.output


class TestSprintStatus:
    def test_sprint_status_default(self, runner: CliRunner, backlog_dir: Path):
        """Shows current sprint items grouped by phase."""
        # Create items in sprint 5 with different phases
        for title, phase in [("Task A", "spec"), ("Task B", "build"), ("Task C", "build")]:
            runner.invoke(main, ["add", title, "--category", "feature", "--sprint", "5"])
            slug = title.lower().replace(" ", "-")
            runner.invoke(main, ["move", slug, "--status", "doing", "--phase", phase])

        with patch("agile_backlog.cli.get_current_sprint", return_value=5):
            result = runner.invoke(main, ["sprint-status"])
        assert result.exit_code == 0
        assert "spec" in result.output
        assert "build" in result.output
        assert "Task A" in result.output
        assert "Task B" in result.output
        # Should show progress
        assert "3" in result.output

    def test_sprint_status_by_number(self, runner: CliRunner, backlog_dir: Path):
        """--sprint flag filters to a specific sprint."""
        runner.invoke(main, ["add", "Sprint 5", "--category", "feature", "--sprint", "5"])
        runner.invoke(main, ["add", "Sprint 6", "--category", "feature", "--sprint", "6"])

        result = runner.invoke(main, ["sprint-status", "--sprint", "6"])
        assert result.exit_code == 0
        assert "Sprint 6" in result.output
        assert "Sprint 5" not in result.output

    def test_sprint_status_empty(self, runner: CliRunner):
        """No items prints clean message."""
        with patch("agile_backlog.cli.get_current_sprint", return_value=99):
            result = runner.invoke(main, ["sprint-status"])
        assert result.exit_code == 0
        assert "No items" in result.output


class TestValidate:
    def test_validate_passing(self, runner: CliRunner):
        """Fully specced items pass validation."""
        runner.invoke(main, ["add", "Good item", "--category", "feature", "--sprint", "5"])
        runner.invoke(
            main,
            [
                "edit",
                "good-item",
                "--goal",
                "Deliver X",
                "--complexity",
                "S",
                "--acceptance-criteria",
                "AC one",
                "--acceptance-criteria",
                "AC two",
                "--technical-specs",
                "File: foo.py",
            ],
        )
        with patch("agile_backlog.cli.get_current_sprint", return_value=5):
            result = runner.invoke(main, ["validate"])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_validate_missing_fields(self, runner: CliRunner):
        """Reports missing goal, complexity, AC."""
        runner.invoke(main, ["add", "Bare item", "--category", "feature", "--sprint", "5"])
        with patch("agile_backlog.cli.get_current_sprint", return_value=5):
            result = runner.invoke(main, ["validate"])
        assert result.exit_code == 1
        assert "FAIL" in result.output
        assert "goal" in result.output
        assert "complexity" in result.output

    def test_validate_exit_code(self, runner: CliRunner):
        """Returns exit code 1 on any failure."""
        runner.invoke(main, ["add", "Good", "--category", "feature", "--sprint", "5"])
        runner.invoke(
            main,
            [
                "edit",
                "good",
                "--goal",
                "G",
                "--complexity",
                "S",
                "--acceptance-criteria",
                "A1",
                "--acceptance-criteria",
                "A2",
                "--technical-specs",
                "File: x.py",
            ],
        )
        runner.invoke(main, ["add", "Bad", "--category", "feature", "--sprint", "5"])
        with patch("agile_backlog.cli.get_current_sprint", return_value=5):
            result = runner.invoke(main, ["validate"])
        assert result.exit_code == 1


class TestDelete:
    def test_delete_item(self, runner: CliRunner, backlog_dir: Path):
        runner.invoke(main, ["add", "Doomed", "--category", "feature"])
        assert (backlog_dir / "doomed.yaml").exists()
        result = runner.invoke(main, ["delete", "doomed", "--yes"])
        assert result.exit_code == 0
        assert "Deleted" in result.output
        assert not (backlog_dir / "doomed.yaml").exists()

    def test_delete_multiple(self, runner: CliRunner, backlog_dir: Path):
        runner.invoke(main, ["add", "A", "--category", "feature"])
        runner.invoke(main, ["add", "B", "--category", "feature"])
        result = runner.invoke(main, ["delete", "a", "b", "--yes"])
        assert result.exit_code == 0
        assert not (backlog_dir / "a.yaml").exists()
        assert not (backlog_dir / "b.yaml").exists()

    def test_delete_nonexistent(self, runner: CliRunner):
        result = runner.invoke(main, ["delete", "nope", "--yes"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_delete_confirm_abort(self, runner: CliRunner):
        runner.invoke(main, ["add", "Keep me", "--category", "feature"])
        result = runner.invoke(main, ["delete", "keep-me"], input="n\n")
        assert "Aborted" in result.output


class TestInstallSkills:
    def test_install_skills(self, runner: CliRunner, tmp_path: Path):
        """Install-skills copies bundled skills to target dir."""
        target = tmp_path / ".claude" / "skills"
        result = runner.invoke(main, ["install-skills", "--target", str(target)])
        assert result.exit_code == 0
        assert "Installed" in result.output
        assert (target / "sprint-start").exists()
        assert (target / "cli-reference").exists()

    def test_install_skills_skip_existing(self, runner: CliRunner, tmp_path: Path):
        """Existing skills are not overwritten without --force."""
        target = tmp_path / ".claude" / "skills"
        runner.invoke(main, ["install-skills", "--target", str(target)])
        result = runner.invoke(main, ["install-skills", "--target", str(target)])
        assert "Skipped" in result.output

    def test_install_skills_force(self, runner: CliRunner, tmp_path: Path):
        """--force overwrites existing skills."""
        target = tmp_path / ".claude" / "skills"
        runner.invoke(main, ["install-skills", "--target", str(target)])
        result = runner.invoke(main, ["install-skills", "--target", str(target), "--force"])
        assert "Installed" in result.output
        assert "Skipped" not in result.output


class TestContextReport:
    def test_context_report_command(self, tmp_path: Path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "reads-test.jsonl"
        log_file.write_text('{"ts":"2026-03-24T10:00:00Z","file":"/src/app.py","offset":0,"limit":200}\n')
        output_dir = tmp_path / "reports"

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["context-report", "--log-dir", str(log_dir), "--output-dir", str(output_dir), "--sprint", "23"],
        )
        assert result.exit_code == 0
        assert "SPRINT23_CONTEXT_REPORT.json" in result.output
        assert (output_dir / "SPRINT23_CONTEXT_REPORT.json").exists()


class TestBacklogDirOverride:
    @pytest.fixture(autouse=True)
    def _patch_backlog_dir(self):
        """Override the module-level autouse fixture — let real get_backlog_dir run."""
        from agile_backlog.yaml_store import set_backlog_dir

        yield
        set_backlog_dir(None)

    def test_backlog_dir_flag(self, runner: CliRunner, tmp_path: Path):
        """Global --backlog-dir flag overrides default backlog directory."""
        custom_dir = tmp_path / "my-backlog"
        result = runner.invoke(main, ["--backlog-dir", str(custom_dir), "add", "Test item", "--category", "feature"])
        assert result.exit_code == 0
        assert (custom_dir / "test-item.yaml").exists()

    def test_backlog_dir_list(self, runner: CliRunner, tmp_path: Path):
        """Items created with --backlog-dir are found with same flag."""
        custom_dir = tmp_path / "my-backlog"
        runner.invoke(main, ["--backlog-dir", str(custom_dir), "add", "Custom item", "--category", "feature"])
        result = runner.invoke(main, ["--backlog-dir", str(custom_dir), "list"])
        assert "custom-item" in result.output
