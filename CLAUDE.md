# agile-backlog — Project Rules

> Lightweight Kanban board tool for agentic development.
> Three interfaces: CLI, NiceGUI web UI, Claude Code plugin.
> One data format: YAML files per backlog item, git-tracked.

## Project Brief

See `docs/superpowers/specs/2026-03-21-agile-backlog-tool-brief.md` for the full product spec.

## Code Style — Python

- **Python 3.11+**
- **Ruff** for linting + formatting — config in `pyproject.toml`
- Line length: 120
- Type hints: modern syntax (`list[dict]`, `str | None`)
- Docstrings: module-level for purpose, not per-function boilerplate

### Commands

Commands are defined in `.claude/sprint-config.yaml` — all skills read from there.

- **Run tests:** `.venv/bin/pytest tests/ -v`
- **Lint:** `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
- **Full CI:** `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
- **Run Web UI:** `.venv/bin/agile-backlog serve`
- **Run CLI:** `.venv/bin/agile-backlog` (venv not auto-activated in Claude Code sessions)

### Dependencies
- `nicegui` — web UI
- `pyyaml` — read/write YAML backlog items
- `click` — CLI framework
- `pydantic` — BacklogItem model validation
- `ruff` — linting (dev)
- `pytest` — testing (dev)

## Design Principles

- **Research first, design second, code third** — validate before building
- **Quality review at every stage** — spec review, plan review, code review (9-point checklist)
- **DRY, YAGNI, TDD** — no premature abstractions
- **When adding deps** — update Dependabot config + dependency inventory

## Context System

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project rules (this file) |
| `.claude/sprint-config.yaml` | Sprint configuration — commands, paths, settings |
| `.claude/MEMORY.md` | Agent memory across sessions |
| `backlog/*.yaml` | Backlog items (single source of truth) |
| `docs/process/PROJECT_CONTEXT.md` | Project snapshot |
| `docs/process/DEFINITION_OF_DONE.md` | Quality gates |
