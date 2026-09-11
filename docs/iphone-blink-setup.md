# Reaching your existing sessions from the iPhone

This assumes what you already have: infrastructure machines that are **up and
full of your work**, with **Tailscale installed on every machine and on the
iPhone**. Nothing here installs a fresh box or wipes anything — it just wires
the iPhone into the sessions that are already running.

```
 iPhone (Blink Shell)  ──── your Tailscale tailnet ────▶  your infra box
        ssh / mosh                100.x.y.z                tmux attach -t main   (or: claude)
```

> Important: this path is **iPhone → your box, directly over your tailnet.**
> It does NOT go through the Claude Code web/app cloud sessions — those run in
> an isolated Anthropic cloud container that is *not* on your tailnet and can't
> reach your infra.

---

## 1. Confirm both ends are on the tailnet

You said Tailscale is already on every machine and the phone. Just confirm:

- On the **iPhone**: open Tailscale → it's Connected, and your infra box is
  listed.
- On the **infra box**: `tailscale status` shows the box with a `100.x.y.z` IP
  and a name (e.g. `studio.tailnet-name.ts.net`).

`scripts/check-host.sh` prints both for you.

## 2. One-time: let Blink authenticate

You have two equally good options — pick one.

**Option A — Tailscale SSH (no keys to manage).**
If you enabled Tailscale SSH (run `sudo tailscale up --ssh` on the box and allow
SSH for your user in the Tailscale admin console ACLs), then your tailnet
identity *is* the auth. Blink just connects; Tailscale authorizes it. Nothing to
copy.

**Option B — an SSH key (classic).**
In Blink: `config` → **Keys** → **New** (ED25519), name it `phone`, copy the
**public** key, and append it to `~/.ssh/authorized_keys` on the infra box.

## 3. Add the host in Blink

In Blink: `config` → **Hosts** → **New**:

| Field    | Value                                               |
| -------- | --------------------------------------------------- |
| Host     | `studio` (a short alias you'll type)                |
| HostName | the box's tailnet name *or* its `100.x.y.z` IP      |
| User     | your username on the box                            |
| Key      | `phone` (only if you chose Option B)                |

## 4. Connect straight into your session

```
ssh studio -t '~/Claude-code/scripts/tmux-session.sh main'
```

…or, if you didn't clone this repo on the box, the plain equivalent:

```
ssh studio -t 'tmux attach -t main || tmux new -s main'
```

Want to land directly in a Claude Code session instead of a shell? Point it at
whatever you run:

```
ssh studio -t 'tmux attach -t claude || tmux new -s claude claude'
```

**On flaky cellular, use mosh** (survives IP changes and lag) — same idea:

```
mosh studio -- ~/Claude-code/scripts/tmux-session.sh main
```

Detach any time with `Ctrl-a d` (this config) or `Ctrl-b d` (default) — the
session and everything in it keeps running on your box.

## 5. Driving tmux from a touch keyboard

If you link the bundled `config/tmux.conf` (`./scripts/check-host.sh --link`):

- Prefix is **`Ctrl-a`** (easier on iOS keyboards than `Ctrl-b`)
- Mouse/touch on: tap panes, drag borders, scroll to scroll back
- `Ctrl-a |` / `Ctrl-a -` split · `Ctrl-a h/j/k/l` move · `Ctrl-a d` detach

---

### Quick reference

| Action                       | Command                                                         |
| ---------------------------- | -------------------------------------------------------------- |
| Connect + attach (SSH)       | `ssh studio -t '~/Claude-code/scripts/tmux-session.sh main'`   |
| Connect + attach (no repo)   | `ssh studio -t 'tmux attach -t main \|\| tmux new -s main'`     |
| Connect + attach (cellular)  | `mosh studio -- ~/Claude-code/scripts/tmux-session.sh main`    |
| List sessions on the box     | `ssh studio 'tmux ls'`                                          |
| Detach (inside tmux)         | `Ctrl-a d`                                                      |
