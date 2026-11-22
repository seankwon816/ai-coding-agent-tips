# Mirror sandbox denyRead rules in permissions.deny and disable unsandboxed retries

**Checked on:** Anthropic sandboxing engineering write-up and Claude Code sandboxing and permissions docs, 2026-11-19

## What goes wrong

OS sandboxing via macOS Seatbelt and Linux bubblewrap cuts Claude Code permission prompts by 84%, which helps teams avoid approval fatigue and `--dangerously-skip-permissions`. Three configuration gaps still leave credential paths exposed even when `"sandbox": { "enabled": true }` is active:

1. `sandbox.filesystem.denyRead` wraps shell subprocesses only. Built-in tools such as `Read`, `Edit`, `Write`, `WebFetch`, and `WebSearch` run outside the sandbox and follow permission rules instead, so a `denyRead` entry does not stop the `Read` tool from opening `~/.ssh` or `~/.aws`.
2. Leaving `sandbox.allowUnsandboxedCommands` enabled allows blocked commands to retry outside the sandbox. In `bypassPermissions` mode, that retry runs without a prompt.
3. Commands listed in `sandbox.excludedCommands` bypass the sandbox completely, and unlocked repository settings can change `autoAllowBashIfSandboxed` or deny entries unless enforced through managed settings.

## Fix

Enable sandboxing, block unsandboxed retries, require startup failure if sandbox dependencies are missing (`failIfUnavailable`), and mirror sensitive `denyRead` paths inside `permissions.deny`:

```json
{
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws"]
    },
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org"]
    }
  },
  "permissions": {
    "deny": [
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)"
    ]
  }
}
```

Enforce the `sandbox` keys in managed settings so checked-in repository configs cannot loosen them, and scan local `.claude/settings*.json` files for unmirrored `denyRead` paths, unsandboxed escape hatches, or `bypassPermissions` defaults:

```bash
python3 scripts/audit_agent_configs.py .
```

## Source

- https://www.anthropic.com/engineering/claude-code-sandboxing: "sandboxing safely reduces permission prompts by 84%."
- https://www.anthropic.com/engineering/claude-code-sandboxing: "Linux bubblewrap and MacOS seatbelt to enforce these restrictions at the OS level."
- https://code.claude.com/docs/en/sandboxing: "tools such as Read, Edit, Write, WebFetch, and WebSearch follow permission rules instead. A `denyRead` entry doesn't stop the Read tool, and `allowedDomains` doesn't limit WebFetch"
- https://code.claude.com/docs/en/sandboxing: "bypassPermissions mode: the retry runs without a prompt"
- https://code.claude.com/docs/en/sandboxing: "commands that match excludedCommands run unsandboxed"
- https://code.claude.com/docs/en/sandboxing: "Set the key in managed settings to keep a repository from changing it"
- https://code.claude.com/docs/en/permissions: "with `Read(./project/**)` allowed and `Read(~/.ssh/**)` denied, a symlink at `./project/key` pointing to `~/.ssh/id_rsa` is blocked"

---

[All verified fixes & 1-command config auditor](../README.md)
