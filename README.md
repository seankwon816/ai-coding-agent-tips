# AI Coding Agent Tips & Config Auditor

Zero-dependency local security auditor, drop-in `AGENTS.md` / `CLAUDE.md` rules, and doc-verified fixes for Claude Code, OpenAI Codex CLI, Cursor, and MCP servers. Every fix is verified word-for-word against official documentation or published studies.

## 1-Command Local Audit (Python 3 stdlib, read-only)

Scan a project for inline credentials inside `.claude/settings.local.json` and `.mcp.json`, unpinned `npx -y` MCP servers, missing `.gitignore` / `.dockerignore` exclusions (`COPY . .` leaks), non-blocking `exit 1` hook rules, out-of-range `autoCompactWindow` settings, unmirrored sandbox `denyRead` paths and unsandboxed escape hatches, blanket `permissions.allow` wildcards, `enableAllProjectMcpServers: true` auto-approvals, shadowed `AGENTS.md` rules, codebase-ownership prompt bloat, and `0.0.0.0` MCP bindings:

```bash
curl -fsSL https://raw.githubusercontent.com/seankwon816/ai-coding-agent-tips/main/scripts/audit_agent_configs.py | python3 - .
```

Or run from a local clone (`exit 0` when clean, `1` when findings exist; supports `--json`):

```bash
python3 scripts/audit_agent_configs.py .
```

## Drop-In Starter Rules

- **[rules/AGENTS.minimal-diffs.md](rules/AGENTS.minimal-diffs.md)**: Ready-to-paste `AGENTS.md` / `CLAUDE.md` rules for surgical diffs, two-phase commits, `$ENV_VAR` command safety, and ignore hygiene.

## Verified Field Fixes

| Area | Fix | What it solves |
|---|---|---|
| Claude Code / Docker | [Inline API keys written by "Yes, and don't ask again"](tips/claude-local-settings-inline-secrets.md) | 31,088 GitHub secrets & 613 Docker Hub leaks from `.claude/settings.local.json` |
| Claude / AGENTS.md | [Prompts claiming codebase ownership cause unrequested refactors](tips/codebase-ownership-causes-unrequested-refactors.md) | Ownership prompts raise unrequested code consolidation from under 10% to about 75% |
| Any agent | [Split coding-agent commits into prep and logic phases](tips/split-agent-commits-two-phases.md) | Oversized agent diffs that mix renames and formatting into feature logic |
| Claude Code | [AGENTS.md ignored when CLAUDE.local.md exists](tips/agents-md-ignored-with-claude-local-md.md) | A personal file silently turns off your shared AGENTS.md |
| Claude Code | [Run the Explore subagent on Haiku](tips/explore-subagent-on-haiku.md) | Codebase searches running on your biggest model |
| Claude Code | [.worktreeinclude and worktree.baseRef](tips/worktreeinclude-and-baseref.md) | New worktrees with no .env that start from main |
| Any agent | [Surgical changes rule](tips/surgical-changes-rule.md) | 3-line fixes that come back as 300-line diffs |
| MCP | [Bind local HTTP servers to 127.0.0.1](tips/mcp-http-bind-localhost.md) | Local MCP servers open to your whole network |
| MCP | [Batch browser MCP form fills and return DOM deltas to cut replay tokens](tips/browser-mcp-batched-dom-deltas.md) | Multi-turn browser MCP form fills replay full ARIA trees each step, reaching 72,614 cumulative tokens |
| Claude Code | [Cap 1M auto-compaction earlier when long sessions drive up token spend](tips/cap-1m-auto-compact-window.md) | On 1M-window models, waiting until ~967K tokens to compact pushes two thirds of spend into the tail |
| Claude Code | [Block unfinished agent edits with Stop hook exit code 2 before PR review](tips/stop-hook-exit-2-pre-review-gates.md) | AI coding PRs are 154% larger and carry up to 2.74x more security flaws, stalling human code review |
| MCP | [Lock down MCP servers with headersHelper, allowlists, and strict-mcp-config](tips/mcp-lockdown-headershelper-and-strict-config.md) | In MCPTox tests across 45 live MCP servers, hidden rules in tool descriptions reached 72.8% attack success |
| Claude Code | [Bound headless agent loops with --max-turns and --max-budget-usd](tips/cap-headless-runs-with-max-turns.md) | Across 27,280 coding agent runs, step count drove inference cost while starting prompt size barely mattered |
| Claude Code | [Mirror sandbox denyRead rules in permissions.deny and disable unsandboxed retries](tips/sandbox-denyread-and-escape-hatch-lockdown.md) | `sandbox.filesystem.denyRead` blocks bash only, leaving built-in `Read` and unsandboxed retries open |
| Python / Security | [Audit site-packages .pth startup hooks in coding-agent Python environments](tips/audit-python-pth-startup-hooks.md) | Compromised Python wheels (`agent-framework` 1.26.1/1.26.2) harvest keys via `.pth` hooks even without import |
| Any agent | [Put a deterministic fail-before-fix proof gate ahead of human PR review](tips/deterministic-pr-proof-gates-review-bottlenecks.md) | 655-firm and 500k-dev studies show code review stalls and releases lag when vacuous agent PRs pass green CI |
| Claude Code | [Enforce hard tool and approval gates instead of relying on prompt-injection filters](tips/gate-agent-actions-against-data-only-injection.md) | Prompt-injection detectors look for adversarial instructions inside tool results, not plausible numbers |
| MCP | [Route all MCP stdio server logs to stderr so stdout carries JSON-RPC only](tips/mcp-stdio-route-logs-to-stderr.md) | In an MCP `stdio` server, all client-server traffic shares a single newline-delimited `stdout` pipe with no... |

| Claude Code | [Audit MCP tools/list for credential exposure and avoid enableAllProjectMcpServers](tips/audit-mcp-tools-list-credential-exposure.md) | Teams often scan MCP servers only for hidden prompt-injection strings and stop there |

| Any agent | [Isolate coding-agent containers with --network none, --read-only, and seccomp](tips/isolate-agent-containers-network-seccomp-imds.md) | Running an open-weight coding model on your own hardware controls where the weights live, not what shell co... |

| MCP | [Trim agent tool results to a 5-field allowlist to raise solve rate and cut token spend](tips/trim-agent-tool-results-field-allowlist.md) | Returning raw REST or MCP JSON payloads from list tools floods the agent's context with URLs, avatar object... |

| Any agent | [Audit AI email connectors against indirect prompt injection](tips/audit-ai-email-connectors-against-indirect-prompt-injection.md) | When you ask an AI assistant to summarize an email, calendar invite, or PDF, the model reads your prompt an... |

_Last checked: 2026-11-21_

## How each tip is written

- One concrete problem, one copy-pasteable fix, and a link to the exact official doc or study lines that prove it.
- Automated verification ([contributing guide](CONTRIBUTING.md)) checks quote accuracy and keeps every tip free of noise.

## License

MIT
