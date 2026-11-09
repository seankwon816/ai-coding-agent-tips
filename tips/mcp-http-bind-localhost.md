# Local HTTP MCP servers should listen on 127.0.0.1 and check Origin

**Checked on:** MCP specification 2025-03-26, 2026-11-09

## What goes wrong

A November 2026 survey of 99 popular MCP server repos found no tool poisoning in 9,965 tool definitions. The real bugs were in network mode: of the 6 repos that serve MCP over HTTP, 3 listen on every network interface by default with no login. A server on `0.0.0.0` that skips the `Origin` check can be reached from other machines on your network and from web pages through DNS rebinding.

## Fix

```typescript
import express from "express";

const app = express();
const ALLOWED_ORIGINS = new Set(["http://localhost:3000", "http://127.0.0.1:3000"]);

app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin && !ALLOWED_ORIGINS.has(origin)) {
    return res.status(403).json({ error: "Forbidden origin" });
  }
  next();
});

// Loopback only. Never 0.0.0.0 without auth.
app.listen(3001, "127.0.0.1");
```

## Source

- https://modelcontextprotocol.io/specification/2025-03-26/basic/transports: "Servers MUST validate the Origin header on all incoming connections to prevent DNS rebinding attacks"
- https://modelcontextprotocol.io/specification/2025-03-26/basic/transports: "When running locally, servers SHOULD bind only to localhost (127.0.0.1) rather than all network interfaces (0.0.0.0)"
- https://github.com/Ahany1440/mcp-auditor/blob/main/SURVEY.md: "6 repos can serve MCP over HTTP. 3 listen only on localhost by default. 3 listen on every network interface by default with no login"
