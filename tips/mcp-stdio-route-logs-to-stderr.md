# Route all MCP stdio server logs to stderr so stdout carries JSON-RPC only

**Checked on:** Model Context Protocol stdio transport specification, 2026-11-20

## What goes wrong

In an MCP `stdio` server, all client-server traffic shares a single newline-delimited `stdout` pipe with no per-request streams. The transport does not strip non-protocol output, so a single `print()`, `console.log()`, or third-party library logger writing to `stdout` corrupts the wire stream mid-session.

Because the server process does not crash, the bug surfaces on the client side as a `JSONDecodeError` or dropped response on an unrelated tool call. Database drivers, HTTP clients, and SDK banners that log to `stdout` by default trigger this the moment a code path touches them.

## Fix

Send every server and dependency log stream to `stderr` before starting the MCP stdio transport, and keep `stdout` reserved for newline-delimited JSON-RPC messages.

Python:

```python
import logging
import sys

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    force=True,
)
```

Node.js / TypeScript:

```ts
// Redirect stray console.log calls away from the JSON-RPC stdout pipe
console.log = (...args: unknown[]) => console.error(...args);
```

Verify that a server's `stdout` emits only valid JSON-RPC lines before registering it in `.mcp.json`:

```python
import json, subprocess, sys

proc = subprocess.run([sys.executable, "server.py"], capture_output=True, text=True)
for idx, line in enumerate(proc.stdout.splitlines(), 1):
    try:
        json.loads(line)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Non-JSON line on stdout (line {idx}): {line!r} ({exc})")
```

## Source

- https://modelcontextprotocol.io/specification/latest/basic/transports/stdio: "The server reads JSON-RPC messages from `stdin` and writes JSON-RPC messages to `stdout`...Messages are delimited by newlines, and **MUST NOT** contain embedded newlines...The server **MAY** write UTF-8 strings to `stderr` for any logging purposes including informational, debug, and error messages...The server **MUST NOT** write anything to its `stdout` that is not a valid MCP message."
- https://modelcontextprotocol.io/specification/latest/basic/transports/stdio: "The client reads server messages from `stdout`, one message per line. All messages share this single channel; there are no per-request streams."

---

[All verified fixes & 1-command config auditor](../README.md)
