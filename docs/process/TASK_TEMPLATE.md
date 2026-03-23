# Sprint Task Template

Task specs live in **YAML backlog items** (`backlog/*.yaml`), not in TODO.md. Use `agile-backlog edit` to populate fields:

```bash
agile-backlog edit <item-id> \
  --goal "One sentence — what this delivers" \
  --complexity M \
  --acceptance-criteria "Verifiable criterion 1" \
  --acceptance-criteria "Verifiable criterion 2" \
  --acceptance-criteria "Tests pass (see sprint-config.yaml test_command)" \
  --acceptance-criteria "Lint clean (see sprint-config.yaml lint_command)" \
  --technical-specs "File: src/path.py — what to change" \
  --technical-specs "File: tests/test_path.py — what to test" \
  --test-plan "tests/test_x.py: test description" \
  --phase spec
```

---

## Required Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `goal` | One sentence: what + why | "Add rate limiting to prevent abuse (100 req/min per key)" |
| `complexity` | S / M / L | S = <50 lines, M = 50-300, L = 300+ |
| `acceptance_criteria` | Independently verifiable checkboxes | "GET /api/health returns 200 with { status: ok }" |
| `technical_specs` | File paths, schemas, config changes | "File: src/rate_limiter.py — sliding window counter" |
| `test_plan` | What tests to write and what they verify | "tests/test_rate_limiter.py: counter, window, 429 response" |
| `sprint_target` | Sprint number | Set via `--sprint N` |
| `phase` | plan → spec → build → review | Tracks progress |

## Optional Fields

| Field | Purpose |
|-------|---------|
| `depends_on` | Other item IDs that must complete first |
| `tags` | Freeform domain labels |
| `notes` | Additional context, flagged comments |

---

## Field Guide

### Goal
One sentence that answers: **what** does this task deliver and **why** does it matter?

| Quality | Example |
|---------|---------|
| Good | "Add rate limiting to the `/api/users` endpoint to prevent abuse (max 100 req/min per API key)" |
| Bad | "Implement rate limiting" |
| Good | "Extract report generation logic from the route handler into a testable module" |
| Bad | "Refactor reports" |

### Complexity

| Size | Guideline |
|------|-----------|
| **S** | Config change, small bug fix, minor UI tweak. < 50 lines changed. |
| **M** | New endpoint, new component, moderate refactoring. 50-300 lines changed. |
| **L** | New subsystem, cross-cutting change, major feature. 300+ lines changed. |

### Acceptance Criteria (DoD)
Every criterion must be **independently verifiable** by grepping the codebase or running a command. See `DEFINITION_OF_DONE.md` for detailed guidance.

| Quality | Example |
|---------|---------|
| Good | `GET /api/health returns 200 with { status: "ok" }` |
| Bad | `Health endpoint works` |
| Good | `Rate limiter returns 429 after 100 requests in 60s` |
| Bad | `Rate limiting implemented` |

**Always include these baseline items:**
- Tests pass (from sprint-config.yaml `test_command`)
- Lint clean (from sprint-config.yaml `lint_command`)

### Technical Specs
Concrete implementation details. File paths, endpoints, schemas, environment variables, configuration changes.

| Quality | Example |
|---------|---------|
| Good | `File: src/rate_limiter.py — sliding window counter using Redis INCR` |
| Bad | `Add rate limiting logic somewhere` |

### Test Plan
What tests to write, what they verify, and where they live.

| Quality | Example |
|---------|---------|
| Good | `tests/test_rate_limiter.py — unit: counter increment, window reset, 429 response` |
| Bad | `Write some tests` |

---

## Full Example (as YAML item)

```yaml
title: "Add API rate limiting middleware"
category: feature
priority: P2
status: doing
sprint_target: 17
phase: spec
goal: "Prevent API abuse by enforcing per-key rate limits (100 req/min) on all authenticated endpoints"
complexity: M
depends_on:
  - api-key-system
acceptance_criteria:
  - "Middleware applied to all /api/* routes"
  - "Returns 429 with Retry-After header when limit exceeded"
  - "Rate limit headers present: X-RateLimit-Limit, X-RateLimit-Remaining"
  - "Tests pass"
  - "Lint clean"
technical_specs:
  - "File: src/rate_limiter.py — sliding window counter (in-memory dict)"
  - "File: src/middleware/rate_limit.py — wraps route handlers"
  - "Env vars: RATE_LIMIT_MAX (default: 100), RATE_LIMIT_WINDOW_MS (default: 60000)"
test_plan:
  - "tests/test_rate_limiter.py — unit: counter increment, window expiry, limit enforcement"
  - "tests/test_rate_limit_middleware.py — integration: header presence, 429 response"
```
