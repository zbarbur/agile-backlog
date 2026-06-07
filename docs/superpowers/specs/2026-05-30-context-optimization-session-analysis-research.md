# Context Optimization & Session Analysis — Research

**Date:** 2026-05-30
**Author:** research workflow (deep-research) + ground-truth verification on this machine
**Purpose:** Inform Dashboard v2 (Sprint 31) and the project's hook/session-analysis direction.
**Status:** Reference. Drives the Sprint 31 replan (see end).

---

## TL;DR

1. **Context rot is the empirical justification for the whole dashboard.** Model recall degrades as the context window fills; the design north-star is "the smallest set of high-signal tokens that achieves the task." Everything we measure should serve that.
2. **We are filling a real gap.** Every existing Claude Code session tool (`ccusage`, `claude-code-trace`, `claude-usage`, `claude-code-transcripts`) only *views* or *aggregates cost*. **None detect inefficiencies or inaccuracies.** That diagnostic layer is exactly Dashboard v2.
3. **Claude Code's own native JSONL transcript is a richer data source than our bespoke hook log** — and it already exists, per session, with no hook required. Verified on this machine. This reverses design-doc decision **D2** (which rejected transcript parsing as "fragile"). See "Native transcript" below.

---

## Section 1 — Verified findings (best practices)

All high-confidence (3-0 adversarial vote) unless noted. Sources cited inline.

| # | Finding | Source |
|---|---------|--------|
| 1 | **Context rot is real & empirically grounded.** As tokens accumulate, recall degrades; the context window is "the most important resource to manage." Corroborated across Anthropic, Chroma's 18-model study, Stanford lost-in-the-middle. | [Anthropic eng](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [CC docs](https://code.claude.com/docs/en/best-practices), [Chroma](https://research.trychroma.com/context-rot) |
| 2 | **Goal = smallest set of high-signal tokens.** Finite attention is a scarce resource. | Anthropic eng |
| 3 | **Bloated/overlapping tool sets cause confusion** — the model hallucinates params or picks the wrong tool. "If a human engineer can't say which tool to use, an agent can't either." Heuristic for detecting wrong-tool selection. | Anthropic eng |
| 4 | **Bloated CLAUDE.md makes Claude ignore instructions** — rules get lost in noise. Test each line: "Would removing this cause mistakes? If not, cut it." (This project's CLAUDE.md already applies it — the DO-NOT-RE-READ rule.) | CC docs |
| 5 | **Subagents cut main-context consumption** by exploring in separate windows and returning only summaries. "Infinite exploration" (unscoped investigate prompts reading hundreds of files) is a named failure mode. Caveat: subagent-heavy flows use ~7x *total* tokens. | CC docs |
| 6 | **Kitchen-sink sessions & repeated corrections degrade performance.** Remedy: `/clear` between unrelated tasks, and `/clear` after >2 corrections on the same issue. → two detectable signals: topic-switching, repeated corrections. | CC docs |
| 7 | **Context editing auto-clears stale tool calls** near token limits; +29% on complex tasks; memory tool + context editing +39%; 100-turn web-search eval cut tokens 84%. **Caveat:** vendor internal benchmarks, not independently reproduced; 84% partly self-fulfilling (baseline runs to exhaustion). | [context-management](https://anthropic.com/news/context-management) |
| 8 | **Prompt caching cuts cost up to 90% / latency up to 85%** for long prompts. "Up to" / best-case. | [prompt-caching](https://claude.com/blog/prompt-caching) |

**Refuted (do NOT cite):**
- "Token-efficient tool use saves ~70%" — **refuted 0-3**.
- "ccusage as a session-analysis basis" — **refuted**; usage/cost only.

---

## Section 2 — The competitive gap (strongest finding)

Across four primary GitHub repos, the ecosystem splits cleanly:

- **Viewing layer:** `claude-code-trace` (JSONL viewer, live tail), `claude-code-transcripts` (→ HTML; explicitly "does not analyze token usage, context efficiency, or detect inefficiencies").
- **Cost-aggregation layer:** `ccusage` (daily/session token+cost), `claude-usage` (token charts, cost estimates; dedupes by `message.id`).
- **Diagnostic layer (re-reads, redundant calls, bloat, failed/guessed calls): does not exist.**

That third layer is Dashboard v2's reason to exist.

---

## Section 3 — Native transcript as canonical data source (VERIFIED HERE)

Claude Code writes an append-only JSONL transcript per session under
`~/.claude/projects/<url-encoded-project>/<session-uuid>.jsonl`, exposed to every hook via `transcript_path`.
**Verified directly on this machine** against the current project's session files. Fields we can build on:

### Per-assistant-turn token usage (real, not estimated)
```
message.usage = {
  input_tokens, output_tokens,
  cache_read_input_tokens, cache_creation_input_tokens,
  cache_creation: { ephemeral_5m_input_tokens, ephemeral_1h_input_tokens },
  service_tier, speed, model, ...
}
```
→ enables **real cache-hit rate**, **real cost**, real per-turn token growth. Retires `TOKENS_PER_LINE = 4`.

### Skill attribution (native — no hook needed)
- Records carry `attributionSkill` (observed: `plan` ×26, `deep-research` ×4 in one session).
- **This eliminates the need for the planned `UserPromptSubmit` skill-invocation hook (Item 4).** Skill usage is captured retroactively for every session.

### Tool call success/failure & pairing (native)
- `tool_use` blocks (with `name`, `id`) in assistant `message.content`.
- `toolUseResult` records carry `success` + link back via `sourceToolAssistantUUID`.
- → retires the heuristic error-sniffing in `post-tool-logger.sh`.

### Other useful top-level fields
`sessionId`, `parentUuid`, `timestamp`, `gitBranch`, `cwd`, `version`, `promptId`, `isSidechain` (separates subagent turns), `permissionMode`/`mode`, `last-prompt`, user prompt text (slash commands recoverable).

### This reverses decision D2
The Sprint 30 design doc chose forward-only hook capture over transcript parsing, calling parsing "fragile across Claude Code versions." New evidence: the format is documented, stable enough that 4 tools parse it, and gives us things a hook never could (real token usage, cache stats, retroactive skill attribution, native success flags). **D2 is reversed for Sprint 31.**

**Caveats to carry:** (a) known duplicate-append bug (claude-code #5034) — dedupe by `message.id`/`uuid`; (b) server-side/Cowork sessions reportedly don't write local JSONL — possible coverage blind spot; (c) `isSidechain` subagent turns must be separated from main-loop accounting.

---

## Section 4 — Open questions (our design work — no source answers these)

1. **Thresholds.** How many re-reads = wasteful? What token-growth slope = bloat? Sources give categories, not numbers. We must set defaults (config-driven).
2. **Skill non-compliance detection.** JSONL doesn't flag "should have used skill X before guessing command Y." Needs our own matching heuristic (CLI-reference / skill registry vs. raw Bash).
3. **Coverage blind spot.** Quantify what fraction of real usage is server-side (no local JSONL).
4. **Cache-hit rate as a headline metric.** Now that we have real cache fields — what's a "good" hit rate to target/surface?

---

## Section 5 — Implication for Sprint 31 (replan)

Re-derive the dashboard around the native transcript:

- **NEW foundation item — Native transcript ingestion layer.** Parse `~/.claude/projects/<proj>/*.jsonl` into a session model (token usage incl. cache, tool_use→result success pairing, `attributionSkill`, prompts, sidechain separation). Feed `context_report.py`. Load-bearing; ships first or alongside the prompt primitive.
- **Item 1 (prompt registry, S)** — unchanged.
- **Item 2 (Context tabs, M)** — now powered by real usage; add a **cache-efficiency** view.
- **Item 4 shrinks L→S** — skill usage from `attributionSkill`; drop the `UserPromptSubmit` hook.
- **Failed-call detection** — now native via `toolUseResult.success`.
- **Item 3 (Guidelines & Audit)** gains real rows: cache-hit rate, real failed-call ratio, repeated-corrections, kitchen-sink topic-switching.

Capacity is ~3 items/sprint. Recommended S31 commit: **ingestion layer + prompt registry + Context tabs (real usage incl. cache)**; defer Guidelines & Audit and tab modernization to S32.
