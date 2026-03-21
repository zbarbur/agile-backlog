# Project Context — agile-backlog

| Field | Value |
|-------|-------|
| **Status** | Sprint 6 Planning |
| **Last Sync** | 2026-03-21 |
| **Objective** | Lightweight Kanban board for agentic development |

## Architecture

Single Python package with three interfaces:
- **CLI** (`src/cli.py`) — Click-based: add, list, move, edit, show, serve
- **Web UI** (`src/app.py`) — Streamlit Kanban board with design system
- **Claude Code plugin** (`plugin/`) — /backlog command wrapping CLI

Data format: YAML files in `backlog/` directory, one per item, git-tracked. YAML is the single source of truth for task specs (goal, complexity, acceptance criteria, technical specs).

## Test Coverage

| Metric | Value |
|--------|-------|
| **Tests** | 96 |
| **Test Runner** | pytest |
| **Lint** | ruff |

## Sprint History

| Sprint | Theme | Tests | PR |
|--------|-------|-------|----|
| 1 | Data model + YAML store + CLI | 41 | (direct to main) |
| 2 | Streamlit Kanban board | 65 | (direct to main) |
| 3 | UI polish + plugin + filtering | 73 | #3 |
| 4 | Design system + phases + installable | 91 | #4 |
| 5 | Single source of truth + CLI edit | 96 | #5 |
