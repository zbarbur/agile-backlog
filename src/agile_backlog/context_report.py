"""Sprint context analysis — parse Claude tool logs, detect waste, generate JSON reports."""

import json
from collections import Counter
from pathlib import Path

TOKENS_PER_LINE = 4
DEFAULT_FULL_FILE_LINES = 500

TOOL_TOKEN_ESTIMATES: dict[str, int] = {
    "Read": 0,  # calculated from entry data
    "Grep": 50,
    "Glob": 20,
    "Edit": 100,
    "Write": 200,
    "Bash": 80,
    "Agent": 500,
    "Skill": 30,
}
DEFAULT_TOOL_TOKENS = 50


def parse_read_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def analyze_reads(entries: list[dict]) -> dict:
    read_entries = [e for e in entries if e.get("tool", "Read") == "Read"]
    if not read_entries:
        return {
            "total_reads": 0,
            "unique_files": 0,
            "reread_count": 0,
            "reread_ratio": 0.0,
            "estimated_tokens": 0,
            "top_files": [],
            "wasteful_reads": [],
        }

    file_counts = Counter(e["file"] for e in read_entries)
    total_lines = sum(e.get("limit", 0) or DEFAULT_FULL_FILE_LINES for e in read_entries)

    seen: dict[str, dict] = {}
    wasteful: list[dict] = []
    reread_count = 0
    for entry in read_entries:
        key = entry["file"]
        if key in seen:
            reread_count += 1
            prev = seen[key]
            if entry.get("offset") == prev.get("offset") and entry.get("limit") == prev.get("limit"):
                wasteful.append(
                    {
                        "file": key,
                        "count": file_counts[key],
                        "range": f"{entry.get('offset', 0)}-{entry.get('limit', 0)}",
                    }
                )
        seen[key] = entry

    wasteful_deduped = {w["file"]: w for w in wasteful}
    top_files = [{"file": f, "count": c} for f, c in file_counts.most_common(10)]

    return {
        "total_reads": len(read_entries),
        "unique_files": len(file_counts),
        "reread_count": reread_count,
        "reread_ratio": round(reread_count / len(read_entries), 2),
        "estimated_tokens": total_lines * TOKENS_PER_LINE,
        "top_files": top_files,
        "wasteful_reads": list(wasteful_deduped.values()),
    }


def analyze_tool_usage(entries: list[dict]) -> dict:
    tool_counts = Counter(e.get("tool", "Read") for e in entries)
    read_tools = {"Read", "Grep", "Glob"}
    write_tools = {"Edit", "Write"}
    reads = sum(tool_counts.get(t, 0) for t in read_tools)
    writes = sum(tool_counts.get(t, 0) for t in write_tools)
    return {
        "total_tool_calls": len(entries),
        "by_tool": dict(tool_counts.most_common()),
        "reads": reads,
        "writes": writes,
        "read_write_ratio": round(reads / writes, 2) if writes > 0 else None,
    }


def analyze_efficiency(entries: list[dict]) -> dict:
    read_entries = [e for e in entries if e.get("tool") == "Read"]
    seen_files: dict[str, int] = {}
    reread_count = 0
    exact_reread_count = 0
    for e in read_entries:
        key = e.get("file", "")
        if not key:
            continue
        if key in seen_files:
            reread_count += 1
            prev_offset = seen_files.get(f"{key}_offset")
            prev_limit = seen_files.get(f"{key}_limit")
            if e.get("offset", 0) == prev_offset and e.get("limit", 0) == prev_limit:
                exact_reread_count += 1
        seen_files[key] = seen_files.get(key, 0) + 1
        seen_files[f"{key}_offset"] = e.get("offset", 0) or 0
        seen_files[f"{key}_limit"] = e.get("limit", 0) or 0

    grep_entries = [e for e in entries if e.get("tool") == "Grep"]
    grep_patterns = [e.get("pattern", "") for e in grep_entries]
    unique_patterns = len(set(grep_patterns))

    return {
        "total_reads": len(read_entries),
        "reread_count": reread_count,
        "exact_reread_count": exact_reread_count,
        "reread_waste_ratio": round(exact_reread_count / len(read_entries), 2) if read_entries else 0.0,
        "unique_grep_patterns": unique_patterns,
        "total_grep_calls": len(grep_entries),
    }


def analyze_errors(entries: list[dict]) -> dict:
    error_entries = [e for e in entries if e.get("error") is True]
    total = len(entries)
    total_errors = len(error_entries)

    errors_by_tool: dict[str, int] = {}
    for e in error_entries:
        tool = e.get("tool", "unknown")
        errors_by_tool[tool] = errors_by_tool.get(tool, 0) + 1

    bash_error_cmds = [e.get("command", "") for e in error_entries if e.get("tool") == "Bash" and e.get("command")]
    cmd_counts = Counter(bash_error_cmds)
    top_error_commands = [{"command": cmd, "count": cnt} for cmd, cnt in cmd_counts.most_common(5)]

    return {
        "total_errors": total_errors,
        "error_rate": round(total_errors / total, 2) if total > 0 else 0.0,
        "errors_by_tool": errors_by_tool,
        "top_error_commands": top_error_commands,
    }


def skill_usage_stats(entries: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in entries:
        if e.get("tool") == "Skill":
            skill = e.get("skill", "unknown")
            counts[skill] = counts.get(skill, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def generate_sprint_report(log_dir: Path, output_dir: Path, sprint: int) -> Path:
    all_entries: list[dict] = []
    sessions: list[dict] = []

    for log_file in sorted(log_dir.glob("tools-*.jsonl")):
        entries = parse_read_log(log_file)
        if entries:
            session_metrics = analyze_reads(entries)
            session_metrics["session_id"] = log_file.stem.replace("tools-", "")
            session_metrics["tool_usage"] = analyze_tool_usage(entries)
            session_metrics["efficiency"] = analyze_efficiency(entries)
            session_metrics["errors"] = analyze_errors(entries)
            sessions.append(session_metrics)
            all_entries.extend(entries)

    # Fallback: also check legacy reads-*.jsonl files
    for log_file in sorted(log_dir.glob("reads-*.jsonl")):
        entries = parse_read_log(log_file)
        if entries:
            session_metrics = analyze_reads(entries)
            session_metrics["session_id"] = log_file.stem.replace("reads-", "")
            session_metrics["tool_usage"] = analyze_tool_usage(entries)
            session_metrics["efficiency"] = analyze_efficiency(entries)
            session_metrics["errors"] = analyze_errors(entries)
            sessions.append(session_metrics)
            all_entries.extend(entries)

    aggregate = analyze_reads(all_entries)
    aggregate["tool_usage"] = analyze_tool_usage(all_entries)
    aggregate["efficiency"] = analyze_efficiency(all_entries)
    aggregate["errors"] = analyze_errors(all_entries)
    report = {
        "sprint": sprint,
        **aggregate,
        "sessions": sessions,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"SPRINT{sprint}_CONTEXT_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report_path


def estimate_tool_tokens(entries: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for e in entries:
        tool = e.get("tool", "Read")
        if tool == "Read":
            lines = e.get("lines") or e.get("limit") or DEFAULT_FULL_FILE_LINES
            tokens = lines * TOKENS_PER_LINE
        else:
            tokens = TOOL_TOKEN_ESTIMATES.get(tool, DEFAULT_TOOL_TOKENS)
        totals[tool] = totals.get(tool, 0) + tokens
    return totals


def generate_sprint_summary(report: dict) -> str:
    sprint = report.get("sprint", "?")
    total_reads = report.get("total_reads", 0)
    reread_ratio = report.get("reread_ratio", 0.0)
    estimated_tokens = report.get("estimated_tokens", 0)
    tool_usage = report.get("tool_usage", {})
    total_calls = tool_usage.get("total_tool_calls", 0)
    by_tool = tool_usage.get("by_tool", {})
    sessions = report.get("sessions", [])
    errors = report.get("errors", {})
    top_files = report.get("top_files", [])
    wasteful_reads = report.get("wasteful_reads", [])

    # Estimate tokens per tool from by_tool counts (no raw entries available in report)
    tool_tokens: dict[str, int] = {}
    for tool, count in by_tool.items():
        if tool == "Read":
            tool_tokens[tool] = estimated_tokens
        else:
            tool_tokens[tool] = count * TOOL_TOKEN_ESTIMATES.get(tool, DEFAULT_TOOL_TOKENS)
    total_est_tokens = sum(tool_tokens.values())

    lines: list[str] = []
    lines.append(f"# Sprint Context Summary — Sprint {sprint}")
    lines.append("")

    # Overview
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- **Total tool calls:** {total_calls}")
    lines.append(f"- **Sessions:** {len(sessions)}")
    lines.append(f"- **Read calls:** {total_reads}")
    lines.append(f"- **Re-read ratio:** {round(reread_ratio * 100, 1)}%")
    lines.append(f"- **Estimated tokens (all tools):** {total_est_tokens:,}")
    lines.append("")

    # Tool Breakdown
    lines.append("## Tool Breakdown")
    lines.append("")
    lines.append("| Tool | Count | % | Est. Tokens |")
    lines.append("|------|------:|--:|------------:|")
    for tool, count in sorted(by_tool.items(), key=lambda x: -x[1]):
        pct = round(count / total_calls * 100, 1) if total_calls else 0
        tk = tool_tokens.get(tool, 0)
        tk_display = f"{tk // 1000}k" if tk >= 1000 else str(tk)
        lines.append(f"| {tool} | {count} | {pct}% | ~{tk_display} |")
    lines.append("")

    # Read Efficiency
    lines.append("## Read Efficiency")
    lines.append("")
    rr_pct = round(reread_ratio * 100, 1)
    if rr_pct < 15:
        assessment = "Excellent"
    elif rr_pct < 30:
        assessment = "Good"
    elif rr_pct < 50:
        assessment = "Needs improvement"
    else:
        assessment = "Poor"
    lines.append(f"- **Re-read ratio:** {rr_pct}% ({assessment})")
    if top_files:
        lines.append("- **Top re-read files:**")
        for f in top_files[:5]:
            lines.append(f"  - `{f['file']}` — {f['count']} reads")
    if wasteful_reads:
        lines.append("- **Wasteful reads (identical range):**")
        for w in wasteful_reads[:5]:
            lines.append(f"  - `{w['file']}` — {w['count']} reads")
    lines.append("")

    # Errors
    total_errors = errors.get("total_errors", 0)
    error_rate = errors.get("error_rate", 0.0)
    if total_errors > 0:
        lines.append("## Errors")
        lines.append("")
        lines.append(f"- **Total errors:** {total_errors}")
        lines.append(f"- **Error rate:** {round(error_rate * 100, 1)}%")
        errors_by_tool = errors.get("errors_by_tool", {})
        if errors_by_tool:
            lines.append("- **By tool:**")
            for t, c in sorted(errors_by_tool.items(), key=lambda x: -x[1]):
                lines.append(f"  - {t}: {c}")
        lines.append("")

    # Optimization Suggestions
    suggestions: list[str] = []
    if reread_ratio > 0.3:
        suggestions.append("High re-read ratio — consider using offset/limit for targeted reads")
    if reread_ratio > 0.5:
        suggestions.append("Critical re-read ratio — pass file content to subagents instead of re-reading")
    if error_rate > 0.05:
        suggestions.append("High error rate — review failing commands")
    for f in top_files:
        if f["count"] > 20:
            suggestions.append(f"File `{f['file']}` read {f['count']} times — consider extracting relevant sections")

    if suggestions:
        lines.append("## Optimization Suggestions")
        lines.append("")
        for s in suggestions:
            lines.append(f"- {s}")
        lines.append("")
    else:
        lines.append("## Optimization Suggestions")
        lines.append("")
        lines.append("No optimization issues detected.")
        lines.append("")

    return "\n".join(lines)


def load_all_sprint_reports(output_dir: Path) -> list[dict]:
    import re

    reports: list[dict] = []
    for f in sorted(output_dir.glob("SPRINT*_CONTEXT_REPORT.json")):
        m = re.search(r"SPRINT(\d+)_CONTEXT_REPORT\.json$", f.name)
        if not m:
            continue
        try:
            data = json.loads(f.read_text())
            data.setdefault("sprint", int(m.group(1)))
            reports.append(data)
        except (json.JSONDecodeError, ValueError):
            continue
    reports.sort(key=lambda r: r.get("sprint", 0))
    return reports


def compare_sprints(reports: list[dict]) -> dict:
    sprints_data: list[dict] = []
    for r in reports:
        tool_usage = r.get("tool_usage", {})
        errors = r.get("errors", {})
        sprints_data.append(
            {
                "sprint": r.get("sprint", 0),
                "total_tool_calls": tool_usage.get("total_tool_calls", 0),
                "read_calls": r.get("total_reads", 0),
                "reread_ratio": r.get("reread_ratio", 0.0),
                "estimated_tokens": r.get("estimated_tokens", 0),
                "error_rate": errors.get("error_rate", 0.0),
                "sessions": len(r.get("sessions", [])),
                "items_completed": None,
            }
        )

    def _trend(key: str, lower_is_better: bool = True) -> str:
        if len(sprints_data) < 3:
            return "stable"
        recent_avg = (sprints_data[-1][key] + sprints_data[-2][key]) / 2
        previous = sprints_data[-3][key]
        if previous == 0:
            return "stable"
        change = (recent_avg - previous) / abs(previous)
        if lower_is_better:
            if change < -0.10:
                return "improving"
            if change > 0.10:
                return "declining"
        else:
            if change > 0.10:
                return "improving"
            if change < -0.10:
                return "declining"
        return "stable"

    return {
        "sprints": sprints_data,
        "trends": {
            "reread_ratio": _trend("reread_ratio", lower_is_better=True),
            "error_rate": _trend("error_rate", lower_is_better=True),
            "token_usage": _trend("estimated_tokens", lower_is_better=True),
        },
    }
