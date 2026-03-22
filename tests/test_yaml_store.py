from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from agile_backlog.models import BacklogItem
from agile_backlog.yaml_store import item_exists, load_all, load_item, save_item


@pytest.fixture()
def backlog_dir(tmp_path: Path) -> Path:
    """Create a temporary backlog directory and patch git root detection."""
    bd = tmp_path / "backlog"
    bd.mkdir()
    return bd


@pytest.fixture(autouse=True)
def _patch_backlog_dir(backlog_dir: Path):
    """Patch get_backlog_dir to return the tmp backlog dir."""
    with patch("agile_backlog.yaml_store.get_backlog_dir", return_value=backlog_dir):
        yield


def _make_item(**overrides) -> BacklogItem:
    defaults = dict(
        id="test-item",
        title="Test item",
        priority="P2",
        category="feature",
    )
    defaults.update(overrides)
    return BacklogItem(**defaults)


class TestSaveAndLoad:
    def test_round_trip(self, backlog_dir: Path):
        item = _make_item()
        save_item(item)
        loaded = load_item("test-item")
        assert loaded.title == "Test item"
        assert loaded.priority == "P2"
        assert loaded.status == "backlog"

    def test_save_creates_yaml_file(self, backlog_dir: Path):
        item = _make_item()
        save_item(item)
        assert (backlog_dir / "test-item.yaml").exists()

    def test_yaml_does_not_contain_id_field(self, backlog_dir: Path):
        item = _make_item()
        save_item(item)
        raw = yaml.safe_load((backlog_dir / "test-item.yaml").read_text())
        assert "id" not in raw

    def test_load_item_not_found_raises(self, backlog_dir: Path):
        with pytest.raises(FileNotFoundError):
            load_item("nonexistent")

    def test_save_updates_updated_date(self, backlog_dir: Path):
        item = _make_item(created=date(2026, 1, 1), updated=date(2026, 1, 1))
        save_item(item)
        loaded = load_item("test-item")
        assert loaded.updated == date.today()
        assert loaded.created == date(2026, 1, 1)  # created preserved

    def test_load_handles_id_field_in_yaml(self, backlog_dir: Path):
        """If someone manually adds id: to a YAML file, it should not crash."""
        data = {
            "id": "wrong-id",
            "title": "Test",
            "status": "backlog",
            "priority": "P2",
            "category": "feature",
            "created": "2026-03-21",
            "updated": "2026-03-21",
            "depends_on": [],
            "tags": [],
            "description": "",
            "acceptance_criteria": [],
            "notes": "",
        }
        (backlog_dir / "test-item.yaml").write_text(yaml.dump(data))
        loaded = load_item("test-item")
        assert loaded.id == "test-item"  # filename-derived, not from YAML


class TestLoadAll:
    def test_empty_dir(self, backlog_dir: Path):
        assert load_all() == []

    def test_multiple_items(self, backlog_dir: Path):
        save_item(_make_item(id="item-a", title="Item A"))
        save_item(_make_item(id="item-b", title="Item B"))
        items = load_all()
        ids = {i.id for i in items}
        assert ids == {"item-a", "item-b"}

    def test_skips_invalid_yaml(self, backlog_dir: Path):
        (backlog_dir / "bad.yaml").write_text(": : : not valid yaml mapping")
        save_item(_make_item(id="good", title="Good"))
        items = load_all()
        assert len(items) == 1
        assert items[0].id == "good"

    def test_skips_yaml_missing_required_fields(self, backlog_dir: Path):
        """YAML that parses as dict but fails Pydantic validation."""
        (backlog_dir / "incomplete.yaml").write_text(yaml.dump({"title": "No priority"}))
        save_item(_make_item(id="good", title="Good"))
        items = load_all()
        assert len(items) == 1
        assert items[0].id == "good"


class TestItemExists:
    def test_exists(self, backlog_dir: Path):
        save_item(_make_item())
        assert item_exists("test-item") is True

    def test_not_exists(self, backlog_dir: Path):
        assert item_exists("nope") is False


class TestSaveOverwrite:
    def test_save_updates_existing(self, backlog_dir: Path):
        save_item(_make_item(description="v1"))
        save_item(_make_item(description="v2"))
        loaded = load_item("test-item")
        assert loaded.description == "v2"
