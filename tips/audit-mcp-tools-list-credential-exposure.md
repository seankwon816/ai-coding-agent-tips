# Audit MCP tools/list for credential exposure and avoid enableAllProjectMcpServers

**Checked on:** MCP tools specification, Claude Code settings reference, and 220,226-tool live MCP audit, 2026-11-21

## What goes wrong

Teams often scan MCP servers only for hidden prompt-injection strings and stop there. A November 2026 scan of 12,987 live MCP servers (220,226 tools) found 0 ignore-instruction injections and 0 zero-width characters, yet nearly 1 in 4 servers exposed a legitimate tool that touches credentials.

If `.claude/settings.json` or `.claude/settings.local.json` sets `"enableAllProjectMcpServers": true`, every server defined in a project's `.mcp.json` is approved without a prompt in trusted folders. A new server added later in a commit or dependency update gets connected before anyone checks what tools it exposes.

## Fix

1. Replace `enableAllProjectMcpServers: true` with an explicit `enabledMcpjsonServers` allowlist in `.claude/settings.json` or `.claude/settings.local.json`:

```json
{
  "enableAllProjectMcpServers": false,
  "enabledMcpjsonServers": ["memory", "github"]
}
```

2. Inspect `tools/list` on any stdio MCP server before enabling it so you can see every tool name and schema upfront:

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"audit","version":"1.0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | npx -y @modelcontextprotocol/server-memory@0.6.2 \
  | python3 -c 'import json,sys; [print(t["name"], "-", t.get("description","")) for ln in sys.stdin if "\"tools\"" in ln for t in json.loads(ln)["result"]["tools"]]'
```

3. Isolate secrets per server: pass only the single scoped credential a server requires rather than exposing your full shell environment or cloud credentials to every MCP server process.

## Source

- https://dev.to/serverdex/i-scanned-220000-mcp-tool-descriptions-for-prompt-injection-the-scare-is-overblown-but-1-in-4-6pk: "12,987 MCP servers that answer a credential-free handshake ... 220,226 tools in total ... Nearly one in four MCP servers has a tool that touches your secrets."
- https://modelcontextprotocol.io/specification/latest/server/tools: "Servers that declare the tools capability MUST respond to tools/list requests with the set of tools currently available to the requesting client."
- https://code.claude.com/docs/en/settings-reference: "Approve every MCP server defined in project .mcp.json files without a prompt. Claude Code writes this key to .claude/settings.local.json when you choose to approve all servers in the approval dialog."
