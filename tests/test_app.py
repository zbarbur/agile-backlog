# tests/test_app.py
# Unit tests for add-dialog sprint target options logic and reopen logic.

from datetime import date

from agile_backlog.models import BacklogItem


class TestAddDialogSprintOptions:
    """Verify the sprint target options built for the 'add new item' dialog."""

    @staticmethod
    def _build_sprint_options(current_sprint: int | None) -> dict:
        """Replicate the option-building logic from app.py add dialog."""
        add_sprint_options = {None: "Backlog (unplanned)"}
        if current_sprint is not None:
            add_sprint_options[current_sprint] = f"Sprint {current_sprint} (current)"
            add_sprint_options[current_sprint + 1] = f"Sprint {current_sprint + 1} (next)"
            add_sprint_options[current_sprint + 2] = f"Sprint {current_sprint + 2}+ (future)"
        return add_sprint_options

    def test_no_current_sprint_only_backlog(self):
        opts = self._build_sprint_options(None)
        assert len(opts) == 1
        assert None in opts

    def test_with_current_sprint_has_four_options(self):
        opts = self._build_sprint_options(16)
        assert len(opts) == 4
        assert None in opts
        assert 16 in opts
        assert 17 in opts
        assert 18 in opts

    def test_option_labels(self):
        opts = self._build_sprint_options(16)
        assert opts[None] == "Backlog (unplanned)"
        assert opts[16] == "Sprint 16 (current)"
        assert opts[17] == "Sprint 17 (next)"
        assert opts[18] == "Sprint 18+ (future)"

    def test_future_is_current_plus_two(self):
        """v.future key equals current_sprint + 2, matching pure.py grouping logic."""
        for sprint in (1, 10, 99):
            opts = self._build_sprint_options(sprint)
            assert sprint + 2 in opts
            assert "(future)" in opts[sprint + 2]


class TestReopenItemLogic:
    """Verify the reopen logic that moves a done item back to doing."""

    @staticmethod
    def _make_done_item(**overrides) -> BacklogItem:
        defaults = {
            "id": "test-item",
            "title": "Test Item",
            "status": "done",
            "priority": "P2",
            "category": "bug",
            "phase": "review",
            "notes": "",
        }
        defaults.update(overrides)
        return BacklogItem(**defaults)

    @staticmethod
    def _apply_reopen(item: BacklogItem, reason: str) -> None:
        """Apply reopen logic using the shared pure function."""
        from agile_backlog.pure import apply_reopen

        apply_reopen(item, reason)

    def test_reopen_sets_status_to_doing(self):
        item = self._make_done_item()
        self._apply_reopen(item, "Found regression")
        assert item.status == "doing"

    def test_reopen_sets_phase_to_build(self):
        item = self._make_done_item()
        self._apply_reopen(item, "Found regression")
        assert item.phase == "build"

    def test_reopen_appends_note_with_reason(self):
        item = self._make_done_item()
        self._apply_reopen(item, "Found regression")
        assert "Found regression" in item.notes
        assert "[Reopened" in item.notes

    def test_reopen_preserves_existing_notes(self):
        item = self._make_done_item(notes="Original note")
        self._apply_reopen(item, "Needs more work")
        assert "Original note" in item.notes
        assert "Needs more work" in item.notes

    def test_reopen_updates_date(self):
        item = self._make_done_item()
        self._apply_reopen(item, "Fix needed")
        assert item.updated == date.today()

    def test_reopen_note_format_includes_date(self):
        item = self._make_done_item()
        self._apply_reopen(item, "Test reason")
        expected_prefix = f"[Reopened {date.today().isoformat()}]"
        assert expected_prefix in item.notes

    def test_reopen_empty_notes_no_leading_whitespace(self):
        """When notes are empty, reopened note should not start with whitespace."""
        item = self._make_done_item(notes="")
        self._apply_reopen(item, "Reason")
        assert not item.notes.startswith("\n")
        assert not item.notes.startswith(" ")
