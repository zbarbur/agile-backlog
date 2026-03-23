# Agentic Agile Manifest

## Core Principles

1. **Research first, design second, code third** — validate before building
2. **Quality review at every stage** — spec review, plan review, code review
3. **YAML items are the single source of truth** — not TODO.md, not KANBAN.md
4. **Sprint skills are config-driven** — one sprint-config.yaml per project
5. **Specialists enhance, reviewers verify** — separation of concerns

## Process Flow

```
Backlog → Sprint Start → Spec → Plan → Build → Review → Done → Sprint End
```

## Context System

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project rules and code style |
| `.claude/MEMORY.md` | Agent memory across sessions |
| `.claude/sprint-config.yaml` | Sprint configuration |
| `docs/process/PROJECT_CONTEXT.md` | Project snapshot |
| `docs/process/DEFINITION_OF_DONE.md` | Quality gates |
| `backlog/*.yaml` | Backlog items (source of truth) |

## Sprint Cadence

1. `/sprint-start N` — scope, spec, branch
2. Build — TDD, frequent commits
3. `/sprint-end` — verify DoD, handover, merge, clean up
