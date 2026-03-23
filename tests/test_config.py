import yaml

from agile_backlog.config import get_current_sprint, set_current_sprint


def test_get_current_sprint_from_sprint_config(tmp_path, monkeypatch):
    """sprint-config.yaml is the primary source."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("current_sprint: 16\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    monkeypatch.setattr("agile_backlog.config._config_path", lambda: tmp_path / "nonexistent.yaml")
    assert get_current_sprint() == 16


def test_get_current_sprint_fallback_to_agile_backlog_yaml(tmp_path, monkeypatch):
    """Falls back to .agile-backlog.yaml when sprint-config.yaml missing."""
    legacy = tmp_path / ".agile-backlog.yaml"
    legacy.write_text("current_sprint: 14\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: tmp_path / "nonexistent.yaml")
    monkeypatch.setattr("agile_backlog.config._config_path", lambda: legacy)
    assert get_current_sprint() == 14


def test_get_current_sprint_none_when_no_config(tmp_path, monkeypatch):
    """Returns None when neither config file exists."""
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: tmp_path / "nope1.yaml")
    monkeypatch.setattr("agile_backlog.config._config_path", lambda: tmp_path / "nope2.yaml")
    assert get_current_sprint() is None


def test_set_current_sprint_writes_to_sprint_config(tmp_path, monkeypatch):
    """set_current_sprint writes to sprint-config.yaml, preserving other fields."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("project_name: test\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    set_current_sprint(17)
    data = yaml.safe_load(config.read_text())
    assert data["current_sprint"] == 17
    assert data["project_name"] == "test"
