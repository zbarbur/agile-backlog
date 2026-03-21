---
name: sprint-start
description: Initialize a new sprint. Walks through the sprint start checklist, selects scope from KANBAN, writes task specs, creates sprint branch.
---

# Sprint Start Skill

You are initializing a new sprint for BigQuery-connector. The user invoked `/sprint-start $ARGUMENTS`.

If an argument is provided, use it as the sprint number. Otherwise, determine the next sprint number from the latest handover in `docs/sprints/` or from MEMORY.md.

## Step 1: Verify Clean Slate

Run these checks and report results:

```bash
git branch --show-current    # should be: main
git status                   # should be: clean working tree
```

- [ ] On `main` branch — if not, warn and ask to switch
- [ ] Working tree clean — if not, warn about uncommitted changes
- [ ] Previous sprint TODO.md is cleared — read TODO.md, check if it has active tasks
- [ ] Previous sprint handover exists — check `docs/sprints/SPRINT{N-1}_HANDOVER.md`

Run `ruff check . && ruff format --check . && pytest tests/ -v` and report pass/fail. If it fails, diagnose before proceeding.

## Step 2: Bug Triage

Read `.claude/project.json` for tracker configuration.

### GitHub Mode (`tracker.type === "github"`)

Fetch open bugs sorted by severity and age:

```bash
gh issue list --repo "{tracker.repo}" --label "bug" --state open --json number,title,labels,createdAt --limit 50
```

Present a table:

| # | Title | Severity | Age | Labels |
|---|-------|----------|-----|--------|

### File-Based Mode (`tracker.type === "none"` or missing)

Read `docs/process/KANBAN.md` and extract any items tagged `[BUG]`.

### No Open Bugs

If no open bugs are found, report: "No open bugs — continuing to scope selection." and proceed.

### User Selection

Ask the user which bugs (if any) to include in the sprint scope. Selected bugs will become task specs in the Write Task Specs step with:
- **Goal:** Fix bug #{N} — {title}
- **Specialist:** based on bug category
- A DoD item: `Fixes #{N}` in commit message (GitHub mode)

## Step 3: Select Sprint Scope

### Check for Pre-Planned Scope

First, check if the next sprint was pre-planned during the previous sprint:

1. Read `docs/process/KANBAN.md` — look for a "Sprint {N} — Candidate" section with items
2. Check if `TODO-NEXT.md` exists — if so, it contains draft task specs

**If candidate items exist:**
- Present the candidate scope to the user: "Sprint {N} was pre-planned. Here's the candidate scope:"
- Show the items and ask: "Use this scope as-is, modify it, or start fresh from backlog?"
- If using pre-planned scope: skip to Step 4 (the items are already selected)
- If `TODO-NEXT.md` exists with task specs: offer to promote it directly to `TODO.md` after review

**If no candidate exists (normal flow):**

Read `docs/process/KANBAN.md` and present:
1. **Backlog items** — show the full list
2. **Tech debt items** — show the full list

Ask the user:
- Which items to pull into this sprint?
- What is the sprint theme (1-sentence summary)?

## Step 4: Write Task Specs

For each selected item, generate a task spec using the template from `docs/process/TASK_TEMPLATE.md`:

```markdown
## Task {N}.{X}: [Title]
**Goal:** [derived from KANBAN item]
**Specialist:** [suggest based on task domain]
**Complexity:** [Small|Medium|Large — estimate from scope]
**DoD:**
- [ ] [specific, verifiable criterion]
- [ ] [specific, verifiable criterion]
- [ ] Tests added in `tests/test_[file].py`, `pytest tests/ -v` passes
**Technical Specs:**
- [concrete implementation details]
**Test Plan:**
- Test file: `tests/test_[name].py`
- Expected test count: ~N
```

Present each task spec to the user for review and adjustment. Then write all specs to `TODO.md`.

## Step 5: Validate Completeness

Review all task specs and verify:
- Every task has at least 2 DoD checkboxes
- Every task has at least 2 technical spec bullets
- Specialist role is valid
- No circular dependencies
- Demo data impact is considered

Report any gaps and suggest fixes.

## Step 6: Update KANBAN.md

Move selected items from Backlog (or Candidate) to "Sprint {N} — Doing" section.
- Clear the "Sprint {N} — Candidate" section (it becomes the new Doing)
- Create a fresh empty "Sprint {N+1} — Candidate" section for next sprint's planning
- If `TODO-NEXT.md` was promoted to `TODO.md`, delete `TODO-NEXT.md`

## Step 7: Create Sprint Branch

```bash
git checkout -b sprint{N}/main
git push -u origin sprint{N}/main
```

## Step 8: Confirm Ready

Present a summary:
- Sprint number and theme
- Number of tasks with complexity breakdown
- Sprint branch name
- Confirm CI passes on sprint branch

## Important Rules

- ALWAYS use `docs/process/TASK_TEMPLATE.md` format for task specs
- NEVER put backlog items in TODO.md — only active sprint tasks
- ALWAYS ask the user to confirm scope before writing task specs
- DoD items must be independently verifiable — reject vague items like "works well"
