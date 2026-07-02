# Design: Two-Channel, One-Step Adoption (`init` command + bundled plugin)

**Date:** 2026-07-02
**Status:** Approved (design), pending implementation plan
**Related:** `docs/guides/ADOPTION.md`, `docs/superpowers/specs/2026-06-07-cli-analyze-optimization-loop-design.md`

## Overview

Adopting agile-backlog in an existing project today is an 8-step manual runbook
(`ADOPTION.md`): pip install → import tasks → hand-write `sprint-config.yaml` →
manually copy a hook script that isn't even shipped in the package → hand-edit 9
`PostToolUse` matchers into `settings.local.json` → create dirs → run
`install-skills` → start a sprint. This is the "Storybook-class" adoption friction.

Goal: **cut adoption friction** so that, after a one-time Python install, everything
else is effectively one step. Secondary: bring the currently-stub `plugin/` up to a
real, installable Claude Code plugin so there are two coherent channels instead of a
working pip path and a misleading plugin stub.

Non-goal (deferred): marketplace publishing / discovery ("reach"). Explicitly out of
scope per brainstorming.

## Design decisions

- **The CLI and the plugin split along the CLI-dependency line.** A Claude Code
  plugin can ship skills/commands/hooks but cannot install a Python CLI. So the
  plugin owns *content*; `pip install` owns the *CLI*; a new `agile-backlog init`
  owns the *project-specific scaffolding* that requires the CLI.
- **Python-as-one-time-prerequisite is acceptable** (confirmed with user: adopters
  are mixed-language but installing Python once is fine). This rules out the heavier
  MCP-server-via-uvx rewrite (YAGNI) — skills keep shelling out to the CLI unchanged.
- **Single source of truth for content, mirrored by a sync script.** Skills and
  hooks live once under the package; a script mirrors them into `plugin/`. A CI check
  prevents drift. No hand-maintained duplicates.
- **`init` merges, never clobbers**, existing `settings.local.json` hooks and
  existing files (idempotent; `--force` to overwrite).

## Adoption paths (target end state)

**Plugin path:**
1. `/plugin install agile-backlog`  → skills + commands + hooks
2. `pip install agile-backlog`       → CLI on PATH
3. `agile-backlog init --config-only` → scaffold `sprint-config.yaml`, dirs, gitignore

**Pip-only path:**
1. `pip install agile-backlog`
2. `agile-backlog init`               → full: config + skills + hooks + dirs + gitignore

Task import remains an interactive, Claude-driven step (via the adoption guide/skill),
not part of `init`.

## Architecture / components

### 1. Canonical content source (single source of truth)
- `src/agile_backlog/bundled_skills/` — the 9 skills (already exists).
- **New** `src/agile_backlog/bundled_hooks/post-tool-logger.sh` — the context-logging
  hook, made package data via `pyproject.toml` (`[tool.setuptools.package-data]` or
  equivalent). Fixes the current gap where the hook ships only in the repo's
  `.claude/hooks/`, not in the pip package.
- agile-backlog's own `.claude/` remains a downstream *consumer* (dogfoods `init`).

### 2. `agile-backlog init` command (`src/agile_backlog/cli.py`)
Behavior:
- **Detect** `test`/`lint`/`ci`/`format` commands and `language` from
  `pyproject.toml` (pytest/ruff) or `package.json` (npm scripts); fall back to
  prompts with sensible defaults.
- **Scaffold** `.claude/sprint-config.yaml` from a template using detected/prompted
  values. Skip if present unless `--force`.
- **Install skills** by reusing the existing `install-skills` logic (DRY — extract a
  shared helper rather than duplicating the copy loop).
- **Install hooks:** copy `bundled_hooks/post-tool-logger.sh` → `.claude/hooks/`, then
  **merge** the 9 `PostToolUse` matchers into `.claude/settings.local.json` without
  discarding existing hook entries (parse JSON, append matchers that aren't already
  present, write back).
- **Create** `docs/sprints/` (and any other dirs the skills reference), append
  `.claude/context-logs/` to `.gitignore` (create if missing, no duplicate lines).
- Flags: `--config-only` (scaffold config + dirs + gitignore only; skip skills/hooks —
  for plugin users), `--force` (overwrite existing files), idempotent by default.
- **CLAUDE.md:** `init` *prints* the suggested process block for the user to paste; it
  does **not** edit an existing `CLAUDE.md` (decision A — non-invasive).

### 3. Full plugin (`plugin/`)
- `plugin/plugin.json` — bump version; keep `commands` + `skills`, add `hooks`.
- `plugin/skills/` — the 9 skills (synced from canonical; replaces the single stub).
- `plugin/commands/` — the sprint slash-commands (`/sprint-start`, `/sprint-execute`,
  `/sprint-end`, `/sprint-plan-next`, `/plan`, `/fix-bug`, `/report-bug`, `/document`,
  plus existing `backlog`) so the discoverable slash surface works in plugin-land
  (decision B).
- `plugin/hooks/hooks.json` — wires `post-tool-logger.sh` to the 9 `PostToolUse`
  matchers, referencing the script via `${CLAUDE_PLUGIN_ROOT}` so it resolves inside
  the installed plugin.
- No `marketplace.json` yet — plugin is valid + installable from the repo; publishing
  is deferred (decision C).

### 4. `scripts/sync-plugin.py`
- Mirrors `src/agile_backlog/bundled_skills/` → `plugin/skills/`,
  `src/agile_backlog/bundled_hooks/` → `plugin/hooks/`, and regenerates command files
  as needed.
- Run at release / pre-commit.
- **CI check:** a pytest (or ruff-adjacent) test that runs the sync in `--check` mode
  and fails if `plugin/` differs from canonical, preventing drift.

### 5. Rewrite `docs/guides/ADOPTION.md`
Replace the 8-step manual runbook with the two 3-step paths above. Keep the
task-import heuristics section (still needed for the interactive import step).

## Data / interface changes

- New CLI command `init` (+ flags). No changes to existing commands' behavior;
  `install-skills` internals refactored to expose a reusable helper.
- `pyproject.toml` package-data gains `bundled_hooks/`.
- `plugin/plugin.json` schema gains `hooks`.
- New file `plugin/hooks/hooks.json`.

## Migration plan

- Existing pip users are unaffected (`install-skills` keeps working). `init` is
  additive.
- agile-backlog itself re-runs `init`/sync to dogfood the new layout; verify its own
  `.claude/` is unchanged in behavior (same hook, same skills).

## Testing strategy

- **`init` unit tests:** config detection (pyproject vs package.json vs neither),
  idempotency (second run is a no-op), `--force`, `--config-only`, and the
  settings.local.json **merge** (existing hooks preserved, no duplicate matchers).
- **Hook-bundling test:** the hook is importable as package data from an installed
  wheel (build + inspect, or `importlib.resources`).
- **Sync/drift test:** `sync-plugin.py --check` passes on a synced tree and fails on a
  divergent one; CI runs it.
- **Plugin validity:** `plugin.json` + `hooks.json` parse; the 9 skills and commands
  are present in `plugin/` after sync.
- CI gate unchanged: `ruff check . && ruff format --check . && pytest tests/ -v`.

## Open questions

None blocking. Detail deferred to the implementation plan:
- Exact `hooks.json` schema fields for plugin hooks (verify against current Claude
  Code plugin docs during implementation).
- Whether command files can be generated from skills or must be authored separately
  (affects step 4 scope).
