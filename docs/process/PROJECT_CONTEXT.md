# Project Context — agile-backlog

| Field | Value |
|-------|-------|
| **Status** | Sprint 14 Planning |
| **Last Sync** | 2026-03-22 |
| **Objective** | Lightweight Kanban board for agentic development |

## Architecture

Single Python package with three interfaces:
- **CLI** (`src/cli.py`) — Click-based: add, list, move, edit, show, serve, note, flagged, set-sprint, resolve-note
- **Web UI** (`src/app.py`) — NiceGUI dark theme Kanban board with comments, tags, filters
- **Claude Code plugin** (`plugin/`) — /backlog command wrapping CLI

Data: YAML files in `backlog/`, config in `.agile-backlog.yaml`. Single source of truth.

Key modules: `src/models.py` (Pydantic), `src/yaml_store.py` (persistence), `src/tokens.py` (design), `src/config.py` (sprint config).

## Test Coverage

| Metric | Value |
|--------|-------|
| **Tests** | 110 |
| **Test Runner** | pytest |
| **Lint** | ruff |

## Sprint History

| Sprint | Theme | Tests | PR |
|--------|-------|-------|----|
| 1 | Data model + YAML store + CLI | 41 | — |
| 2 | Streamlit Kanban board | 65 | — |
| 3 | UI polish + plugin + filtering | 73 | #3 |
| 4 | Design system + phases + installable | 91 | #4 |
| 5 | Single source of truth + CLI edit | 96 | #5 |
| 6 | Sprint skills + phases + frontend eval | 102 | #6 |
| 7 | NiceGUI migration + release pipeline | 103 | #7 |
| 8 | Mission Control dark theme + hot reload | 103 | #8 |
| 9 | Design polish + editing + backlog + agent notes | 110 | #9 |
| 10 | Add item UI + backlog table + fixes | 110 | #10 |
| 11 | Comments + sprint multi-select | 110 | #11 |
| 12 | Comment UX + edit dialog + sprint target | 110 | #12 |
| 13 | Comments resolve + tags + sprint config | 110 | #13 |
