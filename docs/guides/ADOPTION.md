# Adopting agile-backlog in an Existing Project

Instructions for a Claude Code agent to set up agile-backlog in a project that already has task tracking (KANBAN.md, TODO.md, or similar).

Two channels — pick one:

| | Pip-only | Plugin |
|---|---|---|
| 1 | `pip install agile-backlog` | `/plugin install agile-backlog` |
| 2 | `agile-backlog init` | `pip install agile-backlog` |
| 3 | import tasks (below) | `agile-backlog init --config-only`, then import tasks |

**Pip-only** installs skills and hooks into the project's `.claude/`. **Plugin** ships skills, slash commands (namespaced, e.g. `/agile-backlog:sprint-start`), and the context-logging hook via the plugin itself — `init --config-only` then only scaffolds `sprint-config.yaml`, doc dirs, and `.gitignore`.

---

## 1. Install and Initialize

```bash
pip install git+https://github.com/zbarbur/agile-backlog.git
# or: uv pip install git+https://github.com/zbarbur/agile-backlog.git

agile-backlog init            # pip-only path (add --config-only on the plugin path)
```

`init` detects your toolchain (pyproject.toml / package.json), prompts for test/lint/CI commands (accept defaults with `--yes`), then:

- writes `.claude/sprint-config.yaml` (skips if present; `--force` overwrites)
- creates `docs/sprints/`, `docs/process/`, `docs/superpowers/{specs,plans}/`
- adds `.claude/context-logs/` to `.gitignore`
- installs the 9 sprint skills into `.claude/skills/` (pip-only path)
- installs `.claude/hooks/post-tool-logger.sh` and wires it into `.claude/settings.local.json` `PostToolUse` (pip-only path)
- prints a suggested CLAUDE.md process section — paste it in yourself; init never edits CLAUDE.md

Verify:

```bash
agile-backlog list                          # "No items found."
grep current_sprint .claude/sprint-config.yaml
agile-backlog context-report                # after a few Claude Code tool calls
```

### Optional: statusline

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

## 3. Updating

The CLI and web UI update via pip:

```bash
pip install --upgrade agile-backlog
```

This picks up new commands, UI features, bug fixes, and model changes. Your project-specific files (`sprint-config.yaml`, `backlog/*.yaml`, `CLAUDE.md`) are untouched by upgrades.

After upgrading, update skills too:

```bash
agile-backlog install-skills --force
```

Plugin users: update via `/plugin` instead; `init --config-only` never needs re-running.

---

## 4. Start Your First Sprint

With agile-backlog set up and items imported, you can now use the sprint workflow:

1. `/sprint-start` — select scope, write task specs, create sprint branch
2. `/sprint-execute` — implement tasks with TDD, CI gates, code review
3. `/sprint-end` — write handover doc, update context, close sprint

Each sprint item flows through phases: **plan → spec → build → review → done**.
