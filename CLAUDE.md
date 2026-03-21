# agile-backlog — Project Rules

> Lightweight Kanban board tool for agentic development.
> Three interfaces: CLI, Streamlit web UI, Claude Code plugin.
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
- **Run tests:** `pytest tests/ -v`
- **Lint:** `ruff check .`
- **Format check:** `ruff format --check .`
- **Full CI:** `ruff check . && ruff format --check . && pytest tests/ -v`
- **Run Streamlit:** `streamlit run src/app.py`
- **Run CLI:** `agile-backlog` (after pip install -e .)

### Dependencies
- `streamlit` — web UI
- `streamlit-sortables` — drag-and-drop Kanban columns
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
| `.claude/MEMORY.md` | Agent memory across sessions |
| `docs/process/PROJECT_CONTEXT.md` | Project snapshot |
| `TODO.md` | Active sprint tasks |
| `docs/process/KANBAN.md` | Backlog |
