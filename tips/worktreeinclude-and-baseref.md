# New Claude Code worktrees miss your .env and start from main

**Checked on:** Claude Code docs, 2026-11-09

## What goes wrong

When Claude Code makes a worktree (with `--worktree`, or for a subagent with `isolation: worktree`), it is a fresh checkout. Gitignored files like `.env` are not there, so local runs fail. And it branches from the remote default branch, so your unpushed commits are missing.

## Fix

Add `.worktreeinclude` at the project root. It uses `.gitignore` syntax and lists the gitignored files to copy in:

```text
.env
.env.local
```

To branch from your current work, set this in your settings. The only values are `"fresh"` (the default) and `"head"`. A branch name is not allowed.

```json
{
  "worktree": { "baseRef": "head" }
}
```

## Source

- https://code.claude.com/docs/en/worktrees: "A worktree is a fresh checkout, so untracked files like `.env` or `.env.local` from your main repository are not present. To copy them automatically when Claude creates a worktree, add a `.worktreeinclude` file to your project root."
- https://code.claude.com/docs/en/worktrees: "You can't set `worktree.baseRef` to a branch name."
