# tests/test_app.py
from src.app import category_style, detect_current_sprint, filter_items, render_card_html
from src.models import BacklogItem


def _item(**overrides) -> BacklogItem:
    defaults = dict(id="test", title="Test", priority="P2", category="feature")
    defaults.update(overrides)
    return BacklogItem(**defaults)


class TestCategoryStyle:
    def test_known_category_feature(self):
        color, bg = category_style("feature")
        assert color == "#1d4ed8"
        assert bg == "#dbeafe"

    def test_known_category_bug(self):
        color, bg = category_style("bug")
        assert color == "#be185d"
        assert bg == "#fce7f3"

    def test_known_category_security(self):
        color, bg = category_style("security")
        assert color == "#5b21b6"
        assert bg == "#ede9fe"

    def test_known_category_tech_debt(self):
        color, bg = category_style("tech-debt")
        assert color == "#92400e"
        assert bg == "#fef3c7"

    def test_known_category_docs(self):
        color, bg = category_style("docs")
        assert color == "#065f46"
        assert bg == "#d1fae5"

    def test_known_category_infra(self):
        color, bg = category_style("infra")
        assert color == "#155e75"
        assert bg == "#cffafe"

    def test_unknown_category_fallback(self):
        color, bg = category_style("random-thing")
        assert color == "#4b5563"
        assert bg == "#f3f4f6"


class TestFilterItems:
    def test_no_filters_returns_all(self):
        items = [_item(id="a"), _item(id="b")]
        assert len(filter_items(items)) == 2

    def test_filter_by_status(self):
        items = [_item(id="a", status="backlog"), _item(id="b", status="doing")]
        result = filter_items(items, status="doing")
        assert len(result) == 1
        assert result[0].id == "b"

    def test_filter_by_priority(self):
        items = [_item(id="a", priority="P1"), _item(id="b", priority="P3")]
        result = filter_items(items, priority="P1")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_filter_by_category(self):
        items = [_item(id="a", category="bug"), _item(id="b", category="feature")]
        result = filter_items(items, category="bug")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_filter_by_sprint(self):
        items = [_item(id="a", sprint_target=2), _item(id="b", sprint_target=None)]
        result = filter_items(items, sprint=2)
        assert len(result) == 1
        assert result[0].id == "a"

    def test_filter_by_search_title(self):
        items = [_item(id="a", title="Fix auth leak"), _item(id="b", title="Add feature")]
        result = filter_items(items, search="auth")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_filter_by_search_description(self):
        items = [_item(id="a", description="OAuth2 tokens"), _item(id="b", description="Nothing")]
        result = filter_items(items, search="oauth")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_filter_by_search_tags(self):
        items = [_item(id="a", tags=["urgent"]), _item(id="b", tags=["low"])]
        result = filter_items(items, search="urgent")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_combined_filters_and_logic(self):
        items = [
            _item(id="a", priority="P1", category="bug"),
            _item(id="b", priority="P1", category="feature"),
            _item(id="c", priority="P3", category="bug"),
        ]
        result = filter_items(items, priority="P1", category="bug")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_empty_list(self):
        assert filter_items([]) == []

    def test_all_filtered_out(self):
        items = [_item(id="a", priority="P3")]
        assert filter_items(items, priority="P1") == []

    def test_filter_priority_range_p2_plus(self):
        items = [_item(id="a", priority="P1"), _item(id="b", priority="P2"), _item(id="c", priority="P3")]
        result = filter_items(items, priority="P2+")
        assert len(result) == 2
        ids = {i.id for i in result}
        assert ids == {"a", "b"}

    def test_filter_priority_range_p3_plus(self):
        items = [_item(id="a", priority="P1"), _item(id="b", priority="P2"), _item(id="c", priority="P3")]
        result = filter_items(items, priority="P3+")
        assert len(result) == 3

    def test_filter_priority_exact_still_works(self):
        items = [_item(id="a", priority="P1"), _item(id="b", priority="P2")]
        result = filter_items(items, priority="P1")
        assert len(result) == 1
        assert result[0].id == "a"


class TestRenderCardHtml:
    def test_contains_title(self):
        html = render_card_html(_item(title="Fix auth leak"))
        assert "Fix auth leak" in html

    def test_contains_category_text_no_emoji(self):
        html = render_card_html(_item(category="bug"))
        assert "bug" in html
        # No emoji in category pills
        assert "\U0001f41b" not in html

    def test_contains_priority_badge(self):
        html = render_card_html(_item(priority="P1"))
        assert "P1" in html

    def test_contains_sprint_indicator(self):
        html = render_card_html(_item(sprint_target=2))
        assert "S2" in html

    def test_unplanned_sprint(self):
        html = render_card_html(_item(sprint_target=None))
        # Unplanned items don't show a sprint indicator
        assert "S2" not in html
        assert "S3" not in html

    def test_contains_category_color(self):
        html = render_card_html(_item(category="security"))
        assert "#5b21b6" in html

    def test_render_card_with_phase(self):
        html = render_card_html(_item(phase="build"))
        assert "build" in html
        # Phase uses italic style
        assert "italic" in html

    def test_render_card_without_phase(self):
        html = render_card_html(_item(phase=None))
        # Phase badge should not appear when phase is None
        assert "italic" not in html

    def test_p1_card_has_red_left_border(self):
        html = render_card_html(_item(priority="P1"))
        assert "border-left:3px solid #ef4444" in html

    def test_p2_card_no_left_border(self):
        html = render_card_html(_item(priority="P2"))
        assert "border-left" not in html

    def test_card_title_14px(self):
        html = render_card_html(_item(title="Some title"))
        assert "14px" in html

    def test_badge_uses_design_system_colors(self):
        html = render_card_html(_item(category="feature"))
        assert "#1d4ed8" in html
        assert "#dbeafe" in html

    def test_sprint_badge_outlined_style(self):
        html = render_card_html(_item(sprint_target=3))
        assert "background:none" in html
        assert "border:1px solid #e5e7eb" in html

    def test_priority_badge_has_bg_color(self):
        html = render_card_html(_item(priority="P1"))
        assert "#dc2626" in html
        assert "#fef2f2" in html

    def test_design_reviewed_badge_shown_when_true(self):
        html = render_card_html(_item(design_reviewed=True))
        assert "design" in html
        assert "#059669" in html

    def test_code_reviewed_badge_shown_when_true(self):
        html = render_card_html(_item(code_reviewed=True))
        assert "code" in html
        assert "#059669" in html

    def test_review_badges_not_shown_by_default(self):
        html = render_card_html(_item())
        assert "#d1fae5" not in html


class TestDetectCurrentSprint:
    def test_detects_from_doing_items(self):
        items = [
            _item(id="a", status="doing", sprint_target=3),
            _item(id="b", status="doing", sprint_target=3),
            _item(id="c", status="backlog", sprint_target=4),
        ]
        assert detect_current_sprint(items) == 3

    def test_returns_none_when_no_doing(self):
        items = [_item(id="a", status="backlog", sprint_target=2)]
        assert detect_current_sprint(items) is None

    def test_returns_none_when_doing_has_no_sprint(self):
        items = [_item(id="a", status="doing", sprint_target=None)]
        assert detect_current_sprint(items) is None

    def test_returns_most_common_sprint(self):
        items = [
            _item(id="a", status="doing", sprint_target=3),
            _item(id="b", status="doing", sprint_target=3),
            _item(id="c", status="doing", sprint_target=2),
        ]
        assert detect_current_sprint(items) == 3

    def test_empty_list(self):
        assert detect_current_sprint([]) is None
