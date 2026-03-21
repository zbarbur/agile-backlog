"""YAML file store for backlog items. Reads/writes backlog/*.yaml at git root."""

import subprocess
import warnings
from datetime import date
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
        raise RuntimeError("Not inside a git repository. Run this command from within a git repo.")
    return Path(result.stdout.strip())


def get_backlog_dir() -> Path:
    """Return the backlog/ directory path, creating it if needed."""
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


def item_exists(item_id: str) -> bool:
    """Check if a backlog item file exists."""
    return (get_backlog_dir() / f"{item_id}.yaml").exists()
