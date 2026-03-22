# Memory Index

## Project Status
- Sprint 11 COMPLETED (2026-03-22)
- 110 tests, ruff clean, all PRs merged to main
- NiceGUI dark theme ("Mission Control") — full screen width
- YAML is single source of truth
- Phases: plan → spec → build → review

## Architecture
- NiceGUI with IBM Plex Mono + DM Sans fonts
- Design tokens in src/tokens.py (dark theme)
- Comments system (agent_notes field) with AI flagging
- Hot reload enabled by default
- Board/Backlog toggle view (backlog uses ui.table)
- Detail modal on card click, Edit button opens form dialog
- Add Item button in header
- Multi-select filters with chips (priority, category, sprint)
- Priority-colored left borders (P1=red, P2=blue, P3=amber)
- Card layout: title+comment top, move buttons+badges bottom

## Key Patterns
- Use `.venv/bin/python` for all commands (uv-managed venv)
- Sprint skills use agile-backlog CLI (not TODO.md)
- Sprint detection falls back to highest sprint number
- Category select with autocomplete from existing values
- Sprint target as Backlog/current sprint dropdown
- Comments via 💬 button on cards, flagged with 🤖 icon

## Remaining Backlog
- Auto-update phase during execution (P1)
- Track current sprint explicitly (P1)
- Drag-and-drop between columns (P2)
- Design review of backlog grid
- Various P3 items (export/import, PyPI, MCP, etc.)

## Lessons
- Dogfooding finds UX issues faster than specs
- Spec review catches real issues — always run it
- NiceGUI gives full CSS control but needs careful click event handling (click.stop)
- Items already done should be verified before coding (3 Sprint 11 items were already implemented)
- Sprint detection needs explicit tracking, not inference
