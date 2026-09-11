#!/usr/bin/env python3
"""Jarvis Datamap MCP server.

Gives Claude authenticated access to the Jarvis Datamap API, the same way on
every machine where you install it (desktop, notebook, Claude Code).

Configuration — environment variables only (the token is NEVER hard-coded):
  JARVIS_API_TOKEN    (required)  Bearer token for the Datamap API.
  JARVIS_DATAMAP_URL  (optional)  API base. Default: https://prod.jarvis.sk/api/datamap
  JARVIS_OPENAPI_URL  (optional)  OpenAPI spec URL.
                                  Default: https://prod.jarvis.sk/developer/datamap/openapi.json

Exposed tools:
  get_openapi_spec()                          -> the live OpenAPI spec (call it when starting a project)
  datamap_request(method, path, query, body)  -> one authenticated call to the API
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.environ.get("JARVIS_DATAMAP_URL", "https://prod.jarvis.sk/api/datamap").rstrip("/")
OPENAPI_URL = os.environ.get(
    "JARVIS_OPENAPI_URL", "https://prod.jarvis.sk/developer/datamap/openapi.json"
)

mcp = FastMCP("jarvis-datamap")


def _headers() -> dict[str, str]:
    token = os.environ.get("JARVIS_API_TOKEN", "")
    if not token:
        raise RuntimeError(
            "JARVIS_API_TOKEN is not set. Export your Datamap token before starting the server."
        )
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


@mcp.tool()
def get_openapi_spec() -> str:
    """Fetch the current Datamap OpenAPI specification.

    Call this first whenever you start a new project against Datamap, so you are
    working from the up-to-date endpoint list and schemas.
    """
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

    Args:
        method: HTTP verb — GET, POST, PUT, PATCH or DELETE.
        path:   Endpoint path relative to the API base, e.g. "/datasets" or "datasets/42".
        query:  Optional query-string parameters.
        body:   Optional JSON request body.

    Returns a JSON string with the status code, final URL, and the parsed
    response (under "json", or "text" when the body is not JSON).
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


if __name__ == "__main__":
    mcp.run()
