#!/bin/bash
# Install optimize-agent skill for Claude Code
# Run: chmod +x install.sh && ./install.sh

SKILL_DIR="$HOME/.claude/skills/optimize-agent"

# Create directory
mkdir -p "$SKILL_DIR"

# Copy files
cp optimize-agent/SKILL.md "$SKILL_DIR/SKILL.md"
cp optimize-agent/full-guide.md "$SKILL_DIR/full-guide.md"

echo "✅ Installed to $SKILL_DIR"
echo ""
echo "Usage in Claude Code:"
echo "  /optimize-agent                          → Run full audit"
echo "  /optimize-agent Review my CLAUDE.md      → Targeted audit"
echo "  /optimize-agent Fix my skill descriptions → Specific fix"
echo ""
echo "Or just ask Claude Code naturally:"
echo "  'Review my setup and tell me what to improve'"
echo "  'Why does the agent keep guessing commands?'"
echo ""
echo "The skill will auto-invoke when Claude detects optimization tasks."
