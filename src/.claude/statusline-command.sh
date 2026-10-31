#!/usr/bin/env bash
# Claude Code status line - mirrors Starship-style prompt with Claude context

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // empty')
# Live session effort first; fall back to the saved default
effort=$(echo "$input" | jq -r '.effort.level // empty')
if [ -z "$effort" ]; then
  effort=$(jq -r '.effortLevel // empty' ~/.claude/settings.json 2>/dev/null)
fi

# Shorten home directory to ~
home="$HOME"
short_cwd="${cwd/#$home/~}"

# Git branch (skip optional lock to avoid blocking)
branch=""
if git -C "$cwd" rev-parse --is-inside-work-tree --no-optional-locks >/dev/null 2>&1; then
  branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
fi

# Build the status line
parts=()
parts+=("$(printf '\033[34m%s\033[0m' "$short_cwd")")

if [ -n "$branch" ]; then
  parts+=("$(printf '\033[35m(%s)\033[0m' "$branch")")
fi

if [ -n "$model" ]; then
  parts+=("$(printf '\033[36m%s\033[0m' "$model")")
fi

if [ -n "$effort" ]; then
  parts+=("$(printf '\033[32m(%s)\033[0m' "$effort")")
fi

if [ -n "$used_pct" ]; then
  ctx_str=$(printf '%.0f%%' "$used_pct")
  if [ -n "$ctx_size" ]; then
    if [ "$ctx_size" -ge 1000000 ] 2>/dev/null; then
      ctx_k=$(echo "$ctx_size" | awk '{printf "%dM", $1/1000000}')
    else
      ctx_k=$(echo "$ctx_size" | awk '{printf "%dK", $1/1000}')
    fi
    ctx_str="${ctx_str} (${ctx_k})"
  fi
  parts+=("$(printf '\033[33m%s\033[0m' "$ctx_str")")
fi

printf '%s' "${parts[*]}"
