---
name: datamap
description: >-
  Call the Jarvis Datamap API (https://prod.jarvis.sk/api/datamap). Use whenever
  the user wants to read, query, or write data in their Jarvis Datamap platform,
  or mentions "datamap", "jarvis data", or working with their datasets. Works in
  any session that has network access and the JARVIS_API_TOKEN environment
  variable set — the lightweight alternative to the datamap MCP server.
---

# Jarvis Datamap API

You have access to the user's Jarvis Datamap platform over HTTP.

## Configuration

- **API base:** `https://prod.jarvis.sk/api/datamap`
- **OpenAPI spec:** `https://prod.jarvis.sk/developer/datamap/openapi.json`
- **Auth:** every request needs the header `Authorization: Bearer $JARVIS_API_TOKEN`

The token is in the environment variable `JARVIS_API_TOKEN`. **Never** print it,
hard-code it, or commit it. Always reference it as `$JARVIS_API_TOKEN`.

If `JARVIS_API_TOKEN` is unset, ask the user to export it first:
```bash
export JARVIS_API_TOKEN='...'
```

## Step 1 — always load the spec first for a new project

```bash
curl -fsS -H "Authorization: Bearer $JARVIS_API_TOKEN" \
  https://prod.jarvis.sk/developer/datamap/openapi.json
```

Read the returned OpenAPI document to discover the current endpoints, methods,
parameters, and schemas. Do this at the start of any new Datamap task — the API
can change.

## Step 2 — make authenticated calls

```bash
# GET example
curl -fsS -H "Authorization: Bearer $JARVIS_API_TOKEN" \
  "https://prod.jarvis.sk/api/datamap/<endpoint>"

# POST example
curl -fsS -X POST \
  -H "Authorization: Bearer $JARVIS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}' \
  "https://prod.jarvis.sk/api/datamap/<endpoint>"
```

## Notes

- If a call returns `401/403`, the token is missing, wrong, or lacks scope — tell
  the user rather than guessing.
- If the host is unreachable (e.g. a restricted sandbox blocks it with a proxy
  `403`/`CONNECT tunnel failed`), say so: this session's network can't reach
  `prod.jarvis.sk`. It will work from a machine/environment with open network.
- For persistent, tool-native access (no curl), install the MCP server in
  `integrations/datamap-mcp/`.
