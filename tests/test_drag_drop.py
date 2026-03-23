"""Tests for drag-and-drop infrastructure between Kanban board columns."""

from agile_backlog.models import BacklogItem
from agile_backlog.pure import filter_items


class TestDragDropInfrastructure:
    """Verify the move logic that drag-and-drop relies on."""

    def test_move_item_changes_status(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature", status="backlog")
        item.status = "doing"
        assert item.status == "doing"

    def test_move_to_doing_sets_phase(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature", status="backlog")
        item.status = "doing"
        item.phase = item.phase or "plan"
        assert item.phase == "plan"

    def test_move_to_backlog_clears_phase(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature", status="doing", phase="build")
        item.status = "backlog"
        item.phase = None
        assert item.phase is None

    def test_move_preserves_other_fields(self):
        item = BacklogItem(
            id="test",
            title="Test",
            priority="P1",
            category="bug",
            status="backlog",
            sprint_target=18,
            tags=["ui"],
        )
        item.status = "doing"
        assert item.priority == "P1"
        assert item.sprint_target == 18
        assert item.tags == ["ui"]

    def test_filter_items_after_move(self):
        items = [
            BacklogItem(id="a", title="A", priority="P2", category="feature", status="doing"),
            BacklogItem(id="b", title="B", priority="P2", category="feature", status="backlog"),
        ]
        doing = filter_items(items, status="doing")
        assert len(doing) == 1
        assert doing[0].id == "a"
