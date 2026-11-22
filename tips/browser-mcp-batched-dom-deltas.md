# Batch browser MCP form fills and return DOM deltas to cut replay tokens

**Checked on:** MCP specification 2025-06-18, Claude Code env vars docs, and tiktoken browser benchmark, 2026-11-17

## What goes wrong

Multi-turn browser MCP form fills replay full ARIA trees each step, reaching 72,614 cumulative tokens. Because chat agents re-read every prior tool result on each turn, a 3,582-token ARIA snapshot sent across 11 separate form-fill turns compounds from 12,197 direct tokens to 72,614 cumulative tokens. Passing uploaded files inline as Base64 adds similar bloat (44,728 tokens for a 48 KiB PDF versus 85 tokens as a disk path), and oversized MCP outputs trigger warnings past 10,000 tokens before hitting Claude Code's 25,000-token cap.

## Fix

Batch multi-field inputs into one call, return only changed DOM elements (56 tokens vs 3,582 for full ARIA, dropping the 10-field form benchmark to 811 tokens), pass local file uploads by disk path, and gate final submit buttons behind user confirmation:

```json
{
  "tool": "fill_form_batch",
  "arguments": {
    "fields": {
      "owner": "billing-team",
      "plan": "annual",
      "attachmentPath": "./fixtures/receipt.pdf"
    },
    "returnMode": "dom_delta",
    "allowSubmit": false
  }
}
```

```bash
# Claude Code warns on MCP outputs over 10,000 tokens and caps at 25,000 by default
echo "${MAX_MCP_OUTPUT_TOKENS:-25000}"
```

## Source

- https://modelcontextprotocol.io/specification/2025-06-18/server/tools: "Prompt for user confirmation on sensitive operations"
- https://code.claude.com/docs/en/env-vars: "Maximum number of tokens allowed in MCP tool responses (default: 25000). Claude Code displays a warning when output exceeds 10,000 tokens."
- https://raw.githubusercontent.com/Tthanh2k6/turbo-browser-mcp/main/README.md: "11 turns, 12,197 tok direct, 72,614 cumulative | 1 turn, 811 tok | 93.4% direct, 98.9% cumulative"
- https://raw.githubusercontent.com/Tthanh2k6/turbo-browser-mcp/main/README.md: "12,825 chars full ARIA (3,582 tok) | 168 chars (56 tok) | 98.4% vs ARIA"
- https://raw.githubusercontent.com/Tthanh2k6/turbo-browser-mcp/main/README.md: "65,679 chars (44,728 tok) as Base64 | 263 chars (85 tok) disk path | 99.8%"
- https://raw.githubusercontent.com/Tthanh2k6/turbo-browser-mcp/main/README.md: "Buttons that look like a final commit (Submit, Send, Publish, Pay, Confirm, and their Korean, Japanese, Chinese and Vietnamese equivalents) are blocked by default, so an agent can prefill a form and leave the last click to a person."

---

[All verified fixes & 1-command config auditor](../README.md)
