# Project Context — agile-backlog

| Field | Value |
|-------|-------|
| **Status** | Sprint 25 Planning |
| **Last Sync** | 2026-03-25 |
| **Objective** | Lightweight Kanban board for agentic development |

## Architecture

Single Python package with three interfaces:
- **CLI** (`src/agile_backlog/cli.py`) — Click-based: add, list, move, edit, delete, show, serve, note, flagged, set-sprint, resolve-note, sprint-status, validate, install-skills, context-report
- **Web UI** (`src/agile_backlog/app.py`, `pure.py`, `styles.py`, `components.py`) — NiceGUI dark theme board + backlog planning view with click-to-edit, chat comments
- **Claude Code plugin** (`plugin/`) — /backlog command wrapping CLI

Data: YAML files in `backlog/`, config in `.claude/sprint-config.yaml`. Single source of truth.

Key modules: `models.py` (Pydantic), `yaml_store.py` (persistence), `tokens.py` (design tokens), `config.py` (sprint config), `pure.py` (pure functions), `styles.py` (CSS), `components.py` (UI components).

Package installable from git: `pip install git+https://github.com/zbarbur/agile-backlog.git`

## Test Coverage

| Metric | Value |
|--------|-------|
| **Tests** | 244 |
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
| 14 | Package portability + backlog planning design | 117 | — |
| 15 | Backlog view redesign Phase 1 + polish | 156 | #14 |
| 16 | Sprint Planning Phase 2 + Framework Integration | 162 | #15 |
| 17 | Sprint Execute + Framework Completion | 173 | #16 |
| 18 | UI Polish + CLI Visibility | 193 | #17 |
| 19 | CLI Power Tools + Adoption Guide | 204 | #18 |
| 20 | Adoption Hardening | 216 | #19 |
| 21 | UI Polish + Quality Gates | 224 | #20 |
| 22 | Polish + CI | 226 | #21 |
| 23 | Context Analysis + Small Wins | 243 | #22 |
| 24 | Publishing | 244 | — |
