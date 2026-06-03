# NLM-CKN

Python MCP server that exposes search tools for the public NLM Cell Knowledge Network site:

- Website: <https://cell-kn.org/>
- Search endpoint used by the web app: `POST /arango_api/search/`

## What this server provides

- `search_cell_kn`: Search Cell-KN (`phenotypes` or `ontologies`) and return compact results.
- `get_cell_kn_search_defaults`: Return the default search fields used by this server.

## Quick start


```bash
git clone https://github.com/NIH-NLM/NLM-CKN-MCP.git
conda env create -f environment.yml
conda activate nlm-ckn-mcp
pip install -e .
```

## MCP client config example

On the mac, the Claude configuration file is called `claude_desktop_config.json`.

It is found here:
```bash
ls ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Choose your best terminal editor, I use `emacs`, `vi` exists without any install.

I used `homebrew` to `brew install` emacs since I use it in all my environments.

If you don't have admin privileges, you can use conda to install emacs


```bash
conda install conda-forge::emacs -y
```

The `-y` just allows the install to happen with out you being asked again.


Recommended (works reliably in Claude Desktop and other clients that do not inherit your virtualenv PATH):

```json
{
  "mcpServers": {
    "NLM-CKN": {
      "command": "/Users/**[username]**/miniforge3/envs/nlm-ckn-mcp/bin/python",
      "args": [
        "-m",
	"cell_kg_mcp"
      ]
    }
  }
```

## What is happening?

```bash
You (in Claude Desktop)
      │  "search for T cells"
      ▼
Claude decides to use a tool  ──►  server.py  ──►  client.py  ──►  https://cell-kn.org
      ◄──────────────────────────  results  ◄──  raw data  ◄──────  (the real website)
```
 the actual MCP server. It wraps the client and announces tools to Claude:

## The MCP src pattern

This code was supplied by Senior Solutions Engineer, Sangram Sahu and it follows a very common, sensible pattern: 

* separate "what to expose to Claude" from "how to actually talk to the website."

### `client.py` — the part that talks to cell-kn.org

This file knows nothing about MCP or Claude. It's just plain Python that knows how to call the website's search API. 
If you opened a Python shell, you could use it by hand:

* `CellKgSearchClient` is an object that knows the website address (https://cell-kn.org) and how to build the right search request.

Its search(...) method (client.py:40) does the real work: 

* it cleans up your query, 
* picks which fields to search, 
* sends an HTTP POST to /arango_api/search/, 
* checks for errors, and 
* returns the results as a list.

`DEFAULT_SEARCH_FIELDS (client.py:8)` is just the canned list of which database columns to search for each database type (phenotypes vs ontologies).

You could reuse this file in a script that has nothing to do with Claude. That's the point of keeping it separate.

### `server.py` — the part that exposes those abilities to Claude

This is the actual MCP server. It wraps the client and announces tools to Claude:

* mcp = FastMCP("cell-kg-search") (server.py:9) creates the server. 

FastMCP is a helper library that handles all the gory MCP protocol details for you.

* The @mcp.tool() decorator is the magic. 
* Any function with that decorator on top becomes a tool Claude can see and call. 

Sangram exposed two:

* search_cell_kn (server.py:31) — the search itself.
* get_cell_kn_search_defaults (server.py:60) — tells Claude which fields are searched by default.

The docstring under each function (the """...""" text) is literally what Claude reads to decide when to use the tool. 

The function arguments (query, db, limit...) become the inputs Claude fills in.
_compact_result (server.py:13) just trims each result down to the useful fields so Claude isn't flooded with junk.

* main() (server.py:66) calls mcp.run(), which starts the server and waits for Claude to talk to it.

### Summarizing

So the rule of thumb: 

* server.py = the menu Claude sees. 
* client.py = the kitchen that actually cooks.

### How it actually gets launched

You never run this server by double-clicking it. 

Claude Desktop launches it for you. 

That's what the config block in the README does:

"NLM-CKN": {
  "command": "/Users/**[username]**/miniforge3/envs/nlm-ckn-mcp/bin/python",
  "args": ["-m", "cell_kg_mcp"]
}

This tells Claude Desktop: 

* "To start the NLM-CKN tools, run this exact Python with -m cell_kg_mcp." 
* The -m cell_kg_mcp runs src/cell_kg_mcp/__main__.py, which calls main(), which starts the server. 
* Claude and the server then talk to each other over the program's input/output pipes (this is the "stdio" transport — the default, no networking involved).


That's also why the README is so insistent about the absolute path to Python: 

Claude Desktop doesn't know about your conda environment, so you have to spell out exactly which Python has the mcp and requests libraries installed.

###  What to do to set it up?

Boils down to:
* Install it into a conda env

```bash
conda env create -f environment.yml
pip install -e .
```

* Tell Claude Desktop about it by editing `claude_desktop_config.json` with the `absolute path` to that `env's Python (the JSON block above)`.
* Restart Claude Desktop. 

It launches the server, sees the two tools, and you're done.

Test the plumbing independently with pytest — those tests in test_client.py fake the website and check the client builds the right request, so you can confirm the logic without hitting the network.

### Final note

Replace [username] with your [username]!

## Notes about the live endpoint

- `https://cell-kn.org/` over HTTPS serves the real app.
- `http://cell-kn.org/` currently serves a default Apache page.
- The endpoint requires `search_fields` in the payload.

## Troubleshooting

- Error: `Failed to spawn process: No such file or directory`
  - Cause: client cannot find `cell-kg-mcp` on PATH.
  - Fix: use the absolute Python command config above.
- Error sequence: `write EPIPE` right after initialize
  - Usually a follow-on error because the server process failed to spawn or exited early.
  - Fix: switch to absolute command + `cwd`, then restart the MCP client.

## Run tests

```bash
pytest
```
