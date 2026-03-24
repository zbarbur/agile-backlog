#!/bin/bash
# .claude/hooks/inject-reminders.sh
# UserPromptSubmit hook — injects skill/memory reminders before every prompt
# stdout is added to Claude's context

echo "REMINDER: Before acting, check if a skill covers this task."
echo "Available skills:"
for skill in .claude/skills/*/SKILL.md; do
  name=$(grep '^name:' "$skill" 2>/dev/null | head -1 | sed 's/name: *//')
  [ -n "$name" ] && echo "  - /$name"
done
echo "Check .claude/MEMORY.md for project state. DO NOT guess commands."
