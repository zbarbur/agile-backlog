# Sprint 2 Design — Streamlit Kanban Board UI

> **Date:** 2026-03-21
> **Scope:** `src/app.py` — Streamlit web UI with visual Kanban board
> **Parent spec:** `2026-03-21-agile-backlog-tool-brief.md`
> **Depends on:** Sprint 1 (models.py, yaml_store.py, cli.py)

---

## Overview

Sprint 2 delivers a visual Kanban board served via Streamlit. Users run `agile-backlog serve` (or `streamlit run src/app.py`) to open a browser-based board showing all backlog items in three columns with rich styled cards, filter chips, and inline detail expanders.

**Scope change from parent spec:** The parent spec includes "click to edit" and places drag-and-drop in Sprint 3. This sprint focuses on view + move-via-dropdown with rich card styling. Drag-and-drop is deferred to Sprint 3 because `streamlit-sortables` only supports plain text labels — it cannot render the styled cards. Inline editing is also deferred to Sprint 3.

## Design Decisions

### Layout: Clean minimal with filter chips

Top bar contains the project name and a row of filter chips. Below that, three equal-width columns: Backlog, Doing, Done. Each column header shows the column name and item count.

Filter chips are toggleable buttons for:
- **Priority:** P1 / P2 / P3 (click to filter, click again to clear)
- **Category:** dynamically populated from items (feature, bug, tech-debt, etc.)
- **Sprint:** dynamically populated from items' `sprint_target` values
- **Search:** text input that filters on title + description + tags

Multiple filters combine with AND logic. Active filters are visually highlighted. Filter state is stored in `st.session_state`.

### Cards: Category header bar (rich HTML via st.markdown)

Cards are rendered as styled HTML via `st.markdown(unsafe_allow_html=True)` inside each column. This allows full visual control — colored headers, emoji, badges.

Each card has:
- **Colored header strip** with emoji icon + category name + priority badge
- **Title** below the header
- **Sprint indicator** ("S2" or "Unplanned") below the title
- **"Move to →" selectbox** for changing status (replaces drag-and-drop)

Category color map:

| Category | Color | Emoji |
|----------|-------|-------|
| bug | pink (#f472b6) | 🐛 |
| feature | blue (#60a5fa) | ✨ |
| tech-debt | amber (#fbbf24) | 🔧 |
| docs | green (#34d399) | 📚 |
| security | purple (#a78bfa) | 🔒 |
| infra | cyan (#22d3ee) | 🏗️ |
| *(other)* | gray (#9ca3af) | 📋 |

Priority colors (used in badge): P1=red (#ef4444), P2=blue (#3b82f6), P3=amber (#f59e0b).

### Interaction: View + move-via-dropdown

- **Move items:** each card has a selectbox showing the other two statuses. Selecting one updates the item's status via `save_item()` and triggers `st.rerun()`.
- **Click to expand:** `st.expander` below each card shows full details (read-only).
- **No drag-and-drop** in Sprint 2 (`streamlit-sortables` only supports plain text labels).
- **No inline editing** in Sprint 2. Users edit via CLI or directly in YAML files.

### Detail view: Inline expander

When a card's expander is toggled, it shows:
- Full description
- Acceptance criteria (as bullet list)
- Notes
- Tags, depends_on
- Created/updated dates
- Sprint target

### CLI integration

The existing `serve` placeholder in `cli.py` is updated to launch Streamlit:
```python
@main.command()
def serve():
    """Open the Kanban board in the browser."""
    import subprocess
    import sys
    app_path = Path(__file__).parent / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
```

Uses `sys.executable` to ensure Streamlit runs in the same Python environment as the CLI.

---

## Component Structure

### `src/app.py` — Streamlit application

Single file, structured as:

1. **Page config** — `st.set_page_config(page_title="agile-backlog", layout="wide")`
2. **Load data** — `load_all()` from yaml_store, group by status into 3 lists
3. **Filter bar** — render filter chips via `st.columns` + `st.button`/`st.text_input`, apply filters
4. **Render columns** — three `st.columns(3)`, each with header + item count
5. **Render cards** — for each item in column: styled HTML card via `st.markdown`, move selectbox, expander with details
6. **Handle moves** — on selectbox change: update item status, `save_item()`, `st.rerun()`

### Pure functions (extracted for testability)

```python
def category_style(category: str) -> tuple[str, str, str]:
    """Return (emoji, text_color, bg_color) for a category."""

def filter_items(
    items: list[BacklogItem],
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    sprint: int | None = None,
    search: str = "",
) -> list[BacklogItem]:
    """Apply filters to items. Multiple filters combine with AND logic."""

def render_card_html(item: BacklogItem) -> str:
    """Generate the HTML string for a card. Pure function, no Streamlit calls."""
```

---

## Data Flow

```
User opens browser → Streamlit loads → load_all() reads backlog/*.yaml
                                      → group items by status
                                      → render filter bar + 3 columns
                                      → render styled HTML cards per column

User selects       → selectbox on_change fires
"Move to Doing"    → save_item(item) with new status
                   → st.rerun() refreshes board

User expands card  → st.expander toggles inline
                   → shows full item details (read-only)

User applies filter → st.session_state stores active filters
                    → filtered items re-render in columns

Edge cases:
- Empty backlog dir → show "No items yet" message with CLI hint
- All items filtered out → show "No items match filters" per column
- Move to same status → no-op (selectbox only shows other statuses)
```

---

## Testing Strategy

| What | How |
|------|-----|
| `category_style()` | Unit test — all known categories + unknown fallback |
| `filter_items()` | Unit test — each filter dimension, combined filters, empty input |
| `render_card_html()` | Unit test — verify HTML contains expected elements |
| Edge cases | Unit test — empty list, all filtered out, items with missing optional fields |
| Full board rendering | Manual smoke test via `streamlit run src/app.py` |

Test file: `tests/test_app.py`

---

## Out of Scope (Sprint 3+)

- Drag-and-drop via `streamlit-sortables` (plain text limitation — explore alternatives or custom component)
- Inline editing of card fields (parent spec's "click to edit")
- Sprint planning mode / candidate marking
- Sidebar filter panel (may revisit if filter chips get crowded)
- Card reordering within a column (priority ordering)
- Real-time collaboration / auto-refresh
