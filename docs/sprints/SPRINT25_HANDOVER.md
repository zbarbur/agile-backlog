# Sprint 25 Handover — UI Polish + Observability

**Date:** 2026-03-27
**Branch:** sprint25/main
**Tests:** 264 (was 245)
**Commits:** 4

## Completed Tasks (5/5)

| Item | Size | Category |
|------|------|----------|
| Card redesign — reduce badge clutter and improve timestamp visibility | S | feature |
| The show archived doesn't look good | S | bug |
| Add also a "Done" view | M | feature |
| Board should auto-refresh when YAML files change on disk | M | feature |
| Context analysis v2 — track all tool usage, not just Read | M | feature |

## Key Deliverables

### Card Redesign
- Badges reorganized: comment/category/priority on line 1, sprint/complexity on line 2
- Timestamp contrast fixed (`#27272a` → `#a1a1aa`)

### Show Archived Bug Fix
- Checkbox and select styling improved (font size, color contrast)
- Empty done state message has subtle background highlight

### Done View
- New "Done" tab in board navigation
- Completed items grouped by sprint (descending), with handover metadata (theme, date, tests, commits)
- Clickable cards with side panel support (same as board)
- All filters (sprint, priority, category, tags, search) apply
- Sprint groups auto-expand when search query is active

### Board Auto-Refresh
- `backlog_dir_mtime()` pure function polls max YAML file mtime
- 2-second timer triggers board refresh on disk changes
- No spurious refresh on first load (seeded with real mtime)

### Context Analysis v2
- New `post-tool-logger.sh` tracks 6 tool types: Read, Grep, Glob, Bash, WebFetch, Agent
- Tool-specific field extraction (file/offset for Read, pattern/path for Grep, command for Bash, etc.)
- `analyze_tool_usage()` breaks down by tool type in reports
- Legacy `reads-*.jsonl` backward compatibility maintained

## Architecture Changes

- `.claude/hooks/post-tool-logger.sh` — new unified hook script
- `.claude/settings.json` — 6 PostToolUse matchers (was 1)
- `src/agile_backlog/pure.py` — `backlog_dir_mtime()`, `group_done_by_sprint()`, `parse_sprint_handover()`
- `src/agile_backlog/app.py` — Done view, card redesign, auto-refresh timer, archive styling
- `src/agile_backlog/context_report.py` — `analyze_tool_usage()`, multi-tool log support
- `tests/test_pure.py` — +19 tests (card, done grouping, mtime, handover parser)
- `tests/test_context_report.py` — +7 tests (multi-tool parsing, legacy compat)

## Known Issues

- Done view filter logic duplicates board filtering (could extract shared helper)
- Hook settings.json repeats same command block for each tool matcher (format limitation)
- Post-read-logger.sh kept as legacy fallback but superseded by post-tool-logger.sh

## Test Coverage

- 264 tests (up from 245, +19 new)
