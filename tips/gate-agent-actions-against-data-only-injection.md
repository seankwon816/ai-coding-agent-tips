# Enforce hard tool and approval gates instead of relying on prompt-injection filters

**Checked on:** Plain-table agent hijack evaluation and Claude Code permissions docs, 2026-11-20

## What goes wrong

Prompt-injection detectors look for adversarial instructions inside tool results, not plausible numbers. In red-team tests against three hardened models, every explicit injection payload (hidden `assistant_action` lines, fake system tags, policy blocks, forged reasoning, and fake user turns) was ignored or flagged.

A plain structured table with no instructions at all bypassed all three models. By placing an unknown domain slightly ahead of a real newsletter (`5.0%` vs `4.0%` conversion, lower cost per signup, `44%` vs `38%` 90-day retention) with no free text or commands, all three hardened models recommended the attacker's domain in their own words. When a coding agent holds blanket `Bash`, `WebFetch`, or `mcp__*` allow rules, clean-looking data from external issues, web pages, or APIs can steer tool calls without tripping text-level injection filters.

## Fix

Treat model-level prompt-injection filtering as defense in depth only, and enforce hard capability boundaries in settings. Permission rules are evaluated in strict order (`deny`, then `ask`, then `allow`), and a matching `deny` or `ask` rule overrides both `allow` rules and a `PreToolUse` hook returning `"allow"`.

Remove blanket wildcards (`Bash`, `Bash(*)`, `WebFetch(*)`, `mcp__*`) from `permissions.allow`, deny outbound exfiltration tools or sensitive paths, and require explicit confirmation (`ask`) for external side effects:

```json
{
  "permissions": {
    "deny": [
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)",
      "Bash(curl *)",
      "Bash(wget *)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(gh pr create *)",
      "WebFetch"
    ],
    "allow": [
      "Bash(pytest *)",
      "Bash(git status)",
      "Bash(git diff *)"
    ]
  }
}
```

Scan `.claude/settings.json` and `.claude/settings.local.json` for blanket wildcard `permissions.allow` rules or `bypassPermissions` defaults:

```bash
python3 scripts/audit_agent_configs.py .
```

## Source

- https://dev.to/edbrdi/can-a-plain-table-hijack-an-ai-agent-2pde: "The hardened models I tested ignored or flagged every instruction I hid in a tool result. Then a plain table, with no instruction in it, got all three of them to recommend a domain they had never seen."
- https://dev.to/edbrdi/can-a-plain-table-hijack-an-ai-agent-2pde: "Fake system tags, policy blocks, forged reasoning, a fake user turn confirming the action: the hardened models ignored or flagged all of them."
- https://dev.to/edbrdi/can-a-plain-table-hijack-an-ai-agent-2pde: "What finally worked was a plain table: source, visits, conversion, cost per signup, 90-day retention. No notes, no free text...5.0% conversion against 4.0% for the newsletter, a lower cost per signup, 44% retention against 38%. All three hardened models recommended the domain, in their own words."
- https://dev.to/edbrdi/can-a-plain-table-hijack-an-ai-agent-2pde: "What held in my tests were limits on what the model could do: a tool it wasn't allowed to call, an action someone had to approve."
- https://code.claude.com/docs/en/permissions: "Rules are evaluated in order: deny, then ask, then allow. The first match in that order determines the outcome, and rule specificity doesn't change the order."
- https://code.claude.com/docs/en/permissions: "PreToolUse hook decisions don't bypass permission rules. Claude Code evaluates deny and ask rules regardless of what a PreToolUse hook returns: a matching deny rule blocks the call, and a matching ask rule still prompts even when the hook returned"

---

[All verified fixes & 1-command config auditor](../README.md)
