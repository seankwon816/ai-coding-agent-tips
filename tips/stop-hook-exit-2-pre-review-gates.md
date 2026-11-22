# Block unfinished agent edits with Stop hook exit code 2 before PR review

**Checked on:** Claude Code hooks & best practices docs, Faros AI, CodeRabbit, and DORA reports, 2026-11-17

## What goes wrong

AI coding PRs are 154% larger and carry up to 2.74x more security flaws, stalling human code review. Telemetry from over 10,000 developers across 1,255 teams at Faros AI shows PR review time climbing 91% and bugs per developer rising 9% as batch sizes grow. In CodeRabbit's audit of 470 open-source GitHub PRs, AI-assisted PRs averaged 10.83 issues versus 6.45 for human PRs, and DORA found each 25% rise in AI adoption tracked a 7.2% drop in delivery stability. When teams add a Claude Code hook to check types or tests before review, returning Unix exit code 1 fails open because Claude Code treats exit code 1 without valid JSON as a non-blocking error.

## Fix

Write a failing reproduction test first, block incomplete agent turns in `.claude/settings.json` with a `Stop` hook that exits with code 2 (redirecting compiler output to stderr), and review the final diff in an isolated session with `/code-review`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "pnpm tsc --noEmit 1>&2 || exit 2"
          }
        ]
      }
    ]
  }
}
```

Run local review before opening the PR and scan `.claude/settings*.json` hooks for non-blocking `exit 1` commands:

```text
/code-review
```

```bash
python3 scripts/audit_agent_configs.py .
```

## Source

- https://www.faros.ai/blog/ai-software-engineering: "telemetry from over 10,000 developers across 1,255 teams...merge 98% more pull requests...PR review time increases 91%...9% increase in bugs per developer and a 154% increase in average PR size"
- https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report: "470 open-source GitHub pull requests...10.83 issues per PR...6.45 for human-only PRs...Security issues were up to 2.74"
- https://dora.dev/ai/gen-ai-report/report/: "25% increase in AI adoption is associated with a 1.5% decrease in delivery throughput and a 7.2% decrease in delivery stability."
- https://code.claude.com/docs/en/best-practices: "a `Stop` hook runs your script whenever Claude tries to end its turn, and sends Claude back to work if the script exits with code 2."
- https://code.claude.com/docs/en/hooks: "Exit code 1 without valid JSON output is a non-blocking error unless the hook is one whose failure blocks the action, even though 1 is the conventional Unix failure code. If your hook is meant to enforce a policy, use `exit 2`."
- https://code.claude.com/docs/en/code-review-local: "Run `/code-review` in a Claude Code session to find bugs in your branch's changes"

---

[All verified fixes & 1-command config auditor](../README.md)
