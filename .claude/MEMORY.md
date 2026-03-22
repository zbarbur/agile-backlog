# Memory Index

## Project Status
- Sprint 9 COMPLETED (2026-03-22)
- 110 tests, ruff clean, all PRs merged to main
- NiceGUI dark theme ("Mission Control") — full screen width
- YAML is single source of truth

## Architecture
- NiceGUI (not Streamlit) — migrated in Sprint 7
- Pure functions preserved: category_style, filter_items, render_card_html, detect_current_sprint
- Design tokens in src/tokens.py (dark theme colors)
- Agent notes: agile-backlog note/flagged CLI commands
- Hot reload enabled by default

## Key Patterns
- Use `.venv/bin/python` for all commands (uv-managed venv)
- Sprint skills use agile-backlog CLI (not TODO.md)
- Phases: plan, build, review + design_reviewed/code_reviewed flags
- Done items keep their last phase
- Filters: multi-select with chips, sprint filter applies to all columns
- Detail modal on card click, Edit button opens form dialog
- Board/Backlog toggle for different views

## Known Issues (for Sprint 10)
- Font swap item still in backlog (IBM Plex Mono may not be rendering on all elements)
- Some card spacing inconsistencies
- Backlog view needs more polish
- Agent notes not yet shown in board UI modal
- Auto-update phase during execution still in backlog

## Lessons
- Dogfooding finds UX issues faster than specs
- Brainstorm with visual companion before design implementation
- NiceGUI gives full CSS control — no more Streamlit ceiling
- Multi-select filters with chips (Linear pattern) work well
- Sprint skills should auto-update item phases as work progresses
