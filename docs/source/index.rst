
A small **MCP (Model Context Protocol) server** that gives Claude a safe,
curated set of tools for searching and exploring the **NLM Cell Knowledge
Network (NLM-CKN)** — the cell-type knowledge graph behind
`nlm-ckn.org <https://nlm-ckn.org>`_.

You ask a question in plain English and Claude uses these tools to search the
knowledge graph and walk its connections for you. No query language, no schema
knowledge required.

* **Use it in your browser:** add the connector
  ``https://nlm-ckn-mcp.onrender.com/mcp`` in *claude.ai → Settings →
  Connectors → Add custom connector*.
* **Source:** `github.com/NIH-NLM/NLM-CKN-MCP
  <https://github.com/NIH-NLM/NLM-CKN-MCP>`_


Why go through this server
--------------------------

The knowledge graph lives in a database that could, in principle, be queried
directly — but that is not the path we want users on:

* **Safety.** This server exposes only a small, **read-only**, purpose-built set
  of tools. There is no way through it to run arbitrary or destructive queries.
* **No expertise required.** Users don't learn the query language or the schema;
  they ask in English and Claude picks the right tool.
* **Stability.** The database layer is still being hardened. Because users go
  through these fixed tools, that work happens without changing anything for
  users.

The MCP server is the supported, safe, stable front door.


The tools
---------

All five tools are read-only.

``search_cell_kn``
    Search Cell-KN (``phenotypes`` or ``ontologies``) and return compact
    results. This is the usual starting point — it returns node ``_id`` values
    (e.g. ``CL/0000084``) that the graph tools then build on.

``get_cell_kn_search_defaults``
    Report the default search fields used for each database.

``list_cell_kn_collections``
    List the graph collections / ontology prefixes present in the graph
    (``CL``, ``GO``, ``UBERON``, ``MONDO``, …). Useful for scoping a traversal.

``get_cell_kn_neighbors``
    Traverse the graph outward from one or more node ``_id`` values to the nodes
    and links related to them, at a chosen depth and edge direction.

``get_cell_kn_node``
    Fetch a single node's full record by ``_id``.

A typical flow: **search** for a term to get an ``_id``, then ask for its
**neighbors** to see what it connects to.


Installation (developers)
-------------------------
nlm-ckn-mcp Documentation

Python MCP server that exposes search and graph-traversal tools for the
NLM Cell Knowledge Network.

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules

Installation
------------

.. code-block:: bash

   pip install -e .


Indices and tables

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
