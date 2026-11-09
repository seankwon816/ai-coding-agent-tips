# Stop coding agents from rewriting lines you didn't ask about

**Checked on:** CLAUDE.md / AGENTS.md rules, 2026-11-09

## What goes wrong

Ask for a 3-line bug fix and the agent also reformats nearby code, reorders imports, renames variables, or deletes old comments. The diff gets big and review gets slow.

## Fix

Add a scope rule to your root `CLAUDE.md` or `AGENTS.md`. It is adapted from the "Surgical Changes" section of andrej-karpathy-skills:

```markdown
## Surgical Changes
- Touch only the files and lines the request needs.
- Don't reformat, reorder imports, or refactor nearby code that the task doesn't need.
- Remove only the imports, variables, or functions your own change made unused.
- If you spot unrelated dead code, mention it in your summary. Don't delete it.
```

## Source

- https://github.com/forrestchang/andrej-karpathy-skills: "Touch only what you must. Clean up only your own mess."
