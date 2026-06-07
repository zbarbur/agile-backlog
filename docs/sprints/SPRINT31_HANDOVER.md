# Sprint 31 Handover — Native-transcript Foundation + Storybook Adoption Fixes

**Date:** 2026-06-07
**Branch:** sprint31/main -> pending merge to main
**Version:** 0.31.0

## Sprint Theme

Two threads: (1) built the **native Claude Code transcript ingestion layer** as the canonical data source for Dashboard v2 — and the dashboard features on top of it (cache-hit/real-cost, Context-view Tools/Categories/Re-reads tabs, actionable prompt registry); (2) cleared the first external client's (**storybook**) adoption-friction intake — three papercuts hit while pointing the tool at a pre-existing backlog.

## Completed Items (7/7)

| Item | Pri | Category | Cx | Key Files |
|------|-----|----------|----|-----------|
| Native transcript ingestion layer | P1 | feature | M | `src/agile_backlog/transcript.py` (new), `tests/test_transcript.py` |
| Actionable prompt registry + `prompt_button` | P1 | feature | S | `src/agile_backlog/prompts.py` (new), `components.py` |
| Cache-hit rate + real token cost | P1 | feature | S | `context_report.py`, `app.py` |
| Context view Tools/Categories/Re-reads tabs | P1 | feature | M | `pure.py`, `context_report.py`, `app.py` |
| install-skills exit-code (regression guard) | P2 | bug | S | `tests/test_cli.py` (test-only) |
| load_all() skips foreign/non-item YAML quietly | P2 | feature | S | `yaml_store.py`, `CLAUDE.md` |
| add command — richer edit flags | P3 | feature | S | `cli.py`, `tests/test_cli.py` |

## Key Decisions

- **Reverses Sprint 30's D2.** Sprint 30 rejected retroactive transcript parsing (deemed fragile) in favor of a forward-only `UserPromptSubmit` hook. Sprint 31 reversed this: Claude Code's native JSONL is far richer (real per-turn token usage, cache fields, `attributionSkill`, tool success) than the hook log. The parser degrades gracefully (empty, not error) on missing/changed formats, which mitigates the original fragility concern. `attributionSkill` also supersedes the planned skill-tracking hook.
- **`install-skills` "bug" was already fixed on `main`** (commit 8d304e5). The item became a regression guard — added the missing `exit_code == 0` assertions. Action item: tell storybook to upgrade.
- **`list-warns` re-estimated S (from M)** during speccing — one function in `yaml_store.py`; `.backlogignore` and an import/init command were deferred to Sprint 32.
- **Backlog sprint-folders** designed this sprint (three-tier `unplanned/ sprint{N}/ archive/`, folder derived from `sprint_target`), scheduled for Sprint 32. See `docs/superpowers/specs/2026-06-07-sprint-folder-backlog-organization-design.md`.

## Architecture Changes

- New `transcript.py` ingestion module: `parse_transcript`, `discover_transcripts`, typed `Session/Turn/Usage/ToolCall`, pure `cache_hit_rate`. This is the canonical data source other dashboard code now reuses.
- New pure `prompts.py` registry + `prompt_button` component — one implementation for all dashboard fix-prompt buttons.
- `context_report.py` gained cache-aware pricing (`MODEL_PRICING_PER_1M`, `usage_cost_usd`, `analyze_usage`) and `tool_category_breakdown`; `generate_sprint_report` took a backward-compatible optional `transcript_sessions` kwarg.
- Context view refactored from a flat layout into tabs (Overview preserved intact).
- `load_all()` no longer emits per-file pydantic warnings; underscore-prefixed files/dirs are ignored.

## Known Issues

- **Dashboard renderers have no automated coverage** — there is no NiceGUI render-test harness in the repo. Pure logic is well-tested; the `app.py` tab renderers are covered only by an HTTP-200 smoke test + manual render checks. (UI render-smoke harness was offered as a follow-up and declined this round.)
- **Transcript blind spots**: server-side/Cowork sessions write no local JSONL, and the format can drift across Claude Code versions. The parser returns empty rather than erroring in those cases.
- **3 broad `except Exception` blocks** in `app.py` render/discovery paths swallow errors silently — filed as a Sprint 32 chore to add logging.

## Lessons Learned

- **Verify code-review findings before applying.** The branch review flagged 6 issues; only 2 were real. The highest-severity claim ("`discover_transcripts` slug is wrong, pipeline returns no data") was a false positive — disproved in seconds by checking the actual `~/.claude/projects/` dir (the leading-dash slug is correct and finds all 4 transcripts). Two real bugs (multi-tool-turn success clobbering; `prompt_button` silent KeyError) were fixed with a regression test.
- **Subagent fan-out kept context lean and specs grounded.** Speccing fanned out 7 parallel research agents; implementation ran sequential TDD subagents. Specs and code stayed grounded in real files/data (the parser was built against 4 real transcripts).
- **Storybook intake is high-signal.** Our first external adopter's friction maps cleanly to onboarding work; treat it as a proxy for "new team adopting the tool."

## Test Coverage

- **415 tests passing** (was 362 at sprint start — **+53**). Ruff check + format clean.
- Strong pure-logic coverage across `transcript`/`prompts`/`pure`/`context_report`; gap is the UI renderers (see Known Issues).

## Context Efficiency (this sprint)

From `SPRINT31_CONTEXT_REPORT.json`: 106 reads / 34 unique files / **0.68 re-read ratio** / ~115K est. tokens. Most-read: `app.py` (19×), `cli.py` (12×), `context_report.py` (8×). The high re-read ratio persists despite this sprint building re-read-detection tooling — worth watching whether subagent delegation lowers it next sprint.

## Recommendations for Next Sprint (Sprint 32)

All filed as backlog items (tagged sprint 32):

1. **Sprint-folder backlog organization** (P2, feature) — implement the approved three-tier design.
2. **`.backlogignore` + import/init command** (P2, feature) — adoption ergonomics deferred from `list-warns`.
3. **`add --from-yaml` bulk import** (P3, feature) — deferred from the add-flags item; addresses storybook's original migration pain.
4. **Log swallowed exceptions** (P3, chore) — make the broad `except` blocks in `app.py` diagnosable.

External: advise storybook to upgrade past commit `8d304e5` (install-skills exit code).
