# Run Claude Code's built-in Explore subagent on Haiku

**Checked on:** Claude Code docs, 2026-11-09

## What goes wrong

Claude Code hands codebase searches to its built-in `Explore` subagent. Explore runs on your main conversation's model. If your main model is Fable and you use a Claude subscription, a Console account, or a gateway through `ANTHROPIC_BASE_URL`, Explore runs on Opus instead. Either way, plain file searching runs on a large model.

## Fix

Create `.claude/agents/Explore.md` (one project) or `~/.claude/agents/Explore.md` (all projects). A subagent named `Explore` replaces the built-in one and keeps its own model:

```markdown
---
name: Explore
description: Fast, read-only codebase search and file discovery
model: haiku
disallowedTools: Write, Edit
---

Find the files and code the task needs. Use Read, Grep, and Glob. Return short findings with file paths.
```

## Source

- https://code.claude.com/docs/en/sub-agents: "A user or project subagent named `Explore` overrides the built-in and keeps its own `model` field, so define one with `model: haiku` to run exploration on a lower-cost model."
- https://code.claude.com/docs/en/sub-agents: "Tools: read-only tools; Write and Edit are denied"
