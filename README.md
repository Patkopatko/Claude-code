# Mac Studio tmux ← iPhone control

Reach the persistent `tmux` sessions running on your **Mac Studio** and drive
them from your **iPhone**, from anywhere — over a private **Tailscale** tailnet,
using **Blink Shell** on the phone.

```
 iPhone (Blink Shell)  ──── Tailscale (encrypted, no port-forwarding) ────▶  Mac Studio
        mosh / ssh                      100.x.y.z                            tmux: persistent sessions
```

Persistent `tmux` means your shells, builds, and long-running jobs keep running
when you disconnect. Drop off Wi-Fi, switch to cellular, lock the phone — when
you reconnect you land back in the exact same session.

## Why this setup

- **Tailscale** — a private mesh VPN. No router config, no exposing SSH to the
  public internet, works on cellular. The Mac Studio and iPhone just see each
  other as if on the same LAN.
- **Blink Shell** — the best iOS terminal: hardware-keyboard friendly, supports
  `mosh` (roaming connections that survive IP changes and latency), and plays
  well with tmux.
- **tmux** — keeps sessions alive across disconnects so the phone is a true
  remote control, not a fragile live link.

## Quick start

### On the Mac Studio

```bash
git clone <this-repo> ~/Claude-code
cd ~/Claude-code
./scripts/setup-mac-studio.sh        # installs tmux/mosh, enables SSH, brings up Tailscale
./scripts/tmux-session.sh main       # start (or attach to) a persistent session named "main"
```

The setup script prints the Mac's tailnet name/IP at the end — you'll need it
on the phone.

### On the iPhone

Follow **[docs/iphone-blink-setup.md](docs/iphone-blink-setup.md)**:

1. Install **Tailscale**, sign in with the same account → both devices connected.
2. Install **Blink Shell**, create an SSH key, add it to the Mac, add the host.
3. Connect straight into your session:

   ```
   mosh mac-studio -- ~/Claude-code/scripts/tmux-session.sh main
   ```

   This creates the session the first time and re-attaches every time after.

## What's in here

| Path                          | Purpose                                                      |
| ----------------------------- | ------------------------------------------------------------ |
| `scripts/setup-mac-studio.sh` | One-shot, idempotent Mac setup: tmux, mosh, SSH, Tailscale.  |
| `scripts/tmux-session.sh`     | Create-or-attach a named persistent session (the phone runs this). |
| `config/tmux.conf`            | tmux config tuned for a touch keyboard + small screen.       |
| `docs/iphone-blink-setup.md`  | Step-by-step Blink Shell + Tailscale setup on the iPhone.    |

## Everyday commands

| Action                        | Command                                                          |
| ----------------------------- | --------------------------------------------------------------- |
| Connect + attach (cellular)   | `mosh mac-studio -- ~/Claude-code/scripts/tmux-session.sh main` |
| Connect + attach (SSH)        | `ssh -t mac-studio '~/Claude-code/scripts/tmux-session.sh main'`|
| List sessions                 | `./scripts/tmux-session.sh -l`                                  |
| New named session             | `./scripts/tmux-session.sh work`                               |
| Kill a session                | `./scripts/tmux-session.sh -k work`                           |
| Detach (inside tmux)          | `Ctrl-a d`                                                      |

## Keeping sessions alive

Persistent tmux only helps if the Mac stays awake. In **System Settings →
Displays → Advanced** (or Energy), enable *"Prevent automatic sleeping when the
display is off,"* or run `caffeinate -dimsu &`.

## Security notes

- Traffic is end-to-end encrypted by Tailscale (WireGuard); nothing is exposed
  to the public internet.
- Prefer key-based SSH (or Tailscale SSH) — the setup script enables Remote
  Login but you authorize devices explicitly.
- Lock down further with Tailscale ACLs in the admin console so only your phone
  can reach the Mac's SSH port.
