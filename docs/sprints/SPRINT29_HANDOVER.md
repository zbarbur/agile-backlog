# Sprint 29 Handover — Observability & Skill Management

**Date:** 2026-04-07
**Branch:** sprint29/main -> pending merge to main
**Version:** 0.29.0

## Sprint Theme

Added observability tooling (context summary CLI, retrospective dashboard with cross-sprint trends) and skill management UI (view, edit, validate, quality scoring). Also fixed Context dashboard bugs where tool names were invisible and per-tool token costs were missing.

## Completed Items (3/3)

| Item | Pri | Category | Complexity | Key Files |
|------|-----|----------|-----------|-----------|
| Sprint context summary CLI + Done view | P1 | feature | M | `context_report.py` (generate_sprint_summary, estimate_tool_tokens), `cli.py` (context-summary cmd), `app.py` (Done view markdown) |
| Sprint retrospective dashboard | P1 | feature | L | `context_report.py` (load_all_sprint_reports, compare_sprints), `pure.py` (format_trend_indicator), `app.py` (Done view comparison table + per-sprint retro) |
| Skill management UI | P1 | feature | L | `pure.py` (score_skill_quality), `app.py` (Process view expandable skills with edit/validate/save) |

## Deferred Items

None — all 3 items completed.

## Architecture Changes

- **New CLI command**: `agile-backlog context-summary --sprint N` generates markdown summary from JSON report
- **Context analysis pipeline extended**: JSONL logs -> JSON report -> markdown summary -> Done view rendering
- **Cross-sprint comparison**: `compare_sprints()` computes trend analysis (improving/declining/stable) across sprints
- **Skill quality scoring**: `score_skill_quality()` evaluates description length, trigger keywords, action patterns, content structure (0-100 score)
- **Interactive Skills tab**: Replaced static HTML table with expandable cards supporting inline editing and save-back
- **Bug fixes**: Context dashboard tool names now visible (expansion styling + bar_html rendered inside), per-tool token estimates displayed
- **XSS hardening**: All `ui.html()` values consistently wrapped with `safe_html()`, bare `except Exception` narrowed to specific types

## Context Efficiency Report

| Metric | Value |
|--------|-------|
| Sessions | 2 |
| Total tool calls | 751 |
| Reads | 224 (re-read ratio: 78%) |
| Top re-read file | app.py (88x) |
| Edits | 97 |
| Writes | 13 |
| Bash commands | 315 |
| Estimated tokens | ~258k |

**Key insight**: 78% re-read ratio is critical — driven by app.py being read 88 times across subagent and main sessions. The app.py refactoring backlog item is essential. Subagents re-read files the parent already had in context. Future sprints should pass file content directly to subagents and use offset/limit for targeted reads.

## Test Coverage

| Metric | Value |
|--------|-------|
| Tests (start) | 331 |
| Tests (end) | 354 |
| New tests | 23 |
| Test runner | pytest |
| Lint | ruff (clean) |

## Commits

```
cdb00ed feat: Sprint 29 — context summary CLI, retro dashboard, skill management UI
092d54d chore: start Sprint 29 — Observability & Skill Management
```

## Lessons Learned

- **Stale closures in NiceGUI**: Edit/validate buttons captured content at render time. After save, they'd use stale data. Fix: use shared mutable state dicts instead of closure-captured values.
- **XSS consistency matters more than risk assessment**: Code review caught numeric values unescaped — safe in practice but violating the project rule. Consistent `safe_html()` usage prevents future regressions.
- **Subagent auth failures need graceful recovery**: One subagent hit a 401 error mid-implementation. The partially completed work (tests + pure functions) was recoverable, and manual completion of the UI portion was straightforward.
- **app.py at 88 reads is unsustainable**: The single-file UI architecture forces excessive re-reading. The refactoring backlog item should be prioritized.

## Recommendations for Next Sprint

- **Refactor app.py**: Extract Context, Process, Done views into separate modules — 88 reads this sprint is critical
- **Pass file content to subagents**: Reduce re-read ratio by including relevant code in subagent prompts
- **Design session for dashboard v2**: 3 P1 items from Sprint 27 still need consolidated design (process review prompts, optimization guidelines, context dashboard enhancements)
- **Track slash command invocations**: UserPromptSubmit hook to capture /skill-name usage for accurate skill adoption metrics
- **Add integration test for skill edit/save flow**: Current tests cover scoring but not the full edit-save-validate cycle
