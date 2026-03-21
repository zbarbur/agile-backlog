---
name: sprint-end
description: Close the current sprint. Updates TODO.md, KANBAN.md, writes handover doc, updates PROJECT_CONTEXT.md and MEMORY.md, cleans up branches.
---

# Sprint End Skill

You are closing a sprint for BigQuery-connector. The user invoked `/sprint-end $ARGUMENTS`.

Determine the current sprint number from TODO.md header or the current branch name.

Follow `docs/process/SPRINT_END_CHECKLIST.md` as the authoritative checklist. Execute each phase below.

## Phase 1: Verify & Ship

1. Run `ruff check . && ruff format --check . && pytest tests/ -v` — report results
2. Check git status — warn about uncommitted changes
3. Ask: has staging been deployed and verified?
4. Ask: has production been deployed (if applicable)?

## Phase 2: Update Tracking

### TODO.md
Read TODO.md and for each task:
- Check if DoD items are all checked (grep for `- [x]` vs `- [ ]`)
- Report: which tasks are complete, which have unchecked items
- For incomplete tasks, ask: defer to next sprint or mark as done?

### KANBAN.md
Read and update `docs/process/KANBAN.md`:
- Clear the "Doing" section
- Move completed tasks to "Done (Sprint {N})" section
- Ask: any new backlog items discovered during the sprint?
- Ask: any new tech debt items?
- Write the updated KANBAN.md

## Phase 2b: Issue Reconciliation

Read `.claude/project.json` for tracker configuration.

### GitHub Mode (`tracker.type === "github"`)

1. Find issue references in sprint commits:
   ```bash
   git log --oneline --grep="Fixes #" --grep="fixes #" --grep="Closes #" --grep="closes #"
   ```

2. Extract referenced issue numbers and check their status:
   ```bash
   gh issue view {N} --repo "{tracker.repo}" --json state,title
   ```

3. Present a reconciliation table:
   | Issue | Title | Status | Suggested Action |
   |-------|-------|--------|-----------------|
   | #N | {title} | open/closed | Close (fixed in commit abc) / Carry forward |

4. For issues the user approves to close:
   ```bash
   gh issue close {N} --repo "{tracker.repo}" --comment "Closed as part of Sprint {N} — fixed in {commit_sha}"
   ```

5. For unresolved bugs, add them to KANBAN.md backlog.

### File-Based Mode (`tracker.type === "none"` or missing)

Check KANBAN.md for any `[BUG]` items that were addressed during the sprint. Ask the user which ones to move to Done.

### No Tracker

Skip this phase and continue.

## Phase 3: Knowledge Transfer

### Sprint Handover
Create `docs/sprints/SPRINT{N}_HANDOVER.md` with:

Gather information by:
- Reading TODO.md for delivered tasks
- Running `git log --oneline sprint{N}/main..HEAD` (or similar) for commit history
- Reading recent changes to understand architecture impacts

Generate the handover with these sections:
- Sprint Theme
- Completed tasks (table: task, status, key files)
- Deferred items (if any, with reasons)
- Key Decisions (ask the user)
- Architecture Changes (derived from code changes)
- Known Issues (ask the user)
- Lessons Learned (ask the user, synthesize from sprint experience)
- Test Coverage (run `pytest tests/ -v` and count)
- Recommendations for Next Sprint

### PROJECT_CONTEXT.md
Update `docs/process/PROJECT_CONTEXT.md`:
- Status → "Sprint {N+1} Planning"
- Last Sync → today's date
- Test count → from pytest output
- Sprint History table → add current sprint
- Current State → summarize what was delivered

### MEMORY.md
If `.claude/MEMORY.md` exists, update it:
- Add lessons learned from this sprint
- Update sprint status (mark current as COMPLETED)
- Add new patterns or conventions
- Keep under 200 lines

## Phase 3b: Sync to Template (if applicable)

If `bin/sync-to-template.sh` exists and it's been 2+ sprints since last sync:
- Mention it to the user
- Offer to run it

## Phase 4: Clean Slate

### Branch Cleanup
- Remind user to merge sprint branch to main via PR
- After merge: `git checkout main && git pull`
- List any remaining feature branches that should be cleaned up

### Final Verification
```bash
git branch --show-current  # main
git status                 # clean
ruff check . && ruff format --check . && pytest tests/ -v  # all green
```

### Check for Pre-Planned Next Sprint

Check if next sprint was pre-planned:
- Read `docs/process/KANBAN.md` — look for "Sprint {N+1} — Candidate" section with items
- Check if `TODO-NEXT.md` exists

If pre-planned scope exists:
- Report: "Sprint {N} is closed. Sprint {N+1} has pre-planned scope — run `/sprint-start` to review and promote."
- List the candidate items

If no pre-planned scope:
- Report: "Sprint {N} is closed. Ready for Sprint {N+1} planning."

## Important Rules

- NEVER trust docs over code — verify task completion by checking the actual codebase
- ALWAYS ask the user for lessons learned and known issues (don't fabricate)
- Update TODO.md checkboxes based on actual code state, not assumptions
- Write the handover doc even if the sprint was small — it's the context anchor for future sessions
