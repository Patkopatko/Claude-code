# Reach your existing tmux / Claude Code sessions from the iPhone

For infrastructure you **already run** — machines that are up and full of your
work, with **Tailscale on every machine and on the iPhone**. This repo wires
your phone into the sessions already running on those boxes. It installs no
fresh server and assumes nothing is empty.

```
 iPhone (Blink Shell)  ──── your Tailscale tailnet ────▶  your infra box
        ssh / mosh                100.x.y.z                tmux attach -t main   (or: claude)
```

## The one thing to know first

There are two different things both called "Claude Code sessions":

1. **Claude Code on the web / iPhone app** → runs in an *isolated Anthropic
   cloud container*. It is **not** on your tailnet and **cannot** reach your
   infrastructure. (That container is why a session can look "empty.")
2. **tmux / Claude Code running on your own infra box** → the machine that's
   full of your work. **This** is what you reach.

So you reach your sessions **directly: iPhone → your tailnet → your box.** Not
through the cloud app. The steps below set up exactly that direct path.

## Quick start

### On the infra box (verify, don't install)

```bash
git clone <this-repo> ~/Claude-code      # optional — only for the helper scripts
cd ~/Claude-code
./scripts/check-host.sh                   # confirms Tailscale up, SSH on, tmux present; prints your connect command
./scripts/check-host.sh --link            # (optional) use the phone-friendly tmux.conf
```

`check-host.sh` changes nothing on your system (except the optional config
symlink). It just confirms the box is reachable and prints the exact command to
paste into Blink.

### On the iPhone

Follow **[docs/iphone-blink-setup.md](docs/iphone-blink-setup.md)**. The short
version, once Tailscale shows both ends Connected:

```
ssh studio -t '~/Claude-code/scripts/tmux-session.sh main'
# or without the repo on the box:
ssh studio -t 'tmux attach -t main || tmux new -s main'
```

This attaches to your running `main` session — or creates it the first time.
Drop signal, switch Wi-Fi↔cellular, lock the phone: the same session is waiting
when you reconnect.

## What's in here

| Path                         | Purpose                                                          |
| ---------------------------- | --------------------------------------------------------------- |
| `scripts/check-host.sh`      | Verify an existing box is reachable; print the iPhone command. No installs. |
| `scripts/tmux-session.sh`    | Create-or-attach a named persistent session (the command the phone runs). |
| `config/tmux.conf`           | tmux tuned for a touch keyboard + small screen (optional).      |
| `docs/iphone-blink-setup.md` | Step-by-step Blink Shell + Tailscale connection on the iPhone.  |

## Authentication

You already have Tailscale everywhere, so use it as the auth layer — two options:

- **Tailscale SSH** — `sudo tailscale up --ssh` on the box + allow SSH in the
  admin-console ACLs. Your tailnet identity *is* the login; no keys to manage.
- **SSH key** — make a key in Blink, append its public half to
  `~/.ssh/authorized_keys` on the box. Classic and works the same.

## Everyday commands

| Action                       | Command                                                         |
| ---------------------------- | -------------------------------------------------------------- |
| Connect + attach (SSH)       | `ssh studio -t '~/Claude-code/scripts/tmux-session.sh main'`   |
| Connect + attach (no repo)   | `ssh studio -t 'tmux attach -t main \|\| tmux new -s main'`     |
| Connect + attach (cellular)  | `mosh studio -- ~/Claude-code/scripts/tmux-session.sh main`    |
| Land in Claude Code          | `ssh studio -t 'tmux attach -t claude \|\| tmux new -s claude claude'` |
| List sessions                | `ssh studio 'tmux ls'`                                          |
| Detach (inside tmux)         | `Ctrl-a d`                                                      |
