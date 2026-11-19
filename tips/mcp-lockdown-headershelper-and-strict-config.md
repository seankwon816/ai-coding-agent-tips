# Lock down MCP servers with headersHelper, allowlists, and strict-mcp-config

**Checked on:** MCPTox (arXiv:2508.14925), Anthropic Engineering, and Claude Code MCP docs, 2026-11-18

## What goes wrong

In MCPTox tests across 45 live MCP servers, hidden rules in tool descriptions reached 72.8% attack success. Across 353 real tools and 1,348 cases against 20 LLM agents, the highest model refusal rate stayed below 3%. Plaintext tokens inside `.mcp.json` `env` blocks or unpinned `npx -y` servers give untrusted tool metadata direct access to developer credentials and local files, while upfront tool schemas can consume 150,000 tokens before work begins.

## Fix

Replace inline `.mcp.json` secrets with dynamic `headersHelper` auth and defer tools with `"alwaysLoad": false` (`ToolSearch`):

```json
{
  "mcpServers": {
    "internal-api": {
      "type": "http",
      "url": "https://mcp.internal.example.com/mcp",
      "headersHelper": "/opt/bin/get-mcp-auth-headers.sh",
      "alwaysLoad": false
    }
  }
}
```

Restrict approved servers in managed settings (`managed-mcp.json` or `allowedMcpServers`), isolate CI sessions with `--strict-mcp-config`, and scan project files with `audit_agent_configs.py`:

```json
{
  "allowManagedMcpServersOnly": true,
  "allowedMcpServers": [
    { "serverUrl": "https://*.internal.example.com/*" }
  ]
}
```

```bash
claude --strict-mcp-config --mcp-config ./vetted.json
python3 scripts/audit_agent_configs.py .
```

## Source

- https://arxiv.org/abs/2508.14925: "MCPTox is constructed upon 45 live, real-world MCP servers and 353 authentic tools...achieving an attack success rate of 72.8\%...less than 3\%"
- https://www.anthropic.com/engineering/code-execution-with-mcp: "This reduces the token usage from 150,000 tokens to 2,000 tokens...a time and cost saving of 98.7%"
- https://code.claude.com/docs/en/mcp: "set the server's `headersHelper` to a command. Claude Code runs it when connecting and merges its output into the headers it sends...Start the session with [`--strict-mcp-config`](https://code.claude.com/docs/en/cli-reference#cli-flags). Claude Code then loads the servers you pass with `--mcp-config`...To keep all of a server's tools behind tool search, set `\"alwaysLoad\": false` in that server's entry in your MCP configuration."
- https://code.claude.com/docs/en/managed-mcp: "Deploy a fixed server set with `managed-mcp.json`...`allowedMcpServers`/`deniedMcpServers` for filtering what users configure."
