# Prompts claiming codebase ownership cause unrequested refactoring

**Checked on:** Claude Fable 5.2 / Claude Mythos 5.2 prompt engineering docs, 2026-11-16

## What goes wrong

Prompts that assign codebase ownership to a model (such as "You are the owner and long-term maintainer of this codebase") trigger wide refactoring and unrequested code consolidation. In Anthropic testing, consolidation jumped from under 10% without the prompt to about 75% with it, while output tokens rose 70 to 80%. Scope constraints like "No drive-by refactors, renames or cleanups" fail to stop it in more than half of runs.

## Fix

Omit code ownership instructions from system prompts and AGENTS.md rules when you need minimal, targeted diffs:

```markdown
<!-- Bad: triggers unrequested code consolidation and architectural edits -->
You are the owner and long-term maintainer of this codebase, and its design is up to you.

<!-- Good: keep the prompt scoped to the requested change -->
Make only the changes required to satisfy the user request.
```

## Source

- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2.md: "Leave the ownership sentence out where the user owns the code and wants it changed as little as possible"
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2.md: "With this prompt, output tokens rose by about 70 to 80 percent and the model made changes nobody had asked for"

---

[All verified fixes & 1-command config auditor](../README.md)
