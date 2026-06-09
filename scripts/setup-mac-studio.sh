#!/usr/bin/env bash
#
# setup-mac-studio.sh
#
# Prepares a Mac Studio to host persistent tmux sessions that you can attach
# to from an iPhone over Tailscale using Blink Shell.
#
# What it does (idempotent — safe to re-run):
#   1. Installs Homebrew (if missing), tmux, and mosh.
#   2. Enables macOS Remote Login (SSH) so Blink can connect.
#   3. Installs the tmux-friendly config from ./config/tmux.conf.
#   4. Installs and brings up Tailscale, then prints the tailnet hostname/IP.
#   5. Prevents the Mac from sleeping so sessions stay alive (caffeinate hint).
#
# Usage:
#   ./scripts/setup-mac-studio.sh
#
# Re-run any time you change the bundled tmux config.

set -euo pipefail

# --- helpers ---------------------------------------------------------------

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ "$(uname -s)" == "Darwin" ]] || die "This script is for macOS (the Mac Studio). Run it there, not on the iPhone."

# --- 1. Homebrew + packages ------------------------------------------------

if ! command -v brew >/dev/null 2>&1; then
  log "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Make brew available in this shell (Apple Silicon path).
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
else
  log "Homebrew already installed."
fi

for pkg in tmux mosh; do
  if brew list --formula "$pkg" >/dev/null 2>&1; then
    log "$pkg already installed."
  else
    log "Installing $pkg..."
    brew install "$pkg"
  fi
done

# --- 2. Enable Remote Login (SSH) ------------------------------------------

if sudo systemsetup -getremotelogin 2>/dev/null | grep -qi "On"; then
  log "Remote Login (SSH) already enabled."
else
  log "Enabling Remote Login (SSH)... (you may be prompted for your password)"
  sudo systemsetup -setremotelogin on
fi

# --- 3. Install tmux config ------------------------------------------------

TMUX_CONF_SRC="$REPO_ROOT/config/tmux.conf"
TMUX_CONF_DST="$HOME/.tmux.conf"

if [[ -f "$TMUX_CONF_SRC" ]]; then
  if [[ -e "$TMUX_CONF_DST" && ! -L "$TMUX_CONF_DST" ]]; then
    log "Backing up existing ~/.tmux.conf to ~/.tmux.conf.bak"
    cp "$TMUX_CONF_DST" "$TMUX_CONF_DST.bak"
  fi
  log "Linking tmux config -> $TMUX_CONF_DST"
  ln -sf "$TMUX_CONF_SRC" "$TMUX_CONF_DST"
else
  warn "config/tmux.conf not found, skipping tmux config install."
fi

# --- 4. Tailscale ----------------------------------------------------------

if ! command -v tailscale >/dev/null 2>&1 && [[ ! -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]]; then
  log "Installing Tailscale..."
  brew install --cask tailscale
fi

# Resolve the tailscale CLI (cask app ships the binary inside the bundle).
TS_BIN="$(command -v tailscale || true)"
if [[ -z "$TS_BIN" && -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]]; then
  TS_BIN="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
fi

if [[ -n "$TS_BIN" ]]; then
  log "Bringing up Tailscale (a browser window may open to authenticate)..."
  # --ssh lets you use Tailscale SSH (no key management) if you enable it in the admin console.
  sudo "$TS_BIN" up --ssh || warn "tailscale up did not complete; finish login in the Tailscale app."
  echo
  log "Tailnet status:"
  "$TS_BIN" status || true
  echo
  TS_IP="$("$TS_BIN" ip -4 2>/dev/null | head -n1 || true)"
  [[ -n "$TS_IP" ]] && log "Mac Studio tailnet IP: $TS_IP"
else
  warn "Could not locate the tailscale CLI. Open the Tailscale app and log in manually."
fi

# --- 5. Keep-awake reminder ------------------------------------------------

cat <<'EOF'

------------------------------------------------------------------
Setup complete.

Keep sessions alive while you are away from the Mac Studio:
  * System Settings > Displays > Advanced... or Energy:
      - "Prevent automatic sleeping when the display is off" = ON
  * Or run a long-lived guard: caffeinate -dimsu &

Next steps:
  1. Start a persistent session:   ./scripts/tmux-session.sh main
  2. On the iPhone, set up Blink:  docs/iphone-blink-setup.md
------------------------------------------------------------------
EOF
