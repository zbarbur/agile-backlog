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
    relative_time,
    render_card_html,
    render_comment_html,
    safe_html,
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
    def test_shows_title(self):
        html = render_card_html(_item(title="My Task"))
        assert "My Task" in html

    def test_shows_category_pill(self):
        html = render_card_html(_item(category="bug"))
        assert "bug" in html

    def test_shows_priority_pill(self):
        html = render_card_html(_item(priority="P2"))
        assert "P2" in html

    def test_p0_has_left_border(self):
        html = render_card_html(_item(priority="P0"))
        assert "border-left:2px solid #ef4444" in html

    def test_p1_has_left_border(self):
        html = render_card_html(_item(priority="P1"))
        assert "border-left:2px solid #f87171" in html

    def test_p2_shows_yellow_border(self):
        html = render_card_html(_item(priority="P2"))
        assert "border-left:2px solid #fbbf24" in html

    def test_p3_shows_gray_border(self):
        html = render_card_html(_item(priority="P3"))
        assert "border-left:2px solid #6b7280" in html

    def test_p4_shows_dark_gray_border(self):
        html = render_card_html(_item(priority="P4"))
        assert "border-left:2px solid #4b5563" in html

    def test_shows_tags(self):
        html = render_card_html(_item(tags=["ui", "planning"]))
        assert "ui" in html
        assert "planning" in html

    def test_shows_complexity_badge(self):
        html = render_card_html(_item(complexity="M"))
        assert "M" in html

    def test_shows_comment_badge(self):
        html = render_card_html(_item(comments=[{"text": "x", "flagged": True, "resolved": False}]))
        assert "1" in html

    def test_shows_relative_timestamp(self):
        from datetime import date

        html = render_card_html(_item(updated=date.today()))
        assert "today" in html

    def test_p3_muted_title_color(self):
        html = render_card_html(_item(priority="P3"))
        assert "#71717a" in html

    def test_no_phase_badge_on_card(self):
        html = render_card_html(_item(phase="build"))
        assert "build" not in html

    def test_no_review_badge_on_card(self):
        html = render_card_html(_item(design_reviewed=True))
        assert "design" not in html


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
    def test_config_takes_priority(self):
        import unittest.mock

        items = [_item(status="doing", sprint_target=13)]
        with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=15):
            result = detect_current_sprint(items)
        assert result == 15

    def test_config_none_falls_back_to_inference(self):
        import unittest.mock

        items = [_item(status="doing", sprint_target=13)]
        with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=None):
            result = detect_current_sprint(items)
        assert result == 13

    def test_detects_from_doing_items(self):
        import unittest.mock

        items = [
            _item(id="a", status="doing", sprint_target=3),
            _item(id="b", status="doing", sprint_target=3),
            _item(id="c", status="backlog", sprint_target=4),
        ]
        with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=None):
            assert detect_current_sprint(items) == 3

    def test_fallback_to_none_when_no_doing(self):
        import unittest.mock

        items = [_item(id="a", status="backlog", sprint_target=2)]
        with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=None):
            assert detect_current_sprint(items) is None

    def test_returns_none_when_doing_has_no_sprint(self):
        import unittest.mock

        items = [_item(id="a", status="doing", sprint_target=None)]
        with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=None):
            assert detect_current_sprint(items) is None

    def test_returns_max_doing_sprint(self):
        import unittest.mock

        items = [
            _item(id="a", status="doing", sprint_target=3),
            _item(id="b", status="doing", sprint_target=3),
            _item(id="c", status="doing", sprint_target=2),
        ]
        with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=None):
            assert detect_current_sprint(items) == 3

    def test_empty_list(self):
        import unittest.mock

        with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=None):
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


class TestRenderCommentHtml:
    def test_user_comment_right_aligned(self):
        comment = {"text": "Hello", "author": "user", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "flex-end" in html

    def test_agent_comment_left_aligned(self):
        comment = {"text": "Hello", "author": "agent", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "flex-start" in html

    def test_user_blue_background(self):
        comment = {"text": "Hello", "author": "user", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "59,130,246" in html

    def test_agent_gray_background(self):
        comment = {"text": "Hello", "author": "agent", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "#18181b" in html

    def test_flagged_has_red_border(self):
        comment = {"text": "Check", "flagged": True, "resolved": False, "author": "user"}
        html = render_comment_html(comment)
        assert "#f87171" in html

    def test_resolved_has_opacity(self):
        comment = {"text": "Done", "flagged": True, "resolved": True, "author": "agent"}
        html = render_comment_html(comment)
        assert "0.35" in html
        assert "line-through" not in html

    def test_shows_text_and_date(self):
        comment = {
            "text": "Hello world",
            "created": "2026-03-22",
            "author": "user",
            "flagged": False,
            "resolved": False,
        }
        html = render_comment_html(comment)
        assert "Hello world" in html
        assert "2026-03-22" in html


class TestCommentThreadHtml:
    def test_empty_thread(self):
        assert comment_thread_html([]) == ""

    def test_multiple_comments(self):
        comments = [
            {"text": "First", "author": "user", "flagged": False, "resolved": False},
            {"text": "Second", "author": "agent", "flagged": False, "resolved": False},
        ]
        html = comment_thread_html(comments)
        assert "First" in html
        assert "Second" in html
        assert "flex-end" in html
        assert "flex-start" in html


class TestRelativeTime:
    def test_today(self):
        assert relative_time(date.today()) == "today"

    def test_yesterday(self):
        assert relative_time(date.today() - timedelta(days=1)) == "1d"

    def test_3_days(self):
        assert relative_time(date.today() - timedelta(days=3)) == "3d"

    def test_1_week(self):
        assert relative_time(date.today() - timedelta(days=7)) == "1w"

    def test_3_weeks(self):
        assert relative_time(date.today() - timedelta(days=21)) == "3w"

    def test_over_4_weeks(self):
        old = date(2026, 2, 15)
        result = relative_time(old)
        assert result == "Feb 15"

    def test_6_days_still_days(self):
        assert relative_time(date.today() - timedelta(days=6)) == "6d"

    def test_28_days_is_4w(self):
        assert relative_time(date.today() - timedelta(days=28)) == "4w"

    def test_29_days_is_month_format(self):
        d = date.today() - timedelta(days=29)
        result = relative_time(d)
        assert len(result) > 2


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


class TestSafeHtml:
    def test_escapes_angle_brackets(self):
        assert safe_html("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"

    def test_escapes_ampersand(self):
        assert safe_html("A & B") == "A &amp; B"

    def test_escapes_quotes(self):
        assert "&quot;" in safe_html('"hello"')

    def test_passthrough_safe_text(self):
        assert safe_html("Hello World") == "Hello World"

    def test_render_card_html_escapes_title(self):
        item = _item(title='<img src=x onerror="alert(1)">')
        html = render_card_html(item)
        assert "<img" not in html
        assert "&lt;img" in html
