"""Configuration management for agile-backlog."""

from pathlib import Path

import yaml


def _config_path() -> Path:
    from agile_backlog.yaml_store import _git_root

    return _git_root() / ".agile-backlog.yaml"


def get_current_sprint() -> int | None:
    path = _config_path()
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("current_sprint")


def set_current_sprint(sprint: int | None) -> None:
    path = _config_path()
    data = {}
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
    if sprint is None:
        data.pop("current_sprint", None)
    else:
        data["current_sprint"] = sprint
    path.write_text(yaml.dump(data, default_flow_style=False))
