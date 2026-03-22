# Memory Index

## Project Status
- Sprint 12 COMPLETED (2026-03-22)
- 110 tests, ruff clean, all PRs merged to main
- NiceGUI dark theme ("Mission Control")
- YAML is single source of truth
- Phases: plan → spec → build → review

## Architecture
- NiceGUI with IBM Plex Mono + DM Sans fonts
- Design tokens in src/tokens.py (dark theme)
- Comments system (agent_notes field) with AI flagging + badge count
- Board/Backlog toggle (backlog uses ui.table)
- Detail modal + Edit dialog (720px wide, rows=6 textareas)
- Add Item button, multi-select filters with chips
- Priority-colored left borders (P1=red, P2=blue, P3=amber)
- Sprint target: only Backlog/Current/Next options
- Hot reload enabled by default

## Process
- Sprint skills use agile-backlog CLI
- Check flagged comments (agile-backlog flagged) during sprint planning
- Spec review before execution
- Comments for async human-to-agent communication

## Sprint 13 Prep
- Sprint planning tool — backlog sections (Backlog/Next/Future) + drag-and-drop (needs brainstorming)
- Backlog grid design review
- Tags feature for organizing items
- Image paste implementation (research done: file-based + clipboard API)
- Auto-update phase during execution
- Track current sprint explicitly

## Lessons
- Always check flagged comments at sprint start
- Verify items aren't already done before coding
- Split big features (backlog planning tool) into research + implementation sprints
- Comment system enables async feedback loop between sessions
