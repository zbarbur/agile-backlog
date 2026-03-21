# Agile Backlog Tool — Project Brief

> **Purpose:** Kickstart document for a separate repo. Take this to a new Claude Code session.
> **Repo:** TBD (e.g., `agile-backlog`)
> **Type:** Developer tooling — CLI + web UI + Claude Code plugin

---

## Problem

As agentic development projects grow, the single KANBAN.md file becomes hard to manage. Need a lightweight backlog management tool that:
- Both human and AI agent can read/write
- Has a visual Kanban board interface
- Supports filtering, search, prioritization
- Stays in git (YAML files per item)
- Installs easily across projects

## Product

### Three interfaces, one data format

```
agile-backlog (one codebase)
├── CLI tool          pip install → `agile-backlog` command
├── Streamlit web UI  `agile-backlog serve` → Kanban board in browser
├── Claude Code plugin  /backlog commands inside Claude Code
└── YAML files        backlog/*.yaml in each project repo (git-tracked)
```

### Kanban Board UI (Streamlit)

Visual board with 3 columns: **Backlog**, **Doing**, **Done**
- Cards show: title, priority badge (P1/P2/P3), category tag, sprint target
- Drag-and-drop between columns (updates YAML status)
- Click card → expand details, edit
- Filter bar: category, sprint, priority, search
- Uses `streamlit-sortables` or similar for drag-and-drop

### CLI

```bash
agile-backlog serve                                    # open Kanban board
agile-backlog list                                     # list all items
agile-backlog list --category security --priority P1   # filtered
agile-backlog add "Fix auth leak" --priority P1 --category security
agile-backlog move fix-auth-leak --status doing
agile-backlog sprint show                              # current sprint items
agile-backlog sprint candidates                        # items tagged for next sprint
```

### Claude Code Plugin

```
/backlog              — list items or open board
/backlog add "..."    — create new item
/backlog list         — filtered list in terminal
/backlog move         — change status
```

Plugin wraps CLI commands. Agent can also read/write YAML files directly.

### YAML Item Schema

```yaml
# backlog/fix-auth-leak.yaml
id: fix-auth-leak                    # filename-derived
title: Fix authentication leak
status: backlog                      # backlog | doing | done
priority: P1                         # P1 (critical) | P2 (important) | P3 (nice-to-have)
category: security                   # security | scanner | api | infra | tech-debt | docs
sprint_target: 4                     # which sprint this is planned for (null = unplanned)
created: 2026-03-21
updated: 2026-03-21
depends_on: []                       # list of item IDs
tags: []                             # free-form tags
description: |
  Current SAILPOINT_API_TOKEN is a hardcoded dummy bearer token.
  Need OAuth2/JWT validation for production.
acceptance_criteria:
  - OAuth2 token validation implemented
  - Static token removed from .env
  - Tests cover auth flow
notes: |
  Sprint 2 PR review flagged this as a security gap.
```

## Tech Stack

- **Python 3.11+** (same as BigQuery-connector)
- **Streamlit** — web UI (pip install, no build step)
- **streamlit-sortables** — drag-and-drop Kanban
- **PyYAML** — read/write YAML files
- **Click** — CLI framework
- **ruff** — linting/formatting
- **pytest** — testing

## What to Adopt from BigQuery-connector Template

### Keep (adapt for this project)
- CLAUDE.md (Python rules, ruff, pytest — simpler)
- .claude/project.json (project metadata)
- .claude/MEMORY.md + memory files
- docs/process/KANBAN.md (use it to build the tool that replaces it)
- docs/process/TASK_TEMPLATE.md
- docs/process/SPRINT_END_CHECKLIST.md (with 9-point review)
- docs/process/DEFINITION_OF_DONE.md
- docs/process/PROJECT_CONTEXT.md
- Sprint lifecycle skills (sprint-start, sprint-end)
- AGENTIC_AGILE_MANIFEST.md
- BOOTSTRAP.md

### Skip (not relevant)
- CODING_STANDARDS.md (Biome/TypeScript — rewrite for Python)
- SQUAD_PLANNING.md (7 specialists overkill — one python-architect enough)
- Most .claude/agents/ (too many roles)
- deploy, security-audit, rollback, nano-banana skills
- NEXTJS_VS_STATIC_SITE.md
- All GCP/SailPoint specific docs

## Scaffold Structure

```
agile-backlog/
├── CLAUDE.md
├── TODO.md
├── pyproject.toml
├── .claude/
│   ├── project.json
│   ├── MEMORY.md
│   ├── skills/
│   │   ├── sprint-start/SKILL.md
│   │   └── sprint-end/SKILL.md
│   └── commands/
│       ├── sprint-start.md
│       ├── sprint-end.md
│       ├── test.md
│       └── review.md
├── docs/
│   ├── process/
│   │   ├── KANBAN.md
│   │   ├── PROJECT_CONTEXT.md
│   │   ├── TASK_TEMPLATE.md
│   │   ├── SPRINT_END_CHECKLIST.md
│   │   └── DEFINITION_OF_DONE.md
│   └── sprints/
├── src/
│   ├── __init__.py
│   ├── app.py                 # Streamlit Kanban board
│   ├── cli.py                 # Click CLI
│   ├── models.py              # BacklogItem Pydantic model
│   ├── yaml_store.py          # Read/write YAML files
│   └── schema.yaml            # Item schema definition
├── plugin/
│   ├── plugin.json            # Claude Code plugin manifest
│   ├── commands/
│   │   └── backlog.md         # /backlog command
│   └── skills/
│       └── backlog/SKILL.md   # Backlog management skill
└── tests/
    ├── test_models.py
    ├── test_yaml_store.py
    └── test_cli.py
```

## Sprint Plan (rough)

| Sprint | What |
|--------|------|
| 1 | YAML schema + store + CLI basics (add, list, move) + tests |
| 2 | Streamlit Kanban board UI (3 columns, cards, filters) |
| 3 | Claude Code plugin + drag-and-drop + polish |
| 4 | Install/distribution (pip, pipx, claude install) |

## Key Design Principles (from BigQuery-connector learnings)

- Research first, design second, code third
- Quality review at every stage (spec → plan → code)
- 9-point code review before sprint closure
- DRY, YAGNI, TDD
- When adding deps, update Dependabot + dependency inventory
