#!/usr/bin/env python3
"""PreToolUse guard: keep Claude away from AnkiConnect except via the anki MCP server.

The MCP server (tools/anki_mcp.py) only allows read + add. This hook closes the
obvious side doors:
  - Bash commands that talk to AnkiConnect directly (port 8765) or name a
    delete action, e.g. `curl localhost:8765 -d '{"action": ...}'`.
  - Write / Edit / NotebookEdit content that names an AnkiConnect delete action,
    so Claude can't write a script or notebook cell that deletes cards.

Best effort, not a sandbox: a determined workaround could still get past a
string match. Exit code 2 blocks the tool call and shows stderr to Claude.
"""

import json, re, sys

DELETE_RE = re.compile(r"delete(?:Notes|Decks|MediaFile|Model)|removeEmptyNotes", re.I)
PORT_RE   = re.compile(r"8765")

def block(msg):
    print(f"Blocked by .claude/hooks/guard_anki.py: {msg}", file=sys.stderr)
    sys.exit(2)

event = json.load(sys.stdin)
tool  = event.get("tool_name", "")
text  = json.dumps(event.get("tool_input", {}))

if tool == "Bash" and (PORT_RE.search(text) or DELETE_RE.search(text)):
    block("don't call AnkiConnect directly — use the anki MCP tools (read + add only).")

if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit") and DELETE_RE.search(text):
    block("writing code that deletes Anki notes/decks is not allowed in this repo.")
