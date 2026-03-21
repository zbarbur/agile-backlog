# Memory Index

## Project Status
- Sprint 6 COMPLETED (2026-03-21)
- 102 tests, ruff clean, all PRs merged to main
- YAML is single source of truth (TODO.md and KANBAN.md deprecated)
- Decision: migrate from Streamlit to NiceGUI (spec review done, needs expanded migration spec)

## Key Patterns
- Board runs in forced light mode (.streamlit/config.toml)
- Design system spec at docs/superpowers/specs/2026-03-21-design-system.md
- Frontend evaluation at docs/superpowers/specs/2026-03-21-frontend-evaluation.md
- Use `.venv/bin/python` for all commands (uv-managed venv)
- Subagent-driven development for sprint execution
- Sprint skills now use agile-backlog CLI (not TODO.md)
- Phases simplified to: plan, build, review + design_reviewed/code_reviewed flags

## Sprint 7 Prep
- Write NiceGUI migration spec FIRST (address 3 critical + 8 important review findings)
- Verify drag-and-drop with SortableJS proof-of-concept
- Component mapping needed before coding
- NiceGUI has different state model (persistent, no rerun) — architecture guidance needed

## Lessons
- Dogfooding finds UX issues faster than specs
- Streamlit has design ceiling — NiceGUI chosen as replacement
- Design system research before implementation prevents iteration churn
- Screenshots beat text for UI feedback loops
- Spec review before implementation catches architectural gaps
- Sprint skills should write to YAML items, not TODO.md
