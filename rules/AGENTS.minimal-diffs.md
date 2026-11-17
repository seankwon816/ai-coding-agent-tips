# Drop-In Agent Rules: Minimal Diffs & Secret Safety

Paste these sections into your root `AGENTS.md` or `CLAUDE.md` to keep diffs reviewable and prevent accidental credential writes.

```markdown
## Scoped Changes
- Touch only the files and lines required to complete the requested task.
- Avoid drive-by refactors, unrelated renames, import reordering, or dead-code sweeps unless explicitly asked.
- Leave out codebase ownership prompts so changes stay surgical and token usage stays predictable.

## Two-Phase Commits
- Place mechanical edits (renames, formatting, import cleanup) in an isolated prep commit.
- Put behavior changes and their tests in a separate commit focused on a single purpose.

## Credentials & Local Ignore Hygiene
- Reference credentials via environment variables (for example `$N8N_API_KEY`) rather than inline tokens in shell commands.
- Ensure `.claude/settings.local.json` and `.env` files are excluded in both `.gitignore` and `.dockerignore`.
- Never bind local HTTP tool servers to all interfaces without auth; bind to `127.0.0.1` and verify `Origin`.
```
