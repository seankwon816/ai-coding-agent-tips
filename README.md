<div align="center">

# AI Coding Agent Tips & Config Auditor

**Zero-dependency local security auditor, drop-in `AGENTS.md` / `CLAUDE.md` rules, and doc-verified fixes for Claude Code, OpenAI Codex CLI, Cursor, and MCP servers.**

[![CI](https://github.com/seankwon816/ai-coding-agent-tips/actions/workflows/ci.yml/badge.svg)](https://github.com/seankwon816/ai-coding-agent-tips/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3 stdlib](https://img.shields.io/badge/Python-3.10%2B%20stdlib%20only-3776AB.svg)](scripts/audit_agent_configs.py)
[![Verified Fixes](https://img.shields.io/badge/Verified_Fixes-31-059669.svg)](#verified-field-fixes-31)

[1-Command Audit](#1-command-local-audit-python-3-stdlib-read-only) · [Starter Rules](#drop-in-starter-rules) · [Browse by Topic](#browse-by-topic) · [All 31 Fixes](#verified-field-fixes-31) · [Tests](#running-tests) · [Community](#community)

</div>

---

Every fix in this repository is checked word-for-word against official documentation or published studies, with copy-pasteable configs and automated integrity tests on every commit.

## Start in 3 Steps

1. **Audit your repo locally (read-only, zero installs):** Run the single Python command below to catch leaked inline keys, unsafe sandbox settings, and broken hooks.
2. **Add baseline agent rules:** Copy [`rules/AGENTS.minimal-diffs.md`](rules/AGENTS.minimal-diffs.md) into your `AGENTS.md` or `CLAUDE.md`.
3. **Apply targeted fixes:** Pick the category you need from the topic index below.

## 1-Command Local Audit (Python 3 stdlib, read-only)

Run directly against any repository (`exit 0` when clean, `1` when findings exist; supports `--json` for CI):

```bash
curl -fsSL https://raw.githubusercontent.com/seankwon816/ai-coding-agent-tips/main/scripts/audit_agent_configs.py | python3 - .
```

Or run from a local clone:

```bash
python3 scripts/audit_agent_configs.py .
```

<details>
<summary>What the auditor checks (21 built-in rules)</summary>

- **Secrets & leak hygiene**: inline API keys/tokens in `.claude/settings*.json` and `.mcp.json` (redacted in output), `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` set inside `.claude/settings*.json` env blocks, missing `.claude/` in `.gitignore`, Dockerfile `COPY/ADD . .` without `.dockerignore` exclusions.
- **Sandbox & approval gates**: `permissions.defaultMode: "bypassPermissions"`, blanket `permissions.allow` wildcards (`*`, `Bash(*)`, `WebFetch(*)`, `mcp__*`), `sandbox.filesystem.denyRead` not mirrored in `permissions.deny`, missing `allowUnsandboxedCommands: false`, broad `sandbox.excludedCommands`.
- **MCP server safety**: `enableAllProjectMcpServers: true`, `0.0.0.0` wildcard bindings, unpinned `npx -y` packages without `@version`, wildcard `Skill(mcp__*)` allows, and MCP skill denials without `ReadMcpResourceTool` gating.
- **Hooks, context & prompt hygiene**: blocking hooks using non-blocking `exit 1` instead of `exit 2`, out-of-range `autoCompactWindow` settings, invalid/overridden `promptCacheTtl` or `DISABLE_PROMPT_CACHING` flags, `CLAUDE.local.md` shadowing `AGENTS.md` without `@AGENTS.md`, codebase-ownership phrasing that triggers unrequested refactors.

</details>

<details>
<summary>Example output (4 findings)</summary>

```text
[FAIL] Audited /path/to/your-project (4 finding(s))
  - [HIGH] MCP_AUTO_APPROVE_ALL_PROJECT_SERVERS (.claude/settings.local.json): .claude/settings.local.json sets enableAllProjectMcpServers=true, auto-approving every server in .mcp.json without prompting to inspect tools/list.
    Fix: Set enableAllProjectMcpServers to false (or remove it) and list vetted server names explicitly under enabledMcpjsonServers.
  - [HIGH] CLAUDE_LOCAL_INLINE_SECRET (.claude/settings.local.json): Found 2 inline credential pattern(s) (OpenAI/API key, Bearer/Authorization header; e.g. sk-p...abcd [REDACTED], Bear...abcd [REDACTED]).
    Fix: Run /permissions in Claude Code, remove literal secret allow rules, and pass $ENV_VAR names instead.
  - [HIGH] UNIGNORED_CLAUDE_LOCAL_SETTINGS (.gitignore): .claude/ exists without a .gitignore exclusion; future Option 2 rules can be committed by git add .
    Fix: Add '.claude/settings.local.json' (or '.claude/') to .gitignore before staging changes.
  - [MEDIUM] MCP_UNPINNED_NPX (.mcp.json): .mcp.json server 'docs' launches '@modelcontextprotocol/server-filesystem' via npx -y without a pinned @version.
    Fix: Pin exact package versions (pkg@1.2.3) or isolate sessions with managed-mcp.json and --strict-mcp-config.
```

</details>

## Drop-In Starter Rules

- **[rules/AGENTS.minimal-diffs.md](rules/AGENTS.minimal-diffs.md)**: Ready-to-paste `AGENTS.md` / `CLAUDE.md` rules for surgical diffs, two-phase commits, `$ENV_VAR` command safety, and ignore hygiene.

## Browse by Topic

| Category | Fixes | Focus |
| --- | --- | --- |
| [Security & Sandboxing](#security--sandboxing) | 7 | Inline secrets, sandbox gaps, prompt-injection gates, container isolation, `.pth` hooks |
| [MCP Servers & Tool Interfaces](#mcp-servers--tool-interfaces) | 8 | Localhost binding, tool poisoning, stdio logs, payload allowlists, schema overhead |
| [Cost, Context & Token Control](#cost-context--token-control) | 8 | Model routing, compaction thresholds, loop caps, memory layering, Markdown cleanup |
| [Workflow, Git & Prompt Hygiene](#workflow-git--prompt-hygiene) | 8 | `AGENTS.md` precedence, minimal diffs, two-phase commits, Stop hooks, PR proof gates |

## Verified Field Fixes (31)

### Security & Sandboxing

| Area | Fix | What it solves |
|---|---|---|
| Claude Code / Docker | [Inline API keys written by "Yes, and don't ask again"](tips/claude-local-settings-inline-secrets.md) | 31,088 GitHub secrets and 613 Docker Hub leaks from `.claude/settings.local.json` |
| Claude Code | [Mirror sandbox denyRead rules in permissions.deny and disable unsandboxed retries](tips/sandbox-denyread-and-escape-hatch-lockdown.md) | `sandbox.filesystem.denyRead` blocks bash only, leaving built-in `Read` and unsandboxed retries open |
| Claude Code | [Enforce hard tool and approval gates instead of relying on prompt-injection filters](tips/gate-agent-actions-against-data-only-injection.md) | Prompt-injection detectors look for adversarial instructions inside tool results, not plausible numbers |
| Any agent | [Audit AI email connectors against indirect prompt injection](tips/audit-ai-email-connectors-against-indirect-prompt-injection.md) | Hidden instructions inside emails, calendar invites, or PDFs hijack connected OAuth tools (OWASP LLM01, CVE-2026-24301) |
| Any agent | [Isolate coding-agent containers with --network none, --read-only, and seccomp](tips/isolate-agent-containers-network-seccomp-imds.md) | Local model weights do not isolate shell commands from host files, cloud metadata (`169.254.169.254`), or outbound exfiltration |
| Python / Security | [Audit site-packages .pth startup hooks in coding-agent Python environments](tips/audit-python-pth-startup-hooks.md) | Compromised Python wheels (`agent-framework` 1.26.1/1.26.2) harvest keys via `.pth` hooks even without import |
| Claude Code | [Verify AI-generated code with three pre-merge gates](tips/verify-ai-generated-code-with-three-gates.md) | AI coding agents often produce code that compiles cleanly yet ships security defects or quiet structural bloat |

### MCP Servers & Tool Interfaces

| Area | Fix | What it solves |
|---|---|---|
| MCP | [Bind local HTTP servers to 127.0.0.1](tips/mcp-http-bind-localhost.md) | Local MCP servers open to your whole network |
| MCP | [Lock down MCP servers with headersHelper, allowlists, and strict-mcp-config](tips/mcp-lockdown-headershelper-and-strict-config.md) | In MCPTox tests across 45 live MCP servers, hidden rules in tool descriptions reached 72.8% attack success |
| Claude Code / MCP | [Audit MCP tools/list for credential exposure and avoid enableAllProjectMcpServers](tips/audit-mcp-tools-list-credential-exposure.md) | Prompt-injection scans miss benign-looking MCP tools that request or touch credentials |
| MCP | [Route all MCP stdio server logs to stderr so stdout carries JSON-RPC only](tips/mcp-stdio-route-logs-to-stderr.md) | Any non-JSON log line printed to `stdout` breaks newline-delimited MCP `stdio` framing |
| MCP | [Batch browser MCP form fills and return DOM deltas to cut replay tokens](tips/browser-mcp-batched-dom-deltas.md) | Multi-turn browser MCP form fills replay full ARIA trees each step, reaching 72,614 cumulative tokens |
| MCP | [Trim agent tool results to a 5-field allowlist to raise solve rate and cut token spend](tips/trim-agent-tool-results-field-allowlist.md) | Raw REST or MCP list JSON payloads flood context with URLs, avatars, and nested metadata |
| MCP | [Cut MCP tool overhead by 85% with three setup rules](tips/cut-mcp-tool-overhead-with-three-rules.md) | Loading 5+ MCP servers globally injects ~72K-77K schema tokens upfront and drops tool selection accuracy to 49% |
| Claude Code | [Gate both MCP skill loads and ReadMcpResourceTool for remote servers](tips/gate-mcp-skills-and-resources-read.md) | Denying MCP skills leaves raw `resources/read` open, and SEP-2640 SHA-256 digests are unsigned |

### Cost, Context & Token Control

| Area | Fix | What it solves |
|---|---|---|
| Claude Code | [Run the Explore subagent on Haiku](tips/explore-subagent-on-haiku.md) | Codebase searches running on your biggest model |
| Claude Code | [Cap 1M auto-compaction earlier when long sessions drive up token spend](tips/cap-1m-auto-compact-window.md) | On 1M-window models, waiting until ~967K tokens to compact pushes two thirds of spend into the tail |
| Claude Code | [Bound headless agent loops with --max-turns and --max-budget-usd](tips/cap-headless-runs-with-max-turns.md) | Across 27,280 coding agent runs, step count drove inference cost while starting prompt size barely mattered |
| Any agent | [Separate AI project memory with a three-layer setup](tips/separate-ai-project-memory-three-layer-setup.md) | Global AI memory loads into every conversation thread |
| Any agent | [Pack three context blocks instead of polishing prompt wording](tips/pack-three-context-blocks-instead-of-polishing-prompts.md) | Generic or invented answers come from missing facts, examples, and boundaries rather than weak prompt adjectives |
| Claude Code | [Scope ANTHROPIC_API_KEY inline to spend monthly Claude API credits with claude -p](tips/scope-anthropic-api-key-inline-for-monthly-credits.md) | Monthly API credits expire unused while a global `ANTHROPIC_API_KEY` overrides your interactive subscription |
| Any agent | [Cut AI input token bloat by 80% with clean Markdown](tips/convert-raw-html-and-pdfs-to-clean-markdown.md) | Pasting raw HTML web pages or uploading text-heavy PDFs directly into an AI coding agent burns most of your context window on layout noise instead of facts |
| Claude Code | [Pin Claude Code promptCacheTtl to 1h when sessions spill into usage credits](tips/pin-claude-code-prompt-cache-ttl-for-usage-credits.md) | Subscription overage credits and subagents drop Claude Code prompt cache TTL from 1h to 5m, triggering cold uncached rebuilds after short breaks |

### Workflow, Git & Prompt Hygiene

| Area | Fix | What it solves |
|---|---|---|
| Claude Code | [AGENTS.md ignored when CLAUDE.local.md exists](tips/agents-md-ignored-with-claude-local-md.md) | A personal file silently turns off your shared `AGENTS.md` |
| Claude / AGENTS.md | [Prompts claiming codebase ownership cause unrequested refactors](tips/codebase-ownership-causes-unrequested-refactors.md) | Ownership prompts raise unrequested code consolidation from under 10% to about 75% |
| Any agent | [Surgical changes rule](tips/surgical-changes-rule.md) | 3-line fixes that come back as 300-line diffs |
| Any agent | [Split coding-agent commits into prep and logic phases](tips/split-agent-commits-two-phases.md) | Oversized agent diffs that mix renames and formatting into feature logic |
| Claude Code | [.worktreeinclude and worktree.baseRef](tips/worktreeinclude-and-baseref.md) | New worktrees with no `.env` that start from `main` |
| Claude Code | [Block unfinished agent edits with Stop hook exit code 2 before PR review](tips/stop-hook-exit-2-pre-review-gates.md) | AI coding PRs are 154% larger and carry up to 2.74x more security flaws, stalling human code review |
| Any agent | [Put a deterministic fail-before-fix proof gate ahead of human PR review](tips/deterministic-pr-proof-gates-review-bottlenecks.md) | 655-firm and 500k-dev studies show code review stalls and releases lag when vacuous agent PRs pass green CI |
| Any agent | [Real AI agent vs. workflow: the 3-check architecture test](tips/real-ai-agent-vs-workflow-three-check-test.md) | Labeling a multi-step prompt chain an "agent" ships unpredictable loops where a fixed workflow is faster and safer |

_Last checked: 2026-11-27_

## How each tip is written

- One concrete problem, one copy-pasteable fix, and a link to the exact official doc or study lines that prove it.
- Automated verification ([contributing guide](CONTRIBUTING.md)) checks quote accuracy, rule count sync, table formatting, and auditor tests on every commit.

## Running tests

```bash
python3 -m unittest discover -s tests -v
```

## Community

Questions, edge cases, or new tip ideas: open a [GitHub Discussion](https://github.com/seankwon816/ai-coding-agent-tips/discussions), file an [Issue](https://github.com/seankwon816/ai-coding-agent-tips/issues), or join the [Discord community](https://discord.gg/v5KFPkn4ux).

## License

MIT
