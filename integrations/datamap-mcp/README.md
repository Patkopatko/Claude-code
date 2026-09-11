# Jarvis Datamap — MCP server

Gives Claude authenticated access to your **Jarvis Datamap API**, set up once
and working the same way everywhere you install it (desktop, notebook, Claude
Code). The token lives only in an environment variable — it is never written
into any file in this repo.

- **API base:** `https://prod.jarvis.sk/api/datamap`
- **OpenAPI spec:** `https://prod.jarvis.sk/developer/datamap/openapi.json`
- **Auth:** `Authorization: Bearer <token>` on every request

## Tools it exposes to Claude

| Tool | What it does |
| --- | --- |
| `get_openapi_spec()` | Fetches the live OpenAPI spec — call it when starting a new project. |
| `datamap_request(method, path, query?, body?)` | One authenticated call to any Datamap endpoint. |

## 1. Set your token (once per machine)

```bash
export JARVIS_API_TOKEN='your-datamap-token'
```

Put that line in your shell profile (`~/.zshrc` / `~/.bashrc`) so it persists.
Or copy `.env.example` to `.env` and fill it in (the `.env` is gitignored).

> Security: if a token was ever pasted into a chat or shared, rotate it in
> Jarvis and keep the new one only as this env var.

## 2. Install per surface

### Claude Code (CLI / web / this repo)

This repo already ships `.mcp.json`, so inside the repo just run Claude Code and
approve the `jarvis-datamap` server when prompted. To register it globally
(any directory), run:

```bash
claude mcp add jarvis-datamap --scope user \
  -e JARVIS_API_TOKEN=$JARVIS_API_TOKEN \
  -- uv run --with mcp --with httpx python /ABSOLUTE/PATH/TO/integrations/datamap-mcp/server.py
```

### Claude Desktop (Mac / Windows)

Edit the MCP config (Settings → Developer → Edit Config, i.e.
`claude_desktop_config.json`) and add:

```json
{
  "mcpServers": {
    "jarvis-datamap": {
      "command": "uv",
      "args": ["run", "--with", "mcp", "--with", "httpx", "python",
               "/ABSOLUTE/PATH/TO/integrations/datamap-mcp/server.py"],
      "env": { "JARVIS_API_TOKEN": "your-datamap-token" }
    }
  }
}
```

Restart Claude Desktop. You'll see `jarvis-datamap` in the tools list.

### No `uv`? Use a plain virtualenv

```bash
cd integrations/datamap-mcp
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python server.py          # test it starts; Ctrl-C to stop
```

Then point the `command`/`args` at `.venv/bin/python server.py`.

### Phone (Claude mobile app)

The mobile app does **not** run local (stdio) MCP servers. Two honest options:

1. Use a **web Claude Code session** from the phone with this repo — the
   bundled `datamap` skill (see `.claude/skills/datamap/`) tells Claude how to
   call the API with `curl`. Works anywhere the session has network + the token.
2. For native mobile tool access, host this as a **remote (HTTP) MCP** on your
   Jarvis infra and add it as a remote connector. Ask and I'll build that
   variant.

## 3. Try it

Ask Claude: *"Load the Datamap OpenAPI spec and list the available endpoints."*
It should call `get_openapi_spec`, then you can drive real calls via
`datamap_request`.

## Notes

- This server was authored in a cloud sandbox that cannot reach
  `prod.jarvis.sk` (network policy returns 403), so it is written to work
  against the **live** API at install time on your own machines — not tested
  from here. The first `get_openapi_spec` call on your device is the real test.
