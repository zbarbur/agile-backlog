# Sprint 22 Handover — Polish + CI

**Date:** 2026-03-24
**Branch:** sprint22/main
**Tests:** 226 (was 224)
**Commits:** 1

## Completed Tasks (4/4)

| Item | Size | Category |
|------|------|----------|
| Add project name to header | S | feature |
| Search bug — "Volt" not found | S | bug |
| Sprint filter usability | S | feature |
| GitHub Actions CI badge | S | chore |

## Key Deliverables

### Project Name in Header
Reads `project_name` from sprint-config.yaml and displays in header. Falls back to "agile-backlog". XSS-safe via `safe_html()`.

### Search Fix
Search was only applied to backlog items, not doing/done columns (board view) or vnext/vfuture sections (backlog view). Now `filter_items(search=sq)` is applied to all columns and sections.

### Sprint Filter Usability
Sprint dropdown now shows only current +/- 2 sprints plus "Current" and "Unplanned", instead of all 22+ historical sprints.

### GitHub Actions CI
Workflow already existed and was passing — just added the badge to README.

## Architecture Changes

- `config.py` — `get_project_name()` function
- `app.py` — project name in header, search applied to all columns, sprint filter limited to recent range, `safe_html` imported
- `components.py` — search applied to vnext/vfuture sections
- `README.md` — CI badge

## Test Coverage

- 226 tests (up from 224)
- +2 tests for get_project_name config
