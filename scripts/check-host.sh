#!/usr/bin/env bash
#
# check-host.sh — run this ON your infrastructure box (the one that is
# "full of life") to confirm it is ready to accept iPhone connections.
#
# It installs nothing and changes nothing except, optionally, linking the
# bundled tmux.conf. It just verifies the pieces are in place and prints the
# exact command to type in Blink Shell on the iPhone.
#
# Usage:
#   ./scripts/check-host.sh            # verify + print connect command
#   ./scripts/check-host.sh --link     # also symlink config/tmux.conf -> ~/.tmux.conf

set -euo pipefail

ok()   { printf '\033[1;32m[ok]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
bad()  { printf '\033[1;31m[x]\033[0m %s\n' "$*"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
READY=1

echo "== Checking this host for iPhone-over-Tailscale access =="

# 1. Tailscale up, and what is our tailnet name/IP?
TS_BIN="$(command -v tailscale || true)"
[[ -z "$TS_BIN" && -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]] && TS_BIN="/Applications/Tailscale.app/Contents/MacOS/Tailscale"

if [[ -n "$TS_BIN" ]]; then
  if "$TS_BIN" status >/dev/null 2>&1; then
    TS_IP="$("$TS_BIN" ip -4 2>/dev/null | head -n1 || true)"
    TS_NAME="$("$TS_BIN" status --json 2>/dev/null | grep -o '"DNSName":[^,]*' | head -n1 | cut -d'"' -f4 | sed 's/\.$//' || true)"
    ok "Tailscale is up. IP: ${TS_IP:-?}  name: ${TS_NAME:-?}"
  else
    bad "Tailscale is installed but not logged in. Run: sudo tailscale up"
    READY=0
  fi
else
  bad "Tailscale not found on this host. Install it and run 'tailscale up'."
  READY=0
fi

# 2. SSH server reachable? (so Blink can connect)
if command -v launchctl >/dev/null 2>&1; then
  # macOS: Remote Login
  if systemsetup -getremotelogin 2>/dev/null | grep -qi "On"; then
    ok "Remote Login (SSH) is ON."
  else
    bad "Remote Login is OFF. Enable: System Settings > General > Sharing > Remote Login (or: sudo systemsetup -setremotelogin on)"
    READY=0
  fi
elif command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet ssh 2>/dev/null; then
  ok "sshd is active."
elif command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet sshd 2>/dev/null; then
  ok "sshd is active."
else
  warn "Could not confirm an SSH server is running. Make sure sshd is enabled."
fi

# 3. tmux present + current sessions
if command -v tmux >/dev/null 2>&1; then
  ok "tmux present: $(tmux -V)"
  echo "   Existing sessions:"
  tmux ls 2>/dev/null | sed 's/^/     /' || echo "     (none yet — one will be created on first connect)"
else
  bad "tmux not found. Install it (e.g. 'brew install tmux' / 'apt install tmux')."
  READY=0
fi

# 4. Optional: link the mobile-friendly tmux config
if [[ "${1:-}" == "--link" ]]; then
  SRC="$REPO_ROOT/config/tmux.conf"; DST="$HOME/.tmux.conf"
  if [[ -f "$SRC" ]]; then
    [[ -e "$DST" && ! -L "$DST" ]] && { cp "$DST" "$DST.bak"; warn "backed up existing ~/.tmux.conf -> ~/.tmux.conf.bak"; }
    ln -sf "$SRC" "$DST"; ok "linked phone-friendly tmux.conf -> ~/.tmux.conf"
  fi
fi

echo
echo "== iPhone connect command (paste into Blink Shell) =="
USER_NAME="$(whoami)"
TARGET="${TS_NAME:-${TS_IP:-YOUR-HOST}}"
echo "   ssh ${USER_NAME}@${TARGET} -t '~/Claude-code/scripts/tmux-session.sh main'"
echo "   # or just:  ssh ${USER_NAME}@${TARGET}  then:  tmux attach -t main   (or: claude)"
echo

[[ "$READY" == "1" ]] && ok "Host looks ready." || bad "Fix the items marked [x] above, then re-run."
