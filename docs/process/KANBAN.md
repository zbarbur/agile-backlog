# KANBAN — agile-backlog

> **Deprecated:** This file is kept for reference. The source of truth is now `backlog/*.yaml` files, viewable via `agile-backlog serve` or `agile-backlog list`.

---

## Backlog

See `agile-backlog list --status backlog` or the board UI.

## Done (Sprint 1-5)

- **YAML schema + BacklogItem model** — Pydantic model with Literal validation, slugify, to_yaml_dict.
- **YAML store (read/write)** — Git-root auto-detection, load/save/list YAML files, resilient to bad files.
- **CLI basics** — Click CLI: add, list, move, show, serve, edit. Slug collision handling.
- **Streamlit Kanban board** — 3-column board with design system, filters, move buttons, detail expanders.
- **Category colors** — pastel badge pills per category.
- **Search** — full-text search across title, description, and tags.
- **Sprint view** — filter by sprint in CLI and UI.
- **Smart filtering** — backlog-only filters, priority ranges, dimmed done column.
- **Claude Code plugin** — /backlog command wrapping CLI.
- **Sprint indicator** — auto-detected from doing items.
- **Design system** — research-based spec (Linear/Notion/Trello patterns).
- **Phase field** — workflow tracking (scoping → coding → testing).
- **Task definition fields** — goal, complexity, acceptance_criteria, technical_specs.
- **Formatted task details** — structured rendering in card expander.
- **Card design v2** — design system colors, P1 accent, done strikethrough.
- **pip/pipx install** — README with installation instructions.
- **CLI edit command** — update any field on a backlog item.
- **Board as single source of truth** — YAML items replace TODO.md for task specs.
