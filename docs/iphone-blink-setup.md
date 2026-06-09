# Controlling your Mac Studio tmux sessions from the iPhone

This is the iPhone-side companion to `scripts/setup-mac-studio.sh`. By the end
you'll be able to open Blink Shell on your phone, run one short command, and
land directly inside a persistent `tmux` session on the Mac Studio — over
Tailscale, from anywhere (Wi-Fi or cellular).

```
 iPhone (Blink Shell)  ──── Tailscale tailnet ────▶  Mac Studio
        mosh/ssh                (100.x.x.x)            tmux attach -t main
```

---

## 1. Install Tailscale on the iPhone

1. App Store → install **Tailscale**.
2. Sign in with the **same account** you used on the Mac Studio.
3. Confirm both devices are listed and "Connected" in the Tailscale app.

Now your phone can reach the Mac Studio by its tailnet name (e.g.
`mac-studio`) or its `100.x.y.z` IP — no port forwarding, no public exposure.

> Find the Mac's tailnet name/IP: it's printed at the end of
> `setup-mac-studio.sh`, or run `tailscale status` on the Mac.

## 2. Install Blink Shell on the iPhone

App Store → install **Blink Shell**. Open it; you get a terminal prompt.

### Generate a key and authorize it on the Mac

In Blink:

```
config            # opens settings → Keys → New (ED25519). Name it: phone
```

Copy the **public** key (Keys → tap the key → Copy Public Key), then add it to
the Mac Studio. The quickest path, from a terminal already logged into the Mac:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
pbpaste >> ~/.ssh/authorized_keys     # if you copied the pubkey to the Mac's clipboard
chmod 600 ~/.ssh/authorized_keys
```

…or just paste the public key line into `~/.ssh/authorized_keys` by hand.

> If you ran `tailscale up --ssh` on the Mac and enabled **Tailscale SSH** in
> the admin console, you can skip key management entirely — Tailscale handles
> auth. Plain SSH keys (above) work too and are a good fallback.

### Add the host in Blink

In Blink, type `config` → **Hosts** → **New**:

| Field      | Value                                  |
| ---------- | -------------------------------------- |
| Host       | `mac-studio`  (an alias you'll type)   |
| HostName   | `mac-studio` *or* the `100.x.y.z` IP   |
| User       | your macOS username                    |
| Key        | `phone` (the key you just made)        |
| MOSH Server| `mosh-server` (leave default)          |

## 3. Connect into a persistent session

The magic is having SSH/mosh drop you **straight into tmux** so you never see a
bare login shell and your work is always waiting where you left it.

**Best for cellular — use mosh** (survives IP changes, lag, and sleep):

```
mosh mac-studio -- ~/Claude-code/scripts/tmux-session.sh main
```

**Plain SSH alternative:**

```
ssh -t mac-studio '~/Claude-code/scripts/tmux-session.sh main'
```

Either command **creates** the `main` session the first time and **re-attaches**
to it every time after. Close the app, lose signal, switch from Wi-Fi to LTE —
when you reconnect, the same shell (and anything running in it) is still there.

### Make it one tap

In Blink, save the connection as a host whose **startup command** runs the
tmux helper, or add a shell alias on the Mac so the command is tiny:

```bash
# on the Mac, in ~/.zshrc
alias t='~/Claude-code/scripts/tmux-session.sh'
```

then from Blink: `mosh mac-studio -- t main`.

## 4. Driving tmux from a touch keyboard

The bundled `config/tmux.conf` is tuned for this. Highlights:

- **Prefix is `Ctrl-a`** (easier than `Ctrl-b` on iOS keyboards). Blink maps a
  hardware/soft Ctrl; you can also set a Caps-Lock→Ctrl mapping in Blink config.
- **Mouse/touch on**: tap to switch panes, drag borders to resize, scroll to
  scroll back.
- `Ctrl-a |`  split vertical · `Ctrl-a -` split horizontal
- `Ctrl-a h/j/k/l` move between panes (vim style)
- `Ctrl-a d`  detach (your session keeps running)
- `Ctrl-a r`  reload tmux config

## 5. Keep sessions alive on the Mac Studio

Persistent tmux only helps if the Mac stays awake:

- **System Settings → Displays → Advanced** (or Energy): enable
  *"Prevent automatic sleeping when the display is off."*
- Or run a guard: `caffeinate -dimsu &`

---

### Quick reference

| Action                        | Command                                              |
| ----------------------------- | ---------------------------------------------------- |
| Connect + attach (cellular)   | `mosh mac-studio -- ~/Claude-code/scripts/tmux-session.sh main` |
| Connect + attach (SSH)        | `ssh -t mac-studio '~/Claude-code/scripts/tmux-session.sh main'` |
| List sessions                 | `~/Claude-code/scripts/tmux-session.sh -l`           |
| New named session             | `~/Claude-code/scripts/tmux-session.sh work`         |
| Kill a session                | `~/Claude-code/scripts/tmux-session.sh -k work`      |
| Detach (inside tmux)          | `Ctrl-a d`                                           |
