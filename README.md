# agile-backlog

Lightweight Kanban board tool for agentic development. Track backlog items as YAML files, move them through workflow stages via CLI or web UI, and keep everything git-tracked.

## Features

- **CLI** — add, list, move, and inspect items from the terminal
- **Web board** — drag-and-drop Kanban board via Streamlit
- **Claude Code plugin** — manage your backlog without leaving your editor
- **YAML-based storage** — one file per item, human-readable, diff-friendly
- **Git-tracked** — full history of every status change

## Installation

### pip (from GitHub)

```bash
pip install git+https://github.com/zbarbur/agile-backlog.git
```

### pipx (from GitHub, isolated environment)

```bash
pipx install git+https://github.com/zbarbur/agile-backlog.git
```

## Quick Start

```bash
# Add a new backlog item
agile-backlog add "Build login page" --priority high --tags frontend,auth

# List all items
agile-backlog list

# Move an item to a new status
agile-backlog move ITEM-001 in-progress

# Show details for an item
agile-backlog show ITEM-001

# Launch the web board
agile-backlog serve
```

## Workflow Stages

Items move through: `backlog` → `ready` → `in-progress` → `review` → `done`

## Screenshot

_Screenshots coming soon._

## Development

```bash
git clone https://github.com/zbarbur/agile-backlog.git
cd agile-backlog
pip install -e ".[dev]"
pytest tests/ -v
```
