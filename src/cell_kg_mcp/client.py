from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

DEFAULT_SEARCH_FIELDS = {
    "phenotypes": [
        "label",
        "markers",
        "author_cell_term",
        "cell_type",
        "definition",
        "hasExactSynonym",
        "exact_synonym",
        "_id",
    ],
    "ontologies": [
        "label",
        "definition",
        "hasExactSynonym",
        "exact_synonym",
        "comment",
        "_id",
    ],
}
# All graph collections / ontology prefixes returned by /arango_api/collections/.
# Used as the default `allowed_collections` for graph traversal.

GRAPH_COLLECTIONS = [
    "GS", "PR", "UBERON", "MONDO", "CL", "BMC", "GO", "PATO",
    "HsapDv", "CS", "CHEBI", "CHEMBL", "HP", "PUB", "NCBITaxon",
    "BGS", "CSD", "NCT",
]

EDGE_DIRECTIONS = ("ANY", "OUTBOUND", "INBOUND")


@dataclass
class CellKgSearchClient:
    """Simple client for the cell-kn.org Arango search endpoint."""

    base_url: str = "https://cell-kn.org"
    timeout_seconds: float = 20.0

    def _endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}/arango_api/search/"

    def _post(self, path: str, payload: dict) -> Any:
        url = f"{self.base_url.rstrip('/')}{path}"
        response = requests.post(
            url,
            json=payload,
            timeout=self.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text[:1000]
            raise RuntimeError(
                f"NLM-CKN request to {path} failed with HTTP {response.status_code}: {detail}"
            ) from exc
        return response.json()

    def search(
            self,
            query: str,
            db: str = "phenotypes",
            search_fields: list[str] | None = None,
            limit: int = 10,
        ) -> list[dict[str, Any]]:
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("query must not be empty")

        if db not in DEFAULT_SEARCH_FIELDS:
            supported = ", ".join(sorted(DEFAULT_SEARCH_FIELDS.keys()))
            raise ValueError(f"Unsupported db '{db}'. Supported values: {supported}")

        fields = search_fields or DEFAULT_SEARCH_FIELDS[db]
        if not fields:
            raise ValueError("search_fields must contain at least one field")

        payload = {
            "search_term": cleaned_query,
            "db": db,
            "search_fields": fields,
        }

        data = self._post("/arango_api/search/", payload)

        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected response format: {type(data).__name__}")

        return data[: max(limit, 0)]

    def collections(self) -> list[str]:
        data = self._post("/arango_api/collections/", {})
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected collections response: {type(data).__name__}")
        return data

    def graph(
        self,
        node_ids,                              # str or list[str]
        depth: int = 1,
        edge_direction: str = "ANY",
        allowed_collections: list[str] | None = None,
    ) -> dict:
        if isinstance(node_ids, str):
            node_ids = [node_ids]
        if not node_ids:
            raise ValueError("node_ids must contain at least one id")
        if edge_direction not in EDGE_DIRECTIONS:
            raise ValueError(
                f"edge_direction must be one of {EDGE_DIRECTIONS}; got {edge_direction!r}"
            )
        if depth < 1:
            raise ValueError(f"depth must be >= 1; got {depth}")

        payload = {
            "node_ids": list(node_ids),
            "depth": depth,
            "edge_direction": edge_direction,
            "allowed_collections": allowed_collections or GRAPH_COLLECTIONS,
        }
        data = self._post("/arango_api/graph/", payload)
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected graph response: {type(data).__name__}")
        return data

    def get_node(self, node_id: str) -> dict | None:
        result = self.graph([node_id], depth=1, edge_direction="ANY")
        nodes = result.get(node_id, {}).get("nodes", [])
        for n in nodes:
            if n.get("_id") == node_id:
                return n
        return None

