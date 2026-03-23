# Definition of Done

A task is "done" when ALL of the following are true:

## Code Quality
- [ ] All acceptance criteria verified against actual codebase (not just "I think it works")
- [ ] Tests pass: run the test command from sprint-config.yaml
- [ ] Lint clean: run the lint command from sprint-config.yaml
- [ ] No commented-out code, no TODO/FIXME left behind
- [ ] No hardcoded secrets, API keys, or credentials

## Testing
- [ ] New functionality has tests
- [ ] Edge cases covered (empty inputs, error states, boundary values)
- [ ] Tests are independent and repeatable

## Documentation
- [ ] Code is self-documenting (clear names, obvious flow)
- [ ] Complex logic has inline comments explaining WHY, not WHAT
- [ ] Public APIs have docstrings

## Review
- [ ] Changes reviewed (self-review minimum, peer review preferred)
- [ ] No unrelated changes bundled in
- [ ] Commit messages follow project conventions
