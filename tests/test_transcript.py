"""Tests for transcript module — parse Claude Code native session JSONL into a typed Session."""

import json

from agile_backlog.transcript import (
    Session,
    Usage,
    cache_hit_rate,
    discover_transcripts,
    parse_transcript,
    session_token_totals,
    skill_usage_from_attribution,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assistant(uuid, msg_id, usage, content=None, attribution=None, sidechain=False):
    rec = {
        "type": "assistant",
        "uuid": uuid,
        "isSidechain": sidechain,
        "sessionId": "sess-1",
        "gitBranch": "sprint31/main",
        "message": {
            "id": msg_id,
            "role": "assistant",
            "model": "claude-opus-4-8",
            "usage": usage,
            "content": content or [],
        },
    }
    if attribution is not None:
        rec["attributionSkill"] = attribution
    return rec


def _tool_result(uuid, source_assistant_uuid, result):
    return {
        "type": "user",
        "uuid": uuid,
        "isSidechain": False,
        "sessionId": "sess-1",
        "sourceToolAssistantUUID": source_assistant_uuid,
        "toolUseResult": result,
        "message": {"role": "user", "content": "tool result"},
    }


def _usage(inp=0, out=0, cache_read=0, cache_creation=0):
    return {
        "input_tokens": inp,
        "output_tokens": out,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_creation,
    }


# ---------------------------------------------------------------------------
# parse_transcript: usage
# ---------------------------------------------------------------------------


def test_parse_transcript_captures_usage(tmp_path):
    log = tmp_path / "session.jsonl"
    log.write_text(
        json.dumps(_assistant("u1", "msg_1", _usage(inp=100, out=50, cache_read=200, cache_creation=30))) + "\n"
    )
    session = parse_transcript(log)
    assert isinstance(session, Session)
    assert len(session.turns) == 1
    turn = session.turns[0]
    assert turn.usage.input_tokens == 100
    assert turn.usage.output_tokens == 50
    assert turn.usage.cache_read_input_tokens == 200
    assert turn.usage.cache_creation_input_tokens == 30
    totals = session.usage_total
    assert totals.input_tokens == 100
    assert totals.output_tokens == 50
    assert totals.cache_read_input_tokens == 200
    assert totals.cache_creation_input_tokens == 30


def test_cache_hit_rate_computed(tmp_path):
    log = tmp_path / "session.jsonl"
    log.write_text(json.dumps(_assistant("u1", "msg_1", _usage(inp=100, cache_read=600, cache_creation=300))) + "\n")
    session = parse_transcript(log)
    # 600 / (600 + 300 + 100) = 0.6
    assert session.cache_hit_rate == 0.6


def test_cache_hit_rate_zero_denominator():
    # Pure function: denominator 0 -> 0.0
    assert cache_hit_rate(Usage()) == 0.0
    assert cache_hit_rate(Usage(output_tokens=500)) == 0.0


# ---------------------------------------------------------------------------
# tool_use paired to result
# ---------------------------------------------------------------------------


def test_tool_use_paired_to_result_success(tmp_path):
    log = tmp_path / "session.jsonl"
    content = [{"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "false"}}]
    log.write_text(
        json.dumps(_assistant("assist-uuid", "msg_1", _usage(inp=10), content=content))
        + "\n"
        + json.dumps(_tool_result("res-uuid", "assist-uuid", {"commandName": "Bash", "success": False}))
        + "\n"
    )
    session = parse_transcript(log)
    calls = session.tool_calls
    assert len(calls) == 1
    assert calls[0].name == "Bash"
    assert calls[0].id == "toolu_1"
    assert calls[0].success is False


def test_tool_use_result_non_dict_success_none(tmp_path):
    log = tmp_path / "session.jsonl"
    content = [{"type": "tool_use", "id": "toolu_1", "name": "Read", "input": {}}]
    log.write_text(
        json.dumps(_assistant("assist-uuid", "msg_1", _usage(inp=10), content=content))
        + "\n"
        + json.dumps(_tool_result("res-uuid", "assist-uuid", "plain string result"))
        + "\n"
    )
    session = parse_transcript(log)
    assert len(session.tool_calls) == 1
    assert session.tool_calls[0].success is None


# ---------------------------------------------------------------------------
# skill usage from attribution
# ---------------------------------------------------------------------------


def test_skill_usage_from_attribution(tmp_path):
    log = tmp_path / "session.jsonl"
    log.write_text(
        json.dumps(_assistant("u1", "msg_1", _usage(inp=5), attribution="plan"))
        + "\n"
        + json.dumps(_assistant("u2", "msg_2", _usage(inp=5), attribution="plan"))
        + "\n"
        + json.dumps(_assistant("u3", "msg_3", _usage(inp=5), attribution="sprint-start"))
        + "\n"
    )
    session = parse_transcript(log)
    assert session.skill_usage == {"plan": 2, "sprint-start": 1}


def test_skill_usage_from_attribution_helper():
    turns = [
        {"attributionSkill": "plan"},
        {"attributionSkill": "plan"},
        {"attributionSkill": "review"},
        {},
    ]
    assert skill_usage_from_attribution(turns) == {"plan": 2, "review": 1}


# ---------------------------------------------------------------------------
# dedupe
# ---------------------------------------------------------------------------


def test_dedupe_by_message_id(tmp_path):
    log = tmp_path / "session.jsonl"
    dup = json.dumps(_assistant("u1", "msg_dup", _usage(inp=100, out=20)))
    log.write_text(dup + "\n" + dup + "\n")
    session = parse_transcript(log)
    assert len(session.turns) == 1
    assert session.usage_total.input_tokens == 100


# ---------------------------------------------------------------------------
# sidechain separation
# ---------------------------------------------------------------------------


def test_sidechain_separated(tmp_path):
    log = tmp_path / "session.jsonl"
    main_content = [{"type": "tool_use", "id": "tool_main", "name": "Bash", "input": {}}]
    side_content = [{"type": "tool_use", "id": "tool_side", "name": "Read", "input": {}}]
    log.write_text(
        json.dumps(_assistant("u1", "msg_1", _usage(inp=100), content=main_content))
        + "\n"
        + json.dumps(_assistant("u2", "msg_2", _usage(inp=999), content=side_content, sidechain=True))
        + "\n"
    )
    session = parse_transcript(log)
    # Main-loop aggregates exclude sidechain
    assert session.usage_total.input_tokens == 100
    main_tool_ids = {c.id for c in session.tool_calls}
    assert main_tool_ids == {"tool_main"}
    # Sidechain still captured separately
    assert len(session.sidechain_turns) == 1
    assert session.sidechain_turns[0].usage.input_tokens == 999


# ---------------------------------------------------------------------------
# malformed lines
# ---------------------------------------------------------------------------


def test_parse_skips_malformed_lines(tmp_path):
    log = tmp_path / "session.jsonl"
    log.write_text(
        json.dumps(_assistant("u1", "msg_1", _usage(inp=100)))
        + "\n"
        + "THIS IS NOT JSON {{{\n"
        + "\n"  # blank line
        + json.dumps(_assistant("u2", "msg_2", _usage(inp=50)))
        + "\n"
    )
    session = parse_transcript(log)
    assert len(session.turns) == 2
    assert session.usage_total.input_tokens == 150


# ---------------------------------------------------------------------------
# session metadata
# ---------------------------------------------------------------------------


def test_session_metadata_captured(tmp_path):
    log = tmp_path / "session.jsonl"
    log.write_text(json.dumps(_assistant("u1", "msg_1", _usage(inp=1))) + "\n")
    session = parse_transcript(log)
    assert session.session_id == "sess-1"
    assert session.git_branch == "sprint31/main"


# ---------------------------------------------------------------------------
# token totals helper
# ---------------------------------------------------------------------------


def test_session_token_totals_helper():
    usages = [
        Usage(input_tokens=10, output_tokens=5, cache_read_input_tokens=20, cache_creation_input_tokens=3),
        Usage(input_tokens=1, output_tokens=2, cache_read_input_tokens=4, cache_creation_input_tokens=8),
    ]
    total = session_token_totals(usages)
    assert total.input_tokens == 11
    assert total.output_tokens == 7
    assert total.cache_read_input_tokens == 24
    assert total.cache_creation_input_tokens == 11


# ---------------------------------------------------------------------------
# discover_transcripts
# ---------------------------------------------------------------------------


def test_discover_transcripts_slug_and_missing_dir(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    cwd = tmp_path / "Users" / "guyguzner" / "Projects" / "agile-backlog"

    # Missing projects dir -> []
    assert discover_transcripts(cwd) == []

    # Build the expected slug dir
    from pathlib import Path

    slug = str(Path(cwd)).replace("/", "-")
    proj_dir = fake_home / ".claude" / "projects" / slug
    proj_dir.mkdir(parents=True)
    (proj_dir / "a.jsonl").write_text("{}\n")
    (proj_dir / "b.jsonl").write_text("{}\n")
    (proj_dir / "notes.txt").write_text("ignore")

    found = discover_transcripts(cwd)
    names = sorted(p.name for p in found)
    assert names == ["a.jsonl", "b.jsonl"]
