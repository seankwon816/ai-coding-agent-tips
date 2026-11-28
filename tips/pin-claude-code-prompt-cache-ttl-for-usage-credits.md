# Pin Claude Code promptCacheTtl to 1h when sessions spill into usage credits

**Checked on:** Claude Code Prompt Caching Docs and Settings Reference, 2026-11-27

## What goes wrong

Inside a Claude subscription's included allowance, the main conversation defaults to a 1-hour prompt cache TTL. Once a session crosses the plan limit and bills against paid usage credits, Claude Code drops the main conversation to a 5-minute TTL. API key sessions, cloud providers, subagents, forks, and compaction calls also default to 5 minutes even while you remain inside your subscription allowance.

On a 5-minute TTL, any brief break past five minutes expires the cached prefix and forces the next turn to reprocess the entire conversation history as uncached input. Running `/compact` after a pause longer than the TTL is especially expensive because the summarization request resends your system prompt, tools, and full history uncached right before discarding them. Separately, a custom `ANTHROPIC_BASE_URL` gateway that strips `cache_control` markers or flattens block-form system prompts into a plain string while returning success causes every turn to bill uncached.

## Fix

Verify which TTL bucket your session actually writes to before changing settings:

```bash
claude -p "hello" --output-format json
```

Inspect `usage.cache_creation` in the JSON output: 1-hour writes appear under `ephemeral_1h_input_tokens`, and 5-minute writes appear under `ephemeral_5m_input_tokens`. Inside an interactive session, run `/usage` and read the `Prompt cache (main)` line for hit ratio, warm status, and likely cause of the last miss.

If your sessions include frequent breaks longer than five minutes on usage credits or API keys, pin the main conversation TTL to `1h` in `~/.claude/settings.json` (or `.claude/settings.json`):

```json
{
  "promptCacheTtl": "1h",
  "subagentPromptCacheTtl": "5m"
}
```

Key rules and tradeoffs:

1. **Use exact values (`"5m"` or `"1h"`):** Claude Code silently ignores any other value in `promptCacheTtl`, `subagentPromptCacheTtl`, `CLAUDE_CODE_PROMPT_CACHE_TTL`, or `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`.
2. **Watch override precedence:** `FORCE_PROMPT_CACHING_5M=1` takes highest priority and forces 5 minutes for both buckets, overriding `promptCacheTtl: "1h"` and `ENABLE_PROMPT_CACHING_1H=1`. Remove leftover `FORCE_PROMPT_CACHING_5M` or `DISABLE_PROMPT_CACHING*` flags from settings `env` after debugging.
3. **Prefer `/rewind` over cold `/compact` when abandoning a branch:** `/rewind` truncates back to a prefix that is still cached instead of triggering a fresh summarization pass.
4. **Match TTL to work cadence:** The 1-hour TTL charges a higher cache write rate than 5 minutes. Keep `5m` for tight, non-stop bursts; pin `1h` for longer sessions with reviews, meetings, or multi-minute pauses.
5. **Check gateway header forwarding:** When routing through `ANTHROPIC_BASE_URL`, forward `anthropic-beta` headers and `cache_control` markers unchanged.

## Source

- https://code.claude.com/docs/en/prompt-caching.md: "Unless you choose a TTL yourself, Claude Code requests the one-hour TTL only on a Claude subscription within your plan's included usage. ... Once you go over your plan's usage limit and Claude Code draws on usage credits, you are billed for that usage, so Claude Code drops the main conversation to the five-minute TTL, which charges a lower rate for cache writes. ... Each control takes 5m or 1h, and Claude Code ignores any other value."
- https://code.claude.com/docs/en/prompt-caching.md: "After a break longer than the cache lifetime, there is no cache left to read, so the summarization request reprocesses that history as uncached input. ... Rewinding truncates back to a prefix that is already cached, rather than building a new one as compaction does. ... To confirm which TTL your main conversation's cache writes used, run claude -p \"hello\" --output-format json and read usage.cache_creation in the result. Claude Code reports one-hour cache writes under ephemeral_1h_input_tokens and five-minute cache writes under ephemeral_5m_input_tokens."
- https://code.claude.com/docs/en/prompt-caching.md: "Removes the markers while returning success: your entire conversation history bills as uncached input on every turn. A gateway that converts block-form system content to a plain string drops the marker the same way."
- https://code.claude.com/docs/en/settings-reference.md: "Choose how long the prompt cache holds the main conversation. ... Choose how long the prompt cache holds the requests Claude Code makes outside the main conversation."

---

[All verified fixes & 1-command config auditor](../README.md)
