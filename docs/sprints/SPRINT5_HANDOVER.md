# Sprint 5 Handover

> **Date:** 2026-03-21
> **Theme:** Board as single source of truth
> **Branch:** sprint5/main (merged to main)

## Completed Tasks

| Task | Status | Key Files |
|------|--------|-----------|
| T5.1 — Board as single source of truth | Done | `src/cli.py` (edit command), `backlog/*.yaml` |
| T5.2 — Sprint planning and task specs in UI | Done | `src/app.py` (expander rendering) |
| T5.3 — Claude Code plugin install | Done | `README.md`, `plugin/` |

## Key Decisions

- **YAML is the single source of truth.** Task specs (goal, complexity, acceptance criteria, tech specs) live in YAML items, not TODO.md. TODO.md is kept for historical reference only.
- **KANBAN.md deprecated.** Marked as deprecated — backlog is managed via CLI and board UI.
- **Light mode enforced.** Design system targets light mode; `.streamlit/config.toml` forces it.
- **Streamlit design ceiling acknowledged.** Current styling is at practical limits. "Evaluate frontend alternatives" is in backlog for future consideration.

## Architecture Changes

- `agile-backlog edit` command added — updates any field on a BacklogItem
- Sprint skills should write to YAML items directly going forward (not TODO.md)

## Known Issues

- Card design could be more polished (title+badges layout, button styling) — limited by Streamlit
- Dark mode renders poorly with current color palette
- Streamlit requires restart to pick up code changes (no hot reload for some changes)

## Lessons Learned

- **Dogfooding finds real UX issues.** Filter behavior, card layout, dark mode — all discovered by using the board during sprint planning.
- **Streamlit has a ceiling.** Good for MVPs, but per-component styling control is limited. Worth evaluating NiceGUI/Reflex for future.
- **Design system first pays off.** Sprint 4's research task produced a spec that made card redesign systematic instead of ad-hoc.
- **Screenshots > descriptions** for UI feedback. The iterative screenshot-based design loop was more effective than text descriptions.

## Test Coverage

| Metric | Value |
|--------|-------|
| Total tests | 96 |
| Test files | 4 (test_models, test_yaml_store, test_cli, test_app) |
| Lint | ruff clean |

## Sprint History

| Sprint | Theme | Tests |
|--------|-------|-------|
| 1 | Data model + YAML store + CLI | 41 |
| 2 | Streamlit Kanban board | 65 |
| 3 | UI polish + plugin + filtering | 73 |
| 4 | Design system + phases + installable | 91 |
| 5 | Single source of truth + CLI edit | 96 |

## Remaining Backlog

- Drag-and-drop (needs research on alternatives)
- Evaluate frontend alternatives to Streamlit
- Export/Import KANBAN.md
- Sprint subcommands (sprint show, sprint candidates)
- Publish to PyPI
- Sprint planning UI (view candidates, manage scope)

## Recommendations for Next Sprint

1. **Card design polish** — if staying with Streamlit, push key-based CSS selectors for individual button styling
2. **Frontend evaluation** — if design quality is a priority, prototype in NiceGUI
3. **Sprint workflow in YAML** — update sprint-start/sprint-end skills to read/write backlog YAML instead of TODO.md
