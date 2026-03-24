# Sprint 21 Handover — UI Polish + Quality Gates

**Date:** 2026-03-24
**Branch:** sprint21/main
**Tests:** 224 (was 216)
**Commits:** 5 (2 features + 3 fixes)

## Completed Tasks (7/6 — 1 bonus bug fix)

| Item | Size | Category | Tags |
|------|------|----------|------|
| Systematic XSS prevention — safe_html helper | S | chore | ui |
| Markdown for comments | S | feature | ui |
| Review comments feature | S | feature | ui |
| Archiving done items — configurable days | M | feature | ui |
| Image paste in Add dialog | M | feature | ui |
| Auto-reload on data changes | M | feature | ui |
| Board scroll fix (bonus) | S | bug | ui |

## Key Deliverables

### safe_html Helper
Single escape function `safe_html()` in `pure.py` — all user content passes through this. Removed `import html as _html` from `components.py` entirely. 5 new XSS tests including script injection via card titles.

### Markdown Comments
Comments now render via `ui.markdown()` instead of escaped plaintext. Supports bold, links, code, lists. NiceGUI's DOMPurify sanitization handles XSS — no `html.escape()` needed for markdown content. Comment layout restructured from monolithic `comment_thread_html` to per-comment NiceGUI elements with resolve buttons inline.

### Configurable Archive Days
`archive_days` setting in `.claude/sprint-config.yaml` (default: 7). Compact dropdown (7d/14d/30d/90d) next to "Show archived" toggle on the board. Changes persist to config file. 3 new config tests.

### Image Paste in Add Dialog
Cmd+V pastes images in the Add Item dialog. Images stored in memory as base64 until save, then written to `backlog/images/{item-id}/`. Preview thumbnails with remove buttons. Separate JS paste listener (`_mcAddPasteListenerAdded`) avoids conflict with side panel listener.

### Auto-Reload
2-second polling timer checks max mtime of `backlog/*.yaml` files. If changed, triggers `render_board.refresh()`. Skips initial load to avoid double-render.

### Board Scroll Fix
`overflow:hidden` on main content prevented all scrolling. Changed to `overflow:auto` and added `overflow-y:auto` to each board column.

## Key Decisions

1. **safe_html over lint rule** — a wrapper function is simpler and more enforceable than a custom ruff check. All `_html.escape` calls migrated in one pass.
2. **ui.markdown for comments, not custom renderer** — NiceGUI's built-in markdown with DOMPurify is safe and handles all common formatting. No new dependency needed.
3. **Dropdown over number input** — initial number input looked jarring in the header. Compact select with preset values (7d/14d/30d/90d) matches the existing design language.
4. **Polling over watchfiles** — 2s `ui.timer` is simpler than async file watchers and works cross-platform. Acceptable latency for a local dev tool.

## Architecture Changes

- `pure.py` — `safe_html()` helper function
- `components.py` — all `_html.escape` → `safe_html`; removed `import html`; comment rendering restructured to per-comment NiceGUI elements with `ui.markdown()`; image delete by entry reference; image filename path traversal guard
- `app.py` — `get_backlog_dir` import; image paste in Add dialog with in-memory pending storage; auto-reload timer; configurable archive days via select dropdown; board overflow fix
- `config.py` — `get_archive_days()` / `set_archive_days()`
- `.claude/sprint-config.yaml` — `archive_days: 7` setting

## Known Issues

- Dual paste listeners (side panel + Add dialog) both fire if both are open simultaneously — edge case
- Auto-reload timer can cause brief double-refresh if save and poll overlap

## Test Coverage

- 224 tests (up from 216)
- +5 tests for safe_html and XSS prevention
- +3 tests for archive_days config

## Recommendations for Next Sprint

1. **Complete BigQuery-connector adoption** — validate the full adoption guide with install-skills
2. **GitHub Actions CI** (P2) — still no automated CI on push
3. **Settings page/panel** — as more config options appear, a dedicated settings area would be cleaner than cramming controls into the header
4. **Show sprint number on board cards** (P2) — tagged for future sprint
