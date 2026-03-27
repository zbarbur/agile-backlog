"""Configuration management for agile-backlog."""

import re
from pathlib import Path

import yaml


def _config_path() -> Path:
    from agile_backlog.yaml_store import _git_root

    return _git_root() / ".agile-backlog.yaml"


def _sprint_config_path() -> Path:
    from agile_backlog.yaml_store import _git_root

    return _git_root() / ".claude" / "sprint-config.yaml"


def get_current_sprint() -> int | None:
    # Try sprint-config.yaml first (new canonical location)
    sprint_config = _sprint_config_path()
    if sprint_config.exists():
        data = yaml.safe_load(sprint_config.read_text()) or {}
        if "current_sprint" in data:
            return data["current_sprint"]
    # Fallback to .agile-backlog.yaml (legacy)
    path = _config_path()
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text()) or {}
    return data.get("current_sprint")


def get_project_name() -> str:
    sprint_config = _sprint_config_path()
    if sprint_config.exists():
        data = yaml.safe_load(sprint_config.read_text()) or {}
        return data.get("project_name", "agile-backlog")
    return "agile-backlog"


def get_archive_days() -> int:
    sprint_config = _sprint_config_path()
    if sprint_config.exists():
        data = yaml.safe_load(sprint_config.read_text()) or {}
        return data.get("archive_days", 7)
    path = _config_path()
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
        return data.get("archive_days", 7)
    return 7


def set_archive_days(days: int) -> None:
    path = _sprint_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"archive_days: {days}\n")
        return
    text = path.read_text()
    if re.search(r"^archive_days:", text, re.MULTILINE):
        text = re.sub(r"^archive_days:.*$", f"archive_days: {days}", text, flags=re.MULTILINE)
    else:
        text = text.rstrip() + f"\narchive_days: {days}\n"
    path.write_text(text)


def get_serve_port() -> int:
    sprint_config = _sprint_config_path()
    if sprint_config.exists():
        data = yaml.safe_load(sprint_config.read_text()) or {}
        return data.get("serve_port", 8501)
    return 8501


def get_version() -> str:
    from agile_backlog import __version__

    return __version__


def set_current_sprint(sprint: int | None) -> None:
    path = _sprint_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"current_sprint: {sprint}\n")
        return
    text = path.read_text()
    if sprint is None:
        text = re.sub(r"^current_sprint:.*\n?", "", text, flags=re.MULTILINE)
    elif re.search(r"^current_sprint:", text, re.MULTILINE):
        text = re.sub(r"^current_sprint:.*$", f"current_sprint: {sprint}", text, flags=re.MULTILINE)
    else:
        text = text.rstrip() + f"\ncurrent_sprint: {sprint}\n"
    path.write_text(text)
