# Sprint 15 Handover

**Theme:** Backlog View Redesign Phase 1 + Polish
**Duration:** 2026-03-22 to 2026-03-23
**Branch:** sprint15/main → merged to main via PR #14

## Completed (18 items)

### Main Features

| Item | Complexity | Key Files |
|------|-----------|-----------|
| Sprint planning tool — backlog sections (Phase 1) | L | pure.py, components.py, app.py, styles.py, models.py, tokens.py, cli.py |
| Show done checkbox → archive-done | S | pure.py, app.py |
| Expand priority levels P0-P4 | folded | models.py, tokens.py |
| Tags revisited — CLI filter + migration | folded | cli.py, models.py |

### UI Bugs Fixed (14 items)

- Backlog cards missing priority border, badges, tags
- Backlog section headers missing labels
- vNext/vFuture hidden below scroll
- Side panel scrolls with page
- Header/filter bar not sticky
- Side panel metadata too spread out
- No selected card focus indicator
- Edit button closes side panel
- Comments not chat-style
- Move-to buttons inline instead of hover
- Backlog view header design overhaul
- Active filter chips shown twice
- Done items look deleted/faded
- Sprint 13 displayed instead of 15

## Deferred

| Item | Reason |
|------|--------|
| Sprint planning tool — drag-and-drop (Phase 2) | Phase 2 scope, stays in doing |
| Keyboard navigation | Phase 2 scope |

## Architecture Changes

### Module Split
`app.py` (1872 lines) was split into 4 focused modules:
- `pure.py` (224 lines) — framework-independent pure functions
- `styles.py` (229 lines) — CSS constants, design tokens
- `components.py` (~700 lines) — NiceGUI UI components
- `app.py` (475 lines) — page layout, routing

### Data Model
- Priority: `Literal["P1","P2","P3"]` → `Literal["P0","P1","P2","P3","P4"]`
- Category: `str` → `Literal["bug","feature","docs","chore"]` with migration validator
- `agent_notes` → `comments` field rename with backwards-compat validator
- 61 YAML files migrated via `agile-backlog migrate`

### UI
- Unified `render_card_html` for both board and backlog views (two-line design)
- Click-to-edit side panel replaces modal edit dialog (shared by both views)
- iMessage-style chat comments (user right/blue, agent left/gray)
- Three-section backlog layout (Backlog/vNext/vFuture) with zoom
- Sticky header, inline filter chips, sort button
- Archive-done (7-day default) replaces show-done checkbox

### CLI
- `--tags` filter on `list` command
- `migrate` command with `--dry-run`
- `stop` and `restart` server commands
- P0-P4 priority choices, category enum choices

## Key Decisions
- Linear/Notion visual style — minimal, clean, muted accents
- Click-to-edit inline (no Edit button) — matches Linear/Notion patterns
- Cards unified across board and backlog — one `render_card_html` function
- Phase/review badges removed from cards (visible in side panel only)
- Category/priority background alphas lowered for subtlety
- XSS escaping added to all HTML-rendered user content

## Test Coverage
- 156 tests (up from 117)
- New test file: `tests/test_pure.py` for all pure function tests
- Key new test classes: TestRelativeTime, TestGroupItemsBySection, TestRenderCommentHtml (chat style)

## Known Issues
- Sprint planning tool still in `doing` — Phase 2 (drag-and-drop, keyboard nav) not started
- `cli.py` may have stale `agent_notes` references from another session modifying the file
- Resizable sections use flex + zoom button (no drag handles) — `ui.splitter` was considered but flex was simpler

## Post-Sprint: Framework Integration Specs

After the sprint closed, two design specs were written for the Agentic Agile Framework integration:

1. **Framework Integration** (`docs/superpowers/specs/2026-03-23-agentic-agile-framework-integration.md`)
   - Generic sprint skills with `sprint-config.yaml` (portable across projects)
   - `/sprint-execute` skill (automated execution with specialist agents)
   - Process docs adoption from agentic-agile-template
   - VoltAgent specialist agent integration (133 available, ~14 relevant)

2. **Export to Template** (`docs/superpowers/specs/2026-03-23-export-to-agentic-agile-template.md`)
   - Replace KANBAN.md/TODO.md with agile-backlog
   - Migration tools (`import-kanban`, `import-todo`)
   - `specialist` field on BacklogItem model
   - Sprint-execute as the template's missing automation layer

Both specs reviewed and tracked as P1 backlog items.

## Recommendations for Next Sprint
- **Agentic Agile Framework integration** — the two P1 specs above are the major next initiative
- Complete Phase 2: drag-and-drop between sections, keyboard navigation
- Fix backlog section drag resize (bug logged)
- Review `cli.py` for consistency with the `comments` field rename
- The `components.py` file (~700 lines) may benefit from further splitting as more features are added
