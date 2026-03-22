# Changelog

All notable changes to agile-backlog will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [0.3.0] - 2026-03-22
### Changed
- Package renamed from `src` to `agile_backlog` for proper Python packaging
- All imports now use `from agile_backlog import ...`
- Version is now dynamic (single source of truth in `__init__.py`)

### Added
- `py.typed` marker for type checker support
- Public API exports in `__init__.py` (`BacklogItem`, `load_all`, `load_item`, `save_item`)
- `CHANGELOG.md`
- `[build-system]` table in `pyproject.toml`

## [0.2.0] - 2026-03-21

### Added
- NiceGUI migration spec (frontend evaluation)
- Workflow phases: plan, build, review
- Review gate flags: design_reviewed, code_reviewed
- CLI `edit` command for updating any item field
- test_plan field on BacklogItem
- Sprint filter applies to all columns
- "Unplanned" sprint filter option
- Auto-set phase to "plan" when moving to doing
- Phase migration (old 8 phases → new 3)
- Claude Code plugin (/backlog command)
- Design system spec (Linear/Notion/Trello research)
- Sprint indicator badge in board header
- Smart filtering (backlog-only for priority/category, all-columns for sprint)
- README with installation instructions
- GitHub Actions CI (lint + test matrix)
- Dependabot for pip and GitHub Actions
- PR template

### Changed
- Sprint skills rewritten to use YAML instead of TODO.md
- KANBAN.md deprecated (YAML is source of truth)
- Card design: two-row layout, pastel badges, P1 accent, done strikethrough
- Forced light theme via .streamlit/config.toml

## [0.1.0] - 2026-03-21

### Added
- BacklogItem Pydantic model with slugify
- YAML store with git-root auto-detection
- Click CLI: add, list, move, show, serve
- Streamlit Kanban board with 3 columns
- Filter bar (priority, category, sprint, search)
- Category color system with emoji badges
- Full-text search across title, description, tags
