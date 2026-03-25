# Sprint Context Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Track file read patterns during Claude sessions and generate context efficiency reports at sprint end.

**Architecture:** A PostToolUse shell hook logs every Read call as JSON lines to a temp file. The hook also detects re-reads and returns a warning prompt only when a file is read again without edits in between. At sprint end, a Python module aggregates the log into a JSON report with metrics (re-read ratio, top files, token estimates). The sprint-end skill gets a new step to invoke this.

**Tech Stack:** Bash (hook), Python 3.11+ (report generator), JSON lines (log format), JSON (report output)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `.claude/hooks/post-read-logger.sh` | Create | Shell hook — logs Read calls, warns on re-reads |
| `.claude/settings.json` | Modify | Register the PostToolUse hook |
| `src/agile_backlog/context_report.py` | Create | Parse logs, detect waste, generate JSON report |
| `tests/test_context_report.py` | Create | Unit tests for report generation |
| `.claude/skills/sprint-end/SKILL.md` | Modify | Add context report step to Phase 3 |

---

## Task 1: PostToolUse Shell Hook

**Files:**
- Create: `.claude/hooks/post-read-logger.sh`
- Modify: `.claude/settings.json`

The hook receives tool input as JSON on stdin. It must:
1. Parse the file_path from the input
2. Append a JSON line to the session log
3. Check if this file was already logged — if so, return a re-read warning

### Step-by-step

- [ ] **Step 1: Create the hook script**

```bash
#!/usr/bin/env bash
# PostToolUse hook for Read tool — logs reads and warns on re-reads
# Input: JSON on stdin with tool_name and tool_input fields
# Output: warning message to stdout (only on re-reads), exit 0 always

set -uo pipefail

# Read the hook input from stdin
INPUT=$(cat)

# Only process Read tool calls
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
if [ "$TOOL_NAME" != "Read" ]; then
  exit 0
fi

# Extract file path from tool input
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
inp = data.get('tool_input', {})
print(inp.get('file_path', ''))
" 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Log file location — one per session, keyed by CLAUDE_SESSION_ID or PID
LOG_DIR="/tmp/claude-context-logs"
mkdir -p "$LOG_DIR"
SESSION_ID="${CLAUDE_SESSION_ID:-$$}"
LOG_FILE="$LOG_DIR/reads-${SESSION_ID}.jsonl"

# Extract offset and limit
read -r OFFSET LIMIT <<< $(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
inp = data.get('tool_input', {})
print(inp.get('offset', 0), inp.get('limit', 0))
" 2>/dev/null)

# Check for re-read BEFORE logging
if [ -f "$LOG_FILE" ] && grep -q "\"file\":\"${FILE_PATH}\"" "$LOG_FILE"; then
  # Count previous reads of this file
  PREV_COUNT=$(grep -c "\"file\":\"${FILE_PATH}\"" "$LOG_FILE")
  echo "⚠️ Re-read detected: ${FILE_PATH} (read #$((PREV_COUNT + 1))). Consider using cached context from earlier in this conversation."
fi

# Always log the read
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "{\"ts\":\"${TIMESTAMP}\",\"file\":\"${FILE_PATH}\",\"offset\":${OFFSET},\"limit\":${LIMIT}}" >> "$LOG_FILE"

exit 0
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x .claude/hooks/post-read-logger.sh`

- [ ] **Step 3: Register the hook in settings.json**

Update `.claude/settings.json` to:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash .claude/statusline-command.sh"
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Read",
        "type": "command",
        "command": "bash .claude/hooks/post-read-logger.sh"
      }
    ]
  }
}
```

- [ ] **Step 4: Manual smoke test**

Run: `echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/test.txt","offset":0,"limit":100}}' | bash .claude/hooks/post-read-logger.sh`

Expected: no output (first read). Run again — expected: re-read warning.

Verify log: `cat /tmp/claude-context-logs/reads-*.jsonl`
Expected: two JSON lines with `/tmp/test.txt`.

Note: this tests the script in isolation. The hook registration in settings.json should be verified end-to-end in a real session (Task 7) — check that `reads-*.jsonl` is created after an actual Read tool call.

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/post-read-logger.sh .claude/settings.json
git commit -m "feat: add PostToolUse hook to log Read calls for context analysis"
```

---

## Task 2: Context Report Generator — Core Parsing

**Files:**
- Create: `src/agile_backlog/context_report.py`
- Create: `tests/test_context_report.py`

This module reads the JSON lines log and produces structured metrics.

### Step-by-step

- [ ] **Step 1: Write failing test for log parsing**

```python
# tests/test_context_report.py
import json
import tempfile
from pathlib import Path

from agile_backlog.context_report import parse_read_log


def test_parse_read_log_returns_entries():
    lines = [
        {"ts": "2026-03-24T10:00:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
        {"ts": "2026-03-24T10:00:05Z", "file": "/src/models.py", "offset": 0, "limit": 0},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")
        path = Path(f.name)

    entries = parse_read_log(path)
    assert len(entries) == 2
    assert entries[0]["file"] == "/src/app.py"
    assert entries[1]["limit"] == 0


def test_parse_read_log_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = Path(f.name)

    entries = parse_read_log(path)
    assert entries == []


def test_parse_read_log_skips_malformed_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"ts": "2026-03-24T10:00:00Z", "file": "/src/app.py", "offset": 0, "limit": 200}\n')
        f.write("not valid json\n")
        f.write('{"ts": "2026-03-24T10:00:05Z", "file": "/src/models.py", "offset": 0, "limit": 0}\n')
        path = Path(f.name)

    entries = parse_read_log(path)
    assert len(entries) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_context_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agile_backlog.context_report'`

- [ ] **Step 3: Implement parse_read_log**

```python
# src/agile_backlog/context_report.py
import json
from pathlib import Path


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_context_report.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/context_report.py tests/test_context_report.py
git commit -m "feat: add context report log parser"
```

---

## Task 3: Context Report Generator — Metrics & Waste Detection

**Files:**
- Modify: `src/agile_backlog/context_report.py`
- Modify: `tests/test_context_report.py`

Add the analysis engine: count reads per file, detect re-reads, estimate tokens, classify waste.

### Step-by-step

- [ ] **Step 1: Write failing tests for metrics**

```python
# Add to tests/test_context_report.py
from agile_backlog.context_report import analyze_reads


def test_analyze_reads_counts():
    entries = [
        {"ts": "2026-03-24T10:00:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
        {"ts": "2026-03-24T10:01:00Z", "file": "/src/models.py", "offset": 0, "limit": 100},
        {"ts": "2026-03-24T10:02:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
    ]
    report = analyze_reads(entries)
    assert report["total_reads"] == 3
    assert report["unique_files"] == 2
    assert report["reread_count"] == 1


def test_analyze_reads_top_files():
    entries = [
        {"ts": "2026-03-24T10:00:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
        {"ts": "2026-03-24T10:01:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
        {"ts": "2026-03-24T10:02:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
        {"ts": "2026-03-24T10:03:00Z", "file": "/src/models.py", "offset": 0, "limit": 100},
    ]
    report = analyze_reads(entries)
    assert report["top_files"][0]["file"] == "/src/app.py"
    assert report["top_files"][0]["count"] == 3


def test_analyze_reads_token_estimate():
    entries = [
        {"ts": "2026-03-24T10:00:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
    ]
    report = analyze_reads(entries)
    # 200 lines × 4 tokens/line = 800
    assert report["estimated_tokens"] == 800


def test_analyze_reads_token_estimate_full_file():
    entries = [
        {"ts": "2026-03-24T10:00:00Z", "file": "/src/app.py", "offset": 0, "limit": 0},
    ]
    report = analyze_reads(entries)
    # limit=0 means full file, estimated at 500 lines × 4 tokens = 2000
    assert report["estimated_tokens"] == 2000


def test_analyze_reads_wasteful_detection():
    entries = [
        {"ts": "2026-03-24T10:00:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
        {"ts": "2026-03-24T10:01:00Z", "file": "/src/app.py", "offset": 0, "limit": 200},
    ]
    report = analyze_reads(entries)
    assert len(report["wasteful_reads"]) == 1
    assert report["wasteful_reads"][0]["file"] == "/src/app.py"


def test_analyze_reads_empty():
    report = analyze_reads([])
    assert report["total_reads"] == 0
    assert report["unique_files"] == 0
    assert report["reread_count"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_context_report.py -v`
Expected: FAIL — `ImportError: cannot import name 'analyze_reads'`

- [ ] **Step 3: Implement analyze_reads**

```python
# Add to src/agile_backlog/context_report.py
from collections import Counter

TOKENS_PER_LINE = 4


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
    # limit=0 means "read whole file" in the Read tool — estimate 500 lines for those
    total_lines = sum(e.get("limit", 0) or 500 for e in entries)

    # Detect wasteful re-reads: same file + same offset/limit range, no edit in between
    seen: dict[str, dict] = {}  # file -> last read entry
    wasteful = []
    reread_count = 0
    for entry in entries:
        key = entry["file"]
        if key in seen:
            reread_count += 1
            prev = seen[key]
            if entry.get("offset") == prev.get("offset") and entry.get("limit") == prev.get("limit"):
                wasteful.append({"file": key, "count": file_counts[key], "range": f"{entry.get('offset', 0)}-{entry.get('limit', 0)}"})
        seen[key] = entry

    # Deduplicate wasteful entries per file
    wasteful_deduped = {w["file"]: w for w in wasteful}

    top_files = [{"file": f, "count": c} for f, c in file_counts.most_common(10)]

    return {
        "total_reads": len(entries),
        "unique_files": len(file_counts),
        "reread_count": reread_count,
        "reread_ratio": round(reread_count / len(entries), 2) if entries else 0.0,
        "estimated_tokens": total_lines * TOKENS_PER_LINE,
        "top_files": top_files,
        "wasteful_reads": list(wasteful_deduped.values()),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_context_report.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/context_report.py tests/test_context_report.py
git commit -m "feat: add context analysis metrics and waste detection"
```

---

## Task 4: Report Generation — JSON Output

**Files:**
- Modify: `src/agile_backlog/context_report.py`
- Modify: `tests/test_context_report.py`

Add the function that takes a log dir, finds session logs, and writes the sprint report JSON.

### Step-by-step

- [ ] **Step 1: Write failing test for report generation**

```python
# Add to tests/test_context_report.py
from agile_backlog.context_report import generate_sprint_report


def test_generate_sprint_report_creates_json(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "reads-session1.jsonl"
    log_file.write_text(
        '{"ts":"2026-03-24T10:00:00Z","file":"/src/app.py","offset":0,"limit":200}\n'
        '{"ts":"2026-03-24T10:01:00Z","file":"/src/app.py","offset":0,"limit":200}\n'
        '{"ts":"2026-03-24T10:02:00Z","file":"/src/models.py","offset":0,"limit":100}\n'
    )

    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    report_path = generate_sprint_report(log_dir, output_dir, sprint=23)

    assert report_path.exists()
    assert report_path.name == "SPRINT23_CONTEXT_REPORT.json"

    report = json.loads(report_path.read_text())
    assert report["sprint"] == 23
    assert report["total_reads"] == 3
    assert report["unique_files"] == 2
    assert "sessions" in report


def test_generate_sprint_report_no_logs(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    output_dir = tmp_path / "reports"
    output_dir.mkdir()

    report_path = generate_sprint_report(log_dir, output_dir, sprint=23)
    report = json.loads(report_path.read_text())
    assert report["total_reads"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_context_report.py::test_generate_sprint_report_creates_json -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement generate_sprint_report**

```python
# Add to src/agile_backlog/context_report.py
def generate_sprint_report(log_dir: Path, output_dir: Path, sprint: int) -> Path:
    all_entries = []
    sessions = []

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_context_report.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/agile_backlog/context_report.py tests/test_context_report.py
git commit -m "feat: add sprint context report JSON generation"
```

---

## Task 5: CLI Command for Report Generation

**Files:**
- Modify: `src/agile_backlog/cli.py`
- Modify: `tests/test_cli.py`

Add a `context-report` CLI command so it can be invoked from the sprint-end skill.

### Step-by-step

- [ ] **Step 1: Write failing test for CLI command**

```python
# Add to tests/test_cli.py
from click.testing import CliRunner

def test_context_report_command(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "reads-test.jsonl"
    log_file.write_text(
        '{"ts":"2026-03-24T10:00:00Z","file":"/src/app.py","offset":0,"limit":200}\n'
    )
    output_dir = tmp_path / "reports"

    runner = CliRunner()
    result = runner.invoke(main, ["context-report", "--log-dir", str(log_dir), "--output-dir", str(output_dir), "--sprint", "23"])
    assert result.exit_code == 0
    assert "SPRINT23_CONTEXT_REPORT.json" in result.output
    assert (output_dir / "SPRINT23_CONTEXT_REPORT.json").exists()
```

Note: the Click group is `main` — import with `from agile_backlog.cli import main` and invoke as `runner.invoke(main, [...])`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli.py::test_context_report_command -v`
Expected: FAIL

- [ ] **Step 3: Implement CLI command**

Add to `src/agile_backlog/cli.py`:

```python
from agile_backlog.context_report import generate_sprint_report

@main.command("context-report")
@click.option("--log-dir", default="/tmp/claude-context-logs", help="Directory with session read logs")
@click.option("--output-dir", default="docs/sprints", help="Output directory for report")
@click.option("--sprint", required=True, type=int, help="Sprint number")
def context_report(log_dir, output_dir, sprint):
    report_path = generate_sprint_report(Path(log_dir), Path(output_dir), sprint)
    click.echo(f"Report generated: {report_path}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_cli.py::test_context_report_command -v`
Expected: PASS

- [ ] **Step 5: Run full test suite + lint**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
Expected: all passing, lint clean

- [ ] **Step 6: Commit**

```bash
git add src/agile_backlog/cli.py tests/test_cli.py
git commit -m "feat: add context-report CLI command"
```

---

## Task 6: Sprint-End Skill Integration

**Files:**
- Modify: `.claude/skills/sprint-end/SKILL.md`

Add a step in Phase 3 (Knowledge Transfer) to generate the context report.

### Step-by-step

- [ ] **Step 1: Add context report step to sprint-end skill**

Add after the handover doc creation in Phase 3, before the MEMORY.md audit:

```markdown
### Phase 3c: Context Efficiency Report

Generate the context analysis report for this sprint:

\`\`\`bash
{backlog_commands.context_report} --sprint {N} --log-dir /tmp/claude-context-logs --output-dir docs/sprints
\`\`\`

If log data exists, include a brief summary in the handover doc:
- Total reads / unique files / re-read ratio
- Top 3 most-read files
- Any wasteful re-reads to address

If no log data exists (hook wasn't active for this sprint), skip and note "No context logs available."

Add the report JSON to the commit:
\`\`\`bash
git add docs/sprints/SPRINT{N}_CONTEXT_REPORT.json
\`\`\`
```

- [ ] **Step 2: Add context-report command to sprint-config.yaml**

Add to `backlog_commands` section:

```yaml
  context_report: ".venv/bin/agile-backlog context-report"
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/sprint-end/SKILL.md .claude/sprint-config.yaml
git commit -m "feat: integrate context report into sprint-end workflow"
```

---

## Task 7: Final Integration Test & Cleanup

**Files:**
- All files from prior tasks

### Step-by-step

- [ ] **Step 1: End-to-end manual test**

Create a fake session log and generate a report:

```bash
mkdir -p /tmp/claude-context-logs
echo '{"ts":"2026-03-24T10:00:00Z","file":"src/app.py","offset":0,"limit":200}' > /tmp/claude-context-logs/reads-test.jsonl
echo '{"ts":"2026-03-24T10:01:00Z","file":"src/app.py","offset":0,"limit":200}' >> /tmp/claude-context-logs/reads-test.jsonl
echo '{"ts":"2026-03-24T10:02:00Z","file":"src/models.py","offset":0,"limit":100}' >> /tmp/claude-context-logs/reads-test.jsonl
.venv/bin/agile-backlog context-report --sprint 23 --log-dir /tmp/claude-context-logs --output-dir /tmp/test-reports
cat /tmp/test-reports/SPRINT23_CONTEXT_REPORT.json
```

Expected: valid JSON with 3 total reads, 2 unique files, 1 re-read.

- [ ] **Step 2: Run full CI**

Run: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest tests/ -v`
Expected: all passing, lint clean

- [ ] **Step 3: Clean up test artifacts**

```bash
rm -rf /tmp/claude-context-logs/reads-test.jsonl /tmp/test-reports
```

- [ ] **Step 4: Final commit if any formatting fixes needed**

```bash
git add -A
git commit -m "chore: context analysis cleanup and formatting"
```
