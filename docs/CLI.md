# agile-backlog CLI Reference

Lightweight Kanban board tool for agentic development.

## Installation

```bash
# CLI only (lightweight, no NiceGUI)
pip install git+https://github.com/zbarbur/agile-backlog.git

# CLI + web UI
pip install "agile-backlog[ui] @ git+https://github.com/zbarbur/agile-backlog.git"

# From source (development)
git clone https://github.com/zbarbur/agile-backlog.git
cd agile-backlog
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

### Install Sprint Skills

After installing the package, deploy the bundled sprint skills into your project:

```bash
agile-backlog install-skills
```

This copies skills (`sprint-start`, `sprint-execute`, `sprint-end`, etc.) to `.claude/skills/`. Existing skills are not overwritten — use `--force` to update:

```bash
agile-backlog install-skills --force
```

## Quickstart

```bash
# Create your first backlog item
agile-backlog add "Build login page" --category feature --priority P1

# List all items
agile-backlog list

# Move an item to doing
agile-backlog move build-login-page --status doing --phase build

# View item details
agile-backlog show build-login-page

# Add a note
agile-backlog note build-login-page "Started work on auth flow"

# Start the web board
agile-backlog serve
```

## Data Format

Each backlog item is a YAML file in the `backlog/` directory. The file name is the item ID (slugified title). Items are the single source of truth — both CLI and web UI read/write the same files.

## Commands

### add

Create a new backlog item.

```
agile-backlog add TITLE [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--priority` | P0-P4 | P2 | Priority level |
| `--category` | bug/feature/docs/chore | *required* | Category |
| `--description` | text | "" | Item description |
| `--sprint` | integer | none | Target sprint number |

```bash
agile-backlog add "Fix auth leak" --category bug --priority P1
agile-backlog add "Write API docs" --category docs --sprint 18
```

### list

List backlog items with optional filters.

```
agile-backlog list [OPTIONS]
```

| Option | Type | Description |
|--------|------|-------------|
| `--status` | backlog/doing/done | Filter by status |
| `--priority` | P0-P4 | Filter by priority |
| `--category` | bug/feature/docs/chore | Filter by category |
| `--sprint` | integer | Filter by sprint target |
| `--tags` | text (repeatable) | Filter by tag (ANY match) |
| `--json` | flag | Output as JSON |

```bash
agile-backlog list --status doing
agile-backlog list --category bug --priority P1
agile-backlog list --sprint 18
agile-backlog list --tags ui --tags cli
agile-backlog list --json
```

### show

Show full details for a backlog item.

```
agile-backlog show ITEM_ID [OPTIONS]
```

| Option | Type | Description |
|--------|------|-------------|
| `--json` | flag | Output as JSON |

```bash
agile-backlog show fix-auth-leak
agile-backlog show fix-auth-leak --json
```

### move

Change an item's status.

```
agile-backlog move ITEM_ID [OPTIONS]
```

| Option | Type | Description |
|--------|------|-------------|
| `--status` | backlog/doing/done | *required* — target status |
| `--phase` | plan/spec/build/review | Workflow phase (auto-set to "plan" when moving to doing) |

```bash
agile-backlog move fix-auth-leak --status doing --phase build
agile-backlog move fix-auth-leak --status done
agile-backlog move fix-auth-leak --status backlog  # clears phase
```

### edit

Edit fields on a backlog item. Only specified fields are updated.

```
agile-backlog edit ITEM_ID [OPTIONS]
```

| Option | Type | Description |
|--------|------|-------------|
| `--title` | text | New title |
| `--priority` | P0-P4 | Priority level |
| `--category` | bug/feature/docs/chore | Category |
| `--description` | text | Description |
| `--sprint` | integer | Sprint target |
| `--goal` | text | One-sentence goal |
| `--complexity` | S/M/L | Size estimate |
| `--technical-specs` | text (repeatable) | Technical spec entries |
| `--acceptance-criteria` | text (repeatable) | Definition of done criteria |
| `--test-plan` | text (repeatable) | Test plan entries |
| `--phase` | plan/spec/build/review | Workflow phase |
| `--design-reviewed` | flag | Mark design as reviewed |
| `--code-reviewed` | flag | Mark code as reviewed |
| `--tags` | text (repeatable) | Tags |
| `--depends-on` | text (repeatable) | Dependency item IDs |
| `--notes` | text | Notes |
| `--resolve-notes` | flag | Resolve all flagged notes |

```bash
agile-backlog edit fix-auth-leak --goal "Prevent session token leakage" --complexity M
agile-backlog edit fix-auth-leak --acceptance-criteria "No tokens in logs" --acceptance-criteria "Tests pass"
agile-backlog edit fix-auth-leak --tags security --tags backend
agile-backlog edit fix-auth-leak --sprint 18 --phase spec
```

### note

Add a comment/note to a backlog item.

```
agile-backlog note ITEM_ID TEXT [OPTIONS]
```

| Option | Type | Description |
|--------|------|-------------|
| `--flag` | flag | Flag this note for agent attention |

```bash
agile-backlog note fix-auth-leak "Needs review from security team"
agile-backlog note fix-auth-leak "Please research this" --flag
```

### flagged

List items with unresolved flagged notes. This is the async communication channel between user and agent.

```
agile-backlog flagged [OPTIONS]
```

| Option | Type | Description |
|--------|------|-------------|
| `--json` | flag | Output as JSON |

```bash
agile-backlog flagged
agile-backlog flagged --json
```

### resolve-note

Resolve a specific note by its index (0-based).

```
agile-backlog resolve-note ITEM_ID NOTE_INDEX
```

```bash
agile-backlog resolve-note fix-auth-leak 0    # resolve first note
agile-backlog resolve-note fix-auth-leak 2    # resolve third note
```

### set-sprint

Set the current sprint number in the project config.

```
agile-backlog set-sprint NUMBER
```

```bash
agile-backlog set-sprint 18
```

### delete

Delete backlog items. Accepts multiple IDs. Asks for confirmation unless `--yes` is passed.

```
agile-backlog delete ID [ID...] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--yes` | Skip confirmation prompt |

```bash
agile-backlog delete old-item --yes
agile-backlog delete item-a item-b item-c --yes
```

### sprint-status

Show current sprint items grouped by phase with progress count.

```
agile-backlog sprint-status [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--sprint N` | Sprint number | Current sprint from config |

```bash
agile-backlog sprint-status
agile-backlog sprint-status --sprint 19
```

### validate

Check sprint items have required spec fields (goal, complexity, >=2 acceptance criteria, >=1 technical spec). Exit code 1 on failure.

```
agile-backlog validate [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--sprint N` | Sprint number | Current sprint from config |

```bash
agile-backlog validate
agile-backlog validate --sprint 20
```

### install-skills

Install bundled sprint skills into the current project's `.claude/skills/` directory.

```
agile-backlog install-skills [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--target DIR` | Target directory | `.claude/skills` |
| `--force` | Overwrite existing skills | No |

```bash
agile-backlog install-skills
agile-backlog install-skills --force
```

### serve

Start the web UI (NiceGUI Kanban board). Requires `agile-backlog[ui]` install.

```
agile-backlog serve [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | integer | 8501 | Port number |
| `--host` | text | 127.0.0.1 | Host address |
| `--no-reload` | flag | false | Disable hot reload |

```bash
agile-backlog serve
agile-backlog serve --port 9000
```

### stop

Stop a running agile-backlog server.

```bash
agile-backlog stop
```

### restart

Restart the agile-backlog server.

```
agile-backlog restart [OPTIONS]
```

Same options as `serve`.

### migrate

Migrate YAML files to the current schema (category values, agent_notes to comments).

```
agile-backlog migrate [OPTIONS]
```

| Option | Type | Description |
|--------|------|-------------|
| `--dry-run` | flag | Show changes without applying |

```bash
agile-backlog migrate --dry-run    # preview changes
agile-backlog migrate              # apply changes
```

## Workflow Phases

Items in "doing" status have a workflow phase:

| Phase | Description |
|-------|-------------|
| `plan` | Scoping and planning |
| `spec` | Spec written, ready for implementation |
| `build` | Implementation in progress |
| `review` | Code review and verification |

## Item Priorities

| Priority | Usage |
|----------|-------|
| P0 | Critical — blocks everything |
| P1 | High — current sprint must-have |
| P2 | Medium — default priority |
| P3 | Low — nice to have |
| P4 | Backlog — someday/maybe |

## Item Categories

| Category | Usage |
|----------|-------|
| `bug` | Defect or regression |
| `feature` | New functionality |
| `docs` | Documentation |
| `chore` | Maintenance, CI, tooling |
