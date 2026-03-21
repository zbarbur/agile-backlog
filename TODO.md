# TODO — agile-backlog

> Active sprint tasks only. Backlog lives in `backlog/*.yaml`.

---

## Sprint 1 — Complete

- [x] BacklogItem Pydantic model + slugify + tests (12 tests)
- [x] YAML store with git-root detection + tests (13 tests)
- [x] Click CLI: add, list, move, show, serve + tests (16 tests)
- [x] Full CI green (41 tests, ruff clean)
- [x] Entry point `agile-backlog` works via pip install

## Sprint 2 — Complete

- [x] Pure functions: category_style, filter_items, render_card_html + tests (24 tests)
- [x] Streamlit Kanban board with styled cards, filters, move-via-dropdown, expanders
- [x] CLI `serve` command launches Streamlit
- [x] Full CI green (65 tests, ruff clean)
- [x] Dogfooding: backlog managed via YAML files

## Sprint 3 — UI Polish + Plugin

**Theme:** Make the board look professional and add Claude Code plugin.

### T3.1 — Unify card layout
- **Goal:** Wrap card header, move dropdown, and details expander inside one visual container so they look like a single card
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** None
- **DoD:**
  - [ ] Card header, move selectbox, and details expander are visually contained in one bordered card
  - [ ] No floating elements between cards
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/app.py`: use `st.container()` with custom CSS to wrap card elements
  - Inject card container CSS via `st.markdown(unsafe_allow_html=True)` at page load
  - Move selectbox and expander rendered inside the container
- **Test Plan:**
  - `tests/test_app.py` — existing tests still pass (render_card_html unchanged)
  - Manual verification in browser
- **Demo Data Impact:** None

### T3.2 — Smarter filtering UX
- **Goal:** Fix filter behavior so Doing/Done columns are always visible and priority supports ranges
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** None
- **DoD:**
  - [ ] Filters only apply to Backlog column — Doing and Done items always visible
  - [ ] Priority filter options: All, P1, P1+P2, P1+P2+P3
  - [ ] Filters persist across item moves (no reset on st.rerun)
  - [ ] Done column visually dimmed (lower opacity or muted colors)
  - [ ] `filter_items` updated with tests for new behavior
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/app.py`: `filter_items()` only applied to backlog items, doing/done passed through unfiltered
  - Add priority range support: `filter_items(priority="P2+")` matches P1 and P2
  - Store filter state in `st.session_state` with explicit keys to persist across reruns
  - Add CSS for Done column: `opacity: 0.7` or similar
- **Test Plan:**
  - `tests/test_app.py` — new tests: `test_filter_priority_range`, `test_filter_does_not_apply_to_doing`, `test_filter_does_not_apply_to_done`
- **Demo Data Impact:** None

### T3.3 — Polish frontend design
- **Goal:** Make the board look professional with compact layout, better typography, and visual consistency
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** T3.1
- **DoD:**
  - [ ] Cards are compact — reduced padding and spacing
  - [ ] Column headers are styled (not raw markdown h3)
  - [ ] Filter bar is compact and horizontal
  - [ ] Page has consistent dark or light theme styling
  - [ ] Board fills available width without excessive whitespace
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/app.py`: inject global CSS via `st.markdown` for typography, spacing, column styling
  - Update `render_card_html()` for more compact card design
  - Style column headers with item count badges
  - Reduce Streamlit default padding via CSS overrides
- **Test Plan:**
  - `tests/test_app.py` — `render_card_html` tests updated if HTML structure changes
  - Manual verification in browser
- **Demo Data Impact:** None

### T3.4 — Show current sprint indicator
- **Goal:** Display the active sprint number prominently so users know which sprint they're working in
- **Specialist:** python-architect
- **Complexity:** S
- **Depends on:** T3.3
- **DoD:**
  - [ ] Board header shows "Sprint N" badge or label
  - [ ] Sprint number derived from items (most common sprint_target in Doing column)
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Modify `src/app.py`: add sprint detection logic (mode of sprint_target in doing items)
  - Render sprint badge in header area next to "agile-backlog" title
- **Test Plan:**
  - `tests/test_app.py` — test sprint detection function with various item configurations
- **Demo Data Impact:** None

### T3.5 — Claude Code plugin
- **Goal:** Create a Claude Code plugin with /backlog command that wraps the CLI for in-editor backlog management
- **Specialist:** python-architect
- **Complexity:** M
- **Depends on:** None
- **DoD:**
  - [ ] `plugin/plugin.json` manifest with valid structure
  - [ ] `/backlog` command available: list, add, move, show
  - [ ] Plugin wraps CLI commands correctly
  - [ ] Tests pass (`pytest tests/ -v`)
  - [ ] Lint clean (`ruff check .`)
- **Technical Specs:**
  - Create `plugin/plugin.json` — plugin manifest
  - Create `plugin/commands/backlog.md` — `/backlog` slash command
  - Command delegates to `agile-backlog` CLI
- **Test Plan:**
  - Manual verification: install plugin, run `/backlog list`
- **Demo Data Impact:** None
