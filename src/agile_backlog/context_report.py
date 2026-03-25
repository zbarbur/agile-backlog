"""Sprint context analysis — parse Claude read logs, detect waste, generate JSON reports."""

import json
from collections import Counter
from pathlib import Path

TOKENS_PER_LINE = 4
DEFAULT_FULL_FILE_LINES = 500


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
    if not entries:
        return {
            "total_reads": 0,
            "unique_files": 0,
            "reread_count": 0,
            "reread_ratio": 0.0,
            "estimated_tokens": 0,
            "top_files": [],
            "wasteful_reads": [],
        }

    file_counts = Counter(e["file"] for e in entries)
    # limit=0 means "read whole file" — estimate DEFAULT_FULL_FILE_LINES lines
    total_lines = sum(e.get("limit", 0) or DEFAULT_FULL_FILE_LINES for e in entries)

    seen: dict[str, dict] = {}
    wasteful: list[dict] = []
    reread_count = 0
    for entry in entries:
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
        "total_reads": len(entries),
        "unique_files": len(file_counts),
        "reread_count": reread_count,
        "reread_ratio": round(reread_count / len(entries), 2),
        "estimated_tokens": total_lines * TOKENS_PER_LINE,
        "top_files": top_files,
        "wasteful_reads": list(wasteful_deduped.values()),
    }


def generate_sprint_report(log_dir: Path, output_dir: Path, sprint: int) -> Path:
    all_entries: list[dict] = []
    sessions: list[dict] = []

    for log_file in sorted(log_dir.glob("reads-*.jsonl")):
        entries = parse_read_log(log_file)
        if entries:
            session_metrics = analyze_reads(entries)
            session_metrics["session_id"] = log_file.stem.replace("reads-", "")
            sessions.append(session_metrics)
            all_entries.extend(entries)

    aggregate = analyze_reads(all_entries)
    report = {
        "sprint": sprint,
        **aggregate,
        "sessions": sessions,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"SPRINT{sprint}_CONTEXT_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report_path
