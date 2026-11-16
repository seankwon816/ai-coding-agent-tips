# Split coding-agent commits into prep and logic phases

**Checked on:** GitHub 128,018-repository coding-agent study (arXiv:2601.18341), 2026-11-16

## What goes wrong

Across 128,018 GitHub projects, commits assisted by coding agents (Cursor, Claude Code, Codex) are substantially larger than commits authored only by human developers. Agents often bundle file renames, import sorting, and formatting cleanups into the same diff as core logic, slowing down PR reviews and hiding subtle regressions.

## Fix

Add a two-phase commit rule to your root `CLAUDE.md` or `AGENTS.md`:

```markdown
## Two-Phase Commits
- Commit mechanical prep edits (renames, formatting, import sorting) first in an isolated prep commit.
- Implement behavior changes and tests in a second commit scoped to one clear change.
- Keep each commit small enough to explain in a single sentence.
```

## Source

- https://arxiv.org/abs/2601.18341: "We leverage these traces to present the first large-scale study (128,018 projects) of the adoption of coding agents on GitHub"
- https://arxiv.org/abs/2601.18341: "At the commit level, we find that commits assisted by coding agents are larger than commits only authored by human developers, and have a large proportion of features and bug fixes."
