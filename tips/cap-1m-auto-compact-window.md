# Cap 1M auto-compaction earlier when long sessions drive up token spend

**Checked on:** Claude Code model configuration & env vars docs and tokendoctor session replay benchmark, 2026-11-17

## What goes wrong

On 1M-window models, waiting until ~967K tokens to compact pushes two thirds of spend into the tail. Every turn re-sends the full conversation history, so late compaction compounds input costs across long sessions. In a replay comparison of roughly 23K versus 19K main-thread requests, capping the auto-compact window at 400K tokens and routing subagents to Sonnet dropped average context per request from 412K to 219K and API list cost per request by 38%, while adding more frequent summaries averaging 79 seconds each. Watch the configuration unit difference too: bare numbers in `CLAUDE_CODE_AUTO_COMPACT_WINDOW` are read as raw tokens (`200` means 200 tokens even though `/autocompact 200` means 200,000), and `autoCompactWindow` in `settings.json` expects 100000 to 1000000.

## Fix

Run `/autocompact 400k` inside Claude Code when your session logs exceed 400K tokens, or set `autoCompactWindow` in `~/.claude/settings.json` and assign subagents to a smaller model:

```json
{
  "autoCompactWindow": 400000,
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"
  }
}
```

In shell scripts or CI launches, pass an integer token count like `400000` (or `400k` on current Claude Code releases) and audit local settings for out-of-range numbers:

```bash
CLAUDE_CODE_AUTO_COMPACT_WINDOW=400k CLAUDE_CODE_SUBAGENT_MODEL=sonnet claude
python3 scripts/audit_agent_configs.py .
```

## Source

- https://code.claude.com/docs/en/model-config: "A number with no suffix is read as that many tokens, so `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200` means 200 tokens even though `/autocompact 200` means 200,000."
- https://code.claude.com/docs/en/settings-reference: "Set how full the context window gets before Claude Code compacts automatically."
- https://code.claude.com/docs/en/env-vars: "Set the auto-compact window, which is how full the context gets before compaction, to a token count of `100000` or more."
- https://code.claude.com/docs/en/costs: "compacting a large context is itself a large request."
- https://raw.githubusercontent.com/localixai/tokendoctor/main/README.md: "On models with a 1M window, Claude Code compacts only near 967K tokens, so the end of a long session is the expensive part."
- https://raw.githubusercontent.com/localixai/tokendoctor/main/README.md: "So I set a 400K window and Sonnet for subagents. Comparing the month before with the week after, about 23K and 19K main-thread requests, context per request went from 412K to 219K and cost per request fell 38% at API list prices."
- https://raw.githubusercontent.com/localixai/tokendoctor/main/README.md: "The catch is more summaries, and each is a pause: 79 seconds on average in my sessions."

---

[All verified fixes & 1-command config auditor](../README.md)
