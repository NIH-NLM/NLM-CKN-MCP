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


@dataclass
class CellKgSearchClient:
    """Simple client for the cell-kn.org Arango search endpoint."""

    base_url: str = "https://cell-kn.org"
    timeout_seconds: float = 20.0

    def _endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}/arango_api/search/"

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

        response = requests.post(
            self._endpoint(),
            json=payload,
            timeout=self.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text[:1000]
            raise RuntimeError(
                f"Cell-KN search request failed with HTTP {response.status_code}: {detail}"
            ) from exc

        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected response format: {type(data).__name__}")

        return data[: max(limit, 0)]
