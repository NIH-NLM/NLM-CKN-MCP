from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from cell_kg_mcp.client import (
    CellKgSearchClient,
    DEFAULT_SEARCH_FIELDS,
    GRAPH_COLLECTIONS,
)


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

def _mock_response(json_value):
    response = Mock()
    response.status_code = 200
    response.json.return_value = json_value
    response.raise_for_status.return_value = None
    return response


def test_collections_returns_list() -> None:
    client = CellKgSearchClient()
    response = _mock_response(["CL", "GO", "UBERON"])

    with patch("cell_kg_mcp.client.requests.post", return_value=response) as post:
        result = client.collections()

    assert result == ["CL", "GO", "UBERON"]
    assert post.call_args.args[0].endswith("/arango_api/collections/")
    assert post.call_args.kwargs["json"] == {}


def test_graph_builds_payload_with_defaults() -> None:
    client = CellKgSearchClient()
    response = _mock_response({"CL/0000084": {"nodes": [], "links": []}})

    with patch("cell_kg_mcp.client.requests.post", return_value=response) as post:
        client.graph("CL/0000084", depth=2, edge_direction="OUTBOUND")

    payload = post.call_args.kwargs["json"]
    assert payload["node_ids"] == ["CL/0000084"]  # single str is coerced
    assert payload["depth"] == 2
    assert payload["edge_direction"] == "OUTBOUND"
    assert payload["allowed_collections"] == GRAPH_COLLECTIONS


def test_graph_rejects_bad_edge_direction() -> None:
    client = CellKgSearchClient()
    with pytest.raises(ValueError, match="edge_direction"):
        client.graph(["CL/0000084"], edge_direction="any")


def test_graph_rejects_depth_below_one() -> None:
    client = CellKgSearchClient()
    with pytest.raises(ValueError, match="depth"):
        client.graph(["CL/0000084"], depth=0)


def test_get_node_returns_matching_node() -> None:
    client = CellKgSearchClient()
    response = _mock_response(
        {
            "CL/0000084": {
                "nodes": [
                    {"_id": "CL/0000542", "label": "lymphocyte"},
                    {"_id": "CL/0000084", "label": "T cell"},
                ],
                "links": [],
            }
        }
    )

    with patch("cell_kg_mcp.client.requests.post", return_value=response):
        node = client.get_node("CL/0000084")

    assert node == {"_id": "CL/0000084", "label": "T cell"}


def test_get_node_returns_none_when_absent() -> None:
    client = CellKgSearchClient()
    response = _mock_response({"CL/0000084": {"nodes": [], "links": []}})

    with patch("cell_kg_mcp.client.requests.post", return_value=response):
        assert client.get_node("CL/0000084") is None

