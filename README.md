# agile-backlog

[![CI](https://github.com/zbarbur/agile-backlog/actions/workflows/ci.yml/badge.svg)](https://github.com/zbarbur/agile-backlog/actions/workflows/ci.yml)

Lightweight Kanban board tool for agentic development. Track backlog items as YAML files, move them through workflow stages via CLI or web UI, and keep everything git-tracked.

## Features

- **CLI** — add, list, move, edit, delete, validate, and inspect items from the terminal
- **Web board** — NiceGUI dark-theme Kanban board with drag-and-drop, side panel editing, and filters
- **Sprint skills** — bundled Claude Code skills for sprint-start, sprint-execute, sprint-end workflows
- **YAML-based storage** — one file per item, human-readable, diff-friendly
- **Git-tracked** — full history of every status change
- **Workflow phases** — plan → spec → build → review → done

## Installation

```bash
# CLI only (fast, no NiceGUI)
pip install git+https://github.com/zbarbur/agile-backlog.git

# CLI + web UI
pip install "agile-backlog[ui] @ git+https://github.com/zbarbur/agile-backlog.git"
```

### Install Sprint Skills

```bash
agile-backlog install-skills
```

Copies bundled skills to `.claude/skills/`. See `agile-backlog install-skills --help` for options.

## Quick Start

```bash
# Add a new backlog item
agile-backlog add "Fix auth leak" --priority P1 --category bug

# List all items
agile-backlog list

# Filter items
agile-backlog list --status doing --priority P1

# Move an item
agile-backlog move fix-auth-leak --status doing --phase build

# Edit task definition
agile-backlog edit fix-auth-leak --goal "Fix the OAuth token leak" --complexity M

# Show full details
agile-backlog show fix-auth-leak

# Open the Kanban board
agile-backlog serve
```

## Statuses & Phases

Items flow: **backlog** → **doing** → **done**

While in "doing", items track their workflow phase:
`plan` → `spec` → `build` → `review`

## Development

```bash
git clone https://github.com/zbarbur/agile-backlog.git
cd agile-backlog
uv venv && uv pip install -e ".[dev]"
pytest tests/ -v
ruff check . && ruff format --check .
```
