# Memory Index

## Project Status
- Sprint 10 COMPLETED (2026-03-22)
- 110 tests, ruff clean, all PRs merged to main
- NiceGUI dark theme ("Mission Control") — full screen width
- YAML is single source of truth
- Phases: plan → spec → build → review

## Architecture
- NiceGUI (migrated from Streamlit in Sprint 7)
- Design tokens in src/tokens.py (dark theme)
- Agent notes: agile-backlog note/flagged CLI commands
- Hot reload enabled by default
- Board/Backlog toggle view
- Detail modal on card click, Edit button opens form dialog
- Add Item button in header
- Backlog view uses ui.table with sortable columns

## Key Patterns
- Use `.venv/bin/python` for all commands (uv-managed venv)
- Sprint skills use agile-backlog CLI (not TODO.md)
- Sprint detection falls back to highest sprint number (needs proper config tracking)
- Multi-select filters with chips for priority/category
- IBM Plex Mono + DM Sans fonts
- Category select with autocomplete from existing values
- Sprint target as Backlog/current sprint dropdown

## Known Issues for Next Sprint
- Sprint tracking should be explicit (config file, not inferred)
- Auto-update phase during execution still in backlog
- Some UI polish items remain (frontend designer pass)
- Agent notes not yet editable from board UI
- Drag-and-drop still in backlog

## Lessons
- Dogfooding finds UX issues faster than specs
- Brainstorm with visual companion before design implementation
- Spec review catches real issues — always run it
- Phase `spec` was needed — 4 phases better than 3
- Sprint detection needs explicit tracking, not inference
- Category should be select-from-list, not free text input
