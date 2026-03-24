#!/usr/bin/env bash
# Claude Code status line — project · sprint · branch · model · effort · context

input=$(cat)

# --- Project name (basename of git root, fallback to basename of $PWD) ---
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -n "$git_root" ]; then
  project=$(basename "$git_root")
else
  project=$(basename "$PWD")
fi

# --- Current sprint (from .claude/sprint-config.yaml relative to git root) ---
sprint_config=""
[ -n "$git_root" ] && sprint_config="${git_root}/.claude/sprint-config.yaml"
if [ -n "$sprint_config" ] && [ -f "$sprint_config" ]; then
  sprint=$(grep current_sprint "$sprint_config" 2>/dev/null | awk '{print $2}')
else
  sprint=""
fi
sprint_display="${sprint:+S${sprint}}"

# --- Git branch ---
branch=$(git branch --show-current 2>/dev/null)

# --- Model (extract from model.id: "claude-sonnet-4-6" -> "sonnet", "claude-opus-4-6" -> "opus") ---
model_id=$(echo "$input" | jq -r '.model.id // ""')
# Split on "-", take the second segment (index 1): claude-SEGMENT-...
model_short=$(echo "$model_id" | awk -F'-' '{print $2}')
[ -z "$model_short" ] && model_short="unknown"

# --- Effort level ---
# Priority: stdin JSON → project .claude/settings.local.json → ~/.claude/settings.json
effort_raw=$(echo "$input" | jq -r '.effortLevel // empty' 2>/dev/null)
if [ -z "$effort_raw" ] && [ -n "$git_root" ] && [ -f "${git_root}/.claude/settings.local.json" ]; then
  effort_raw=$(jq -r '.effortLevel // empty' "${git_root}/.claude/settings.local.json" 2>/dev/null)
fi
if [ -z "$effort_raw" ]; then
  effort_raw=$(jq -r '.effortLevel // empty' ~/.claude/settings.json 2>/dev/null)
fi
if [ -n "$effort_raw" ]; then
  case "$effort_raw" in
    high)   effort_display="⚡high" ;;
    medium|med) effort_display="⚡med" ;;
    low)    effort_display="⚡low" ;;
    *)      effort_display="⚡${effort_raw}" ;;
  esac
else
  effort_display=""
fi

# --- Context window ---
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# --- ANSI colours ---
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"

# Progress bar: 6 chars wide, colour-coded by usage
if [ -n "$used_pct" ]; then
  pct_int=$(printf "%.0f" "$used_pct")

  if   [ "$pct_int" -lt 40 ]; then BAR_COLOR="\033[32m"       # green
  elif [ "$pct_int" -lt 70 ]; then BAR_COLOR="\033[33m"       # yellow
  elif [ "$pct_int" -lt 85 ]; then BAR_COLOR="\033[38;5;208m" # orange
  else                              BAR_COLOR="\033[31m"       # red
  fi

  # 6-char bar
  filled=$(( (pct_int * 6 + 50) / 100 ))
  [ "$filled" -gt 6 ] && filled=6
  empty=$(( 6 - filled ))
  bar=""
  for i in $(seq 1 $filled); do bar="${bar}█"; done
  for i in $(seq 1 $empty);  do bar="${bar}░"; done

  ctx_display="${BAR_COLOR}${bar}${RESET} ${DIM}${pct_int}%${RESET}"
else
  ctx_display="${DIM}--${RESET}"
fi

# --- Assemble: agile-backlog · S18 · main · sonnet · ⚡high · ctx: ████░░ 42% ---
sep="${DIM} · ${RESET}"

line="${BOLD}${project}${RESET}"
[ -n "$sprint_display" ] && line="${line}${sep}${DIM}${sprint_display}${RESET}"
[ -n "$branch" ]         && line="${line}${sep}${DIM}${branch}${RESET}"
line="${line}${sep}${DIM}${model_short}${RESET}"
[ -n "$effort_display" ] && line="${line}${sep}${DIM}${effort_display}${RESET}"
line="${line}${sep}${DIM}ctx:${RESET} %b"

printf "${line}\n" "$ctx_display"
