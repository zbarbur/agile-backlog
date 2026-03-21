# KANBAN — agile-backlog

> Backlog for the backlog tool. Items flow: **Backlog** → **Doing** → **Done**

---

## Backlog

### Core

- **Drag-and-drop** — explore alternatives to `streamlit-sortables` for rich card drag-and-drop.
- **Claude Code plugin** — `plugin/` directory with plugin.json, /backlog command, wraps CLI.
- **Sprint subcommands** — `sprint show`, `sprint candidates` CLI subcommands.
- **Inline editing** — click card to edit fields in the UI.

### Polish

- **Export** — generate KANBAN.md from YAML items (for repos that still want markdown)
- **Import** — parse existing KANBAN.md into YAML items (migration tool)

---

## Done

- **YAML schema + BacklogItem model** — Pydantic model with Literal validation, slugify, to_yaml_dict. 12 tests.
- **YAML store (read/write)** — Git-root auto-detection, load/save/list YAML files, resilient to bad files. 13 tests.
- **CLI basics** — Click CLI: `add`, `list` (with filters), `move`, `show`, `serve`. Slug collision handling. 16 tests.
- **Streamlit Kanban board** — 3-column board with styled cards (category headers, priority badges), filters (priority/category/sprint/search), move-via-dropdown, inline detail expanders. 24 tests.
- **Category colors** — visual badges on cards with emoji + colored header strips.
- **Search** — full-text search across title, description, and tags.
- **Sprint view** — filter by sprint number in both CLI and UI.
