from datetime import date

import pytest

from src.models import BacklogItem, slugify


class TestSlugify:
    def test_simple_title(self):
        assert slugify("Fix auth leak") == "fix-auth-leak"

    def test_special_characters(self):
        assert slugify("Add OAuth2/JWT support!") == "add-oauth2-jwt-support"

    def test_consecutive_hyphens_collapsed(self):
        assert slugify("foo  --  bar") == "foo-bar"

    def test_leading_trailing_hyphens_stripped(self):
        assert slugify("--hello--") == "hello"

    def test_empty_string(self):
        assert slugify("") == ""


class TestBacklogItem:
    def test_minimal_valid_item(self):
        item = BacklogItem(
            id="test-item",
            title="Test item",
            priority="P2",
            category="feature",
        )
        assert item.status == "backlog"
        assert item.created == date.today()
        assert item.updated == date.today()
        assert item.depends_on == []
        assert item.tags == []

    def test_all_fields(self):
        item = BacklogItem(
            id="full-item",
            title="Full item",
            status="doing",
            priority="P1",
            category="security",
            sprint_target=2,
            created=date(2026, 1, 1),
            updated=date(2026, 3, 21),
            depends_on=["other-item"],
            tags=["urgent"],
            description="A detailed description.",
            acceptance_criteria=["Criterion 1"],
            notes="Some notes.",
        )
        assert item.sprint_target == 2
        assert item.depends_on == ["other-item"]

    def test_invalid_status_rejected(self):
        with pytest.raises(ValueError):
            BacklogItem(id="bad", title="Bad", status="invalid", priority="P1", category="x")

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValueError):
            BacklogItem(id="bad", title="Bad", priority="P0", category="x")


class TestToYamlDict:
    def test_excludes_id(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        d = item.to_yaml_dict()
        assert "id" not in d
        assert d["title"] == "Test"
        assert d["status"] == "backlog"

    def test_dates_are_date_objects(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        d = item.to_yaml_dict()
        assert isinstance(d["created"], date)

    def test_empty_lists_included(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        d = item.to_yaml_dict()
        assert d["depends_on"] == []
        assert d["tags"] == []
