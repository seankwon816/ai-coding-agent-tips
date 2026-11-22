# Separate AI project memory with a three-layer setup

**Checked on:** Anthropic Engineering context engineering guide, OpenAI Help Center, and Claude Help Center, 2026-11-22

## What goes wrong

Global AI memory loads into every conversation thread. When you keep client constraints, repo conventions, formatting rules, and one-off task instructions inside one shared memory bucket, unrelated rules bleed across projects.

As extra tokens accumulate in the context window, recall accuracy drops (a failure mode Anthropic Engineering calls context rot). Instead of forgetting your instructions, the assistant pulls stale rules from an older project into your current work.

## Fix

Split persistent instructions into three distinct layers and sweep Saved Memory once a month:

```text
3-Layer AI Memory Setup Template

1. Global Memory (5 lines max)
   Keep only your role, preferred tone, output format, and units.
   Delete all project-specific or client-specific rules.

2. Isolated Project Memory
   Store repo conventions, client specs, and style guides strictly inside each Project.
   - ChatGPT: Project Settings > Project-only memory
   - Claude: Project Memory > turn OFF "Use account memory"

3. Plain NOTES.md File (edited directly in the project)
   Track active goals, open decisions, and next steps outside chat history.

4. Monthly 60-second sweep
   Open Saved Memory once a month and remove stale one-off instructions.
```

Keep a lightweight `NOTES.md` inside each working project folder so long multi-step sessions stay grounded without bloating global memory:

```markdown
# NOTES.md

## Active Goal
- Ship v1 invoice parser without changing the CSV export schema.

## Open Decisions
- Confirm timeout threshold for external webhook retries (default 15s).

## Next Steps
1. Add unit test for malformed UTF-8 rows.
2. Run pytest on tests/test_parser.py and record failures here.
```

## Source

- https://www.anthropic.com/research/effective-context-engineering-for-ai-agents: "as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases."
- https://www.anthropic.com/research/effective-context-engineering-for-ai-agents: "LLMs have an \"attention budget\" that they draw on when parsing large volumes of context."
- https://www.anthropic.com/research/effective-context-engineering-for-ai-agents: "maintaining a NOTES.md file, this simple pattern allows the agent to track progress across complex tasks, maintaining critical context and dependencies that would otherwise be lost across dozens of tool calls."
- https://help.openai.com/en/articles/10169521-projects-in-chatgpt: "Projects keep related chats, files, and instructions together."
- https://help.openai.com/en/articles/10169521-projects-in-chatgpt: "Shared projects automatically use project-only memory and cannot access an individual member's memories or context from outside the project."
- https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context: "To keep a project's memory fully separate, turn off \"Use account memory\" under Memory on the project's page."

---

[All verified fixes & 1-command config auditor](../README.md)
