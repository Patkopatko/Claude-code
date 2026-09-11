# Connect the Claude **app** to Datamap (not the CLI)

The CLI already works on your machine. The **app** (phone / desktop) reaches a
custom API only through **Connectors**. There are two cases — pick by which app:

| App | Can run the local server? | What you need |
| --- | --- | --- |
| **Claude desktop app** (Mac/Win) | ✅ yes | Edit a config file — no hosting. See A. |
| **Claude mobile app** (iPhone) | ❌ no | A **remote MCP** at a public HTTPS URL. See B. |

---

## A. Desktop Claude app — local server, no hosting

1. Open the Claude desktop app → **Settings** → **Developer** → **Edit Config**
   (this opens `claude_desktop_config.json`).
2. Add this (merge into any existing `mcpServers`):
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
   Replace the path with the real location of `server.py` on your Mac.
3. Save, fully **quit and reopen** the Claude app.
4. In a chat, open the tools/connector menu — you'll see `jarvis-datamap`.
   Ask: *"Load the Datamap OpenAPI spec and list the endpoints."*

---

## B. Mobile Claude app (iPhone) — remote MCP

The phone can't run a local server, so `server_http.py` must run somewhere with a
public HTTPS URL. Host it **on your Jarvis infrastructure** (it's right next to
the API) — that's the natural home.

### B1. Deploy the remote server (on your Jarvis box / infra)

```bash
export JARVIS_API_TOKEN='your-datamap-token'      # talks to Datamap, server-side
export MCP_SHARED_SECRET='make-a-long-random-string'   # protects the endpoint
export PORT=8080
uv run --with "mcp[cli]" --with httpx --with uvicorn python server_http.py
```

Then put it behind HTTPS with your existing reverse proxy, e.g. expose it as:
```
https://prod.jarvis.sk/mcp/datamap      ->  proxies to  http://127.0.0.1:8080/mcp
```

> Security: always set `MCP_SHARED_SECRET` (or keep it behind Jarvis auth).
> Without it, anyone who learns the URL can call your Datamap through it.

### B2. Add it in the iPhone app

1. Claude app → **Settings** → **Connectors** → **Add custom connector**
   (wording may be "Add connector" / "Custom connector").
2. **URL:** `https://prod.jarvis.sk/mcp/datamap`
3. If it asks for auth / a header, give the bearer secret you set:
   `Authorization: Bearer <MCP_SHARED_SECRET>`.
4. Save → enable the connector in a chat → ask:
   *"Load the Datamap OpenAPI spec and list the endpoints."*

---

## Which should you do?

- Want it on the **iPhone app** → **B** (needs the one-time hosting on Jarvis).
- Want it in the **desktop app** → **A** (just a config file, 2 minutes).
- Just using **Claude Code CLI** (what you already have) → nothing to do here;
  use the local `server.py` / the `datamap` skill.

If you tell me where on your Jarvis infra this can run (and how you expose
HTTPS), I'll give you the exact proxy snippet and a ready-to-run service file.
