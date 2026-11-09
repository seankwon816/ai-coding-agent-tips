# Adding CLAUDE.local.md makes Claude Code stop reading AGENTS.md

**Checked on:** Claude Code v2.1.285, 2026-11-09

## What goes wrong

By default Claude Code reads `AGENTS.md` only when there is no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` in your working directory or above it. `CLAUDE.local.md` counts. So if your repo relies on a shared `AGENTS.md` and you add a personal `CLAUDE.local.md`, Claude quietly stops reading `AGENTS.md`.

## Fix

Type `/config` and set **Project instructions** to `claude-md-and-agents-md`. Or put this in `~/.claude/settings.json` (project and local settings files ignore it):

```json
{
  "pluginConfigs": {
    "cc-plugin-agents-md@builtin": {
      "options": { "instructionFiles": "claude-md-and-agents-md" }
    }
  }
}
```

On versions before v2.1.285, use `agents-md@builtin` as the key. v2.1.285 and later read either key.

## Source

- https://code.claude.com/docs/en/memory: "Because `CLAUDE.local.md` counts, adding one to keep your own uncommitted instructions in a project that relies on `AGENTS.md` stops Claude from reading `AGENTS.md` for you."
- https://code.claude.com/docs/en/memory: "Claude Code reads the entry from `~/.claude/settings.json`, a `--settings` file, or managed settings, and ignores it in project and local settings files."
- https://code.claude.com/docs/en/memory: "Before v2.1.285, the plugin's ID was `agents-md@builtin`, and Claude Code ignored an entry under `cc-plugin-agents-md@builtin`."
