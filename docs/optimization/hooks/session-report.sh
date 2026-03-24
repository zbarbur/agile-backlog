#!/bin/bash
# .claude/hooks/session-report.sh
# SessionEnd hook — generates full session analytics report
# Combines: ccstats + custom JSONL analysis + start metadata

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

# 3. Run custom JSONL analysis (if analyzer exists)
CUSTOM_STATS="custom_analysis: not_configured"
if [ -f .claude/hooks/analyze-session.py ]; then
  CUSTOM_STATS=$(python3 .claude/hooks/analyze-session.py 2>/dev/null || echo "custom_analysis_error: true")
fi

# 4. Combine into report
{
  echo "---"
  echo "report_generated: $(date -Iseconds)"
  echo ""
  echo "# Session Start Info"
  echo "start_info:"
  echo "$START_META" | jq -r 'to_entries[] | "  \(.key): \(.value)"' 2>/dev/null || echo "  error: could not parse start metadata"
  echo ""
  echo "# ccstats Output"
  echo "ccstats:"
  echo "$CCSTATS" | sed 's/^/  /'
  echo ""
  echo "# Custom Analysis"
  echo "$CUSTOM_STATS"
} > "$REPORT_FILE"

# Cleanup temp file
rm -f ~/.claude/session-stats/current-session.json
