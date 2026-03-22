# Backlog View Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 14 UI bugs and elevate the backlog view to Linear/Notion quality — resizable sections, unified two-line cards, click-to-edit side panel, iMessage chat comments, inline filters with sort.

**Architecture:** Start by splitting `app.py` (1872 lines) into focused modules, then build bottom-up — pure functions first (testable without NiceGUI), then tokens, then UI components. The split reduces merge conflicts and makes each task more isolated.

**Tech Stack:** Python 3.11+, NiceGUI (Quasar-based), Pydantic v2, pytest, ruff

**Spec:** `docs/superpowers/specs/2026-03-22-backlog-view-redesign-phase1-polish.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/agile_backlog/pure.py` | Create | All pure functions: render_card_html, comment_html, filter_items, group_items_by_section, detect_current_sprint, relative_time, category_style, comment_badge_html, etc. |
| `src/agile_backlog/styles.py` | Create | GLOBAL_CSS constant, GOOGLE_FONTS_URL, COLUMN_STYLES, LABELS — all CSS/styling constants |
| `src/agile_backlog/components.py` | Create | Reusable NiceGUI UI components: side panel, card renderer, section, filters, comment dialog |
| `src/agile_backlog/app.py` | Modify | Slim orchestrator: `kanban_page()` layout, routing, `run_app()`. Imports from pure, styles, components |
| `src/agile_backlog/tokens.py` | Modify | Lower category/priority background alphas |
| `tests/test_pure.py` | Create | Tests for all pure functions (moved from test_app.py) |
| `tests/test_app.py` | Modify | Remaining UI-level tests (if any), mostly just import path updates |

---

### Task 0: Split app.py into focused modules

**Files:**
- Modify: `src/agile_backlog/app.py` (extract code out)
- Create: `src/agile_backlog/pure.py`
- Create: `src/agile_backlog/styles.py`
- Create: `src/agile_backlog/components.py`
- Create: `tests/test_pure.py`
- Modify: `tests/test_app.py`

This is a pure refactor — no behavior changes. All tests must pass identically after the split.

- [ ] **Step 1: Create pure.py — extract all pure functions**

Move these functions from `app.py` to `src/agile_backlog/pure.py`:
- `category_style()`
- `filter_items()`
- `render_card_html()` (currently two versions — keep both for now, merge in Task 4)
- `render_backlog_card_html()`
- `detect_current_sprint()`
- `_complexity_badge()`
- `comment_badge_html()`
- `group_items_by_section()`
- `render_comment_html()`
- `comment_thread_html()`
- `is_recently_done()`

Add necessary imports at top of `pure.py`:
```python
"""Pure functions for agile-backlog — framework-independent, fully tested."""

from datetime import date, timedelta

from agile_backlog.models import BacklogItem
from agile_backlog.tokens import CATEGORY_STYLES, PRIORITY_COLORS, PRIORITY_ORDER
```

In `app.py`, replace the pure functions section with imports:
```python
from agile_backlog.pure import (
    category_style, comment_badge_html, comment_thread_html,
    detect_current_sprint, filter_items, group_items_by_section,
    is_recently_done, render_backlog_card_html, render_card_html,
    render_comment_html, _complexity_badge,
)
```

- [ ] **Step 2: Create styles.py — extract CSS constants**

Move from `app.py` to `src/agile_backlog/styles.py`:
- `GLOBAL_CSS` string constant
- `GOOGLE_FONTS_URL`
- `COLUMN_STYLES` dict
- `LABELS` dict
- Any other CSS/styling constants

In `app.py`, replace with:
```python
from agile_backlog.styles import GLOBAL_CSS, GOOGLE_FONTS_URL, COLUMN_STYLES, LABELS
```

- [ ] **Step 3: Create components.py — extract UI component functions**

Move from `app.py` to `src/agile_backlog/components.py`:
- `_render_pill()`
- `_show_comment_dialog()`
- `_render_card()`
- `_render_detail_modal_content()`
- `_show_edit_dialog()`
- `_render_detail_panel()`
- `_render_backlog_list()`
- `_render_side_panel_content()`

Add necessary imports. These functions use NiceGUI (`ui.*`) so they need:
```python
"""NiceGUI UI components for agile-backlog."""

from datetime import date
from nicegui import ui

from agile_backlog.models import BacklogItem
from agile_backlog.pure import (
    category_style, comment_badge_html, comment_thread_html,
    detect_current_sprint, filter_items, group_items_by_section,
    is_recently_done, render_backlog_card_html, render_card_html,
    render_comment_html, _complexity_badge,
)
from agile_backlog.tokens import PRIORITY_COLORS, PRIORITY_ORDER
from agile_backlog.yaml_store import save_item
```

In `app.py`, replace with imports from components and keep only `kanban_page()` and `run_app()`.

- [ ] **Step 4: Create tests/test_pure.py — move pure function tests**

Move all pure function test classes from `tests/test_app.py` to `tests/test_pure.py`:
- `TestCategoryStyle`
- `TestFilterItems`
- `TestRenderCardHtml`
- `TestRenderBacklogCardHtml`
- `TestCommentBadgeHtml`
- `TestDetectCurrentSprint`
- `TestGroupItemsBySection`
- `TestRenderCommentHtml`
- `TestCommentThreadHtml`
- `TestArchiveDone`

Update imports in `test_pure.py`:
```python
from agile_backlog.pure import (
    category_style, comment_badge_html, comment_thread_html,
    detect_current_sprint, filter_items, group_items_by_section,
    is_recently_done, render_backlog_card_html, render_card_html,
    render_comment_html,
)
```

Keep `tests/test_app.py` for any remaining integration tests (may be empty after move).

- [ ] **Step 5: Run all tests — must pass identically**

Run: `.venv/bin/pytest tests/ -v`
Expected: Same number of tests passing as before (153).

- [ ] **Step 6: Run lint**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check .`

Fix any import ordering or unused import issues.

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/pure.py src/agile_backlog/styles.py src/agile_backlog/components.py src/agile_backlog/app.py tests/test_pure.py tests/test_app.py
git commit -m "refactor: split app.py into pure.py, styles.py, components.py"
```

---

### Task 1: Update tokens.py — lower background alphas

**Files:**
- Modify: `src/agile_backlog/tokens.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Update CATEGORY_STYLES alphas**

In `src/agile_backlog/tokens.py`, replace CATEGORY_STYLES:

```python
CATEGORY_STYLES: dict[str, tuple[str, str]] = {
    "bug": ("#f472b6", "rgba(244,114,182,0.08)"),
    "feature": ("#60a5fa", "rgba(59,130,246,0.08)"),
    "docs": ("#34d399", "rgba(52,211,153,0.08)"),
    "chore": ("#a78bfa", "rgba(167,139,250,0.08)"),
}
```

- [ ] **Step 2: Update PRIORITY_COLORS alphas**

Replace PRIORITY_COLORS:

```python
PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "P0": ("#ef4444", "rgba(239,68,68,0.10)"),
    "P1": ("#f87171", "rgba(248,113,113,0.10)"),
    "P2": ("#fbbf24", "rgba(251,191,36,0.10)"),
    "P3": ("#6b7280", "rgba(107,114,128,0.08)"),
    "P4": ("#4b5563", "rgba(75,85,99,0.08)"),
}
```

- [ ] **Step 3: Update test assertions that check exact bg colors**

In `tests/test_app.py`, update `test_badge_uses_design_system_colors` — it asserts `rgba(59,130,246,0.15)` for feature. Change to `rgba(59,130,246,0.08)`.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/tokens.py tests/test_app.py
git commit -m "style: lower category/priority background alphas for subtlety"
```

---

### Task 2: Add relative_time pure function

**Files:**
- Modify: `src/agile_backlog/pure.py` (add function)
- Test: `tests/test_pure.py`

- [ ] **Step 1: Write failing tests**

In `tests/test_pure.py`, add import for `relative_time` and `TestRelativeTime`:

```python
from datetime import date, timedelta

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
        assert len(result) > 2  # "Mon DD" format
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `.venv/bin/pytest tests/test_app.py::TestRelativeTime -v`

- [ ] **Step 3: Implement relative_time**

In `src/agile_backlog/pure.py`, add after `is_recently_done`:

```python
def relative_time(dt: date) -> str:
    """Format a date as a relative timestamp for card display."""
    days = (date.today() - dt).days
    if days <= 0:
        return "today"
    if days <= 6:
        return f"{days}d"
    weeks = days // 7
    if weeks <= 4:
        return f"{weeks}w"
    return dt.strftime("%b %-d")
```

- [ ] **Step 4: Add to imports in test file**

Update the import line in `tests/test_pure.py` to include `relative_time`.

- [ ] **Step 5: Run tests — expect PASS**

Run: `.venv/bin/pytest tests/test_app.py::TestRelativeTime -v`

- [ ] **Step 6: Run full suite**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: add relative_time pure function for card timestamps"
```

---

### Task 3: Fix detect_current_sprint — config-first

**Files:**
- Modify: `src/agile_backlog/pure.py` (update `detect_current_sprint`)
- Test: `tests/test_pure.py`

- [ ] **Step 1: Write failing test**

In `tests/test_pure.py`, add to `TestDetectCurrentSprint`:

```python
def test_config_takes_priority(self):
    """Config sprint overrides inference from items."""
    items = [_item(status="doing", sprint_target=13)]
    with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=15):
        result = detect_current_sprint(items)
    assert result == 15

def test_config_none_falls_back_to_inference(self):
    items = [_item(status="doing", sprint_target=13)]
    with unittest.mock.patch("agile_backlog.pure.get_current_sprint", return_value=None):
        result = detect_current_sprint(items)
    assert result == 13
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `.venv/bin/pytest tests/test_app.py::TestDetectCurrentSprint::test_config_takes_priority -v`

- [ ] **Step 3: Update detect_current_sprint**

In `src/agile_backlog/pure.py`, find `detect_current_sprint` and update:

```python
def detect_current_sprint(items: list[BacklogItem]) -> int | None:
    """Return the current sprint number. Checks config first, infers from doing items second."""
    from agile_backlog.config import get_current_sprint

    configured = get_current_sprint()
    if configured is not None:
        return configured
    # Fall back to inference from doing items
    sprints = [i.sprint_target for i in items if i.status == "doing" and i.sprint_target]
    return max(sprints) if sprints else None
```

- [ ] **Step 4: Remove redundant config checks at call sites**

Search `app.py` for patterns like `get_current_sprint() or detect_current_sprint(...)` and replace with just `detect_current_sprint(items)`. Key locations:
- `_render_backlog_list` (around line ~1434)
- Any other call site

- [ ] **Step 5: Run tests — expect PASS**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 6: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "fix: detect_current_sprint checks config first, fixes sprint 13 display"
```

---

### Task 4: Unified render_card_html — two-line card design

**Files:**
- Modify: `src/agile_backlog/pure.py` (merge and replace both card functions)
- Test: `tests/test_pure.py`

- [ ] **Step 1: Write failing tests for new card design**

In `tests/test_pure.py`, replace `TestRenderCardHtml` and `TestRenderBacklogCardHtml` with a unified `TestRenderCardHtml`:

```python
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

    def test_p2_no_left_border(self):
        html = render_card_html(_item(priority="P2"))
        assert "border-left:2px solid transparent" in html

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
        html = render_card_html(_item(updated=date.today()))
        assert "today" in html

    def test_p3_muted_title_color(self):
        html = render_card_html(_item(priority="P3"))
        assert "#71717a" in html  # muted text

    def test_no_phase_badge_on_card(self):
        html = render_card_html(_item(phase="build"))
        assert "build" not in html  # phase badges removed from cards

    def test_no_review_badge_on_card(self):
        html = render_card_html(_item(design_reviewed=True))
        assert "design" not in html  # review badges removed from cards
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `.venv/bin/pytest tests/test_app.py::TestRenderCardHtml -v`

- [ ] **Step 3: Replace both card functions with unified render_card_html**

In `src/agile_backlog/pure.py`, delete both `render_card_html` (old board version) and `render_backlog_card_html`, replace with:

```python
def render_card_html(item: BacklogItem) -> str:
    """Render a unified two-line card row as HTML. Used by both board and backlog views."""
    pri_color = PRIORITY_COLORS.get(item.priority, ("#6b7280", "rgba(107,114,128,0.08)"))
    bar_color = pri_color[0] if item.priority in ("P0", "P1") else "transparent"
    cat_style = category_style(item.category)
    title_color = "#71717a" if item.priority in ("P3", "P4") else "#e4e4e7"

    # Badges: comment, category, priority
    badge = comment_badge_html(item.comments)
    cat_pill = (
        f'<span style="font-size:9px;color:{cat_style[0]};background:{cat_style[1]};'
        f'padding:1px 6px;border-radius:3px;">{item.category}</span>'
    )
    pri_pill = (
        f'<span style="font-size:9px;color:{pri_color[0]};background:{pri_color[1]};'
        f'padding:1px 6px;border-radius:3px;font-weight:600;">{item.priority}</span>'
    )
    complexity = _complexity_badge(item.complexity) if item.complexity else ""

    # Tags
    tag_chips = "".join(
        f'<span style="font-size:9px;color:#52525b;background:rgba(82,82,91,0.10);'
        f'padding:1px 6px;border-radius:3px;margin-right:4px;">{t}</span>'
        for t in item.tags
    )

    # Timestamp
    ts = relative_time(item.updated)

    return (
        f'<div style="border-left:2px solid {bar_color};padding:6px 10px;cursor:pointer;'
        f'border-radius:5px;margin:1px 0;" class="mc-card-row">'
        # Row 1: title + badges
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<span style="color:{title_color};font-size:12.5px;font-weight:500;'
        f'flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{item.title}</span>'
        f'<span style="display:flex;gap:5px;align-items:center;flex-shrink:0;">'
        f"{badge}{complexity}{cat_pill}{pri_pill}</span>"
        f"</div>"
        # Row 2: tags + timestamp
        f'<div style="display:flex;align-items:center;gap:5px;margin-top:3px;">'
        f"{tag_chips}"
        f'<span style="font-size:9px;color:#27272a;margin-left:auto;">{ts}</span>'
        f"</div>"
        f"</div>"
    )
```

- [ ] **Step 4: Update all callers of render_backlog_card_html to use render_card_html**

Search `components.py` for `render_backlog_card_html` and replace with `render_card_html`. Update imports.

- [ ] **Step 5: Run tests — expect PASS**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 6: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: unified two-line card design for board and backlog views"
```

---

### Task 5: Update render_comment_html — iMessage chat style

**Files:**
- Modify: `src/agile_backlog/pure.py`
- Test: `tests/test_pure.py`

- [ ] **Step 1: Write failing tests for chat-style comments**

In `tests/test_pure.py`, replace `TestRenderCommentHtml` and `TestCommentThreadHtml`:

```python
class TestRenderCommentHtml:
    def test_user_comment_right_aligned(self):
        comment = {"text": "Hello", "author": "user", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "flex-end" in html  # right-aligned

    def test_agent_comment_left_aligned(self):
        comment = {"text": "Hello", "author": "agent", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "flex-start" in html  # left-aligned

    def test_user_blue_background(self):
        comment = {"text": "Hello", "author": "user", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "59,130,246" in html  # blue tint

    def test_agent_gray_background(self):
        comment = {"text": "Hello", "author": "agent", "flagged": False, "resolved": False}
        html = render_comment_html(comment)
        assert "#18181b" in html  # dark gray

    def test_flagged_has_red_border(self):
        comment = {"text": "Check", "flagged": True, "resolved": False, "author": "user"}
        html = render_comment_html(comment)
        assert "#f87171" in html

    def test_resolved_has_opacity(self):
        comment = {"text": "Done", "flagged": True, "resolved": True, "author": "agent"}
        html = render_comment_html(comment)
        assert "0.35" in html
        assert "line-through" not in html  # no strikethrough

    def test_shows_text_and_date(self):
        comment = {"text": "Hello world", "created": "2026-03-22", "author": "user", "flagged": False, "resolved": False}
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
        assert "flex-end" in html  # user right
        assert "flex-start" in html  # agent left
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `.venv/bin/pytest tests/test_app.py::TestRenderCommentHtml -v`

- [ ] **Step 3: Replace render_comment_html with chat-style version**

```python
def render_comment_html(comment: dict) -> str:
    """Render a single comment as an iMessage-style chat bubble."""
    author = comment.get("author", "agent")
    text = comment.get("text", "")
    created = comment.get("created", "")
    flagged = comment.get("flagged", False)
    resolved = comment.get("resolved", False)

    is_user = author == "user"
    align = "flex-end" if is_user else "flex-start"
    icon = "👤" if is_user else "🤖"
    bg = "rgba(59,130,246,0.12)" if is_user else "#18181b"
    flat_corner = "border-bottom-right-radius:4px;" if is_user else "border-bottom-left-radius:4px;"
    meta_align = "text-align:right;" if is_user else "text-align:left;"
    border = f"border-left:2px solid #f87171;" if flagged and not resolved else ""
    opacity = "opacity:0.35;" if resolved else ""

    return (
        f'<div style="display:flex;flex-direction:column;max-width:82%;align-self:{align};{opacity}">'
        f'<div style="font-size:9px;color:#3f3f46;margin-bottom:2px;padding:0 4px;{meta_align}">'
        f'{icon} {author} · {created}{"  · 🚩" if flagged and not resolved else ""}</div>'
        f'<div style="padding:8px 12px;border-radius:12px;{flat_corner}'
        f'background:{bg};color:#d4d4d8;font-size:12px;line-height:1.5;{border}">'
        f'{text}</div>'
        f'</div>'
    )
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: iMessage-style chat comments — user right, agent left"
```

---

### Task 6: Update global CSS — card hover, selection, move buttons, side panel

**Files:**
- Modify: `src/agile_backlog/styles.py` (GLOBAL_CSS constant)

- [ ] **Step 1: Update GLOBAL_CSS**

Find the `GLOBAL_CSS` string constant in `styles.py` and add/replace these CSS rules:

```css
/* Unified card row */
.mc-card-row { transition: background 0.1s; }
.mc-card-row:hover { background: rgba(255,255,255,0.03) !important; }
.mc-card-row.mc-selected { background: rgba(59,130,246,0.06) !important; border-left-color: #3b82f6 !important; }

/* Hover move buttons */
.mc-move-buttons { display:none; position:absolute; bottom:4px; right:8px; gap:3px; align-items:center; }
.mc-card-row:hover .mc-move-buttons { display:flex; }
.mc-card-row.mc-selected .mc-move-buttons { display:none; }

/* Side panel */
.mc-side-panel {
    background: #0c0c0e;
    border-left: 1px solid #1e1e23;
    overflow-y: auto;
}
.mc-side-panel::-webkit-scrollbar { width: 4px; }
.mc-side-panel::-webkit-scrollbar-thumb { background: #27272a; border-radius: 2px; }

/* Click-to-edit affordance */
.mc-editable { border: 1px solid transparent; border-radius: 4px; cursor: pointer; transition: border-color 0.15s; }
.mc-editable:hover { border-color: #27272a; }

/* Done items — green-gray tint instead of faded */
.mc-card.mc-done { opacity: 0.7; }
.mc-card.mc-done:hover { opacity: 1.0; }

/* Resize handle */
.mc-resize-handle { height: 3px; cursor: row-resize; position: relative; }
.mc-resize-handle::after { content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 40px; height: 3px; border-radius: 2px; background: #1e1e23; }
.mc-resize-handle:hover::after { background: #3b82f6; }
```

Also remove old CSS rules for `.mc-card` (`.mc-p1`, `.mc-p2`, `.mc-p3` border-left rules) since cards now use inline styles for borders.

- [ ] **Step 2: Run tests**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 3: Commit**

```bash
git add src/agile_backlog/app.py
git commit -m "style: update CSS for unified cards, side panel, click-to-edit, resize handles"
```

---

### Task 7: Rewrite header and filter bar — sticky, no sprint badge, inline chips, sort

**Files:**
- Modify: `src/agile_backlog/app.py` (kanban_page function — header section)
- Modify: `src/agile_backlog/components.py` (filter components if extracted)

- [ ] **Step 1: Rewrite header rendering**

In `kanban_page()`, find the header rendering section and replace with:

1. **Header row:** Logo "agile-backlog" + Board/Backlog tabs + "Add Item" button. No sprint badge when Backlog is active. "Show archived" only when Board is active.
2. **Filter bar:** Compact dropdowns (Priority, Category, Tags) + inline removable chips for active filters + sort button (`↓ Priority`) + search input. No duplicate chip row below.

Key implementation details:
- Header: `flex-shrink:0` so it never scrolls
- Filter bar: `flex-shrink:0`, same principle
- Sort button: `ui.button` styled as dropdown, click opens `ui.menu` with sort options
- Active filter chips: rendered inline in the filter bar `div`, each with a ✕ button that clears that filter
- Remove the separate `_refresh_chips` function and chips row

- [ ] **Step 2: Test manually**

Run: `.venv/bin/agile-backlog serve --no-reload`

Verify:
- Header stays fixed on scroll
- No sprint badge in backlog view
- Filter chips appear inline next to dropdowns
- Sort button shows active sort
- "Show archived" only visible on Board tab

- [ ] **Step 3: Run tests**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 4: Commit**

```bash
git add src/agile_backlog/app.py
git commit -m "feat: sticky header with inline filter chips and sort button"
```

---

### Task 8: Rewrite _render_backlog_list — resizable three-section layout

**Files:**
- Modify: `src/agile_backlog/components.py` (replace `_render_backlog_list`)

- [ ] **Step 1: Replace _render_backlog_list**

Rewrite the function to render three resizable sections with independent inner scroll:

1. **Outer layout:** Column flexbox filling remaining viewport height (`flex:1;overflow:hidden`)
2. **Three sections** with `ui.splitter` (vertical) or custom flex layout:
   - Each section: header (collapsible arrow + label + count + zoom button) + scrollable item list
   - Section header colors: Backlog=#71717a, vNext=#ca8a04, vFuture=#22c55e
   - Section labels include sprint context: "vNext — Sprint N+1", "vFuture — Sprint N+2+"
3. **Resize handles** between sections (if not using `ui.splitter`)
4. **Zoom button** (⤢) on each header: expands section to full height, collapses others to header-only. Click again to restore.
5. **Items** rendered with `ui.html(render_card_html(item))` inside each section's scrollable area
6. **Move buttons** on hover: position:absolute, appear at bottom-right of card on hover
7. **Filters** apply to Backlog section only (vNext/vFuture always unfiltered)
8. **Clicking a card** opens the side panel (Task 9)

Implementation approach for resizable sections:
- Try NiceGUI's `ui.splitter(horizontal=False)` first — it supports drag-to-resize natively
- If `ui.splitter` doesn't support triple-split, use nested splitters: outer splits Backlog from (vNext+vFuture), inner splits vNext from vFuture
- Each splitter pane contains a section header + scrollable items div

- [ ] **Step 2: Wire move-to buttons**

Each card row gets hover-revealed move buttons. Implementation:
- Wrap card HTML + buttons in a `position:relative` container
- Buttons use `mc-move-buttons` CSS class (hidden by default, shown on hover)
- Button click: update `item.sprint_target`, call `save_fn(item)`, refresh

Move-to targets by section:
- Backlog items: [→ vNext] [→ vFuture]
- vNext items: [← Backlog] [→ vFuture]
- vFuture items: [← Backlog] [← vNext]

- [ ] **Step 3: Manual test**

Run: `.venv/bin/agile-backlog serve --no-reload`

Verify:
- Three sections always visible
- Each section scrolls independently
- Section headers show label + count
- Resize handles work between sections
- Zoom button expands/restores sections
- Move buttons appear on hover
- Filters apply to Backlog only

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/app.py
git commit -m "feat: resizable three-section backlog layout with independent scroll"
```

---

### Task 9: Rewrite side panel — click-to-edit, chat comments

**Files:**
- Modify: `src/agile_backlog/components.py` (replace `_render_side_panel_content`)
- Modify: `src/agile_backlog/components.py` (remove `_render_detail_modal_content`, `_show_edit_dialog`)

This is the largest UI task. The side panel needs:
1. Click-to-edit for all fields (no Edit button)
2. iMessage chat comments at bottom
3. Fixed position with independent scroll
4. Comment input pinned to bottom

- [ ] **Step 1: Replace _render_side_panel_content**

Rewrite to implement:

**Panel structure:**
- Header: Close button (✕) only — no Edit button
- Panel body: scrollable (`overflow-y:auto; flex:1`)
- Comment input: pinned to bottom (`flex-shrink:0`)

**Title (click to edit):**
- Default: `ui.label` with `mc-editable` class
- Click → `ui.input` with blue border, pre-filled with current title
- Blur/Enter → save, switch back to label, refresh card list

**Metadata pills (row 1: status, phase, priority, complexity, category):**
- Each pill is a clickable `ui.html` element with `mc-editable` class
- Click → `ui.select` or `ui.menu` appears below with options
- Select option → save, close dropdown, refresh

**Tags (row 2):**
- Each tag is a clickable pill — click to remove (with confirmation or immediate)
- "+ tag" pill → `ui.input` with autocomplete from existing tags across all items
- Enter/select → add tag, save, refresh

**Text sections (description, AC, tech specs):**
- Default: rendered text with `mc-editable` class
- Click → `ui.textarea` with blue border, pre-filled
- Save/Cancel buttons below textarea
- Save → persist, switch back to text view

**Comments section:**
- Thread rendered with `comment_thread_html()` via `ui.html`
- Per-comment "Resolve" button for flagged unresolved comments (using NiceGUI `ui.button`)
- Comment input area at bottom (pinned):
  - `ui.textarea` (2 rows) with placeholder
  - "Flag for AI" checkbox
  - "Send" button
  - On send: append comment dict, save, refresh thread

- [ ] **Step 2: Update selected card highlighting**

When a card is clicked:
- Add `mc-selected` class to the clicked card container
- Remove `mc-selected` from previously selected card
- Track selected item ID in panel state

- [ ] **Step 3: Remove _show_edit_dialog and _render_detail_modal_content**

Delete these functions — they're replaced by the inline-editing side panel. Update all callers:
- Board view card click → opens side panel instead of detail modal
- Board view edit → uses side panel inline editing

- [ ] **Step 4: Wire side panel to board view**

The board view (`_render_card`) currently opens a detail modal on click. Change to open the shared side panel:
- Board view gets the same 50/50 split layout as backlog
- Clicking a board card opens the side panel with that item
- Same click-to-edit behavior

- [ ] **Step 5: Manual test**

Run: `.venv/bin/agile-backlog serve --no-reload`

Verify:
- Click card → side panel opens with 50/50 split
- Selected card highlighted with blue border
- Click title → editable input, save on blur
- Click priority pill → dropdown with P0-P4
- Click category pill → dropdown with bug/feature/docs/chore
- Click description → textarea with Save/Cancel
- Comments show iMessage style (user right, agent left)
- Resolve button works on flagged comments
- Comment input works with flag toggle
- Escape closes panel
- Works on both Board and Backlog tabs

- [ ] **Step 6: Run tests**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/app.py
git commit -m "feat: click-to-edit side panel with chat comments, shared by board and backlog"
```

---

### Task 10: Clean up removed tests and update board card rendering

**Files:**
- Modify: `tests/test_pure.py`
- Modify: `src/agile_backlog/components.py` (`_render_card` function for board view)

- [ ] **Step 1: Remove obsolete tests**

Delete these test methods (functions no longer exist or behavior changed):
- `test_render_card_with_phase` — phase badges removed from cards
- `test_render_card_without_phase` — same
- Any tests for `_show_edit_dialog` or `_render_detail_modal_content`
- Any tests referencing `render_backlog_card_html` (now `render_card_html`)

- [ ] **Step 2: Update board _render_card to use unified render_card_html**

In `_render_card()`, replace the call to the old `render_card_html` with the new unified version. Ensure board-specific features still work:
- Move buttons (→ doing, → done) on hover
- Done card opacity treatment
- Click → opens side panel (not modal)

- [ ] **Step 3: Run full tests**

Run: `.venv/bin/pytest tests/ -v`

- [ ] **Step 4: Run lint**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check .`

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "refactor: clean up obsolete tests, update board card to unified design"
```

---

### Task 11: Full integration verification

- [ ] **Step 1: Run lint + format + tests**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`

- [ ] **Step 2: Manual smoke test**

Run: `.venv/bin/agile-backlog serve --no-reload`

Verify all spec acceptance criteria:
1. Header is sticky, no sprint badge in backlog, filters inline, no duplicate chips
2. Three sections always visible with resize handles and zoom
3. Cards show two-line layout with priority border, badges, tags, timestamp
4. Move buttons appear on hover only
5. Side panel: click-to-edit works for all fields (title, priority, category, etc.)
6. Comments display as iMessage-style chat (user right, agent left)
7. Selected card highlighted with blue border
8. Side panel scrolls independently, comment input pinned
9. Sort button works
10. Board view uses same card design and side panel
11. Done items show 0.7 opacity with green-gray tint
12. Works on both Board and Backlog tabs with unified experience

- [ ] **Step 3: Fix any issues found**

- [ ] **Step 4: Commit fixes**

```bash
git add -A
git commit -m "fix: integration fixes from smoke testing"
```
