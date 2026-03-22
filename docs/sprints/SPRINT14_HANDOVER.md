# Sprint 14 Handover

**Date:** 2026-03-22
**Theme:** Package portability + backlog planning design
**Commits:** 12
**Tests:** 117 (was 110)

## Completed

### Package Restructure (P1, tech-debt)
- Moved `src/*.py` → `src/agile_backlog/` for proper Python packaging
- All imports updated from `from src.` to `from agile_backlog.`
- `pyproject.toml` updated: dynamic versioning, build-system, package-data
- Public API: `from agile_backlog import BacklogItem, load_all`
- Added `py.typed`, `CHANGELOG.md`, `__version__ = "0.3.0"`
- Package now installable from git: `pip install git+https://github.com/zbarbur/agile-backlog.git`
- **Key files:** `src/agile_backlog/__init__.py`, `pyproject.toml`, `CHANGELOG.md`

### Comment Badge Bug Fix (P1, bug)
- Badge now shows red count for unresolved flagged comments, blue for total
- Extracted `comment_badge_html()` pure function for testability
- **Key files:** `src/agile_backlog/app.py`, `tests/test_app.py`

### CLI --json Output Flag (P2, feature)
- Added `--json` flag to `list`, `show`, and `flagged` commands
- Added `to_dict()` method on BacklogItem with date serialization
- 7 new tests
- **Key files:** `src/agile_backlog/cli.py`, `src/agile_backlog/models.py`, `tests/test_cli.py`

### CLAUDE.md Updates (P1, docs)
- Documented `.venv/bin/agile-backlog` as the CLI path
- Updated deps from Streamlit to NiceGUI
- Fixed stale `streamlit run src/app.py` command

### Sort the Board (P2, feature)
- Folded into backlog view redesign spec — sorting by priority within sections

### Hot Reload (P2, feature)
- Decided: solved-by-design — new backlog view with auto-save on field blur makes reloads harmless

## Deferred to Backlog
- Bundled Claude plugin — needs own brainstorm session
- Add flagged comments check to sprint-start — waiting for plugin work

## Still in Doing (Sprint 15 scope)
- Sprint planning tool (backlog view redesign) — spec complete, needs implementation plan
- Expand priority levels P0/P4 — part of backlog redesign Phase 1
- Tags revisited — category/tag taxonomy decided, part of backlog redesign Phase 1

## Key Decisions

1. **Package structure:** Adopted standard Python src layout (`src/agile_backlog/`), enabling git and future PyPI installs
2. **Category taxonomy:** Strict 4-value enum: `bug`, `feature`, `docs`, `chore`. Domain classification moves to tags.
3. **Tag system:** Freeform multi-value labels starting with `ui`, `cli`, `comments`, `planning`, `packaging`, `data`
4. **Priority levels:** Expanding from P1-P3 to P0-P4 (P0=critical, P4=icebox)
5. **Backlog view:** Card-list layout with 3 collapsible sections (Backlog/vNext/vFuture), side panel, chat-like comments
6. **Comments rename:** `agent_notes` → `comments` with model validator migration
7. **Phased delivery:** Phase 1 = core planning view + data model. Phase 2 = drag-and-drop + inline editing
8. **PyPI strategy:** Start with git installs, add PyPI publishing later (just a CI workflow, no code changes)

## Architecture Changes
- Package is now `agile_backlog` (was `src`)
- Dynamic versioning: `__version__` in `__init__.py` is single source of truth
- `[build-system]` table added to `pyproject.toml`

## New Backlog Items Created (12)
- CLI improvements: --json (done), --title alias, batch add, list columns, docs
- Packaging: bundled Claude plugin, GitHub CI, GitHub publish
- Planning: expand priorities, /check-comments command
- Data: YAML JSON schema
- Other: archiving done items

## Specs Written
- `docs/superpowers/specs/2026-03-22-package-restructure-design.md` (implemented)
- `docs/superpowers/specs/2026-03-22-backlog-view-redesign.md` (ready for Phase 1 planning)
- `docs/superpowers/plans/2026-03-22-package-restructure.md` (executed)

## Recommendations for Next Sprint
1. Write implementation plan for backlog view redesign Phase 1
2. Create sprint branch for the redesign (it's a big feature)
3. Start with data model changes (categories, priorities, comments rename) — they're mechanical and unblock everything
4. Research NiceGUI side panel and drag-and-drop feasibility early
