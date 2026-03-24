#!/bin/bash
# ~/.claude/statusline.sh
# chmod +x ~/.claude/statusline.sh
# Register via /statusline command or add path to settings

data=$(cat)
pct=$(echo "$data" | jq -r '.context.used_percentage // 0')
model=$(echo "$data" | jq -r '.model // "unknown"')
branch=$(git branch --show-current 2>/dev/null || echo "no-git")

filled=$((pct / 10))
empty=$((10 - filled))
bar=$(printf '%0.s▓' $(seq 1 $filled))
bar+=$(printf '%0.s░' $(seq 1 $empty))

if [ "$pct" -lt 50 ]; then color="32"    # green
elif [ "$pct" -lt 70 ]; then color="33"   # yellow
else color="31"; fi                        # red

printf "\e[${color}m%s %d%%\e[0m | %s | %s" \
  "$bar" "$pct" "$model" "$branch"
