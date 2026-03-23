# Sprint 16 Handover

**Theme:** Sprint Planning Phase 2 + Framework Integration
**Duration:** 2026-03-23
**Branch:** sprint16/main

## Completed (5 items)

### Features

| Item | Complexity | Key Files |
|------|-----------|-----------|
| Sprint planning Phase 2 — drag-and-drop + keyboard nav | L | components.py, styles.py |
| Agentic Agile Framework — sprint-config.yaml + skill refactoring | L | sprint-config.yaml, config.py, sprint-start/SKILL.md, sprint-end/SKILL.md |

### Bugs Fixed

| Item | Complexity | Key Files |
|------|-----------|-----------|
| UI shows Sprint 15 instead of current sprint number | S | sprint-config.yaml, config.py |
| Priority color border missing for P2+ items | S | pure.py |
| Backlog sections not resizable — drag handles don't work | M | components.py, styles.py |

## Deferred

| Item | Reason |
|------|--------|
| Complete framework integration — verify full spec adoption | Phase 1 done but needs verification against spec, added to Sprint 17 |

## Architecture Changes

### Framework Integration (Phase 1)
- Created `.claude/sprint-config.yaml` — central config for all sprint skills
- Sprint-start and sprint-end skills refactored to read commands from config via `{config_ref}` placeholders
- `config.py` migrated: reads `current_sprint` from `sprint-config.yaml` first, falls back to `.agile-backlog.yaml`
- `set_current_sprint()` uses regex replacement to preserve YAML comments/ordering (not `yaml.dump`)
- `.agile-backlog.yaml` deleted — `sprint-config.yaml` is the canonical location

### Drag-and-Drop (Backlog View)
- HTML5 Drag API with JS injected via `ui.run_javascript`
- JS→Python bridge: hidden `#mc-drop-trigger` element + `window._lastDrop` pattern
- Card rows get `draggable="true"` with `data-item-id` attributes
- Section content divs become `.mc-drop-zone` with `data-sprint-target`
- Drop auto-sets `sprint_target` (null for Backlog, N+1 for vNext, N+2 for vFuture)

### Keyboard Navigation
- Arrow keys navigate items across all three backlog sections
- Combined list: `filtered_backlog + vnext_items + vfuture_items`
- Side panel updates on navigation, scroll-into-view on focus change
- Click selection syncs with nav state so arrows continue from clicked item

### Drag-to-Resize
- Resize handles between sections use `mousedown`/`mousemove`/`mouseup` JS
- NiceGUI wraps elements in container divs — JS navigates to `handle.parentElement` (wrapper) before using `previousElementSibling`/`nextElementSibling`

### Process Docs
- `docs/process/DEFINITION_OF_DONE.md` — adopted from agentic-agile-template
- `docs/process/AGENTIC_AGILE_MANIFEST.md` — core principles and process flow

### CLI Fix
- `_kill_server()` now uses `os.killpg()` to kill uvicorn worker processes, not just the parent

## Key Decisions
- **sprint-config.yaml as canonical config** — replaces .agile-backlog.yaml, read by all sprint skills
- **Regex-based YAML writes** — `set_current_sprint` uses `re.sub` instead of `yaml.dump` to preserve comments and key ordering
- **NiceGUI wrapper navigation** — JS must go up to parent element before finding siblings due to NiceGUI's container wrapping
- **Hidden element click pattern** — simplest JS→Python bridge in NiceGUI for drag-and-drop callbacks
- **Process docs pulled from Phase 3 to Phase 1** — small markdown files, immediate value

## Known Issues
- Framework integration Phase 1 may have gaps vs spec — verification item added for Sprint 17
- `cli.py` may still have the `agile-backlog serve` hardcoded reference in sprint-start skill (should be config-driven)
- Drag-and-drop uses `window._lastDrop` global — rapid successive drops could theoretically race (unlikely in single-user)
- `set_current_sprint` doesn't create `.claude/` directory if it doesn't exist

## Test Coverage
- 162 tests (up from 156 in Sprint 15)
- New test file: `tests/test_config.py` (4 tests for config migration)
- Updated: `tests/test_pure.py` (P2/P3/P4 border tests)

## Recommendations for Next Sprint
- **Complete framework integration verification** (P1, Sprint 17)
- **Sprint-execute skill** (P1, Sprint 17) — the big automation piece
- **Template skills** (P2, Sprint 17) — /plan, /document, /report-bug, /fix-bug
- Specialist agent integration (P2, Sprint 18)
- Consider adding `--tags` to CLI `add` command (P3, quick win)
