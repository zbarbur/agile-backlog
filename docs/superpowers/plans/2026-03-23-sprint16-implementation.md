# Sprint 16 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Sprint 16 — fix 3 UI bugs, implement backlog section drag-resize, and create the sprint-config.yaml framework foundation.

**Architecture:** Four tasks covering 5 backlog items, executed in order of complexity (S bugs first, then M resize, then L framework). The two S bugs are one-line fixes with tests. The M resize adds JS drag handlers to existing CSS. The L framework integration creates sprint-config.yaml and refactors sprint skills to read from it.

**Tech Stack:** Python 3.11+, NiceGUI, Click CLI, PyYAML, Pydantic, pytest

**Note:** The carryover item `sprint-planning-tool-backlog-sections-drag-and-drop` (Phase 2 — drag-and-drop between columns + keyboard nav) is `doing` in Sprint 16 but is NOT covered in this plan. It has its own specs from Sprint 15 and should be planned separately after Tasks 1-4 are complete.

**Scope note:** Process docs (DEFINITION_OF_DONE.md, AGENTIC_AGILE_MANIFEST.md) are Phase 3 per the framework integration spec but are pulled into Phase 1 here because they are small markdown files and provide immediate value to the sprint process.

---

## File Map

| File | Action | Tasks |
|------|--------|-------|
| `src/agile_backlog/pure.py` | Modify | 2 (line 56 — remove P0/P1 gate) |
| `src/agile_backlog/config.py` | Modify | 4d (read from sprint-config.yaml) |
| `tests/test_pure.py` | Modify | 2 (update + add tests) |
| `tests/test_config.py` | Create | 4d (config migration tests) |
| `src/agile_backlog/components.py` | Modify | 3 (add resize handle elements + JS) |
| `src/agile_backlog/styles.py` | Modify | 3 (resize handle CSS already exists, may need tweaks) |
| `.claude/sprint-config.yaml` | Create | 4 |
| `.claude/skills/sprint-start/SKILL.md` | Modify | 4 |
| `.claude/skills/sprint-end/SKILL.md` | Modify | 4 |
| `docs/process/DEFINITION_OF_DONE.md` | Create | 4 |
| `docs/process/AGENTIC_AGILE_MANIFEST.md` | Create | 4 |
| `.agile-backlog.yaml` | Delete | 4f (migrated to sprint-config.yaml) |

---

## Task 1: Fix Sprint Number Bug (S)

The config file `.agile-backlog.yaml` was already updated to `current_sprint: 16` during sprint setup. The sprint-start skill update to manage `current_sprint` is folded into Task 4b (sprint-start refactoring), since Task 4 replaces `.agile-backlog.yaml` with `sprint-config.yaml` entirely.

**Existing test coverage:** `TestDetectCurrentSprint::test_config_takes_priority` (line 229) already verifies that config values take priority over inference. No duplicate test needed.

**Status:** Config fix already applied. Remaining skill changes handled in Task 4. This task is complete.

---

## Task 2: Fix Priority Color Border (S)

**Files:**
- Modify: `src/agile_backlog/pure.py:56`
- Test: `tests/test_pure.py`

- [ ] **Step 1: Update existing test + write new failing tests for P2-P4 border colors**

First, update the existing test `test_p2_no_left_border` (line 161 of `tests/test_pure.py`) — it currently asserts `transparent` which will break after the fix:

```python
# REPLACE existing test_p2_no_left_border with:
def test_p2_shows_yellow_border(self):
    html = render_card_html(_item(priority="P2"))
    assert "border-left:2px solid #fbbf24" in html
```

Then add new tests for P3 and P4:

```python
def test_p3_shows_gray_border(self):
    html = render_card_html(_item(priority="P3"))
    assert "border-left:2px solid #6b7280" in html

def test_p4_shows_dark_gray_border(self):
    html = render_card_html(_item(priority="P4"))
    assert "border-left:2px solid #4b5563" in html
```

- [ ] **Step 2: Run tests to verify P3/P4 fail** (P2 test also fails since we changed assertion)

Run: `.venv/bin/pytest tests/test_pure.py::TestRenderCardHtml::test_p2_shows_yellow_border tests/test_pure.py::TestRenderCardHtml::test_p3_shows_gray_border tests/test_pure.py::TestRenderCardHtml::test_p4_shows_dark_gray_border -v`
Expected: FAIL — currently returns `transparent` for P2+

- [ ] **Step 3: Fix pure.py line 56**

Change:
```python
bar_color = pri_color[0] if item.priority in ("P0", "P1") else "transparent"
```

To:
```python
bar_color = pri_color[0]
```

- [ ] **Step 4: Run all render_card tests**

Run: `.venv/bin/pytest tests/test_pure.py::TestRenderCardHtml -v`
Expected: ALL PASS

- [ ] **Step 5: Verify existing P0/P1 tests still pass**

Run: `.venv/bin/pytest tests/test_pure.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/agile_backlog/pure.py tests/test_pure.py
git commit -m "fix: show priority color border for all priority levels (P0-P4)"
```

---

## Task 3: Backlog Section Drag Resize (M)

**Files:**
- Modify: `src/agile_backlog/components.py:703-754` — add resize handle elements between sections
- Modify: `src/agile_backlog/styles.py:146-152` — refine resize handle styles if needed

The CSS for `.mc-resize-handle` already exists in styles.py but is never rendered. We need to:
1. Add `<div class="mc-resize-handle">` elements between the three sections
2. Add JavaScript mousedown/mousemove/mouseup handlers for drag-to-resize
3. Update flex values on the section containers during drag

- [ ] **Step 1: Read the current section layout code**

Read `src/agile_backlog/components.py` lines 700-755 to understand the exact flex container structure.

- [ ] **Step 2: Add resize handle elements between sections**

In `components.py`, after the backlog section outer div and before the vNext section, add a resize handle. Same between vNext and vFuture. The handles are NiceGUI `ui.html` elements with the `.mc-resize-handle` class.

```python
# After backlog section, before vNext section:
ui.html('<div class="mc-resize-handle" data-resize="backlog-vnext"></div>')

# After vNext section, before vFuture section:
ui.html('<div class="mc-resize-handle" data-resize="vnext-vfuture"></div>')
```

- [ ] **Step 3: Add JavaScript drag handler**

Add a `ui.run_javascript()` call that sets up mousedown/mousemove/mouseup on `.mc-resize-handle` elements. The JS should:
- On mousedown: record initial Y position and initial flex values of adjacent sections
- On mousemove: calculate delta Y, update flex values proportionally
- On mouseup: remove listeners

```python
RESIZE_JS = """
document.querySelectorAll('.mc-resize-handle').forEach(handle => {
    handle.addEventListener('mousedown', function(e) {
        e.preventDefault();
        const container = handle.parentElement;
        const sections = Array.from(container.querySelectorAll(':scope > div:not(.mc-resize-handle)'));
        const idx = Array.from(container.children).indexOf(handle);
        // Section above the handle (index-wise: handle is between section pairs)
        const above = container.children[idx - 1];
        const below = container.children[idx + 1];
        if (!above || !below) return;
        const startY = e.clientY;
        const startAboveH = above.getBoundingClientRect().height;
        const startBelowH = below.getBoundingClientRect().height;
        const totalH = startAboveH + startBelowH;

        function onMove(ev) {
            const dy = ev.clientY - startY;
            const newAbove = Math.max(44, startAboveH + dy);
            const newBelow = Math.max(44, startBelowH - dy);
            above.style.flex = '0 0 ' + newAbove + 'px';
            below.style.flex = '0 0 ' + newBelow + 'px';
        }
        function onUp() {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
});
"""
```

- [ ] **Step 4: Inject the JS after the layout renders**

After the section layout is built (end of `_render_backlog_list`), add:
```python
ui.timer(0.1, lambda: ui.run_javascript(RESIZE_JS), once=True)
```

- [ ] **Step 5: Verify zoom still works**

Zoom toggles flex values on sections. After a drag resize, zoom should still work (it sets explicit flex values which override the drag values). Test manually:
1. Drag resize between backlog and vNext
2. Click zoom on vNext — should expand fully
3. Click zoom again — should return to pre-zoom sizes

- [ ] **Step 6: Run all tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS (no new tests needed — this is JS-only behavior)

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/components.py
git commit -m "feat: add drag-to-resize between backlog sections"
```

---

## Task 4: Framework Integration — sprint-config.yaml + Skill Refactoring (L)

**Files:**
- Create: `.claude/sprint-config.yaml`
- Modify: `.claude/skills/sprint-start/SKILL.md`
- Modify: `.claude/skills/sprint-end/SKILL.md`
- Create: `docs/process/DEFINITION_OF_DONE.md`
- Create: `docs/process/AGENTIC_AGILE_MANIFEST.md`

This is Phase 1 of the framework integration spec (`docs/superpowers/specs/2026-03-23-agentic-agile-framework-integration.md`). We're making sprint skills config-driven so they can be reused across projects.

### Sub-task 4a: Create sprint-config.yaml

- [ ] **Step 1: Create the config file**

```yaml
# .claude/sprint-config.yaml
# Project Sprint Configuration — read by all sprint skills

project_name: agile-backlog
language: python
python_version: "3.11+"

# Current sprint
current_sprint: 16

# Commands
test_command: ".venv/bin/pytest tests/ -v"
lint_command: ".venv/bin/ruff check . && .venv/bin/ruff format --check ."
format_command: ".venv/bin/ruff format ."
ci_command: ".venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v"

# Backlog tool
backlog_tool: agile-backlog
backlog_commands:
  list: ".venv/bin/agile-backlog list"
  list_doing: ".venv/bin/agile-backlog list --status doing"
  list_done: ".venv/bin/agile-backlog list --status done"
  list_backlog: ".venv/bin/agile-backlog list --status backlog"
  list_bugs: ".venv/bin/agile-backlog list --category bug --status backlog"
  show: ".venv/bin/agile-backlog show {id}"
  add: ".venv/bin/agile-backlog add \"{title}\" --category {category} --priority {priority}"
  move: ".venv/bin/agile-backlog move {id} --status {status}"
  edit: ".venv/bin/agile-backlog edit {id}"
  flagged: ".venv/bin/agile-backlog flagged"

# Documentation paths
docs:
  handover_dir: "docs/sprints/"
  specs_dir: "docs/superpowers/specs/"
  plans_dir: "docs/superpowers/plans/"
  project_context: "docs/process/PROJECT_CONTEXT.md"
  definition_of_done: "docs/process/DEFINITION_OF_DONE.md"

# Branch conventions
branch_pattern: "sprint{N}/main"
commit_style: conventional

# Sprint settings
default_sprint_capacity:
  small: 3-4
  medium: 2-3
  large: 1-2
```

- [ ] **Step 2: Commit config**

```bash
git add .claude/sprint-config.yaml
git commit -m "feat: add sprint-config.yaml — project config for generic sprint skills"
```

### Sub-task 4b: Refactor sprint-start skill

- [ ] **Step 3: Read current sprint-start skill**

Read `.claude/skills/sprint-start/SKILL.md` fully.

- [ ] **Step 4: Refactor sprint-start to use config references**

Replace all hardcoded commands with references to sprint-config.yaml. The skill should instruct the agent to:
1. Read `.claude/sprint-config.yaml` at the start
2. Use `{ci_command}` instead of hardcoded `ruff check . && ...`
3. Use `{backlog_commands.list}` instead of `agile-backlog list`
4. Use `{branch_pattern}` instead of hardcoded `sprintN/main`
5. Update `current_sprint` in sprint-config.yaml (replacing .agile-backlog.yaml)

Key changes:
- Add a preamble: "Read `.claude/sprint-config.yaml` to get project-specific commands"
- Replace all `agile-backlog` commands with `{backlog_commands.X}` placeholders
- Replace `ruff check . && ruff format --check . && pytest tests/ -v` with `{ci_command}`
- In Step 6, update `current_sprint` in sprint-config.yaml instead of .agile-backlog.yaml

- [ ] **Step 5: Commit sprint-start refactor**

```bash
git add .claude/skills/sprint-start/
git commit -m "refactor: sprint-start skill reads from sprint-config.yaml"
```

### Sub-task 4c: Refactor sprint-end skill

- [ ] **Step 6: Read current sprint-end skill**

Read `.claude/skills/sprint-end/SKILL.md` fully.

- [ ] **Step 7: Refactor sprint-end to use config references**

Same pattern as sprint-start:
1. Read `.claude/sprint-config.yaml` at the start
2. Use config commands instead of hardcoded ones
3. Use `{docs.handover_dir}` for handover path
4. Use `{docs.project_context}` for PROJECT_CONTEXT path

- [ ] **Step 8: Commit sprint-end refactor**

```bash
git add .claude/skills/sprint-end/
git commit -m "refactor: sprint-end skill reads from sprint-config.yaml"
```

### Sub-task 4d: Migrate from .agile-backlog.yaml to sprint-config.yaml

- [ ] **Step 9: Update config.py to read AND write from sprint-config.yaml**

Modify `src/agile_backlog/config.py` to read/write `current_sprint` from `.claude/sprint-config.yaml` instead of `.agile-backlog.yaml`. Keep `.agile-backlog.yaml` as read fallback for backwards compatibility.

```python
def _sprint_config_path() -> Path:
    from agile_backlog.yaml_store import _git_root
    return _git_root() / ".claude" / "sprint-config.yaml"

def get_current_sprint() -> int | None:
    # Try sprint-config.yaml first
    sprint_config = _sprint_config_path()
    if sprint_config.exists():
        data = yaml.safe_load(sprint_config.read_text()) or {}
        if "current_sprint" in data:
            return data["current_sprint"]
    # Fallback to .agile-backlog.yaml
    path = _config_path()
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("current_sprint")

def set_current_sprint(sprint: int | None) -> None:
    # Always write to sprint-config.yaml (new canonical location)
    path = _sprint_config_path()
    data = {}
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
    if sprint is None:
        data.pop("current_sprint", None)
    else:
        data["current_sprint"] = sprint
    path.write_text(yaml.dump(data, default_flow_style=False))
```

- [ ] **Step 10: Write tests for new config paths**

Create `tests/test_config.py`:

```python
from agile_backlog.config import get_current_sprint, set_current_sprint

def test_get_current_sprint_from_sprint_config(tmp_path, monkeypatch):
    """sprint-config.yaml is the primary source."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("current_sprint: 16\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    monkeypatch.setattr("agile_backlog.config._config_path", lambda: tmp_path / "nonexistent.yaml")
    assert get_current_sprint() == 16

def test_get_current_sprint_fallback_to_agile_backlog_yaml(tmp_path, monkeypatch):
    """Falls back to .agile-backlog.yaml when sprint-config.yaml missing."""
    legacy = tmp_path / ".agile-backlog.yaml"
    legacy.write_text("current_sprint: 14\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: tmp_path / "nonexistent.yaml")
    monkeypatch.setattr("agile_backlog.config._config_path", lambda: legacy)
    assert get_current_sprint() == 14

def test_get_current_sprint_none_when_no_config(tmp_path, monkeypatch):
    """Returns None when neither config file exists."""
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: tmp_path / "nope1.yaml")
    monkeypatch.setattr("agile_backlog.config._config_path", lambda: tmp_path / "nope2.yaml")
    assert get_current_sprint() is None

def test_set_current_sprint_writes_to_sprint_config(tmp_path, monkeypatch):
    """set_current_sprint writes to sprint-config.yaml."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("project_name: test\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    set_current_sprint(17)
    import yaml
    data = yaml.safe_load(config.read_text())
    assert data["current_sprint"] == 17
    assert data["project_name"] == "test"  # preserves other fields
```

- [ ] **Step 11: Run all tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 12: Commit config migration**

```bash
git add src/agile_backlog/config.py tests/test_config.py
git commit -m "feat: read/write current_sprint from sprint-config.yaml with .agile-backlog.yaml fallback"
```

### Sub-task 4e: Adopt process docs

- [ ] **Step 13: Create DEFINITION_OF_DONE.md**

Adopt from the agentic-agile-template, genericized for any project. Reference `{ci_command}` pattern.

```markdown
# Definition of Done

A task is "done" when ALL of the following are true:

## Code Quality
- [ ] All acceptance criteria verified against actual codebase (not just "I think it works")
- [ ] Tests pass: run `{test_command}` from sprint-config.yaml
- [ ] Lint clean: run `{lint_command}` from sprint-config.yaml
- [ ] No commented-out code, no TODO/FIXME left behind
- [ ] No hardcoded secrets, API keys, or credentials

## Testing
- [ ] New functionality has tests
- [ ] Edge cases covered (empty inputs, error states, boundary values)
- [ ] Tests are independent and repeatable

## Documentation
- [ ] Code is self-documenting (clear names, obvious flow)
- [ ] Complex logic has inline comments explaining WHY, not WHAT
- [ ] Public APIs have docstrings

## Review
- [ ] Changes reviewed (self-review minimum, peer review preferred)
- [ ] No unrelated changes bundled in
- [ ] Commit messages follow project conventions
```

- [ ] **Step 14: Create AGENTIC_AGILE_MANIFEST.md**

```markdown
# Agentic Agile Manifest

## Core Principles

1. **Research first, design second, code third** — validate before building
2. **Quality review at every stage** — spec review, plan review, code review
3. **YAML items are the single source of truth** — not TODO.md, not KANBAN.md
4. **Sprint skills are config-driven** — one sprint-config.yaml per project
5. **Specialists enhance, reviewers verify** — separation of concerns

## Process Flow

```
Backlog → Sprint Start → Spec → Plan → Build → Review → Done → Sprint End
```

## Context System

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project rules and code style |
| `.claude/MEMORY.md` | Agent memory across sessions |
| `.claude/sprint-config.yaml` | Sprint configuration |
| `docs/process/PROJECT_CONTEXT.md` | Project snapshot |
| `docs/process/DEFINITION_OF_DONE.md` | Quality gates |
| `backlog/*.yaml` | Backlog items (source of truth) |

## Sprint Cadence

1. `/sprint-start N` — scope, spec, branch
2. Build — TDD, frequent commits
3. `/sprint-end` — verify DoD, handover, merge, clean up
```

- [ ] **Step 15: Commit process docs**

```bash
git add docs/process/DEFINITION_OF_DONE.md docs/process/AGENTIC_AGILE_MANIFEST.md
git commit -m "docs: adopt DEFINITION_OF_DONE and AGENTIC_AGILE_MANIFEST from template"
```

### Sub-task 4f: Clean up .agile-backlog.yaml

- [ ] **Step 16: Remove .agile-backlog.yaml** (current_sprint now lives in sprint-config.yaml)

```bash
git rm .agile-backlog.yaml
git commit -m "chore: remove .agile-backlog.yaml — current_sprint moved to sprint-config.yaml"
```

- [ ] **Step 17: Run full CI**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
Expected: ALL PASS

---

## Execution Order

| Order | Task | Complexity | Deps |
|-------|------|-----------|------|
| 1 | Priority border fix (Task 2) | S | None |
| 2 | Backlog drag resize (Task 3) | M | None |
| 3 | Framework integration (Task 4) | L | None (absorbs Task 1) |

Task 1 (sprint number bug) is already resolved — config updated, remaining skill changes folded into Task 4b. Tasks 2 and 3 are independent and can be parallelized.
