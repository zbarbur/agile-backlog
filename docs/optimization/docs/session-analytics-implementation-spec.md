# Implementation Spec: Session Analytics & Monitoring

## Objective

Build an automated session analytics system that captures performance metrics at the end of every Claude Code session, accumulates data over time, and enables sprint retrospectives — all without consuming context window tokens.

---

## Part 1: Hooks Setup

### 1.1 SessionStart Hook — Capture Baseline

Create `.claude/hooks/capture-start.sh`:

```bash
#!/bin/bash
# Captures session start metadata
# This runs once at session startup — the agent never sees this data

data=$(cat)
session_id=$(echo "$data" | jq -r '.session_id')
timestamp=$(date -Iseconds)

mkdir -p ~/.claude/session-stats

jq -n \
  --arg sid "$session_id" \
  --arg ts "$timestamp" \
  --arg cwd "$(pwd)" \
  --arg branch "$(git branch --show-current 2>/dev/null || echo 'none')" \
  '{session_id: $sid, start_time: $ts, cwd: $cwd, branch: $branch}' \
  > ~/.claude/session-stats/current-session.json
```

Make executable: `chmod +x .claude/hooks/capture-start.sh`

### 1.2 SessionEnd Hook — Run Analytics

Create `.claude/hooks/session-report.sh`:

```bash
#!/bin/bash
# Runs at session end — generates full analytics report
# Combines: ccstats output + custom JSONL analysis + start metadata

mkdir -p ~/.claude/session-stats
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="$HOME/.claude/session-stats/report-${TIMESTAMP}.yaml"

# 1. Capture ccstats
CCSTATS=$(npx ccstats -o yaml 2>/dev/null || echo "ccstats_error: true")

# 2. Load start metadata
START_META="{}"
if [ -f ~/.claude/session-stats/current-session.json ]; then
  START_META=$(cat ~/.claude/session-stats/current-session.json)
fi

# 3. Run custom JSONL analysis
CUSTOM_STATS=$(python3 .claude/hooks/analyze-session.py 2>/dev/null || echo "custom_analysis_error: true")

# 4. Combine into report
{
  echo "---"
  echo "report_generated: $(date -Iseconds)"
  echo ""
  echo "# Session Start Info"
  echo "start_info:"
  echo "$START_META" | jq -r 'to_entries[] | "  \(.key): \(.value)"'
  echo ""
  echo "# ccstats Output"
  echo "ccstats:"
  echo "$CCSTATS" | sed 's/^/  /'
  echo ""
  echo "# Custom Analysis"
  echo "$CUSTOM_STATS"
} > "$REPORT_FILE"

# Cleanup
rm -f ~/.claude/session-stats/current-session.json
```

Make executable: `chmod +x .claude/hooks/session-report.sh`

### 1.3 UserPromptSubmit Hook — Inject Reminders

Create `.claude/hooks/inject-reminders.sh`:

```bash
#!/bin/bash
# Injects skill/memory reminders before every prompt is processed
# stdout is added to Claude's context

echo "REMINDER: Before acting, check if a skill covers this task."
echo "Available skills:"
for skill in .claude/skills/*/SKILL.md; do
  name=$(grep '^name:' "$skill" 2>/dev/null | head -1 | sed 's/name: *//')
  [ -n "$name" ] && echo "  - /$name"
done
echo "Check .claude/MEMORY.md for project state. DO NOT guess commands."
```

Make executable: `chmod +x .claude/hooks/inject-reminders.sh`

### 1.4 PreToolUse Hook — Enforce Skill Usage

Create `.claude/hooks/validate-command.sh`:

```bash
#!/bin/bash
# Blocks bash commands that should go through a skill
# Exit 0 = allow, structured JSON with deny = block

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check Bash tool
[ "$TOOL_NAME" != "Bash" ] && exit 0
[ -z "$COMMAND" ] && exit 0

# Allow safe utility commands
SAFE_PATTERNS="^(cd|ls|cat|echo|pwd|mkdir|cp|mv|head|tail|wc|grep|find|which|type|git status|git log|git diff|git branch|git checkout|git add|git commit|git push|git pull|npm install|pip install)"
echo "$COMMAND" | grep -qiE "$SAFE_PATTERNS" && exit 0

# Block commands that match skill-covered domains
# CUSTOMIZE THIS LIST for your project
SKILL_PATTERNS="(gcloud|bq |kubectl|docker compose|docker build|terraform|deploy|migrate|rollback)"
if echo "$COMMAND" | grep -qiE "$SKILL_PATTERNS"; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "BLOCKED: This command matches a skill-covered domain. Check your skills with /cli-reference or /deploy first. Read the skill file, find the correct command, then retry."
    }
  }'
  exit 0
fi

# Log non-skill commands for analysis
mkdir -p ~/.claude/logs
jq -n --arg cmd "$COMMAND" --arg ts "$(date -Iseconds)" \
  '{timestamp: $ts, command: $cmd, source: "direct"}' \
  >> ~/.claude/logs/bash-commands.jsonl

exit 0
```

Make executable: `chmod +x .claude/hooks/validate-command.sh`

### 1.5 SessionStart (compact) Hook — Post-Compact Recovery

Inline in settings.json — no separate script needed.

### 1.6 Register All Hooks

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/capture-start.sh",
            "once": true
          }
        ]
      },
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Post-compact: Re-read CLAUDE.md. Check skills before acting. DO NOT guess commands.'"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/inject-reminders.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/validate-command.sh"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/session-report.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Part 2: Custom JSONL Analyzer

### 2.1 Purpose

Parses the raw session JSONL logs in `~/.claude/projects/` to extract metrics that ccstats doesn't provide: skill invocations, command sources, and PreToolUse denials.

### 2.2 Implementation

Create `.claude/hooks/analyze-session.py`:

**Input:** Reads the most recent JSONL session file for the current project from `~/.claude/projects/`

**Output:** YAML-formatted stats to stdout

**Metrics to extract:**

1. **Skill invocations** — count how many times each skill file was read (look for Read/View tool calls targeting `.claude/skills/*/SKILL.md` or `~/.claude/skills/*/SKILL.md`)

2. **Direct bash commands** — count bash tool calls, categorize:
   - Skill-backed (preceded by a skill file read within the last 3 tool calls)
   - Direct (no preceding skill read)
   - Safe utility (matches safe pattern list: cd, ls, cat, git status, etc.)

3. **PreToolUse denials** — count entries where a tool call was denied by a hook (look for hook denial messages in the transcript)

4. **Files modified** — list of files written or edited via Write/Edit tools

5. **Web searches** — count of web search tool calls (indicates potential local knowledge gaps)

6. **Compliance ratio** — (skill-backed commands) / (skill-backed + direct commands) as a percentage

**Output format:**

```yaml
custom_analysis:
  skill_invocations:
    cli-reference: 5
    api-reference: 2
    testing: 3
  command_breakdown:
    total_bash: 24
    skill_backed: 15
    direct: 4
    safe_utility: 5
  compliance_ratio: 79%
  pretool_denials: 2
  web_searches: 1
  files_modified:
    - src/connector/index.ts
    - src/models/account.ts
```

### 2.3 JSONL Structure Reference

The JSONL files contain one JSON object per line. Key message types to parse:

- **Tool calls:** `{"type": "tool_use", "name": "Bash", "input": {"command": "..."}}`
- **Tool results:** `{"type": "tool_result", "content": "..."}`
- **Assistant messages:** `{"type": "assistant", "content": [...]}`
- **Content blocks** within assistant messages may contain `{"type": "tool_use", ...}` blocks

Note: The exact schema may vary. Read a sample JSONL file first to understand the structure before writing the parser. Use defensive parsing — skip malformed lines, handle missing fields gracefully.

### 2.4 Error Handling

- If no JSONL file found: output `custom_analysis_error: "No session file found"`
- If parsing fails: output `custom_analysis_error: "Parse failed"` with the error
- Never crash the hook — always exit 0 and output something

---

## Part 3: Sprint Retrospective

### 3.1 Retrospective Script

Create `.claude/hooks/sprint-retro.sh`:

**Input:** All report files in `~/.claude/session-stats/report-*.yaml` within a date range (default: last 7 days)

**Output:** A summary report saved to `~/.claude/session-stats/retro-{date}.md`

**What to aggregate:**

1. **Session count** and total duration
2. **Average compliance ratio** across sessions — trending up or down?
3. **Most/least used skills** — are any skills never invoked? (description needs fixing)
4. **PreToolUse denial trend** — decreasing = setup is improving
5. **Average ending context %** — are sessions scoped well?
6. **Web search count** — are there knowledge gaps that should become skills?
7. **Top direct commands** — commands run without skill backing, candidates for new skills
8. **Actionable recommendations** based on the data:
   - Skills with 0 invocations → review their descriptions
   - Compliance ratio < 70% → strengthen CLAUDE.md enforcement
   - Average context > 70% → sessions are too long, scope smaller
   - Repeated direct commands → create a skill for them

**Output format (markdown):**

```markdown
# Sprint Retrospective: [date range]

## Summary
- Sessions: X
- Avg compliance: X%
- Avg ending context: X%
- Total PreToolUse denials: X

## Skill Usage
| Skill | Invocations | Trend |
|-------|-------------|-------|
| cli-reference | 23 | ↑ |
| testing | 5 | → |
| database | 0 | ⚠️ never used |

## Top Unskilled Commands
| Command Pattern | Count | Action |
|----------------|-------|--------|
| docker build ... | 8 | Create /docker skill |
| bq query ... | 3 | Covered by /bigquery — check description |

## Recommendations
1. [data-driven recommendation]
2. [data-driven recommendation]
```

### 3.2 Running the Retrospective

Add a slash command so you can trigger it manually:

Create `.claude/skills/sprint-retro/SKILL.md`:

```yaml
---
name: sprint-retro
description: >
  USE THIS to run a sprint retrospective analyzing session stats,
  skill usage, compliance ratio, and context efficiency trends.
  Generates actionable recommendations for improving the agent setup.
---
```

Content:

```markdown
# Sprint Retrospective

Run the retrospective script and analyze the results:

1. Execute: `bash .claude/hooks/sprint-retro.sh`
2. Read the generated report in `~/.claude/session-stats/retro-*.md`
3. Present findings to the user
4. Suggest specific changes to CLAUDE.md and skill descriptions
5. If approved, implement the changes
```

Then run it anytime with:
```
/sprint-retro
```

---

## Part 4: Status Line

### 4.1 Setup

Create `~/.claude/statusline.sh`:

```bash
#!/bin/bash
data=$(cat)
pct=$(echo "$data" | jq -r '.context.used_percentage // 0')
model=$(echo "$data" | jq -r '.model // "unknown"')
branch=$(git branch --show-current 2>/dev/null || echo "no-git")

filled=$((pct / 10))
empty=$((10 - filled))
bar=$(printf '%0.s▓' $(seq 1 $filled))
bar+=$(printf '%0.s░' $(seq 1 $empty))

if [ "$pct" -lt 50 ]; then color="32"
elif [ "$pct" -lt 70 ]; then color="33"
else color="31"; fi

printf "\e[${color}m%s %d%%\e[0m | %s | %s" \
  "$bar" "$pct" "$model" "$branch"
```

Make executable: `chmod +x ~/.claude/statusline.sh`

Register via `/statusline` command or add path to settings.

---

## Part 5: File Structure

When complete, the file structure should be:

```
.claude/
  settings.json                        # Hook registrations
  hooks/
    capture-start.sh                   # SessionStart: save baseline
    inject-reminders.sh                # UserPromptSubmit: inject context
    validate-command.sh                # PreToolUse: enforce skills
    session-report.sh                  # SessionEnd: generate report
    analyze-session.py                 # Custom JSONL analyzer
    sprint-retro.sh                    # Sprint retrospective generator
  skills/
    sprint-retro/SKILL.md             # /sprint-retro command
  MEMORY.md                            # Project state (existing)
  SESSION_STATE.md                     # Handoff notes (existing)
~/.claude/
  statusline.sh                        # Status line script
  session-stats/                       # Auto-generated reports
    current-session.json               # Temp: current session start data
    report-YYYYMMDD-HHMMSS.yaml       # Per-session reports
    retro-YYYY-MM-DD.md               # Sprint retrospectives
```

---

## Part 6: Implementation Order

1. **Create directory structure** — `.claude/hooks/`, ensure `~/.claude/session-stats/` exists
2. **Status line** — quickest win, immediate visibility
3. **validate-command.sh** — the enforcement hook, biggest impact on skill compliance
4. **inject-reminders.sh** — soft reminder layer
5. **capture-start.sh** — baseline capture
6. **settings.json** — register all hooks
7. **analyze-session.py** — custom JSONL parser (most complex piece)
8. **session-report.sh** — ties ccstats + custom analysis together
9. **sprint-retro.sh** + skill — retrospective workflow
10. **Test the full pipeline** — run a short session, verify reports generate correctly

---

## Part 7: Customization Required

The following must be customized for your specific project:

1. **`validate-command.sh` → `SKILL_PATTERNS`** — add patterns matching your project's skill-covered domains (currently has gcloud, bq, kubectl, docker, terraform, deploy, migrate as examples)

2. **`validate-command.sh` → `SAFE_PATTERNS`** — adjust the list of commands that should always be allowed without skill checks

3. **`inject-reminders.sh`** — verify the skill directory path matches your project structure

4. **`analyze-session.py` → JSONL parsing** — read a sample JSONL file from `~/.claude/projects/` first to understand the exact schema before writing the parser. The schema is not guaranteed stable — use defensive parsing.

---

## Dependencies

- `jq` — JSON parsing in bash (should be pre-installed)
- `python3` — for the JSONL analyzer
- `npx ccstats` — for base session statistics (install: `npm install -g ccstats` or use `npx ccstats@latest`)
- `git` — for branch detection in status line
