# Package Restructure — Proper Python Packaging

**Date:** 2026-03-22
**Status:** Approved
**Backlog Item:** package-restructure-proper-python-packaging-for-portability

## Goal

Restructure the Python package from `src` to `agile_backlog` so the tool can be installed from git (`pip install git+...`) and imported as a library (`from agile_backlog import BacklogItem`). This also unblocks future PyPI publishing.

## Directory Structure

### Before

```
src/
  __init__.py
  cli.py
  models.py
  yaml_store.py
  app.py
  config.py
  tokens.py
  schema.yaml
  agile_backlog.egg-info/
```

### After

```
src/
  agile_backlog/
    __init__.py           # exports __version__, public API
    cli.py
    models.py
    yaml_store.py
    app.py
    config.py
    tokens.py
    schema.yaml
    py.typed              # zero-byte marker for type checkers
```

Deleted: `src/__init__.py`, `src/agile_backlog.egg-info/`

### New files at repo root

- `CHANGELOG.md`

## pyproject.toml Changes

```toml
# Entry point
[project.scripts]
agile-backlog = "agile_backlog.cli:main"    # was: src.cli:main

# Package discovery
[tool.setuptools.packages.find]
where = ["src"]                              # was: include = ["src*"]
```

Version bump to `0.3.0` (breaking change — import paths change).

Add package-data config for non-Python files:

```toml
[tool.setuptools.package-data]
agile_backlog = ["schema.yaml", "py.typed"]

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
```

## Import Updates

All `from src.` → `from agile_backlog.`:

### Source files

| File | Old Import | New Import |
|---|---|---|
| `yaml_store.py` | `from src.models import BacklogItem` | `from agile_backlog.models import BacklogItem` |
| `app.py` | `from src.models import BacklogItem, slugify` | `from agile_backlog.models import BacklogItem, slugify` |
| `app.py` | `from src.tokens import ...` | `from agile_backlog.tokens import ...` |
| `cli.py` | `from src.models import BacklogItem, slugify` | `from agile_backlog.models import BacklogItem, slugify` |
| `cli.py` | `from src.yaml_store import ...` | `from agile_backlog.yaml_store import ...` |
| `cli.py` | `from src.config import set_current_sprint` | `from agile_backlog.config import set_current_sprint` |
| `cli.py` | `from src.app import run_app` | `from agile_backlog.app import run_app` |
| `config.py` | `from src.yaml_store import _git_root` | `from agile_backlog.yaml_store import _git_root` |
| `app.py` | `from src.yaml_store import load_all as _load_all` | `from agile_backlog.yaml_store import load_all as _load_all` |
| `app.py` | `from src.yaml_store import item_exists, load_all, save_item` | `from agile_backlog.yaml_store import item_exists, load_all, save_item` |
| `app.py` | `from src.config import get_current_sprint` | `from agile_backlog.config import get_current_sprint` |

Note: Several of these are **lazy imports** inside function bodies, not at the top of the file. A full `grep -rn "src\." src/ tests/` must be run during implementation to catch all references.

### Test files

| File | Old Import | New Import |
|---|---|---|
| `test_app.py` | `from src.app import ...` | `from agile_backlog.app import ...` |
| `test_app.py` | `from src.models import BacklogItem` | `from agile_backlog.models import BacklogItem` |
| `test_yaml_store.py` | `from src.models import BacklogItem` | `from agile_backlog.models import BacklogItem` |
| `test_yaml_store.py` | `from src.yaml_store import ...` | `from agile_backlog.yaml_store import ...` |
| `test_models.py` | `from src.models import BacklogItem, slugify` | `from agile_backlog.models import BacklogItem, slugify` |
| `test_cli.py` | `from src.cli import main` | `from agile_backlog.cli import main` |

### Mock/patch string targets

These are string-based module references that also need updating:

| File | Old Target | New Target |
|---|---|---|
| `test_yaml_store.py` | `patch("src.yaml_store.get_backlog_dir", ...)` | `patch("agile_backlog.yaml_store.get_backlog_dir", ...)` |
| `test_cli.py` | `patch("src.yaml_store.get_backlog_dir", ...)` | `patch("agile_backlog.yaml_store.get_backlog_dir", ...)` |
| `test_cli.py` | `monkeypatch.setattr("src.app.run_app", ...)` | `monkeypatch.setattr("agile_backlog.app.run_app", ...)` |

## Public API (`__init__.py`)

```python
"""agile-backlog: Lightweight Kanban board tool for agentic development."""

__version__ = "0.3.0"

from agile_backlog.models import BacklogItem
from agile_backlog.yaml_store import load_all, load_item, save_item
```

Enables:
```python
from agile_backlog import BacklogItem, load_all
```

## New Files

### `py.typed`

Zero-byte file in `src/agile_backlog/`. Signals to mypy and other type checkers that the package ships type hints.

### `CHANGELOG.md`

```markdown
# Changelog

## [0.3.0] - 2026-03-22
### Changed
- Package renamed from `src` to `agile_backlog` for proper Python packaging
- All imports now use `from agile_backlog import ...`

### Added
- `py.typed` marker for type checker support
- Public API exports in `__init__.py`
- CHANGELOG.md
```

## Verification

1. `ruff check .` — lint clean
2. `ruff format --check .` — format clean
3. `pytest tests/ -v` — all tests pass
4. `pip install -e .` — installs without error
5. `agile-backlog list` — CLI works
6. `python -c "from agile_backlog import BacklogItem; print(BacklogItem)"` — library import works
7. `python -c "import agile_backlog; print(agile_backlog.__version__)"` — version accessible

## What Does NOT Change

- CLI command name (`agile-backlog`)
- YAML file format and backlog data
- Test structure and coverage
- `.claude/` plugin, skills, memory
- NiceGUI web UI functionality

## What DOES Change (besides imports)

- `CLAUDE.md` — update `streamlit run src/app.py` to `agile-backlog serve`
- `TODO.md` — update `src/` file path references to `src/agile_backlog/` (active working document)
- `.claude/MEMORY.md` — update `src/config.py` reference to `src/agile_backlog/config.py`
- Historical specs/plans in `docs/` contain `from src.` references — leave as-is (documentation, not runtime code)

## Version Single Source of Truth

Use dynamic versioning so the version is defined once in `__init__.py` and read by `pyproject.toml`:

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "agile_backlog.__version__"}
```

Remove the hardcoded `version = "0.3.0"` from `[project]` in `pyproject.toml`.
