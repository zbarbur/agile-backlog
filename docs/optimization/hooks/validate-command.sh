#!/bin/bash
# .claude/hooks/validate-command.sh
# PreToolUse hook — blocks bash commands that should go through a skill
# Exit 0 = allow, structured JSON with deny = block

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check Bash tool
[ "$TOOL_NAME" != "Bash" ] && exit 0
[ -z "$COMMAND" ] && exit 0

# Allow safe utility commands that never need skill lookup
SAFE_PATTERNS="^(cd|ls|cat|echo|pwd|mkdir|cp|mv|head|tail|wc|grep|find|which|type|chmod|chown|git status|git log|git diff|git branch|git checkout|git add|git commit|git push|git pull|npm install|pip install|node |python3? )"
echo "$COMMAND" | grep -qiE "$SAFE_PATTERNS" && exit 0

# ============================================================
# CUSTOMIZE: Add patterns matching your project's skill domains
# These commands will be BLOCKED with a message to use the skill
# ============================================================
SKILL_PATTERNS="(gcloud|bq |kubectl|docker compose|docker build|terraform|deploy|migrate|rollback)"
if echo "$COMMAND" | grep -qiE "$SKILL_PATTERNS"; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "BLOCKED: This command matches a skill-covered domain. Check your skills first (use /cli-reference, /deploy, etc.). Read the skill file, find the correct command, then retry."
    }
  }'
  exit 0
fi

# Log non-skill commands for sprint analysis
mkdir -p ~/.claude/logs
jq -n --arg cmd "$COMMAND" --arg ts "$(date -Iseconds)" \
  '{timestamp: $ts, command: $cmd, source: "direct"}' \
  >> ~/.claude/logs/bash-commands.jsonl

exit 0
