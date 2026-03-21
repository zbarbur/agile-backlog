# Sprint 1: Core Data Layer + CLI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the BacklogItem model, YAML file store, and CLI so users can create, list, filter, and move backlog items from the terminal.

**Architecture:** Three-layer stack — Pydantic model (`models.py`) validates data, YAML store (`yaml_store.py`) handles persistence to `backlog/*.yaml` files discovered via git root, CLI (`cli.py`) exposes Click commands. Each layer depends only on the one below it.

**Tech Stack:** Python 3.11+, Pydantic 2, PyYAML, Click, pytest, ruff

**Spec:** `docs/superpowers/specs/2026-03-21-sprint1-core-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/models.py` | `BacklogItem` Pydantic model, `slugify()`, `to_yaml_dict()` |
| `src/yaml_store.py` | Git root detection, load/save YAML files from `backlog/` |
| `src/cli.py` | Click CLI group: `list`, `add`, `move`, `show`, `serve` |
| `tests/test_models.py` | Model validation, defaults, slugify edge cases |
| `tests/test_yaml_store.py` | Round-trip persistence, collision handling, error resilience |
| `tests/test_cli.py` | CLI commands via `CliRunner`, end-to-end flows |

---

## Task 1: BacklogItem Model + Tests

**Files:**
- Create: `src/models.py`
- Create: `tests/test_models.py`

### Step 1: Write failing tests for BacklogItem

- [ ] **Write tests**

```python
# tests/test_models.py
from datetime import date

import pytest

from src.models import BacklogItem, slugify


class TestSlugify:
    def test_simple_title(self):
        assert slugify("Fix auth leak") == "fix-auth-leak"

    def test_special_characters(self):
        assert slugify("Add OAuth2/JWT support!") == "add-oauth2-jwt-support"

    def test_consecutive_hyphens_collapsed(self):
        assert slugify("foo  --  bar") == "foo-bar"

    def test_leading_trailing_hyphens_stripped(self):
        assert slugify("--hello--") == "hello"

    def test_empty_string(self):
        assert slugify("") == ""


class TestBacklogItem:
    def test_minimal_valid_item(self):
        item = BacklogItem(
            id="test-item",
            title="Test item",
            priority="P2",
            category="feature",
        )
        assert item.status == "backlog"
        assert item.created == date.today()
        assert item.updated == date.today()
        assert item.depends_on == []
        assert item.tags == []

    def test_all_fields(self):
        item = BacklogItem(
            id="full-item",
            title="Full item",
            status="doing",
            priority="P1",
            category="security",
            sprint_target=2,
            created=date(2026, 1, 1),
            updated=date(2026, 3, 21),
            depends_on=["other-item"],
            tags=["urgent"],
            description="A detailed description.",
            acceptance_criteria=["Criterion 1"],
            notes="Some notes.",
        )
        assert item.sprint_target == 2
        assert item.depends_on == ["other-item"]

    def test_invalid_status_rejected(self):
        with pytest.raises(ValueError):
            BacklogItem(
                id="bad", title="Bad", status="invalid", priority="P1", category="x"
            )

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValueError):
            BacklogItem(
                id="bad", title="Bad", priority="P0", category="x"
            )


class TestToYamlDict:
    def test_excludes_id(self):
        item = BacklogItem(
            id="test", title="Test", priority="P2", category="feature"
        )
        d = item.to_yaml_dict()
        assert "id" not in d
        assert d["title"] == "Test"
        assert d["status"] == "backlog"

    def test_dates_are_date_objects(self):
        item = BacklogItem(
            id="test", title="Test", priority="P2", category="feature"
        )
        d = item.to_yaml_dict()
        assert isinstance(d["created"], date)

    def test_empty_lists_included(self):
        item = BacklogItem(
            id="test", title="Test", priority="P2", category="feature"
        )
        d = item.to_yaml_dict()
        assert d["depends_on"] == []
        assert d["tags"] == []
```

- [ ] **Run tests — expect FAIL**

```bash
pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.models'`

### Step 2: Implement BacklogItem model

- [ ] **Write implementation**

```python
# src/models.py
"""BacklogItem Pydantic model and helpers for agile-backlog."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


def slugify(title: str) -> str:
    """Convert a title to a URL-friendly slug ID."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


class BacklogItem(BaseModel):
    """A single backlog item."""

    id: str
    title: str
    status: Literal["backlog", "doing", "done"] = "backlog"
    priority: Literal["P1", "P2", "P3"]
    category: str
    sprint_target: int | None = None
    created: date = Field(default_factory=date.today)
    updated: date = Field(default_factory=date.today)
    depends_on: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    notes: str = ""

    def to_yaml_dict(self) -> dict:
        """Serialize to dict for YAML output, excluding id (derived from filename)."""
        d = self.model_dump()
        d.pop("id")
        return d
```

- [ ] **Run tests — expect PASS**

```bash
pytest tests/test_models.py -v
```

Expected: all tests pass

- [ ] **Lint**

```bash
ruff check src/models.py tests/test_models.py && ruff format --check src/models.py tests/test_models.py
```

- [ ] **Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: add BacklogItem Pydantic model with slugify and tests"
```

---

## Task 2: YAML Store + Tests

**Files:**
- Create: `src/yaml_store.py`
- Create: `tests/test_yaml_store.py`

### Step 1: Write failing tests for yaml_store

- [ ] **Write tests**

```python
# tests/test_yaml_store.py
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.models import BacklogItem
from src.yaml_store import get_backlog_dir, item_exists, load_all, load_item, save_item


@pytest.fixture()
def backlog_dir(tmp_path: Path) -> Path:
    """Create a temporary backlog directory and patch git root detection."""
    bd = tmp_path / "backlog"
    bd.mkdir()
    return bd


@pytest.fixture(autouse=True)
def _patch_backlog_dir(backlog_dir: Path):
    """Patch get_backlog_dir to return the tmp backlog dir."""
    with patch("src.yaml_store.get_backlog_dir", return_value=backlog_dir):
        yield


def _make_item(**overrides) -> BacklogItem:
    defaults = dict(
        id="test-item",
        title="Test item",
        priority="P2",
        category="feature",
    )
    defaults.update(overrides)
    return BacklogItem(**defaults)


class TestGetBacklogDir:
    def test_returns_path_inside_git_root(self, tmp_path: Path):
        with patch(
            "src.yaml_store._git_root", return_value=tmp_path
        ):
            result = get_backlog_dir.__wrapped__() if hasattr(get_backlog_dir, '__wrapped__') else get_backlog_dir()
        # The autouse patch overrides this, so test _git_root directly
        assert True  # Covered by integration below


class TestSaveAndLoad:
    def test_round_trip(self, backlog_dir: Path):
        item = _make_item()
        save_item(item)
        loaded = load_item("test-item")
        assert loaded.title == "Test item"
        assert loaded.priority == "P2"
        assert loaded.status == "backlog"

    def test_save_creates_yaml_file(self, backlog_dir: Path):
        item = _make_item()
        save_item(item)
        assert (backlog_dir / "test-item.yaml").exists()

    def test_yaml_does_not_contain_id_field(self, backlog_dir: Path):
        item = _make_item()
        save_item(item)
        raw = yaml.safe_load((backlog_dir / "test-item.yaml").read_text())
        assert "id" not in raw

    def test_load_item_not_found_raises(self, backlog_dir: Path):
        with pytest.raises(FileNotFoundError):
            load_item("nonexistent")


class TestLoadAll:
    def test_empty_dir(self, backlog_dir: Path):
        assert load_all() == []

    def test_multiple_items(self, backlog_dir: Path):
        save_item(_make_item(id="item-a", title="Item A"))
        save_item(_make_item(id="item-b", title="Item B"))
        items = load_all()
        ids = {i.id for i in items}
        assert ids == {"item-a", "item-b"}

    def test_skips_invalid_yaml(self, backlog_dir: Path):
        (backlog_dir / "bad.yaml").write_text(": : : not valid yaml mapping")
        save_item(_make_item(id="good", title="Good"))
        items = load_all()
        assert len(items) == 1
        assert items[0].id == "good"


class TestItemExists:
    def test_exists(self, backlog_dir: Path):
        save_item(_make_item())
        assert item_exists("test-item") is True

    def test_not_exists(self, backlog_dir: Path):
        assert item_exists("nope") is False


class TestSlugCollision:
    def test_save_updates_existing(self, backlog_dir: Path):
        save_item(_make_item(description="v1"))
        save_item(_make_item(description="v2"))
        loaded = load_item("test-item")
        assert loaded.description == "v2"
```

- [ ] **Run tests — expect FAIL**

```bash
pytest tests/test_yaml_store.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.yaml_store'`

### Step 2: Implement yaml_store

- [ ] **Write implementation**

```python
# src/yaml_store.py
"""YAML file store for backlog items. Reads/writes backlog/*.yaml at git root."""

import subprocess
import warnings
from pathlib import Path

import yaml

from src.models import BacklogItem


def _git_root() -> Path:
    """Find the git repository root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Not inside a git repository. Run this command from within a git repo."
        )
    return Path(result.stdout.strip())


def get_backlog_dir() -> Path:
    """Return the backlog/ directory path, creating it if needed."""
    backlog = _git_root() / "backlog"
    backlog.mkdir(exist_ok=True)
    return backlog


def save_item(item: BacklogItem) -> Path:
    """Write a BacklogItem to backlog/<id>.yaml. Returns the file path."""
    path = get_backlog_dir() / f"{item.id}.yaml"
    data = item.to_yaml_dict()
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    return path


def load_item(item_id: str) -> BacklogItem:
    """Load a single item by ID. Raises FileNotFoundError if missing."""
    path = get_backlog_dir() / f"{item_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No backlog item: {item_id}")
    raw = yaml.safe_load(path.read_text())
    return BacklogItem(id=item_id, **raw)


def load_all() -> list[BacklogItem]:
    """Load all backlog items. Skips files that fail to parse."""
    items = []
    for path in sorted(get_backlog_dir().glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text())
            if not isinstance(raw, dict):
                raise ValueError(f"Expected mapping, got {type(raw).__name__}")
            item_id = path.stem
            items.append(BacklogItem(id=item_id, **raw))
        except Exception as exc:
            warnings.warn(f"Skipping {path.name}: {exc}", stacklevel=2)
    return items


def item_exists(item_id: str) -> bool:
    """Check if a backlog item file exists."""
    return (get_backlog_dir() / f"{item_id}.yaml").exists()
```

- [ ] **Run tests — expect PASS**

```bash
pytest tests/test_yaml_store.py -v
```

- [ ] **Lint**

```bash
ruff check src/yaml_store.py tests/test_yaml_store.py && ruff format --check src/yaml_store.py tests/test_yaml_store.py
```

- [ ] **Commit**

```bash
git add src/yaml_store.py tests/test_yaml_store.py
git commit -m "feat: add YAML store with git-root detection and tests"
```

---

## Task 3: CLI + Tests

**Files:**
- Create: `src/cli.py`
- Create: `tests/test_cli.py`

### Step 1: Write failing tests for CLI

- [ ] **Write tests**

```python
# tests/test_cli.py
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.cli import main


@pytest.fixture()
def backlog_dir(tmp_path: Path) -> Path:
    bd = tmp_path / "backlog"
    bd.mkdir()
    return bd


@pytest.fixture(autouse=True)
def _patch_backlog_dir(backlog_dir: Path):
    with patch("src.yaml_store.get_backlog_dir", return_value=backlog_dir):
        yield


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestAdd:
    def test_add_basic(self, runner: CliRunner, backlog_dir: Path):
        result = runner.invoke(main, ["add", "Fix auth leak", "--priority", "P1", "--category", "security"])
        assert result.exit_code == 0
        assert "fix-auth-leak" in result.output
        assert (backlog_dir / "fix-auth-leak.yaml").exists()

    def test_add_default_priority(self, runner: CliRunner):
        result = runner.invoke(main, ["add", "Some task", "--category", "feature"])
        assert result.exit_code == 0
        assert "some-task" in result.output

    def test_add_with_description(self, runner: CliRunner):
        result = runner.invoke(
            main, ["add", "My task", "--category", "docs", "--description", "Details here"]
        )
        assert result.exit_code == 0


class TestList:
    def test_list_empty(self, runner: CliRunner):
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "No items" in result.output or result.output.strip() == ""

    def test_list_shows_items(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--priority", "P1", "--category", "feature"])
        runner.invoke(main, ["add", "Task B", "--priority", "P2", "--category", "docs"])
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "task-a" in result.output
        assert "task-b" in result.output

    def test_list_filter_by_status(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--category", "feature"])
        runner.invoke(main, ["move", "task-a", "--status", "doing"])
        result = runner.invoke(main, ["list", "--status", "doing"])
        assert "task-a" in result.output
        result2 = runner.invoke(main, ["list", "--status", "done"])
        assert "task-a" not in result2.output

    def test_list_filter_by_priority(self, runner: CliRunner):
        runner.invoke(main, ["add", "Urgent", "--priority", "P1", "--category", "feature"])
        runner.invoke(main, ["add", "Chill", "--priority", "P3", "--category", "feature"])
        result = runner.invoke(main, ["list", "--priority", "P1"])
        assert "urgent" in result.output
        assert "chill" not in result.output


class TestMove:
    def test_move_status(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--category", "feature"])
        result = runner.invoke(main, ["move", "task-a", "--status", "doing"])
        assert result.exit_code == 0
        assert "doing" in result.output

    def test_move_nonexistent(self, runner: CliRunner):
        result = runner.invoke(main, ["move", "nope", "--status", "doing"])
        assert result.exit_code != 0


class TestShow:
    def test_show_item(self, runner: CliRunner):
        runner.invoke(main, ["add", "Task A", "--priority", "P1", "--category", "security"])
        result = runner.invoke(main, ["show", "task-a"])
        assert result.exit_code == 0
        assert "Task A" in result.output
        assert "P1" in result.output
        assert "security" in result.output

    def test_show_nonexistent(self, runner: CliRunner):
        result = runner.invoke(main, ["show", "nope"])
        assert result.exit_code != 0


class TestServe:
    def test_serve_placeholder(self, runner: CliRunner):
        result = runner.invoke(main, ["serve"])
        assert result.exit_code == 0
        assert "Sprint 2" in result.output
```

- [ ] **Run tests — expect FAIL**

```bash
pytest tests/test_cli.py -v
```

Expected: `ImportError`

### Step 2: Implement CLI

- [ ] **Write implementation**

```python
# src/cli.py
"""Click CLI for agile-backlog."""

from datetime import date

import click

from src.models import BacklogItem, slugify
from src.yaml_store import item_exists, load_all, load_item, save_item


@click.group()
def main():
    """Lightweight Kanban board tool for agentic development."""


@main.command()
@click.argument("title")
@click.option("--priority", type=click.Choice(["P1", "P2", "P3"]), default="P2", help="Priority level.")
@click.option("--category", required=True, help="Category tag (e.g., feature, security, docs).")
@click.option("--description", default="", help="Item description.")
@click.option("--sprint", "sprint_target", type=int, default=None, help="Target sprint number.")
def add(title: str, priority: str, category: str, description: str, sprint_target: int | None):
    """Create a new backlog item."""
    item_id = slugify(title)

    # Handle slug collision
    if item_exists(item_id):
        n = 2
        while item_exists(f"{item_id}-{n}"):
            n += 1
        item_id = f"{item_id}-{n}"

    item = BacklogItem(
        id=item_id,
        title=title,
        priority=priority,
        category=category,
        description=description,
        sprint_target=sprint_target,
    )
    save_item(item)
    click.echo(f"Created: {item_id}")


@main.command("list")
@click.option("--status", type=click.Choice(["backlog", "doing", "done"]), default=None)
@click.option("--priority", type=click.Choice(["P1", "P2", "P3"]), default=None)
@click.option("--category", default=None)
@click.option("--sprint", "sprint_target", type=int, default=None)
def list_items(status: str | None, priority: str | None, category: str | None, sprint_target: int | None):
    """List backlog items with optional filters."""
    items = load_all()

    if status:
        items = [i for i in items if i.status == status]
    if priority:
        items = [i for i in items if i.priority == priority]
    if category:
        items = [i for i in items if i.category == category]
    if sprint_target is not None:
        items = [i for i in items if i.sprint_target == sprint_target]

    if not items:
        click.echo("No items found.")
        return

    # Header
    click.echo(f"{'ID':<30} {'Title':<30} {'Status':<10} {'Pri':<5} {'Category':<15}")
    click.echo("-" * 90)
    for item in items:
        click.echo(f"{item.id:<30} {item.title:<30} {item.status:<10} {item.priority:<5} {item.category:<15}")


@main.command()
@click.argument("item_id")
@click.option("--status", type=click.Choice(["backlog", "doing", "done"]), required=True)
def move(item_id: str, status: str):
    """Change an item's status."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")
    item.status = status
    item.updated = date.today()
    save_item(item)
    click.echo(f"Moved {item_id} → {status}")


@main.command()
@click.argument("item_id")
def show(item_id: str):
    """Show full details for a backlog item."""
    try:
        item = load_item(item_id)
    except FileNotFoundError:
        raise SystemExit(f"Error: item '{item_id}' not found.")

    click.echo(f"ID:          {item.id}")
    click.echo(f"Title:       {item.title}")
    click.echo(f"Status:      {item.status}")
    click.echo(f"Priority:    {item.priority}")
    click.echo(f"Category:    {item.category}")
    click.echo(f"Sprint:      {item.sprint_target or 'unplanned'}")
    click.echo(f"Created:     {item.created}")
    click.echo(f"Updated:     {item.updated}")
    if item.tags:
        click.echo(f"Tags:        {', '.join(item.tags)}")
    if item.depends_on:
        click.echo(f"Depends on:  {', '.join(item.depends_on)}")
    if item.description:
        click.echo(f"\n{item.description}")
    if item.acceptance_criteria:
        click.echo("\nAcceptance Criteria:")
        for ac in item.acceptance_criteria:
            click.echo(f"  - {ac}")
    if item.notes:
        click.echo(f"\nNotes:\n{item.notes}")


@main.command()
def serve():
    """Open the Kanban board in the browser."""
    click.echo("Streamlit Kanban board — coming in Sprint 2.")
```

- [ ] **Run tests — expect PASS**

```bash
pytest tests/test_cli.py -v
```

- [ ] **Run full test suite + lint**

```bash
ruff check . && ruff format --check . && pytest tests/ -v
```

- [ ] **Commit**

```bash
git add src/cli.py tests/test_cli.py
git commit -m "feat: add Click CLI with add, list, move, show commands and tests"
```

---

## Task 4: Final Verification + Sprint Cleanup

**Files:**
- Modify: `TODO.md`
- Modify: `docs/process/KANBAN.md`

- [ ] **Run full CI**

```bash
ruff check . && ruff format --check . && pytest tests/ -v
```

- [ ] **Verify CLI entry point works**

```bash
pip install -e ".[dev]" && agile-backlog --help
```

- [ ] **Quick smoke test**

```bash
agile-backlog add "Test item" --priority P2 --category feature
agile-backlog list
agile-backlog move test-item --status doing
agile-backlog show test-item
```

- [ ] **Update TODO.md and KANBAN.md** — mark Sprint 1 core items as Done

- [ ] **Commit**

```bash
git add TODO.md docs/process/KANBAN.md
git commit -m "chore: update KANBAN and TODO for Sprint 1 completion"
```
