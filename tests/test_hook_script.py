"""Integration tests for .claude/hooks/post-tool-logger.sh — subprocess-based."""

import json
import subprocess
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / ".claude" / "hooks" / "post-tool-logger.sh"


def _run_hook(tool_input: dict, log_dir: Path, session_id: str = "test-session") -> subprocess.CompletedProcess:
    env = {
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "CONTEXT_LOG_DIR": str(log_dir),
        "CLAUDE_SESSION_ID": session_id,
    }
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _last_log_entry(log_dir: Path, session_id: str = "test-session") -> dict:
    log_file = log_dir / f"tools-{session_id}.jsonl"
    lines = [line.strip() for line in log_file.read_text().splitlines() if line.strip()]
    return json.loads(lines[-1])


class TestToolLogging:
    def test_read_tool(self, tmp_path):
        inp = {"tool_name": "Read", "tool_input": {"file_path": "/src/main.py", "offset": 10, "limit": 50}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Read"
        assert entry["file"] == "/src/main.py"
        assert entry["offset"] == 10
        assert entry["limit"] == 50

    def test_grep_tool(self, tmp_path):
        inp = {"tool_name": "Grep", "tool_input": {"pattern": "def main", "path": "src/", "glob": "*.py"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Grep"
        assert entry["pattern"] == "def main"
        assert entry["path"] == "src/"
        assert entry["glob"] == "*.py"

    def test_glob_tool(self, tmp_path):
        inp = {"tool_name": "Glob", "tool_input": {"pattern": "**/*.py", "path": "src/"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Glob"
        assert entry["pattern"] == "**/*.py"

    def test_bash_tool(self, tmp_path):
        inp = {"tool_name": "Bash", "tool_input": {"command": "pytest tests/ -v"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Bash"
        assert entry["command"] == "pytest tests/ -v"

    def test_bash_long_command_truncated(self, tmp_path):
        long_cmd = "x" * 300
        inp = {"tool_name": "Bash", "tool_input": {"command": long_cmd}}
        _run_hook(inp, tmp_path)
        entry = _last_log_entry(tmp_path)
        assert len(entry["command"]) == 200

    def test_webfetch_tool(self, tmp_path):
        inp = {"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "WebFetch"
        assert entry["url"] == "https://example.com"

    def test_agent_tool(self, tmp_path):
        inp = {"tool_name": "Agent", "tool_input": {"prompt": "Search for bugs"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Agent"
        assert entry["prompt"] == "Search for bugs"

    def test_edit_tool(self, tmp_path):
        inp = {"tool_name": "Edit", "tool_input": {"file_path": "/src/main.py", "replace_all": True}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Edit"
        assert entry["file"] == "/src/main.py"
        assert entry["replace_all"] is True

    def test_write_tool(self, tmp_path):
        inp = {"tool_name": "Write", "tool_input": {"file_path": "/src/new_file.py"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Write"
        assert entry["file"] == "/src/new_file.py"

    def test_skill_tool(self, tmp_path):
        inp = {"tool_name": "Skill", "tool_input": {"skill": "commit", "args": "-m 'fix'"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "Skill"
        assert entry["skill"] == "commit"
        assert entry["args"] == "-m 'fix'"

    def test_unknown_tool_logs_keys(self, tmp_path):
        inp = {"tool_name": "FutureTool", "tool_input": {"alpha": 1, "beta": "two"}}
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        entry = _last_log_entry(tmp_path)
        assert entry["tool"] == "FutureTool"
        assert set(entry["input_keys"]) == {"alpha", "beta"}


class TestRereadDetection:
    def test_reread_warning(self, tmp_path):
        inp = {"tool_name": "Read", "tool_input": {"file_path": "/src/main.py", "offset": 0, "limit": 100}}
        _run_hook(inp, tmp_path)
        result = _run_hook(inp, tmp_path)
        assert result.returncode == 0
        assert "Re-read detected" in result.stdout
        assert "/src/main.py" in result.stdout

    def test_no_warning_on_first_read(self, tmp_path):
        inp = {"tool_name": "Read", "tool_input": {"file_path": "/src/main.py", "offset": 0, "limit": 100}}
        result = _run_hook(inp, tmp_path)
        assert "Re-read detected" not in result.stdout


class TestMalformedInput:
    def test_empty_stdin(self, tmp_path):
        env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "CONTEXT_LOG_DIR": str(tmp_path), "CLAUDE_SESSION_ID": "test"}
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)], input="", capture_output=True, text=True, env=env, timeout=10
        )
        assert result.returncode == 0

    def test_invalid_json(self, tmp_path):
        env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "CONTEXT_LOG_DIR": str(tmp_path), "CLAUDE_SESSION_ID": "test"}
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)], input="not json", capture_output=True, text=True, env=env, timeout=10
        )
        assert result.returncode == 0

    def test_missing_tool_name(self, tmp_path):
        env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "CONTEXT_LOG_DIR": str(tmp_path), "CLAUDE_SESSION_ID": "test"}
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            input=json.dumps({"tool_input": {"file": "x.py"}}),
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert result.returncode == 0


class TestLogFileStructure:
    def test_entries_are_valid_jsonl(self, tmp_path):
        tools = [
            {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
            {"tool_name": "Grep", "tool_input": {"pattern": "foo"}},
            {"tool_name": "Edit", "tool_input": {"file_path": "b.py"}},
        ]
        for t in tools:
            _run_hook(t, tmp_path)

        log_file = tmp_path / "tools-test-session.jsonl"
        lines = [line for line in log_file.read_text().splitlines() if line.strip()]
        assert len(lines) == 3
        for line in lines:
            entry = json.loads(line)
            assert "ts" in entry
            assert "tool" in entry

    def test_timestamp_format(self, tmp_path):
        inp = {"tool_name": "Read", "tool_input": {"file_path": "a.py"}}
        _run_hook(inp, tmp_path)
        entry = _last_log_entry(tmp_path)
        assert entry["ts"].endswith("Z")
        assert "T" in entry["ts"]
