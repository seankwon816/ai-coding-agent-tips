# Gate both MCP skill loads and ReadMcpResourceTool for remote servers

**Checked on:** MCP Skills Extension beta spec (SEP-2640) and Claude Code MCP docs, 2026-11-25

## What goes wrong

Denying MCP skills leaves raw `resources/read` open, and SEP-2640 SHA-256 digests are unsigned.

Under the Skills over MCP beta specification (`io.modelcontextprotocol/skills`, SEP-2640), skill files still travel through standard `resources/read` calls on `skill://` URIs. Reading a `SKILL.md` through `resources/read` does not activate the skill, yet the returned bytes still enter model context. In Claude Code, blocking skills with `Skill(mcp__docs__*)` in `permissions.deny` or setting `disableDirectMcpSkills` to `true` stops skill activation while keeping normal MCP resource reads allowed.

Two more gaps affect remote servers:

1. `skills/get` SHA-256 digests are unsigned and come from the same server that serves the files. They detect mid-session changes after approval, but a compromised server or gateway can rewrite both manifest and payload. Servers that declare `"resources": "dynamic"` skip content-bound digest checks altogether.
2. In Claude Code, server-side security scanning covers third-party Directory connectors added on claude.ai and Enterprise custom connectors with scanning enabled. Direct servers added with `claude mcp add` skip that scan, and auto mode's classifier decides whether a skill loads without reading its body.

## Fix

1. Require an interactive prompt before loading remote MCP skills, and deny `ReadMcpResourceTool` when you want to stop raw MCP resource reads (including skill supporting files) from entering context. Put the rules in `.claude/settings.json` or user settings:

```json
{
  "permissions": {
    "ask": [
      "Skill(mcp__docs__*)"
    ],
    "deny": [
      "ReadMcpResourceTool"
    ]
  }
}
```

2. Avoid placing wildcard `Skill(mcp__docs__*)` entries in `permissions.allow` for remote servers whose content can change between sessions.
3. If you disable direct MCP skills with `"disableDirectMcpSkills": true`, pair it with a `ReadMcpResourceTool` rule in `permissions.deny` (or block the server outright with `mcp__docs` in `permissions.deny`) if the server is untrusted.
4. For custom MCP hosts implementing SEP-2640, pin every `{uri, digest}` pair at approval time and reject `"resources": "dynamic"` skills from untrusted origins.

## Source

- https://github.com/modelcontextprotocol/ext-skills/blob/main/specification/beta/skills.mdx: "Digests are unsigned and supplied by the same server that supplies the content. A match proves the two are consistent, not that either is trustworthy."
- https://github.com/modelcontextprotocol/ext-skills/blob/main/specification/beta/skills.mdx: "Skill files are read via the standard `resources/read` method. No skill-specific read semantics are defined."
- https://github.com/modelcontextprotocol/ext-skills/blob/main/specification/beta/skills.mdx: "A skill whose `resources` is `\"dynamic\"` cannot be content-bound."
- https://github.com/modelcontextprotocol/ext-skills/blob/main/specification/beta/skills.mdx: "Hosts **MUST** treat MCP-served skills as a higher-risk surface than remote tool invocation."
- https://code.claude.com/docs/en/mcp: "With `deny` rules, normal [resource reads](#use-mcp-resources) from the server are still allowed. To stop Claude from reading any server's resources, including allowed skills' supporting files, deny `ReadMcpResourceTool`."
- https://code.claude.com/docs/en/mcp: "Normal [resource reads](#use-mcp-resources) from MCP servers are still allowed when skills are turned off."
- https://code.claude.com/docs/en/mcp: "Anthropic doesn't scan skills from other connectors or servers, including Directory servers added with `claude mcp add`."
- https://code.claude.com/docs/en/mcp: "The classifier decides whether the skill loads, without reading it."

---

[All verified fixes & 1-command config auditor](../README.md)
