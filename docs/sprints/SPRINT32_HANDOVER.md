# Sprint 32 Handover — Adoption + External Feedback

**Date:** 2026-07-23
**Branch:** sprint32/main -> merged to main (PR #33, `1c459e0`)
**Version:** 0.32.0

## Sprint Theme

Make the tool survive contact with other projects. Six of the seven items trace directly to external
adopter reports rather than internal roadmap. Two adopters drove the sprint: **tracksupp.ai** (filed
five items across two rounds, including a real sprint-13 planning session) and **dag-bedrock-demo**
(adopted mid-sprint). The through-line: agile-backlog worked for the person who built it and broke on
contact with anyone else's environment or workflow.

This displaced the previously-planned spine (the CLI `analyze` epic + Dashboard v2), which moved to
Sprint 33 intact.

## Completed Items (7/7)

| Item | Pri | Category | Cx | Key Files |
|------|-----|----------|----|-----------|
| Two-channel adoption — `init` + bundled plugin | P1 | feature | L | `scaffold.py` (new), `cli.py`, `bundled_hooks/` (new), `plugin/`, `scripts/sync_plugin.py` (new), `docs/guides/ADOPTION.md` |
| `serve` dead on default install | P1 | bug | S | `pyproject.toml`, `cli.py` |
| Planning view — lane sizing + zoom | P2 | feature | M | `components.py`, `pure.py` |
| `sprint-status` double-lists done items | P2 | bug | S | `cli.py` |
| No capacity signal while assembling a sprint | P2 | feature | S | `components.py`, `pure.py` |
| `sprint-start` — just-in-time per-item speccing | P3 | feature | S | `cli.py`, `bundled_skills/sprint-start/SKILL.md` |
| Log swallowed exceptions | P3 | chore | S | `app.py`, `yaml_store.py` |

**Also closed:** 3 housekeeping items (2 duplicates, 1 already-shipped `add --tags` verified against
`--help`). **Deferred to S33:** `dogfood-claude-skills-can-silently-drift-from-canonical-bundled-skills`
— filed mid-execution, never entered build. Not a scope failure; it was discovered by the sprint's own work.

## Key Decisions

- **`nicegui` promoted to base dependencies, AND the error message fixed** — both halves, not either/or.
  `serve` is a headline command that was dead on every default install; the `[ui]` extra is kept so
  existing `agile-backlog[ui]` installs still resolve. The improved error remains as a safety net for
  stripped environments.
- **`sprint-status` fix is display-only.** `item.phase` is deliberately NOT cleared when an item moves
  to done — the stored phase is history worth keeping, and clearing it would rewrite YAML on every
  completion. The `Progress: N/M` line was left untouched.
- **`validate --level` defaults to `full`.** Just-in-time speccing is opt-in; the no-flag path is
  byte-identical to `--level full`, verified by test, so no existing project changes behaviour.
- **`init` never edits an existing `CLAUDE.md`** — it prints the block for the user to paste
  (non-invasive, carried from the design). It merges `settings.local.json` rather than clobbering.
- **Plugin content is single-sourced.** `plugin/skills/` and `plugin/hooks/scripts/` are generated only
  by `scripts/sync_plugin.py`; a pytest runs `--check` so CI fails on drift. `KEEP = {"backlog"}`
  allowlists the one plugin-only skill.
- **Sprint 32's scope cut replaced a stale proposal.** The paused plan from 2026-06-07 predated both the
  two-channel P1 and all six feedback items, so it was re-cut rather than applied.

## Architecture Changes

- **New `scaffold.py`** — all `init` logic as pure functions taking an explicit `root: Path`, testable
  with `tmp_path`. `install-skills` was refactored to share `install_skills_from_package` (DRY).
- **New `bundled_hooks/`** — the context-logging hook is now package data. Previously it existed only in
  this repo's `.claude/hooks/` and never shipped to adopters.
- **`plugin/` became a real plugin** — 9 synced skills, 8 authored commands, `hooks.json` resolving via
  `${CLAUDE_PLUGIN_ROOT}`, fed from one canonical source with a CI drift gate.
- **`pure.py` gained the planning-view math** — `lane_flex_weights`, `summarize_complexity`,
  `format_complexity_breakdown`. UI proportions are unit-testable without a browser.
- **`app.py` logging** — transcript parse and usage-summary paths extracted into
  `_parse_all_transcripts` / `_compute_usage_summary` with a module logger.

## Known Issues

1. **Dogfood `.claude/skills/` drift is unguarded.** `sync_plugin.py` covers `plugin/` and the
   `.claude/hooks/` dogfood copy, but nothing checks `.claude/skills/` against canonical
   `bundled_skills/`. This bit us live: commit `5fbb009` documented the new JIT-speccing tiers in the
   dogfood `sprint-start` skill only, so the feature shipped with documentation adopters never receive.
   Repaired at sprint-end by promoting the dogfood copies to canonical; the gate itself is filed for S33.
2. **No way to clear `sprint_target`.** `edit --sprint 0` is silently accepted and writes
   `sprint_target: 0`, a sprint that does not exist and then appears in filters. The `sprint-end` skill
   itself instructed this command until this sprint; it now says to retag instead. CLI fix filed for S33.
3. **`_detect_install_context` is a machine-global heuristic.** It looks for a uv receipt under the
   user's home, so a pip-installed user who has uv installed for anything else gets the uv remedy. This
   is inherent to the approach the design chose, not an implementation defect, but it can misdirect.
4. **Re-read ratio is 0.68 and flat.** 140 re-reads across 67 unique files (`app.py` 27x, `cli.py` 24x),
   against a CLAUDE.md that opens with a hard "DO NOT RE-READ FILES" rule. Across five well-sampled
   sprints the ratio has not improved: 0.65 (S25), 0.61 (S27), 0.78 (S29), 0.68 (S31), 0.68 (S32). The
   rule is not working. Parallel agents each independently reading the same large files is part of it.

## Lessons Learned

- **Parallel agents need disjoint file ownership and a "report, don't fix" rule.** Four implementers ran
  concurrently only because each owned a distinct file set and was explicitly told to report — not
  repair — failures outside it. They share one `pytest tests/` suite, so each periodically observed
  another's half-written state; two of them did, and correctly reported instead of acting. Without that
  instruction they would have overwritten each other's work.
- **Green CI is not proof of the claim.** PR CI passed and was initially cited as proving `serve` works
  on a default install. It proved no such thing: the test job installs the `[dev]` extra, which already
  contained `nicegui`, so it would have passed either way. The real claim needed a separate fresh-install
  test in a clean venv. Verify the claim, not the proxy for it.
- **Read every comment before speccing scope.** The adopter reported that a third of their sprint was
  phantom scope — items whose comments said "no code work remains" — caught only because someone read
  them first. Running that check here cost one command and found nothing, which is exactly the point:
  cheap insurance that belongs in `sprint-start` permanently.

## Test Coverage

- **474 passing**, lint clean (baseline at sprint start: 415, so **+59 tests**).
- 73 files changed, +3646 / -434.
- New suites: `test_scaffold.py` (16), `test_init_cli.py` (5), `test_plugin_sync.py` (4), plus additions
  to `test_pure.py` (+16), `test_cli.py`, `test_transcript.py`, `test_yaml_store.py`.
- Remote CI green on `main` across Python 3.11 / 3.12 / 3.13.

## Context Efficiency

| Metric | Value |
|---|---|
| Total reads | 207 |
| Unique files | 67 |
| Re-reads | 140 (**0.68 ratio**) |
| Estimated tokens | 244,640 |
| Tool calls | 1194 (Bash 584, Read 207, Edit 105) |

Most re-read: `app.py` (27), `cli.py` (24), `test_cli.py` (13), `components.py` (13), the two-channel
plan (11). See `SPRINT32_CONTEXT_REPORT.json`.

## Recommendations for Next Sprint

1. **Guard the dogfood skills copy** — extend `sync_plugin.py` to cover `.claude/skills/`. Filed:
   `dogfood-claude-skills-can-silently-drift-from-canonical-bundled-skills`.
2. **Allow clearing `sprint_target`** — accept `--sprint none`/`--no-sprint` or reject 0. Filed:
   `no-way-to-clear-sprint-target-sprint-0-silently-writes-a-bogus-sprint-0`.
3. **Warn on stale sprint picks, and stop `validate` checking done items.** Filed:
   `nothing-warns-that-a-sprint-pick-is-already-resolved-work-and-validate-checks-done-items`.
4. **Surface the saved context reports in the UI, with a cross-sprint trend.** Nine reports exist and
   nothing reads them. Filed:
   `surface-saved-sprint-context-reports-in-the-ui-per-sprint-view-plus-re-read-trend`.
5. **Act on the flat re-read ratio.** Five sprints of no improvement means the CLAUDE.md rule needs to
   become a mechanism, not a request. Filed:
   `re-read-rule-is-not-working-make-it-a-mechanism-not-a-request`.
6. **Resume the displaced spine** — the CLI `analyze` epic (2×M, spec + items ready) and Dashboard v2 are
   tagged S33 and were never descoped on merit, only outranked by adopter signal.
