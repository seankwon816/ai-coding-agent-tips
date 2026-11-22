# Clicking "Yes, and don't ask again" writes inline API keys to .claude/settings.local.json

**Checked on:** Claude Code permissions & settings docs and GitGuardian scan, 2026-11-16

## What goes wrong

When you approve a shell command with inline credentials by picking "Yes, and don't ask again", Claude Code saves the exact command prefix into `.claude/settings.local.json`, literal API key included. A GitGuardian scan found 31,088 exposed secrets in committed `.claude/settings.local.json` files across 23,276 GitHub repositories (with 5,343 still valid), plus 613 secrets (99 valid) packed into Docker Hub images via `COPY . .`, which ignores `.gitignore`.

## Fix

Pass environment variable names instead of inline tokens so allow rules store only the variable name, ignore `.claude/` in both Git and Docker builds, and run `/permissions` to prune any existing inline secrets:

```text
# .gitignore and .dockerignore
.claude/
.claude/settings.local.json
```

```bash
# Bad: writes literal secret into .claude/settings.local.json
curl -H "X-N8N-API-KEY: n8n_api_9f8a72e1d0b44c21" https://n8n.example.internal/api/v1/workflows

# Good: writes the variable name, expanded from your shell environment at runtime
curl -H "X-N8N-API-KEY: $N8N_API_KEY" https://n8n.example.internal/api/v1/workflows
```

Check your current repo in one command:

```bash
python3 scripts/audit_agent_configs.py .
```

## Source

- https://blog.gitguardian.com/claude-code-settings-local-json-secrets-docker-hub/: "31,088 secrets in Claude Code’s .claude/settings.local.json on public GitHub, 5,343 valid at detection, 23,276 repositories. 613 more in Docker Hub images, 99 valid."
- https://code.claude.com/docs/en/permissions.md: "Claude Code saves the rule to .claude/settings.local.json at the root of the git repository"
- https://code.claude.com/docs/en/settings.md: "Claude Code keeps it out of git when it creates the file; if you create it by hand, add it to .gitignore yourself"

---

[All verified fixes & 1-command config auditor](../README.md)
