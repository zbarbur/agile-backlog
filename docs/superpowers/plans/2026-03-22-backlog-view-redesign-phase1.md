# Backlog View Redesign — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the raw backlog table with a card-list planning view: three collapsible sections (Backlog/vNext/vFuture), "Move to" buttons, side panel with detail view and chat comments, plus data model migration (categories → enum, P0-P4 priorities, agent_notes → comments rename).

**Architecture:** Bottom-up build — data model and tokens first (no UI deps), then pure functions (testable without NiceGUI), then CLI updates, then UI components. Each layer is tested before the next starts. The two-layer migration strategy (model validators for transparent compat + optional CLI command for YAML cleanup) means we never break existing data.

**Tech Stack:** Python 3.11+, Pydantic v2, NiceGUI, Click, PyYAML, pytest, ruff

**Spec:** `docs/superpowers/specs/2026-03-22-backlog-view-redesign.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/agile_backlog/models.py` | Modify | Category enum, priority P0-P4, agent_notes → comments, migration validators |
| `src/agile_backlog/tokens.py` | Modify | P0/P4 colors, chore category style, fix fallback |
| `src/agile_backlog/app.py` | Modify | New backlog view (sections, cards, side panel, comments), archive-done |
| `src/agile_backlog/cli.py` | Modify | Updated enums, comments field, --tags filter, migrate command |
| `src/agile_backlog/schema.yaml` | Modify | Updated enums, comments field docs |
| `tests/test_models.py` | Modify | Migration validators, new enums |
| `tests/test_app.py` | Modify | group_items_by_section, card rendering, comment rendering, archive-done |
| `tests/test_cli.py` | Modify | --tags filter, migrate command, updated enums |

---

### Task 1: Expand Priority Enum (models.py + tokens.py)

**Files:**
- Modify: `src/agile_backlog/models.py:25` (priority field)
- Modify: `src/agile_backlog/tokens.py:14-21` (PRIORITY_COLORS, PRIORITY_ORDER)
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for P0 and P4**

In `tests/test_models.py`, add to `TestBacklogItem`:

```python
def test_p0_priority_valid(self):
    item = BacklogItem(id="x", title="x", priority="P0", category="bug")
    assert item.priority == "P0"

def test_p4_priority_valid(self):
    item = BacklogItem(id="x", title="x", priority="P4", category="bug")
    assert item.priority == "P4"
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_models.py::TestBacklogItem::test_p0_priority_valid tests/test_models.py::TestBacklogItem::test_p4_priority_valid -v`
Expected: FAIL — P0/P4 not in Literal

- [ ] **Step 3: Update priority Literal in models.py**

In `src/agile_backlog/models.py:25`, change:
```python
priority: Literal["P1", "P2", "P3"]
```
to:
```python
priority: Literal["P0", "P1", "P2", "P3", "P4"]
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `pytest tests/test_models.py -v`

- [ ] **Step 5: Update tokens.py — PRIORITY_COLORS and PRIORITY_ORDER**

In `src/agile_backlog/tokens.py`, replace PRIORITY_COLORS and PRIORITY_ORDER:

```python
PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "P0": ("#ef4444", "rgba(239,68,68,0.18)"),
    "P1": ("#f87171", "rgba(248,113,113,0.15)"),
    "P2": ("#fbbf24", "rgba(251,191,36,0.12)"),
    "P3": ("#6b7280", "rgba(107,114,128,0.10)"),
    "P4": ("#4b5563", "rgba(75,85,99,0.08)"),
}

PRIORITY_ORDER: dict[str, int] = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
```

Note: P2 color changed from blue to amber per spec. P3 changed from amber to gray.

- [ ] **Step 6: Update app.py tests for new priority colors**

In `tests/test_app.py`, update `TestCategoryStyle` and any priority filter tests that reference only P1-P3. Add:

```python
def test_filter_p0_items(self):
    items = [_item(priority="P0"), _item(priority="P2")]
    result = filter_items(items, priority="P0")
    assert len(result) == 1
```

- [ ] **Step 7: Run full test suite**

Run: `pytest tests/ -v`

- [ ] **Step 8: Commit**

```bash
git add src/agile_backlog/models.py src/agile_backlog/tokens.py tests/test_models.py tests/test_app.py
git commit -m "feat: expand priority enum to P0-P4 with updated colors"
```

---

### Task 2: Category Enum + Migration Validator (models.py)

**Files:**
- Modify: `src/agile_backlog/models.py:26` (category field), add validator
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for category enum and migration**

In `tests/test_models.py`, add `TestCategoryMigration`:

```python
class TestCategoryMigration:
    def test_valid_categories(self):
        for cat in ("bug", "feature", "docs", "chore"):
            item = BacklogItem(id="x", title="x", priority="P2", category=cat)
            assert item.category == cat

    def test_infra_migrates_to_chore(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="infra")
        assert item.category == "chore"
        assert "infra" in item.tags

    def test_tech_debt_migrates_to_chore(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="tech-debt")
        assert item.category == "chore"
        assert "tech-debt" in item.tags

    def test_security_migrates_to_feature(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="security")
        assert item.category == "feature"
        assert "security" in item.tags

    def test_unknown_category_migrates_to_chore(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="random-thing")
        assert item.category == "chore"

    def test_migration_does_not_duplicate_tags(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="infra", tags=["infra", "ci"])
        assert item.category == "chore"
        assert item.tags.count("infra") == 1
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_models.py::TestCategoryMigration -v`

- [ ] **Step 3: Add migrate_old_categories validator to BacklogItem**

In `src/agile_backlog/models.py`, after `migrate_old_phases`, add:

```python
@model_validator(mode="before")
@classmethod
def migrate_old_categories(cls, data: dict) -> dict:
    """Migrate old category values to the new 4-value enum."""
    if not isinstance(data, dict):
        return data
    cat = data.get("category", "")
    tags = list(data.get("tags", []))
    migration_map = {
        "infra": ("chore", "infra"),
        "tech-debt": ("chore", "tech-debt"),
        "security": ("feature", "security"),
    }
    if cat in migration_map:
        new_cat, tag = migration_map[cat]
        data["category"] = new_cat
        if tag not in tags:
            tags.append(tag)
        data["tags"] = tags
    elif cat not in ("bug", "feature", "docs", "chore"):
        data["category"] = "chore"
    return data
```

- [ ] **Step 4: Change category type to Literal**

In `src/agile_backlog/models.py:26`, change:
```python
category: str
```
to:
```python
category: Literal["bug", "feature", "docs", "chore"]
```

- [ ] **Step 5: Run tests — expect PASS**

Run: `pytest tests/test_models.py -v`

- [ ] **Step 6: Run full suite to check no YAML files break**

Run: `pytest tests/ -v`

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/models.py tests/test_models.py
git commit -m "feat: enforce category enum (bug/feature/docs/chore) with migration validator"
```

---

### Task 3: Rename agent_notes → comments (models.py)

**Files:**
- Modify: `src/agile_backlog/models.py:42` (field rename + validator)
- Modify: `src/agile_backlog/yaml_store.py` (no changes needed — transparent via validator)
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for comments field and migration**

In `tests/test_models.py`, add `TestCommentsField`:

```python
class TestCommentsField:
    def test_comments_field_exists(self):
        item = BacklogItem(id="x", title="x", priority="P2", category="bug")
        assert item.comments == []

    def test_comments_field_populated(self):
        item = BacklogItem(
            id="x", title="x", priority="P2", category="bug",
            comments=[{"text": "hello", "flagged": False, "resolved": False}],
        )
        assert len(item.comments) == 1

    def test_agent_notes_migrates_to_comments(self):
        """Old YAML files with agent_notes key should load into comments field."""
        item = BacklogItem(
            id="x", title="x", priority="P2", category="bug",
            agent_notes=[{"text": "old note", "flagged": True, "resolved": False}],
        )
        assert len(item.comments) == 1
        assert item.comments[0]["text"] == "old note"
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_models.py::TestCommentsField -v`

- [ ] **Step 3: Add migration validator and rename field**

In `src/agile_backlog/models.py`:

1. Rename the field from `agent_notes` to `comments`:
```python
comments: list[dict] = Field(default_factory=list)
```

2. Add migration validator (after `migrate_old_categories`):
```python
@model_validator(mode="before")
@classmethod
def migrate_agent_notes_to_comments(cls, data: dict) -> dict:
    """Migrate old agent_notes field to comments."""
    if not isinstance(data, dict):
        return data
    if "agent_notes" in data and "comments" not in data:
        data["comments"] = data.pop("agent_notes")
    elif "agent_notes" in data:
        data.pop("agent_notes")
    return data
```

- [ ] **Step 4: Update to_yaml_dict to exclude agent_notes alias**

No change needed — Pydantic `model_dump()` will use the new field name `comments`.

- [ ] **Step 5: Run model tests — expect PASS**

Run: `pytest tests/test_models.py -v`

- [ ] **Step 6: Update existing test references from agent_notes to comments**

Search all test files for `agent_notes` and update to `comments`. Key locations:
- `tests/test_models.py`: `TestAgentNotes` class — update field references
- `tests/test_app.py`: `TestCommentBadgeHtml` — update field name in test items
- `tests/test_cli.py`: `TestNote` — update field references

- [ ] **Step 7: Run full suite**

Run: `pytest tests/ -v`

- [ ] **Step 8: Commit**

```bash
git add src/agile_backlog/models.py tests/
git commit -m "feat: rename agent_notes to comments with backwards-compat validator"
```

---

### Task 4: Update tokens.py — chore style + fallback fix

**Files:**
- Modify: `src/agile_backlog/tokens.py:4-11` (CATEGORY_STYLES)
- Modify: `src/agile_backlog/app.py:14-16` (category_style fallback)
- Test: `tests/test_app.py`

- [ ] **Step 1: Write failing test for chore category style**

In `tests/test_app.py`, add to `TestCategoryStyle`:

```python
def test_chore_style(self):
    text, bg = category_style("chore")
    assert text.startswith("#")
    assert bg.startswith("rgba")
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `pytest tests/test_app.py::TestCategoryStyle::test_chore_style -v`

- [ ] **Step 3: Add chore to CATEGORY_STYLES, clean up old entries**

In `src/agile_backlog/tokens.py`, replace CATEGORY_STYLES:

```python
CATEGORY_STYLES: dict[str, tuple[str, str]] = {
    "bug": ("#f472b6", "rgba(244,114,182,0.12)"),
    "feature": ("#60a5fa", "rgba(59,130,246,0.15)"),
    "docs": ("#34d399", "rgba(52,211,153,0.12)"),
    "chore": ("#a78bfa", "rgba(167,139,250,0.12)"),
}
```

Note: Removed `tech-debt`, `security`, `infra` (now migrated via model validators). `chore` gets the purple color previously used by `security`.

- [ ] **Step 4: Fix category_style fallback in app.py**

In `src/agile_backlog/app.py`, find `category_style()` (line 14) and update the fallback from light-theme color to dark-theme:

```python
def category_style(cat: str) -> tuple[str, str]:
    return CATEGORY_STYLES.get(cat, ("#9ca3af", "rgba(156,163,175,0.10)"))
```

- [ ] **Step 5: Update fallback test**

In `tests/test_app.py`, update the fallback test in `TestCategoryStyle`:

```python
def test_unknown_category_fallback(self):
    text, bg = category_style("unknown")
    assert text == "#9ca3af"
    assert "rgba" in bg
```

- [ ] **Step 6: Run full tests**

Run: `pytest tests/ -v`

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/tokens.py src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: add chore category style, fix dark-theme fallback color"
```

---

### Task 5: Update CLI — enums, comments field, --tags filter

**Files:**
- Modify: `src/agile_backlog/cli.py` (priority choices, category choices, comments references, --tags filter)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for --tags filter**

In `tests/test_cli.py`, add to a new `TestTagsFilter` class:

```python
class TestTagsFilter:
    def test_list_filter_by_tag(self, runner, backlog_dir):
        (backlog_dir / "a.yaml").write_text(yaml.dump({
            "title": "A", "status": "backlog", "priority": "P2",
            "category": "feature", "tags": ["ui", "planning"],
        }))
        (backlog_dir / "b.yaml").write_text(yaml.dump({
            "title": "B", "status": "backlog", "priority": "P2",
            "category": "feature", "tags": ["cli"],
        }))
        result = runner.invoke(main, ["list", "--tags", "ui"])
        assert "A" in result.output
        assert "B" not in result.output
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `pytest tests/test_cli.py::TestTagsFilter -v`

- [ ] **Step 3: Update CLI priority choices to P0-P4**

In `src/agile_backlog/cli.py`, find all `click.Choice(["P1", "P2", "P3"])` and update to `click.Choice(["P0", "P1", "P2", "P3", "P4"])`. Locations:
- `add` command `--priority` option
- `list` command `--priority` option
- `edit` command `--priority` option

- [ ] **Step 4: Add category choices to CLI**

In `src/agile_backlog/cli.py`, update the `add` and `edit` commands' `--category` option to use `click.Choice(["bug", "feature", "docs", "chore"])` instead of free text. Update `list` command's `--category` similarly.

- [ ] **Step 5: Update all agent_notes references to comments**

In `src/agile_backlog/cli.py`, replace all `item.agent_notes` with `item.comments` and `agent_notes` dict key references. Key locations:
- `show` command (line ~156-163): Display comments section
- `note` command (line ~224-231): Append to `item.comments`
- `flagged` command (line ~242): Filter on `item.comments`
- `resolve-note` command (line ~276): Index into `item.comments`
- `edit` command `--resolve-notes` (line ~205-208): Iterate `item.comments`

- [ ] **Step 6: Add --tags filter to list command**

In `src/agile_backlog/cli.py`, add to the `list` command options:

```python
@click.option("--tags", multiple=True, help="Filter by tag (items matching ANY tag shown)")
```

Add filter logic after existing filters:

```python
if tags:
    items = [i for i in items if set(tags) & set(i.tags)]
```

- [ ] **Step 7: Update existing CLI tests for new field name**

In `tests/test_cli.py`, update `TestNote` and other tests that reference `agent_notes` to use `comments`.

- [ ] **Step 8: Run full tests**

Run: `pytest tests/ -v`

- [ ] **Step 9: Commit**

```bash
git add src/agile_backlog/cli.py tests/test_cli.py
git commit -m "feat: update CLI — P0-P4 priorities, category enum, comments field, --tags filter"
```

---

### Task 6: Update schema.yaml

**Files:**
- Modify: `src/agile_backlog/schema.yaml`

- [ ] **Step 1: Update schema.yaml enums and field names**

Update `src/agile_backlog/schema.yaml`:

1. Priority enum: `[P0, P1, P2, P3, P4]` with updated descriptions
2. Category: add `enum: [bug, feature, docs, chore]` with descriptions
3. Rename `agent_notes` → `comments`, add `author` property

- [ ] **Step 2: Commit**

```bash
git add src/agile_backlog/schema.yaml
git commit -m "docs: update schema.yaml — P0-P4 priorities, category enum, comments field"
```

---

### Task 7: Pure function — group_items_by_section()

**Files:**
- Modify: `src/agile_backlog/app.py` (add pure function at top)
- Test: `tests/test_app.py`

- [ ] **Step 1: Write failing tests for group_items_by_section**

In `tests/test_app.py`, add `TestGroupItemsBySection`:

```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_app.py::TestGroupItemsBySection -v`

- [ ] **Step 3: Implement group_items_by_section**

In `src/agile_backlog/app.py`, add after the existing pure functions (after `comment_badge_html`):

```python
def group_items_by_section(
    items: list[BacklogItem], current_sprint: int | None
) -> dict[str, list[BacklogItem]]:
    """Group backlog/unplanned items into three planning sections.

    Items with status 'doing' or 'done' are excluded (they belong on the board).
    """
    backlog, vnext, vfuture = [], [], []
    for item in items:
        if item.status in ("doing", "done"):
            continue
        if current_sprint is None or item.sprint_target is None:
            backlog.append(item)
        elif item.sprint_target == current_sprint + 1:
            vnext.append(item)
        elif item.sprint_target >= current_sprint + 2:
            vfuture.append(item)
        else:
            backlog.append(item)

    def _sort_key(i: BacklogItem) -> tuple:
        return (PRIORITY_ORDER.get(i.priority, 99), str(i.updated))

    backlog.sort(key=_sort_key)
    vnext.sort(key=_sort_key)
    vfuture.sort(key=_sort_key)
    return {"backlog": backlog, "vnext": vnext, "vfuture": vfuture}
```

- [ ] **Step 4: Export function for tests**

Ensure `group_items_by_section` is importable in tests. Add it to the test file's import line:

```python
from agile_backlog.app import category_style, filter_items, render_card_html, comment_badge_html, detect_current_sprint, group_items_by_section
```

- [ ] **Step 5: Run tests — expect PASS**

Run: `pytest tests/test_app.py::TestGroupItemsBySection -v`

- [ ] **Step 6: Run full suite**

Run: `pytest tests/ -v`

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: add group_items_by_section pure function"
```

---

### Task 8: Pure function — render_comment_html()

**Files:**
- Modify: `src/agile_backlog/app.py` (add pure function)
- Test: `tests/test_app.py`

- [ ] **Step 1: Write failing tests for render_comment_html**

In `tests/test_app.py`, add `TestRenderCommentHtml`:

```python
class TestRenderCommentHtml:
    def test_basic_comment(self):
        comment = {"text": "Hello world", "flagged": False, "resolved": False, "created": "2026-03-22", "author": "user"}
        html = render_comment_html(comment)
        assert "Hello world" in html
        assert "2026-03-22" in html

    def test_flagged_comment_highlighted(self):
        comment = {"text": "Check this", "flagged": True, "resolved": False, "created": "2026-03-22", "author": "agent"}
        html = render_comment_html(comment)
        assert "flagged" in html.lower() or "#f87171" in html or "border" in html

    def test_resolved_comment_faded(self):
        comment = {"text": "Done", "flagged": True, "resolved": True, "created": "2026-03-22", "author": "agent"}
        html = render_comment_html(comment)
        assert "opacity" in html or "line-through" in html

    def test_user_vs_agent_icons(self):
        user_html = render_comment_html({"text": "x", "author": "user", "flagged": False, "resolved": False})
        agent_html = render_comment_html({"text": "x", "author": "agent", "flagged": False, "resolved": False})
        assert user_html != agent_html  # Different styling for user vs agent
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_app.py::TestRenderCommentHtml -v`

- [ ] **Step 3: Implement render_comment_html**

In `src/agile_backlog/app.py`, add pure function:

```python
def render_comment_html(comment: dict) -> str:
    """Render a single comment as an HTML bubble."""
    author = comment.get("author", "agent")
    text = comment.get("text", "")
    created = comment.get("created", "")
    flagged = comment.get("flagged", False)
    resolved = comment.get("resolved", False)

    icon = "👤" if author == "user" else "🤖"
    border_color = "#f87171" if flagged and not resolved else "transparent"
    opacity = "0.5" if resolved else "1.0"
    text_style = "text-decoration:line-through;" if resolved else ""

    return (
        f'<div style="border-left:3px solid {border_color};padding:8px 12px;'
        f'margin:4px 0;border-radius:6px;background:rgba(255,255,255,0.04);opacity:{opacity};">'
        f'<div style="font-size:11px;color:#71717a;margin-bottom:4px;">'
        f'{icon} {author} &nbsp; {created}</div>'
        f'<div style="{text_style}color:#d4d4d8;font-size:13px;">{text}</div>'
        f'</div>'
    )
```

- [ ] **Step 4: Add comment_thread_html**

```python
def comment_thread_html(comments: list[dict]) -> str:
    """Render a full comment thread as HTML."""
    return "".join(render_comment_html(c) for c in comments)
```

- [ ] **Step 5: Run tests — expect PASS**

Run: `pytest tests/test_app.py::TestRenderCommentHtml -v`

- [ ] **Step 6: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: add render_comment_html and comment_thread_html pure functions"
```

---

### Task 9: Pure function — render_backlog_card_html()

**Files:**
- Modify: `src/agile_backlog/app.py` (add pure function)
- Test: `tests/test_app.py`

- [ ] **Step 1: Write failing tests for render_backlog_card_html**

In `tests/test_app.py`, add `TestRenderBacklogCardHtml`:

```python
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

    def test_shows_complexity_badge(self):
        item = _item(complexity="M")
        html = render_backlog_card_html(item)
        assert "M" in html

    def test_shows_comment_badge(self):
        item = _item(comments=[{"text": "x", "flagged": True, "resolved": False}])
        html = render_backlog_card_html(item)
        assert "1" in html  # badge count
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_app.py::TestRenderBacklogCardHtml -v`

- [ ] **Step 3: Implement render_backlog_card_html**

In `src/agile_backlog/app.py`, add pure function:

```python
def render_backlog_card_html(item: BacklogItem) -> str:
    """Render a backlog card row as HTML for the planning view."""
    pri_color = PRIORITY_COLORS.get(item.priority, ("#6b7280", "rgba(107,114,128,0.1)"))
    bar_color = pri_color[0] if item.priority in ("P0", "P1") else "transparent"
    cat_style = category_style(item.category)

    # Comment badge
    badge = comment_badge_html(item.comments)

    # Complexity badge
    complexity = _complexity_badge(item.complexity) if item.complexity else ""

    # Tags
    tag_chips = "".join(
        f'<span style="font-size:10px;color:#9ca3af;background:rgba(156,163,175,0.10);'
        f'padding:1px 6px;border-radius:4px;margin-right:4px;">{t}</span>'
        for t in item.tags
    )

    # Category pill
    cat_pill = (
        f'<span style="font-size:10px;color:{cat_style[0]};background:{cat_style[1]};'
        f'padding:1px 8px;border-radius:4px;margin-right:4px;">{item.category}</span>'
    )

    return (
        f'<div style="border-left:3px solid {bar_color};padding:8px 12px;cursor:pointer;'
        f'border-radius:6px;background:rgba(255,255,255,0.03);margin:2px 0;" '
        f'class="backlog-card-row">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="color:#e4e4e7;font-size:13px;">{item.title}</span>'
        f'<span>{badge}{complexity}</span>'
        f'</div>'
        f'<div style="margin-top:4px;">{cat_pill}{tag_chips}</div>'
        f'</div>'
    )
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `pytest tests/test_app.py::TestRenderBacklogCardHtml -v`

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: add render_backlog_card_html pure function for planning view"
```

---

### Task 10: Update app.py — comments field references

**Files:**
- Modify: `src/agile_backlog/app.py` (all agent_notes → comments)
- Test: `tests/test_app.py`

- [ ] **Step 1: Replace all agent_notes references in app.py**

Search `src/agile_backlog/app.py` for `agent_notes` and replace with `comments`. Key locations:
- `comment_badge_html()` — parameter/field access
- `_show_comment_dialog()` — reads/writes agent_notes
- `_render_detail_modal_content()` — displays agent_notes
- `_render_card()` — accesses agent_notes for badge
- `render_card_html()` — accesses agent_notes for badge

- [ ] **Step 2: Run full tests**

Run: `pytest tests/ -v`

- [ ] **Step 3: Commit**

```bash
git add src/agile_backlog/app.py
git commit -m "refactor: update app.py agent_notes references to comments"
```

---

### Task 11: Backlog planning view — three sections with cards

**Files:**
- Modify: `src/agile_backlog/app.py` (replace `_render_backlog_list`)

This is the largest UI task. It replaces the current Quasar table with the three-section card list.

- [ ] **Step 1: Replace _render_backlog_list with new planning view**

Replace `_render_backlog_list()` (lines ~922-1019) with a new function that:

1. Gets current sprint via `detect_current_sprint()` or config
2. Calls `group_items_by_section(items, current_sprint)`
3. Renders three collapsible sections using `ui.expansion`:
   - **BACKLOG (unplanned)** — with item count
   - **vNEXT — Sprint N+1** — with item count
   - **vFUTURE — Sprint N+2+** — with item count
4. Each section contains card rows rendered via `ui.html(render_backlog_card_html(item))`
5. Each card row is clickable → opens side panel (next task)
6. Each card row has "Move to" buttons:
   - Backlog items: [→ vNext] [→ vFuture]
   - vNext items: [← Backlog] [→ vFuture]
   - vFuture items: [← Backlog] [← vNext]

**Move-to button logic:**
- → vNext: set `sprint_target = current_sprint + 1`
- → vFuture: set `sprint_target = current_sprint + 2`
- → Backlog: set `sprint_target = None`
- Save item, refresh view

- [ ] **Step 2: Add filter controls for Backlog section only**

Above the sections, add filter row (reuse existing filter pattern):
- Priority multi-select
- Category multi-select
- Tags multi-select
- Search input

Filters apply ONLY to the Backlog section. vNext and vFuture are always unfiltered.

- [ ] **Step 3: Manual test in browser**

Run: `.venv/bin/agile-backlog serve`

Verify:
- Three sections visible with correct items
- Sections collapse/expand
- Move-to buttons work
- Filters apply to Backlog only

- [ ] **Step 4: Run full tests**

Run: `pytest tests/ -v`

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/app.py
git commit -m "feat: replace backlog table with three-section planning view"
```

---

### Task 12: Side panel — detail view + edit button

**Files:**
- Modify: `src/agile_backlog/app.py`

- [ ] **Step 1: Implement side panel**

When a card row is clicked, open a side panel on the right side. Implementation approach: two-column flexbox layout where the right column is conditionally rendered.

Panel contents (reuse `_render_detail_modal_content` pattern):
- Close button (top left) + Edit button (top right)
- Title
- Metadata grid: Status, Phase, Priority, Complexity, Category, Sprint, Tags
- Description section
- Acceptance Criteria (with checkboxes)
- Technical Specs
- Comments thread (using `comment_thread_html`)
- Comment input at bottom (text field + flag toggle + send button)

**Edit button:** Opens existing `_show_edit_dialog()`.

**Close:** Click close button, press Escape, or click outside panel.

- [ ] **Step 2: Wire comment input to save**

Comment input at bottom of side panel:
- Text input field
- Flag toggle (checkbox "Flag for AI")
- Send button
- On send: append comment dict to `item.comments`, save, refresh panel

**Resolve button:** Per-comment button that sets `resolved: True`, saves, refreshes.

- [ ] **Step 3: Manual test**

Run: `.venv/bin/agile-backlog serve`

Verify:
- Click card → side panel opens
- Panel shows all item details
- Edit button opens edit dialog
- Comment input works (add, flag, resolve)
- Close button, Escape key work
- List narrows when panel opens

- [ ] **Step 4: Run full tests**

Run: `pytest tests/ -v`

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/app.py
git commit -m "feat: add side panel with detail view, comments, and edit button"
```

---

### Task 13: Replace show-done checkbox with archive-done

**Files:**
- Modify: `src/agile_backlog/app.py` (board view done column)
- Test: `tests/test_app.py`

- [ ] **Step 1: Write failing test for done item age filtering**

In `tests/test_app.py`, add `TestArchiveDone`:

```python
from datetime import date, timedelta

class TestArchiveDone:
    def test_recent_done_items_visible(self):
        item = _item(status="done", updated=date.today())
        assert is_recently_done(item, days=7)

    def test_old_done_items_hidden(self):
        item = _item(status="done", updated=date.today() - timedelta(days=10))
        assert not is_recently_done(item, days=7)

    def test_non_done_items_always_visible(self):
        item = _item(status="doing", updated=date.today() - timedelta(days=30))
        assert is_recently_done(item, days=7)  # Function only filters done items
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_app.py::TestArchiveDone -v`

- [ ] **Step 3: Implement is_recently_done pure function**

In `src/agile_backlog/app.py`, add:

```python
def is_recently_done(item: BacklogItem, days: int = 7) -> bool:
    """Return True if item should be visible on the board.

    Non-done items are always visible. Done items are visible only if
    updated within the last `days` days.
    """
    if item.status != "done":
        return True
    cutoff = date.today() - timedelta(days=days)
    return item.updated >= cutoff
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `pytest tests/test_app.py::TestArchiveDone -v`

- [ ] **Step 5: Replace done_check checkbox with archive toggle in board view**

In the board view (`kanban_page`):
1. Remove `done_check = ui.checkbox("Show done", ...)` (line ~1177-1179)
2. Replace with: `archive_toggle = ui.checkbox("Show archived", value=False)` — when checked, shows ALL done items; when unchecked, shows only recently done (last 7 days)
3. Update the done column filtering logic:
   - If archive_toggle unchecked: `filtered_done = [i for i in filtered_done if is_recently_done(i)]`
   - If archive_toggle checked: show all done items
4. Update empty state message for done column

- [ ] **Step 6: Manual test**

Run: `.venv/bin/agile-backlog serve`

Verify: Done column shows recent items by default, "Show archived" reveals older ones.

- [ ] **Step 7: Run full tests**

Run: `pytest tests/ -v`

- [ ] **Step 8: Commit**

```bash
git add src/agile_backlog/app.py tests/test_app.py
git commit -m "feat: replace show-done checkbox with archive-done (7-day default)"
```

---

### Task 14: Migration CLI command

**Files:**
- Modify: `src/agile_backlog/cli.py` (add `migrate` command)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for migrate command**

In `tests/test_cli.py`, add `TestMigrate`:

```python
class TestMigrate:
    def test_migrate_dry_run(self, runner, backlog_dir):
        (backlog_dir / "old.yaml").write_text(yaml.dump({
            "title": "Old Item", "status": "backlog", "priority": "P2",
            "category": "infra", "agent_notes": [{"text": "note", "flagged": False, "resolved": False}],
        }))
        result = runner.invoke(main, ["migrate", "--dry-run"])
        assert result.exit_code == 0
        assert "old" in result.output
        assert "category: infra → chore" in result.output
        assert "agent_notes → comments" in result.output
        # Verify file was NOT modified
        raw = yaml.safe_load((backlog_dir / "old.yaml").read_text())
        assert raw["category"] == "infra"

    def test_migrate_applies_changes(self, runner, backlog_dir):
        (backlog_dir / "old.yaml").write_text(yaml.dump({
            "title": "Old Item", "status": "backlog", "priority": "P2",
            "category": "tech-debt", "agent_notes": [{"text": "note", "flagged": False, "resolved": False}],
        }))
        result = runner.invoke(main, ["migrate"])
        assert result.exit_code == 0
        # Verify file WAS modified
        raw = yaml.safe_load((backlog_dir / "old.yaml").read_text())
        assert raw["category"] == "chore"
        assert "comments" in raw
        assert "agent_notes" not in raw
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_cli.py::TestMigrate -v`

- [ ] **Step 3: Implement migrate command**

In `src/agile_backlog/cli.py`, add (note: the CLI group is `main`, not `cli`; also add `import yaml` and `from agile_backlog.yaml_store import get_backlog_dir` to imports if not already present):

```python
@main.command()
@click.option("--dry-run", is_flag=True, help="Show changes without applying them")
def migrate(dry_run):
    """Migrate YAML files to new schema (categories, comments field)."""
    items = load_all()
    changes = []
    for item in items:
        path = get_backlog_dir() / f"{item.id}.yaml"
        raw = yaml.safe_load(path.read_text())
        item_changes = []

        # Check category migration
        old_cat = raw.get("category", "")
        if old_cat != item.category:
            item_changes.append(f"category: {old_cat} → {item.category}")

        # Check agent_notes → comments
        if "agent_notes" in raw:
            item_changes.append("agent_notes → comments")

        # Check tags added by migration
        old_tags = set(raw.get("tags", []))
        new_tags = set(item.tags)
        added_tags = new_tags - old_tags
        if added_tags:
            item_changes.append(f"tags added: {', '.join(added_tags)}")

        if item_changes:
            changes.append((item.id, item_changes))
            if not dry_run:
                save_item(item)

    if not changes:
        click.echo("No migrations needed.")
        return

    for item_id, item_changes in changes:
        click.echo(f"\n{item_id}:")
        for change in item_changes:
            click.echo(f"  {change}")

    if dry_run:
        click.echo(f"\n{len(changes)} item(s) would be migrated. Run without --dry-run to apply.")
    else:
        click.echo(f"\n{len(changes)} item(s) migrated.")
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `pytest tests/test_cli.py::TestMigrate -v`

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -v`

- [ ] **Step 6: Commit**

```bash
git add src/agile_backlog/cli.py tests/test_cli.py
git commit -m "feat: add migrate CLI command for schema migration with dry-run"
```

---

### Task 15: Run migration on real backlog data

**Files:**
- Modify: `backlog/*.yaml` (via CLI command)

- [ ] **Step 1: Dry run**

Run: `.venv/bin/agile-backlog migrate --dry-run`

Review output — verify category migrations and agent_notes renames look correct.

- [ ] **Step 2: Apply migration**

Run: `.venv/bin/agile-backlog migrate`

- [ ] **Step 3: Verify**

Run: `.venv/bin/agile-backlog list` — confirm all items load correctly.

Run: `pytest tests/ -v` — confirm nothing broke.

- [ ] **Step 4: Commit migrated files**

```bash
git add backlog/
git commit -m "chore: migrate backlog YAML files to new schema"
```

---

### Task 16: Full integration verification

- [ ] **Step 1: Run lint**

Run: `ruff check . && ruff format --check .`

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`

- [ ] **Step 3: Manual smoke test**

Run: `.venv/bin/agile-backlog serve`

Verify all acceptance criteria from the spec:
1. Old YAML files load without error
2. Three sections visible with correct items
3. Move-to buttons work
4. Filtering works on Backlog section only
5. Side panel opens with all details
6. Chat comments display with flag/resolve
7. P0-P4 priorities render correctly
8. Category enum enforced
9. Archive-done replaces show-done checkbox
10. CLI commands work with updated enums

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: integration fixes from smoke testing"
```
