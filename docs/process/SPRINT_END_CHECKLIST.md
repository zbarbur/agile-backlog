# Sprint End Checklist — agile-backlog

## Phase 1: Verify & Ship

### 1. Final Quality Gate
- [ ] CI passes: `ruff check . && ruff format --check . && pytest tests/ -v`
- [ ] No lint warnings or errors

### 1b. Comprehensive Code Review
- [ ] Run 9-point code review against all sprint changes
- [ ] All Critical findings fixed
- [ ] Warning findings fixed or added to backlog

**Review checklist:**
1. Logging — appropriate levels, structured
2. Error handling — actionable messages, no swallowed exceptions
3. Edge cases — empty inputs, null values, missing files
4. Resilience — missing YAML files, malformed data, missing fields
5. Input validation — invalid status, bad priority, missing required fields
6. Test coverage — gaps, negative tests
7. Security — no secrets, no injection
8. Code quality — DRY, YAGNI, clear naming
9. Spec compliance — matches design doc

## Phase 2: Update Tracking
- [ ] TODO.md checkboxes all checked
- [ ] KANBAN.md updated (Doing → Done)

## Phase 3: Knowledge Transfer
- [ ] Sprint handover written
- [ ] PROJECT_CONTEXT.md updated
- [ ] MEMORY.md updated

## Phase 4: Clean Slate
- [ ] Branch merged to main
- [ ] Working tree clean
