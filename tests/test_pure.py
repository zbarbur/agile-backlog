# tests/test_pure.py
from datetime import date, timedelta

from agile_backlog.models import BacklogItem
from agile_backlog.pure import (
    category_style,
    comment_badge_html,
    comment_thread_html,
    detect_current_sprint,
    filter_items,
    group_items_by_section,
    is_recently_done,
    render_backlog_card_html,
    render_card_html,
    render_comment_html,
)


def _item(**overrides) -> BacklogItem:
    defaults = dict(id="test", title="Test", priority="P2", category="feature")
    defaults.update(overrides)
    return BacklogItem(**defaults)


class TestCategoryStyle:
    def test_known_category_feature(self):
        color, bg = category_style("feature")
        assert color == "#60a5fa"
        assert bg == "rgba(59,130,246,0.08)"

    def test_known_category_bug(self):
        color, bg = category_style("bug")
        assert color == "#f472b6"
        assert bg == "rgba(244,114,182,0.08)"

    def test_known_category_docs(self):
        color, bg = category_style("docs")
        assert color == "#34d399"
        assert bg == "rgba(52,211,153,0.08)"

    def test_chore_style(self):
        text, bg = category_style("chore")
        assert text.startswith("#")
        assert bg.startswith("rgba")

    def test_unknown_category_fallback(self):
        color, bg = category_style("unknown")
        assert color == "#9ca3af"
        assert "rgba" in bg


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

    def test_filter_p0_items(self):
        items = [_item(priority="P0"), _item(priority="P2")]
        result = filter_items(items, priority="P0")
        assert len(result) == 1

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
        # "security" migrates to "feature"; verify the feature color is rendered
        html = render_card_html(_item(category="security"))
        assert "#60a5fa" in html

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
        assert "#60a5fa" in html
        assert "rgba(59,130,246,0.08)" in html

    def test_sprint_badge_outlined_style(self):
        html = render_card_html(_item(sprint_target=3))
        assert "background:none" in html
        assert "border:1px solid #27272a" in html

    def test_priority_badge_has_bg_color(self):
        html = render_card_html(_item(priority="P1"))
        assert "#f87171" in html
        assert "rgba(248,113,113,0.10)" in html

    def test_design_reviewed_badge_shown_when_true(self):
        html = render_card_html(_item(design_reviewed=True))
        assert "design" in html
        assert "#4ade80" in html

    def test_code_reviewed_badge_shown_when_true(self):
        html = render_card_html(_item(code_reviewed=True))
        assert "code" in html
        assert "#4ade80" in html

    def test_review_badges_not_shown_by_default(self):
        html = render_card_html(_item())
        assert "rgba(74,222,128,0.1)" not in html


class TestCommentBadgeHtml:
    def test_red_badge_for_unresolved_flagged(self):
        notes = [
            {"text": "fix this", "flagged": True, "resolved": False},
            {"text": "looks good", "flagged": False, "resolved": False},
        ]
        html = comment_badge_html(notes)
        assert "#f87171" in html  # red
        assert ">1<" in html  # count of unresolved flagged

    def test_blue_badge_when_no_unresolved_flagged(self):
        notes = [
            {"text": "fix this", "flagged": True, "resolved": True},
            {"text": "looks good", "flagged": False, "resolved": False},
        ]
        html = comment_badge_html(notes)
        assert "#3b82f6" in html  # blue
        assert ">2<" in html  # total count

    def test_no_badge_when_no_comments(self):
        assert comment_badge_html([]) == ""

    def test_resolved_flagged_not_counted(self):
        notes = [
            {"text": "old issue", "flagged": True, "resolved": True},
        ]
        html = comment_badge_html(notes)
        assert "#3b82f6" in html  # blue, not red
        assert ">1<" in html


class TestDetectCurrentSprint:
    def test_detects_from_doing_items(self):
        items = [
            _item(id="a", status="doing", sprint_target=3),
            _item(id="b", status="doing", sprint_target=3),
            _item(id="c", status="backlog", sprint_target=4),
        ]
        assert detect_current_sprint(items) == 3

    def test_fallback_to_highest_sprint_when_no_doing(self):
        items = [_item(id="a", status="backlog", sprint_target=2)]
        assert detect_current_sprint(items) == 2

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


class TestGroupItemsBySection:
    def test_unplanned_backlog_items_in_backlog_section(self):
        items = [_item(status="backlog", sprint_target=None)]
        result = group_items_by_section(items, current_sprint=15)
        assert len(result["backlog"]) == 1
        assert result["vnext"] == []
        assert result["vfuture"] == []

    def test_vnext_items(self):
        items = [_item(status="backlog", sprint_target=16)]
        result = group_items_by_section(items, current_sprint=15)
        assert len(result["vnext"]) == 1
        assert result["backlog"] == []

    def test_vfuture_items(self):
        items = [_item(status="backlog", sprint_target=17)]
        result = group_items_by_section(items, current_sprint=15)
        assert len(result["vfuture"]) == 1

    def test_sprint_18_also_vfuture(self):
        items = [_item(status="backlog", sprint_target=18)]
        result = group_items_by_section(items, current_sprint=15)
        assert len(result["vfuture"]) == 1

    def test_doing_and_done_excluded(self):
        items = [
            _item(status="doing", sprint_target=15),
            _item(status="done", sprint_target=15),
            _item(status="backlog", sprint_target=None),
        ]
        result = group_items_by_section(items, current_sprint=15)
        assert len(result["backlog"]) == 1
        assert result["vnext"] == []
        assert result["vfuture"] == []

    def test_no_current_sprint_all_in_backlog(self):
        items = [
            _item(status="backlog", sprint_target=None),
            _item(status="backlog", sprint_target=16),
        ]
        result = group_items_by_section(items, current_sprint=None)
        assert len(result["backlog"]) == 2
        assert result["vnext"] == []
        assert result["vfuture"] == []

    def test_sorted_by_priority_then_updated(self):
        items = [
            _item(id="low", status="backlog", priority="P3"),
            _item(id="high", status="backlog", priority="P1"),
            _item(id="med", status="backlog", priority="P2"),
        ]
        result = group_items_by_section(items, current_sprint=15)
        ids = [i.id for i in result["backlog"]]
        assert ids == ["high", "med", "low"]


class TestRenderBacklogCardHtml:
    def test_shows_title(self):
        item = _item(title="My Task")
        html = render_backlog_card_html(item)
        assert "My Task" in html

    def test_shows_category_pill(self):
        item = _item(category="bug")
        html = render_backlog_card_html(item)
        assert "bug" in html

    def test_shows_tags(self):
        item = _item(tags=["ui", "planning"])
        html = render_backlog_card_html(item)
        assert "ui" in html
        assert "planning" in html

    def test_shows_priority_bar_for_p0(self):
        item = _item(priority="P0")
        html = render_backlog_card_html(item)
        assert "#ef4444" in html  # P0 red

    def test_no_priority_bar_for_p3(self):
        item = _item(priority="P3")
        html = render_backlog_card_html(item)
        assert "transparent" in html  # no colored bar for P3

    def test_shows_complexity_badge(self):
        item = _item(complexity="M")
        html = render_backlog_card_html(item)
        assert "M" in html

    def test_shows_comment_badge(self):
        item = _item(comments=[{"text": "x", "flagged": True, "resolved": False}])
        html = render_backlog_card_html(item)
        assert "1" in html  # badge count


class TestRenderCommentHtml:
    def test_basic_comment(self):
        comment = {
            "text": "Hello world",
            "flagged": False,
            "resolved": False,
            "created": "2026-03-22",
            "author": "user",
        }
        html = render_comment_html(comment)
        assert "Hello world" in html
        assert "2026-03-22" in html

    def test_flagged_comment_highlighted(self):
        comment = {"text": "Check this", "flagged": True, "resolved": False, "created": "2026-03-22", "author": "agent"}
        html = render_comment_html(comment)
        assert "#f87171" in html  # red border for flagged

    def test_resolved_comment_faded(self):
        comment = {"text": "Done", "flagged": True, "resolved": True, "created": "2026-03-22", "author": "agent"}
        html = render_comment_html(comment)
        assert "opacity" in html
        assert "line-through" in html

    def test_user_vs_agent_icons(self):
        user_html = render_comment_html({"text": "x", "author": "user", "flagged": False, "resolved": False})
        agent_html = render_comment_html({"text": "x", "author": "agent", "flagged": False, "resolved": False})
        assert user_html != agent_html


class TestCommentThreadHtml:
    def test_empty_thread(self):
        assert comment_thread_html([]) == ""

    def test_multiple_comments(self):
        comments = [
            {"text": "First", "flagged": False, "resolved": False, "author": "user"},
            {"text": "Second", "flagged": True, "resolved": False, "author": "agent"},
        ]
        html = comment_thread_html(comments)
        assert "First" in html
        assert "Second" in html


class TestArchiveDone:
    def test_recent_done_items_visible(self):
        item = _item(status="done", updated=date.today())
        assert is_recently_done(item, days=7)

    def test_old_done_items_hidden(self):
        item = _item(status="done", updated=date.today() - timedelta(days=10))
        assert not is_recently_done(item, days=7)

    def test_non_done_items_always_visible(self):
        item = _item(status="doing", updated=date.today() - timedelta(days=30))
        assert is_recently_done(item, days=7)
