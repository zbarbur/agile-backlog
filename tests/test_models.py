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


class TestPhaseField:
    def test_phase_default_none(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        assert item.phase is None

    def test_phase_valid_value(self):
        for val in ("plan", "build", "review"):
            item = BacklogItem(id="test", title="Test", priority="P2", category="feature", phase=val)
            assert item.phase == val

    def test_phase_invalid_migrated_to_plan(self):
        # Unknown old phase values are migrated to "plan" rather than raising
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature", phase="invalid-phase")
        assert item.phase == "plan"

    def test_phase_migration(self):
        """Old phase values are migrated to new 3-value enum on load."""
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="scoping").phase == "plan"
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="spec").phase == "plan"
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="spec-review").phase == "plan"
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="design").phase == "plan"
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="design-review").phase == "plan"
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="coding").phase == "build"
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="code-review").phase == "review"
        assert BacklogItem(id="t", title="T", priority="P2", category="x", phase="testing").phase == "review"

    def test_design_reviewed_default_false(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        assert item.design_reviewed is False

    def test_code_reviewed_default_false(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        assert item.code_reviewed is False


class TestTaskDefinitionFields:
    def test_goal_default_empty(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        assert item.goal == ""

    def test_complexity_valid_values(self):
        for val in ("S", "M", "L"):
            item = BacklogItem(id="test", title="Test", priority="P2", category="feature", complexity=val)
            assert item.complexity == val

    def test_complexity_invalid_rejected(self):
        with pytest.raises(ValueError):
            BacklogItem(id="test", title="Test", priority="P2", category="feature", complexity="XL")

    def test_complexity_default_none(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        assert item.complexity is None

    def test_technical_specs_default_empty(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        assert item.technical_specs == []


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
