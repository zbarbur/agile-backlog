# Sprint 2: Streamlit Kanban Board UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a visual Kanban board web UI with rich styled cards, filter chips, move-via-dropdown, and inline detail expanders.

**Architecture:** Single Streamlit app (`src/app.py`) that reads from the existing `yaml_store` layer. Pure functions extracted for testability (`category_style`, `filter_items`, `render_card_html`). The `serve` CLI command is updated to launch Streamlit.

**Tech Stack:** Streamlit, Python 3.11+, existing `src/models.py` + `src/yaml_store.py`

**Spec:** `docs/superpowers/specs/2026-03-21-sprint2-kanban-ui-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/app.py` | Streamlit Kanban board application |
| `src/cli.py` | Modify: update `serve` command to launch Streamlit |
| `tests/test_app.py` | Tests for pure functions: category_style, filter_items, render_card_html |

---

## Task 1: Pure Functions + Tests

**Files:**
- Create: `src/app.py` (pure functions only, no Streamlit UI yet)
- Create: `tests/test_app.py`

### Step 1: Write failing tests

- [ ] **Write tests**

```python
# tests/test_app.py
from datetime import date

from src.app import category_style, filter_items, render_card_html
from src.models import BacklogItem


def _item(**overrides) -> BacklogItem:
    defaults = dict(id="test", title="Test", priority="P2", category="feature")
    defaults.update(overrides)
    return BacklogItem(**defaults)


class TestCategoryStyle:
    def test_known_category_feature(self):
        emoji, color, bg = category_style("feature")
        assert emoji == "✨"
        assert "#60a5fa" in color

    def test_known_category_bug(self):
        emoji, color, bg = category_style("bug")
        assert emoji == "🐛"

    def test_known_category_security(self):
        emoji, color, bg = category_style("security")
        assert emoji == "🔒"

    def test_known_category_tech_debt(self):
        emoji, color, bg = category_style("tech-debt")
        assert emoji == "🔧"

    def test_known_category_docs(self):
        emoji, color, bg = category_style("docs")
        assert emoji == "📚"

    def test_known_category_infra(self):
        emoji, color, bg = category_style("infra")
        assert emoji == "🏗️"

    def test_unknown_category_fallback(self):
        emoji, color, bg = category_style("random-thing")
        assert emoji == "📋"
        assert "#9ca3af" in color


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


class TestRenderCardHtml:
    def test_contains_title(self):
        html = render_card_html(_item(title="Fix auth leak"))
        assert "Fix auth leak" in html

    def test_contains_category_emoji(self):
        html = render_card_html(_item(category="bug"))
        assert "🐛" in html

    def test_contains_priority_badge(self):
        html = render_card_html(_item(priority="P1"))
        assert "P1" in html

    def test_contains_sprint_indicator(self):
        html = render_card_html(_item(sprint_target=2))
        assert "S2" in html

    def test_unplanned_sprint(self):
        html = render_card_html(_item(sprint_target=None))
        assert "Unplanned" in html

    def test_contains_category_color(self):
        html = render_card_html(_item(category="security"))
        assert "#a78bfa" in html or "a78bfa" in html
```

- [ ] **Run tests — expect FAIL**

```bash
.venv/bin/python -m pytest tests/test_app.py -v
```

Expected: `ImportError: cannot import name 'category_style' from 'src.app'`

### Step 2: Implement pure functions

- [ ] **Write implementation**

```python
# src/app.py
"""Streamlit Kanban board for agile-backlog."""

from src.models import BacklogItem

CATEGORY_STYLES: dict[str, tuple[str, str, str]] = {
    # category: (emoji, text_color, bg_color)
    "bug": ("🐛", "#f472b6", "#3a1a2a"),
    "feature": ("✨", "#60a5fa", "#1a2a3a"),
    "tech-debt": ("🔧", "#fbbf24", "#2a2a1a"),
    "docs": ("📚", "#34d399", "#1a3a2a"),
    "security": ("🔒", "#a78bfa", "#2a1a3a"),
    "infra": ("🏗️", "#22d3ee", "#1a2a2a"),
}

PRIORITY_COLORS: dict[str, str] = {
    "P1": "#ef4444",
    "P2": "#3b82f6",
    "P3": "#f59e0b",
}


def category_style(category: str) -> tuple[str, str, str]:
    """Return (emoji, text_color, bg_color) for a category."""
    return CATEGORY_STYLES.get(category, ("📋", "#9ca3af", "#2a2a2a"))


def filter_items(
    items: list[BacklogItem],
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    sprint: int | None = None,
    search: str = "",
) -> list[BacklogItem]:
    """Apply filters to items. Multiple filters combine with AND logic."""
    result = items
    if status:
        result = [i for i in result if i.status == status]
    if priority:
        result = [i for i in result if i.priority == priority]
    if category:
        result = [i for i in result if i.category == category]
    if sprint is not None:
        result = [i for i in result if i.sprint_target == sprint]
    if search:
        q = search.lower()
        result = [
            i for i in result
            if q in i.title.lower()
            or q in i.description.lower()
            or any(q in t.lower() for t in i.tags)
        ]
    return result


def render_card_html(item: BacklogItem) -> str:
    """Generate the HTML string for a styled card."""
    emoji, cat_color, cat_bg = category_style(item.category)
    pri_color = PRIORITY_COLORS.get(item.priority, "#888")
    sprint_text = f"S{item.sprint_target}" if item.sprint_target is not None else "Unplanned"

    return f"""<div style="border-radius:8px;overflow:hidden;margin-bottom:8px;border:1px solid #333;">
  <div style="background:{cat_bg};padding:4px 10px;display:flex;align-items:center;gap:6px;">
    <span>{emoji}</span>
    <span style="font-size:12px;color:{cat_color};font-weight:600;text-transform:uppercase;">{item.category}</span>
    <span style="margin-left:auto;font-size:11px;background:rgba(0,0,0,0.3);color:{pri_color};padding:2px 8px;border-radius:4px;font-weight:700;">{item.priority}</span>
  </div>
  <div style="padding:8px 10px;">
    <div style="font-size:14px;font-weight:500;">{item.title}</div>
    <div style="font-size:11px;color:#888;margin-top:2px;">{sprint_text}</div>
  </div>
</div>"""
```

- [ ] **Run tests — expect PASS**

```bash
.venv/bin/python -m pytest tests/test_app.py -v
```

- [ ] **Lint**

```bash
.venv/bin/python -m ruff check src/app.py tests/test_app.py && .venv/bin/python -m ruff format src/app.py tests/test_app.py
```

- [ ] **Commit**

```bash
git add src/app.py tests/test_app.py
git commit -m "feat: add pure functions for Kanban UI (category_style, filter_items, render_card_html)"
```

---

## Task 2: Streamlit Board UI

**Files:**
- Modify: `src/app.py` (add Streamlit UI below pure functions)

### Step 1: Add Streamlit board rendering

- [ ] **Add the board UI to app.py**

Append the following to the end of `src/app.py`:

```python
def main():
    """Render the Kanban board."""
    import streamlit as st

    from src.yaml_store import load_all, save_item

    st.set_page_config(page_title="agile-backlog", layout="wide")

    # --- Load data ---
    all_items = load_all()

    # --- Filter bar ---
    st.markdown("## agile-backlog")

    filter_cols = st.columns([1, 1, 1, 2])

    with filter_cols[0]:
        priority_filter = st.selectbox(
            "Priority", [None, "P1", "P2", "P3"], format_func=lambda x: "All priorities" if x is None else x
        )
    with filter_cols[1]:
        categories = sorted({i.category for i in all_items})
        category_filter = st.selectbox(
            "Category", [None, *categories], format_func=lambda x: "All categories" if x is None else x
        )
    with filter_cols[2]:
        sprints = sorted({i.sprint_target for i in all_items if i.sprint_target is not None})
        sprint_filter = st.selectbox(
            "Sprint", [None, *sprints], format_func=lambda x: "All sprints" if x is None else f"Sprint {x}"
        )
    with filter_cols[3]:
        search = st.text_input("Search", placeholder="Filter by title, description, tags...")

    filtered = filter_items(all_items, priority=priority_filter, category=category_filter, sprint=sprint_filter, search=search)

    # --- Group by status ---
    columns_map = {"backlog": [], "doing": [], "done": []}
    for item in filtered:
        columns_map[item.status].append(item)

    # --- Render columns ---
    col_backlog, col_doing, col_done = st.columns(3)

    statuses = ["backlog", "doing", "done"]
    column_widgets = [col_backlog, col_doing, col_done]
    labels = ["BACKLOG", "DOING", "DONE"]

    for col_widget, status, label in zip(column_widgets, statuses, labels):
        items_in_col = columns_map[status]
        with col_widget:
            st.markdown(f"### {label} ({len(items_in_col)})")
            st.divider()

            if not items_in_col:
                st.caption("No items match filters." if all_items else "No items yet — use `agile-backlog add` to create one.")
                continue

            for item in items_in_col:
                # Render styled card
                st.markdown(render_card_html(item), unsafe_allow_html=True)

                # Move selectbox
                other_statuses = [s for s in statuses if s != status]
                move_key = f"move_{item.id}"
                new_status = st.selectbox(
                    "Move to",
                    [status, *other_statuses],
                    key=move_key,
                    label_visibility="collapsed",
                    format_func=lambda s, current=status: f"Move to → {s}" if s != current else f"📍 {current}",
                )
                if new_status != status:
                    item.status = new_status
                    save_item(item)
                    st.rerun()

                # Detail expander
                with st.expander(f"Details: {item.title}"):
                    if item.description:
                        st.markdown(item.description)
                    if item.acceptance_criteria:
                        st.markdown("**Acceptance Criteria:**")
                        for ac in item.acceptance_criteria:
                            st.markdown(f"- {ac}")
                    if item.notes:
                        st.markdown(f"**Notes:** {item.notes}")
                    if item.tags:
                        st.markdown(f"**Tags:** {', '.join(item.tags)}")
                    if item.depends_on:
                        st.markdown(f"**Depends on:** {', '.join(item.depends_on)}")
                    detail_cols = st.columns(3)
                    with detail_cols[0]:
                        st.caption(f"Sprint: {item.sprint_target or 'Unplanned'}")
                    with detail_cols[1]:
                        st.caption(f"Created: {item.created}")
                    with detail_cols[2]:
                        st.caption(f"Updated: {item.updated}")


if __name__ == "__main__":
    main()
```

- [ ] **Run existing tests — still pass**

```bash
.venv/bin/python -m pytest tests/ -v
```

- [ ] **Lint and format**

```bash
.venv/bin/python -m ruff check src/app.py && .venv/bin/python -m ruff format src/app.py
```

- [ ] **Manual smoke test**

```bash
.venv/bin/python -m streamlit run src/app.py
```

Verify in browser:
- Three columns render with correct headers and counts
- Cards show category header with emoji, priority badge, title, sprint
- Filter dropdowns work (priority, category, sprint, search)
- Move selectbox changes item status and board refreshes
- Expander shows full item details
- Empty board shows helpful message

- [ ] **Commit**

```bash
git add src/app.py
git commit -m "feat: add Streamlit Kanban board with cards, filters, and move"
```

---

## Task 3: Update CLI serve command

**Files:**
- Modify: `src/cli.py:119-122`
- Modify: `tests/test_cli.py` (update serve test)

### Step 1: Update the serve test

- [ ] **Update test**

In `tests/test_cli.py`, replace `TestServe`:

```python
class TestServe:
    def test_serve_launches_streamlit(self, runner: CliRunner, monkeypatch):
        """Verify serve attempts to launch streamlit (we mock subprocess.run)."""
        import subprocess as sp

        calls = []
        monkeypatch.setattr(sp, "run", lambda cmd, **kw: calls.append(cmd))
        result = runner.invoke(main, ["serve"])
        assert result.exit_code == 0
        assert len(calls) == 1
        assert "streamlit" in str(calls[0])
        assert "app.py" in str(calls[0])
```

- [ ] **Run test — expect FAIL**

```bash
.venv/bin/python -m pytest tests/test_cli.py::TestServe -v
```

Expected: FAIL (serve still prints placeholder text)

### Step 2: Update serve command

- [ ] **Update cli.py**

Replace the `serve` function in `src/cli.py`:

```python
@main.command()
def serve():
    """Open the Kanban board in the browser."""
    import subprocess
    import sys
    from pathlib import Path

    app_path = Path(__file__).parent / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
```

- [ ] **Run tests — expect PASS**

```bash
.venv/bin/python -m pytest tests/ -v
```

- [ ] **Lint**

```bash
.venv/bin/python -m ruff check src/cli.py tests/test_cli.py && .venv/bin/python -m ruff format src/cli.py tests/test_cli.py
```

- [ ] **Commit**

```bash
git add src/cli.py tests/test_cli.py
git commit -m "feat: update serve command to launch Streamlit board"
```

---

## Task 4: Final Verification + Sprint Cleanup

**Files:**
- Modify: `TODO.md`
- Modify: `docs/process/KANBAN.md`
- Modify: `backlog/streamlit-kanban-board.yaml` (via CLI)

- [ ] **Run full CI**

```bash
.venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check . && .venv/bin/python -m pytest tests/ -v
```

- [ ] **Full smoke test in browser**

```bash
.venv/bin/agile-backlog serve
```

Walk through: view board, filter by priority, filter by category, move an item, expand details, search.

- [ ] **Update backlog items**

```bash
.venv/bin/agile-backlog move streamlit-kanban-board --status done
```

- [ ] **Update TODO.md and KANBAN.md**

- [ ] **Commit and push**

```bash
git add TODO.md docs/process/KANBAN.md backlog/
git commit -m "chore: complete Sprint 2 — Kanban board UI done"
git push
```
