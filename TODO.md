# TODO — agile-backlog

> Active sprint tasks only. Backlog lives in `docs/process/KANBAN.md`.

---

## Sprint 1 — Complete

- [x] BacklogItem Pydantic model + slugify + tests (12 tests)
- [x] YAML store with git-root detection + tests (13 tests)
- [x] Click CLI: add, list, move, show, serve + tests (16 tests)
- [x] Full CI green (41 tests, ruff clean)
- [x] Entry point `agile-backlog` works via pip install

## Sprint 2 — Complete

- [x] Pure functions: category_style, filter_items, render_card_html + tests (24 tests)
- [x] Streamlit Kanban board with styled cards, filters, move-via-dropdown, expanders
- [x] CLI `serve` command launches Streamlit
- [x] Full CI green (65 tests, ruff clean)
- [x] Dogfooding: backlog managed via YAML files
