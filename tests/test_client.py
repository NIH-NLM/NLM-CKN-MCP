from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from cell_kg_mcp.client import CellKgSearchClient, DEFAULT_SEARCH_FIELDS


def test_search_uses_default_fields_for_db() -> None:
    client = CellKgSearchClient(base_url="https://cell-kn.org")

    response = Mock()
    response.status_code = 200
    response.json.return_value = [{"_id": "CL/0000084", "label": "T cell"}]
    response.raise_for_status.return_value = None

    with patch("cell_kg_mcp.client.requests.post", return_value=response) as post:
        result = client.search("T cell", db="phenotypes", limit=5)

    assert result == [{"_id": "CL/0000084", "label": "T cell"}]
    payload = post.call_args.kwargs["json"]
    assert payload["search_term"] == "T cell"
    assert payload["db"] == "phenotypes"
    assert payload["search_fields"] == DEFAULT_SEARCH_FIELDS["phenotypes"]


def test_search_rejects_unknown_db() -> None:
    client = CellKgSearchClient()
    with pytest.raises(ValueError, match="Unsupported db"):
        client.search("x", db="unknown")


def test_search_returns_limited_results() -> None:
    client = CellKgSearchClient()

    response = Mock()
    response.status_code = 200
    response.json.return_value = [
        {"_id": "1", "label": "a"},
        {"_id": "2", "label": "b"},
        {"_id": "3", "label": "c"},
    ]
    response.raise_for_status.return_value = None

    with patch("cell_kg_mcp.client.requests.post", return_value=response):
        result = client.search("x", db="ontologies", limit=2)

    assert len(result) == 2
