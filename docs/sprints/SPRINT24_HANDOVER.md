# Sprint 24 Handover — Publishing

**Date:** 2026-03-25
**Branch:** sprint24/main
**Tests:** 244 (was 243)
**Commits:** 8

## Completed Tasks (5/5)

| Item | Size | Category |
|------|------|----------|
| Repo polish — LICENSE, pyproject metadata, README | S | chore |
| Versioning policy + auto-tag on sprint end | M | feature |
| Show version in web UI header | S | feature |
| Publish to PyPI | M | chore |
| GitHub Actions publish workflow | S | chore |

## Key Deliverables

### Repo Polish
- MIT LICENSE file added
- `[project.urls]` section in pyproject.toml (Homepage, Repository, Issues)
- README updated with PyPI badge, License badge, PyPI install instructions
- Removed leftover `.streamlit/` directory

### Versioning Policy
- Sprint-based scheme: `v0.{sprint}.{patch}` (currently v0.24.0)
- `__version__` in `__init__.py` is single source of truth
- `sprint-config.yaml` has `version_scheme` and `current_version` fields
- Sprint-end skill auto-tags releases (`git tag -a v0.24.0`)
- `get_version()` helper in `config.py`

### Version in UI
- Version label displayed in header next to project name (muted style)

### PyPI Publishing
- Build verified: wheel + sdist pass `twine check`
- Fixed TOML ordering bug (`[project.urls]` was breaking `dependencies`)
- Test install from wheel: CLI works, version correct
- Publishing guide at `docs/guides/PYPI_PUBLISHING.md`

### GitHub Actions Publish Workflow
- `.github/workflows/publish.yml` triggers on `v*` tag push
- Uses OIDC trusted publishing (no API tokens)
- Requires `pypi` environment configured in GitHub repo settings

## Architecture Changes

- `LICENSE` — new file (MIT)
- `pyproject.toml` — project-urls, TOML ordering fix
- `README.md` — badges, PyPI install instructions
- `src/agile_backlog/__init__.py` — version bumped to 0.24.0
- `src/agile_backlog/config.py` — `get_version()` function
- `src/agile_backlog/app.py` — version display in header
- `.claude/sprint-config.yaml` — version fields
- `.claude/skills/sprint-end/SKILL.md` — auto-tag step
- `.github/workflows/publish.yml` — new workflow
- `docs/guides/PYPI_PUBLISHING.md` — new guide

## Known Issues

- PyPI trusted publishing requires GitHub environment `pypi` to be configured (done)
- License format deprecation warning in build (deadline 2027-02-18): `license = { text = "MIT" }` should become `license = "MIT"`
- Context analysis hook still not producing real data (registered mid-session in Sprint 23)
- Repo made public during this sprint

## Test Coverage

- 244 tests (up from 243)
- +1 test for get_version()
