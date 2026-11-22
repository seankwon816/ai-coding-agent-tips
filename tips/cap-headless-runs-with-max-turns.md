# Bound headless agent loops with --max-turns and --max-budget-usd

**Checked on:** FrontierHarness Eval v1.1 and Claude Code CLI reference, 2026-11-18

## What goes wrong

Across 27,280 coding agent runs, step count drove inference cost while starting prompt size barely mattered. In FrontierHarness Eval v1.1 (22 harnesses, 5 models, 62 tasks, 83B tokens), steps per pass correlated with cost per pass at +0.51 (p = 0.015), whereas start tokens, tool count, and cache hit rate landed between -0.03 and +0.02 (p >= 0.88). Non-passing trials took 64.5% of scored list-price spend (52.7% failures and 11.8% timeouts), and 68% to 82% of failed runs ended with a confident final answer.

## Fix

Stop optimizing a few hundred tokens out of initial prompts. Bound non-interactive loop depth and spend explicitly with `--max-turns` and `--max-budget-usd`, and pair the run with a deterministic `Stop` hook verification gate:

```bash
claude -p --max-turns 10 --max-budget-usd 5.00 "Fix the failing auth test and run pytest"
```

## Source

- https://runta.com/blog/introducing-frontierharness-eval-v1-1/: "We partnered with Baseten to build the largest-scale harness leaderboard using 83B tokens across 27,280 agent runs...Over the 22 harnesses, the rank correlation of the steps per pass and the cost per pass was +0.51 (p = 0.015). For the other three factors, it was −0.03 to +0.02 (p ≥ 0.88)...64.5% of the list-price cost of the scored runs went to trials that did not pass...68% to 82% of the failed runs ended with a confident final answer"
- https://code.claude.com/docs/en/cli-reference: "Limit the number of agentic turns (print mode only). No limit by default...Stop the run once estimated spend on API calls reaches this amount (print mode only)."

---

[All verified fixes & 1-command config auditor](../README.md)
