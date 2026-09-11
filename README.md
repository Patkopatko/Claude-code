# Give Claude access to your Jarvis Datamap — everywhere

The goal: wherever you install Claude (desktop, notebook, Claude Code), it can
reach your **Jarvis Datamap API** the same way. This repo carries that
integration, set up once and reused everywhere.

- **API base:** `https://prod.jarvis.sk/api/datamap`
- **OpenAPI spec:** `https://prod.jarvis.sk/developer/datamap/openapi.json`
- **Auth:** `Authorization: Bearer <token>` — the token lives **only** in the
  `JARVIS_API_TOKEN` environment variable, never in any committed file.

## Two ways in (use both — they complement each other)

| Path | Where it runs | Best for |
| --- | --- | --- |
| **MCP server** (`integrations/datamap-mcp/`) | Desktop, notebook, Claude Code | Native tool access: `get_openapi_spec`, `datamap_request`. |
| **`datamap` skill** (`.claude/skills/datamap/`) | Any session with network + token | Lightweight `curl`-based access, incl. web sessions from the phone. |

## Quick start

```bash
# 1. Set your token once (put it in ~/.zshrc to persist)
export JARVIS_API_TOKEN='your-datamap-token'

# 2a. Claude Code: just open this repo — .mcp.json registers the server; approve it.
# 2b. Other installs: see integrations/datamap-mcp/README.md (Desktop, global CLI, venv, phone)
```

Then ask Claude: *"Load the Datamap OpenAPI spec and list the endpoints."*

## 🔐 Token safety

- The token is referenced only as `$JARVIS_API_TOKEN`. It is **never** written to
  a file here; `.env` is gitignored and only `.env.example` (a placeholder) is
  committed.
- If the token was ever pasted into a chat or shared, **rotate it in Jarvis** and
  keep the new one only as the env var.

## Layout

| Path | Purpose |
| --- | --- |
| `integrations/datamap-mcp/server.py` | The MCP server (Python, FastMCP). |
| `integrations/datamap-mcp/README.md` | Per-surface install: Claude Code, Desktop, venv, phone. |
| `integrations/datamap-mcp/.env.example` | Template for your local `.env`. |
| `.mcp.json` | Registers the server for Claude Code in this repo. |
| `.claude/skills/datamap/SKILL.md` | The lightweight `curl`-based access skill. |

---

### Also in this repo: reach your Mac sessions from the iPhone

Earlier setup for attaching to tmux / Claude Code sessions on your own
infrastructure from the iPhone over Tailscale lives in
**[docs/iphone-blink-setup.md](docs/iphone-blink-setup.md)** and `scripts/`.
Separate from Datamap — keep it or say the word and I'll remove it.
