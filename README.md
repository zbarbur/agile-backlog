# agile-backlog

Lightweight Kanban board tool for agentic development. Track backlog items as YAML files, move them through workflow stages via CLI or web UI, and keep everything git-tracked.

## Features

- **CLI** — add, list, move, edit, and inspect items from the terminal
- **Web board** — visual Kanban board via Streamlit with filters and move buttons
- **Claude Code plugin** — manage your backlog with `/backlog` without leaving your editor
- **YAML-based storage** — one file per item, human-readable, diff-friendly
- **Git-tracked** — full history of every status change
- **Workflow phases** — scoping, spec, design, coding, code-review, testing

## Installation

### pip (from GitHub)

```bash
pip install git+https://github.com/zbarbur/agile-backlog.git
```

### pipx (recommended — isolated environment)

```bash
pipx install git+https://github.com/zbarbur/agile-backlog.git
```

### Claude Code plugin

```bash
claude mcp add-from-claude-code agile-backlog -- git+https://github.com/zbarbur/agile-backlog.git
```

Or clone and install locally:

```bash
git clone https://github.com/zbarbur/agile-backlog.git
claude plugin add ./agile-backlog/plugin
```

## Quick Start

```bash
# Add a new backlog item
agile-backlog add "Fix auth leak" --priority P1 --category security

# List all items
agile-backlog list

# Filter items
agile-backlog list --status doing --priority P1

# Move an item
agile-backlog move fix-auth-leak --status doing --phase coding

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
`scoping` → `spec` → `spec-review` → `design` → `design-review` → `coding` → `code-review` → `testing`

## Development

```bash
git clone https://github.com/zbarbur/agile-backlog.git
cd agile-backlog
uv venv && uv pip install -e ".[dev]"
pytest tests/ -v
ruff check . && ruff format --check .
```
