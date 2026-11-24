# Scope ANTHROPIC_API_KEY inline to spend monthly Claude API credits with claude -p

**Checked on:** Claude Support monthly API credits guide and Claude Code authentication docs, 2026-11-23

## What goes wrong

Monthly Claude API credits expire unused every billing cycle, while setting `ANTHROPIC_API_KEY` globally hijacks your subscription budget.

Claude Max ($100/mo), Ultra ($200/mo), and Team ($20 per Standard seat and $100 per Premium seat, pooled up to $500) include monthly Claude Platform API credits after seven days on an eligible plan. Those credits do not deposit automatically, and unused balances expire at the end of each billing cycle.

Interactive Claude Code in the terminal, IDE, desktop app, or web does not draw from those monthly credits. Runs launched by the Claude Code GitHub Action, an IDE extension, or the Claude desktop app also count as Claude Code usage, even with `-p`. On the other hand, exporting `ANTHROPIC_API_KEY` in a shell profile or `.claude/settings.json` causes interactive Claude Code sessions to authenticate with that API key once approved instead of using your subscription plan.

## Fix

1. Claim the monthly grant in a desktop browser under **Settings > Billing** (or **Organization settings > Billing** for Team owners) and click **Link organization** in the API credits section. Pick the target Console organization carefully because each plan links to one organization.
2. Keep `ANTHROPIC_API_KEY` unset in your shell profile and project `.claude/settings*.json` files so interactive sessions stay on your subscription login. If an earlier export took over, reset it and check the active login method:

```bash
unset ANTHROPIC_API_KEY
# Inside Claude Code, run /status to confirm your subscription login is active
```

3. Scope the linked Console organization key inline only for standalone `claude -p` shell commands and local Claude Agent SDK jobs, which Anthropic bills as Agent SDK usage covered by the monthly credits:

```bash
ANTHROPIC_API_KEY="<your-linked-console-api-key>" \
  claude -p "Review the staged git diff for edge cases and missing error handling"
```

If that linked Console organization has no payment card or purchased balance, covered API calls spend the monthly grant first and stop cleanly when the grant reaches zero without charging your Claude subscription.

## Source

- https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans: "API credits cover claude -p and the Claude Agent SDK when you run them yourself with an API key from your linked Claude Console organization, because that usage is billed as Agent SDK usage."
- https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans: "Runs started by the Claude Code GitHub Action, an IDE extension or the Claude desktop app count as Claude Code usage, so API credits don't cover them, even with -p"
- https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans: "Unused credits expire at the end of each billing cycle."
- https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans: "If the organization has no other credits, API requests stop until your next monthly credits arrive. Usage is never charged to your Claude plan."
- https://code.claude.com/docs/en/authentication.md: "Run `unset ANTHROPIC_API_KEY` to fall back to your subscription, and check `/status` to confirm which method is active."

---

[All verified fixes & 1-command config auditor](../README.md)
