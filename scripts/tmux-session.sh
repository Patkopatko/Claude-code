#!/usr/bin/env bash
#
# tmux-session.sh — create-or-attach a named, persistent tmux session.
#
# This is the command you run on the Mac Studio (and the one Blink runs for you
# from the iPhone). It is idempotent: if the session exists you attach to it,
# otherwise it is created. Sessions survive disconnects, so you can drop off
# cellular and pick the exact same shell back up later.
#
# Usage:
#   ./scripts/tmux-session.sh [session-name]   # default: "main"
#   ./scripts/tmux-session.sh -l               # list existing sessions
#   ./scripts/tmux-session.sh -k <name>        # kill a session
#
# Tip: put this on your PATH (or alias it) so the iPhone-side command is short:
#   alias t='~/Claude-code/scripts/tmux-session.sh'

set -euo pipefail

command -v tmux >/dev/null 2>&1 || { echo "tmux is not installed. Run scripts/setup-mac-studio.sh first." >&2; exit 1; }

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

case "${1:-}" in
  -h|--help) usage 0 ;;
  -l|--list)
    tmux ls 2>/dev/null || echo "No tmux sessions running."
    exit 0
    ;;
  -k|--kill)
    [[ -n "${2:-}" ]] || { echo "Usage: $0 -k <session-name>" >&2; exit 2; }
    tmux kill-session -t "$2"
    echo "Killed session: $2"
    exit 0
    ;;
esac

SESSION="${1:-main}"

# If we are already inside tmux, switch instead of nesting.
if [[ -n "${TMUX:-}" ]]; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    exec tmux switch-client -t "$SESSION"
  else
    tmux new-session -d -s "$SESSION"
    exec tmux switch-client -t "$SESSION"
  fi
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Attaching to existing session: $SESSION"
  exec tmux attach-session -t "$SESSION"
else
  echo "Creating new session: $SESSION"
  exec tmux new-session -s "$SESSION"
fi
