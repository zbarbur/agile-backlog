# Sprint 18 Handover — UI Polish + CLI Visibility

**Date:** 2026-03-24
**Branch:** sprint18/main
**Tests:** 193 (was 173)
**Commits:** 9 (1 sprint start + 3 features + 1 docs + 4 fixes)

## Completed Tasks (6/6)

| Item | Size | Category | Tags |
|------|------|----------|------|
| CLI list — add Phase and Sprint columns | S | feature | cli |
| CLI documentation — command reference + quickstart | M | docs | cli |
| Descriptions — markdown support | S | feature | ui |
| Drag-and-drop between columns | L | feature | ui |
| Paste image when creating/editing items | M | feature | ui |
| NiceGUI serve --reload crash (bonus bug fix) | S | bug | ui |

## Key Deliverables

### CLI List Columns
Added Phase and Sprint columns to default `list` table output. Empty values show "-". JSON output unchanged.

### CLI Documentation
Complete `docs/CLI.md` with install instructions, quickstart workflow, all 13 commands with options tables and examples, workflow phases, and priority/category reference.

### Markdown Rendering
Goal, description, and notes fields now render as markdown in the web UI side panel. Added dark-theme CSS for `.nicegui-markdown` elements (headers, code blocks, lists, blockquotes). Edit mode still shows raw text.

### Drag-and-Drop Between Kanban Columns
Board cards can now be dragged between backlog/doing/done columns. Uses the same JS drag/drop + hidden trigger pattern established in the backlog view. No external JS dependencies.

### Image Paste/Upload
Clipboard paste (Cmd+V) and file upload for attaching images to backlog items. Images stored in `backlog/images/{item-id}/`, displayed as base64 data URL thumbnails with click-to-view fullscreen dialog. Delete on hover.

**This feature required significant iteration (5 fix commits after initial implementation):**
1. `emitEvent()` doesn't exist in NiceGUI — replaced with hidden trigger pattern
2. `ui.image()` with local file paths unreliable — switched to base64 data URLs
3. JS paste listener duplicated on each refresh — moved outside `_refresh_images()`, added guard
4. Panel closed on paste/delete — separated image save from full board refresh
5. Thumbnails too small, upload widget unstyled — UX polish pass

### Serve --reload Fix
CLI `serve` command now defaults to `--no-reload` (opt-in with `--reload`). NiceGUI reload mode requires `ui.run()` at module level via `__mp_main__` guard, which doesn't work when launched through Click CLI. Pre-existing bug.

## Key Decisions

1. **Base64 data URLs for images** — NiceGUI's `ui.image()` with local file paths is unreliable. Base64 embedding works consistently but means images transit through WebSocket. Acceptable for backlog screenshots.
2. **No external JS dependencies** — drag-and-drop uses native HTML5 drag API + hidden trigger pattern, not SortableJS. Keeps the project dependency-free on the JS side.
3. **Reload mode opt-in** — `agile-backlog serve` defaults to `--no-reload` since reload mode is incompatible with CLI entry points in NiceGUI. Developers can use `--reload` explicitly.
4. **Images not git-tracked** — `backlog/images/` is in `.gitignore`. Images are local-only. Future: consider git-lfs or external storage.

## Architecture Changes

- `cli.py` — Phase + Sprint columns in list output; `--no-reload` → `--reload` flag flip
- `components.py` — `_render_images_section()` with paste/upload/display; markdown for goal/notes fields
- `styles.py` — `.nicegui-markdown` dark theme CSS; `.mc-upload` widget styling; `.mc-board-drop-zone` CSS
- `models.py` — `images: list[dict]` field added to BacklogItem
- `app.py` — board column drag-and-drop with JS handlers + hidden trigger
- `docs/CLI.md` — new, full command reference
- `.gitignore` — `backlog/images/` added

## Known Issues

- Image paste in Add Item dialog not supported (needs temp storage before save) — filed as backlog item
- Large images as base64 may be slow over WebSocket — acceptable for screenshots, consider compression for large files
- Reload mode still broken when using `--reload` flag via CLI (NiceGUI limitation)

## Lessons Learned

1. **Browser-to-NiceGUI communication is tricky** — `emitEvent()` doesn't exist. The hidden trigger + `ui.run_javascript()` pattern is the reliable bridge. Document this for future features.
2. **Image features need more design upfront** — paste-image required 5 rounds of fixes. NiceGUI's file handling, JS event bridging, and refresh lifecycle all interacted in unexpected ways. For complex browser-integration features, prototype the JS↔Python bridge first.
3. **Worktree agents need explicit commit instructions** — agents working in worktrees made changes but didn't commit, requiring manual diff extraction. Future: instruct worktree agents to commit their work.

## Test Coverage

- 193 tests (up from 173)
- +2 tests for CLI list columns
- +9 tests for markdown support
- +4 tests for image model fields
- +5 tests for drag-and-drop infrastructure

## Recommendations for Next Sprint

1. **CLI bulk operations (P2)** — still the most impactful QoL improvement (carried from Sprint 17)
2. **GitHub Actions CI (P2)** — automated CI on push
3. **Image paste in Add dialog** — filed this sprint, improves the UX flow
4. **Board auto-refresh on YAML changes (P3)** — useful when CLI and board are used together
5. **Delete items (P2)** — new item appeared during sprint, no way to delete items currently
