#!/bin/bash
# .claude/hooks/capture-start.sh
# SessionStart hook — captures session baseline metadata
# The agent never sees this data — zero token cost

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
