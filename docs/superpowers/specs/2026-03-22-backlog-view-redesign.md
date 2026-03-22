# Backlog View Redesign — Planning View with Sections + Chat Comments

**Date:** 2026-03-22
**Status:** Approved
**Backlog Items:** sprint-planning-tool-backlog-sections-drag-and-drop, be-able-to-sort-the-board, do-a-design-review-of-the-backlog-grid, expand-priority-levels-add-p0-critical-and-p4-icebox

## Goal

Replace the current raw backlog table with a polished card-list planning view. Three collapsible horizontal sections (Backlog / vNext / vFuture), "move to" buttons between sections (Phase 1) with drag-and-drop (Phase 2), filtering on Backlog only, side panel with detail view and chat-like comment thread.

## Phasing

This is split into two phases to manage complexity:

**Phase 1 — Core Planning View:**
- Data model changes (categories, priorities, comments rename)
- Three-section card-list layout with collapsible sections
- "Move to" buttons for moving items between sections
- Side panel using existing dialog-based editing
- Chat-like comments display with flag/resolve
- Sorting within sections
- Filtering (Backlog section only)

**Phase 2 — Polish:**
- Drag-and-drop between sections
- Inline click-to-edit fields in side panel
- Keyboard navigation (up/down arrows between items)

## Data Model Changes

### Categories — strict work type (single value)

Change `category: str` to `category: Literal["bug", "feature", "docs", "chore"]`:

| Value | Meaning |
|---|---|
| `bug` | Something broken |
| `feature` | User-facing functionality |
| `docs` | Documentation |
| `chore` | Non-user-facing work (infra, tech-debt, tooling, CI) |

**Model validator required** — add `migrate_old_categories` (same pattern as existing `migrate_old_phases`):
- `infra` → `chore` (add `infra` to tags)
- `tech-debt` → `chore` (add `tech-debt` to tags)
- `security` → `feature` (add `security` to tags)
- Any unknown category → `chore` (safe fallback)

This ensures old YAML files load correctly without requiring a migration script to have run first.

### Comments — rename `agent_notes` to `comments`

Rename the field from `agent_notes: list[dict]` to `comments: list[dict]`.

**Model validator required** — add `migrate_agent_notes_to_comments`:
- If YAML has `agent_notes` key, move value to `comments`
- Supports `author` values: `"user"` and `"agent"`

Update all code references: `app.py`, `cli.py`, `yaml_store.py`, tests, `schema.yaml`.

### Tags — freeform domain labels (multi-value)

The `tags` field already exists on BacklogItem. Starting set:
- `ui`, `cli`, `comments`, `planning`, `packaging`, `data`
- Tags grow organically — no enum enforcement

### Priority — expand to 5 levels

| Value | Name | Color | Meaning |
|---|---|---|---|
| `P0` | Critical | `#ef4444` (bright red) | Drop everything |
| `P1` | High | `#f87171` (red) | Must do this sprint |
| `P2` | Medium | `#fbbf24` (amber) | Should do soon |
| `P3` | Low | `#6b7280` (gray) | Nice to have |
| `P4` | Icebox | `#4b5563` (dim gray) | Acknowledged, not planned |

**Update `PRIORITY_ORDER` in `tokens.py`** to `{"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}`.

**Update `PRIORITY_COLORS` in `tokens.py`** to include P0 and P4.

**Add `chore` to `CATEGORY_STYLES` in `tokens.py`** with dark-theme-appropriate colors.

**Fix `category_style()` fallback** — current fallback `#f3f4f6` is a light-theme color, change to dark-theme default.

### Migration

Two-layer approach:
1. **Model validators** (always active) — handle old field names and enum values on load
2. **Migration CLI command** (one-time) — bulk-update YAML files to new format + auto-tag based on title keywords

## Layout — Three Sections

```
┌─────────────────────────────────────────────────────────┐
│ [Filters: priority, category, tags, search]             │
│ (filters apply to Backlog section ONLY)                 │
├─────────────────────────────────────────────────────────┤
│ ▼ BACKLOG (unplanned)                              [14] │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ▎ Drag-and-drop between columns    feature  ui    │   │
│ │ ▎ GitHub Actions CI workflow        chore packaging│   │
│ │ ▎ YAML schema — convert to JSON     chore  data   │   │
│ │ ...                                               │   │
│ └───────────────────────────────────────────────────┘   │
│                                                         │
│ ▼ vNEXT — Sprint 15                                [3]  │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ▎ Bundled Claude plugin             feature cli 🔴1│   │
│ │ ▎ CLI docs — command reference      docs    cli   │   │
│ └───────────────────────────────────────────────────┘   │
│                                                         │
│ ▼ vFUTURE — Sprint 16+                             [1]  │
│ ┌───────────────────────────────────────────────────┐   │
│ │ ▎ MCP server for board API          feature data  │   │
│ └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Section definitions

- **Backlog** — `sprint_target` is null AND `status` is `backlog` (unplanned)
- **vNext** — `sprint_target` = current sprint + 1
- **vFuture** — `sprint_target` >= current sprint + 2
- **P4/Icebox items** — hidden by default in all sections, toggle to show
- **Done/Doing items** — not shown in backlog view (they appear on the board)

### Current sprint resolution

Use `config.get_current_sprint()` first (explicit config). If null, fall back to `detect_current_sprint()` (inferred from doing items). If both null, vNext and vFuture sections are empty and all items appear in Backlog.

### Section behavior

- All sections **collapsible** with item count in header
- **Phase 1:** "Move to" buttons on each row (→ vNext, → vFuture, → Backlog)
- **Phase 2:** Drag-and-drop rows between sections → auto-sets `sprint_target`
  - Drop into Backlog → `sprint_target = null`
  - Drop into vNext → `sprint_target = current + 1`
  - Drop into vFuture → `sprint_target = current + 2`
- **Filters** (priority, category, tags, search) apply to **Backlog section only**
  - This is intentionally different from the board view where filters apply to all columns
- vNext and vFuture remain **unfiltered and always visible**
- **Sorting** within each section: default by priority (P0 first), then by updated date

## Card Row Design

Each row in the card list:

```
┌─────────────────────────────────────────────────────────┐
│ ▎ Title of the backlog item              🔴1    [S]     │
│ ▎ [feature] [ui] [cli]                                  │
└─────────────────────────────────────────────────────────┘
```

- **Left border** — 3px colored bar for priority (P0/P1 = red, P2 = amber, P3/P4 = invisible)
- **Title** — primary text, truncated with ellipsis if too long
- **Comment badge** — red (unresolved flagged count) or blue (total count), right-aligned
- **Complexity badge** — S/M/L in outlined pill, right-aligned
- **Second line** — category pill + tag chips
- **Hover** — subtle background highlight
- **Click** — opens side panel

## Side Panel

Click a row → side panel opens on the right, list narrows on the left.

### Phase 1 implementation

Use a right-aligned `ui.dialog` with custom CSS positioning, or a two-column flexbox layout where the right column is conditionally rendered. The panel reuses the existing edit dialog pattern — an "Edit" button opens the current edit dialog.

### Panel layout

```
┌──────────────────────────────────────┐
│ [← Close]                    [Edit]  │
│                                      │
│ Title                                │
│                                      │
│ Status: doing     Phase: build       │
│ Priority: P1      Complexity: M      │
│ Category: feature Sprint: 14         │
│ Tags: [ui] [planning]               │
│                                      │
│ ─── Description ───                  │
│ Full description text...             │
│                                      │
│ ─── Acceptance Criteria ───          │
│ ☑ Criterion 1                        │
│ ☐ Criterion 2                        │
│                                      │
│ ─── Technical Specs ───              │
│ • File: src/agile_backlog/app.py     │
│                                      │
│ ─── Comments ───                     │
│ ┌────────────────────────────────┐   │
│ │ 👤 user  3/22                  │   │
│ │ Research backlog best practices│   │
│ │                       [🚩 flag]│   │
│ └────────────────────────────────┘   │
│ ┌────────────────────────────────┐   │
│ │ 🤖 agent  3/22                │   │
│ │ Done — findings in memory      │   │
│ │                     [✓ resolve]│   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ Type a comment...    [🚩] [↑]  │   │
│ └────────────────────────────────┘   │
└──────────────────────────────────────┘
```

### Phase 2: Fields — click to edit (deferred)

All metadata fields become click-to-edit inline:
- Click priority → dropdown with P0-P4
- Click category → dropdown with bug/feature/docs/chore
- Click tags → chip input with autocomplete
- Click title → inline text edit
- Click description → textarea
- Click complexity → dropdown S/M/L

### Comments — chat-like thread

- Messages styled by author: **user** vs **agent** (distinct visual styles)
- Each message shows: author icon, timestamp, text
- **Flagged messages** — highlighted with a colored left border or flag icon, visually prominent
- **Resolved messages** — faded/muted, optionally collapsible
- **Input at bottom** — text field + flag toggle (checkbox or button) + send button
- **Resolve action** — per-message button to mark as resolved

### Panel transitions

- **Open** — appears on right, list width reduces (e.g., 60/40 split)
- **Close** — click close button, press Escape, or click outside panel
- **Phase 2:** Up/down arrows to navigate between items within and across sections

## Interactions Summary

| Action | Behavior | Phase |
|---|---|---|
| Click row | Open side panel with full details | 1 |
| Click "Move to" button | Move item to target section | 1 |
| Click section header | Collapse/expand section | 1 |
| Filter (Backlog only) | Filter by priority, category, tags, search | 1 |
| Click "Edit" in panel | Open existing edit dialog | 1 |
| Type in comment input | Add comment (with optional flag) | 1 |
| Click resolve on comment | Mark as resolved (faded) | 1 |
| Escape | Close panel | 1 |
| Drag row to another section | Move item, auto-set sprint_target | 2 |
| Click field in panel | Inline edit | 2 |
| Up/down arrows (panel open) | Navigate between items | 2 |

## Technical Approach

### Pure functions to extract and test

- `group_items_by_section(items, current_sprint)` → dict with backlog/vnext/vfuture lists
- `render_backlog_card_html(item)` → HTML string for card row
- `render_comment_html(comment)` → HTML string for single comment bubble
- `comment_thread_html(comments)` → HTML string for full comment thread

### Files to modify

- `src/agile_backlog/models.py` — category enum, priority enum, rename `agent_notes` → `comments`, add model validators for migration
- `src/agile_backlog/tokens.py` — add P0/P4 to `PRIORITY_ORDER` and `PRIORITY_COLORS`, add `chore` to `CATEGORY_STYLES`, fix fallback color
- `src/agile_backlog/schema.yaml` — update enums, rename agent_notes to comments (documentation only)
- `src/agile_backlog/app.py` — new backlog view replacing current table, side panel, chat comments, new pure functions
- `src/agile_backlog/cli.py` — update category/priority enums, update note/flagged commands for `comments` field
- `tests/` — update tests for new enums, add tests for new pure functions (`group_items_by_section`, `render_backlog_card_html`, etc.)

### NiceGUI components

- Card list rows: custom HTML rendering (like current `render_card_html`)
- Sections: `ui.expansion` or custom collapsible
- Side panel: right-aligned `ui.dialog` with custom CSS, or two-column flexbox with conditional right column
- Chat comments: custom HTML rendering + `ui.input` for new comments
- Move buttons: `ui.button` with click handlers that update `sprint_target` and re-render

### Migration CLI command

A one-time CLI command (`agile-backlog migrate`) to:
1. Migrate `infra`/`tech-debt` categories → `chore` + tag in YAML files
2. Rename `agent_notes` → `comments` in YAML files
3. Auto-tag existing items based on title keywords
4. Report changes for review before saving (dry-run mode)

Note: model validators handle migration transparently on load, so this command is optional but keeps YAML files clean.

## What Does NOT Change

- Board view (Kanban columns) — unchanged
- YAML file format — backwards compatible via model validators
- Detail modal on board view — unchanged (backlog uses side panel instead)

## What DOES Change

- CLI category/priority enum options expanded
- CLI `note`/`flagged` commands updated for `comments` field name
- Backlog view completely replaced
- Filter behavior: backlog view filters Backlog section only (board view unchanged)

## Verification

### Phase 1
1. `ruff check .` — lint clean
2. `ruff format --check .` — format clean
3. `pytest tests/ -v` — all tests pass
4. Old YAML files with `agent_notes`, `infra`, `tech-debt` load without error
5. Backlog view shows three sections with correct items
6. "Move to" buttons move items between sections
7. Filtering works on Backlog section only
8. Side panel opens with all fields and edit button
9. Chat comments display correctly with flag/resolve
10. P0/P4 priority levels render correctly
11. Category migration produces correct results

### Phase 2
12. Drag-and-drop moves items between sections
13. Inline click-to-edit works for all fields
14. Keyboard navigation between items works
