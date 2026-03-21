# Memory Index

## Project Status
- Sprint 5 COMPLETED (2026-03-21)
- 96 tests, ruff clean, all PRs merged
- YAML is single source of truth (TODO.md and KANBAN.md deprecated)

## Key Patterns
- Board runs in forced light mode (.streamlit/config.toml)
- Design system spec at docs/superpowers/specs/2026-03-21-design-system.md
- Use `.venv/bin/python` for all commands (uv-managed venv)
- Subagent-driven development for sprint execution

## Lessons
- Dogfooding finds UX issues faster than specs
- Streamlit has design ceiling — evaluate alternatives when polish matters
- Design system research before implementation prevents iteration churn
- Screenshots beat text for UI feedback loops
