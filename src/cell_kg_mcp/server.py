from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .client import DEFAULT_SEARCH_FIELDS, CellKgSearchClient

mcp = FastMCP("cell-kg-search")
client = CellKgSearchClient()


def _compact_result(item: dict[str, Any]) -> dict[str, Any]:
    # Keep the highest-value fields compact for LLM context size.
    keys = [
        "_id",
        "_key",
        "label",
        "author_cell_term",
        "markers",
        "definition",
        "hasExactSynonym",
        "exact_synonym",
    ]
    compact = {k: item[k] for k in keys if k in item}
    if not compact:
        compact = item
    return compact


@mcp.tool()
def search_cell_kn(
    query: str,
    db: Literal["phenotypes", "ontologies"] = "phenotypes",
    limit: int = 10,
    search_fields: list[str] | None = None,
    include_raw: bool = False,
) -> dict[str, Any]:
    """Search the NLM Cell Knowledge Network via https://cell-kn.org/arango_api/search/."""
    results = client.search(
        query=query,
        db=db,
        search_fields=search_fields,
        limit=limit,
    )

    compact_results = [_compact_result(item) for item in results]
    payload: dict[str, Any] = {
        "query": query,
        "db": db,
        "count": len(results),
        "results": compact_results,
        "default_search_fields": DEFAULT_SEARCH_FIELDS[db],
    }
    if include_raw:
        payload["raw_results"] = results
    return payload


@mcp.tool()
def get_cell_kn_search_defaults() -> dict[str, list[str]]:
    """Return supported graph databases and the default search fields."""
    return DEFAULT_SEARCH_FIELDS


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
