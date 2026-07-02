# Two-Channel Adoption (`init` + Bundled Plugin) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `agile-backlog init` command that scaffolds a project in one step (config + skills + hooks), and turn `plugin/` into a real Claude Code plugin fed from one canonical content source.

**Architecture:** New `scaffold.py` module holds all init logic as pure functions taking an explicit `root: Path` (testable with `tmp_path`). The hook script moves into the package as `bundled_hooks/` package data. `plugin/` mirrors `bundled_skills/` + `bundled_hooks/` via `scripts/sync_plugin.py`; a pytest runs it in `--check` mode so CI fails on drift. Plugin hooks use ONE pipe-regex matcher; `plugin.json` stays minimal (auto-discovery covers `skills/`, `commands/`, `hooks/hooks.json`).

**Tech Stack:** Python 3.11+, Click, PyYAML, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-07-02-two-channel-adoption-init-and-plugin-design.md`

## Global Constraints

- Python 3.11+; type hints in modern style (`list[dict]`, `str | None`).
- Ruff, 120-char lines. Lint gate: `.venv/bin/ruff check . && .venv/bin/ruff format --check .`
- No per-function docstrings — module-level only. EXCEPTION: Click command functions use a one-line docstring (it becomes `--help` text; existing pattern in `cli.py`).
- CI command (run after each task): `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
- Conventional commits.
- `init` must be idempotent: second run with same flags changes nothing and says so. It merges JSON settings — never clobbers existing keys/entries.
- Plugin content is NEVER hand-edited in `plugin/skills/` or `plugin/hooks/scripts/` — only via sync. `plugin/hooks/hooks.json`, `plugin/commands/*.md`, `plugin/plugin.json` are authored.

---

### Task 1: Bundle the hook script as package data

**Files:**
- Create: `src/agile_backlog/bundled_hooks/post-tool-logger.sh` (copy of `.claude/hooks/post-tool-logger.sh`)
- Modify: `pyproject.toml` (package-data line)
- Modify: `tests/test_hook_script.py:7` (HOOK_SCRIPT path)

**Interfaces:**
- Consumes: existing `.claude/hooks/post-tool-logger.sh` (unchanged content).
- Produces: canonical hook at `src/agile_backlog/bundled_hooks/post-tool-logger.sh`, shipped in the wheel. Later tasks resolve it as `Path(scaffold.__file__).parent / "bundled_hooks" / "post-tool-logger.sh"`.

- [ ] **Step 1: Copy the hook into the package (canonical location)**

```bash
mkdir -p src/agile_backlog/bundled_hooks
cp .claude/hooks/post-tool-logger.sh src/agile_backlog/bundled_hooks/post-tool-logger.sh
```

The `.claude/hooks/` copy stays — agile-backlog dogfoods its own consumer layout. Task 6's sync `--check` will guard the two copies against drift.

- [ ] **Step 2: Ship it as package data**

In `pyproject.toml`, change:

```toml
[tool.setuptools.package-data]
agile_backlog = ["schema.yaml", "py.typed", "bundled_skills/**/*"]
```

to:

```toml
[tool.setuptools.package-data]
agile_backlog = ["schema.yaml", "py.typed", "bundled_skills/**/*", "bundled_hooks/**/*"]
```

- [ ] **Step 3: Point the hook tests at the canonical copy**

In `tests/test_hook_script.py` line 7, change:

```python
HOOK_SCRIPT = Path(__file__).parent.parent / ".claude" / "hooks" / "post-tool-logger.sh"
```

to:

```python
HOOK_SCRIPT = Path(__file__).parent.parent / "src" / "agile_backlog" / "bundled_hooks" / "post-tool-logger.sh"
```

- [ ] **Step 4: Run the hook tests**

Run: `.venv/bin/pytest tests/test_hook_script.py -v`
Expected: all PASS (same script content, new path).

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/bundled_hooks pyproject.toml tests/test_hook_script.py
git commit -m "feat: bundle post-tool-logger hook as package data"
```

---

### Task 2: `scaffold.py` — project detection

**Files:**
- Create: `src/agile_backlog/scaffold.py`
- Create: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `detect_project(root: Path) -> dict` with keys `project_name`, `language`, `test_command`, `lint_command`, `format_command`, `cli_command` (values `str | None` except `project_name`/`cli_command`). Task 5 consumes this.

- [ ] **Step 1: Write failing tests**

Create `tests/test_scaffold.py`:

```python
"""Tests for scaffold.py — init detection, config scaffolding, hooks install/merge."""

import json
from pathlib import Path

from agile_backlog import scaffold


class TestDetectProject:
    def test_python_project_with_pytest_and_ruff(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo"\ndependencies = []\n'
            '[project.optional-dependencies]\ndev = ["pytest>=8.0.0", "ruff>=0.8.0"]\n'
        )
        d = scaffold.detect_project(tmp_path)
        assert d["language"] == "python"
        assert d["test_command"] == "pytest tests/ -v"
        assert d["lint_command"] == "ruff check . && ruff format --check ."
        assert d["format_command"] == "ruff format ."
        assert d["cli_command"] == "agile-backlog"

    def test_python_project_with_venv_prefixes_commands(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["pytest", "ruff"]\n')
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        d = scaffold.detect_project(tmp_path)
        assert d["test_command"] == ".venv/bin/pytest tests/ -v"
        assert d["cli_command"] == ".venv/bin/agile-backlog"

    def test_node_project(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            json.dumps({"name": "webapp", "scripts": {"test": "vitest", "lint": "eslint ."}})
        )
        d = scaffold.detect_project(tmp_path)
        assert d["language"] == "javascript"
        assert d["project_name"] == "webapp"
        assert d["test_command"] == "npm test"
        assert d["lint_command"] == "npm run lint"
        assert d["format_command"] is None

    def test_typescript_detected_via_tsconfig(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(json.dumps({"name": "webapp", "scripts": {}}))
        (tmp_path / "tsconfig.json").write_text("{}")
        assert scaffold.detect_project(tmp_path)["language"] == "typescript"

    def test_empty_project_falls_back_to_dirname(self, tmp_path: Path):
        d = scaffold.detect_project(tmp_path)
        assert d["project_name"] == tmp_path.name
        assert d["language"] is None
        assert d["test_command"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_scaffold.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agile_backlog.scaffold'` (or ImportError).

- [ ] **Step 3: Implement detection**

Create `src/agile_backlog/scaffold.py`:

```python
"""Project scaffolding for `agile-backlog init` — detection, sprint-config, skills, hooks, settings merge."""

import json
from pathlib import Path

PACKAGE_DIR = Path(__file__).parent
HOOK_NAME = "post-tool-logger.sh"
HOOK_MATCHERS = ["Read", "Grep", "Glob", "Bash", "WebFetch", "Agent", "Edit", "Write", "Skill"]
HOOK_COMMAND = f"bash .claude/hooks/{HOOK_NAME}"
GITIGNORE_LINE = ".claude/context-logs/"
DOC_DIRS = ["docs/sprints", "docs/process", "docs/superpowers/specs", "docs/superpowers/plans"]


def detect_project(root: Path) -> dict:
    detected: dict = {
        "project_name": root.resolve().name,
        "language": None,
        "test_command": None,
        "lint_command": None,
        "format_command": None,
        "cli_command": "agile-backlog",
    }
    pyproject = root / "pyproject.toml"
    package_json = root / "package.json"
    if pyproject.exists():
        text = pyproject.read_text()
        prefix = ".venv/bin/" if (root / ".venv" / "bin").exists() else ""
        detected["language"] = "python"
        detected["cli_command"] = f"{prefix}agile-backlog"
        if "pytest" in text:
            detected["test_command"] = f"{prefix}pytest tests/ -v"
        if "ruff" in text:
            detected["lint_command"] = f"{prefix}ruff check . && {prefix}ruff format --check ."
            detected["format_command"] = f"{prefix}ruff format ."
    elif package_json.exists():
        data = json.loads(package_json.read_text())
        detected["language"] = "typescript" if (root / "tsconfig.json").exists() else "javascript"
        detected["project_name"] = data.get("name") or detected["project_name"]
        scripts = data.get("scripts", {})
        if "test" in scripts:
            detected["test_command"] = "npm test"
        if "lint" in scripts:
            detected["lint_command"] = "npm run lint"
        if "format" in scripts:
            detected["format_command"] = "npm run format"
    return detected
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_scaffold.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/scaffold.py tests/test_scaffold.py
git commit -m "feat: scaffold.detect_project — toolchain detection for init"
```

---

### Task 3: `scaffold.py` — sprint-config template, doc dirs, gitignore

**Files:**
- Modify: `src/agile_backlog/scaffold.py`
- Modify: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: constants from Task 2 (`GITIGNORE_LINE`, `DOC_DIRS`).
- Produces: `render_sprint_config(values: dict) -> str`; `scaffold_sprint_config(root: Path, values: dict, force: bool = False) -> bool`; `ensure_doc_dirs(root: Path) -> list[str]`; `ensure_gitignore(root: Path) -> bool`. Booleans mean "wrote/changed something". Task 5 consumes all four.

- [ ] **Step 1: Write failing tests** (append to `tests/test_scaffold.py`)

```python
VALUES = {
    "project_name": "demo",
    "language": "python",
    "test_command": "pytest tests/ -v",
    "lint_command": "ruff check .",
    "format_command": "ruff format .",
    "ci_command": "ruff check . && pytest tests/ -v",
    "cli_command": "agile-backlog",
}


class TestSprintConfig:
    def test_render_contains_values_and_placeholders(self):
        text = scaffold.render_sprint_config(VALUES)
        assert "project_name: demo" in text
        assert 'ci_command: "ruff check . && pytest tests/ -v"' in text
        assert "current_sprint: 1" in text
        assert 'show: "agile-backlog show {id}"' in text  # runtime placeholders survive rendering
        assert 'branch_pattern: "sprint{N}/main"' in text

    def test_scaffold_writes_once_and_respects_force(self, tmp_path: Path):
        assert scaffold.scaffold_sprint_config(tmp_path, VALUES) is True
        cfg = tmp_path / ".claude" / "sprint-config.yaml"
        assert cfg.exists()
        assert scaffold.scaffold_sprint_config(tmp_path, VALUES) is False  # idempotent
        cfg.write_text("current_sprint: 9\n")
        assert scaffold.scaffold_sprint_config(tmp_path, VALUES, force=True) is True
        assert "current_sprint: 1" in cfg.read_text()


class TestDirsAndGitignore:
    def test_ensure_doc_dirs_creates_then_noops(self, tmp_path: Path):
        created = scaffold.ensure_doc_dirs(tmp_path)
        assert "docs/sprints" in created
        assert (tmp_path / "docs" / "superpowers" / "plans").is_dir()
        assert scaffold.ensure_doc_dirs(tmp_path) == []

    def test_ensure_gitignore_appends_once(self, tmp_path: Path):
        (tmp_path / ".gitignore").write_text("*.pyc\n")
        assert scaffold.ensure_gitignore(tmp_path) is True
        assert scaffold.ensure_gitignore(tmp_path) is False
        content = (tmp_path / ".gitignore").read_text()
        assert content.count(".claude/context-logs/") == 1
        assert "*.pyc" in content

    def test_ensure_gitignore_creates_file(self, tmp_path: Path):
        assert scaffold.ensure_gitignore(tmp_path) is True
        assert (tmp_path / ".gitignore").read_text() == ".claude/context-logs/\n"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_scaffold.py -v`
Expected: new tests FAIL with `AttributeError: module 'agile_backlog.scaffold' has no attribute 'render_sprint_config'`; Task 2 tests still PASS.

- [ ] **Step 3: Implement** (append to `src/agile_backlog/scaffold.py`)

```python
SPRINT_CONFIG_TEMPLATE = """\
# Project Sprint Configuration — read by all sprint skills
project_name: {project_name}
language: {language}

current_sprint: 1

# Commands
test_command: "{test_command}"
lint_command: "{lint_command}"
format_command: "{format_command}"
ci_command: "{ci_command}"

# Backlog tool
backlog_tool: agile-backlog
backlog_commands:
  list: "{cli_command} list"
  list_doing: "{cli_command} list --status doing"
  list_done: "{cli_command} list --status done"
  list_backlog: "{cli_command} list --status backlog"
  list_bugs: "{cli_command} list --category bug --status backlog"
  show: "{cli_command} show {{id}}"
  add: "{cli_command} add \\"{{title}}\\" --category {{category}} --priority {{priority}}"
  move: "{cli_command} move {{id}} --status {{status}}"
  edit: "{cli_command} edit {{id}}"
  flagged: "{cli_command} flagged"
  context_report: "{cli_command} context-report"

# Documentation paths
docs:
  handover_dir: "docs/sprints/"
  specs_dir: "docs/superpowers/specs/"
  plans_dir: "docs/superpowers/plans/"
  project_context: "docs/process/PROJECT_CONTEXT.md"
  definition_of_done: "docs/process/DEFINITION_OF_DONE.md"

# Branch conventions
branch_pattern: "sprint{{N}}/main"
commit_style: conventional

# Sprint settings
default_sprint_capacity:
  small: 3-4
  medium: 2-3
  large: 1-2
"""


def render_sprint_config(values: dict) -> str:
    return SPRINT_CONFIG_TEMPLATE.format(**values)


def scaffold_sprint_config(root: Path, values: dict, force: bool = False) -> bool:
    path = root / ".claude" / "sprint-config.yaml"
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_sprint_config(values))
    return True


def ensure_doc_dirs(root: Path) -> list[str]:
    created = []
    for rel in DOC_DIRS:
        path = root / rel
        if not path.exists():
            path.mkdir(parents=True)
            created.append(rel)
    return created


def ensure_gitignore(root: Path) -> bool:
    path = root / ".gitignore"
    lines = path.read_text().splitlines() if path.exists() else []
    if GITIGNORE_LINE in lines:
        return False
    lines.append(GITIGNORE_LINE)
    path.write_text("\n".join(lines) + "\n")
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_scaffold.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/scaffold.py tests/test_scaffold.py
git commit -m "feat: scaffold sprint-config template, doc dirs, gitignore"
```

---

### Task 4: `scaffold.py` — hook install and settings.local.json merge

**Files:**
- Modify: `src/agile_backlog/scaffold.py`
- Modify: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: `PACKAGE_DIR`, `HOOK_NAME`, `HOOK_MATCHERS`, `HOOK_COMMAND` (Task 2); canonical hook file (Task 1).
- Produces: `install_hooks(root: Path, force: bool = False) -> bool`; `merge_settings_hooks(root: Path) -> bool`. Task 5 consumes both. Merge rule: if ANY existing PostToolUse hook command mentions `post-tool-logger.sh`, treat as already wired (return False); otherwise append ONE entry with pipe-joined matcher.

- [ ] **Step 1: Write failing tests** (append to `tests/test_scaffold.py`)

```python
class TestHooks:
    def test_install_hooks_copies_script(self, tmp_path: Path):
        assert scaffold.install_hooks(tmp_path) is True
        dest = tmp_path / ".claude" / "hooks" / "post-tool-logger.sh"
        assert dest.exists()
        assert "PostToolUse hook" in dest.read_text()
        assert scaffold.install_hooks(tmp_path) is False  # idempotent
        assert scaffold.install_hooks(tmp_path, force=True) is True

    def test_merge_creates_settings_with_single_regex_matcher(self, tmp_path: Path):
        assert scaffold.merge_settings_hooks(tmp_path) is True
        settings = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
        entries = settings["hooks"]["PostToolUse"]
        assert len(entries) == 1
        assert entries[0]["matcher"] == "Read|Grep|Glob|Bash|WebFetch|Agent|Edit|Write|Skill"
        assert entries[0]["hooks"][0]["command"] == "bash .claude/hooks/post-tool-logger.sh"

    def test_merge_preserves_existing_settings(self, tmp_path: Path):
        path = tmp_path / ".claude" / "settings.local.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "permissions": {"allow": ["Bash(ls:*)"]},
            "hooks": {"PostToolUse": [
                {"matcher": "Write", "hooks": [{"type": "command", "command": "bash lint.sh"}]}
            ]},
        }))
        assert scaffold.merge_settings_hooks(tmp_path) is True
        settings = json.loads(path.read_text())
        assert settings["permissions"] == {"allow": ["Bash(ls:*)"]}
        assert len(settings["hooks"]["PostToolUse"]) == 2  # existing entry kept, ours appended

    def test_merge_detects_already_wired(self, tmp_path: Path):
        assert scaffold.merge_settings_hooks(tmp_path) is True
        assert scaffold.merge_settings_hooks(tmp_path) is False  # no duplicate entry
        settings = json.loads((tmp_path / ".claude" / "settings.local.json").read_text())
        assert len(settings["hooks"]["PostToolUse"]) == 1

    def test_merge_detects_per_tool_wiring(self, tmp_path: Path):
        path = tmp_path / ".claude" / "settings.local.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"hooks": {"PostToolUse": [
            {"matcher": "Read", "hooks": [{"type": "command", "command": "bash .claude/hooks/post-tool-logger.sh"}]}
        ]}}))
        assert scaffold.merge_settings_hooks(tmp_path) is False  # existing per-tool style respected
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_scaffold.py::TestHooks -v`
Expected: FAIL with `AttributeError` on `install_hooks`.

- [ ] **Step 3: Implement** (append to `src/agile_backlog/scaffold.py`; add `import shutil` at top with the other imports)

```python
def install_hooks(root: Path, force: bool = False) -> bool:
    src = PACKAGE_DIR / "bundled_hooks" / HOOK_NAME
    dest = root / ".claude" / "hooks" / HOOK_NAME
    if dest.exists() and not force:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def merge_settings_hooks(root: Path) -> bool:
    path = root / ".claude" / "settings.local.json"
    settings = json.loads(path.read_text()) if path.exists() else {}
    post = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])
    for entry in post:
        for hook in entry.get("hooks", []):
            if HOOK_NAME in hook.get("command", ""):
                return False
    post.append({
        "matcher": "|".join(HOOK_MATCHERS),
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n")
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_scaffold.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/scaffold.py tests/test_scaffold.py
git commit -m "feat: scaffold hook install + settings.local.json merge"
```

---

### Task 5: `init` CLI command + `install-skills` refactor

**Files:**
- Modify: `src/agile_backlog/scaffold.py` (add `install_skills_from_package`, `CLAUDE_MD_BLOCK`)
- Modify: `src/agile_backlog/cli.py` (`install-skills` body at lines 422-455; new `init` command)
- Create: `tests/test_init_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 2-4.
- Produces: `scaffold.install_skills_from_package(target_dir: Path, force: bool = False) -> tuple[list[str], list[str]]` (installed, skipped); CLI `agile-backlog init [--config-only] [--force] [--yes]`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_init_cli.py`:

```python
"""Tests for `agile-backlog init` — full setup, --config-only, idempotency."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from agile_backlog.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\ndependencies = ["pytest", "ruff"]\n')
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestInit:
    def test_full_init(self, runner: CliRunner, project: Path):
        result = runner.invoke(main, ["init", "--yes"])
        assert result.exit_code == 0
        assert (project / ".claude" / "sprint-config.yaml").exists()
        assert (project / ".claude" / "skills" / "sprint-start").is_dir()
        assert (project / ".claude" / "hooks" / "post-tool-logger.sh").exists()
        settings = json.loads((project / ".claude" / "settings.local.json").read_text())
        assert settings["hooks"]["PostToolUse"][0]["matcher"].startswith("Read|")
        assert (project / "docs" / "sprints").is_dir()
        assert ".claude/context-logs/" in (project / ".gitignore").read_text()
        assert "## Commands" in result.output  # printed CLAUDE.md block

    def test_config_only_skips_skills_and_hooks(self, runner: CliRunner, project: Path):
        result = runner.invoke(main, ["init", "--config-only", "--yes"])
        assert result.exit_code == 0
        assert (project / ".claude" / "sprint-config.yaml").exists()
        assert not (project / ".claude" / "skills").exists()
        assert not (project / ".claude" / "hooks").exists()
        assert not (project / ".claude" / "settings.local.json").exists()

    def test_init_is_idempotent(self, runner: CliRunner, project: Path):
        runner.invoke(main, ["init", "--yes"])
        marker = project / ".claude" / "sprint-config.yaml"
        marker.write_text(marker.read_text().replace("current_sprint: 1", "current_sprint: 7"))
        result = runner.invoke(main, ["init", "--yes"])
        assert result.exit_code == 0
        assert "current_sprint: 7" in marker.read_text()  # not clobbered without --force
        settings = json.loads((project / ".claude" / "settings.local.json").read_text())
        assert len(settings["hooks"]["PostToolUse"]) == 1  # no duplicate hook entry

    def test_detected_commands_land_in_config(self, runner: CliRunner, project: Path):
        runner.invoke(main, ["init", "--yes"])
        text = (project / ".claude" / "sprint-config.yaml").read_text()
        assert 'test_command: "pytest tests/ -v"' in text
        assert "language: python" in text


class TestInstallSkillsStillWorks:
    def test_install_skills_unchanged(self, runner: CliRunner, project: Path):
        result = runner.invoke(main, ["install-skills"])
        assert result.exit_code == 0
        assert "Installed" in result.output
        assert (project / ".claude" / "skills" / "cli-reference").is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_init_cli.py -v`
Expected: `TestInit` tests FAIL (`Error: No such command 'init'`); `TestInstallSkillsStillWorks` PASSES (guards the refactor).

- [ ] **Step 3: Add `install_skills_from_package` and `CLAUDE_MD_BLOCK` to scaffold.py**

Append to `src/agile_backlog/scaffold.py`:

```python
CLAUDE_MD_BLOCK = """\
## Commands

- **CI:** `{ci_command}`
- **Sprint config:** `.claude/sprint-config.yaml`

## Design Principles

- Research first, design second, code third
- Code review before every merge
- DRY, YAGNI, TDD

## Context

| File | Purpose |
|---|---|
| `.claude/sprint-config.yaml` | Commands, paths, sprint settings |
| `backlog/*.yaml` | Backlog items (single source of truth) |
"""


def install_skills_from_package(target_dir: Path, force: bool = False) -> tuple[list[str], list[str]]:
    skills_src = PACKAGE_DIR / "bundled_skills"
    if not skills_src.exists():
        raise FileNotFoundError("bundled skills not found in package")
    target_dir.mkdir(parents=True, exist_ok=True)
    installed, skipped = [], []
    for skill_dir in sorted(skills_src.iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = target_dir / skill_dir.name
        if dest.exists() and not force:
            skipped.append(skill_dir.name)
            continue
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        installed.append(skill_dir.name)
    return installed, skipped
```

- [ ] **Step 4: Refactor `install-skills` in cli.py to use the helper**

Replace the body of `install_skills` (cli.py lines 422-455) with:

```python
@main.command("install-skills")
@click.option("--target", default=".claude/skills", help="Target directory for skills.")
@click.option("--force", is_flag=True, help="Overwrite existing skills.")
def install_skills(target: str, force: bool):
    """Install bundled sprint skills into the current project."""
    from agile_backlog import scaffold

    try:
        installed, skipped = scaffold.install_skills_from_package(Path(target), force)
    except FileNotFoundError:
        raise SystemExit("Error: bundled skills not found in package.")

    if installed:
        click.echo(f"Installed {len(installed)} skill(s): {', '.join(installed)}")
    if skipped:
        click.echo(f"Skipped {len(skipped)} existing skill(s): {', '.join(skipped)} (use --force to overwrite)")
    if not installed and not skipped:
        click.echo("No skills found to install.")
```

- [ ] **Step 5: Add the `init` command to cli.py** (place after `install_skills`)

```python
@main.command()
@click.option("--config-only", is_flag=True, help="Scaffold config, dirs, and gitignore only (for plugin users).")
@click.option("--force", is_flag=True, help="Overwrite existing sprint-config and hook script.")
@click.option("--yes", is_flag=True, help="Accept detected defaults without prompting.")
def init(config_only: bool, force: bool, yes: bool):
    """Set up agile-backlog in the current project — sprint-config, skills, hooks."""
    from agile_backlog import scaffold

    root = Path.cwd()
    values = scaffold.detect_project(root)
    if not yes:
        values["project_name"] = click.prompt("Project name", default=values["project_name"])
        values["language"] = click.prompt("Language", default=values["language"] or "python")
        values["test_command"] = click.prompt("Test command", default=values["test_command"] or "pytest tests/ -v")
        values["lint_command"] = click.prompt("Lint command", default=values["lint_command"] or "")
        values["format_command"] = click.prompt("Format command", default=values["format_command"] or "")
    else:
        values["language"] = values["language"] or "python"
        values["test_command"] = values["test_command"] or "pytest tests/ -v"
        values["lint_command"] = values["lint_command"] or ""
        values["format_command"] = values["format_command"] or ""

    default_ci = " && ".join(c for c in (values["lint_command"], values["test_command"]) if c)
    values["ci_command"] = default_ci if yes else click.prompt("CI command", default=default_ci)

    wrote_config = scaffold.scaffold_sprint_config(root, values, force)
    click.echo(f"{'Wrote' if wrote_config else 'Kept existing'} .claude/sprint-config.yaml")
    created = scaffold.ensure_doc_dirs(root)
    if created:
        click.echo(f"Created dirs: {', '.join(created)}")
    if scaffold.ensure_gitignore(root):
        click.echo("Added .claude/context-logs/ to .gitignore")

    if not config_only:
        installed, skipped = scaffold.install_skills_from_package(root / ".claude" / "skills", force)
        if installed:
            click.echo(f"Installed {len(installed)} skill(s)")
        if skipped:
            click.echo(f"Skipped {len(skipped)} existing skill(s)")
        if scaffold.install_hooks(root, force):
            click.echo("Installed .claude/hooks/post-tool-logger.sh")
        if scaffold.merge_settings_hooks(root):
            click.echo("Wired PostToolUse logging hook in .claude/settings.local.json")
        else:
            click.echo("PostToolUse logging hook already wired")

    click.echo("\nAdd this to your CLAUDE.md (init never edits it for you):\n")
    click.echo(scaffold.CLAUDE_MD_BLOCK.format(ci_command=values["ci_command"] or "<your CI command>"))
    click.echo("Done. Next: import your existing tasks, then run /sprint-start.")
```

- [ ] **Step 6: Run the new tests, then the full suite**

Run: `.venv/bin/pytest tests/test_init_cli.py tests/test_cli.py tests/test_scaffold.py -v`
Expected: all PASS (install-skills behavior unchanged, init works).

- [ ] **Step 7: Commit**

```bash
git add src/agile_backlog/scaffold.py src/agile_backlog/cli.py tests/test_init_cli.py
git commit -m "feat: agile-backlog init — one-step project setup (config + skills + hooks)"
```

---

### Task 6: Full plugin + sync script

**Files:**
- Create: `scripts/sync_plugin.py`
- Create: `plugin/hooks/hooks.json` (authored)
- Create: `plugin/commands/sprint-start.md`, `sprint-execute.md`, `sprint-end.md`, `sprint-plan-next.md`, `plan.md`, `fix-bug.md`, `report-bug.md`, `document.md` (authored; `plugin/commands/backlog.md` already exists — keep)
- Modify: `plugin/plugin.json`
- Create: `tests/test_plugin_sync.py`
- Generated by sync: `plugin/skills/*` (9 skills), `plugin/hooks/scripts/post-tool-logger.sh`

**Interfaces:**
- Consumes: `bundled_skills/` and `bundled_hooks/` as canonical (Tasks 1-2 layout).
- Produces: `scripts/sync_plugin.py` with `sync(root: Path) -> list[str]` (list of changed paths) and `check(root: Path) -> list[str]` (list of drifted paths, empty = in sync); CLI `python scripts/sync_plugin.py [--check]` exiting 1 on drift. Task 7's CI gate relies on `tests/test_plugin_sync.py`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_plugin_sync.py`:

```python
"""Tests for scripts/sync_plugin.py — canonical → plugin mirroring and drift check."""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

spec = importlib.util.spec_from_file_location("sync_plugin", REPO_ROOT / "scripts" / "sync_plugin.py")
sync_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_plugin)


def _make_tree(root: Path) -> Path:
    skills = root / "src" / "agile_backlog" / "bundled_skills" / "demo-skill"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\nname: demo-skill\n---\nbody\n")
    hooks = root / "src" / "agile_backlog" / "bundled_hooks"
    hooks.mkdir(parents=True)
    (hooks / "post-tool-logger.sh").write_text("#!/usr/bin/env bash\necho hook\n")
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".claude" / "hooks" / "post-tool-logger.sh").write_text("#!/usr/bin/env bash\necho hook\n")
    (root / "plugin" / "skills" / "backlog").mkdir(parents=True)  # plugin-only skill, preserved
    (root / "plugin" / "skills" / "backlog" / "SKILL.md").write_text("stub\n")
    return root


class TestSync:
    def test_sync_mirrors_and_check_passes(self, tmp_path: Path):
        root = _make_tree(tmp_path)
        changed = sync_plugin.sync(root)
        assert (root / "plugin" / "skills" / "demo-skill" / "SKILL.md").exists()
        assert (root / "plugin" / "hooks" / "scripts" / "post-tool-logger.sh").exists()
        assert (root / "plugin" / "skills" / "backlog" / "SKILL.md").exists()  # preserved
        assert changed
        assert sync_plugin.check(root) == []
        assert sync_plugin.sync(root) == []  # idempotent

    def test_check_detects_drift_and_stale_skill(self, tmp_path: Path):
        root = _make_tree(tmp_path)
        sync_plugin.sync(root)
        (root / "plugin" / "skills" / "demo-skill" / "SKILL.md").write_text("tampered\n")
        assert sync_plugin.check(root) != []
        sync_plugin.sync(root)
        stale = root / "plugin" / "skills" / "removed-skill"
        stale.mkdir()
        (stale / "SKILL.md").write_text("x\n")
        assert sync_plugin.check(root) != []

    def test_check_detects_dogfood_hook_drift(self, tmp_path: Path):
        root = _make_tree(tmp_path)
        sync_plugin.sync(root)
        (root / ".claude" / "hooks" / "post-tool-logger.sh").write_text("#!/usr/bin/env bash\necho drift\n")
        assert sync_plugin.check(root) != []


class TestRepoIsInSync:
    def test_repo_plugin_matches_canonical(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "sync_plugin.py"), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"plugin/ drifted from canonical:\n{result.stdout}{result.stderr}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_plugin_sync.py -v`
Expected: FAIL at import — `scripts/sync_plugin.py` doesn't exist.

- [ ] **Step 3: Implement the sync script**

Create `scripts/sync_plugin.py`:

```python
"""Mirror canonical package content into plugin/ (and the dogfood .claude hook copy).

Canonical sources:
  src/agile_backlog/bundled_skills/  -> plugin/skills/        (plugin-only skills in KEEP are preserved)
  src/agile_backlog/bundled_hooks/   -> plugin/hooks/scripts/
  src/agile_backlog/bundled_hooks/post-tool-logger.sh -> .claude/hooks/post-tool-logger.sh (dogfood copy)

Usage: python scripts/sync_plugin.py [--check]
  --check: exit 1 listing drifted paths instead of writing.
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

KEEP = {"backlog"}  # plugin-only skills, not synced from the package


def _pairs(root: Path) -> list[tuple[Path, Path]]:
    pkg = root / "src" / "agile_backlog"
    pairs = []
    for skill in sorted((pkg / "bundled_skills").iterdir()):
        if skill.is_dir():
            pairs.append((skill, root / "plugin" / "skills" / skill.name))
    for hook in sorted((pkg / "bundled_hooks").iterdir()):
        if hook.is_file():
            pairs.append((hook, root / "plugin" / "hooks" / "scripts" / hook.name))
            pairs.append((hook, root / ".claude" / "hooks" / hook.name))
    return pairs


def _stale_skills(root: Path) -> list[Path]:
    plugin_skills = root / "plugin" / "skills"
    if not plugin_skills.exists():
        return []
    canonical = {p.name for p in (root / "src" / "agile_backlog" / "bundled_skills").iterdir() if p.is_dir()}
    return [p for p in sorted(plugin_skills.iterdir()) if p.is_dir() and p.name not in canonical | KEEP]


def _files_under(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file())


def _differs(src: Path, dest: Path) -> bool:
    if src.is_file():
        return not dest.exists() or not filecmp.cmp(src, dest, shallow=False)
    src_files = _files_under(src)
    if not dest.exists():
        return True
    if [p.relative_to(src) for p in src_files] != [p.relative_to(dest) for p in _files_under(dest)]:
        return True
    return any(not filecmp.cmp(f, dest / f.relative_to(src), shallow=False) for f in src_files)


def check(root: Path) -> list[str]:
    drifted = [str(dest.relative_to(root)) for src, dest in _pairs(root) if _differs(src, dest)]
    drifted += [f"{p.relative_to(root)} (stale — not in bundled_skills)" for p in _stale_skills(root)]
    return drifted


def sync(root: Path) -> list[str]:
    changed = []
    for src, dest in _pairs(root):
        if not _differs(src, dest):
            continue
        if src.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        else:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        changed.append(str(dest.relative_to(root)))
    for stale in _stale_skills(root):
        shutil.rmtree(stale)
        changed.append(f"{stale.relative_to(root)} (removed)")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without writing; exit 1 if drifted.")
    args = parser.parse_args()
    root = Path(__file__).parent.parent
    if args.check:
        drifted = check(root)
        if drifted:
            print("plugin/ is out of sync — run: python scripts/sync_plugin.py")
            for path in drifted:
                print(f"  {path}")
            return 1
        print("plugin/ is in sync.")
        return 0
    changed = sync(root)
    print(f"Synced {len(changed)} path(s)." if changed else "Already in sync.")
    for path in changed:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Author the plugin hooks.json**

Create `plugin/hooks/hooks.json` (single pipe-regex matcher; `${CLAUDE_PLUGIN_ROOT}` resolves to the installed plugin root):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Read|Grep|Glob|Bash|WebFetch|Agent|Edit|Write|Skill",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}\"/hooks/scripts/post-tool-logger.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Author the plugin command files**

Commands are namespaced on install (`/agile-backlog:sprint-start`). Create each file in `plugin/commands/`:

`plugin/commands/sprint-start.md`:
```markdown
---
description: Initialize a new sprint — scope selection, task specs, sprint branch
---

Initialize a new sprint. Use the sprint-start skill to walk through the sprint start checklist, select scope, write task specs to YAML items, and create a sprint branch. Arguments: $ARGUMENTS
```

`plugin/commands/sprint-execute.md`:
```markdown
---
description: Execute current sprint items with TDD, CI gates, and code review
---

Execute current sprint items. Use the sprint-execute skill to read doing items, dispatch subagents to implement each task, run CI after each, and mark items as review phase. Arguments: $ARGUMENTS
```

`plugin/commands/sprint-end.md`:
```markdown
---
description: Close the current sprint — handover doc, status updates, cleanup
---

Close the current sprint. Use the sprint-end skill to read status from YAML items, write the handover doc, update project context, and clean up branches. Arguments: $ARGUMENTS
```

`plugin/commands/sprint-plan-next.md`:
```markdown
---
description: Pre-plan next sprint scope while the current sprint runs
---

Pre-plan next sprint scope. Use the sprint-plan-next skill to review untagged backlog items, tag candidates, and balance capacity. Arguments: $ARGUMENTS
```

`plugin/commands/plan.md`:
```markdown
---
description: Run planning processes — inception, roadmap review, sprint allocation, scope analysis
---

Run planning processes. Use the plan skill to analyze project scope, review roadmaps, or balance sprint allocation. Arguments: $ARGUMENTS
```

`plugin/commands/fix-bug.md`:
```markdown
---
description: Investigate and fix a bug from the backlog
---

Investigate and fix a bug. Use the fix-bug skill to load bug details from the backlog, diagnose root cause, implement fix after approval, run CI, and update item status. Pass a bug item ID as argument. Arguments: $ARGUMENTS
```

`plugin/commands/report-bug.md`:
```markdown
---
description: Report a bug — structured details, auto-created backlog item
---

Report a bug. Use the report-bug skill to gather structured details, create a backlog item, tag with the current sprint, and explore related code. Arguments: $ARGUMENTS
```

`plugin/commands/document.md`:
```markdown
---
description: Documentation processes — research, design, architecture, audit, runbook, update, review
---

Create and manage documentation. Use the document skill — modes: research, design, architecture, audit, runbook, update, review. Arguments: $ARGUMENTS
```

- [ ] **Step 6: Update plugin.json**

Replace `plugin/plugin.json` content (drop explicit `commands`/`skills` paths — auto-discovery covers `commands/`, `skills/`, and `hooks/hooks.json`):

```json
{
  "name": "agile-backlog",
  "version": "0.32.0",
  "description": "Kanban backlog management and sprint workflow for agentic development — sprint skills, slash commands, and context-logging hooks. Requires the agile-backlog CLI (pip install agile-backlog)."
}
```

- [ ] **Step 7: Run the sync, then all tests**

```bash
.venv/bin/python scripts/sync_plugin.py
```
Expected: reports synced paths — 9 skills into `plugin/skills/`, hook into `plugin/hooks/scripts/` (the `.claude/hooks/` copy should report only if it drifted).

Run: `.venv/bin/pytest tests/test_plugin_sync.py -v`
Expected: all PASS, including `TestRepoIsInSync` (this is the CI drift gate from now on).

- [ ] **Step 8: Commit**

```bash
git add scripts/sync_plugin.py plugin/ tests/test_plugin_sync.py
git commit -m "feat: full plugin (skills + hooks + commands) with canonical sync + drift check"
```

---

### Task 7: Rewrite ADOPTION.md and run full CI

**Files:**
- Modify: `docs/guides/ADOPTION.md` (replace §1, §3-§7; KEEP §2 "Import Existing Tasks" and §8 "Start Your First Sprint" as-is, renumber)

**Interfaces:**
- Consumes: `init` command behavior (Task 5), plugin channel (Task 6).
- Produces: final adoption doc; green CI.

- [ ] **Step 1: Rewrite the guide around the two paths**

Replace everything between the title block and current §2 with:

```markdown
# Adopting agile-backlog in an Existing Project

Instructions for a Claude Code agent to set up agile-backlog in a project that already has task tracking (KANBAN.md, TODO.md, or similar).

Two channels — pick one:

| | Pip-only | Plugin |
|---|---|---|
| 1 | `pip install agile-backlog` | `/plugin install agile-backlog` |
| 2 | `agile-backlog init` | `pip install agile-backlog` |
| 3 | import tasks (below) | `agile-backlog init --config-only`, then import tasks |

**Pip-only** installs skills and hooks into the project's `.claude/`. **Plugin** ships skills, slash commands (namespaced, e.g. `/agile-backlog:sprint-start`), and the context-logging hook via the plugin itself — `init --config-only` then only scaffolds `sprint-config.yaml`, doc dirs, and `.gitignore`.

## 1. Install and Initialize

```bash
pip install git+https://github.com/zbarbur/agile-backlog.git
# or: uv pip install git+https://github.com/zbarbur/agile-backlog.git

agile-backlog init            # pip-only path (add --config-only on the plugin path)
```

`init` detects your toolchain (pyproject.toml / package.json), prompts for test/lint/CI commands (accept defaults with `--yes`), then:

- writes `.claude/sprint-config.yaml` (skips if present; `--force` overwrites)
- creates `docs/sprints/`, `docs/process/`, `docs/superpowers/{specs,plans}/`
- adds `.claude/context-logs/` to `.gitignore`
- installs the 9 sprint skills into `.claude/skills/` (pip-only path)
- installs `.claude/hooks/post-tool-logger.sh` and wires it into `.claude/settings.local.json` `PostToolUse` (pip-only path)
- prints a suggested CLAUDE.md process section — paste it in yourself; init never edits CLAUDE.md

Verify:

```bash
agile-backlog list                          # "No items found."
grep current_sprint .claude/sprint-config.yaml
agile-backlog context-report                # after a few Claude Code tool calls
```
```

Then: keep current §2 (Import Existing Tasks) verbatim as new §2. Delete current §3 (Set Up Sprint Methodology), §4 (Configure Hooks), §5 (Verify Setup), and §6 (Install Sprint Skills) — `init` now does all of it; fold the §4.2 statusline JSON snippet into a short "Optional: statusline" subsection at the end of new §1. Keep §7 (Updating) as new §3, adding after the existing upgrade text: "Plugin users: update via `/plugin` instead; `init --config-only` never needs re-running." Keep §8 (Start Your First Sprint) as new §4.

- [ ] **Step 2: Verify doc consistency**

Run: `grep -n "install-skills\|Section\|§" docs/guides/ADOPTION.md`
Expected: no references to removed sections; `install-skills` may appear only in the Updating section (`install-skills --force` after upgrade is still the skill-refresh mechanism for pip users).

- [ ] **Step 3: Run full CI**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
Expected: all green. If ruff format complains about new files, run `.venv/bin/ruff format .` and re-check.

- [ ] **Step 4: Commit**

```bash
git add docs/guides/ADOPTION.md
git commit -m "docs: rewrite ADOPTION.md around init + plugin two-channel adoption"
```

---

## Self-Review Notes

- **Spec coverage:** canonical hook bundling (T1), detection (T2), config/dirs/gitignore (T3), hooks+merge (T4), init + install-skills refactor + CLAUDE.md print (T5), plugin + sync + CI drift gate (T6), ADOPTION rewrite (T7). Spec's open questions resolved: hooks.json uses one pipe-regex matcher with `${CLAUDE_PLUGIN_ROOT}`; plugin commands are authored one-liners (no sync needed).
- **Deliberate exclusions (YAGNI, per spec):** no marketplace.json, no MCP server, no CLAUDE.md editing, no `--apply`-style config migration.
- **Type consistency check:** `install_skills_from_package(target_dir: Path, force: bool) -> tuple[list[str], list[str]]` used identically in T5 steps 3-5; `sync/check(root: Path) -> list[str]` used identically in T6 steps 1 and 3.
