"""Tests for context_report module — parse_read_log, analyze_reads, analyze_tool_usage, generate_sprint_report."""

import json

from agile_backlog.context_report import (
    analyze_efficiency,
    analyze_reads,
    analyze_tool_usage,
    generate_sprint_report,
    parse_read_log,
)

# ---------------------------------------------------------------------------
# Task 2: parse_read_log
# ---------------------------------------------------------------------------


def test_parse_read_log_returns_entries(tmp_path):
    log = tmp_path / "tools-abc.jsonl"
    log.write_text(
        json.dumps({"tool": "Read", "file": "foo.py", "offset": 0, "limit": 100})
        + "\n"
        + json.dumps({"tool": "Read", "file": "bar.py", "offset": 0, "limit": 50})
        + "\n"
    )
    entries = parse_read_log(log)
    assert len(entries) == 2
    assert entries[0]["file"] == "foo.py"
    assert entries[1]["file"] == "bar.py"


def test_parse_read_log_empty_file(tmp_path):
    log = tmp_path / "tools-empty.jsonl"
    log.write_text("")
    assert parse_read_log(log) == []


def test_parse_read_log_skips_malformed_lines(tmp_path):
    log = tmp_path / "tools-mixed.jsonl"
    log.write_text(
        json.dumps({"tool": "Read", "file": "good.py", "offset": 0, "limit": 10})
        + "\n"
        + "NOT_JSON\n"
        + json.dumps({"tool": "Read", "file": "also_good.py", "offset": 0, "limit": 20})
        + "\n"
    )
    entries = parse_read_log(log)
    assert len(entries) == 2
    assert entries[0]["file"] == "good.py"
    assert entries[1]["file"] == "also_good.py"


def test_parse_read_log_multi_tool_entries(tmp_path):
    log = tmp_path / "tools-multi.jsonl"
    log.write_text(
        json.dumps({"tool": "Read", "file": "foo.py", "offset": 0, "limit": 100})
        + "\n"
        + json.dumps({"tool": "Grep", "pattern": "def main", "path": "src/"})
        + "\n"
        + json.dumps({"tool": "Bash", "command": "ls -la"})
        + "\n"
    )
    entries = parse_read_log(log)
    assert len(entries) == 3
    assert entries[0]["tool"] == "Read"
    assert entries[1]["tool"] == "Grep"
    assert entries[2]["tool"] == "Bash"


# ---------------------------------------------------------------------------
# Task 3: analyze_reads
# ---------------------------------------------------------------------------


def test_analyze_reads_counts():
    entries = [
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},
        {"tool": "Read", "file": "b.py", "offset": 0, "limit": 50},
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},  # re-read
    ]
    result = analyze_reads(entries)
    assert result["total_reads"] == 3
    assert result["unique_files"] == 2
    assert result["reread_count"] == 1
    assert result["reread_ratio"] == round(1 / 3, 2)


def test_analyze_reads_filters_non_read_tools():
    entries = [
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},
        {"tool": "Grep", "pattern": "foo", "path": "src/"},
        {"tool": "Read", "file": "b.py", "offset": 0, "limit": 50},
        {"tool": "Bash", "command": "ls"},
    ]
    result = analyze_reads(entries)
    assert result["total_reads"] == 2
    assert result["unique_files"] == 2
    assert result["reread_count"] == 0


def test_analyze_reads_top_files():
    entries = [{"tool": "Read", "file": "a.py", "offset": 0, "limit": 10}] * 5 + [
        {"tool": "Read", "file": "b.py", "offset": 0, "limit": 10}
    ] * 3
    result = analyze_reads(entries)
    assert result["top_files"][0]["file"] == "a.py"
    assert result["top_files"][0]["count"] == 5
    assert result["top_files"][1]["file"] == "b.py"
    assert result["top_files"][1]["count"] == 3


def test_analyze_reads_token_estimate():
    """limit=200 -> 200 lines x 4 tokens = 800 tokens."""
    entries = [{"tool": "Read", "file": "a.py", "offset": 0, "limit": 200}]
    result = analyze_reads(entries)
    assert result["estimated_tokens"] == 800


def test_analyze_reads_token_estimate_full_file():
    """limit=0 means full file — estimate 500 lines -> 2000 tokens."""
    entries = [{"tool": "Read", "file": "a.py", "offset": 0, "limit": 0}]
    result = analyze_reads(entries)
    assert result["estimated_tokens"] == 2000


def test_analyze_reads_wasteful_detection():
    """Same file, same offset/limit, no edit in between -> wasteful."""
    entries = [
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},  # wasteful: identical range
    ]
    result = analyze_reads(entries)
    assert len(result["wasteful_reads"]) == 1
    assert result["wasteful_reads"][0]["file"] == "a.py"


def test_analyze_reads_empty():
    result = analyze_reads([])
    assert result["total_reads"] == 0
    assert result["unique_files"] == 0
    assert result["reread_count"] == 0
    assert result["reread_ratio"] == 0.0
    assert result["estimated_tokens"] == 0
    assert result["top_files"] == []
    assert result["wasteful_reads"] == []


def test_analyze_reads_legacy_entries_without_tool_key():
    """Legacy log entries without 'tool' key default to Read."""
    entries = [
        {"file": "a.py", "offset": 0, "limit": 100},
        {"file": "b.py", "offset": 0, "limit": 50},
    ]
    result = analyze_reads(entries)
    assert result["total_reads"] == 2
    assert result["unique_files"] == 2


# ---------------------------------------------------------------------------
# Task: analyze_tool_usage
# ---------------------------------------------------------------------------


def test_analyze_tool_usage_counts():
    entries = [
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},
        {"tool": "Grep", "pattern": "foo", "path": "src/"},
        {"tool": "Read", "file": "b.py", "offset": 0, "limit": 50},
        {"tool": "Bash", "command": "ls"},
        {"tool": "Grep", "pattern": "bar", "path": "tests/"},
    ]
    result = analyze_tool_usage(entries)
    assert result["total_tool_calls"] == 5
    assert result["by_tool"]["Read"] == 2
    assert result["by_tool"]["Grep"] == 2
    assert result["by_tool"]["Bash"] == 1


def test_analyze_tool_usage_empty():
    result = analyze_tool_usage([])
    assert result["total_tool_calls"] == 0
    assert result["by_tool"] == {}


def test_analyze_tool_usage_read_write_ratio():
    entries = [
        {"tool": "Read", "file": "a.py"},
        {"tool": "Read", "file": "b.py"},
        {"tool": "Grep", "pattern": "foo"},
        {"tool": "Edit", "file": "a.py"},
    ]
    result = analyze_tool_usage(entries)
    assert result["reads"] == 3  # 2 Read + 1 Grep
    assert result["writes"] == 1  # 1 Edit
    assert result["read_write_ratio"] == 3.0


def test_analyze_tool_usage_no_writes():
    entries = [{"tool": "Read", "file": "a.py"}, {"tool": "Grep", "pattern": "foo"}]
    result = analyze_tool_usage(entries)
    assert result["read_write_ratio"] is None


def test_analyze_tool_usage_write_and_skill():
    entries = [
        {"tool": "Edit", "file": "a.py"},
        {"tool": "Write", "file": "b.py"},
        {"tool": "Skill", "skill": "commit"},
    ]
    result = analyze_tool_usage(entries)
    assert result["writes"] == 2
    assert result["by_tool"]["Skill"] == 1


# ---------------------------------------------------------------------------
# analyze_efficiency
# ---------------------------------------------------------------------------


def test_analyze_efficiency_rereads():
    entries = [
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},
        {"tool": "Read", "file": "a.py", "offset": 0, "limit": 100},  # exact reread
        {"tool": "Read", "file": "a.py", "offset": 50, "limit": 50},  # different range
    ]
    result = analyze_efficiency(entries)
    assert result["total_reads"] == 3
    assert result["reread_count"] == 2
    assert result["exact_reread_count"] == 1
    assert result["reread_waste_ratio"] == round(1 / 3, 2)


def test_analyze_efficiency_grep_patterns():
    entries = [
        {"tool": "Grep", "pattern": "foo"},
        {"tool": "Grep", "pattern": "bar"},
        {"tool": "Grep", "pattern": "foo"},  # duplicate pattern
    ]
    result = analyze_efficiency(entries)
    assert result["total_grep_calls"] == 3
    assert result["unique_grep_patterns"] == 2


def test_analyze_efficiency_empty():
    result = analyze_efficiency([])
    assert result["total_reads"] == 0
    assert result["reread_waste_ratio"] == 0.0


# ---------------------------------------------------------------------------
# Task 4: generate_sprint_report
# ---------------------------------------------------------------------------


def test_generate_sprint_report_creates_json(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"

    session1 = log_dir / "tools-session1.jsonl"
    session1.write_text(
        json.dumps({"tool": "Read", "file": "a.py", "offset": 0, "limit": 100})
        + "\n"
        + json.dumps({"tool": "Grep", "pattern": "import", "path": "src/"})
        + "\n"
        + json.dumps({"tool": "Read", "file": "b.py", "offset": 0, "limit": 50})
        + "\n"
        + json.dumps({"tool": "Read", "file": "a.py", "offset": 0, "limit": 100})
        + "\n"  # re-read
    )
    session2 = log_dir / "tools-session2.jsonl"
    session2.write_text(
        json.dumps({"tool": "Read", "file": "c.py", "offset": 0, "limit": 200})
        + "\n"
        + json.dumps({"tool": "Bash", "command": "pytest"})
        + "\n"
    )

    report_path = generate_sprint_report(log_dir, output_dir, sprint=99)

    assert report_path == output_dir / "SPRINT99_CONTEXT_REPORT.json"
    assert report_path.exists()

    data = json.loads(report_path.read_text())
    assert data["sprint"] == 99
    assert data["total_reads"] == 4
    assert data["unique_files"] == 3
    assert data["reread_count"] == 1
    assert "top_files" in data
    assert "wasteful_reads" in data
    assert "sessions" in data
    assert len(data["sessions"]) == 2
    session_ids = {s["session_id"] for s in data["sessions"]}
    assert session_ids == {"session1", "session2"}
    # Verify tool_usage breakdown exists
    assert "tool_usage" in data
    assert data["tool_usage"]["total_tool_calls"] == 6
    assert data["tool_usage"]["by_tool"]["Read"] == 4
    assert data["tool_usage"]["by_tool"]["Grep"] == 1
    assert data["tool_usage"]["by_tool"]["Bash"] == 1
    # Verify per-session tool_usage
    for session in data["sessions"]:
        assert "tool_usage" in session


def test_generate_sprint_report_no_logs(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"

    report_path = generate_sprint_report(log_dir, output_dir, sprint=0)

    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["sprint"] == 0
    assert data["total_reads"] == 0
    assert data["sessions"] == []
    assert data["tool_usage"]["total_tool_calls"] == 0


def test_generate_sprint_report_legacy_reads_files(tmp_path):
    """Legacy reads-*.jsonl files should still be picked up."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"

    legacy_session = log_dir / "reads-legacy1.jsonl"
    legacy_session.write_text(json.dumps({"file": "old.py", "offset": 0, "limit": 100}) + "\n")

    report_path = generate_sprint_report(log_dir, output_dir, sprint=25)
    data = json.loads(report_path.read_text())
    assert data["total_reads"] == 1
    assert len(data["sessions"]) == 1
    assert data["sessions"][0]["session_id"] == "legacy1"
