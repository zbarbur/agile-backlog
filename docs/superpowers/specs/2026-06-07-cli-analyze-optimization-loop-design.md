# CLI `analyze` — Terminal-Native Optimization Loop — Design

**Date:** 2026-06-07
**Status:** Approved (design); implementation tracked as two Sprint 32 items under one epic
**Author:** brainstorming session

## Motivation

We already compute rich optimization signals (real token usage, re-read waste, cache-hit
rate, tool/category breakdown) and we have a registry of *actionable* prompts in
`prompts.py` (`claude_md_audit`, `claude_md_trim`, `permission_consolidate`,
`re_read_waste_fix`, `context_budget_check`, …). Today those only surface as **copy-buttons
in the NiceGUI dashboard**. A developer driving work from the terminal with Claude in the
loop has no way to pull that analysis into the session and act on it.

This design closes that loop: a CLI `analyze` command group emits findings — readable for a
human, structured for an in-session Claude — covering three optimization targets:

1. **CLAUDE.md** — bloat, vague directives, rules that aren't actually working.
2. **Context efficiency** — re-read waste, low cache-hit rate.
3. **Claude tool policy** — redundant / dead / over-narrow `settings.local.json` permissions.

At sprint-end (and on demand) Claude runs the sweep, reads the findings, and applies the
high-value fixes in-session after the user's review.

Explicitly **not** a goal (this cut): the CLI editing any file itself. The CLI is a pure
analyzer; Claude performs every edit through its own tools. A mechanical `--apply` for the
deterministic tool-policy consolidation is noted as a future, not built here.

## Decisions (from brainstorming)

| # | Question | Decision |
|---|----------|----------|
| 1 | Output contract | **Hybrid** — readable by default; `--json` yields structured findings, each carrying its ready-to-run action prompt. |
| 2 | Who applies the fix | **Analyze-only** — CLI never writes; Claude applies every edit after user review. Mechanical tool-policy `--apply` deferred. |
| 3 | Command surface | **Click subcommand group** — `analyze claude-md \| context \| tool-policy \| all`. |
| 4 | Lifecycle | **Sprint-end sweep + always on-demand.** Sprint-start pass deferred. Sweep is a skippable close-out step, not a gate. |
| 5 | Tool-policy basis | **Static core + usage enrichment** — heuristics over `settings.local.json` now; `transcript.py` usage counts as a confidence signal that degrades gracefully. |

## Architecture

New pure module **`src/agile_backlog/analyze.py`** — produces `Finding` objects and nothing
else. No file writes, no terminal I/O. The CLI layer renders.

Reuses existing units behind stable interfaces:

- `transcript.py` — session data (real tool calls, tokens, skill attribution) via `discover_transcripts(cwd)` / `parse_transcript`.
- `context_report.py` / `pure.py` — `cache_hit_rate`, `compute_reread_waste`, tool/category breakdown.
- `prompts.py` — the resolved action prompt attached to each finding.

Each analyzer is one isolated function returning the common type:

```python
analyze_claude_md(claude_md_text: str, sessions: list[Session]) -> list[Finding]
analyze_context(sessions: list[Session])                        -> list[Finding]
analyze_tool_policy(settings: dict, sessions: list[Session])    -> list[Finding]
```

**One `Finding` type, three producers, two renderers.** Adding a target later = write one
analyzer; the envelope, `--json`, and lifecycle wiring are untouched.

## The `Finding` envelope

```python
class Finding(BaseModel):
    target: str          # "claude-md" | "context" | "tool-policy"
    id: str              # stable finding-type slug, e.g. "redundant-permission"
    severity: str        # "high" | "medium" | "low"
    title: str           # one-line human summary
    evidence: dict       # concrete specifics (lines, counts, file refs) — free-form per analyzer
    suggested_action: str        # what to do, in prose
    action_prompt: str | None    # resolved prompts.py text Claude can run as-is
    confidence: float = 1.0      # raised/lowered by usage enrichment
```

`evidence` is intentionally a free-form dict so each analyzer can attach the shape that fits
(approved during brainstorming over a stricter per-target type).

**Two render modes from the same findings:**

- **Default (human):** grouped by target → severity; each finding shows `title`, `evidence`, and `action_prompt`.
- **`--json`:** an agent-consumable envelope:

```json
{
  "tool": "agile-backlog analyze",
  "target": "all",
  "generated_for": "claude",
  "summary": {"high": 2, "medium": 5, "low": 3},
  "findings": [ { "...Finding": "..." } ]
}
```

## The three analyzers

### `analyze claude-md` — source: CLAUDE.md; enrichment: transcripts
- **Bloat over budget** — token-estimate vs threshold → `claude_md_trim` (high if well over).
- **Vague/unenforceable directives** — heuristic scan for soft language → `claude_md_audit`.
- **Duplicated rules** — repeated stop-rules (e.g. our own "DO NOT RE-READ FILES" top & bottom); flagged *low* with a "may be deliberate reinforcement" note.
- **Enrichment:** cross-reference a rule against behavior — if CLAUDE.md forbids re-reading but transcript re-read ratio is high, the rule isn't working → raise severity, attach re-read evidence.

### `analyze context` — source: transcripts (usage-native)
- **High re-read ratio** (`compute_reread_waste`) → `re_read_waste_fix`; evidence = top re-read files + counts.
- **Low cache-hit rate** (`cache_hit_rate`) → `context_budget_check`.
- Wraps today's `context-report` numbers into `Finding` form; `context-report` becomes a thin alias.

### `analyze tool-policy` — source: `settings.local.json`; enrichment: transcripts
- **Static core (ships first):**
  - *Dead one-offs* — hardcoded line numbers (`NR==646`), `__TRACKED_VAR__` placeholders, one-shot `-k` filters.
  - *Redundant/overlapping* — `pytest -v` + `-q` + `-k` collapse under `pytest *`.
  - *Over-narrow clusters* — many `agile-backlog <verb> *` → umbrella consolidation.
  - → `permission_consolidate`.
- **Usage enrichment:** count actual Bash calls from transcripts against each allow entry — annotate "used 0× across last N sessions" (safe-drop, ↑confidence) or surface frequently-run commands **not** covered (add candidates). Falls back to static-only when history is thin.

### `analyze all`
Runs all three, merges findings into one envelope + summary. This is the sprint-end sweep.

## CLI surface

```
agile-backlog analyze claude-md    [--json]
agile-backlog analyze context      [--json] [--sprint N]
agile-backlog analyze tool-policy  [--json]
agile-backlog analyze all          [--json]
```

`context-report` is retained as a thin alias → `analyze context`; its current JSON output is
preserved for back-compat.

## Lifecycle integration

`/sprint-end` gains a close-out step: run `analyze all`, present findings grouped by
severity, and Claude offers to apply the high-value ones before the PR. It is a normal
skippable step, not a hard gate (consistent with the analyze-only philosophy). Sprint-start
integration is deferred to a fast follow once the output format is proven.

## Error handling

Consistent with the existing quiet-skip philosophy:

- Missing `CLAUDE.md` / settings file → that analyzer emits no findings plus a one-line note; never crashes.
- No transcripts discovered → usage enrichment silently skipped; static findings still produced.
- Malformed settings JSON → single warning, skip the tool-policy analyzer only.

## Testing

- **Pure-analyzer units** — synthetic CLAUDE.md text / settings dict / `Session` objects → assert findings. Deterministic, no real files.
- **tool-policy heuristics** — dead-one-off, redundant-overlap, over-narrow detection; usage 0× vs N× annotation.
- **Envelope** — JSON shape + human render.
- **CLI** — each subcommand incl. `--json`; `context-report` alias regression.

## Implementation phasing

The epic is an **L**, staged in the implementation plan and split across **two backlog
items** for sprint tracking:

**Item 1 — analyzer core + context + claude-md**
1. `Finding` model + `analyze` Click group skeleton + shared renderers (human + `--json`).
2. `context` target wrapping `context-report` (alias retained).
3. `claude-md` analyzer (static checks + re-read enrichment).

**Item 2 — tool-policy + sweep + lifecycle**
4. `tool-policy` analyzer (static core + usage enrichment).
5. `analyze all` merge + `/sprint-end` close-out wiring.

## Backlog reconciliation

This epic **supersedes three existing items**, which will be closed as superseded with a
pointer to the two epic items:

- `optimize-claude-md-structure-stop-rules-routing-table-skill-reinforcement` (P2, s28) → claude-md analyzer.
- `analyze-and-optimize-settings-local-json-allowed-command-patterns-consolidate-redundant-permissions-show-stats` (P2, untagged) → tool-policy analyzer.
- `session-analytics-jsonl-analyzer-skill-compliance-ratio-command-categorization-sprint-retro-integration` (P2, s28) → partially the context analyzer (skill-compliance/retro aspects remain a possible later finding type).

## Risks & interactions

- **Output-contract churn:** Claude consumes the `--json` envelope, so the schema is a
  contract. Keep `Finding` stable; add fields rather than rename. This is why lifecycle
  wiring (Q4) is minimal until the format is proven.
- **Usage-signal noise:** sparse transcript history makes enrichment weak; it must degrade
  to static-only without misleading "used 0×" claims (guard on a minimum session count).
- **`context-report` alias:** existing callers / the sprint-end context report must keep
  working unchanged.

## Out of scope

- CLI editing any file (`--apply`) — deferred; mechanical tool-policy apply is the most
  likely first follow-up.
- Sprint-start lifecycle pass — deferred fast-follow.
- New prompt templates — the existing `prompts.py` registry covers all initial findings.
