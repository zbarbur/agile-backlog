# Sprint 30 Design — Dashboard v2: Compliance, Visibility, Action

**Date:** 2026-04-21
**Sprint:** 30 (design produced this sprint, ships sprint 31)
**Author:** Sprint 30 design session
**Status:** Proposed
**Supersedes:** 3 source backlog items (see Section 5)

## Purpose

Three P1 backlog items have been circling since sprint 27 without a unified design:

1. `optimization-guidelines-dashboard` — compliance checks against the optimization guide.
2. `design-session-context-and-process-dashboard-v2` — visibility (per-tool cost, skill usage, plugins, hooks).
3. `process-review-prompts` — actionable one-click prompts for CLAUDE.md / skills / hooks / permissions / context.

Each thread overlaps the other two. Shipping them piecemeal would either duplicate UI plumbing (three "actionable prompts" implementations) or leave the user with a half-instrumented dashboard. This document consolidates them into a single coherent dashboard v2 and decomposes that work into 3-5 sprint-31-sized items.

The design is grounded in:

- Current view structure in `src/agile_backlog/app.py` (1,852 lines, soon to be split).
- Sprint 29's shipped infrastructure: `context_report.py` (`compare_sprints`, `estimate_tool_tokens`), `pure.py` (`score_skill_quality`), Done view markdown rendering, JSONL session logs in `.claude/context-logs/`.
- The existing optimization guide at `docs/optimization/docs/claude-code-agent-optimization-guide.md` (878 lines, exists — no design needed for the source).
- Sprint 29 lessons: 78% re-read ratio, app.py read 88x; stale closures bite NiceGUI; XSS regressions; YAML is the single source of truth for sprint state.

---

## Section 1 — Synthesis

### 1.1 Redundancies across the three threads

| Theme | T1 Optimization Guidelines | T2 Dashboard v2 | T3 Review Prompts |
|---|---|---|---|
| One-click prompts | "Each guideline has a one-click prompt" | "Actionable prompts: each section has a run-this-to-improve button" | Entire item is about one-click prompts |
| CLAUDE.md audit | "CLAUDE.md budget check" | (implicit, not listed) | "CLAUDE.md audit" |
| Skill audit | "Skill description audit" | "Skills tab shows usage counts alongside description token cost" + "Unused skills highlighted" | "Skill description optimization" |
| Hook visibility | (not listed) | "Hooks tab: show actual command strings" | "Hook coverage gaps" |
| Permission consolidation | (not listed) | "Permissions tab: show consolidation suggestions" | "Permission consolidation" |
| Context budget | "Re-read waste score" | "Per-tool context cost" + "Context breakdown by category" | "Context budget check" |

**Conclusion:** the three threads are not three features — they are three *layers* of the same feature.

- **T1 = the rules** (what does "good" look like, scored numerically).
- **T2 = the data** (what is actually happening in the project, measured from logs and config).
- **T3 = the verbs** (what the user can do about a finding, packaged as copyable prompts).

A single dashboard v2 needs all three layers, woven through the same tabs. Shipping them as three separate UI features would produce three different button styles, three different "prompts" implementations, and three different ideas of what a "compliance score" means.

### 1.2 Complementarity

- T1 produces *scores and findings*: "CLAUDE.md is 2,400 tokens, over budget by 400" or "skill `report-bug` description is 250 chars, exceeds 200."
- T2 produces *measurements and breakdowns*: "tool `Read` consumed 124k of 258k tokens this sprint" or "skill `sprint-execute` was invoked 0 times in 3 sessions."
- T3 turns each finding/measurement into a *copy-pasteable prompt* the user can drop into a Claude Code session: "Audit CLAUDE.md and propose three trims to bring it under 2K tokens. Here is the current content: ..."

Every finding produced by T1 or T2 should yield a T3 prompt next to it. This is only sane if the prompts are co-located with the data — see decision D1.

### 1.3 Proposed unified information architecture

The current dashboard has three top-level views: **Context**, **Process**, **Done**. The v2 design keeps all three views and changes the *contents of tabs*. No new top-level view is added — that would fragment the user's mental model.

```
+-------------------------------------------------------------------------+
|  Top nav:  [Context]   [Process]   [Done]                              |
+-------------------------------------------------------------------------+

CONTEXT VIEW
  +-- Overview (tokens, sessions, top files) ............... existing
  +-- Tools (per-tool cost, sortable + drilldown) .......... NEW (T2)
  +-- Categories (read/write/search/exec breakdown) ........ NEW (T2)
  +-- Re-reads (waste score per session, file ranking) ..... NEW (T1+T2)
       Each row has an inline "Generate fix prompt" button.

PROCESS VIEW
  +-- Overview (CLAUDE.md, project shape) .................. existing
  +-- Guidelines & Audit (compliance scorecard) ............ NEW (T1)
       6 rule rows. Each row: rule, status, score, fix-prompt.
       Rules: CLAUDE.md budget, skill descriptions, memory tier,
              command guessing, re-read waste, hook coverage.
  +-- Skills (existing card UI + usage counts) ............. MODIFIED (T2)
       Adds invocation count column, "unused" badge with prompt.
  +-- Hooks (event/matcher/command + coverage gap prompt) .. MODIFIED (T2+T3)
       Replaces matcher-only display with command strings.
  +-- Permissions (list + consolidation suggestions) ....... MODIFIED (T2+T3)
  +-- Plugins (installed plugins -> skills/hooks/agents) ... NEW (T2)
  +-- CLAUDE.md (token count, tier check, trim prompt) ..... MODIFIED (T1+T3)

DONE VIEW
  +-- existing per-sprint summaries + cross-sprint compare
       (no changes in sprint 31; deferred items only)
```

### 1.4 Tab change inventory

| View | Tab | Verdict | Source thread |
|---|---|---|---|
| Context | Overview | unchanged | — |
| Context | Tools | **new** | T2 |
| Context | Categories | **new** | T2 |
| Context | Re-reads | **new** | T1 + T2 |
| Process | Overview | unchanged | — |
| Process | Guidelines & Audit | **new** | T1 |
| Process | Skills | modified (add usage column + prompts) | T2 |
| Process | Hooks | modified (show commands + coverage prompt) | T2 + T3 |
| Process | Permissions | modified (add consolidation suggestions) | T2 + T3 |
| Process | Plugins | **new** | T2 |
| Process | CLAUDE.md | modified (token budget + trim prompt) | T1 + T3 |
| Done | all | unchanged | — |

Eight tabs are touched. Four are new. Four are modifications to existing tabs.

### 1.5 The "actionable prompt" is a primitive, not a tab

Every new or modified tab above produces findings. Every finding gets a "Copy fix prompt" button next to it (decision D1). The prompt template is rendered server-side from a small registry — see Section 3 item 4 for the implementation shape. There is **no Action Center tab**; co-location wins (decision D1 below).

---

## Section 2 — Decision log

### D1. Where do "actionable prompts" live?

**Decision:** Inline, per-finding. Each finding row in any tab has a small "Copy prompt" button that copies a pre-formatted, context-aware prompt to the clipboard.

**Alternatives considered:**

1. **Dedicated "Action Center" tab** that aggregates every prompt across the dashboard. *Rejected:* forces context switch ("I see a problem here, now I leave to find the fix prompt"). Decouples prompts from data, which the user complained about implicitly when listing T3 separately from T1/T2.
2. **Pull-out side panel** that lists prompts contextual to the current tab. *Rejected:* adds NiceGUI layout complexity (right-rail panels are painful in `ui.row`/`ui.column` layouts) for marginal benefit over inline buttons. Stale-closure bug risk per sprint 29's lesson.

**Rationale:** Co-location is the cheapest, lowest-risk pattern, and it scales to 50+ findings naturally. A finding without a prompt is a missing feature; a tab full of prompts without findings is noise.

### D2. Skill invocation tracking — source of truth?

**Decision:** **Forward-only via `UserPromptSubmit` hook.** Capture `/skill-name` invocations as a new event type appended to the existing JSONL logs in `.claude/context-logs/`. No retroactive transcript parsing.

**Alternatives considered:**

1. **Retroactive parsing of historical Claude Code transcripts.** *Rejected:* transcript location and format are not stable across Claude Code versions. Sprint 27/28/29 logs would yield inconsistent data, and we would have to maintain a parser per format. The benefit (back-filled metrics) is not worth the maintenance cost.
2. **Both — hook plus retroactive backfill.** *Rejected:* doubles the surface area for a one-sprint-old benefit. Forward-only data accumulates within 2-3 sprints anyway.

**Rationale:** A new metric should start clean. After sprint 31 ships the hook, sprint 32's Done view will show real invocation counts. Until then, the Skills tab labels invocation count as `(tracking from sprint 31)` for skills with zero captured events — better than wrong data.

**Out-of-band note:** the JSONL schema gains an `event_type` field. Existing tool-call lines are implicitly `event_type: "tool_call"`. Skill invocations are `event_type: "skill_invocation"`. `context_report.py` must learn to skip non-tool-call events when computing tool stats.

### D3. Compliance + visibility — single tab or two?

**Decision:** **Two distinct things, but co-located in the Process view.** A new "Guidelines & Audit" tab holds the *compliance scorecard* (T1). Existing Skills/Hooks/Permissions/CLAUDE.md tabs hold the *raw visibility data* (T2), and each surfaces its own slice of the relevant compliance rule (e.g. CLAUDE.md tab shows the tier check inline; Skills tab shows description-length warnings inline).

**Alternatives considered:**

1. **Single merged tab** showing rules and raw data together. *Rejected:* either gets too long to scan, or the rules drown out the data the user came for. Different tasks.
2. **Compliance-only tab** that links to data tabs. *Rejected:* link-only flow forces extra clicks for the common case ("I want to see what's wrong in CLAUDE.md").

**Rationale:** The Guidelines & Audit tab answers "am I following the rules?" The data tabs answer "what's actually configured?" Both questions are valid; both deserve a home. Duplication is cheap because the underlying scoring functions live in `pure.py` and are called from both places.

### D4. Per-tool context cost UI — table, chart, or drilldown?

**Decision:** **Sortable table with expandable per-tool drilldown rows.** Each tool occupies one row showing call count, total tokens, and a collapsed bar; clicking the row expands to a sub-table of per-call samples and per-file breakdown for that tool.

**Alternatives considered:**

1. **Bar chart only.** *Rejected:* loses sortability, hard to drill into specific tools. Chart-only is great for a glance, useless for "why did `Read` consume 124k tokens?"
2. **Three-pane view (chart + table + drilldown).** *Rejected:* three panes is too much for a tab the user visits a few times per sprint. Diminishing returns for layout work.

**Rationale:** Tables match how the data is used (find the worst offender, drill in). Sprint 29 shipped expandable-card drilldown in Done view and the pattern is known to work in NiceGUI; we reuse it. Reuses the `state dict` pattern from sprint 29 to avoid stale closures.

### D5. CLAUDE.md token budget — threshold and action?

**Decision:** **2,000-token soft warn, 3,000-token hard warn, both configurable in `.claude/sprint-config.yaml`. Action is *suggest only* — never block.**

```yaml
optimization:
  claude_md_budget:
    soft_limit_tokens: 2000
    hard_limit_tokens: 3000
```

**Alternatives considered:**

1. **Hard 2K limit, block save.** *Rejected:* CLAUDE.md is edited outside this tool (in editors, by other Claude sessions). Blocking saves we don't own is impossible. Blocking *something* (e.g. a UI button) is theatre — the user just edits the file directly.
2. **No threshold, just show the count.** *Rejected:* loses the "is this OK?" answer. A score with no rubric is uninformative.

**Rationale:** The optimization guide recommends ~2K tokens. Soft/hard tiers match how guidelines work in practice (recommendation, then concern). Configurable means a project with genuinely complex rules (e.g. compliance-heavy codebases) can raise the bar without forking the tool. "Suggest only" matches the dashboard's role: it observes, it does not enforce.

### D6. Plugins data source

**Decision:** Read from `.claude/settings.json`'s `plugins` list (when present) plus enumerate `.claude/plugins/*/` if the directory exists. Cross-reference each plugin's manifest (`plugin.json`) for declared skills/hooks/agents.

**Rationale (no alternative was seriously considered):** Claude Code's plugin layout is documented; the dashboard should match it. No need to invent a new convention. If the layout shifts, this is the *only* place it bites us.

### D7. Sprint scope boundaries

**Decision:** Sprint 31 implements **Context tabs (Tools, Categories, Re-reads)**, **Process Guidelines & Audit tab**, **Skills usage tracking + hook**, and **Hook/Permissions/CLAUDE.md tab modifications**. The **Plugins tab is deferred to sprint 32** because plugin manifest semantics need a half-day of research and no current user pain points target plugins.

**Rationale:** 4 medium items + 1 small item is at the edge of "medium" sprint capacity (2-3 medium per the config). Plugins is genuinely independent — deferring it does not block any other tab. See Section 4.

---

## Section 3 — Sprint 31 implementation items

Five items, sized to sprint capacity. Three medium, one large, one small. Total estimated effort matches recent sprint pace (sprint 29 shipped 3 items: M+L+L).

Items are presented in the order they should ship; later items depend on earlier infrastructure.

---

### Item 1 — `dashboard-v2-actionable-prompt-registry-and-component`

**Goal:** Build the shared "Copy fix prompt" primitive that every other v2 tab will use, so we ship one implementation, not five.

**Complexity:** **S**

**Acceptance criteria:**

1. New module `src/agile_backlog/prompts.py` contains a `PromptTemplate` dataclass and a registry function `get_prompt(template_id, context: dict) -> str` that renders the prompt with project-specific data interpolated.
2. At least 8 templates registered: `claude_md_audit`, `claude_md_trim`, `skill_description_audit`, `skill_unused_analysis`, `hook_coverage_gap`, `permission_consolidate`, `context_budget_check`, `re_read_waste_fix`.
3. Each template returns a prompt that (a) names the specific finding, (b) includes relevant data inline (e.g. current CLAUDE.md content snippet, skill description text), (c) ends with a clear ask ("Propose 3 specific changes...").
4. New NiceGUI component `prompt_button(template_id, context)` in `src/agile_backlog/components.py` renders a small button labeled "Copy fix prompt" that copies the rendered prompt to clipboard via `ui.run_javascript`.
5. The button uses the shared-mutable-state-dict pattern (sprint 29 lesson) — no stale closures.
6. All clipboard text is XSS-safe in the Python layer; the JS bridge uses `navigator.clipboard.writeText` with a properly escaped payload.
7. Unit tests in `tests/test_prompts.py` verify each template renders with a representative context and produces non-empty, well-formed output.

**Technical specs:**

- Files created: `src/agile_backlog/prompts.py`, `tests/test_prompts.py`.
- Files modified: `src/agile_backlog/components.py` (add `prompt_button`).
- Templates are plain Python format strings, not Jinja — keep dependencies flat. Multi-line strings; 120-char rule applies.
- The button visually matches the existing `safe_html()` styling already used in cards.

**Dependencies:** None. Ships first.

---

### Item 2 — `dashboard-v2-context-view-tools-categories-rereads-tabs`

**Goal:** Add three new tabs to the Context view giving per-tool cost, category breakdown, and re-read waste analysis, each wired to the prompt registry from item 1.

**Complexity:** **M**

**Acceptance criteria:**

1. Context view gains three new tabs: **Tools**, **Categories**, **Re-reads**, in that order after the existing Overview tab.
2. **Tools tab:** sortable table with columns `Tool | Calls | Total tokens | % of session`. Sorting works on every column. Clicking a row expands an inline drilldown showing per-file token cost for that tool and a `prompt_button` that copies a context-budget-check prompt scoped to the tool.
3. **Categories tab:** four-row table grouping tools into `Reads`, `Writes`, `Search`, `Execution`. Each row shows total tokens, call count, and a percentage bar. The mapping (e.g. `Read+Glob` -> Reads, `Edit+Write` -> Writes, `Grep` -> Search, `Bash` -> Execution) lives in `pure.py` as a constant dict so it is pure-testable.
4. **Re-reads tab:** lists files re-read more than 3 times in the current report, sorted by count desc. Each row has the file path, count, total tokens spent re-reading, and a `prompt_button` for the `re_read_waste_fix` template.
5. All three tabs read from the existing `context_report.py` JSON output — no new log parsing.
6. Numeric and string content in `ui.html` calls is wrapped with `safe_html()` (sprint 29 XSS rule).
7. Tests added: `pure.py` category-mapping function gets unit tests; integration test verifies tab renders without exceptions for the existing fixture report.

**Technical specs:**

- Files modified: `src/agile_backlog/app.py` (Context view function — note: app.py extraction is a separate sprint 30 item; this work happens in the post-extraction `views/context.py` if extraction lands first, otherwise inline in app.py).
- Files modified: `src/agile_backlog/pure.py` (add `categorize_tools` and `compute_reread_waste`).
- Files modified: `src/agile_backlog/context_report.py` (add `tool_category_breakdown` helper).
- Drilldown uses the same `state dict` pattern shipped in sprint 29 fix `2c0faaa`.
- Tests: `tests/test_pure.py` (categorization), `tests/test_context_report.py` (breakdown), `tests/test_app_smoke.py` (renders).

**Dependencies:** Ships after item 1 (uses `prompt_button`).

---

### Item 3 — `dashboard-v2-process-view-guidelines-audit-tab`

**Goal:** Add the Process view "Guidelines & Audit" tab — a 6-row compliance scorecard that surfaces the optimization guide's rules with live measurements and one-click fix prompts.

**Complexity:** **M**

**Acceptance criteria:**

1. Process view gains a **Guidelines & Audit** tab (placed after Overview, before Skills).
2. Six guideline rows are rendered, each with `rule | status (pass/warn/fail) | measurement | prompt button`. Rules:
   - **CLAUDE.md token budget** — measure tokens in `CLAUDE.md`; pass if under soft, warn if soft <= n < hard, fail if >= hard. Threshold from `sprint-config.yaml`.
   - **Skill description audit** — count skills with descriptions over 200 chars OR missing the `Use this skill when...` / `Do not use when...` pattern; pass if zero.
   - **Memory tier compliance** — verify presence of L1 (`CLAUDE.md`) and that user-memory `MEMORY.md` exists; warn if any item in `MEMORY.md` looks like project-scope content (heuristic: contains the word "this project" or a file path inside the repo).
   - **Command guessing detection** — from session logs, ratio of `Bash` calls invoking a command for which a skill exists vs. invoking the skill itself. Threshold: warn at 20%, fail at 40%.
   - **Re-read waste score** — from session logs, ratio of duplicate `Read` calls per session, averaged across the report. Pass < 30%, warn 30-60%, fail > 60%.
   - **Hook coverage** — at minimum: a tool-logging hook (presence of `.claude/context-logs/` activity) and a `UserPromptSubmit` hook for skill invocations (after item 4 ships). Pass if both present.
3. Each row's "Copy fix prompt" button calls `prompt_button` from item 1 with appropriate template + context.
4. Scoring functions live in `pure.py` and `context_report.py`; the tab is a thin renderer.
5. Configuration values (token thresholds, ratios) come from a new `optimization:` section in `sprint-config.yaml`; defaults are baked in if absent.
6. Tests cover each scoring function with a representative fixture (good case, warn case, fail case).
7. Tab renders in under 500ms for the existing fixture data (no regression).

**Technical specs:**

- Files modified: `src/agile_backlog/app.py` (Process view — Guidelines & Audit tab).
- Files modified: `src/agile_backlog/pure.py` (`score_claude_md_budget`, `score_skill_descriptions_aggregate`, `score_memory_tier`).
- Files modified: `src/agile_backlog/context_report.py` (`score_command_guessing`, `score_reread_waste`, `score_hook_coverage`).
- Files modified: `src/agile_backlog/config.py` (optional `OptimizationConfig` Pydantic model with thresholds).
- Files modified: `.claude/sprint-config.yaml` (add `optimization:` block with documented defaults).
- Tests: `tests/test_pure.py`, `tests/test_context_report.py`, `tests/test_config.py`.
- Reuses `score_skill_quality` from sprint 29 for the per-skill component of the skill description rule.

**Dependencies:** Ships after item 1 (uses `prompt_button`). Independent of item 2.

---

### Item 4 — `dashboard-v2-skill-invocation-tracking-hook-and-skills-tab-usage`

**Goal:** Capture `/skill-name` invocations forward-only via a `UserPromptSubmit` hook, plumb them through the report pipeline, and surface usage counts on the Skills tab.

**Complexity:** **L**

**Acceptance criteria:**

1. New hook script at `.claude/hooks/log-skill-invocations.sh` (or `.py` — see specs) appends one JSONL line per `/skill-name` use to a new file `.claude/context-logs/skill-invocations.jsonl` with shape `{"timestamp", "event_type": "skill_invocation", "session_id", "skill"}`.
2. Hook is registered in `.claude/settings.json` under `hooks.UserPromptSubmit`.
3. `context_report.py` learns to read both `tools-*.jsonl` and `skill-invocations.jsonl`. Tool-stats logic explicitly filters to `event_type` either absent or `"tool_call"` (backwards-compat with pre-existing logs).
4. Sprint summary report gains a `skill_invocations` section: list of `{skill, count}` pairs sorted desc.
5. Process Skills tab gains a new column: `Invocations (this report)`. Skills with zero invocations after 5+ sessions show an "unused" badge with a `prompt_button` for `skill_unused_analysis` template.
6. Skills with no measured sessions (because the hook hasn't fired yet) show `(tracking from sprint 31)` instead of `0`. The dashboard distinguishes "no data yet" from "definitely zero."
7. Tests: fixture JSONL with mixed event types; verify tool stats are correct and skill counts are correct; verify backwards-compat with old logs that have no `event_type` key.

**Technical specs:**

- Files created: `.claude/hooks/log-skill-invocations.py` (Python preferred for cross-platform compat).
- Files modified: `.claude/settings.json` (register the hook). The hook entry uses the documented `UserPromptSubmit` event with a regex matcher for prompts beginning with `/`.
- Files modified: `src/agile_backlog/context_report.py` (event-type filtering, `skill_invocations` aggregation).
- Files modified: `src/agile_backlog/app.py` (Skills tab — usage column, unused badge).
- Files modified: `src/agile_backlog/pure.py` (helper to format the "tracking from sprint N" label).
- Tests: `tests/test_context_report.py` (mixed event-type fixture), `tests/test_pure.py` (label helper).
- Note: the hook captures the *typed* prompt text; we strip leading `/` and split on first whitespace to get the skill name. Skill names beginning with `plugin:` (e.g. `superpowers:writing-plans`) are preserved verbatim.

**Dependencies:** Ships after item 1 (uses `prompt_button` for the unused badge). Item 3's hook-coverage rule expects this hook to exist; if items 3 and 4 ship in the same sprint, item 3 should treat hook-presence as a soft pass even before this hook lands.

---

### Item 5 — `dashboard-v2-hooks-permissions-claude-md-tab-enhancements`

**Goal:** Modernize three existing Process tabs — Hooks (show command strings), Permissions (consolidation suggestions), CLAUDE.md (token budget UI).

**Complexity:** **M**

**Acceptance criteria:**

1. **Hooks tab:** displays each hook as `event | matcher | command` (full command string, not truncated; if multi-line, render in a code block). Each hook row gets a `prompt_button` for `hook_coverage_gap` if the matcher's tool/event is one we recommend covering and isn't.
2. **Permissions tab:** lists allow/deny entries from `.claude/settings.json` and `settings.local.json`. New "Suggested consolidations" sub-section flags pairs of entries that could collapse into one (e.g. `Bash(npm install)` + `Bash(npm test)` -> suggest `Bash(npm:*)`). Detection lives in `pure.py` as a pure function over the parsed permission list.
3. **CLAUDE.md tab:** shows current token count, soft/hard limits from config, status indicator (pass/warn/fail), and a `prompt_button` for `claude_md_trim` template (which embeds the current CLAUDE.md content for the prompt to act on).
4. Token counting reuses `tokens.py` if it has a counter; else add a thin wrapper using the same approximation `context_report.py` uses for tool-call estimation, for consistency.
5. Permission consolidation logic is an honest heuristic — it suggests, never auto-applies. UI text reads "Suggested" not "Recommended."
6. All three tabs use `safe_html()` for any rendered command/permission strings (sprint 29 XSS rule — these strings come from user-edited config files and may contain HTML-active characters).
7. Tests: `pure.py` consolidation function with a fixture permission list (>= 6 entries, mix of consolidatable and non-consolidatable patterns); CLAUDE.md token counter with a fixture file at known length.

**Technical specs:**

- Files modified: `src/agile_backlog/app.py` (three tab modifications).
- Files modified: `src/agile_backlog/pure.py` (`suggest_permission_consolidations`, `count_claude_md_tokens` if not already in `tokens.py`).
- Files modified: `src/agile_backlog/tokens.py` (add CLAUDE.md counter if missing).
- Tests: `tests/test_pure.py`, `tests/test_tokens.py`.

**Dependencies:** Ships after item 1 (uses `prompt_button`). Independent of items 2-4 but benefits from being last so the Guidelines & Audit tab (item 3) can link to the modernized data tabs in its prompts.

---

### Sprint 31 capacity summary

| Item | Size | Cumulative |
|---|---|---|
| 1. Prompt registry + component | S | S |
| 2. Context tabs (Tools/Categories/Re-reads) | M | S+M |
| 3. Process Guidelines & Audit tab | M | S+2M |
| 4. Skill invocation hook + Skills usage | L | S+2M+L |
| 5. Hooks/Permissions/CLAUDE.md modernization | M | S+3M+L |

Reads as: 1 small + 3 medium + 1 large. The default config says "medium: 2-3, large: 1-2." This sprint is at the upper edge but still within bounds. If sprint planning judges this too aggressive, item 5 is the first to defer (it is the most independent and visually less impactful than items 2 and 3). If anything else slips, ship items 1+2+3 — the prompt registry, the new context tabs, and the audit tab — these are the load-bearing v2 features. Items 4 and 5 are enhancements on top.

---

## Section 4 — Out of scope / deferred

| What | Source | Why deferred |
|---|---|---|
| **Plugins tab** (Process view) | T2 AC #6 ("Plugins tab: show installed plugins with their skills, hooks, agents") | No current user pain — no plugins in heavy use in this project. Plugin manifest format needs research before we commit UI to it. Deferred to sprint 32. |
| **Cross-sprint trend on per-tool cost** | T2 (extension) | Sprint 29 already ships cross-sprint trend on aggregate metrics. Per-tool trends would multiply the table cells by N sprints — needs a different visualization (line chart per tool) and is a sprint 33+ Done view enhancement. |
| **Retroactive skill invocation backfill** | implied by T2 AC #3 | Decision D2 above. Forward-only for sprint 31; sprint 32 will revisit only if the hook proves unreliable. |
| **Auto-applying permission consolidations** | T3 (implied by "permission consolidation" wording) | Sprint 31 ships *suggestions*. Auto-apply requires a write path to `settings.json` + a confirmation flow + rollback — its own sprint item. |
| **Optimization guide editing UI** | T1 (implied) | The guide is a markdown file. Editing it is what code editors are for. We score against it, we do not edit it from the dashboard. |
| **Per-session drilldown for skill invocations** | T2 AC #3 (extension) | Sprint 31 aggregates invocation counts across the report. Per-session drilldown is a sprint 32 item once we have multi-sprint data to drill into. |
| **Guideline rule customization UI** | T1 (extension) | Threshold values are configurable via YAML in sprint 31; full custom rule authoring (user-defined guidelines) is a sprint 33+ feature. |

---

## Section 5 — Migration notes (do not execute)

These notes describe the YAML edits to make against the three source backlog items once this design is approved. They are *documented*, not executed, per the task constraint.

### 5.1 `optimization-guidelines-dashboard-display-claude-code-best-practices-with-compliance-checks-and-improvement-prompts`

- **Outcome:** **Close as superseded.** Replaced by sprint-31 item 3 (`dashboard-v2-process-view-guidelines-audit-tab`).
- **Notes field:** prepend `Superseded by docs/design/SPRINT30_DASHBOARD_V2_DESIGN.md (sprint 31 item 3 — dashboard-v2-process-view-guidelines-audit-tab). All 7 ACs from the original item are addressed by the new item's 7 ACs; threshold values moved to sprint-config.yaml per design decision D5.`
- **Status:** move to `done` with a closure note, OR `archived` — depends on the project's convention for design-superseded items. Recommend `done` so it shows in the Done view archive with the closure note.

### 5.2 `design-session-context-and-process-dashboard-v2-with-per-tool-context-cost-skill-invocation-tracking-historical-sprint-comparison-and-actionable-prompts`

- **Outcome:** **Close as superseded.** Replaced by sprint-31 items 1, 2, 4, 5 collectively.
- **Notes field:** `This design session item is fulfilled by docs/design/SPRINT30_DASHBOARD_V2_DESIGN.md. Implementation lives in sprint-31 items: dashboard-v2-actionable-prompt-registry-and-component, dashboard-v2-context-view-tools-categories-rereads-tabs, dashboard-v2-skill-invocation-tracking-hook-and-skills-tab-usage, dashboard-v2-hooks-permissions-claude-md-tab-enhancements. Plugins tab (AC #6) deferred to sprint 32.`
- **AC handling:** Use the new sprint-30 `--acceptance-criteria` (replace) flag (per the `edit-repeatable-list-flags` item) to **replace** the original 10 AC bullets with one summary line: `See SPRINT30_DASHBOARD_V2_DESIGN.md for sprint-31 decomposition. Original 10 ACs traced to items 1/2/4/5 of that design.` Do not use `--append-acceptance-criteria` here; the original ACs are the *source*, not additional work.
- **Status:** move to `done` with closure note.

### 5.3 `process-review-prompts-actionable-one-click-prompts-for-claude-md-audit-skill-description-optimization-hook-coverage-gaps-permission-consolidation-and-context-budget-check`

- **Outcome:** **Close as superseded.** Replaced by sprint-31 item 1 (the prompt registry) plus the per-tab consumers in items 2-5.
- **Notes field:** `Superseded by docs/design/SPRINT30_DASHBOARD_V2_DESIGN.md. The "actionable prompts" surface is implemented as a shared registry in sprint-31 item 1 (dashboard-v2-actionable-prompt-registry-and-component) and consumed inline by items 2/3/4/5. Per design decision D1, prompts are co-located with findings rather than aggregated into an Action Center.`
- **AC handling:** This item had no ACs to migrate. Use `--append-acceptance-criteria` once with a single bullet: `Closed by sprint-31 item 1 + consumers; see design doc.` to leave a paper trail in the AC log.
- **Status:** move to `done` with closure note.

### 5.4 New sprint-31 items to create

For each of the 5 items above, create a new YAML in `backlog/`:

| Slug | Priority | Category | Sprint target |
|---|---|---|---|
| `dashboard-v2-actionable-prompt-registry-and-component` | P1 | feature | 31 |
| `dashboard-v2-context-view-tools-categories-rereads-tabs` | P1 | feature | 31 |
| `dashboard-v2-process-view-guidelines-audit-tab` | P1 | feature | 31 |
| `dashboard-v2-skill-invocation-tracking-hook-and-skills-tab-usage` | P1 | feature | 31 |
| `dashboard-v2-hooks-permissions-claude-md-tab-enhancements` | P1 | feature | 31 |

Each new item's `notes` field links back to this design doc as the source of record.

---

## Appendix A — Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `app.py` refactor (sprint 30 separate item) lands mid-sprint and rebases items 2/3/5 | Medium | Items 2/3/5 modify Context/Process view *bodies*. If extraction lands first, work in `views/context.py` and `views/process.py`; otherwise inline in app.py. Items are written to be insensitive to which file owns the view function. |
| `UserPromptSubmit` hook semantics differ across Claude Code versions | Low | Item 4 hook is read-only — it appends to a log file. If matcher syntax changes, only one file is affected. Hook script logs unparseable input verbatim under `event_type: "skill_invocation_unparsed"` so we never lose data. |
| Stale closures in NiceGUI bite again (sprint 29 lesson) | Medium | Every item that wires interactive UI uses the shared mutable state dict pattern from sprint 29 fix `2c0faaa`. AC #5 of item 1 makes this explicit for the prompt button. |
| XSS regression in any of the new tabs | Medium | All `ui.html()` content wrapped with `safe_html()` per sprint 29 lesson. AC #6 of item 2, AC #6 of item 5 make this explicit. Code review checklist includes XSS check. |
| Item count exceeds sprint capacity | Medium | Item 5 is the designated cut. Items 1+2+3 are the must-ship core; item 4 is high-value but standalone; item 5 is enhancement-only. |

## Appendix B — Open questions resolved during this design

- **"Should we add an Action Center top-level view?"** No — see decision D1. Co-located prompts.
- **"Should compliance scores affect Done view trends?"** Not in sprint 31. Once 2-3 sprints of compliance data accumulate, compliance trend lines are a natural sprint 33 Done view enhancement.
- **"Should the prompt registry support user-authored templates?"** Not in sprint 31. Built-in templates only. User-authored is a sprint 33+ feature gated on real demand.
- **"How does plugin manifest data flow into the (deferred) Plugins tab?"** Out of scope for this design. Sprint 32 design will research current Claude Code plugin layout and produce a separate spec.

## Appendix C — Touched-file inventory (sprint 31 cumulative)

```
NEW
  src/agile_backlog/prompts.py                     (item 1)
  tests/test_prompts.py                            (item 1)
  .claude/hooks/log-skill-invocations.py           (item 4)

MODIFIED
  src/agile_backlog/app.py                         (items 2, 3, 4, 5)
    or per-view files if app.py extraction lands first
  src/agile_backlog/components.py                  (item 1: prompt_button)
  src/agile_backlog/pure.py                        (items 2, 3, 4, 5)
  src/agile_backlog/context_report.py              (items 2, 3, 4)
  src/agile_backlog/config.py                      (item 3)
  src/agile_backlog/tokens.py                      (item 5, possibly)
  .claude/settings.json                            (item 4: hook registration)
  .claude/sprint-config.yaml                       (item 3: optimization block)
  tests/test_pure.py                               (items 2, 3, 5)
  tests/test_context_report.py                     (items 2, 3, 4)
  tests/test_config.py                             (item 3)
  tests/test_tokens.py                             (item 5)
  tests/test_app_smoke.py                          (item 2)
```

Files modified across multiple items show why item 1 must ship first: every later item depends on the prompt-button component, and four of five items modify `app.py` and `pure.py` — sequential ordering keeps merge conflicts manageable.

---

**End of design.**
