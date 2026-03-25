"""Tests for context_report module — parse_read_log, analyze_reads, generate_sprint_report."""

import json

from agile_backlog.context_report import analyze_reads, generate_sprint_report, parse_read_log

# ---------------------------------------------------------------------------
# Task 2: parse_read_log
# ---------------------------------------------------------------------------


def test_parse_read_log_returns_entries(tmp_path):
    log = tmp_path / "reads-abc.jsonl"
    log.write_text(
        json.dumps({"file": "foo.py", "offset": 0, "limit": 100})
        + "\n"
        + json.dumps({"file": "bar.py", "offset": 0, "limit": 50})
        + "\n"
    )
    entries = parse_read_log(log)
    assert len(entries) == 2
    assert entries[0]["file"] == "foo.py"
    assert entries[1]["file"] == "bar.py"


def test_parse_read_log_empty_file(tmp_path):
    log = tmp_path / "reads-empty.jsonl"
    log.write_text("")
    assert parse_read_log(log) == []


def test_parse_read_log_skips_malformed_lines(tmp_path):
    log = tmp_path / "reads-mixed.jsonl"
    log.write_text(
        json.dumps({"file": "good.py", "offset": 0, "limit": 10})
        + "\n"
        + "NOT_JSON\n"
        + json.dumps({"file": "also_good.py", "offset": 0, "limit": 20})
        + "\n"
    )
    entries = parse_read_log(log)
    assert len(entries) == 2
    assert entries[0]["file"] == "good.py"
    assert entries[1]["file"] == "also_good.py"


# ---------------------------------------------------------------------------
# Task 3: analyze_reads
# ---------------------------------------------------------------------------


def test_analyze_reads_counts():
    entries = [
        {"file": "a.py", "offset": 0, "limit": 100},
        {"file": "b.py", "offset": 0, "limit": 50},
        {"file": "a.py", "offset": 0, "limit": 100},  # re-read
    ]
    result = analyze_reads(entries)
    assert result["total_reads"] == 3
    assert result["unique_files"] == 2
    assert result["reread_count"] == 1
    assert result["reread_ratio"] == round(1 / 3, 2)


def test_analyze_reads_top_files():
    entries = [{"file": "a.py", "offset": 0, "limit": 10}] * 5 + [{"file": "b.py", "offset": 0, "limit": 10}] * 3
    result = analyze_reads(entries)
    assert result["top_files"][0]["file"] == "a.py"
    assert result["top_files"][0]["count"] == 5
    assert result["top_files"][1]["file"] == "b.py"
    assert result["top_files"][1]["count"] == 3


def test_analyze_reads_token_estimate():
    """limit=200 → 200 lines × 4 tokens = 800 tokens."""
    entries = [{"file": "a.py", "offset": 0, "limit": 200}]
    result = analyze_reads(entries)
    assert result["estimated_tokens"] == 800


def test_analyze_reads_token_estimate_full_file():
    """limit=0 means full file — estimate 500 lines → 2000 tokens."""
    entries = [{"file": "a.py", "offset": 0, "limit": 0}]
    result = analyze_reads(entries)
    assert result["estimated_tokens"] == 2000


def test_analyze_reads_wasteful_detection():
    """Same file, same offset/limit, no edit in between → wasteful."""
    entries = [
        {"file": "a.py", "offset": 0, "limit": 100},
        {"file": "a.py", "offset": 0, "limit": 100},  # wasteful: identical range
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


# ---------------------------------------------------------------------------
# Task 4: generate_sprint_report
# ---------------------------------------------------------------------------


def test_generate_sprint_report_creates_json(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"

    session1 = log_dir / "reads-session1.jsonl"
    session1.write_text(
        json.dumps({"file": "a.py", "offset": 0, "limit": 100})
        + "\n"
        + json.dumps({"file": "b.py", "offset": 0, "limit": 50})
        + "\n"
        + json.dumps({"file": "a.py", "offset": 0, "limit": 100})
        + "\n"  # re-read
    )
    session2 = log_dir / "reads-session2.jsonl"
    session2.write_text(json.dumps({"file": "c.py", "offset": 0, "limit": 200}) + "\n")

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
