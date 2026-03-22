# Package Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the Python package from `src` to `src/agile_backlog/` so it can be installed from git and imported as a library.

**Architecture:** Move all `.py` and data files from `src/` into `src/agile_backlog/`, update all imports from `from src.` to `from agile_backlog.`, update `pyproject.toml` for proper src layout with dynamic versioning.

**Tech Stack:** Python 3.11+, setuptools, pytest, ruff

**Spec:** `docs/superpowers/specs/2026-03-22-package-restructure-design.md`

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `src/agile_backlog/` | New package directory |
| Move | `src/*.py` → `src/agile_backlog/` | All 6 source modules |
| Move | `src/schema.yaml` → `src/agile_backlog/` | YAML schema |
| Create | `src/agile_backlog/py.typed` | Type checker marker |
| Rewrite | `src/agile_backlog/__init__.py` | Public API + `__version__` |
| Delete | `src/__init__.py` | Old empty init |
| Delete | `src/agile_backlog.egg-info/` | Stale build artifact |
| Modify | `pyproject.toml` | Entry point, package discovery, build-system, dynamic version |
| Modify | `tests/test_app.py` | Update imports |
| Modify | `tests/test_cli.py` | Update imports + patch targets |
| Modify | `tests/test_models.py` | Update imports |
| Modify | `tests/test_yaml_store.py` | Update imports + patch target |
| Create | `CHANGELOG.md` | New changelog |
| Modify | `CLAUDE.md:24` | Fix stale Streamlit command |
| Modify | `TODO.md` | Update `src/` path references |
| Modify | `.claude/MEMORY.md` | Update `src/config.py` reference |

---

### Task 1: Move files into new package directory

**Files:**
- Create: `src/agile_backlog/`
- Move: `src/cli.py`, `src/models.py`, `src/yaml_store.py`, `src/app.py`, `src/config.py`, `src/tokens.py`, `src/schema.yaml` → `src/agile_backlog/`
- Delete: `src/__init__.py`, `src/agile_backlog.egg-info/`

- [ ] **Step 1: Create the new package directory**

```bash
mkdir -p src/agile_backlog
```

- [ ] **Step 2: Move all source files**

```bash
git mv src/cli.py src/agile_backlog/cli.py
git mv src/models.py src/agile_backlog/models.py
git mv src/yaml_store.py src/agile_backlog/yaml_store.py
git mv src/app.py src/agile_backlog/app.py
git mv src/config.py src/agile_backlog/config.py
git mv src/tokens.py src/agile_backlog/tokens.py
git mv src/schema.yaml src/agile_backlog/schema.yaml
```

- [ ] **Step 3: Delete old files and build artifacts**

```bash
git rm src/__init__.py
rm -rf src/agile_backlog.egg-info
```

- [ ] **Step 4: Create new `__init__.py` with public API**

Write `src/agile_backlog/__init__.py`:

```python
"""agile-backlog: Lightweight Kanban board tool for agentic development."""

__version__ = "0.3.0"

from agile_backlog.models import BacklogItem
from agile_backlog.yaml_store import load_all, load_item, save_item
```

- [ ] **Step 5: Create `py.typed` marker**

```bash
touch src/agile_backlog/py.typed
```

- [ ] **Step 6: Commit file moves**

```bash
git add -A src/
git commit -m "refactor: move src/*.py to src/agile_backlog/ package"
```

---

### Task 2: Update all source file imports

**Files:**
- Modify: `src/agile_backlog/yaml_store.py:10`
- Modify: `src/agile_backlog/cli.py:7-8,259,271`
- Modify: `src/agile_backlog/app.py:6-7,719,1015,1023`
- Modify: `src/agile_backlog/config.py:9`

- [ ] **Step 1: Update `yaml_store.py`**

Line 10: `from src.models import BacklogItem` → `from agile_backlog.models import BacklogItem`

- [ ] **Step 2: Update `cli.py` top-level imports**

Line 7: `from src.models import BacklogItem, slugify` → `from agile_backlog.models import BacklogItem, slugify`
Line 8: `from src.yaml_store import item_exists, load_all, load_item, save_item` → `from agile_backlog.yaml_store import item_exists, load_all, load_item, save_item`

- [ ] **Step 3: Update `cli.py` lazy imports**

Line 259: `from src.config import set_current_sprint` → `from agile_backlog.config import set_current_sprint`
Line 271: `from src.app import run_app` → `from agile_backlog.app import run_app`

- [ ] **Step 4: Update `app.py` top-level imports**

Line 6: `from src.models import BacklogItem, slugify` → `from agile_backlog.models import BacklogItem, slugify`
Line 7: `from src.tokens import CATEGORY_STYLES, PRIORITY_COLORS, PRIORITY_ORDER` → `from agile_backlog.tokens import CATEGORY_STYLES, PRIORITY_COLORS, PRIORITY_ORDER`

- [ ] **Step 5: Update `app.py` lazy imports**

Line 719: `from src.yaml_store import load_all as _load_all` → `from agile_backlog.yaml_store import load_all as _load_all`
Line 1015: `from src.yaml_store import item_exists, load_all, save_item` → `from agile_backlog.yaml_store import item_exists, load_all, save_item`
Line 1023: `from src.config import get_current_sprint` → `from agile_backlog.config import get_current_sprint`

- [ ] **Step 6: Update `config.py` lazy import**

Line 9: `from src.yaml_store import _git_root` → `from agile_backlog.yaml_store import _git_root`

- [ ] **Step 7: Verify no remaining `from src.` in source**

Run: `grep -rn "from src\." src/agile_backlog/`
Expected: No output

- [ ] **Step 8: Commit import updates**

```bash
git add src/agile_backlog/
git commit -m "refactor: update all source imports from src to agile_backlog"
```

---

### Task 3: Update all test imports and patch targets

**Files:**
- Modify: `tests/test_app.py:2-3`
- Modify: `tests/test_cli.py:7,19,236`
- Modify: `tests/test_models.py:5`
- Modify: `tests/test_yaml_store.py:8-9,23`

- [ ] **Step 1: Update `test_app.py`**

Line 2: `from src.app import category_style, detect_current_sprint, filter_items, render_card_html` → `from agile_backlog.app import category_style, detect_current_sprint, filter_items, render_card_html`
Line 3: `from src.models import BacklogItem` → `from agile_backlog.models import BacklogItem`

- [ ] **Step 2: Update `test_cli.py` imports and patch targets**

Line 7: `from src.cli import main` → `from agile_backlog.cli import main`
Line 19: `patch("src.yaml_store.get_backlog_dir"` → `patch("agile_backlog.yaml_store.get_backlog_dir"`
Line 236: `monkeypatch.setattr("src.app.run_app"` → `monkeypatch.setattr("agile_backlog.app.run_app"`

- [ ] **Step 3: Update `test_models.py`**

Line 5: `from src.models import BacklogItem, slugify` → `from agile_backlog.models import BacklogItem, slugify`

- [ ] **Step 4: Update `test_yaml_store.py`**

Line 8: `from src.models import BacklogItem` → `from agile_backlog.models import BacklogItem`
Line 9: `from src.yaml_store import item_exists, load_all, load_item, save_item` → `from agile_backlog.yaml_store import item_exists, load_all, load_item, save_item`
Line 23: `patch("src.yaml_store.get_backlog_dir"` → `patch("agile_backlog.yaml_store.get_backlog_dir"`

- [ ] **Step 5: Verify no remaining `src.` references in tests**

Run: `grep -rn "from src\.\|\"src\." tests/`
Expected: No output

- [ ] **Step 6: Commit test updates**

```bash
git add tests/
git commit -m "refactor: update all test imports from src to agile_backlog"
```

---

### Task 4: Update `pyproject.toml`

**Files:**
- Modify: `pyproject.toml:2-3,34-35,37-38` + add new sections

- [ ] **Step 1: Update version to dynamic**

Remove line 3 (`version = "0.2.0"`).
Add `dynamic = ["version"]` after the `name` field.

Result:
```toml
[project]
name = "agile-backlog"
dynamic = ["version"]
```

- [ ] **Step 2: Update entry point**

Line 35: `agile-backlog = "src.cli:main"` → `agile-backlog = "agile_backlog.cli:main"`

- [ ] **Step 3: Update package discovery**

Lines 37-38: Replace:
```toml
[tool.setuptools.packages.find]
include = ["src*"]
```
With:
```toml
[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: Add package-data and build-system sections**

Append before `[tool.ruff]`:

```toml
[tool.setuptools.package-data]
agile_backlog = ["schema.yaml", "py.typed"]

[tool.setuptools.dynamic]
version = {attr = "agile_backlog.__version__"}

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 5: Commit pyproject.toml**

```bash
git add pyproject.toml
git commit -m "build: update pyproject.toml for agile_backlog package layout"
```

---

### Task 5: Run tests and verify

- [ ] **Step 1: Reinstall package in dev mode**

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

If pip is not available in venv:
```bash
.venv/bin/python -m ensurepip && .venv/bin/python -m pip install -e ".[dev]"
```

- [ ] **Step 2: Run linter**

Run: `ruff check .`
Expected: All passed

- [ ] **Step 3: Run formatter check**

Run: `ruff format --check .`
Expected: All files already formatted

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v`
Expected: All 110 tests pass

- [ ] **Step 5: Verify CLI works**

Run: `.venv/bin/agile-backlog list --status doing`
Expected: Shows 4 items in doing

- [ ] **Step 6: Verify library import works**

Run: `.venv/bin/python -c "from agile_backlog import BacklogItem, __version__; print(f'v{__version__}', BacklogItem)"`
Expected: `v0.3.0 <class 'agile_backlog.models.BacklogItem'>`

- [ ] **Step 7: Verify old imports fail**

Run: `.venv/bin/python -c "from src.models import BacklogItem"`
Expected: `ModuleNotFoundError`

---

### Task 6: Create CHANGELOG.md and update docs

**Files:**
- Create: `CHANGELOG.md`
- Modify: `CLAUDE.md:24`
- Modify: `TODO.md:73-135`
- Modify: `.claude/MEMORY.md:17`

- [ ] **Step 1: Create CHANGELOG.md**

Write `CHANGELOG.md`:

```markdown
# Changelog

## [0.3.0] - 2026-03-22
### Changed
- Package renamed from `src` to `agile_backlog` for proper Python packaging
- All imports now use `from agile_backlog import ...`
- Version is now dynamic (single source of truth in `__init__.py`)

### Added
- `py.typed` marker for type checker support
- Public API exports in `__init__.py` (`BacklogItem`, `load_all`, `load_item`, `save_item`)
- `CHANGELOG.md`
- `[build-system]` table in `pyproject.toml`
```

- [ ] **Step 2: Update CLAUDE.md**

Line 24: `- **Run Streamlit:** \`streamlit run src/app.py\`` → `- **Run Web UI:** \`agile-backlog serve\``

- [ ] **Step 3: Update TODO.md**

Replace all `src/models.py` → `src/agile_backlog/models.py`, `src/cli.py` → `src/agile_backlog/cli.py`, `src/app.py` → `src/agile_backlog/app.py`, `src/schema.yaml` → `src/agile_backlog/schema.yaml` in TODO.md.

- [ ] **Step 4: Update .claude/MEMORY.md**

Line 17: `src/config.py` → `src/agile_backlog/config.py`

- [ ] **Step 5: Commit docs**

```bash
git add CHANGELOG.md CLAUDE.md TODO.md .claude/MEMORY.md
git commit -m "docs: add CHANGELOG.md, update paths in CLAUDE.md, TODO.md, MEMORY.md"
```

---

### Task 7: Final verification and cleanup

- [ ] **Step 1: Run full CI check**

```bash
ruff check . && ruff format --check . && pytest tests/ -v
```

Expected: All green

- [ ] **Step 2: Verify no stale `from src.` references remain**

```bash
grep -rn "from src\." src/ tests/
```

Expected: No output

- [ ] **Step 3: Verify git status is clean**

```bash
git status
```

Expected: Clean working tree (except untracked backlog YAML files)

- [ ] **Step 4: Update backlog item status**

```bash
.venv/bin/agile-backlog move package-restructure-proper-python-packaging-for-portability --status done
```
