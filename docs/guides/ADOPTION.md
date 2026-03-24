# Adopting agile-backlog in an Existing Project

Instructions for a Claude Code agent to set up agile-backlog in a project that already has task tracking (KANBAN.md, TODO.md, or similar).

This is a one-time migration runbook. Follow each section in order.

---

## 1. Install agile-backlog

```bash
pip install agile-backlog
# or if using uv:
uv pip install agile-backlog
```

Verify:

```bash
agile-backlog --help
agile-backlog list          # should print "No items found."
```

This creates a `backlog/` directory in the project root for YAML item files.

---

## 2. Import Existing Tasks

Read the project's existing task file (KANBAN.md, TODO.md, etc.) and create YAML items using the CLI.

### Mapping Heuristics

When reading a markdown-based task list, apply these rules:

| Markdown signal | YAML field | Rule |
|---|---|---|
| `## Backlog` / `## Doing` / `## Done` section | `status` | Direct map: backlog, doing, done |
| `### Section Header` (e.g., "Security") | consider for `tags` | Map to closest tag (see taxonomy below) |
| **Bold text** before `—` or `:` | `title` | First bold phrase is the title |
| Text after the `—` or `:` | `description` | Rest of the line is description |
| ~~Strikethrough items~~ | `status: done` | Or skip entirely (see flag below) |
| "→ Sprint N" cross-references | skip | These reference completed work, not active items |

### Defaults for Imported Items

- `priority`: **P2** (safe middle ground — adjust during sprint planning)
- `category`: **feature** unless description mentions "bug"/"fix"/"broken" → `bug`, or "docs"/"documentation" → `docs`, or "debt"/"cleanup"/"ci"/"infra" → `chore`
- `complexity`, `acceptance_criteria`, `technical_specs`, `test_plan`: leave empty — sprint planning fills these
- `sprint_target`: unset

### Tag Taxonomy

When mapping section headers or keywords to tags, use:

| Tag | Matches |
|---|---|
| `ui` | web UI, frontend, board, cards, dialogs, CSS |
| `cli` | CLI commands, arguments, terminal |
| `skills` | sprint skills, slash commands, automation |
| `plugin` | plugin packaging, MCP, distribution |
| `packaging` | PyPI, CI/CD, dependencies |
| `data` | schema, import/export, archiving, migration |
| `planning` | sprint planning, backlog management, validation |
| `comments` | comments, notes, async communication |

### Import Flow

1. **Read** the source file completely
2. **Extract** items using the heuristics above
3. **Present a preview table** to the user:
   ```
   Found 28 items (19 backlog, 7 doing, 2 done — done skipped)

     # | Title                               | Status  | Pri | Category | Tags
   ----+-------------------------------------+---------+-----+----------+-------
     1 | Implement API authentication        | backlog | P2  | feature  | security
     2 | Fix silent rollback failures        | backlog | P2  | bug      | data
     ...
   ```
4. **Wait for user confirmation** — they may adjust priorities, drop items, or change categories
5. **Create items** using the CLI:
   ```bash
   agile-backlog add "Item title" --category feature --priority P2 --description "Description text"
   ```
6. **Report** what was created

### Flags

- **Skip done items** by default. Only import backlog + doing unless the user asks for full history.
- **Skip strikethrough items** — they reference completed work.
- **Deduplicate** — if the source file has the same item in multiple places (e.g., in a roadmap section and a backlog section), import it once.

---

## 3. Set Up Sprint Methodology

### Create sprint-config.yaml

Create `.claude/sprint-config.yaml` with project-specific commands:

```yaml
project_name: <project-name>
language: <python|typescript|go|etc>

current_sprint: 1

# Commands — adapt to your project's toolchain
test_command: "<your test command>"
lint_command: "<your lint command>"
format_command: "<your format command>"
ci_command: "<your full CI command — lint + test>"

# Backlog tool
backlog_tool: agile-backlog
backlog_commands:
  list: "agile-backlog list"
  list_doing: "agile-backlog list --status doing"
  list_done: "agile-backlog list --status done"
  list_backlog: "agile-backlog list --status backlog"
  list_bugs: "agile-backlog list --category bug --status backlog"
  show: "agile-backlog show {id}"
  add: "agile-backlog add \"{title}\" --category {category} --priority {priority}"
  move: "agile-backlog move {id} --status {status}"
  edit: "agile-backlog edit {id}"
  flagged: "agile-backlog flagged"

# Documentation paths
docs:
  handover_dir: "docs/sprints/"
  specs_dir: "docs/superpowers/specs/"
  plans_dir: "docs/superpowers/plans/"
  project_context: "docs/process/PROJECT_CONTEXT.md"
  definition_of_done: "docs/process/DEFINITION_OF_DONE.md"

# Branch conventions
branch_pattern: "sprint{N}/main"
commit_style: conventional

# Sprint settings
default_sprint_capacity:
  small: 3-4
  medium: 2-3
  large: 1-2
```

Adjust `test_command`, `lint_command`, `ci_command` to match the project's actual toolchain. If the CLI is installed in a venv, prefix with `.venv/bin/`.

### Create Documentation Directories

```bash
mkdir -p docs/sprints docs/process
```

### Add CLAUDE.md Process Section

Add the following to the project's `CLAUDE.md` (create if it doesn't exist):

```markdown
## Commands

- **CI:** `<ci_command from sprint-config>`
- **Sprint config:** `.claude/sprint-config.yaml`

## Design Principles

- Research first, design second, code third
- Code review before every merge
- DRY, YAGNI, TDD

## Context

| File | Purpose |
|---|---|
| `.claude/sprint-config.yaml` | Commands, paths, sprint settings |
| `backlog/*.yaml` | Backlog items (single source of truth) |
```

---

## 4. Configure Statusline

Add a statusline hook to `.claude/settings.local.json` to show sprint status in the Claude Code terminal. Create or merge into the existing file:

```json
{
  "hooks": {
    "StatusLine": [
      {
        "type": "command",
        "command": "sprint=$(grep 'current_sprint:' .claude/sprint-config.yaml 2>/dev/null | awk '{print $2}'); doing=$(agile-backlog list --status doing 2>/dev/null | tail -n +3 | wc -l | tr -d ' '); echo \"Sprint $sprint | $doing doing\""
      }
    ]
  }
}
```

This shows `Sprint N | X doing` in the status bar.

---

## 5. Verify Setup

Run these checks to confirm everything is working:

```bash
# CLI works
agile-backlog list

# Sprint config is readable
grep current_sprint .claude/sprint-config.yaml

# CI passes
<ci_command>

# Items imported (if migration was done)
agile-backlog list --status backlog
```

---

## 6. Copy Sprint Skills (Manual — Temporary)

The sprint skills (`sprint-start`, `sprint-execute`, `sprint-end`, etc.) are not yet distributed with the pip package. For now, copy them manually from the agile-backlog repo:

```bash
# From the agile-backlog source repo
cp -r .claude/skills/sprint-start <target-project>/.claude/skills/
cp -r .claude/skills/sprint-execute <target-project>/.claude/skills/
cp -r .claude/skills/sprint-end <target-project>/.claude/skills/
cp -r .claude/skills/sprint-plan-next <target-project>/.claude/skills/
```

> **Known limitation:** Skills copied this way won't auto-update when agile-backlog is upgraded. A bundled Claude Code plugin is planned to solve this — once shipped, `pip install --upgrade agile-backlog` will update both the CLI/UI and the sprint skills together.

## 7. Updating

The CLI and web UI update via pip:

```bash
pip install --upgrade agile-backlog
```

This picks up new commands, UI features, bug fixes, and model changes. Your project-specific files (`sprint-config.yaml`, `backlog/*.yaml`, `CLAUDE.md`) are untouched by upgrades.

Sprint skills must be re-copied manually until plugin packaging is available.

---

## 8. Start Your First Sprint

With agile-backlog set up and items imported, you can now use the sprint workflow:

1. `/sprint-start` — select scope, write task specs, create sprint branch
2. `/sprint-execute` — implement tasks with TDD, CI gates, code review
3. `/sprint-end` — write handover doc, update context, close sprint

Each sprint item flows through phases: **plan → spec → build → review → done**.
