# Sprint 27 Handover — Process Tools, Context Dashboard & Bug Fixes

**Date:** 2026-04-02
**Branch:** sprint27/main -> pending merge to main
**Version:** 0.27.0

## Sprint Theme

Added observability layer to the web UI — Context analysis dashboard and Process management tools view — alongside error detection in hooks and two bug fixes. Extensive user feedback drove iterative UI improvements.

## Completed Items (6/6)

| Item | Pri | Category | Complexity | Key Files |
|------|-----|----------|-----------|-----------|
| Process management tools review | P1 | feature | L | `app.py` (Process view: Skills/CLAUDE.md/Handovers/Hooks/Permissions tabs) |
| Context analysis dashboard | P2 | feature | M | `app.py` (Context view: tool breakdown, file heatmap, sessions) |
| Detect failed tool calls | P2 | feature | M | `post-tool-logger.sh`, `context_report.py` (analyze_errors) |
| Claude code optimization review | P2 | chore | S | 4 new backlog items from docs/optimization research |
| filter_items dead code fix | P3 | bug | S | `pure.py` (removed unreachable 'unplanned' branch) |
| set_current_sprint None fix | P3 | bug | S | `config.py` (guard against None in missing config) |

## Deferred Items

None — all 6 items completed.

## Architecture Changes

- **Two new UI views**: "Context" and "Process" added as view modes alongside Board/Backlog/Done
- **Visual nav grouping**: divider separates Sprint views (Board/Backlog/Done) from Observability views (Context/Process)
- **Error detection in hooks**: `post-tool-logger.sh` now captures `exit_code`, `error`, `error_message` from tool_result
- **analyze_errors()**: new function in `context_report.py` for error rate analysis
- **skill_usage_stats()**: new function for per-skill invocation counting
- **Plugin skill scanning**: Process view scans project, personal, and plugin cache directories for skills

## Context Efficiency Report

| Metric | Value |
|--------|-------|
| Sessions | 2 |
| Total tool calls | 409 |
| Reads | 110 (unique: 43) |
| Re-read ratio | 61% |
| Top re-read file | app.py (39x) |
| Edits | 51 |
| Writes | 10 |
| Bash commands | 211 |
| Errors | 0 |

**Key insight**: 61% re-read ratio driven by iterative UI development on app.py. Subagents also re-read files the main session had in context. Future sprint should enforce offset/limit targeted reads and pass more context to subagents.

## Test Coverage

| Metric | Value |
|--------|-------|
| Tests (start) | 304 |
| Tests (end) | 331 |
| New tests | 27 |
| Test runner | pytest |
| Lint | ruff (clean) |

## Commits

```
4fe1c43 chore: add sprint context summary automation backlog item
e7546ce chore: add optimization guidelines dashboard backlog item
0783e5d chore: add design session backlog item for dashboard v2
48a7b33 fix: show tool names in Context drilldown, show tokens in Skills tab
46f3295 fix: scan correct plugin cache path (vendor/plugin/version/skills)
2b1da0c fix: restore Context page, show plugin/personal skills in Process view
cabd625 chore: add backlog items for sprint retro dashboard, process prompts, skill tracking
4101eb7 feat: context dashboard drilldown, sprint history in Done view, process view divider
8355040 feat: Sprint 27 — process tools UI, context dashboard, error detection, bug fixes
58b3494 chore: start Sprint 27 — Process Tools, Context Dashboard & Bug Fixes
```

## Lessons Learned

- **NiceGUI refreshable + nonlocal don't mix**: Sprint selector broke the Context page because `nonlocal` inside `_on_sprint_change` conflicted with `@ui.refreshable`. Use state dicts instead.
- **Plugin cache has vendor directory**: Path is `cache/vendor/plugin/version/skills/`, not `cache/plugin/version/skills/`.
- **Skill usage tracking gap**: PostToolUse hook only captures Skill tool calls, not `/slash-command` invocations. Need UserPromptSubmit hook.
- **Showing zeros is worse than showing nothing**: Skills tab showed 0 usage for all skills — removed in favor of token cost.
- **Iterative UI work drives high re-read ratios**: app.py was read 39x due to edit-verify cycles.

## Recommendations for Next Sprint

- **Design session first**: Run /plan to scope the dashboard v2 before implementing — 3 P1 items need consolidated design
- **Sprint context summary automation**: Build `agile-backlog context-summary` CLI command and integrate into sprint-end
- **Optimization guidelines dashboard**: Display best practices with compliance checks and improvement prompts
- **Track slash command invocations**: UserPromptSubmit hook to capture /skill-name usage
- **Consider app.py refactoring**: At ~1500 lines, the single-file app is getting large. Process/Context views could be extracted.

## New Backlog Items Created (10)

From optimization review:
1. Optimize CLAUDE.md structure (P2, chore)
2. Session lifecycle hooks (P2, feature)
3. Status line script (P3, feature)
4. Session analytics JSONL analyzer (P2, feature)

From user feedback:
5. Sprint retro dashboard — full per-sprint analysis (P1, feature)
6. Process review prompts — actionable improvement prompts (P1, feature)
7. Track slash command skill invocations (P2, feature)
8. Improve Process view (P2, feature)
9. Design session — dashboard v2 (P1, feature)
10. Optimization guidelines dashboard (P1, feature)
11. Analyze/optimize settings.local.json permissions (P2, feature)
12. Sprint context summary CLI + Done view integration (P1, feature)
