# Verify AI-generated code with three pre-merge gates

**Checked on:** Veracode 2025 GenAI Code Security Report (Jul 2025), GitClear 2025 AI Copilot Code Quality Report (Feb 2025), and Anthropic Claude Code Best Practices Docs, 2026-11-27

## What goes wrong

AI coding agents often produce code that compiles cleanly yet ships security defects or quiet structural bloat. In Veracode's evaluation of 100+ LLMs across 80 coding tasks, 45% of AI-generated code samples failed security tests and introduced known OWASP Top 10 vulnerabilities (Java 72%, C# 45%, JavaScript 43%, Python 38%), with cross-site scripting (CWE-80) defenses failing in 86% of relevant samples.

Quality drift compounds alongside security gaps. GitClear's analysis of 211 million changed lines (2020 through 2024) found a spike in duplicated code blocks, higher short-term churn, and declining code reuse. Polite reminders inside a prompt ("please run tests before finishing") get skipped under long context once output looks plausible.

## Fix

Enforce three deterministic gates before merging any AI-authored diff:

```text
3-Gate AI Code Verification Scorecard:

1. Lock Failing Tests First (TDD)
   - Prompt: "Write unit and edge-case tests for [expected inputs/outputs + error paths]
     first. Run the suite and confirm they fail. Do not write implementation code yet."
   - Commit the failing test files, then forbid the agent from editing them while
     implementing the fix.

2. Enforce Deterministic Exit-Code Hooks
   - Wire unit tests, typecheck, linter, and static security scanning (SAST) into a
     pre-commit or agent stop hook so any non-zero exit code blocks completion.
   - Replace prose reminders in instruction files with enforced shell checks.

3. Audit Every Diff in a Fresh Session
   - Open a clean session that did not write the code and inspect git diff for
     OWASP Top 10 risks (XSS, injection, auth bypass), duplicated blocks, and
     overfitted tests.
   - Require exact command stdout proof before approving ("All tests pass" alone
     is not evidence).
```

## Source

- https://www.veracode.com/blog/genai-code-security-report/: "45% of code samples failed security tests and introduced OWASP Top 10 security vulnerabilities into the code. ... Java was the riskiest language, with a 72% security failure rate across tasks. ... Python: 38% JavaScript: 43% C#: 45% ... AI tools failed to defend against it in 86 % of relevant code samples."
- https://www.gitclear.com/ai_assistant_code_quality_2025_research: "211 million changed lines of code, authored between January 2020 and December 2024 ... we observe a spike in the prevalence of duplicate code blocks, along with increases in short-term churn code, and the continued decline of moved lines (code reuse)."
- https://code.claude.com/docs/en/best-practices: "write a failing test that reproduces it, then fix it ... that's a job for a stop hook. A line like always typecheck before you finish in this file works most of the time, not every time. ... A second session is also the easiest independent reviewer you can get."

---

[All verified fixes & 1-command config auditor](../README.md)
