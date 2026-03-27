#!/usr/bin/env bash
# PostToolUse hook — logs all tool calls and warns on re-reads
# Input: JSON on stdin with tool_name and tool_input fields
# Output: warning message to stdout (only on re-reads), exit 0 always

set -uo pipefail

# Read the hook input from stdin
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
if [ -z "$TOOL_NAME" ]; then
  exit 0
fi

# Log file location — one per session
LOG_DIR="/tmp/claude-context-logs"
mkdir -p "$LOG_DIR"
SESSION_ID="${CLAUDE_SESSION_ID:-${TERM_SESSION_ID:-$(date +%Y%m%d-%H%M)}}"
# Sanitize colons from session IDs for safe filenames
SESSION_ID=$(echo "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')
LOG_FILE="$LOG_DIR/tools-${SESSION_ID}.jsonl"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build log entry based on tool type using python3 for valid JSON
LOG_ENTRY=$(echo "$INPUT" | python3 -c "
import sys, json

data = json.load(sys.stdin)
tool = data.get('tool_name', '')
inp = data.get('tool_input', {})
ts = '$TIMESTAMP'

entry = {'ts': ts, 'tool': tool}

if tool == 'Read':
    entry['file'] = inp.get('file_path', '')
    entry['offset'] = inp.get('offset', 0) or 0
    entry['limit'] = inp.get('limit', 0) or 0
elif tool == 'Grep':
    entry['pattern'] = inp.get('pattern', '')
    entry['path'] = inp.get('path', '')
    entry['glob'] = inp.get('glob', '')
    entry['output_mode'] = inp.get('output_mode', '')
elif tool == 'Glob':
    entry['pattern'] = inp.get('pattern', '')
    entry['path'] = inp.get('path', '')
elif tool == 'Bash':
    cmd = inp.get('command', '')
    # Truncate long commands to 200 chars
    entry['command'] = cmd[:200] if len(cmd) > 200 else cmd
elif tool == 'WebFetch':
    entry['url'] = inp.get('url', '')
elif tool == 'Agent':
    prompt = inp.get('prompt', inp.get('task', ''))
    entry['prompt'] = prompt[:200] if len(prompt) > 200 else prompt
else:
    # Generic fallback — log tool_input keys
    entry['input_keys'] = list(inp.keys())[:10]

print(json.dumps(entry))
" 2>/dev/null)

if [ -z "$LOG_ENTRY" ]; then
  exit 0
fi

# Re-read detection for Read tool specifically
if [ "$TOOL_NAME" = "Read" ]; then
  FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))
" 2>/dev/null)

  if [ -n "$FILE_PATH" ] && [ -f "$LOG_FILE" ] && grep -q "\"tool\":[ ]*\"Read\".*\"file\":[ ]*\"${FILE_PATH}\"" "$LOG_FILE" 2>/dev/null; then
    PREV_COUNT=$(grep -c "\"file\":[ ]*\"${FILE_PATH}\"" "$LOG_FILE" 2>/dev/null)
    echo "⚠️ Re-read detected: ${FILE_PATH} (read #$((PREV_COUNT + 1))). Consider using cached context from earlier in this conversation."
  fi
fi

# Append log entry
echo "$LOG_ENTRY" >> "$LOG_FILE" 2>/dev/null

exit 0
