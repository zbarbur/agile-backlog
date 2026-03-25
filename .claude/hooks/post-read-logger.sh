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

# Log file location — one per session
# Try CLAUDE_SESSION_ID first, then TERM_SESSION_ID (stable per terminal), then fallback to date
LOG_DIR="/tmp/claude-context-logs"
mkdir -p "$LOG_DIR"
SESSION_ID="${CLAUDE_SESSION_ID:-${TERM_SESSION_ID:-$(date +%Y%m%d-%H%M)}}"
# Sanitize colons from session IDs for safe filenames
SESSION_ID="${SESSION_ID//:/-}"
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
