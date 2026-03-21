# KANBAN — agile-backlog

> Backlog for the backlog tool. Items flow: **Backlog** → **Doing** → **Done**

---

## Backlog

### Core

- **Streamlit Kanban board** — `src/app.py` — 3-column board (Backlog, Doing, Done), cards with title/priority/category, filter bar, click to expand.
- **Drag-and-drop** — `streamlit-sortables` integration for moving cards between columns.
- **Claude Code plugin** — `plugin/` directory with plugin.json, /backlog command, wraps CLI.
- **Sprint subcommands** — `sprint show`, `sprint candidates` CLI subcommands.

### Polish

- **Search** — full-text search across title + description + tags
- **Sprint view** — filter board to show only items for current sprint
- **Category colors** — visual badges on cards
- **Export** — generate KANBAN.md from YAML items (for repos that still want markdown)
- **Import** — parse existing KANBAN.md into YAML items (migration tool)

---

## Done

- **YAML schema + BacklogItem model** — Pydantic model with Literal validation, slugify, to_yaml_dict. 12 tests.
- **YAML store (read/write)** — Git-root auto-detection, load/save/list YAML files, resilient to bad files. 13 tests.
- **CLI basics** — Click CLI: `add`, `list` (with filters), `move`, `show`, `serve` placeholder. Slug collision handling. 16 tests.
