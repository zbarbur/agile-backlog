# Sprint 30 Mid-Sprint Handover

**Date:** 2026-04-27
**Branch:** `sprint30/main` (pushed to origin)
**Version:** v0.30.0
**Theme:** Dashboard v2 consolidation + debt paydown
**Status:** 2/3 items in `review` phase, 1 item in `plan` phase, CI green (361 tests)

## TL;DR for resume

1. Read this doc.
2. Read `docs/design/SPRINT30_DASHBOARD_V2_DESIGN.md` (sprint 31 implementation blueprint produced by Item 2).
3. Decide Item 3 execution path: subagent vs manual (see "Next decision" below).
4. Execute Item 3 → CI → review phase.
5. Run `/sprint-end` when all 3 items are in review.

## Sprint 30 scope (4 items, 1 stretch)

| Item | Pri | Cpx | Phase | Status |
|---|---|---|---|---|
| `edit-repeatable-list-flags` (bug) | P1 | S | review | ✅ done, code-reviewed |
| `design-session-dashboard-v2-consolidation` | P1 | M | review | ✅ done, design-reviewed |
| `refactor-app-py` (Done view slice) | P2 | L | plan | ⏳ not started |
| `add-claude-code-terminal-session` | P2 | — | backlog | stretch, not picked up |

## Item 1: edit-repeatable-list-flags — DONE ✅

**Pivoted scope:** the original bug ("flags append instead of replace") did NOT reproduce in this codebase — `cli.py:273` has always done `setattr(item, field, list(value))`. The bug was filed from data_classifier work against a forked/older CLI. Pivot agreed (option Y): keep replace as default, add `--append-*` opt-in flags + regression tests.

**Files changed:**
- `src/agile_backlog/cli.py` — 3 new Click options (`--append-technical-specs`, `--append-acceptance-criteria`, `--append-test-plan`); handler pops them before main setattr loop and `extend()`s after
- `tests/test_cli.py` — replaced anemic `test_edit_acceptance_criteria` with 3 new methods: `test_edit_list_flag_replaces_existing` (parametrized × 3), `test_edit_append_flag_extends_existing` (parametrized × 3), `test_edit_replace_then_append_in_one_call`
- `docs/superpowers/plans/2026-04-23-edit-append-opt-in-flags.md` — implementation plan

**Combined-flag semantic:** `edit X --acceptance-criteria A --append-acceptance-criteria B` produces `[A, B]` (replace first, then append). Documented and tested.

**Tests:** 7 new test cases, 361 total (was 355).

**AC compliance:** 5/5 met.

## Item 2: design-session-dashboard-v2-consolidation — DONE ✅

**Output:** `docs/design/SPRINT30_DASHBOARD_V2_DESIGN.md` (467 lines, 5,010 words). Drafted by general-purpose subagent with full source-thread context inlined.

**Sections:**
- §1 Synthesis (redundancies, complementarity, IA diagram)
- §2 Decision log (5 decisions with alternatives + rationale)
- §3 Sprint 31 implementation items (5 items decomposed)
- §4 Out-of-scope / deferred (e.g. Plugins tab → sprint 32)
- §5 Migration notes (notes for the 3 source items, executed below)
- Appendices: risk register, open questions, file inventory

**5 sprint 31 items proposed (in ship order):**
1. `dashboard-v2-actionable-prompt-registry-and-component` — S, ships first (everything else depends)
2. `dashboard-v2-context-view-tools-categories-rereads-tabs` — M
3. `dashboard-v2-process-view-guidelines-audit-tab` — M
4. `dashboard-v2-skill-invocation-tracking-hook-and-skills-tab-usage` — L
5. `dashboard-v2-hooks-permissions-claude-md-tab-enhancements` — M (designated as cut/stretch — total capacity S+3M+L is upper edge)

**Subagent caveats flagged:**
- `app.py` is **1852 lines** now (sprint 29 added ~280 — refactor more urgent than handover #29 stated)
- §5 recommends closing the 3 source items as `done` (superseded). Deferred to `/sprint-plan-next` to keep sprint 30 burndown clean.

**Source items updated:**
- `optimization-guidelines-dashboard-...` — notes point at design doc, AC #3 mapping
- `design-session-context-and-process-dashboard-v2-...` — notes describe 4-item fulfillment + Plugins tab deferral
- `process-review-prompts-...` — notes describe registry-as-shared-component decision

**AC compliance:** 5/5 met.

## Item 3: refactor-app-py Done view extraction — NOT STARTED ⏳

**Scope (first slice — full refactor is 3+ sprints):** extract Done view rendering, retrospective comparison UI, markdown loading from `app.py` into new `src/agile_backlog/views/done.py`. Reduce `app.py` by ≥300 lines.

**Phase:** `plan`. No plan doc written yet.

**AC (7):** see `agile-backlog show refactor-app-py-extract-context-process-and-done-views-into-separate-modules-to-reduce-1576-line-single-file`. Title is now stale (1852 lines, not 1576).

**Critical NiceGUI constraints (from sprint 29 lessons — DO NOT SKIP):**
- Use **shared mutable state dicts** for buttons that rebind on save — closures capture content at render time and go stale.
- Wrap **all** `ui.html()` values with `safe_html()`. XSS regression is a recurring pattern in this project.
- No new abstractions just for refactoring — move code as-is, only adjust imports.

**Risk:** NiceGUI patterns are subtle. Per memory `feedback_complex_features_prototype.md`, don't trust subagent NiceGUI API assumptions blindly.

## Next decision needed (resume here)

**Item 3 execution path:**
- **(a) Subagent dispatch** — faster, but high risk on NiceGUI stale-closure regressions; mitigation = include sprint 29 handover §"Lessons Learned" inline in prompt, then verify by running `agile-backlog serve` and clicking through Done tab manually.
- **(b) Drive manually** — slower but safer; do the move, run tests, run serve, eyeball each rendered widget.

**Leaning:** (a) with strong context inlining, then post-hoc UI verification. The mechanical work (move 300+ lines of methods + adjust imports) is well-suited to a subagent; the risk is in *which* methods carry shared-state dependencies that an agent might miss.

Either way, **must run `agile-backlog serve` and click through the Done view** before declaring complete. CI alone won't catch render regressions.

## Uncommitted work (snapshot at handover write time)

```
M backlog/design-session-context-and-process-dashboard-v2-...yaml   (notes update — Item 2)
M backlog/design-session-dashboard-v2-consolidation-...yaml         (phase=review, design-reviewed — Item 2)
M backlog/edit-repeatable-list-flags-...yaml                        (phase=review, code-reviewed, goal reframe — Item 1)
M backlog/optimization-guidelines-dashboard-...yaml                 (notes update — Item 2)
M backlog/process-review-prompts-...yaml                            (notes update — Item 2)
M src/agile_backlog/cli.py                                          (3 new --append-* options + handler — Item 1)
M tests/test_cli.py                                                 (7 new test cases — Item 1)
?? docs/design/                                                     (new design doc — Item 2)
?? docs/superpowers/plans/2026-04-23-edit-append-opt-in-flags.md    (Item 1 plan)
```

## Suggested pre-restart commits (commit on `sprint30/main`, push)

Two logical commits keeps git log readable:

**Commit A — Item 1 (bug fix scope-pivot):**
```
git add src/agile_backlog/cli.py tests/test_cli.py \
        backlog/edit-repeatable-list-flags-only-append-no-way-to-replace-acceptance-criteria-technical-specs-test-plan.yaml \
        docs/superpowers/plans/2026-04-23-edit-append-opt-in-flags.md

git commit -m "feat(cli): add --append-* opt-in flags for edit list fields

Bug filed against append behavior did not reproduce — replace was already the
default. Pivot to add explicit --append-* opt-in flags for the accumulation
case + parametrized regression tests locking in replace semantics.

Closes sprint 30 item: edit-repeatable-list-flags."
```

**Commit B — Item 2 (design session output):**
```
git add docs/design/ \
        backlog/design-session-dashboard-v2-consolidation-process-prompts-optimization-guidelines-context-enhancements.yaml \
        backlog/design-session-context-and-process-dashboard-v2-with-per-tool-context-cost-skill-invocation-tracking-historical-sprint-comparison-and-actionable-prompts.yaml \
        backlog/optimization-guidelines-dashboard-display-claude-code-best-practices-with-compliance-checks-and-improvement-prompts.yaml \
        backlog/process-review-prompts-actionable-one-click-prompts-for-claude-md-audit-skill-description-optimization-hook-coverage-gaps-permission-consolidation-and-context-budget-check.yaml

git commit -m "docs: SPRINT30_DASHBOARD_V2_DESIGN — consolidate 3 sprint 31 threads

Decomposes optimization-guidelines, dashboard-v2-observability, and
process-review-prompts into 5 sprint 31 items with concrete AC. Source
items' notes updated to point at design doc.

Closes sprint 30 item: design-session-dashboard-v2-consolidation."
```

Then `git push`.

## Resume checklist

- [ ] `cd /Users/guyguzner/Projects/agile-backlog && git status` — confirm clean tree on `sprint30/main`
- [ ] `git pull` — sync any remote updates
- [ ] `.venv/bin/agile-backlog flagged` — check for async notes
- [ ] `.venv/bin/agile-backlog list --status doing` — confirm Item 3 still in `doing/plan`
- [ ] Read `docs/sprints/SPRINT30_MIDSPRINT_HANDOVER.md` (this doc) and `docs/design/SPRINT30_DASHBOARD_V2_DESIGN.md`
- [ ] Decide Item 3 execution path (a/b above)
- [ ] Execute Item 3, run CI, run `agile-backlog serve` for visual verification
- [ ] When Item 3 in `review`, run `/sprint-end`

## Sprint 31 prep (after sprint-end of 30)

The 5 sprint 31 items in the design doc need to be created as YAML items and tagged. `/sprint-plan-next` is the right vehicle — it'll also handle closing the 3 source items as `done` per design §5.
