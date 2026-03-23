# Agentic Agile Framework Integration — Design Spec

**Date:** 2026-03-23
**Status:** Draft
**Context:** Analysis of `zbarbur/agentic-agile-template` (12 sprints of engineering knowledge) + `zbarbur/agile-backlog` (Sprint 15, backlog tooling) + `VoltAgent/awesome-claude-code-subagents` (133 specialist agents)

## Goal

Create a portable agentic development framework that combines:
- Generic sprint process skills (from template, made tool-agnostic)
- Structured backlog management (from agile-backlog)
- Specialist agent selection (from VoltAgent)
- Development workflow automation (from superpowers plugin)

Any project can adopt this by installing the skills + writing one `sprint-config.yaml`.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER / ORCHESTRATOR               │
├─────────────────────────────────────────────────────┤
│              AGILE PROCESS SKILLS                   │
│  /sprint-start  /sprint-execute  /sprint-end        │
│  /plan  /report-bug  /fix-bug  /document            │
│  /sprint-plan-next  /review  /test                  │
├──────────────┬──────────────┬───────────────────────┤
│  sprint-     │  SUPERPOWERS │  SPECIALIST           │
│  config.md   │  PLUGIN      │  AGENTS               │
│  (project    │  (workflow)  │  (domain expertise)   │
│  specific)   │              │                       │
│              │  brainstorm  │  python-pro           │
│  test_cmd    │  write-plans │  ui-designer          │
│  lint_cmd    │  subagent-dd │  security-auditor     │
│  backlog_tool│  TDD         │  code-reviewer        │
│  doc_paths   │  code-review │  ...                  │
├──────────────┴──────────────┴───────────────────────┤
│              BACKLOG TOOLING                        │
│  agile-backlog CLI + YAML items + Web UI            │
│  (or GitHub Issues, or KANBAN.md — via config)      │
└─────────────────────────────────────────────────────┘
```

---

## Workstream 1: Generic Sprint Skills + sprint-config.yaml

### The Config File

`.claude/sprint-config.yaml` — one file per project, read by all sprint skills:

```yaml
# Project Sprint Configuration

project_name: agile-backlog
language: python
python_version: "3.11+"

# Commands
test_command: ".venv/bin/pytest tests/ -v"
lint_command: ".venv/bin/ruff check . && .venv/bin/ruff format --check ."
format_command: ".venv/bin/ruff format ."
ci_command: ".venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v"

# Backlog tool
backlog_tool: agile-backlog           # "agile-backlog" | "kanban-md" (agile-backlog is recommended)
github_sync: false                    # optional: sync bugs/items to GitHub Issues for visibility
backlog_commands:
  list: ".venv/bin/agile-backlog list"
  list_doing: ".venv/bin/agile-backlog list --status doing"
  list_done: ".venv/bin/agile-backlog list --status done"
  list_backlog: ".venv/bin/agile-backlog list --status backlog"
  list_bugs: ".venv/bin/agile-backlog list --category bug --status backlog"
  show: ".venv/bin/agile-backlog show {id}"
  add: ".venv/bin/agile-backlog add \"{title}\" --category {category} --priority {priority}"
  move: ".venv/bin/agile-backlog move {id} --status {status}"
  edit: ".venv/bin/agile-backlog edit {id}"
  flagged: ".venv/bin/agile-backlog flagged"

# Documentation paths
docs:
  handover_dir: "docs/sprints/"
  specs_dir: "docs/superpowers/specs/"
  plans_dir: "docs/superpowers/plans/"
  project_context: "docs/process/PROJECT_CONTEXT.md"
  definition_of_done: "docs/process/DEFINITION_OF_DONE.md"

# Branch conventions
branch_pattern: "sprint{N}/main"
commit_style: "conventional"  # conventional | freeform

# Sprint settings
default_sprint_capacity:
  small: 3-4
  medium: 2-3
  large: 1-2

# Specialist defaults (optional — maps task categories to specialists)
specialist_defaults:
  ui: frontend-developer
  backend: python-pro
  security: security-auditor
  refactor: refactoring-specialist
  test: test-automator
  docs: documentation-engineer
  design: ui-designer
  cli: cli-developer
  review: code-reviewer
  debug: debugger
```

### Skills to Create/Refactor

#### /sprint-start (refactor existing)

**Process (generic):**
1. Verify clean slate (main branch, clean tree, CI passing)
2. Review previous sprint handover
3. Bug triage — list open bugs, ask which to include
4. Select scope from backlog — show items, ask user to select
5. Write task specs — for each item, populate goal, AC, complexity, tech specs, test plan
6. Validate completeness — every item has goal, AC, complexity, sprint tag
7. Create sprint branch
8. Confirm ready

**Project-specific (from sprint-config.yaml):**
- CI command to verify clean slate
- Backlog commands to list/edit/move items
- Branch naming pattern
- DoD reference path

#### /sprint-execute (NEW)

**Process (generic):**
1. Read all sprint items (from backlog tool)
2. For each item with status=doing:
   a. Check if spec exists (in specs_dir) — if not, invoke brainstorming
   b. Review spec for completeness
   c. Write implementation plan (invoke writing-plans)
   d. Execute plan (invoke subagent-driven-development)
      - Select specialist based on task domain (from specialist_defaults or auto-detect)
      - Prepend specialist prompt to implementer prompt
      - Dispatch subagent with specialist context + task spec
      - Two-stage review (spec compliance + code quality)
   e. Run CI after each task
   f. Mark item phase as "review" when all AC implemented
3. Report status: "N/M tasks complete, tests passing"

**Key rules:**
- Only sprint-end moves items to "done" (sprint-execute marks as "review")
- Any bugs found during execution are tagged with current sprint
- If a task is blocked, report and move to next task
- Specialist selection is optional — auto-detect from file types and task description if not specified

#### /sprint-end (refactor existing)

**Process (generic):**
1. Verify CI passing
2. For each item in doing/review status:
   a. Read acceptance criteria
   b. Verify each AC against actual codebase (dispatch verification subagent)
   c. Report ✅/❌ per criterion
   d. If all AC pass → move to done
   e. If AC fail → report gaps, ask user: fix or defer?
3. Tag all done items with sprint number
4. Write handover doc
5. Update PROJECT_CONTEXT.md
6. Update MEMORY.md — ask user for lessons learned
7. Create PR, request review, merge
8. Clean up branch
9. Report: "Sprint N closed. Ready for Sprint N+1."

**Key rules:**
- ONLY this skill moves items to "done"
- DoD verification is automated, not trust-based
- Deferred items move back to backlog with cleared sprint_target

---

## Workstream 2: Process Docs from Template

### Adopt as-is (adapt language)

| Template Doc | Adopt to | Changes needed |
|-------------|----------|----------------|
| `DEFINITION_OF_DONE.md` | `docs/process/DEFINITION_OF_DONE.md` | Replace `npm test/lint` with generic `{test_command}/{lint_command}`. Add Python examples alongside TypeScript ones. |
| `AGENTIC_AGILE_MANIFEST.md` | `docs/process/AGENTIC_AGILE_MANIFEST.md` | Update context table to reference agile-backlog instead of KANBAN.md/TODO.md. Update quality gates to be generic. Keep philosophy unchanged. |
| `TASK_TEMPLATE.md` | `docs/process/TASK_TEMPLATE.md` | Update to reference agile-backlog fields (goal, AC, tech specs, test plan, complexity) instead of TODO.md format. Keep the good/bad examples. |

### Adopt as skills (adapted to sprint-config.yaml)

#### /plan (from template — 4 modes)

| Mode | What it does | Adaptation needed |
|------|-------------|-------------------|
| `/plan project` | Project inception → Project Charter | Minimal — generic already |
| `/plan roadmap` | Strategic review every 3-5 sprints | Read from agile-backlog instead of KANBAN.md |
| `/plan sprint` | Sprint allocation balance (features/debt/security %) | Read from agile-backlog categories |
| `/plan scope [feature]` | Scope analysis before committing to build | Minimal — generic already |

#### /document (from template — 7 modes)

| Mode | What it does | Adaptation needed |
|------|-------------|-------------------|
| `/document research [topic]` | Options analysis doc | Minimal — generic already |
| `/document design [feature]` | Design doc before implementation | Already covered by superpowers:brainstorming — evaluate overlap |
| `/document architecture` | Generate system overview from code | Adapt file scanning for Python |
| `/document audit` | Staleness audit of all docs | Minimal — generic already |
| `/document runbook [op]` | Operational runbook | Minimal — generic already |
| `/document update [file]` | Refresh doc against code | Minimal — generic already |
| `/document review [file]` | Review doc for completeness | Minimal — generic already |

**Note:** `/document design` overlaps with `superpowers:brainstorming`. Decision: use brainstorming for interactive design sessions, `/document design` for writing the formal design doc after decisions are made.

#### /report-bug (from template)

**Process:** Gather details (title, severity, steps to reproduce, expected vs actual, environment) → create structured report.

**Adaptation:** Bugs are always created in agile-backlog (single source of truth):
- `agile-backlog add "title" --category bug --priority {severity_to_priority} --description "..." --sprint N`
- Optional: sync to GitHub Issues for external visibility (`gh issue create` with link back to agile-backlog item ID)

GitHub Issues is NOT a parallel tracking system — it's an optional notification/visibility layer. The agile-backlog item is the source of truth for status, AC, comments, and sprint assignment.

**Enhancement over template:** Auto-tag with current sprint number. Auto-explore codebase for related code. Structured bug fields in YAML (steps to reproduce, expected/actual) instead of free-text markdown.

#### /sprint-plan-next (from template)

**Process:** While current sprint runs, pre-plan next sprint scope. Write candidates to backlog with vNext sprint_target.

**Adaptation:** Use `agile-backlog edit {id} --sprint {N+1}` instead of writing to KANBAN.md candidate section.

**Integration:** This is what the user does in a separate Claude session while the main session runs sprint-execute.

#### /review (from template — enhanced)

**Process:** Review code changes against project standards. 8 categories: coding standards, error handling, security, API design, data integrity, testing, deployment, code health.

**Adaptation:** Replace Node.js-specific checks with Python/project-specific checks from CLAUDE.md. Keep the severity-based report format (Critical/Warning/Suggestion/Positive).

**Integration:** Used by sprint-execute during the code quality review stage. Also available standalone.

#### /test (from template — adapted)

**Process:** 7 modes: run all, run specific, find related, coverage analysis, generate tests.

**Adaptation:** Replace `npm test` / `node --test` with pytest. Replace TypeScript test generation with Python test generation. Keep the failure diagnosis patterns.

#### /fix-bug (from template)

**Process:** Load bug details → investigate root cause → present analysis → implement after approval → commit with reference.

**Adaptation:** Read bugs from agile-backlog instead of GitHub issues. Use `agile-backlog show {id}` to load details.

---

## Workstream 3: Specialist Agent Integration

### Source

[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) — 133 agents in 10 categories.

### Installation

Use `bin/agents.sh import {name}` from the template to install agents into `.claude/agents/`. Each agent is a markdown file with:
- Expertise summary
- Responsibilities
- Available tools
- Key principles
- When to assign

### Relevant Agents for This Project

| Category | Agent | Why |
|----------|-------|-----|
| Core Development | `python-pro` | Primary language |
| Core Development | `frontend-developer` | NiceGUI UI work |
| Core Development | `cli-developer` | Click CLI improvements |
| Core Development | `fullstack-developer` | Cross-cutting tasks |
| Quality & Security | `code-reviewer` | PR reviews, quality gates |
| Quality & Security | `security-auditor` | Security reviews (caught XSS) |
| Quality & Security | `test-automator` | Test generation, coverage |
| Quality & Security | `debugger` | Bug investigation |
| Specialized | `ui-designer` | Design decisions |
| Specialized | `ux-researcher` | User experience |
| Specialized | `refactoring-specialist` | Code restructuring |
| Specialized | `documentation-engineer` | Process docs |
| Meta | `scrum-master` | Sprint process |
| Meta | `workflow-orchestrator` | Sprint execution |

### How Specialists Integrate with Sprint-Execute

**Key principle:** Specialists enhance implementation only. Reviews use superpowers' own agents (independent reviewer is better than same-domain reviewer).

**No conflict with superpowers:** Superpowers dispatches agents by type (`general-purpose`, `superpowers:code-reviewer`, etc.). Our specialists are prompt content, not agent types. They compose cleanly:

| Stage | Agent type (superpowers) | Specialist prompt (ours) | Result |
|-------|-------------------------|-------------------------|--------|
| Implementation | `general-purpose` | Prepended (e.g., python-pro) | Subagent has domain expertise + task context |
| Spec review | `general-purpose` | None | Clean spec compliance check |
| Code review | `superpowers:code-reviewer` | None — but task context mentions specialist | Reviewer knows what domain patterns to verify |

```
sprint-execute receives task:
  1. Determine specialist from:
     - Explicit "specialist" field in task spec (if set)
     - Category mapping from specialist_defaults in sprint-config.yaml
     - Auto-detect from task description keywords
     - Default to project's primary language specialist

  2. Load specialist prompt:
     - Read .claude/agents/{specialist}.md

  3. IMPLEMENTATION stage — specialist IS used:
     - Construct prompt = specialist prompt + implementer prompt
     - Dispatch via superpowers as `general-purpose` agent
     - Subagent has: domain expertise + task spec + project context

  4. SPEC REVIEW stage — specialist NOT used:
     - Superpowers dispatches its own spec reviewer
     - Task context includes: "Implemented by {specialist} — verify domain patterns"

  5. CODE REVIEW stage — specialist NOT used:
     - Superpowers dispatches `superpowers:code-reviewer`
     - Task context includes: "Implemented by {specialist} — check {domain-specific concerns}"
     - For security-sensitive tasks, add to review context: "Pay extra attention to XSS, input validation, auth patterns"
```

**Why reviews don't use specialists:** An independent reviewer catches assumptions that a same-domain specialist would share. The `python-pro` might implement something that looks correct to another Python expert but has an architectural flaw that a general reviewer catches. Separation of concerns between builder and reviewer.

### Specialist Selection Logic

```python
# Pseudocode for auto-selecting specialist

def select_specialist(task, config):
    # 1. Explicit assignment
    if task.specialist:
        return task.specialist

    # 2. Category-based mapping from config
    if task.category in config.specialist_defaults:
        return config.specialist_defaults[task.category]

    # 3. File-type inference
    file_types = detect_file_types(task.technical_specs)
    if ".py" in file_types:
        return "python-pro"
    if ".html" in file_types or ".css" in file_types:
        return "frontend-developer"
    if ".yaml" in file_types or ".yml" in file_types:
        return "devops-engineer"

    # 4. Keyword inference
    if any(kw in task.goal.lower() for kw in ["security", "xss", "auth", "vulnerability"]):
        return "security-auditor"
    if any(kw in task.goal.lower() for kw in ["test", "coverage", "fixture"]):
        return "test-automator"
    if any(kw in task.goal.lower() for kw in ["refactor", "split", "extract", "restructure"]):
        return "refactoring-specialist"

    # 5. Default
    return "python-pro"  # or whatever the project's primary language specialist is
```

---

## Workstream 4: Export agile-backlog to Template

### What Changes in the Template

| Template Component | Current | After Integration |
|-------------------|---------|-------------------|
| Backlog storage | `KANBAN.md` (markdown) | `agile-backlog` YAML items + CLI + Web UI |
| Task specs | `TODO.md` (markdown) | agile-backlog item fields (goal, AC, tech specs) |
| Sprint filtering | Manual markdown sections | `agile-backlog list --sprint N` |
| Bug tracking | GitHub Issues or KANBAN.md | `agile-backlog add --category bug` (source of truth, optional GitHub sync) |
| Item status | Markdown sections (Backlog/Doing/Done) | `agile-backlog move --status doing/done` |
| Sprint planning view | None | agile-backlog Web UI (three sections, side panel) |
| DoD verification | Manual TODO.md checkboxes | `agile-backlog show {id}` → verify AC against code |

### Template Gets

- `agile-backlog` as a dependency (pip install)
- Sprint skills updated to use `agile-backlog` commands via sprint-config.yaml
- Web UI for visual sprint planning
- Structured data (queryable, filterable, sortable)
- Chat comments on items for async human-agent communication

### Template Keeps

- Process docs (DEFINITION_OF_DONE, MANIFEST, etc.)
- Specialist agents
- Non-sprint skills (/plan, /document, /deploy, /rollback)
- GitHub Actions CI workflows
- Module system (modules.json, enable/disable)

---

## Interaction Between Skills and Superpowers

| Agile Skill | Invokes Superpowers | When |
|-------------|-------------------|------|
| `/sprint-execute` | `brainstorming` | When a task needs a spec |
| `/sprint-execute` | `writing-plans` | To create implementation plan |
| `/sprint-execute` | `subagent-driven-development` | To dispatch task implementers |
| `/sprint-execute` | `test-driven-development` | Subagents follow TDD |
| `/sprint-execute` | `requesting-code-review` | After each task |
| `/sprint-end` | `verification-before-completion` | DoD verification |
| `/sprint-end` | `finishing-a-development-branch` | PR + merge |
| `/plan` | `brainstorming` | Scope analysis, design decisions |
| `/fix-bug` | `systematic-debugging` | Root cause investigation |

Superpowers is the **development methodology engine**. Agile skills are the **project management layer**. They compose, never duplicate.

---

## Implementation Priority

| Phase | What | Why first |
|-------|------|----------|
| Phase 1 | `sprint-config.yaml` + refactor sprint-start/sprint-end | Foundation — everything else builds on this |
| Phase 2 | `/sprint-execute` skill | The big missing piece — automated execution |
| Phase 3 | Process docs (DoD, Manifest, Task Template) | Quality guides |
| Phase 4 | Template skills (/plan, /document, /report-bug) | Extended capabilities |
| Phase 5 | Specialist agent integration | Enhanced subagent quality |
| Phase 6 | Export to template | Make it reusable across projects |

---

## Resolved Questions

1. **sprint-config.yaml format → YAML.** The file is machine-read by skills, not human-browsed. Pure YAML avoids parsing complexity.

2. **Specialist agents location → `.claude/agents/`** — follows Claude Code convention and template pattern.

## Open Questions

3. **How to handle multi-project setups?** If agile-backlog manages backlog for project X, and project X has its own sprint-config.yaml, how do they reference each other?

4. **Should /sprint-execute be fully autonomous or checkpoint with user?** Today we ran subagent-driven-development with review between tasks but no user interaction. **Recommendation:** default to checkpoint-after-plan (user approves the plan before subagent dispatch begins). User can skip with a flag. This matches the "research first, design second, code third" principle.

5. **VoltAgent agents — install all relevant ones or pick per sprint?** Installing 14 agents adds context. Could install on-demand via `bin/agents.sh import` when a task needs a specialist not yet installed.

6. **"review" status in sprint-execute.** The spec introduces a "review" phase between "doing" and "done" that sprint-execute sets. The current agile-backlog model uses `phase: plan|spec|build|review` (not status). Sprint-execute should set `phase: review` (not a new status), which is already supported. No model change needed.

7. **Error handling in sprint-execute.** When a subagent fails mid-task: (a) tests don't pass → retry once with error context, then mark as blocked; (b) subagent produces no output → escalate to more capable model; (c) task is too large → break into subtasks. After 2 failures on same task, pause and report to user.

8. **`/document design` vs `superpowers:brainstorming`.** Brainstorming is for interactive design sessions (user-driven, exploratory). `/document design` is for writing the formal design doc after decisions are made. `/document design` is a standalone skill, NOT part of the sprint-execute pipeline. Sprint-execute uses brainstorming → writing-plans.

9. **Specialist file-type mappings.** File-type → specialist mappings should come from `specialist_defaults` in sprint-config.yaml, not hardcoded. The pseudocode in Workstream 3 is illustrative, not prescriptive.

10. **Template migration (Workstream 4).** Existing template users with data in KANBAN.md/TODO.md will need manual migration. The `agile-backlog migrate` CLI command pattern (with dry-run) could be extended to import from KANBAN.md format. Add as a Phase 6 subtask.
