"""Tests for context_report module — parse, analyze reads/tools/errors, generate sprint report."""

import json

from agile_backlog.context_report import (
    analyze_efficiency,
    analyze_errors,
    analyze_reads,
    analyze_tool_usage,
    analyze_usage,
    generate_sprint_report,
    parse_read_log,
    skill_usage_stats,
    usage_cost_usd,
)
from agile_backlog.transcript import Turn, Usage

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
# analyze_errors
# ---------------------------------------------------------------------------


def test_analyze_errors_no_errors():
    entries = [
        {"tool": "Read", "file": "a.py"},
        {"tool": "Bash", "command": "ls", "exit_code": 0},
        {"tool": "Grep", "pattern": "foo"},
    ]
    result = analyze_errors(entries)
    assert result["total_errors"] == 0
    assert result["error_rate"] == 0.0
    assert result["errors_by_tool"] == {}
    assert result["top_error_commands"] == []


def test_analyze_errors_mixed():
    entries = [
        {"tool": "Read", "file": "a.py"},
        {"tool": "Bash", "command": "pytest", "error": True, "exit_code": 1},
        {"tool": "Bash", "command": "ls"},
        {"tool": "Grep", "pattern": "foo", "error": True, "error_message": "no matches"},
        {"tool": "Bash", "command": "ruff check", "error": True, "exit_code": 1},
    ]
    result = analyze_errors(entries)
    assert result["total_errors"] == 3
    assert result["error_rate"] == round(3 / 5, 2)
    assert result["errors_by_tool"]["Bash"] == 2
    assert result["errors_by_tool"]["Grep"] == 1


def test_analyze_errors_by_tool_grouping():
    entries = [
        {"tool": "Bash", "command": "cmd1", "error": True},
        {"tool": "Bash", "command": "cmd2", "error": True},
        {"tool": "Read", "file": "x.py", "error": True},
        {"tool": "Edit", "file": "y.py", "error": True},
    ]
    result = analyze_errors(entries)
    assert result["errors_by_tool"] == {"Bash": 2, "Read": 1, "Edit": 1}


def test_analyze_errors_top_error_commands():
    entries = [
        {"tool": "Bash", "command": "pytest", "error": True},
        {"tool": "Bash", "command": "pytest", "error": True},
        {"tool": "Bash", "command": "pytest", "error": True},
        {"tool": "Bash", "command": "ruff check", "error": True},
        {"tool": "Bash", "command": "ruff check", "error": True},
        {"tool": "Bash", "command": "npm install", "error": True},
    ]
    result = analyze_errors(entries)
    assert len(result["top_error_commands"]) == 3
    assert result["top_error_commands"][0]["command"] == "pytest"
    assert result["top_error_commands"][0]["count"] == 3
    assert result["top_error_commands"][1]["command"] == "ruff check"
    assert result["top_error_commands"][1]["count"] == 2


def test_analyze_errors_empty():
    result = analyze_errors([])
    assert result["total_errors"] == 0
    assert result["error_rate"] == 0.0
    assert result["errors_by_tool"] == {}
    assert result["top_error_commands"] == []


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


def test_generate_sprint_report_includes_errors(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"

    session = log_dir / "tools-errtest.jsonl"
    session.write_text(
        json.dumps({"tool": "Bash", "command": "pytest", "error": True, "exit_code": 1})
        + "\n"
        + json.dumps({"tool": "Read", "file": "a.py"})
        + "\n"
        + json.dumps({"tool": "Bash", "command": "ls"})
        + "\n"
    )

    report_path = generate_sprint_report(log_dir, output_dir, sprint=50)
    data = json.loads(report_path.read_text())

    assert "errors" in data
    assert data["errors"]["total_errors"] == 1
    assert data["errors"]["error_rate"] == round(1 / 3, 2)
    assert data["errors"]["errors_by_tool"]["Bash"] == 1

    assert "errors" in data["sessions"][0]
    assert data["sessions"][0]["errors"]["total_errors"] == 1


def test_generate_sprint_report_includes_usage(tmp_path):
    from agile_backlog.transcript import Session

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"

    session = log_dir / "tools-sess-usage.jsonl"
    session.write_text(json.dumps({"tool": "Read", "file": "a.py", "offset": 0, "limit": 100}) + "\n")

    tsession = Session(
        session_id="sess-usage",
        turns=[
            Turn(role="assistant", model="claude-opus-4-8", usage=Usage(input_tokens=100, output_tokens=200)),
            Turn(
                role="assistant",
                model="claude-haiku-4-5",
                usage=Usage(input_tokens=50, cache_read_input_tokens=450),
            ),
        ],
    )

    report_path = generate_sprint_report(log_dir, output_dir, sprint=77, transcript_sessions=[tsession])
    data = json.loads(report_path.read_text())

    # Aggregate usage block present
    assert "usage" in data
    assert data["usage"]["input_tokens"] == 150
    assert data["usage"]["cache_read_input_tokens"] == 450
    assert data["usage"]["cache_hit_rate"] == 0.75
    assert data["usage"]["cost_usd"] > 0.0

    # Per-session usage matched by session_id
    sess = data["sessions"][0]
    assert sess["session_id"] == "sess-usage"
    assert sess["usage"]["input_tokens"] == 150
    assert sess["usage"]["cache_hit_rate"] == 0.75


def test_generate_sprint_report_usage_zero_without_transcript(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"
    session = log_dir / "tools-s.jsonl"
    session.write_text(json.dumps({"tool": "Read", "file": "a.py", "offset": 0, "limit": 100}) + "\n")

    report_path = generate_sprint_report(log_dir, output_dir, sprint=78)
    data = json.loads(report_path.read_text())
    assert data["usage"]["cost_usd"] == 0.0
    assert data["sessions"][0]["usage"]["cache_hit_rate"] == 0.0


# ---------------------------------------------------------------------------
# skill_usage_stats
# ---------------------------------------------------------------------------


def test_skill_usage_stats_counts_skills():
    entries = [
        {"tool": "Skill", "skill": "commit"},
        {"tool": "Skill", "skill": "review"},
        {"tool": "Skill", "skill": "commit"},
        {"tool": "Read", "file": "a.py"},
        {"tool": "Skill", "skill": "commit"},
    ]
    result = skill_usage_stats(entries)
    assert result == {"commit": 3, "review": 1}


def test_skill_usage_stats_ignores_other_tools():
    entries = [
        {"tool": "Read", "file": "a.py"},
        {"tool": "Grep", "pattern": "foo"},
        {"tool": "Bash", "command": "ls"},
    ]
    result = skill_usage_stats(entries)
    assert result == {}


def test_skill_usage_stats_empty():
    result = skill_usage_stats([])
    assert result == {}


# ---------------------------------------------------------------------------
# estimate_tool_tokens
# ---------------------------------------------------------------------------


def test_estimate_tool_tokens_read_with_lines():
    from agile_backlog.context_report import estimate_tool_tokens

    entries = [
        {"tool": "Read", "file": "a.py", "lines": 200},
        {"tool": "Read", "file": "b.py", "lines": 100},
    ]
    result = estimate_tool_tokens(entries)
    assert result["Read"] == (200 + 100) * 4  # 1200


def test_estimate_tool_tokens_read_fallback():
    from agile_backlog.context_report import DEFAULT_FULL_FILE_LINES, TOKENS_PER_LINE, estimate_tool_tokens

    entries = [{"tool": "Read", "file": "a.py"}]
    result = estimate_tool_tokens(entries)
    assert result["Read"] == DEFAULT_FULL_FILE_LINES * TOKENS_PER_LINE


def test_estimate_tool_tokens_mixed():
    from agile_backlog.context_report import estimate_tool_tokens

    entries = [
        {"tool": "Read", "file": "a.py", "lines": 100},
        {"tool": "Grep", "pattern": "foo"},
        {"tool": "Grep", "pattern": "bar"},
        {"tool": "Bash", "command": "ls"},
        {"tool": "Edit", "file": "x.py"},
    ]
    result = estimate_tool_tokens(entries)
    assert result["Read"] == 400
    assert result["Grep"] == 100
    assert result["Bash"] == 80
    assert result["Edit"] == 100


# ---------------------------------------------------------------------------
# generate_sprint_summary
# ---------------------------------------------------------------------------


def _make_report(**overrides) -> dict:
    base = {
        "sprint": 29,
        "total_reads": 50,
        "unique_files": 20,
        "reread_count": 10,
        "reread_ratio": 0.2,
        "estimated_tokens": 40000,
        "top_files": [
            {"file": "app.py", "count": 15},
            {"file": "cli.py", "count": 8},
        ],
        "wasteful_reads": [{"file": "app.py", "count": 15, "range": "0-0"}],
        "tool_usage": {
            "total_tool_calls": 120,
            "by_tool": {"Read": 50, "Grep": 30, "Bash": 20, "Edit": 10, "Glob": 10},
            "reads": 90,
            "writes": 10,
            "read_write_ratio": 9.0,
        },
        "efficiency": {"reread_waste_ratio": 0.1},
        "errors": {"total_errors": 2, "error_rate": 0.02, "errors_by_tool": {"Bash": 2}, "top_error_commands": []},
        "sessions": [{"session_id": "s1"}, {"session_id": "s2"}],
    }
    base.update(overrides)
    return base


def test_generate_sprint_summary_basic():
    from agile_backlog.context_report import generate_sprint_summary

    report = _make_report()
    result = generate_sprint_summary(report)
    assert "Sprint Context Summary" in result
    assert "Sprint 29" in result
    assert "Overview" in result
    assert "Tool Breakdown" in result
    assert "Read Efficiency" in result


def test_generate_sprint_summary_thresholds():
    from agile_backlog.context_report import generate_sprint_summary

    report = _make_report(
        reread_ratio=0.65,
        errors={"total_errors": 10, "error_rate": 0.08, "errors_by_tool": {"Bash": 10}, "top_error_commands": []},
    )
    result = generate_sprint_summary(report)
    assert "High re-read ratio" in result
    assert "Critical re-read ratio" in result
    assert "High error rate" in result


def test_generate_sprint_summary_clean():
    from agile_backlog.context_report import generate_sprint_summary

    report = _make_report(
        reread_ratio=0.1,
        errors={"total_errors": 0, "error_rate": 0.0, "errors_by_tool": {}, "top_error_commands": []},
    )
    result = generate_sprint_summary(report)
    assert "No optimization issues detected" in result or "Optimization Suggestions" not in result


def test_generate_sprint_summary_top_file_warning():
    from agile_backlog.context_report import generate_sprint_summary

    report = _make_report(top_files=[{"file": "big_file.py", "count": 25}, {"file": "small.py", "count": 3}])
    result = generate_sprint_summary(report)
    assert "big_file.py" in result
    assert "25 times" in result


# ---------------------------------------------------------------------------
# load_all_sprint_reports / compare_sprints
# ---------------------------------------------------------------------------


def _make_sprint_report(
    sprint: int,
    reread_ratio: float = 0.2,
    error_rate: float = 0.01,
    total_calls: int = 100,
    total_reads: int = 30,
    estimated_tokens: int = 50000,
) -> dict:
    return {
        "sprint": sprint,
        "total_reads": total_reads,
        "unique_files": 10,
        "reread_ratio": reread_ratio,
        "estimated_tokens": estimated_tokens,
        "top_files": [{"file": "app.py", "count": 10}],
        "wasteful_reads": [],
        "tool_usage": {
            "total_tool_calls": total_calls,
            "by_tool": {"Read": total_reads, "Bash": total_calls - total_reads},
            "reads": total_reads,
            "writes": 5,
        },
        "efficiency": {"reread_waste_ratio": reread_ratio * 0.5},
        "errors": {"total_errors": int(total_calls * error_rate), "error_rate": error_rate, "errors_by_tool": {}},
        "sessions": [{"session_id": f"session-{sprint}"}],
    }


def test_load_all_sprint_reports(tmp_path):
    from agile_backlog.context_report import load_all_sprint_reports

    for s in [25, 26, 27]:
        (tmp_path / f"SPRINT{s}_CONTEXT_REPORT.json").write_text(json.dumps(_make_sprint_report(s)))
    result = load_all_sprint_reports(tmp_path)
    assert len(result) == 3
    assert [r["sprint"] for r in result] == [25, 26, 27]


def test_load_all_sprint_reports_skips_invalid(tmp_path):
    from agile_backlog.context_report import load_all_sprint_reports

    (tmp_path / "SPRINT25_CONTEXT_REPORT.json").write_text(json.dumps(_make_sprint_report(25)))
    (tmp_path / "SPRINT26_CONTEXT_REPORT.json").write_text("NOT VALID JSON {{{")
    (tmp_path / "SPRINT27_CONTEXT_REPORT.json").write_text(json.dumps(_make_sprint_report(27)))
    result = load_all_sprint_reports(tmp_path)
    assert len(result) == 2
    assert [r["sprint"] for r in result] == [25, 27]


def test_compare_sprints_three_sprints():
    from agile_backlog.context_report import compare_sprints

    reports = [
        _make_sprint_report(25, reread_ratio=0.5, error_rate=0.05, estimated_tokens=80000),
        _make_sprint_report(26, reread_ratio=0.3, error_rate=0.03, estimated_tokens=60000),
        _make_sprint_report(27, reread_ratio=0.2, error_rate=0.02, estimated_tokens=40000),
    ]
    result = compare_sprints(reports)
    assert len(result["sprints"]) == 3
    assert result["trends"]["reread_ratio"] == "improving"
    assert result["trends"]["error_rate"] == "improving"
    assert result["trends"]["token_usage"] == "improving"


def test_compare_sprints_two_sprints():
    from agile_backlog.context_report import compare_sprints

    reports = [
        _make_sprint_report(25, reread_ratio=0.5),
        _make_sprint_report(26, reread_ratio=0.2),
    ]
    result = compare_sprints(reports)
    assert len(result["sprints"]) == 2
    assert result["trends"]["reread_ratio"] == "stable"
    assert result["trends"]["error_rate"] == "stable"
    assert result["trends"]["token_usage"] == "stable"


def test_compare_sprints_worsening():
    from agile_backlog.context_report import compare_sprints

    reports = [
        _make_sprint_report(25, reread_ratio=0.2, error_rate=0.01, estimated_tokens=30000),
        _make_sprint_report(26, reread_ratio=0.3, error_rate=0.03, estimated_tokens=50000),
        _make_sprint_report(27, reread_ratio=0.5, error_rate=0.06, estimated_tokens=80000),
    ]
    result = compare_sprints(reports)
    assert result["trends"]["reread_ratio"] == "declining"
    assert result["trends"]["error_rate"] == "declining"
    assert result["trends"]["token_usage"] == "declining"


# ---------------------------------------------------------------------------
# cache-hit rate (reused from transcript.cache_hit_rate)
# ---------------------------------------------------------------------------


def test_cache_hit_rate_basic():
    from agile_backlog.context_report import cache_hit_rate

    usage = Usage(cache_read_input_tokens=900, cache_creation_input_tokens=50, input_tokens=50)
    assert cache_hit_rate(usage) == 0.9


def test_cache_hit_rate_zero_denominator():
    from agile_backlog.context_report import cache_hit_rate

    assert cache_hit_rate(Usage()) == 0.0


def test_cache_hit_rate_no_cache():
    from agile_backlog.context_report import cache_hit_rate

    usage = Usage(input_tokens=100, output_tokens=200)
    assert cache_hit_rate(usage) == 0.0


# ---------------------------------------------------------------------------
# usage_cost_usd
# ---------------------------------------------------------------------------


def test_usage_cost_opus():
    # opus base in=5.0/1M, out=25.0/1M; cache_read 0.1x, cache_creation 1.25x
    usage = Usage(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
        cache_creation_input_tokens=1_000_000,
    )
    cost = usage_cost_usd(usage, "claude-opus-4-8")
    # input: 1M*5 = 5; cache_read: 1M*5*0.1 = 0.5; cache_creation: 1M*5*1.25 = 6.25; output: 1M*25 = 25
    assert cost == round((5.0 + 0.5 + 6.25 + 25.0), 6)


def test_usage_cost_unknown_model_falls_back():
    usage = Usage(input_tokens=1_000_000, output_tokens=1_000_000)
    cost = usage_cost_usd(usage, "some-future-model-v99")
    assert isinstance(cost, float)
    assert cost > 0.0


def test_usage_cost_accepts_dict():
    cost = usage_cost_usd({"input_tokens": 1_000_000}, "claude-haiku-4-5")
    assert cost == round(1.0, 6)


# ---------------------------------------------------------------------------
# analyze_usage
# ---------------------------------------------------------------------------


def test_analyze_usage_aggregates_and_mixed_models():
    t1 = Turn(role="assistant", model="claude-opus-4-8", usage=Usage(input_tokens=100, output_tokens=200))
    t2 = Turn(
        role="assistant",
        model="claude-haiku-4-5",
        usage=Usage(input_tokens=50, cache_read_input_tokens=450, cache_creation_input_tokens=0),
    )
    result = analyze_usage([t1, t2])
    assert result["input_tokens"] == 150
    assert result["output_tokens"] == 200
    assert result["cache_read_input_tokens"] == 450
    assert result["cache_creation_input_tokens"] == 0
    # hit rate on summed totals: 450 / (450 + 0 + 150) = 0.75
    assert result["cache_hit_rate"] == 0.75
    # cost = per-turn sum
    expected = usage_cost_usd(t1.usage, t1.model) + usage_cost_usd(t2.usage, t2.model)
    assert result["cost_usd"] == round(expected, 6)


def test_analyze_usage_empty():
    result = analyze_usage([])
    assert result["input_tokens"] == 0
    assert result["output_tokens"] == 0
    assert result["cache_read_input_tokens"] == 0
    assert result["cache_creation_input_tokens"] == 0
    assert result["cache_hit_rate"] == 0.0
    assert result["cost_usd"] == 0.0
