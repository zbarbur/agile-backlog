"""Native transcript ingestion — parse Claude Code session JSONL into a typed Session.

This is the canonical data source Dashboard v2 builds on. Claude Code writes one JSONL
record per line under ``~/.claude/projects/<slug>/<session-id>.jsonl``. Records carry a
top-level ``type`` (``assistant`` / ``user`` / ``system`` and a few bookkeeping types).

What we extract:
- Real per-turn token usage from ``message.usage`` (input/output/cache-read/cache-creation).
- ``tool_use`` content blocks (assistant ``message.content``) paired to their result via
  ``toolUseResult`` records linked by ``sourceToolAssistantUUID`` -> the assistant record's
  ``uuid``. Each call exposes ``success: bool | None``.
- Skill attribution from the top-level ``attributionSkill`` string.

Real-format notes (grounded in actual transcripts, deviating from the spec where needed):
- ``toolUseResult`` is usually a dict but is sometimes a plain string; only some dicts carry
  a ``success`` key. Missing/non-dict -> ``success = None``.
- ``sourceToolAssistantUUID`` links to the *assistant record's* ``uuid`` (not the tool_use
  block id). One assistant record may contain multiple ``tool_use`` blocks; a single result
  record links to one assistant record, so we attach its ``success`` to that record's calls.
- ``attributionSkill`` is a plain skill-name string attached to assistant turns; the skill map
  counts each tagged turn.
- ``isSidechain: true`` turns (sub-agent loops) are kept separately and excluded from
  main-loop aggregates.

The ``Usage`` shape (input_tokens / output_tokens / cache_read_input_tokens /
cache_creation_input_tokens, all defaulting to 0) is intentionally dict-friendly so the
cache-hit-rate and context-view sprint items can consume it directly.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class ToolCall(BaseModel):
    name: str
    id: str
    success: bool | None = None
    skill: str | None = None


class Turn(BaseModel):
    role: str
    usage: Usage = Usage()
    model: str | None = None
    is_sidechain: bool = False
    tool_calls: list[ToolCall] = []
    attribution_skill: str | None = None
    uuid: str | None = None
    message_id: str | None = None


class Session(BaseModel):
    session_id: str | None = None
    git_branch: str | None = None
    turns: list[Turn] = []
    prompts: list[str] = []

    @property
    def _main_turns(self) -> list[Turn]:
        return [t for t in self.turns if not t.is_sidechain]

    @property
    def sidechain_turns(self) -> list[Turn]:
        return [t for t in self.turns if t.is_sidechain]

    @property
    def usage_total(self) -> Usage:
        return session_token_totals([t.usage for t in self._main_turns])

    @property
    def cache_hit_rate(self) -> float:
        return cache_hit_rate(self.usage_total)

    @property
    def tool_calls(self) -> list[ToolCall]:
        calls: list[ToolCall] = []
        for turn in self._main_turns:
            calls.extend(turn.tool_calls)
        return calls

    @property
    def skill_usage(self) -> dict[str, int]:
        return skill_usage_from_attribution(
            [{"attributionSkill": t.attribution_skill} for t in self._main_turns if t.attribution_skill]
        )


# ---------------------------------------------------------------------------
# Pure aggregate helpers
# ---------------------------------------------------------------------------


def session_token_totals(usages: list[Usage]) -> Usage:
    total = Usage()
    for u in usages:
        total.input_tokens += u.input_tokens
        total.output_tokens += u.output_tokens
        total.cache_read_input_tokens += u.cache_read_input_tokens
        total.cache_creation_input_tokens += u.cache_creation_input_tokens
    return total


def cache_hit_rate(usage: Usage) -> float:
    """cache_read / (cache_read + cache_creation + input). 0.0 when denominator is 0."""
    denom = usage.cache_read_input_tokens + usage.cache_creation_input_tokens + usage.input_tokens
    if denom == 0:
        return 0.0
    return usage.cache_read_input_tokens / denom


def skill_usage_from_attribution(turns: list[dict]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for turn in turns:
        skill = turn.get("attributionSkill")
        if skill:
            counts[skill] += 1
    return dict(counts)


def _usage_from_dict(raw: dict | None) -> Usage:
    if not isinstance(raw, dict):
        return Usage()
    return Usage(
        input_tokens=raw.get("input_tokens", 0) or 0,
        output_tokens=raw.get("output_tokens", 0) or 0,
        cache_read_input_tokens=raw.get("cache_read_input_tokens", 0) or 0,
        cache_creation_input_tokens=raw.get("cache_creation_input_tokens", 0) or 0,
    )


def _tool_calls_from_content(content: object) -> list[ToolCall]:
    calls: list[ToolCall] = []
    if not isinstance(content, list):
        return calls
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_use" and block.get("name") and block.get("id"):
            calls.append(ToolCall(name=block["name"], id=block["id"]))
    return calls


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_transcript(path: Path) -> Session:
    turns: list[Turn] = []
    prompts: list[str] = []
    session_id: str | None = None
    git_branch: str | None = None

    seen_ids: set[str] = set()
    # assistant record uuid -> Turn (for linking tool results back to their calls)
    turns_by_uuid: dict[str, Turn] = {}

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue

            session_id = session_id or rec.get("sessionId")
            git_branch = git_branch or rec.get("gitBranch")

            message = rec.get("message") or {}
            rec_type = rec.get("type")

            # Dedup key: assistant uses message.id; others use uuid.
            if rec_type == "assistant":
                dedup_key = message.get("id") or rec.get("uuid")
            else:
                dedup_key = rec.get("uuid")
            if dedup_key is not None:
                if dedup_key in seen_ids:
                    continue
                seen_ids.add(dedup_key)

            if rec_type == "assistant":
                turn = Turn(
                    role="assistant",
                    usage=_usage_from_dict(message.get("usage")),
                    model=message.get("model"),
                    is_sidechain=bool(rec.get("isSidechain")),
                    tool_calls=_tool_calls_from_content(message.get("content")),
                    attribution_skill=rec.get("attributionSkill"),
                    uuid=rec.get("uuid"),
                    message_id=message.get("id"),
                )
                turns.append(turn)
                if turn.uuid:
                    turns_by_uuid[turn.uuid] = turn

            # A record may carry a toolUseResult linking back to an assistant turn.
            tool_result = rec.get("toolUseResult")
            if tool_result is not None:
                source_uuid = rec.get("sourceToolAssistantUUID")
                success = tool_result.get("success") if isinstance(tool_result, dict) else None
                target = turns_by_uuid.get(source_uuid) if source_uuid else None
                if target is not None:
                    for call in target.tool_calls:
                        call.success = success

            # Collect user prompts (string content, not tool results / meta).
            if (
                rec_type == "user"
                and tool_result is None
                and not rec.get("isMeta")
                and isinstance(message.get("content"), str)
            ):
                prompts.append(message["content"])

    return Session(
        session_id=session_id,
        git_branch=git_branch,
        turns=turns,
        prompts=prompts,
    )


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_transcripts(cwd: Path) -> list[Path]:
    """Resolve the project slug (cwd path with '/' -> '-') under ~/.claude/projects/<slug>/
    and return its session .jsonl files. Returns [] when the dir is absent."""
    slug = str(Path(cwd)).replace("/", "-")
    proj_dir = Path.home() / ".claude" / "projects" / slug
    if not proj_dir.is_dir():
        return []
    return sorted(proj_dir.glob("*.jsonl"))
