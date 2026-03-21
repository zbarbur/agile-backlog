---
name: sprint-end
description: Close the current sprint. Reads status from YAML items, writes handover doc, updates PROJECT_CONTEXT.md and MEMORY.md, cleans up branches.
---

# Sprint End Skill

You are closing a sprint for agile-backlog. The user invoked `/sprint-end $ARGUMENTS`.

Determine the current sprint number from the branch name or by checking which sprint has doing items:

```bash
agile-backlog list --status doing
```

## Phase 1: Verify & Ship

1. Run `ruff check . && ruff format --check . && pytest tests/ -v` — report results
2. Check git status — warn about uncommitted changes

## Phase 2: Update Tracking

### Check Item Status

List all items for the current sprint:

```bash
agile-backlog list --status doing
agile-backlog list --status done
```

For each doing item, check its acceptance criteria by expanding details:

```bash
agile-backlog show <item-id>
```

Report: which items are complete (all acceptance criteria met), which are still in progress.

For incomplete items, ask: move to done (if actually complete) or defer to next sprint (move back to backlog)?

### Move Completed Items

```bash
agile-backlog move <item-id> --status done
```

### Move Deferred Items

```bash
agile-backlog move <item-id> --status backlog
agile-backlog edit <item-id> --sprint 0  # clear sprint target
```

## Phase 2b: Issue Reconciliation

Check for GitHub issues referenced in sprint commits:

```bash
git log --oneline --grep="Fixes #" --grep="closes #"
```

If issues found, check their status and offer to close them.

## Phase 3: Knowledge Transfer

### Sprint Handover

Create `docs/sprints/SPRINT{N}_HANDOVER.md` with:

Gather information by:
- Running `agile-backlog list --status done` filtered by sprint
- Running `git log --oneline` for commit history
- Reading recent changes

Generate the handover with:
- Sprint Theme
- Completed tasks (from YAML items — goal, complexity, key files)
- Deferred items (if any, with reasons)
- Key Decisions (ask the user)
- Architecture Changes
- Known Issues (ask the user)
- Lessons Learned (ask the user)
- Test Coverage (pytest count)
- Recommendations for Next Sprint

### PROJECT_CONTEXT.md

Update `docs/process/PROJECT_CONTEXT.md`:
- Status → "Sprint {N+1} Planning"
- Last Sync → today's date
- Test count → from pytest output
- Sprint History table → add current sprint

### MEMORY.md

Update `.claude/MEMORY.md`:
- Update sprint status
- Add lessons learned
- Add new patterns or conventions

## Phase 4: Clean Slate

### Merge and Cleanup

```bash
# Create PR and merge
gh pr create --title "Sprint N: <theme>" --body "..."
gh pr merge --merge --delete-branch

# Switch to main
git checkout main && git pull
```

### Final Verification

```bash
git branch --show-current  # main
git status                 # clean
agile-backlog list --status doing  # should be empty
pytest tests/ -v  # all green
```

### Next Sprint

Check backlog for next sprint candidates:

```bash
agile-backlog list --status backlog
```

Report: "Sprint {N} is closed. Ready for Sprint {N+1} planning — run `/sprint-start`."

## Important Rules

- YAML items are the single source of truth — read from `agile-backlog show/list`, not TODO.md
- NEVER trust docs over code — verify completion by checking the codebase
- ALWAYS ask the user for lessons learned and known issues
- Write the handover doc even if the sprint was small
