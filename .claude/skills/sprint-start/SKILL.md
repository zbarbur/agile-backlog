---
name: sprint-start
description: Initialize a new sprint. Uses agile-backlog CLI to select scope, write task specs to YAML items, tag with sprint number, and create sprint branch.
---

# Sprint Start Skill

You are initializing a new sprint for agile-backlog. The user invoked `/sprint-start $ARGUMENTS`.

If an argument is provided, use it as the sprint number. Otherwise, determine the next sprint number from the latest handover in `docs/sprints/` or from MEMORY.md.

## Step 1: Verify Clean Slate

```bash
git branch --show-current    # should be: main
git status                   # should be: clean working tree
```

- [ ] On `main` branch
- [ ] Working tree clean
- [ ] Previous sprint items are done (`agile-backlog list --status doing` should be empty)

Run `ruff check . && ruff format --check . && pytest tests/ -v` and report pass/fail.

## Step 2: Bug Triage

Check for open bugs via GitHub issues or backlog items with category "bug":

```bash
agile-backlog list --category bug --status backlog
```

If bugs exist, ask which to include in sprint scope.

## Step 3: Select Sprint Scope

Show the backlog:

```bash
agile-backlog list --status backlog
```

Also offer the board for visual selection: `agile-backlog serve`

Ask the user:
- Which items to pull into this sprint?
- What is the sprint theme?

The user may also move items to "doing" via the board UI directly.

## Step 4: Write Task Specs to YAML

For each selected item, use `agile-backlog edit` to populate the task definition:

```bash
agile-backlog edit <item-id> \
  --sprint N \
  --goal "One sentence — what this delivers" \
  --complexity M \
  --acceptance-criteria "Verifiable criterion 1" \
  --acceptance-criteria "Verifiable criterion 2" \
  --acceptance-criteria "Tests pass (pytest tests/ -v)" \
  --acceptance-criteria "Lint clean (ruff check .)" \
  --technical-specs "File: src/path.py — what to change" \
  --technical-specs "File: tests/test_path.py — what to test" \
  --test-plan "tests/test_x.py: test description" \
  --phase plan
```

Present each task spec to the user for review. Adjust as needed.

**Move items to doing with phase:**

```bash
agile-backlog move <item-id> --status doing --phase plan
```

## Step 5: Validate Completeness

For each sprint item, verify via `agile-backlog show <item-id>`:
- Has goal
- Has complexity (S/M/L)
- Has at least 2 acceptance criteria
- Has at least 2 technical specs
- Has test plan
- Has sprint_target set to current sprint
- Phase is set

Report any gaps and suggest fixes.

## Step 6: Create Sprint Branch

```bash
git add backlog/
git commit -m "chore: start Sprint N — <theme>"
git checkout -b sprintN/main
git push -u origin sprintN/main
```

## Step 7: Confirm Ready

Present a summary:
- Sprint number and theme
- Number of tasks with complexity breakdown
- Sprint branch name
- CI status

## Important Rules

- YAML items are the single source of truth — do NOT write to TODO.md
- Use `agile-backlog edit` to populate task specs, not manual file editing
- Always set sprint_target and phase when moving items to doing
- Always tag items with the sprint number
- DoD items must be independently verifiable
