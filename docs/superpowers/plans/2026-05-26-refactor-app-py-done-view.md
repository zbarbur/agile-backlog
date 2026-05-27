# Plan — Extract Done view from app.py

**Item:** `refactor-app-py-extract-context-process-and-done-views-into-separate-modules-to-reduce-1576-line-single-file`
**Sprint:** 30
**Date:** 2026-05-26

## Goal

Extract the Done-view rendering block (currently inlined inside `kanban_page()` in `app.py`) into a new module `src/agile_backlog/views/done.py`. This is the proof-of-pattern slice toward breaking up the 1852-line file.

## Boundaries

- Done view: app.py lines ~645–946 (~300 lines, matches AC ≥300 line reduction)
- Marker comments: `# --- Done view: all completed items grouped by sprint ---` (start) and `# --- Context analysis dashboard ---` (end)

## Closure dependencies (must be passed as parameters)

The Done view block currently captures these from `kanban_page()`:

**Data:**
- `items` — list of all BacklogItem
- `sq` (search query), `pf_list` (priority filter), `cf_list` (category filter), `tf_list`/`tf_set` (tag filter), `resolved_sprints` (sprint filter)

**Helpers / functions:**
- `_sprint_match(sprint_target)` — filter predicate
- `save_item`, `load_item` — yaml_store functions (already importable)
- `render_board.refresh` — refreshable callback

**UI state (created inside the block, no need to pass):**
- `done_panel_state`, `done_list_ref`, `done_panel_ref`

## Approach

1. Create `src/agile_backlog/views/__init__.py` (empty package init).
2. Create `src/agile_backlog/views/done.py` with a single entry point:
   ```python
   def render_done_view(
       items: list[BacklogItem],
       search_query: str,
       priority_filter: list[str],
       category_filter: list[str],
       tag_filter_list: list[str],
       tag_filter_set: set[str],
       resolved_sprints: bool,
       sprint_match_fn: Callable[[int | None], bool],
       refresh_board: Callable[[], None],
   ) -> None:
       """Render the Done view inside the current NiceGUI parent."""
   ```
3. Move the Done-view code body verbatim into `render_done_view`, replacing closure references with the parameter names.
4. Keep `save_item`/`load_item` imports inside the new module (they're already imported via `yaml_store`).
5. In `app.py`, replace the inlined Done view block with:
   ```python
   if view_mode["current"] == "done":
       from agile_backlog.views.done import render_done_view
       render_done_view(
           items=items,
           search_query=sq,
           priority_filter=pf_list,
           ...
       )
   ```
6. Preserve all existing patterns:
   - State dicts (no closure capture for stale-closure safety per S29 lesson)
   - `safe_html()` on all `ui.html()` calls
   - All existing tests pass unchanged

## Acceptance verification

- `wc -l src/agile_backlog/app.py` shows ≥300 line reduction
- `.venv/bin/pytest tests/ -v` — all 361 tests still pass
- `.venv/bin/ruff check . && .venv/bin/ruff format --check .` — clean
- Manual smoke (optional): `.venv/bin/agile-backlog serve` → Done tab renders correctly

## Risks

- Stale closure regression: if `render_done_view` accidentally captures rather than receives `items`, the panel might show stale data after edits. Use the shared-state-dict pattern as in S29.
- Filter regression: the sprint filter (`_sprint_match`) is a closure that captures `resolved_sprints`. Pass it as a function reference, not redefine.
- Import cycles: `views/done.py` must not import from `app.py`. Use `components`, `pure`, `yaml_store`, `models` directly.
