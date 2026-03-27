from agile_backlog.config import (
    get_archive_days,
    get_current_sprint,
    get_project_name,
    get_serve_port,
    get_version,
    set_archive_days,
    set_current_sprint,
)


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
    """set_current_sprint writes to sprint-config.yaml, preserving comments and other fields."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("# Project config\nproject_name: test\ncurrent_sprint: 16\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    set_current_sprint(17)
    text = config.read_text()
    assert "current_sprint: 17" in text
    assert "project_name: test" in text
    assert "# Project config" in text  # comments preserved


def test_get_archive_days_default(tmp_path, monkeypatch):
    """Returns 7 when no config exists."""
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: tmp_path / "nope.yaml")
    monkeypatch.setattr("agile_backlog.config._config_path", lambda: tmp_path / "nope2.yaml")
    assert get_archive_days() == 7


def test_get_archive_days_from_config(tmp_path, monkeypatch):
    """Reads archive_days from sprint-config.yaml."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("archive_days: 14\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    assert get_archive_days() == 14


def test_set_archive_days(tmp_path, monkeypatch):
    """Writes archive_days to sprint-config.yaml."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("current_sprint: 21\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    set_archive_days(30)
    text = config.read_text()
    assert "archive_days: 30" in text
    assert "current_sprint: 21" in text


def test_get_project_name_default(tmp_path, monkeypatch):
    """Returns 'agile-backlog' when no config exists."""
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: tmp_path / "nope.yaml")
    assert get_project_name() == "agile-backlog"


def test_get_project_name_from_config(tmp_path, monkeypatch):
    """Reads project_name from sprint-config.yaml."""
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("project_name: my-project\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    assert get_project_name() == "my-project"


def test_get_serve_port_default(tmp_path, monkeypatch):
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: tmp_path / "nope.yaml")
    assert get_serve_port() == 8501


def test_get_serve_port_from_config(tmp_path, monkeypatch):
    config = tmp_path / ".claude" / "sprint-config.yaml"
    config.parent.mkdir()
    config.write_text("serve_port: 9000\n")
    monkeypatch.setattr("agile_backlog.config._sprint_config_path", lambda: config)
    assert get_serve_port() == 9000


def test_get_version_returns_string():
    version = get_version()
    assert isinstance(version, str)
    assert "." in version  # semver-like
