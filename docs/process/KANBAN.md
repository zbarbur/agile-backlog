# KANBAN — agile-backlog

> Backlog for the backlog tool. Items flow: **Backlog** → **Doing** → **Done**

---

## Backlog

### Core

- **YAML schema + BacklogItem model** — Define the canonical YAML structure for backlog items. Pydantic model for validation. Schema file at `src/schema.yaml`.
- **YAML store (read/write)** — `src/yaml_store.py` — read all items from `backlog/` dir, write item to YAML, update status. Handles file naming, dedup, validation.
- **CLI basics** — `src/cli.py` using Click: `add`, `list`, `move`, `show`, `sprint show`, `sprint candidates`. Entry point: `agile-backlog`.
- **Streamlit Kanban board** — `src/app.py` — 3-column board (Backlog, Doing, Done), cards with title/priority/category, filter bar, click to expand.
- **Drag-and-drop** — `streamlit-sortables` integration for moving cards between columns.
- **Claude Code plugin** — `plugin/` directory with plugin.json, /backlog command, wraps CLI.

### Polish

- **Search** — full-text search across title + description + tags
- **Sprint view** — filter board to show only items for current sprint
- **Category colors** — visual badges on cards
- **Export** — generate KANBAN.md from YAML items (for repos that still want markdown)
- **Import** — parse existing KANBAN.md into YAML items (migration tool)

---

## Done

_(empty)_
