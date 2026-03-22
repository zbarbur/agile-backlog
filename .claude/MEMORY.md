# Memory Index

## Project Status
- Sprint 13 COMPLETED (2026-03-22)
- Sprint 14 items selected (4 items in doing)
- 110 tests, ruff clean
- Current sprint: 13 (set in .agile-backlog.yaml)

## Sprint 14 Scope (already in doing)
- Sprint planning tool — backlog sections + drag-and-drop (P1, needs brainstorming)
- Comment badge logic bug — counts total not unresolved flagged (P1)
- Sort the board (P2)
- Hot reload losing work when editing (P2)

## Architecture
- NiceGUI dark theme, IBM Plex Mono + DM Sans
- src/config.py for explicit sprint tracking (.agile-backlog.yaml)
- Comments system with author field (user/agent), per-comment resolve
- Tags on cards with filter
- Board/Backlog toggle, detail modal, edit dialog
- Multi-select filters with chips
- Priority-colored left borders

## Process
- Sprint skills use agile-backlog CLI
- Check flagged comments (agile-backlog flagged) at sprint start
- Phases: plan → spec → build → review
- Spec review before execution
- Use --no-reload when editing from board to avoid losing work

## Remaining Backlog Highlights
- Paste image implementation (research done)
- Comments UX further polish
- Frontend designer polish pass
- Show done checkbox fix
- Various P3 items
