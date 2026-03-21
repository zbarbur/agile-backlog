---
name: backlog
description: Manage backlog items for the current project. Use when the user wants to view, add, move, or manage backlog items, sprint planning, or open the Kanban board.
---

You have access to the `agile-backlog` CLI tool for managing backlog items stored as YAML files in the `backlog/` directory.

## Quick Reference

| Action | Command |
|--------|---------|
| List all | `agile-backlog list` |
| Filter | `agile-backlog list --status doing --priority P1` |
| Add item | `agile-backlog add "title" --priority P2 --category feature` |
| Move item | `agile-backlog move <id> --status doing` |
| Show details | `agile-backlog show <id>` |
| Open board | `agile-backlog serve` |

## Item Schema

Items have: id, title, status (backlog/doing/done), priority (P1/P2/P3), category, sprint_target, description, acceptance_criteria, tags, depends_on, notes.

## When to Use

- User asks about backlog, tasks, or sprint items
- User wants to add, move, or view work items
- User mentions Kanban board or sprint planning
- You need to check what's in progress or what's planned
