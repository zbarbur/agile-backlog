# Sprint 19 Handover — CLI Power Tools + Adoption Guide

**Date:** 2026-03-24
**Branch:** sprint19/main
**Tests:** 204 (was 193)
**Commits:** 5 (1 sprint start + 1 features + 2 docs + 1 fixes)

## Completed Tasks (6/6)

| Item | Size | Category | Tags |
|------|------|----------|------|
| CLI sprint-status command | S | feature | cli, planning |
| CLI validate command | S | feature | cli, planning |
| CLI bulk operations (multi-ID move/edit, --sprint on move) | M | feature | cli |
| Agile-backlog adoption guide | M | docs | data |
| Remember backlog screen sizing (localStorage) | M | bug | ui |
| Edit item — preserve selection after save | S | bug | ui |

## Key Deliverables

### CLI sprint-status
New `sprint-status` command showing items grouped by phase with progress count. Reads current sprint from config, supports `--sprint N` override.

### CLI validate
New `validate` command checking sprint items have required spec fields (goal, complexity, >=2 acceptance criteria, >=1 technical spec). Exit code 1 on failure — usable as a CI gate.

### CLI Bulk Operations
`move` and `edit` now accept multiple item IDs (`nargs=-1`). `move` gains `--sprint` flag to set sprint target in the same call. Partial failures don't abort the batch — each item reports individually.

### Adoption Guide
`docs/guides/ADOPTION.md` — reusable runbook for onboarding agile-backlog into any existing project. Covers: installation, KANBAN.md import with AI-driven mapping heuristics and preview-confirm flow, sprint-config setup, skill adoption (merge not copy), statusline config, updating. Documents the known limitation that skills don't auto-update until the bundled plugin is shipped.

### View Mode Persistence
Active page (board/backlog) saved to `localStorage` and restored on page load. No more defaulting to board view every refresh.

### Edit Selection Fix
Side panel now re-selects the edited item after save via `reselect_fn` callback. Fixed in both backlog list and board views. The root cause was `_save_and_refresh()` calling `refresh_fn()` which rebuilt the view with fresh `panel_state = {"selected_id": None}`.

## Key Decisions

1. **Import as adoption guide, not a skill** — importing a KANBAN.md is a one-time operation per project. A permanent skill would be overengineered. Instead, the adoption guide teaches the agent the mapping heuristics inline.
2. **AI-driven import, not deterministic parser** — KANBAN.md formats vary too much (strikethrough, nested sections, inline sprint refs). AI handles ambiguity naturally. No brittle parser to maintain.
3. **Merge skills, don't blindly copy** — target projects may already have their own skills. The guide instructs agents to compare and integrate rather than overwrite.
4. **Plugin packaging deferred to Sprint 20** — skills distribution via `pip install` requires bundling as a Claude Code plugin. Tagged for next sprint.

## Architecture Changes

- `cli.py` — `sprint-status` and `validate` commands; `move` and `edit` changed from single `item_id` to `nargs=-1` tuple with per-item error handling; `move` gains `--sprint` option; `get_current_sprint` imported at module level
- `components.py` — `_render_side_panel_content` gains `reselect_fn` kwarg; `_save_and_refresh` calls `reselect_fn(item_id)` after refresh
- `app.py` — `_reselect_board_panel` and `_reselect_after_refresh` functions; `load_item` added to imports; localStorage save/restore for `ab_view_mode`; async `_restore_view` timer on page load
- `docs/guides/ADOPTION.md` — new file

## Known Issues

- localStorage persistence covers view mode only — selected item and panel open/close state are not yet persisted across full page reloads (only across in-page refreshes after edits)
- Sprint skills must be manually copied/merged into target projects until plugin packaging ships

## Lessons Learned

1. **Brainstorming shapes scope** — the import feature started as two separate items and ended as a documentation deliverable. The brainstorming session caught the overengineering early (skill for a one-time operation) and identified the real need (reusable adoption runbook).
2. **Bulk operations are backward compatible** — Click's `nargs=-1` accepts 1+ args, so all existing single-ID tests passed without modification after the change.
3. **NiceGUI state doesn't survive `@ui.refreshable`** — any mutable dict created inside a refreshable function resets on refresh. State that must persist (like selected item) needs to live outside the refresh boundary or be restored via callback.

## Test Coverage

- 204 tests (up from 193)
- +3 tests for sprint-status
- +3 tests for validate
- +5 tests for bulk operations (multi-ID move, multi-ID edit, --sprint flag, partial failures)

## Recommendations for Next Sprint

1. **Bundled Claude Code plugin** (P2, tagged Sprint 20) — ship skills with the pip package for auto-updates
2. **Delete items command** (P2) — still no way to delete items from CLI, carried from Sprint 18
3. **GitHub Actions CI** (P2) — automated CI on push, carried from Sprint 18
4. **Full localStorage persistence** — extend to selected item, panel state, filter selections
5. **Use the adoption guide** — onboard BigQuery-connector as the first real-world test
