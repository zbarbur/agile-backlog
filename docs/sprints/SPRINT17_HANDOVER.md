# Sprint 17 Handover — Sprint Execute + Framework Completion

**Date:** 2026-03-23
**Branch:** sprint17/main
**Tests:** 173 (was 162)
**Commits:** 2 (setup + implementation)

## Completed Tasks (7/7)

| Item | Size | Category | Tags |
|------|------|----------|------|
| v.future bug fix — add dialog missing future option | S | bug | ui |
| Reopen done items — button + reason dialog | S | feature | ui, planning |
| Flagged comments check in sprint-start | S | feature | skills, comments |
| /check-comments slash command | S | feature | skills, comments |
| Framework integration audit | M | feature | skills, planning |
| Sprint-execute skill — subagent dispatch | L | feature | skills |
| Template skills — /plan, /document, /report-bug, /fix-bug, /sprint-plan-next | L | feature | skills |

## Key Deliverables

### Sprint-Execute Skill (Phase 2 of framework integration)
The core automation piece. `/sprint-execute` reads doing items, selects specialists from `specialist_defaults` in sprint-config.yaml, dispatches subagents via superpowers, runs CI after each task, and moves items to review phase. Integrates with brainstorming, writing-plans, subagent-driven-development, and requesting-code-review skills.

### Template Skills (Phase 4 of framework integration)
5 process skills ported from agentic-agile-template spec:
- `/plan` — 4 modes: project inception, roadmap, sprint allocation, scope analysis
- `/document` — 7 modes: research, design, architecture, audit, runbook, update, review
- `/report-bug` — structured bug creation with auto-tagging
- `/fix-bug` — load from backlog, diagnose, fix after approval
- `/sprint-plan-next` — pre-plan next sprint scope during current sprint

### Full Sprint Lifecycle
The project now has a complete automated sprint lifecycle:
```
/sprint-start → /sprint-execute → /sprint-end
```
Plus supporting skills: /plan, /document, /report-bug, /fix-bug, /sprint-plan-next, /check-comments

### Framework Audit Fixes
- TASK_TEMPLATE.md rewritten to reference YAML items (was referencing TODO.md)
- specialist_defaults added to sprint-config.yaml (10 domain→agent mappings)
- Handover review step added to sprint-start skill
- CLAUDE.md context table updated (removed TODO.md/KANBAN.md references)
- Memory audit step added to sprint-end skill

### Bug Fix + UI Features
- Add dialog now shows 4 sprint target options (was 3 — v.future was missing)
- Done items have a Reopen button with reason dialog; logic extracted to `pure.py:apply_reopen()`

## Key Decisions

1. **Skills are generic, config is project-specific** — all skills use `{config_ref}` placeholders. Any project can adopt by writing one sprint-config.yaml.
2. **Memory audit at sprint boundaries, not per-session** — avoids noise during regular work. Sprint-end skill has a structured 4-step audit.
3. **Tag taxonomy expanded** — 8 tags (ui, cli, skills, plugin, packaging, data, planning, comments) covering all backlog domains. Applied to all 38 items.
4. **Gap report accepted inline** — framework integration audit done conversationally, gaps found and fixed. Future gaps filed as issues.

## Architecture Changes

- `pure.py` — added `apply_reopen()` function (reopen logic extracted from components.py)
- `app.py` — added v.future sprint target option to add dialog
- `components.py` — added reopen dialog and button for done items
- `.claude/skills/` — 6 new skill files (sprint-execute, plan, document, report-bug, fix-bug, sprint-plan-next)
- `.claude/commands/` — 6 new command files
- `.claude/sprint-config.yaml` — added specialist_defaults section
- `docs/process/TASK_TEMPLATE.md` — full rewrite for YAML items

## Known Issues

- Board requires page refresh after CLI-driven YAML changes (backlog item created)
- No specialist agent files in `.claude/agents/` yet (Phase 5 — sprint-execute works without them via auto-detection)
- `cli-bulk-operations` still missing — tagging 38 items required 37 separate commands (bumped to P2)

## Test Coverage

- 173 tests (up from 162)
- +4 tests for v.future add dialog
- +7 tests for reopen item logic

## Recommendations for Next Sprint

1. **CLI bulk operations (P2)** — most impactful quality-of-life improvement for agent operations
2. **CLI validate + sprint status commands (P2)** — agent-facing CLI improvements
3. **CLI list columns (P2)** — show phase/sprint/tags in default table output
4. **Specialist agent integration (P2)** — Phase 5 of framework, install agent prompts
5. **GitHub Actions CI (P2)** — automated CI on push
