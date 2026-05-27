# Memory Index

## Project Status
- Sprint 30 COMPLETED (2026-05-26): Dashboard v2 Design + Debt Paydown
- Sprint 31 Planning — 5 dashboard-v2 implementation items + close 3 superseded source items
- 361 tests, ruff + format clean
- Current version: 0.30.0 (next release: 0.31.0)
- Current sprint: set in `.claude/sprint-config.yaml` (`current_sprint`)

## Sprint 30 Outcomes
- Dashboard v2 unified design doc: `docs/design/SPRINT30_DASHBOARD_V2_DESIGN.md` (468 lines, 7 decisions D1–D7, 5 decomposed items for S31)
- CLI bug fix: `edit` list flags now replace-by-default; `--append-*` opt-in preserves old behavior
- First slice of app.py refactor: Done view extracted to `src/agile_backlog/views/done.py` (app.py 1852 → 1565)

## Architecture
- NiceGUI dark theme, IBM Plex Mono + DM Sans
- Single Pydantic model in `models.py`; YAML store as single source of truth in `backlog/`
- Three views inlined in `kanban_page()` (app.py) — Done view extracted to `views/done.py` as proof-of-pattern. Context and Process view extractions still pending.
- Sprint state, version, and commands centralized in `.claude/sprint-config.yaml`
- Context analysis pipeline: `.claude/context-logs/*.jsonl` → `context_report.py` → JSON report → markdown summary → Done view rendering
- Skill quality scoring + cross-sprint trend comparison shipped Sprint 29

## Process
- Sprint skills (`/sprint-plan-next`, `/sprint-start`, `/sprint-execute`, `/sprint-end`) use `agile-backlog` CLI exclusively
- `agile-backlog flagged` at sprint start; phases: plan → spec → build → review → done
- CI: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
- Web UI: `.venv/bin/agile-backlog serve` (port 8501)
- Branch pattern: `sprint{N}/main`; merge to main via PR at sprint end

## Sprint 31 Candidate Pool (from Dashboard v2 design Section 3)
1. `dashboard-v2-actionable-prompt-registry-and-component` (S) — ships first; everyone uses it
2. `dashboard-v2-context-view-tools-categories-rereads-tabs` (M)
3. `dashboard-v2-process-view-guidelines-audit-tab` (M)
4. `dashboard-v2-skill-invocation-tracking-hook-and-skills-tab-usage` (L)
5. `dashboard-v2-hooks-permissions-claude-md-tab-enhancements` (M)

Plus close as superseded: `optimization-guidelines-dashboard`, `process-review-prompts-actionable…`, `design-session-context-and-process-dashboard-v2-…`

## On-Hold / Deferred
- `add-claude-code-terminal-session` — Node.js dependency concern; revisit when smaller "open in terminal with backlog context" alternative is pursued. Untagged; tagged `on-hold`.

## Lessons (from Sprint 30)
- Adopt remote sprint state before planning — `/sprint-plan-next` should fetch first to avoid building plans on stale main
- Closure-heavy views (Done, Context, Process) require careful parameter passing during extraction; use shared state-dict pattern from Sprint 29 to avoid stale closures
- CLI defaults matter for agent ergonomics — `edit` replace-by-default is the correct default; opt-in append handles the additive case
- Design + implementation in same sprint works only when scoped tightly (e.g. design + 1 small bug + 1 large refactor; no build of designed items in same sprint)
