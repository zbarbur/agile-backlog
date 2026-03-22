# Backlog View Redesign — Phase 1 Polish (UI Bug Fix Pass)

**Date:** 2026-03-22
**Status:** Draft
**Sprint:** 15
**Addresses bugs:** 14 items from smoke test

## Goal

Fix all UI bugs from the Phase 1 smoke test and elevate the backlog planning view to Linear/Notion-quality design: clean, minimal, high contrast, directly editable.

## Design Decisions (from brainstorming)

| Decision | Choice |
|----------|--------|
| Visual style | Linear/Notion — minimal, clean, muted accents |
| Section layout | Resizable panels with drag handles + zoom/focus button |
| Panel width | 50% when open |
| Card density | Two-line: title+badges on row 1, tags+timestamp on row 2 |
| Move-to buttons | Hover-only, bottom of card |
| Panel metadata | Two rows of pills (core metadata + tags) |
| Edit experience | Click-to-edit inline (no Edit button), Linear-style |
| Comments | iMessage chat layout — user right (blue), agent left (gray) |
| Filter chips | Inline in filter bar (no duplicate row) |
| Sorting | Sort button in filter bar with active sort label |
| Timestamps | Relative time on each card ("2h", "3d", "1w"), muted |

## Bugs Fixed

### Layout & Scroll
1. **vnext-and-vfuture-sections-hidden-below-scroll** — Replace page-level scroll with three resizable sections, each with independent inner scroll. All sections always visible. Drag handles between sections to resize. Zoom button (⤢) on each section header to expand/restore.
2. **side-panel-scrolls-with-page** — Side panel uses position:fixed (or flex column with overflow-y:auto). Panel body scrolls independently. Comment input pinned to bottom.
3. **header-and-filter-bar-scroll-off-screen** — Header and filter bar are flex-shrink:0 in a column layout. Main content area fills remaining height. No page-level scroll.

### Section Headers
4. **backlog-section-header-missing** — Each section has a prominent header: arrow icon (▼/▶) + section label (uppercase, colored) + item count badge + zoom button. Colors: Backlog=#71717a (gray), vNext=#ca8a04 (gold), vFuture=#22c55e (green).

### Card Design
5. **backlog-cards-missing-priority-border-priority-badge-tags** — Unify card design. Two-line cards with: left border (colored for P0/P1, transparent for P2+), title + badges on row 1 (comment badge + category + priority), tags + relative timestamp on row 2. P3 items have muted title text.
6. **move-to-buttons-should-be-at-bottom-of-card** — Move buttons hidden by default, appear on hover as a floating action bar at bottom-right of card. Not shown on selected card.

### Side Panel
7. **side-panel-metadata-too-spread-out** — Replace 7-row grid with two rows of inline pills. Row 1: status, phase, priority, complexity, category. Row 2: tags + "+ tag" pill + "updated X ago" timestamp.
8. **no-visual-focus-indicator-on-selected-card** — Selected card gets: `background:rgba(59,130,246,0.06)` + `border-left-color:#3b82f6`. Selection state persists until panel is closed or different card clicked.
9. **edit-button-closes-side-panel** — Remove the Edit button entirely. All fields are directly editable inline:
   - **Title:** Click → input field with blue border, auto-save on blur/Enter
   - **Metadata pills:** Click → dropdown overlay with options, select to save
   - **Tags:** Click existing tag to remove, click "+ tag" to add from autocomplete
   - **Text sections (description, AC, specs):** Click → textarea with Save/Cancel buttons
   - **Hover affordance:** All editable fields show subtle border on hover

### Header & Filters
10. **backlog-view-header-needs-design-overhaul** — Clean header: logo + Board/Backlog tab toggle + "Add Item" button. No sprint badge in backlog view (irrelevant — sprint context is in section headers). "Show archived" toggle is board-view only.
11. **active-filter-shown-twice** — Remove the duplicate chip row below filters. Active filters shown as inline removable chips within the filter bar itself, next to the dropdowns.

### Comments
12. **comments-need-chat-style-layout** — iMessage-style alignment:
    - **User messages:** Right-aligned, blue-tinted background (`rgba(59,130,246,0.12)`), rounded corners with flat bottom-right
    - **Agent messages:** Left-aligned, dark gray background (`#18181b`), rounded corners with flat bottom-left
    - **Flagged:** Red left border on the bubble
    - **Resolved:** 35% opacity, no strikethrough (cleaner)
    - **Max width:** 82% of thread width
    - **Meta line:** author icon + name + date, aligned to bubble side

### Additional Polish
13. **done-item-still-look-deleted-an-faded** — In scope (card styles are being unified). Done items on board should look complete with a subtle green-gray tint, not deleted/faded. Reduce opacity to 0.7 (not 0.65) and use a muted green-tinged text color instead of pure gray.
14. **we-re-in-sprint-15-but-it-s-displayed-sprint-13** — Fix `detect_current_sprint()` function to check `config.get_current_sprint()` first, fall back to inference from doing items second. Currently the config check happens at call sites, not in the function itself. Move it into the function for a single source of truth.

## Layout Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER  [agile-backlog]    [Board|Backlog]      [+ Add]    │  ← flex-shrink:0
├─────────────────────────────────────────────────────────────┤
│ FILTERS [Priority▾][Category▾] bug✕ [Tags▾] │↓Pri│ Search  │  ← flex-shrink:0
├──────────────────────────────┬──────────────────────────────┤
│ ▼ BACKLOG              14 ⤢ │  ✕                           │
│ ┌──────────────────────────┐│  Title (click to edit)       │
│ │ Item title    bug P1  2h ││                              │
│ │  [ui]                    ││  [backlog][plan][P1][S][bug]  │
│ ├──────────────────────────┤│  [ui][design][+ tag]  2h ago │
│ │ Item title  feat P2  3d  ││  ─────────────────────────── │
│ │  [ui][planning]          ││  DESCRIPTION                 │
│ └──────────────────────────┘│  Click to edit...            │
│ ═══ drag handle ═══════════ │  ─────────────────────────── │
│ ▼ vNEXT — Sprint 16    2 ⤢ │  COMMENTS                    │
│ │ Bundled plugin feat P2 3d││       [user msg blue] →      │
│ ═══ drag handle ═══════════ ││  ← [agent msg gray]         │
│ ▶ vFUTURE — Sprint 17+ 1 ⤢ ││       [user msg flagged] →  │
│                             │├─────────────────────────────┤
│                             ││  [Write a comment...]  Send │  ← pinned
└─────────────────────────────┴──────────────────────────────┘
```

## Card Row HTML Structure

```
┌─────────────────────────────────────────────────────────┐
│ ▎ Title of the backlog item          ●2  feature  P2   │  ← row 1
│ ▎  [ui] [planning]                                 3d  │  ← row 2
│                              [→ vNext] [→ vFuture]     │  ← hover only
└─────────────────────────────────────────────────────────┘
```

- Left border: 2px, colored for P0 (#ef4444) and P1 (#f87171), transparent for P2+
- Comment badge: red dot + count for unresolved flagged, blue for total, hidden if none
- Category badge: colored pill (bug=pink, feature=blue, docs=green, chore=purple)
- Priority badge: colored pill (P0=red, P1=red, P2=amber, P3=gray, P4=dim gray)
- Tags: muted gray pills
- Timestamp: very muted, right-aligned ("2h", "3d", "1w", "Mar 15")
- P3 items: muted title text color (#71717a)

## Click-to-Edit Behavior

| Field | View State | Hover | Click | Save |
|-------|-----------|-------|-------|------|
| Title | Bold text | Subtle border appears | Input field, blue border | Blur or Enter |
| Status | Pill | Subtle border | Dropdown: backlog/doing/done | Select |
| Phase | Italic pill | Subtle border | Dropdown: plan/spec/build/review | Select |
| Priority | Colored pill | Subtle border | Dropdown: P0-P4 with color dots | Select |
| Complexity | Green pill | Subtle border | Dropdown: S/M/L | Select |
| Category | Colored pill | Subtle border | Dropdown: bug/feature/docs/chore | Select |
| Tags | Gray pills | — | Click tag to remove | Immediate |
| + tag | Dashed pill | Solid border | Autocomplete input | Enter or select |
| Description | Text block | Subtle border | Textarea + Save/Cancel | Save button |
| AC | Bulleted list | Subtle border | Textarea (one per line) + Save/Cancel | Save button |
| Tech Specs | Bulleted list | Subtle border | Textarea (one per line) + Save/Cancel | Save button |

**Dropdown behavior:**
- Appears below the pill, floating over content (no layout shift)
- Dark background (#18181b), subtle border, shadow
- Options show color dots for priority/category
- Current value marked with checkmark
- Click outside or Escape to close without saving
- Click option to select and close

**Text field behavior:**
- Click text → transforms to textarea with blue border
- Original text pre-filled
- Save/Cancel buttons appear below
- Cancel or Escape: restore original text
- Save or Cmd+Enter: persist and refresh

## Resizable Sections

- Drag handles between sections: thin line, highlights blue on hover
- Cursor changes to `row-resize` on hover
- Drag to adjust vertical space allocation
- Minimum height per section: 44px (header only when collapsed)
- Zoom button (⤢) on each section header: click to expand section to full height, other sections collapse to header-only. Click again to restore previous proportions.
- Sections remember proportions during the session

## Sort Control

- Sort button in filter bar: `↓ Priority` (default)
- Click → dropdown with options:
  - Priority (high → low) — default
  - Priority (low → high)
  - Updated (newest first)
  - Updated (oldest first)
  - Created (newest first)
  - Title (A → Z)
- Active sort shown on button label
- Sort applies per-section (all sections use same sort)

## Relative Timestamp Format

| Age | Display |
|-----|---------|
| Today | "today" |
| 1-6 days | "Xd" |
| 1-4 weeks | "Xw" |
| > 4 weeks | "Mon DD" (e.g. "Mar 15") |

Implemented as a pure function: `relative_time(dt: date) -> str`. Note: BacklogItem.updated is a `date` (no time component), so sub-day granularity is not possible — "today" is the finest resolution.

## Color Palette (refined)

### Backgrounds
| Element | Color |
|---------|-------|
| Page background | #09090b |
| Card hover | rgba(255,255,255,0.03) |
| Card selected | rgba(59,130,246,0.06) |
| Side panel | #0c0c0e |
| Dropdown | #18181b |
| Input field (editing) | #18181b |
| Section header hover | rgba(255,255,255,0.02) |

### Text
| Element | Color |
|---------|-------|
| Primary text (titles) | #e4e4e7 |
| Secondary text (descriptions) | #9ca3af |
| Muted text (P3 titles) | #71717a |
| Labels (section headers) | varies by section |
| Timestamps | #27272a |
| Placeholder text | #3f3f46 |

### Borders
| Element | Color |
|---------|-------|
| Section dividers | #18181b |
| Card selected border | #3b82f6 |
| Input focus border | #3b82f6 |
| Hover affordance border | #27272a |
| Resize handle (hover) | #3b82f6 |

### Category Colors (unchanged)
| Category | Text | Background |
|----------|------|------------|
| bug | #f472b6 | rgba(244,114,182,0.08) |
| feature | #60a5fa | rgba(59,130,246,0.08) |
| docs | #34d399 | rgba(52,211,153,0.08) |
| chore | #a78bfa | rgba(167,139,250,0.08) |

### Priority Colors (unchanged)
| Priority | Text | Background |
|----------|------|------------|
| P0 | #ef4444 | rgba(239,68,68,0.1) |
| P1 | #f87171 | rgba(248,113,113,0.1) |
| P2 | #fbbf24 | rgba(251,191,36,0.1) |
| P3 | #6b7280 | rgba(107,114,128,0.08) |
| P4 | #4b5563 | rgba(75,85,99,0.08) |

## Files to Modify

| File | Changes |
|------|---------|
| `src/agile_backlog/app.py` | Replace `_render_backlog_list`, `_render_side_panel_content`, `render_backlog_card_html`, `render_comment_html`, `comment_thread_html`. Update `kanban_page` header/filter rendering. Add `relative_time` pure function. Add click-to-edit NiceGUI components. |
| `tests/test_app.py` | Update tests for `render_backlog_card_html` (new structure), `render_comment_html` (chat style), add tests for `relative_time`, `comment_thread_html` updates. |

## Board View Impact

The board (Kanban columns) adopts the same card design AND edit experience as the backlog view:

**Unified card rendering:** Merge `render_card_html` and `render_backlog_card_html` into a single `render_card_html` function used by both views:
- Same two-line layout: title + badges on row 1, tags + timestamp on row 2
- Same priority left border, category/priority badges, comment badge
- Board cards show move buttons (→ doing, → done) on hover — same hover pattern as backlog
- Board's "Show archived" toggle stays in the header but only renders when Board tab is active
- Done column cards keep reduced opacity but use a subtle green-gray tint instead of faded/deleted look (fixes bug 13)

**Unified edit experience:** Clicking a board card opens the same side panel with click-to-edit — replacing the current modal dialog (`_render_detail_modal_content`). One side panel component shared between both views. This means:
- Remove `_render_detail_modal_content` (replaced by side panel)
- Remove `_show_edit_dialog` (replaced by inline editing in side panel)
- Board view gets the same 50/50 split layout when a card is clicked
- One code path for viewing and editing items, regardless of which tab you're on

**Files affected:** `render_card_html`, `_render_card`, `_render_detail_modal_content` (remove), `_show_edit_dialog` (remove), `kanban_page` layout in `app.py`, plus `TestRenderCardHtml` in `test_app.py`.

## What Does NOT Change

- Data model — no schema changes
- CLI — no changes
- YAML files — no migration needed

## Verification

1. `ruff check .` — lint clean
2. `ruff format --check .` — format clean
3. `pytest tests/ -v` — all tests pass
4. Header is sticky, filters inline, no duplicate chips
5. Three sections always visible with resize handles
6. Cards show two-line layout with priority border, badges, tags, timestamp
7. Move buttons appear on hover only
8. Side panel: click-to-edit works for all fields
9. Comments display as iMessage-style chat
10. Selected card highlighted with blue border
11. Side panel scrolls independently, comment input pinned
12. Sort button works with multiple sort options

## Mockups

Visual mockups created during brainstorming session at:
`.superpowers/brainstorm/90989-1774210446/`
- `full-redesign-v2.html` — full page layout
- `panel-edit-inline.html` — click-to-edit interaction states
- `card-density-v2.html` — card density comparison
- `panel-metadata.html` — metadata layout comparison
