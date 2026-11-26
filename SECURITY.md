# Security Policy

## Scope

`scripts/audit_agent_configs.py` runs locally, read-only, with Python 3 standard library only and zero network calls. Detected inline secrets are redacted in terminal and JSON output.

## Reporting a Vulnerability or False Negative

If you find a security issue in the auditor script, a bypassed detection rule, or accidentally exposed sensitive data in this repository:

1. Use [GitHub Security Advisories](https://github.com/seankwon816/ai-coding-agent-tips/security/advisories/new) to report sensitive issues privately.
2. For non-sensitive rule gaps or false positives, open an Issue using the `Tip is outdated or wrong` template and include a minimal redacted reproducer.

Never paste real API keys, tokens, or private `.env` files into public Issues or Pull Requests.
