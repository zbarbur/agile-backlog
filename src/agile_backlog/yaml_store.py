"""YAML file store for backlog items. Reads/writes backlog/*.yaml at git root."""

import subprocess
import warnings
from datetime import date
from pathlib import Path

import yaml

from agile_backlog.models import BacklogItem

_backlog_dir_override: Path | None = None


def set_backlog_dir(path: Path | None) -> None:
    global _backlog_dir_override
    _backlog_dir_override = path


def _git_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Not inside a git repository. Run this command from within a git repo.")
    return Path(result.stdout.strip())


def get_backlog_dir() -> Path:
    if _backlog_dir_override is not None:
        _backlog_dir_override.mkdir(parents=True, exist_ok=True)
        return _backlog_dir_override
    backlog = _git_root() / "backlog"
    backlog.mkdir(exist_ok=True)
    return backlog


def save_item(item: BacklogItem) -> Path:
    """Write a BacklogItem to backlog/<id>.yaml. Updates the 'updated' date."""
    item.updated = date.today()
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
    raw.pop("id", None)
    return BacklogItem(id=item_id, **raw)


def load_all() -> list[BacklogItem]:
    """Load all backlog items. Skips files that fail to parse."""
    items = []
    for path in sorted(get_backlog_dir().glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text())
            if not isinstance(raw, dict):
                raise ValueError(f"Expected mapping, got {type(raw).__name__}")
            raw.pop("id", None)
            item_id = path.stem
            items.append(BacklogItem(id=item_id, **raw))
        except Exception as exc:
            warnings.warn(f"Skipping {path.name}: {exc}", stacklevel=2)
    return items


def delete_item(item_id: str) -> None:
    path = (get_backlog_dir() / f"{item_id}.yaml").resolve()
    if not path.is_relative_to(get_backlog_dir().resolve()):
        raise ValueError(f"Invalid item_id: {item_id!r}")
    if not path.exists():
        raise FileNotFoundError(f"No backlog item: {item_id}")
    path.unlink()


def item_exists(item_id: str) -> bool:
    return (get_backlog_dir() / f"{item_id}.yaml").exists()
