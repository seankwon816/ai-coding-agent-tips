# Put a deterministic fail-before-fix proof gate ahead of human PR review

**Checked on:** Harvard 655-firm telemetry study, NBER w35275, Herbold et al. (arXiv:2610.20394), and ai-fix-verifier benchmarks, 2026-11-19

## What goes wrong

Coding agents raise raw code output far faster than teams can verify and ship it. A Harvard study covering 445M work events for 720,542 workers at 655 firms found that code review becomes the bottleneck: code waits longer to reach a reviewer, spends longer in active review, and receives more requested changes. Separately, an NBER study of more than 500,000 GitHub developers (w35275) measured autonomous coding agents lifting commits by 240%, while actual releases rose only 30%. In a 432-scenario simulation (arXiv:2610.20394), escaped bugs drove total cost and 61% of the optimal agent budget went to finding bugs.

Relying on green CI alone still lets vacuous tests reach human reviewers when an agent writes a test that already passes on the buggy base commit or weakens an existing test to make the suite pass.

## Fix

Require a deterministic pre-review proof gate before assigning human reviewers:

1. Check out the base commit, apply only the PR's new or modified test files, and confirm at least one new test fails on the old code.
2. Check the diff to verify no existing test assertions were weakened or deleted and no public functions were silently removed.
3. Run the full suite on the patched commit and block reviewer assignment until the test flips from fail on base to pass on head.

Minimal local verification command before opening a PR:

```bash
# Confirm the added test fails on the base branch before running it on your fix branch
git worktree add --detach /tmp/pr-base origin/main
cp tests/test_bugfix.py /tmp/pr-base/tests/test_bugfix.py
(cd /tmp/pr-base && pytest tests/test_bugfix.py) && echo "VACUOUS TEST: passed on base!" && exit 1
git worktree remove --force /tmp/pr-base
pytest tests/test_bugfix.py
```

## Source

- https://fion.ac/: "covering 445M work events"
- https://fion.ac/: "for 720,542 workers at 655 firms"
- https://fion.ac/: "Code review becomes the bottleneck. Code waits longer to reach a reviewer, spends longer in active review, and receives more requested changes."
- https://www.nber.org/papers/w35275: "using data on more than 500,000 GitHub developers combined with their AI usage telemetry."
- https://www.nber.org/papers/w35275: "the 240% cumulative effect falls to 80% for the number of projects, and to 30% for actual releases."
- https://arxiv.org/abs/2610.20394: "Escaped bugs are the dominant cost driver, and 61% of the agent budget goes to finding bugs. Agent capability matters more than token price, since higher-quality outputs reduce downstream quality assurance costs."
- https://raw.githubusercontent.com/simplynadaf/ai-fix-verifier/main/README.md: "Deterministic Python decides. No model grades the model"
- https://raw.githubusercontent.com/simplynadaf/ai-fix-verifier/main/README.md: "checks that no test was weakened, no function was deleted, nothing regressed, and that the fix is backed by a test which fails on the old code and passes on the new."

---

[All verified fixes & 1-command config auditor](../README.md)
