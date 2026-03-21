# NiceGUI Migration Spec

> **Date:** 2026-03-21
> **Type:** Implementation spec
> **Status:** Draft
> **Depends on:** [Frontend Evaluation](2026-03-21-frontend-evaluation.md), [Design System](2026-03-21-design-system.md)

---

## 1. Component Mapping Table

Every Streamlit widget used in `src/app.py` and its NiceGUI replacement.

| Streamlit Widget | NiceGUI Equivalent | Notes |
|---|---|---|
| `st.set_page_config(layout="wide")` | `@ui.page('/')` + `ui.query('body').classes(...)` | Page config via decorator and Tailwind classes |
| `st.markdown(html, unsafe_allow_html=True)` | `ui.html(html)` | Direct HTML rendering, no `unsafe_allow_html` flag needed |
| `st.markdown(css_style_block)` | `ui.add_head_html('<style>...</style>')` | Or use Tailwind classes directly on elements |
| `st.columns(n)` | `ui.row()` containing `ui.column()` elements | Full CSS control via `.classes()` and `.style()` |
| `st.container(border=True)` | `ui.card()` | Quasar QCard with built-in border, shadow, padding |
| `st.expander(label)` | `ui.expansion(label)` | Quasar QExpansionItem, same click-to-toggle pattern |
| `st.selectbox(label, options)` | `ui.select(label, options)` | Quasar QSelect with search, custom rendering |
| `st.text_input(label)` | `ui.input(label)` | Quasar QInput with placeholder support |
| `st.button(label, key=...)` | `ui.button(label, on_click=handler)` | Event callback instead of rerun-based check |
| `st.caption(text)` | `ui.label(text).classes('text-xs text-gray-400')` | Styled label with Tailwind |
| `st.rerun()` | *(not needed)* | NiceGUI updates UI reactively via callbacks |
| `st.session_state` | Python instance variables / module-level state | Persistent process means normal Python state works |

### Example: Select box

**Streamlit:**
```python
priority_filter = st.selectbox("Priority", [None, "P1", "P2+", "P3+"],
                               format_func=lambda x: labels.get(x, str(x)))
```

**NiceGUI:**
```python
priority_filter = ui.select(
    label="Priority",
    options={None: "All priorities", "P1": "P1 only", "P2+": "P1 & P2", "P3+": "All (P1-P3)"},
    value=None,
    on_change=lambda e: refresh_board(),
)
```

### Example: Card with HTML content

**Streamlit:**
```python
with st.container(border=True):
    st.markdown(render_card_html(item), unsafe_allow_html=True)
```

**NiceGUI:**
```python
with ui.card().classes('w-full'):
    ui.html(render_card_html(item))
```

### Example: Move button with callback

**Streamlit:**
```python
if st.button(f"{arrow} {target}", key=f"move_{item.id}_{target}"):
    item.status = target
    save_item(item)
    st.rerun()
```

**NiceGUI:**
```python
def move_item(item: BacklogItem, target: str):
    item.status = target
    if target == "doing":
        item.phase = item.phase or "plan"
    else:
        item.phase = None
    save_item(item)
    board_container.refresh()

ui.button(f"{arrow} {target}", on_click=lambda: move_item(item, target))
```

---

## 2. Feature Parity Checklist

Every behavior in the current `src/app.py` that must be preserved in the NiceGUI rewrite.

### Filters

- [ ] **Priority filter** — selectbox with options: All, P1, P2+ (P1 & P2), P3+ (all). Range logic via `PRIORITY_ORDER` dict; `P2+` means `PRIORITY_ORDER[priority] <= PRIORITY_ORDER["P2"]`.
- [ ] **Category filter** — selectbox populated dynamically from all items' categories, sorted. Includes "All categories" option.
- [ ] **Sprint filter** — selectbox with: All, Unplanned (items with `sprint_target is None`), then each sprint number from data. Sprint filter applies to **all three columns** (backlog, doing, done). Other filters apply to backlog only.
- [ ] **Search filter** — text input. Matches against `title`, `description`, and `tags` (case-insensitive substring). Applies to backlog only.
- [ ] **AND combination** — all active filters combine with AND logic.
- [ ] **Sprint filter on doing/done** — when sprint is set (including "unplanned"), doing and done columns are filtered directly (not through `filter_items`).

### Card Rendering

- [ ] **Title** — 14px, weight 600, color `#111827`, line-height 1.35.
- [ ] **Category badge** — uppercase, colored text on colored bg per `CATEGORY_STYLES` map. Unknown categories fall back to gray.
- [ ] **Priority badge** — uppercase, colored per `PRIORITY_COLORS` map.
- [ ] **Phase badge** — italic, gray text on gray bg. Only shown when `item.phase` is not None.
- [ ] **Review badges** — small green checkmark badges for `design_reviewed` and `code_reviewed` when True. Not shown when False.
- [ ] **Sprint badge** — outlined style (`background:none; border:1px solid #e5e7eb`). Shows `S{n}`. Only shown when `sprint_target` is not None.
- [ ] **Badge order** — category, priority, phase, review flags, sprint.
- [ ] **P1 left border accent** — `border-left: 3px solid #ef4444` on P1 cards.
- [ ] **Done cards dimmed** — opacity 0.5, title gets `line-through` and muted color. Hover restores opacity to 1.

### Move Buttons

- [ ] **Two buttons per card** — one for each other status (not the current one).
- [ ] **Directional arrows** — `←` for leftward moves, `→` for rightward moves.
- [ ] **Phase auto-set** — moving to "doing" sets `phase = item.phase or "plan"` (preserves existing phase, defaults to "plan").
- [ ] **Phase clear** — moving to "backlog" or "done" sets `phase = None`.
- [ ] **Save and refresh** — `save_item(item)` then UI refresh.

### Detail Expander

- [ ] **Label** — item ID (slug).
- [ ] **Goal** — shown first if present, bold label.
- [ ] **Complexity** — HTML badge (S/M/L) with colored background.
- [ ] **Description** — markdown-rendered.
- [ ] **Acceptance Criteria** — bullet list if present.
- [ ] **Technical Specs** — bullet list if present.
- [ ] **Test Plan** — bullet list if present.
- [ ] **Notes** — plain text if present.
- [ ] **Tags** — rendered as small gray pills (inline HTML).
- [ ] **Depends on** — comma-separated item IDs.
- [ ] **Footer row** — three columns: Sprint, Created date, Updated date.

### Layout and Chrome

- [ ] **Page title** — "agile-backlog" with sprint indicator (e.g., "· Sprint 3") when detected.
- [ ] **Sprint detection** — `detect_current_sprint()`: most common `sprint_target` among "doing" items.
- [ ] **Three columns** — Backlog, In Progress, Done.
- [ ] **Column headers** — uppercase label with count badge.
- [ ] **Column backgrounds** — backlog: `#f9fafb`, doing: `#fffbeb`, done: `#f0fdf4`.
- [ ] **Empty column messages** — backlog shows "No items match filters." (or add hint if no items at all). Doing/done show "No items."
- [ ] **Filter bar** — four controls in a row with bottom border separator.

---

## 3. NiceGUI Architecture

### Execution Model

NiceGUI runs a persistent Python process (FastAPI + uvicorn). Unlike Streamlit, the entire script does **not** re-execute on every interaction. Instead:

- The page function runs **once per client connection**. Each browser tab gets its own invocation of `kanban_page()`, with its own local variables and widget instances. This means filter state is inherently per-client — no cross-user state collision.
- UI updates happen through **event callbacks** (e.g., `on_click`, `on_change`).
- State is normal Python variables — no `st.session_state` needed. **Important:** Use local variables inside `kanban_page()`, not module-level state, to avoid shared mutable state between connections.
- To re-render a section of the UI, use `@ui.refreshable` decorator and call `.refresh()`.

### App Structure

```python
from nicegui import ui
from src.yaml_store import load_all, save_item
from src.models import BacklogItem

@ui.page('/')
def kanban_page():
    # State: Python variables
    filters = {"priority": None, "category": None, "sprint": None, "search": ""}

    @ui.refreshable
    def render_board():
        all_items = load_all()
        # ... filter logic, render columns ...

    # Filter bar
    with ui.row().classes('w-full gap-4 pb-3 border-b'):
        ui.select(..., on_change=lambda: render_board.refresh())
        # ...

    render_board()

ui.run(title='agile-backlog', port=8501)
```

### State Management

| Streamlit | NiceGUI |
|---|---|
| `st.session_state["priority"]` | `filters["priority"]` (dict) or `priority_select.value` (widget value) |
| Survives rerun | Survives for connection lifetime (persistent process) |
| Cleared on page refresh | Cleared on page refresh (same behavior) |

Filter state can be read directly from widget `.value` properties. No separate state dict is strictly necessary — the select/input widgets hold their own values.

### How Filter Changes Trigger UI Updates

1. Each filter widget has `on_change=lambda: render_board.refresh()`.
2. `render_board.refresh()` clears and re-renders the `@ui.refreshable` function.
3. Inside `render_board()`, we read `priority_select.value`, `category_select.value`, etc.
4. Data is re-loaded from YAML, filters applied, columns rendered.

### How Move Buttons Update State and Refresh

1. Button `on_click` calls `move_item(item, target_status)`.
2. `move_item()` updates `item.status`, sets/clears `item.phase`, calls `save_item(item)`.
3. Calls `render_board.refresh()` to re-render the board with updated data.

---

## 4. Drag-and-Drop Approach

### What NiceGUI Actually Supports

NiceGUI does **not** have a built-in `ui.sortable` component. Quasar's sortable capabilities are limited. The community approach is to integrate [SortableJS](https://github.com/SortableJS/Sortable) via `ui.add_head_html()` and JavaScript interop.

### SortableJS Integration Pattern

```python
from nicegui import ui

# Load SortableJS from CDN
ui.add_head_html('<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>')

@ui.page('/')
def page():
    with ui.row().classes('w-full gap-4') as board:
        for status in ['backlog', 'doing', 'done']:
            with ui.column().classes('sortable-column') as col:
                col.props(f'data-status="{status}"')
                # ... render cards with data-item-id attributes ...

    # Initialize SortableJS on each column
    ui.run_javascript('''
        document.querySelectorAll('.sortable-column').forEach(col => {
            Sortable.create(col, {
                group: 'kanban',
                animation: 150,
                ghostClass: 'opacity-30',
                onEnd: function(evt) {
                    const itemId = evt.item.dataset.itemId;
                    const newStatus = evt.to.dataset.status;
                    // Call Python via NiceGUI's JS-to-Python bridge
                    emitEvent('move_item', {item_id: itemId, status: newStatus});
                }
            });
        });
    ''')
```

### What Happens on Drop

1. SortableJS `onEnd` fires with the item ID and target column status.
2. JavaScript calls back to Python via `emitEvent` / `ui.on()`.
3. Python handler: load item, update status, apply phase logic (set "plan" for doing, clear for backlog/done), call `save_item()`.
4. Refresh the board to reflect persisted state.

### Phased Approach (Recommended)

**Sprint 7 — Move buttons only (feature parity):**
- Keep the existing move button pattern. This already works and is well-tested.
- Focus migration effort on the core rewrite.

**Sprint 8 — Add drag-and-drop as enhancement:**
- Layer SortableJS on top of the working board.
- Drag-and-drop supplements move buttons (both work).
- If DnD proves fragile with `@ui.refreshable` re-renders, move buttons remain the reliable path.

### Known Risk

SortableJS operates on the DOM. When `@ui.refreshable` re-renders the board, DOM elements are replaced. SortableJS instances must be re-initialized after each refresh. This can be handled by running `ui.run_javascript(init_sortable_script)` at the end of `render_board()`.

---

## 5. Serve Command

### Current Implementation

```python
# src/cli.py serve command
@main.command()
def serve():
    """Open the Kanban board in the browser."""
    import subprocess
    import sys
    from pathlib import Path
    app_path = Path(__file__).parent / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
```

This spawns a separate Streamlit process via `subprocess.run`. The CLI blocks until Streamlit exits.

### New Implementation

```python
@main.command()
@click.option("--port", default=8501, type=int, help="Port number.")
@click.option("--host", default="127.0.0.1", help="Host address.")
def serve(port: int, host: str):
    """Open the Kanban board in the browser."""
    from src.app import run_app
    run_app(host=host, port=port)
```

In `src/app.py`:

```python
def run_app(host: str = "127.0.0.1", port: int = 8501):
    """Start the NiceGUI Kanban board server."""
    # Page registration happens at import time via @ui.page decorator
    ui.run(title="agile-backlog", host=host, port=port, reload=False)
```

### Key Differences

| Aspect | Streamlit (old) | NiceGUI (new) |
|---|---|---|
| Process model | `subprocess.run` spawns separate process | Direct Python call in same process |
| Blocking | Blocks on subprocess | Blocks on `ui.run()` (uvicorn event loop) |
| Port | Streamlit default 8501 | Configurable, default 8501 for continuity |
| Auto-open browser | Streamlit opens browser automatically | NiceGUI opens browser automatically via `ui.run()` |
| Reload | Streamlit has built-in hot reload | NiceGUI has `reload=True` option (dev only) |

### Impact on CLI Architecture

- No more `subprocess` import needed in `serve`.
- The `app.py` module must be importable without side effects — `ui.run()` must only be called from `run_app()`, not at module level.
- The `@ui.page('/')` decorator registers the page at import time, which is fine.

---

## 6. Testing Strategy

### Pure Functions That Survive Unchanged

These functions have no UI dependencies and keep their existing tests in `tests/test_app.py`:

| Function | What It Does | Test Status |
|---|---|---|
| `category_style(category)` | Returns `(text_color, bg_color)` tuple | Tests unchanged |
| `filter_items(items, ...)` | Applies filter logic, returns filtered list | Tests unchanged |
| `detect_current_sprint(items)` | Returns most common sprint from doing items | Tests unchanged |
| `render_card_html(item)` | Generates HTML string for card | Tests unchanged (HTML output is framework-agnostic) |
| `_complexity_badge(complexity)` | Returns HTML string for complexity badge | Can add tests |

These functions produce strings and lists — they do not depend on Streamlit or NiceGUI. The existing 40+ tests in `TestCategoryStyle`, `TestFilterItems`, `TestRenderCardHtml`, and `TestDetectCurrentSprint` all pass without modification.

### What Changes in Tests

The current `tests/test_app.py` tests pure functions only — there are no Streamlit integration tests. This means **no test rewriting is needed** for the migration. The test file stays as-is.

**Import side effects:** The `@ui.page('/')` decorator in `src/app.py` registers a route at import time. However, NiceGUI's page registration is inert without `ui.run()` being called — it merely stores the route in a registry. This means `from src.app import category_style` in tests will not trigger a server or cause side effects. If this assumption breaks in a future NiceGUI version, extract pure functions to `src/board_logic.py` and import from there in tests.

If we add UI integration tests (new), they would use NiceGUI's testing framework:

### NiceGUI Testing Options

**Option A: `nicegui.testing` User fixture (recommended for CI)**

NiceGUI provides a `User` fixture that simulates browser interaction entirely in Python — no browser needed. Fast, runs in pytest.

```python
from nicegui.testing import User

async def test_board_renders_columns(user: User):
    await user.open('/')
    await user.should_see('BACKLOG')
    await user.should_see('IN PROGRESS')
    await user.should_see('DONE')
```

Requires: `pytest-asyncio` in dev dependencies. Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` in `pyproject.toml`.

**Option B: `nicegui.testing` Screen fixture (browser-based)**

Uses Selenium/ChromeDriver for full browser testing. Slower, useful for visual regression.

**Option C: Playwright (external)**

Full E2E testing with Playwright. Most realistic but heaviest.

### Recommended Test Pyramid

1. **Unit tests** (existing, fast) — `filter_items`, `category_style`, `render_card_html`, `detect_current_sprint`. Already done.
2. **Component tests** (new, medium) — Use `nicegui.testing.User` to verify page renders, filters work, move buttons update state.
3. **E2E tests** (optional, slow) — Playwright if drag-and-drop needs browser-level testing.

### Regression Checklist

After migration, verify manually (or with integration tests):

- [ ] Board loads with three columns
- [ ] Cards render with correct badges (category, priority, phase, sprint, review)
- [ ] P1 cards have red left border
- [ ] Done cards are dimmed with strikethrough
- [ ] Priority filter with range (P2+) works
- [ ] Sprint filter applies to all columns
- [ ] Category/search filters apply to backlog only
- [ ] "Unplanned" sprint filter shows items with no sprint
- [ ] Move buttons update status and phase correctly
- [ ] Expander shows all detail fields
- [ ] Empty column messages display correctly
- [ ] Sprint indicator in page header updates

---

## 7. Design Tokens (Framework-Agnostic)

Extract all design values from the design system as Python constants. These work with both `render_card_html()` (inline HTML) and NiceGUI Tailwind classes.

### Token Module: `src/tokens.py`

```python
"""Design tokens for the agile-backlog UI. Framework-agnostic Python constants."""

# --- Category colors: (text_color, bg_color) ---
CATEGORY_STYLES: dict[str, tuple[str, str]] = {
    "bug": ("#be185d", "#fce7f3"),
    "feature": ("#1d4ed8", "#dbeafe"),
    "tech-debt": ("#92400e", "#fef3c7"),
    "docs": ("#065f46", "#d1fae5"),
    "security": ("#5b21b6", "#ede9fe"),
    "infra": ("#155e75", "#cffafe"),
}
CATEGORY_DEFAULT: tuple[str, str] = ("#4b5563", "#f3f4f6")

# --- Priority colors: (text_color, bg_color) ---
PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "P1": ("#dc2626", "#fef2f2"),
    "P2": ("#2563eb", "#eff6ff"),
    "P3": ("#d97706", "#fffbeb"),
}
PRIORITY_ORDER: dict[str, int] = {"P1": 1, "P2": 2, "P3": 3}
P1_ACCENT: str = "#ef4444"

# --- Phase colors ---
PHASE_TEXT: str = "#6b7280"
PHASE_BG: str = "#f3f4f6"

# --- Sprint badge ---
SPRINT_TEXT: str = "#6b7280"
SPRINT_BORDER: str = "#e5e7eb"

# --- Review badge ---
REVIEW_TEXT: str = "#059669"
REVIEW_BG: str = "#d1fae5"

# --- Column backgrounds ---
COLUMN_BG: dict[str, str] = {
    "backlog": "#f9fafb",
    "doing": "#fffbeb",
    "done": "#f0fdf4",
}

# --- Chrome / UI ---
COLOR_BORDER: str = "#e5e7eb"
COLOR_TEXT_PRIMARY: str = "#111827"
COLOR_TEXT_SECONDARY: str = "#6b7280"
COLOR_TEXT_MUTED: str = "#9ca3af"
COLOR_BG_CARD: str = "#ffffff"

# --- Sizing ---
CARD_BORDER_RADIUS: str = "8px"
BADGE_BORDER_RADIUS: str = "4px"
BADGE_HEIGHT: str = "20px"
BADGE_FONT_SIZE: str = "11px"
TITLE_FONT_SIZE: str = "14px"

# --- Complexity badge colors ---
COMPLEXITY_COLORS: dict[str, tuple[str, str]] = {
    "S": ("#065f46", "#d1fae5"),
    "M": ("#92400e", "#fef3c7"),
    "L": ("#dc2626", "#fef2f2"),
}
```

### Migration Path

1. Create `src/tokens.py` with the constants above.
2. Update `src/app.py` to import from `src.tokens` instead of defining `CATEGORY_STYLES`, `PRIORITY_COLORS`, `PRIORITY_ORDER` inline.
3. The `render_card_html()` function and `_complexity_badge()` use these tokens for inline styles (works identically in NiceGUI's `ui.html()`).
4. NiceGUI-specific styling (Tailwind classes, Quasar props) references the same token values where inline styles are not used.

### Tailwind Class Mapping

For NiceGUI components styled via Tailwind (not inline HTML), map tokens to Tailwind classes:

| Token | Tailwind Class |
|---|---|
| Column bg backlog `#f9fafb` | `bg-gray-50` |
| Column bg doing `#fffbeb` | `bg-amber-50` |
| Column bg done `#f0fdf4` | `bg-green-50` |
| Text primary `#111827` | `text-gray-900` |
| Text secondary `#6b7280` | `text-gray-500` |
| Text muted `#9ca3af` | `text-gray-400` |
| Border `#e5e7eb` | `border-gray-200` |

---

## 8. Files Changed

### Create

| File | Purpose |
|---|---|
| `src/tokens.py` | Design tokens as Python constants (extracted from app.py) |

### Modify

| File | Change |
|---|---|
| `src/app.py` | **Complete rewrite** — replace Streamlit with NiceGUI. Keep pure functions (`filter_items`, `category_style`, `render_card_html`, `detect_current_sprint`, `_complexity_badge`). Replace `main()` with `@ui.page('/')` function and `run_app()` entry point. Import tokens from `src.tokens`. |
| `src/cli.py` | Update `serve` command: remove `subprocess` call, import `run_app` from `src.app`, add `--port` and `--host` options. |
| `pyproject.toml` | Replace `streamlit>=1.30.0` and `streamlit-sortables>=0.3.0` with `nicegui>=2.0.0`. Add `pytest-asyncio>=0.23.0` to dev deps (for NiceGUI testing). |
| `CLAUDE.md` | Update run commands (Streamlit -> NiceGUI), dependency list. |
| `tests/test_app.py` | **No changes needed** — all tests exercise pure functions that are framework-independent. |

### Delete

| File | Reason |
|---|---|
| `.streamlit/config.toml` | Streamlit config no longer needed. (Check if it exists first.) |

### Modify

| File | Change |
|---|---|
| `tests/test_cli.py` | Update the serve test — mock `run_app()` instead of `subprocess.run` |

### Unchanged

| File | Reason |
|---|---|
| `src/models.py` | Data model — no UI dependency |
| `src/yaml_store.py` | Data layer — no UI dependency |
| `tests/test_models.py` | Tests pure model logic |
| `tests/test_yaml_store.py` | Tests YAML I/O |
| `backlog/*.yaml` | Data files |
| `plugin/` | Claude Code plugin — no changes |

---

## 9. Dependencies

### pyproject.toml Changes

**Remove:**
```
"streamlit>=1.30.0",
"streamlit-sortables>=0.3.0",
```

**Add:**
```
"nicegui>=2.0.0",
```

**Dev deps add:**
```
"pytest-asyncio>=0.23.0",
```

### Transitive Dependencies

NiceGUI pulls in these notable transitive dependencies:

| Package | Role | Concern |
|---|---|---|
| `fastapi` | ASGI framework, NiceGUI's server layer | Well-maintained, no conflict expected |
| `uvicorn` | ASGI server | Production-grade, used by NiceGUI's `ui.run()` |
| `starlette` | ASGI toolkit (FastAPI dependency) | Indirect |
| `python-socketio` | WebSocket communication (UI ↔ server) | Required for NiceGUI's real-time updates |
| `httptools` / `uvloop` | Optional uvicorn performance deps | May install on Linux |
| `itsdangerous` | Session security | FastAPI/Starlette dependency |

### Net Dependency Impact

- **Removed:** `streamlit` (heavy: pulls in `altair`, `pandas`, `numpy`, `pyarrow`, `protobuf`, `tornado`, etc.)
- **Added:** `nicegui` (lighter: `fastapi`, `uvicorn`, `python-socketio`, Tailwind/Quasar bundled)
- **Net effect:** Significantly fewer total packages. Streamlit's dependency tree is much larger than NiceGUI's.

### Dependabot Config

If `.github/dependabot.yml` exists, no changes needed — it already monitors pip dependencies. If adding one:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 10. Migration Steps (Ordered)

### Step 1: Create `src/tokens.py`

Extract `CATEGORY_STYLES`, `PRIORITY_COLORS`, `PRIORITY_ORDER`, and other color/sizing constants from `src/app.py` into `src/tokens.py`. Update `src/app.py` to import from tokens. Run tests — all should pass (no behavior change).

### Step 2: Update `pyproject.toml`

Replace streamlit dependencies with nicegui. Install with `pip install -e ".[dev]"`.

```diff
 dependencies = [
-    "streamlit>=1.30.0",
-    "streamlit-sortables>=0.3.0",
+    "nicegui>=2.0.0",
     "pyyaml>=6.0.0",
     "click>=8.1.0",
     "pydantic>=2.0.0",
 ]
```

### Step 3: Rewrite `src/app.py` — Skeleton

Keep all pure functions (`filter_items`, `category_style`, `render_card_html`, `detect_current_sprint`, `_complexity_badge`). Replace `main()` with:

```python
from nicegui import ui

@ui.page('/')
def kanban_page():
    # Header
    # Filter bar
    # Board (three columns)
    pass

def run_app(host: str = "127.0.0.1", port: int = 8501):
    ui.run(title="agile-backlog", host=host, port=port, reload=False)
```

Run tests — pure function tests should still pass.

### Step 4: Implement Filter Bar

Build the four filter controls using `ui.select` and `ui.input`. Wire `on_change` to `render_board.refresh()`.

### Step 5: Implement Board Columns

Implement `@ui.refreshable render_board()` that:
1. Loads items from YAML.
2. Applies filters (reading from widget `.value`).
3. Renders three columns with headers, cards, expanders, and move buttons.

### Step 6: Implement Card Rendering

Reuse `render_card_html()` via `ui.html()` inside `ui.card()`. Add done-card styling with Tailwind/CSS classes. Add move buttons with `on_click` callbacks.

### Step 7: Implement Detail Expander

Use `ui.expansion(item.id)` containing goal, complexity, description, acceptance criteria, technical specs, test plan, notes, tags, depends-on, and footer row.

### Step 8: Update `src/cli.py` Serve Command

Replace subprocess call with direct `run_app()` import. Add `--port` and `--host` options.

### Step 9: Delete Streamlit Artifacts

Remove `.streamlit/` directory if it exists. Remove any Streamlit-specific imports.

### Step 10: Update `CLAUDE.md`

Update run commands, dependency list, and any Streamlit references.

### Step 11: Run Full CI

```bash
ruff check . && ruff format --check . && pytest tests/ -v
```

### Step 12: Manual Regression Test

Walk through the regression checklist in Section 6. Verify every behavior from the feature parity checklist in Section 2.

### Step 13 (Sprint 8): Drag-and-Drop Enhancement

Layer SortableJS integration on top of the working board. Add CDN script, initialize Sortable on columns, handle drop events via JavaScript-to-Python bridge.

---

## Key Decisions Summary

1. **Pure functions preserved** — `filter_items`, `render_card_html`, `category_style`, `detect_current_sprint` stay as-is. Existing tests pass unchanged.
2. **`@ui.refreshable` for reactivity** — single refresh mechanism replaces Streamlit's full-page rerun.
3. **Drag-and-drop deferred to Sprint 8** — move buttons provide feature parity in Sprint 7. SortableJS layered on afterward.
4. **Design tokens extracted** — `src/tokens.py` makes colors/sizing framework-agnostic and reusable.
5. **Serve command simplified** — direct Python call replaces subprocess spawn.
6. **No test rewrite needed** — all current tests exercise pure functions, not UI framework code.
