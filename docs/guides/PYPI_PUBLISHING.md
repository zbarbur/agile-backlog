# PyPI Publishing Guide

## Prerequisites

- PyPI account at https://pypi.org/account/register/
- GitHub repo: `zbarbur/agile-backlog`

## One-Time Setup

### 1. Configure Trusted Publishing on PyPI

1. Log in to https://pypi.org
2. Go to https://pypi.org/manage/account/publishing/
3. Under "Add a new pending publisher", fill in:
   - **PyPI project name:** `agile-backlog`
   - **Owner:** `zbarbur`
   - **Repository name:** `agile-backlog`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`
4. Click "Add"

### 2. Configure GitHub Environment

1. Go to https://github.com/zbarbur/agile-backlog/settings/environments
2. Click "New environment"
3. Name it `pypi`
4. (Optional) Add protection rules:
   - **Required reviewers** — require approval before publish
   - **Deployment branches** — restrict to `main` or tags only

### 3. Verify Build Locally

```bash
pip install build twine
python -m build
twine check dist/*
```

Expected output: `PASSED` for both wheel and sdist.

Clean up: `rm -rf dist/ build/ src/*.egg-info`

## How Publishing Works

```
Sprint end
  └─ git tag v0.24.0 && git push origin v0.24.0
      └─ GitHub Actions triggers .github/workflows/publish.yml
          └─ Builds wheel + sdist
              └─ Publishes to PyPI via OIDC (no API tokens)
                  └─ Available: pip install agile-backlog
```

The publish workflow (`.github/workflows/publish.yml`) triggers on any tag matching `v*`.

## Manual First Publish

If you want to test publishing before relying on the automated workflow:

```bash
# Build
python -m build

# Upload (will prompt for PyPI username/password or API token)
twine upload dist/*

# Verify
pip install agile-backlog
agile-backlog --help
```

After the first manual upload, trusted publishing takes over for subsequent releases.

## Versioning Scheme

Sprint-based: `v0.{sprint}.{patch}`

| Version | Meaning |
|---------|---------|
| `v0.24.0` | Sprint 24 release |
| `v0.24.1` | Hotfix after Sprint 24 |
| `v0.25.0` | Sprint 25 release |
| `v1.0.0` | First stable/breaking release (manual decision) |

The version is set in `src/agile_backlog/__init__.py` (`__version__`) and read by `pyproject.toml` via `[tool.setuptools.dynamic]`.

The sprint-end skill auto-tags after merge:
```bash
VERSION=$(grep 'current_version' .claude/sprint-config.yaml | awk '{print $2}' | tr -d '"')
git tag -a "v${VERSION}" -m "Release v${VERSION} — Sprint N"
git push origin "v${VERSION}"
```

## Troubleshooting

### "Project name already taken"
Someone else registered `agile-backlog` on PyPI. You'd need to pick a different name in `pyproject.toml`.

### Trusted publishing fails with 403
- Verify the environment name matches exactly (`pypi`)
- Verify the workflow filename matches (`publish.yml`)
- Verify the GitHub owner/repo matches (`zbarbur/agile-backlog`)
- Check that the `pypi` environment exists in GitHub repo settings

### Build fails
```bash
python -m build 2>&1 | tail -20
```
Common issues: missing `build-system` in pyproject.toml, invalid TOML syntax, missing package files.

### Package installs but CLI doesn't work
Verify `[project.scripts]` in pyproject.toml points to the correct entry point:
```toml
[project.scripts]
agile-backlog = "agile_backlog.cli:main"
```
