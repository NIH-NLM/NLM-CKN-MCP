"""
run_aql — read-only AQL cursor passthrough for the NLM-CKN FastMCP server.

Drop this into the same server module that already exposes search_cell_kn /
get_cell_kn_neighbors (the one you run via `uv`). It wraps ArangoDB's
/_api/cursor endpoint so aggregation queries (COLLECT, LENGTH, counts) that the
search + traversal tools can't express become available directly.

Config: reuse whatever the existing connector already uses to reach
https://stage.nlm-ckn.org/arango_api/ . Point ARANGO_BASE at the host/prefix
that fronts /_db/<db>/_api/* and set the db name + auth. If your existing
client object already holds base_url + creds, just borrow it and delete the
env plumbing below.
"""

import os
import httpx

# from your_server_module import mcp   # <-- your existing FastMCP() instance

ARANGO_BASE = os.environ.get("NLM_CKN_ARANGO_BASE", "https://stage.nlm-ckn.org/arango_api")
ARANGO_DB   = os.environ.get("NLM_CKN_DB", "_system")
ARANGO_USER = os.environ.get("NLM_CKN_USER")
ARANGO_PASS = os.environ.get("NLM_CKN_PASS")
ARANGO_TOKEN = os.environ.get("NLM_CKN_TOKEN")  # bearer, if you use JWT instead of basic auth

_WRITE_OPS = ("INSERT ", "UPDATE ", "REPLACE ", "REMOVE ", "UPSERT ")


def _auth_kwargs() -> dict:
    if ARANGO_TOKEN:
        return {"headers": {"Authorization": f"Bearer {ARANGO_TOKEN}"}}
    if ARANGO_USER:
        return {"auth": (ARANGO_USER, ARANGO_PASS or "")}
    return {}


@mcp.tool()  # noqa: F821  (mcp = your existing FastMCP instance)
def run_aql(query: str, bind_vars: dict | None = None, full_count: bool = False) -> dict:
    """Execute a READ-ONLY AQL query against the loaded NLM-CKN graph and return all rows.

    Streams the ArangoDB cursor to completion (follows hasMore batching), so a
    COLLECT/aggregation over the whole graph comes back in one call. Write
    operations are blocked.

    Args:
        query:      AQL string. Use bind vars for anything dynamic.
        bind_vars:  dict of bind parameters, e.g. {"graph": "cell-kn"}.
        full_count: if True, also returns the pre-LIMIT row count.
    """
    upper = query.upper()
    if any(op in upper for op in _WRITE_OPS):
        raise ValueError("run_aql is read-only; INSERT/UPDATE/REPLACE/REMOVE/UPSERT are blocked.")

    url = f"{ARANGO_BASE}/_db/{ARANGO_DB}/_api/cursor"
    payload = {
        "query": query,
        "bindVars": bind_vars or {},
        "batchSize": 1000,
        "options": {"fullCount": full_count},
    }
    kw = _auth_kwargs()

    with httpx.Client(timeout=180.0) as client:
        r = client.post(url, json=payload, **kw)
        r.raise_for_status()
        body = r.json()
        rows = list(body.get("result", []))
        cursor_id = body.get("id")
        while body.get("hasMore"):
            r = client.put(f"{url}/{cursor_id}", **kw)
            r.raise_for_status()
            body = r.json()
            rows.extend(body.get("result", []))

    out = {"count": len(rows), "result": rows}
    if full_count:
        out["full_count"] = body.get("extra", {}).get("stats", {}).get("fullCount")
    return out
