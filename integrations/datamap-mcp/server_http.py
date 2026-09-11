#!/usr/bin/env python3
"""Jarvis Datamap MCP server — REMOTE (HTTP) variant.

Use this when you want the Claude **app** (phone or desktop) to reach Datamap as
a custom Connector. The Claude mobile app cannot run a local (stdio) MCP server,
so it needs a remote one reachable at a public HTTPS URL — host this on your
Jarvis infrastructure (next to the API) and add its URL as a custom connector.

(For Claude Code CLI and the Claude desktop app you can instead use the local
stdio server in server.py — no hosting required.)

Configuration — environment variables:
  JARVIS_API_TOKEN    (required)  Bearer token for the Datamap API (server-side).
  JARVIS_DATAMAP_URL  (optional)  API base. Default: https://prod.jarvis.sk/api/datamap
  JARVIS_OPENAPI_URL  (optional)  OpenAPI spec URL.
  MCP_SHARED_SECRET   (optional but STRONGLY recommended) If set, every incoming
                                  request must send  Authorization: Bearer <this>.
                                  Without it the endpoint is open to anyone who
                                  knows the URL — only skip it behind a trusted gateway.
  HOST                (optional)  Bind host. Default: 0.0.0.0
  PORT                (optional)  Bind port. Default: 8080

Run:
  uv run --with "mcp[cli]" --with httpx python server_http.py
The MCP endpoint is served at  http://<host>:<port>/mcp

Put this behind HTTPS (your reverse proxy / Jarvis gateway), e.g.
  https://prod.jarvis.sk/mcp/datamap  ->  proxies to this server's /mcp
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

API_BASE = os.environ.get("JARVIS_DATAMAP_URL", "https://prod.jarvis.sk/api/datamap").rstrip("/")
OPENAPI_URL = os.environ.get(
    "JARVIS_OPENAPI_URL", "https://prod.jarvis.sk/developer/datamap/openapi.json"
)
SHARED_SECRET = os.environ.get("MCP_SHARED_SECRET", "")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))

mcp = FastMCP("jarvis-datamap", host=HOST, port=PORT)


def _headers() -> dict[str, str]:
    token = os.environ.get("JARVIS_API_TOKEN", "")
    if not token:
        raise RuntimeError("JARVIS_API_TOKEN is not set on the server.")
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


@mcp.tool()
def get_openapi_spec() -> str:
    """Fetch the current Datamap OpenAPI specification. Call it when starting a new project."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(OPENAPI_URL, headers=_headers())
        resp.raise_for_status()
        return resp.text


@mcp.tool()
def datamap_request(
    method: str,
    path: str,
    query: Optional[dict] = None,
    body: Optional[dict] = None,
) -> str:
    """Make one authenticated request to the Datamap API.

    method: GET/POST/PUT/PATCH/DELETE
    path:   endpoint path relative to the API base, e.g. "/datasets" or "datasets/42"
    query:  optional query params
    body:   optional JSON body
    """
    url = f"{API_BASE}/{path.lstrip('/')}"
    with httpx.Client(timeout=60) as client:
        resp = client.request(method.upper(), url, params=query, json=body, headers=_headers())
        out: dict[str, Any] = {"status": resp.status_code, "url": str(resp.url)}
        try:
            out["json"] = resp.json()
        except Exception:
            out["text"] = resp.text
        return json.dumps(out, ensure_ascii=False, indent=2)


def _build_app():
    """Return the ASGI app, optionally gated by a shared-secret bearer token."""
    app = mcp.streamable_http_app()

    if SHARED_SECRET:
        from starlette.middleware.base import BaseHTTPMiddleware

        class BearerGate(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                auth = request.headers.get("authorization", "")
                if auth != f"Bearer {SHARED_SECRET}":
                    return JSONResponse({"error": "unauthorized"}, status_code=401)
                return await call_next(request)

        app.add_middleware(BearerGate)

    return app


if __name__ == "__main__":
    if SHARED_SECRET:
        import uvicorn

        uvicorn.run(_build_app(), host=HOST, port=PORT)
    else:
        # No gate configured — rely on a trusted gateway in front. Serve directly.
        mcp.run(transport="streamable-http")
