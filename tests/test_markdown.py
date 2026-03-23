"""Tests for markdown rendering support in the web UI."""

import inspect

from agile_backlog.models import BacklogItem


class TestMarkdownFieldSupport:
    """Verify that _render_editable_textarea accepts use_markdown and fields store markdown."""

    def test_render_editable_textarea_has_use_markdown_param(self):
        from agile_backlog.components import _render_editable_textarea

        sig = inspect.signature(_render_editable_textarea)
        assert "use_markdown" in sig.parameters
        param = sig.parameters["use_markdown"]
        assert param.default is False

    def test_description_with_markdown_characters(self):
        item = BacklogItem(
            id="md-test",
            title="Markdown test",
            priority="P2",
            category="feature",
            description=(
                "# Heading\n\n- bullet one\n- bullet two\n\n**bold** and *italic*\n\n```python\nprint('hello')\n```"
            ),
        )
        assert "# Heading" in item.description
        assert "**bold**" in item.description
        assert "```python" in item.description

    def test_goal_with_markdown_characters(self):
        item = BacklogItem(
            id="md-goal",
            title="Goal markdown",
            priority="P2",
            category="feature",
            goal="Enable **markdown** rendering for `description` fields",
        )
        assert "**markdown**" in item.goal
        assert "`description`" in item.goal

    def test_notes_with_markdown_characters(self):
        item = BacklogItem(
            id="md-notes",
            title="Notes markdown",
            priority="P2",
            category="feature",
            notes="> This is a blockquote\n\n1. First\n2. Second",
        )
        assert "> This is a blockquote" in item.notes
        assert "1. First" in item.notes

    def test_markdown_roundtrip_through_yaml_dict(self):
        md_desc = "## Section\n\n- item 1\n- item 2\n\n```\ncode block\n```"
        item = BacklogItem(
            id="rt-test",
            title="Roundtrip",
            priority="P2",
            category="feature",
            description=md_desc,
            goal="**bold goal**",
            notes="*italic notes*",
        )
        d = item.to_yaml_dict()
        assert d["description"] == md_desc
        assert d["goal"] == "**bold goal**"
        assert d["notes"] == "*italic notes*"

    def test_description_empty_string_default(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="feature")
        assert item.description == ""

    def test_goal_empty_string_default(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="feature")
        assert item.goal == ""

    def test_notes_empty_string_default(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="feature")
        assert item.notes == ""


class TestMarkdownCssInStyles:
    """Verify that dark-theme markdown CSS is present in GLOBAL_CSS."""

    def test_global_css_contains_markdown_styles(self):
        from pathlib import Path

        styles_path = Path(__file__).parent.parent / "src" / "agile_backlog" / "styles.py"
        css_content = styles_path.read_text()
        assert ".nicegui-markdown" in css_content
        assert ".nicegui-markdown h1" in css_content
        assert ".nicegui-markdown pre" in css_content
        assert ".nicegui-markdown code" in css_content
        assert ".nicegui-markdown blockquote" in css_content
        assert ".nicegui-markdown ul" in css_content
