# AI Coding Agent Tips

Small, copy-paste fixes for AI coding agents: Claude Code, OpenAI Codex CLI, Cursor, MCP servers, and the setups around them. Each tip is checked against the official docs for the version it names.

## Tips

| Area | Tip | What it fixes |
|---|---|---|
| Claude Code | [AGENTS.md ignored when CLAUDE.local.md exists](tips/agents-md-ignored-with-claude-local-md.md) | A personal file silently turns off your shared AGENTS.md |
| Claude Code | [Run the Explore subagent on Haiku](tips/explore-subagent-on-haiku.md) | Codebase searches running on your biggest model |
| Claude Code | [.worktreeinclude and worktree.baseRef](tips/worktreeinclude-and-baseref.md) | New worktrees with no .env that start from main |
| Any agent | [Surgical changes rule](tips/surgical-changes-rule.md) | 3-line fixes that come back as 300-line diffs |
| MCP | [Bind local HTTP servers to 127.0.0.1](tips/mcp-http-bind-localhost.md) | Local MCP servers open to your whole network |

_Last checked: 2026-11-09_

## How each tip is written

- One problem, one fix, one file in `tips/`.
- A snippet you can paste as is.
- The tool version it was checked on, and a link to the official doc line that backs it.
- If a tip goes stale with a new release, it gets fixed or removed.

## License

MIT
