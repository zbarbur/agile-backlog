---
name: backlog
description: Manage backlog items — list, add, move, show, or open the Kanban board
arguments:
  - name: action
    description: "Action to perform: list, add, move, show, serve (default: list)"
    required: false
  - name: args
    description: "Additional arguments for the action"
    required: false
---

You are managing backlog items for the current project using the `agile-backlog` CLI tool.

## Available Actions

Based on the user's request, run the appropriate CLI command:

### List items
```bash
agile-backlog list
agile-backlog list --status doing
agile-backlog list --priority P1
agile-backlog list --category bug
agile-backlog list --sprint 3
```

### Add item
```bash
agile-backlog add "Item title" --priority P2 --category feature
agile-backlog add "Item title" --priority P1 --category bug --sprint 3 --description "Details"
```

### Move item
```bash
agile-backlog move <item-id> --status doing
agile-backlog move <item-id> --status done
```

### Show item details
```bash
agile-backlog show <item-id>
```

### Open Kanban board
```bash
agile-backlog serve
```

## Instructions

1. If no action is specified, run `agile-backlog list` to show all items
2. Parse the user's request to determine which command to run
3. Run the command using Bash
4. Present the output clearly

## Notes

- Items are stored as YAML files in `backlog/` directory (git-tracked)
- IDs are slug-derived from titles (e.g., "Fix auth leak" → "fix-auth-leak")
- Priority levels: P1 (critical), P2 (important), P3 (nice-to-have)
- Status flow: backlog → doing → done
