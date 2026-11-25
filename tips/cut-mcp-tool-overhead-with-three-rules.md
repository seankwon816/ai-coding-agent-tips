# Cut MCP tool overhead by 85% with three setup rules

**Checked on:** Anthropic Engineering (Nov 4 & Nov 24, 2025) and Model Context Protocol Specification, 2026-11-25

## What goes wrong

Connecting five or more MCP servers globally loads every server's full `tools/list` JSON schema into context before your first prompt. In Anthropic Engineering benchmarks, 50+ preloaded MCP tools consumed roughly 72K to 77K tokens upfront (nearly 40% of a 200K context window) and dragged Claude Opus 4 tool selection accuracy down to 49% because overlapping tool names collide in attention.

Dumping raw multi-thousand-row JSON tool outputs straight into chat history compounds the problem and crowds out reasoning.

## Fix

Apply this 3-rule MCP hygiene checklist before adding another server:

```text
3-Rule MCP Context Hygiene Checklist:

1. Scope Servers Per Workspace (<10 Active Tools)
   - Move global MCP servers into project-level .mcp.json files.
   - Disable unused servers to cut schema tokens and reduce local stdio permission exposure.

2. Turn On Deferred Tool Loading
   - Once a workspace passes 10 tools or 10K schema tokens, set defer_loading: true
     so the model fetches 3 to 5 matching tool schemas on demand.
   - Anthropic benchmark: cuts tool definition overhead by 85% and lifts Opus 4 accuracy
     from 49% to 74%.

3. Filter Bulky Outputs In Code First
   - Trim, slice, and aggregate large JSON tool outputs in a script or sandbox before
     returning results to chat context.
   - Anthropic worked MCP flow: reduced token usage from 150,000 tokens to 2,000 tokens (-98.7%).
```

Example pre-filter before returning rows to the model:

```python
clean = [r for r in rows if r["open"]][:20]
```

## Source

- https://www.anthropic.com/engineering/advanced-tool-use: "Total context consumption: ~77K tokens before any work begins ... This represents an 85% reduction in token usage while maintaining access to your full tool library. ... Opus 4 improved from 49% to 74%"
- https://www.anthropic.com/engineering/code-execution-with-mcp: "This reduces the token usage from 150,000 tokens to 2,000 tokens ... reducing context overhead by up to 98.7%."
- https://modelcontextprotocol.io/specification/2025-06-18/server/tools: "To discover available tools, clients send a tools/list request."

---

[All verified fixes & 1-command config auditor](../README.md)
