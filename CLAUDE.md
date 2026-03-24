# agile-backlog — Project Rules

## ⚠️ CRITICAL: DO NOT RE-READ FILES

**BEFORE calling the Read tool, CHECK if the file was already read in this conversation.** If you have already read a file, use the information from the earlier read. Only re-read if you made edits and need to verify the current state. Re-reading large files like `components.py`, `app.py`, `cli.py` wastes thousands of tokens. Use offset/limit for targeted reads when you only need a specific section.

## Stack

Python 3.11+ · NiceGUI · Click · Pydantic · YAML · Ruff · pytest

## Commands

- **CI:** `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
- **Web UI:** `.venv/bin/agile-backlog serve`
- **CLI:** `.venv/bin/agile-backlog`
- Sprint config: `.claude/sprint-config.yaml`

## Code Style

- Ruff linting + formatting (120 char lines)
- Type hints: `list[dict]`, `str | None`
- No per-function docstrings — module-level only

## Design Principles

- Research first, design second, code third
- Code review before every merge
- DRY, YAGNI, TDD

## Context

| File | Purpose |
|---|---|
| `.claude/sprint-config.yaml` | Commands, paths, sprint settings |
| `backlog/*.yaml` | Backlog items (single source of truth) |
| `docs/process/PROJECT_CONTEXT.md` | Project snapshot |

## ⚠️ REMINDER: DO NOT RE-READ FILES YOU ALREADY HAVE IN CONTEXT
