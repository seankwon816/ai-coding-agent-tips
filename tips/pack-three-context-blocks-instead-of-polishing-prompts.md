# Pack three context blocks instead of polishing prompt wording

**Checked on:** Anthropic Engineering context engineering guide and Lewis et al. (NeurIPS 2020), 2026-11-23

## What goes wrong

When an AI answer comes back generic or invents details, rewriting prompt adjectives ("act as a world-class expert", "be concise and thorough") rarely fixes the root cause. Models guess whenever exact source facts, concrete formatting examples, and explicit boundaries are missing from the context window.

In NeurIPS 2020 RAG evaluations (Lewis et al.), human evaluators rated source-grounded outputs more factual than parametric-only memory outputs in 42.7% of comparisons vs. 7.1% for memory alone (a 6x gap), while FEVER claim verification rose from 81.1% to 89.5%.

## Fix

Replace vague persona adjectives with a compact three-block context pack:

```text
<source>
Paste only the exact notes, metrics, or policy text needed for this task.
</source>

<examples>
Input: [sample 1] -> Good Output: [real approved output 1]
Input: [sample 2] -> Good Output: [real approved output 2]
</examples>

<rules>
Answer only from <source>. Match the tone and structure of <examples>.
If a required fact is missing, reply "Not in sources." Do not guess.
</rules>
```

Keep each block lean so the model spends its attention budget on high-signal evidence rather than filler instructions:

```text
Before:
"Act as a world-class B2B SaaS analyst. Write a sharp, executive-ready Q3 summary."

After:
<source>Q3 ARR: $4.2M (+18% QoQ). Churn: 2.1%. Top blocker: SSO onboarding delay.</source>
<examples>Q2 Update: ARR hit $3.56M (+14% QoQ); churn held at 2.3%; main risk was API rate limits.</examples>
<rules>Use only numbers in <source>. Keep to 3 bullets max. If a metric is missing, write "Not in sources."</rules>
```

## Source

- https://www.anthropic.com/research/effective-context-engineering-for-ai-agents: "finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome"
- https://arxiv.org/abs/2005.11401: "RAG models generate more specific, diverse and factual language than a state-of-the-art parametric-only seq2seq baseline"
- https://ar5iv.labs.arxiv.org/html/2005.11401: "BART was more factual than RAG in only 7.1% of cases, while RAG was more factual in 42.7% of cases"

---

[All verified fixes & 1-command config auditor](../README.md)
