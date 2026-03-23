# Export agile-backlog to Agentic Agile Template — Design Spec

**Date:** 2026-03-23
**Status:** Draft
**Context:** The agentic-agile-template uses KANBAN.md + TODO.md (flat markdown) for backlog management. agile-backlog offers structured YAML items + CLI + Web UI. This spec defines how to integrate agile-backlog into the template as the backlog management layer.

## Goal

Replace the template's markdown-based backlog system (KANBAN.md + TODO.md) with agile-backlog, add automated sprint execution (`/sprint-execute`), and preserve the template's proven process docs, specialist agents, and session recovery protocol.

---

## What the Template Currently Has

| Component | Format | Purpose |
|-----------|--------|---------|
| `KANBAN.md` | Flat markdown sections | Backlog → Candidate → Doing → Done flow |
| `TODO.md` | Markdown task specs | Active sprint tasks with DoD checkboxes |
| `TODO-NEXT.md` | Optional markdown | Draft next sprint scope |
| `.claude/project.json` | JSON | Tracker config (github/none), infra config |
| `SPRINT{N}_HANDOVER.md` | Markdown | Sprint delivery log |
| `PROJECT_CONTEXT.md` | Markdown | Project snapshot with sprint history |
| `SPRINT_START_CHECKLIST.md` | Markdown checklist | Planning protocol |
| `SPRINT_END_CHECKLIST.md` | Markdown checklist | Closure protocol |

### How Items Flow Today (template)

```
KANBAN.md Backlog
  ↓ (/sprint-start: select scope)
KANBAN.md Doing + TODO.md task specs
  ↓ (MANUAL execution: implement, check off DoD by hand)
KANBAN.md Done + TODO.md marked complete
  ↓ (/sprint-end: archive)
SPRINT{N}_HANDOVER.md
```

### How Items Will Flow (with agile-backlog + sprint-execute)

```
agile-backlog items (status: backlog)
  ↓ (/sprint-start: select scope, write specs, tag sprint)
agile-backlog items (status: doing, phase: plan → spec)
  ↓ (/sprint-execute: brainstorm → plan → dispatch subagents → build → test → review)
agile-backlog items (status: doing, phase: review)
  ↓ (/sprint-end: verify DoD against code → move to done)
agile-backlog items (status: done) + SPRINT{N}_HANDOVER.md
```

The key difference: **the template has no /sprint-execute**. Execution is entirely manual — the developer reads TODO.md, implements, and checks off boxes. We add automated execution with specialist agents, two-stage review, and TDD.

**Pain points (current template):**
- Manual markdown editing for every state change
- No filtering, sorting, or querying
- No web UI for visual planning
- DoD checkboxes are text — not verifiable programmatically
- Items lack structured fields (just `- [area] description (S/M/L)`)
- Sprint history scattered across KANBAN.md Done section + handover docs

---

## What agile-backlog Replaces

| Template Component | Replaced By | How |
|-------------------|------------|-----|
| `KANBAN.md` Backlog section | `backlog/*.yaml` items with `status: backlog` | Each item is a YAML file with structured fields |
| `KANBAN.md` Doing section | Items with `status: doing` | `agile-backlog list --status doing` |
| `KANBAN.md` Done section | Items with `status: done` | `agile-backlog list --status done --sprint N` |
| `KANBAN.md` Candidate section | Items with `sprint_target: N+1` | `agile-backlog list --sprint N+1` |
| `KANBAN.md` Tech Debt section | Items with `category: chore` and `tags: [tech-debt]` | `agile-backlog list --category chore --tags tech-debt` |
| `TODO.md` task specs | Item fields: goal, acceptance_criteria, technical_specs, test_plan, complexity | `agile-backlog show {id}` |
| `TODO.md` DoD checkboxes | `acceptance_criteria: [...]` field | Verifiable by code inspection at sprint-end |
| `TODO-NEXT.md` | Items with `sprint_target: N+1`, `status: backlog` | `agile-backlog list --sprint N+1 --status backlog` |
| Manual status tracking | `agile-backlog move {id} --status doing/done` | CLI commands |
| Bug entries in KANBAN.md | `agile-backlog add "title" --category bug` | Structured bug items |

## What the Template KEEPS (unchanged)

| Component | Why kept |
|-----------|---------|
| `CLAUDE.md` | Project rules — auto-loaded, essential |
| `MEMORY.md` | Session context — auto-loaded, essential |
| `BOOTSTRAP.md` | Session recovery protocol — references agile-backlog commands instead of file reads |
| `PROJECT_CONTEXT.md` | Project snapshot — still written at sprint-end |
| `SPRINT{N}_HANDOVER.md` | Sprint delivery log — still written, now generated from agile-backlog data |
| `CODING_STANDARDS.md` | Code style — unchanged |
| `DEFINITION_OF_DONE.md` | DoD guide — unchanged (referenced when writing AC) |
| `AGENTIC_AGILE_MANIFEST.md` | Philosophy — updated to reference agile-backlog |
| `TASK_TEMPLATE.md` | Updated to show agile-backlog field mapping |
| `.claude/agents/*.md` | Specialist agents — unchanged |
| `SQUAD_PLANNING.md` | Agent assignment guide — unchanged |
| `bin/agents.sh` | Agent management — unchanged |
| `.claude/project.json` | Extended with agile-backlog config |

---

## Integration Design

### 1. agile-backlog as Template Dependency

The template adds agile-backlog as a development tool:

```bash
# In template's init-project.sh or setup guide
pip install agile-backlog  # or: pip install git+https://github.com/zbarbur/agile-backlog.git
```

**Directory structure added:**
```
project-root/
  backlog/           ← YAML items (git-tracked)
  .agile-backlog.yaml  ← config (current sprint, etc.)
```

### 2. Field Mapping: KANBAN.md Item → agile-backlog Item

| KANBAN.md format | agile-backlog YAML field |
|-----------------|------------------------|
| `- [area] description (M)` | `title`, `tags: [area]`, `complexity: M` |
| Section: Backlog / Doing / Done | `status: backlog / doing / done` |
| `(S)` / `(M)` / `(L)` in parentheses | `complexity: S / M / L` |
| `## Sprint N — Candidate` section | `sprint_target: N`, `status: backlog` |
| `[area]` tag | `tags: [area]` + `category` mapping (see below) |
| Sprint number from section header | `sprint_target: N` |
| Tech Debt section | `category: chore`, `tags: [tech-debt]` |
| Bug label `[BUG]` | `category: bug` |

**Area → Category mapping:**
| KANBAN area | agile-backlog category | agile-backlog tags |
|------------|----------------------|-------------------|
| `[test]` | `chore` | `test` |
| `[core]` | `feature` | `core` |
| `[module]` | `feature` | `module` |
| `[infra]` | `chore` | `infra` |
| `[docs]` | `docs` | `docs` |
| `[api]` | `feature` | `api` |
| `[ui]` | `feature` | `ui` |
| `[security]` | `feature` | `security` |
| `[ci]` | `chore` | `ci` |
| `[refactor]` | `chore` | `refactor` |
| `[perf]` | `feature` | `performance` |
| `[research]` | `docs` | `research` |
| `[process]` | `docs` | `process` |
| `[lint]` | `chore` | `lint` |

### 3. Field Mapping: TODO.md Task Spec → agile-backlog Item Fields

| TODO.md field | agile-backlog field | Notes |
|--------------|--------------------|----|
| `Goal:` | `goal` | Direct mapping |
| `Specialist:` | `tags: [specialist-name]` or new `specialist` field | See specialist integration below |
| `Complexity:` | `complexity` | Direct mapping (S/M/L) |
| `Depends on:` | `depends_on: [item-ids]` | Direct mapping |
| `DoD:` checkboxes | `acceptance_criteria: [...]` | Each checkbox → one AC string |
| `Technical Specs:` | `technical_specs: [...]` | Direct mapping |
| `Test Plan:` | `test_plan: [...]` | Direct mapping |
| `Demo Data Impact:` | Not applicable for all projects | Could add as optional field or use `notes` |
| `Status:` | `status` + `phase` | `doing` + `phase: build/review` |

### 4. Specialist Field

Add an optional `specialist` field to BacklogItem model:

```python
specialist: list[str] = Field(default_factory=list)  # e.g., ["python-pro"] or ["frontend-developer", "security-auditor"]
```

This maps directly to the template's `Specialist:` field in task specs and integrates with the specialist agent selection in sprint-execute.

### 5. Updated .claude/project.json

Extend the template's project config:

```json
{
  "project": {
    "name": "My Project",
    "slug": "my-project"
  },
  "tracker": {
    "type": "agile-backlog",
    "github_sync": false
  },
  "infra": { ... }
}
```

`tracker.type: "agile-backlog"` tells all skills to use agile-backlog CLI commands instead of KANBAN.md or GitHub Issues.

### 6. Updated sprint-config.md

The template includes a `.claude/sprint-config.yaml` that maps to the project's tooling:

```yaml
project_name: my-project
language: typescript  # or python, etc.

test_command: "npm run ci"
lint_command: "npm run lint"

backlog_tool: agile-backlog
backlog_commands:
  list: "agile-backlog list"
  show: "agile-backlog show {id}"
  add: "agile-backlog add \"{title}\" --category {category} --priority {priority}"
  move: "agile-backlog move {id} --status {status}"
  edit: "agile-backlog edit {id}"
  serve: "agile-backlog serve"

docs:
  handover_dir: "docs/sprints/"
  project_context: "docs/process/PROJECT_CONTEXT.md"
```

---

## Updated Template Workflows

### Sprint Start (before vs after)

**Before (KANBAN.md + TODO.md):**
1. Read KANBAN.md manually
2. Select items from Backlog text
3. Write task specs in TODO.md by hand
4. Move items in KANBAN.md (cut/paste text between sections)
5. Create sprint branch, commit

**After (agile-backlog):**
1. `agile-backlog list --status backlog` — view backlog
2. `agile-backlog serve` — or use Web UI for visual selection
3. Select items → `agile-backlog move {id} --status doing --phase plan`
4. `agile-backlog edit {id} --sprint N --goal "..." --acceptance-criteria "..." --technical-specs "..." --complexity M`
5. Sprint branch created by `/sprint-start` skill
6. Items automatically filtered by `agile-backlog list --status doing --sprint N`

### Sprint End (before vs after)

**Before:**
1. Manually verify DoD checkboxes in TODO.md
2. Edit KANBAN.md — move Doing items to Done section
3. Write SPRINT{N}_HANDOVER.md by hand
4. Update PROJECT_CONTEXT.md by hand
5. Merge branch

**After:**
1. `agile-backlog list --status doing --sprint N` — see what's still in progress
2. For each item: `agile-backlog show {id}` → verify AC against code (automated)
3. `agile-backlog move {id} --status done` — only after AC verified
4. SPRINT{N}_HANDOVER.md generated from `agile-backlog list --status done --sprint N` + git log
5. PROJECT_CONTEXT.md updated automatically
6. PR + merge

### Sprint Execution (before vs after) — THE BIG ADDITION

**Before (template):**
No automation. The developer manually:
1. Reads TODO.md task spec
2. Implements code
3. Writes tests
4. Checks off DoD checkboxes by hand in TODO.md
5. Commits with task reference

There is no brainstorming, no spec review, no automated plan writing, no subagent dispatch, no two-stage review. The entire sprint is manual.

**After (with /sprint-execute):**
1. `/sprint-execute` reads all doing items from agile-backlog
2. For each item:
   a. Check if design spec exists — if not, invoke `superpowers:brainstorming` to create one
   b. Review spec for completeness
   c. Write implementation plan via `superpowers:writing-plans`
   d. User approves plan (checkpoint)
   e. Dispatch subagents via `superpowers:subagent-driven-development`:
      - Select specialist from `.claude/agents/` based on task domain
      - Prepend specialist prompt to implementer prompt
      - Subagent implements with TDD (`superpowers:test-driven-development`)
      - Spec compliance review (superpowers reviewer — independent of specialist)
      - Code quality review (superpowers reviewer — independent of specialist)
   f. Run CI after each task
   g. Mark item `phase: review` when all AC implemented
3. Report status: "N/M tasks complete, tests passing, ready for /sprint-end"

**What this means for template users:**
- They can say `/sprint-execute` and the entire sprint is built autonomously
- Specialist agents provide domain expertise (python-pro, frontend-developer, security-auditor)
- Two-stage review catches bugs before they accumulate
- TDD ensures every feature has tests
- The user reviews at the plan checkpoint and again at sprint-end (DoD verification)

### Bug Reporting (before vs after)

**Before:**
- GitHub mode: `gh issue create --label bug`
- File mode: Append `- [BUG] description` to KANBAN.md

**After:**
- `agile-backlog add "bug title" --category bug --priority P1 --sprint N --description "steps to reproduce..."`
- Optional: `github_sync: true` → also creates GitHub Issue with link to agile-backlog item
- Bug has structured fields: title, priority, category, description, sprint, AC, comments

---

## Migration Tool

For existing template users with data in KANBAN.md and TODO.md, provide a migration path:

### `agile-backlog import-kanban`

Parse KANBAN.md and create YAML items:

```bash
agile-backlog import-kanban docs/process/KANBAN.md
```

**Parser logic:**
1. Read KANBAN.md, identify sections (Backlog, Doing, Done, Tech Debt, Candidate)
2. For each item line: `- [area] description (S/M/L)` (note: actual format omits `complexity:` prefix)
   - Extract: area (→ tags + category), description (→ title), complexity from bare letter in parens
   - Done section has different format: `- [Sprint N] T{N}.{X} — description` — extract sprint number and title
   - Set status based on section (Backlog → backlog, Doing → doing, Done → done)
   - Set sprint_target from section header (e.g., `## Sprint 14 — Candidate` → `sprint_target: 14`)
   - Support `--sprint N` flag to specify current sprint for relative parsing
   - Tech Debt items: `category: chore`, `tags: [tech-debt, area]`
3. Create YAML files in `backlog/`
4. Report: "Imported N items from KANBAN.md"

### `agile-backlog import-todo`

Parse TODO.md and enrich existing items with task spec fields:

```bash
agile-backlog import-todo TODO.md
```

**Parser logic:**
1. Read TODO.md, identify task blocks (`## T{N}.{X} — Title`)
2. For each task: extract Goal, Specialist, Complexity, Depends on, DoD, Technical Specs, Test Plan
3. Match to existing agile-backlog item by title similarity or create new item
4. Populate: goal, acceptance_criteria, technical_specs, test_plan, complexity, depends_on, specialist
5. Report: "Enriched N items from TODO.md"

### Dry-run support

Both commands support `--dry-run` to preview changes without writing files.

---

## Template Files to Update

| File | Change |
|------|--------|
| `CLAUDE.md` | Add agile-backlog commands section. Update "Bug Tracking" to reference agile-backlog. Add `backlog/` to project structure. |
| `docs/process/BOOTSTRAP.md` | Thorough rewrite — replace all TODO.md/KANBAN.md references with agile-backlog commands. Affects: On-Demand Context table, Session Start sections, Session Recovery, Quick Reference blocks. |
| `docs/process/AGENTIC_AGILE_MANIFEST.md` | Update context table: TODO.md → `agile-backlog list --doing`, KANBAN.md → `agile-backlog list --backlog`. Update workflow diagram. |
| `TASK_TEMPLATE.md` | Add section showing agile-backlog CLI equivalent for each field. Keep markdown template for reference. |
| `SPRINT_START_CHECKLIST.md` | Replace "Edit KANBAN.md" steps with `agile-backlog move/edit` commands. Replace "Write TODO.md" with `agile-backlog edit --goal --acceptance-criteria`. |
| `SPRINT_END_CHECKLIST.md` | Replace "Update KANBAN.md" with `agile-backlog move --status done`. Replace "Check TODO.md DoD" with `agile-backlog show {id}` + AC verification. |
| `SQUAD_PLANNING.md` | Add note: specialist field in agile-backlog maps to squad assignment. |
| `.claude/project.json` | Change `tracker.type` default from `"github"` to `"agile-backlog"`. Update all conditional logic in template docs that branches on tracker type (currently handles `"github"` / `"none"` — add `"agile-backlog"` as third option). |
| `.claude/sprint-config.yaml` | **CREATE** — new file with project-specific commands for sprint skills (test, lint, backlog tool, doc paths). Required by framework integration spec Phase 1. |
| `.gitignore` | Add `.agile-backlog.pid`, `.agile-backlog.yaml` |
| `package.json` or setup docs | Add `pip install agile-backlog` to setup instructions |
| `bin/init-project.sh` | Add `pip install agile-backlog` step. Create initial `backlog/` directory. Create `.claude/sprint-config.yaml` from template. |
| `landing/content/*.md` | Update parallel copies of process docs (AGENTIC_AGILE_MANIFEST.md, SPRINT_START_CHECKLIST.md, etc.) to match updated originals. The landing page build uses these copies. |

### Files to Remove (after migration)

| File | Replaced by |
|------|------------|
| `KANBAN.md` | `backlog/*.yaml` + agile-backlog CLI |
| `TODO.md` | agile-backlog item fields (goal, AC, tech specs) |
| `TODO-NEXT.md` | Items with `sprint_target: N+1` |

**Note:** Don't delete immediately — keep for reference during migration period. Add deprecation notice at top of each file pointing to agile-backlog commands.

---

## Web UI for Template Users

Template users get the full agile-backlog web UI:

```bash
agile-backlog serve
```

This gives them:
- **Board view** — Kanban columns (Backlog/Doing/Done) with unified card design
- **Backlog view** — Three-section planning (Backlog/vNext/vFuture) with filters, sort, side panel
- **Click-to-edit** — Inline editing of all fields (Linear-style)
- **Chat comments** — Human-agent async communication on items
- **Sprint filtering** — View items by sprint number

---

## Model Changes Required in agile-backlog

### New optional field: `specialist`

```python
# In models.py
specialist: str | None = None  # Agent name from .claude/agents/
```

Add to:
- BacklogItem model
- CLI `edit` command (`--specialist`)
- CLI `show` command (display if set)
- Web UI side panel (as clickable pill)
- schema.yaml

### New CLI commands

```bash
# Import from KANBAN.md format
agile-backlog import-kanban <path-to-kanban.md> [--dry-run]

# Import task specs from TODO.md format
agile-backlog import-todo <path-to-todo.md> [--dry-run]
```

---

## Implementation Priority

| Phase | What | Depends on |
|-------|------|-----------|
| 1 | Add `specialist` field to model + CLI + UI | Nothing |
| 2 | Build `import-kanban` command | Phase 1 |
| 3 | Build `import-todo` command | Phase 1 |
| 4 | Update template process docs (CLAUDE.md, BOOTSTRAP.md, checklists) | Phase 1 |
| 5 | Update template skills (sprint-start, sprint-end) to use sprint-config.md | Phase 4 + framework integration spec |
| 6 | Test: create new project from template, use agile-backlog end-to-end | Phase 5 |
| 7 | Test: migrate existing template project (import KANBAN.md + TODO.md) | Phase 2-3 |

---

## Success Criteria

1. New project from template uses agile-backlog out of the box (no KANBAN.md/TODO.md)
2. Existing template project can migrate with `import-kanban` + `import-todo`
3. All sprint skills work via sprint-config.md (no hardcoded tool references)
4. Specialist field flows from task spec → sprint-execute → subagent prompt
5. Web UI works for template projects (board + backlog planning)
6. Template process docs reference agile-backlog commands, not markdown editing
