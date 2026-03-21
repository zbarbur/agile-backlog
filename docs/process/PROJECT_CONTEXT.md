# Project Context — agile-backlog

| Field | Value |
|-------|-------|
| **Status** | Sprint 1 Planning |
| **Last Sync** | 2026-03-21 |
| **Objective** | Lightweight Kanban board for agentic development |

## Architecture

Single Python package with three interfaces:
- **CLI** (`src/cli.py`) — Click-based, `agile-backlog` command
- **Web UI** (`src/app.py`) — Streamlit Kanban board
- **Claude Code plugin** (`plugin/`) — wraps CLI as /backlog commands

Data format: YAML files in `backlog/` directory, one per item, git-tracked.

## Test Coverage

| Metric | Value |
|--------|-------|
| **Tests** | 0 (not started) |
| **Test Runner** | pytest |
| **Lint** | ruff |
