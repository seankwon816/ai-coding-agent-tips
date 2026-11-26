# Real AI agent vs. workflow: the 3-check architecture test

**Checked on:** Anthropic Engineering (Dec 2024), OpenAI Agents SDK docs (2025), and Gartner Newsroom (June 25, 2025), 2026-11-24

## What goes wrong

Teams often label any multi-step prompt chain an "AI agent" and ship an unpredictable loop where a deterministic workflow would be faster, cheaper, and easier to debug. Gartner (June 25, 2025) estimated only about 130 real agentic AI vendors out of thousands ("agent washing") and predicted over 40% of agentic AI projects will be canceled by the end of 2027 due to escalating costs, unclear business value, or inadequate risk controls.

Anthropic Engineering draws a clear line by runtime control: workflows orchestrate LLMs and tools through predefined code paths, while agents let the model dynamically direct its own tool choices and loop steps until a stop condition fires.

## Fix

Run this 10-second 3-check scorecard before you build or buy:

```text
Workflow vs. True AI Agent 3-Check Matrix:

1. Dynamic Tool Selection
   - Workflow: Fixed code order (Step 1 -> Step 2)
   - Agent: Model decides which tool runs next at runtime

2. Live Error Feedback
   - Workflow: Halts on empty output or HTTP 429 error
   - Agent: Reads the tool error trace, adjusts arguments, and retries

3. Explicit Stop Condition
   - Workflow: Ends at the last hardcoded step
   - Agent: Enforces a verified goal check, max-turn cap, or human handoff
```

Score your design before writing code:

```text
- 0-1 Yes -> Ship a deterministic workflow (faster runs, lower token cost, predictable outputs)
- 2 Yes   -> Add explicit stop guardrails (verified goal, max_turns cap, human handoff) before production
- 3 Yes   -> True AI agent (use only when steps cannot be hardcoded upfront)
```

## Source

- https://www.anthropic.com/research/building-effective-agents: "Workflows are systems where LLMs and tools are orchestrated through predefined code paths."
- https://openai.github.io/openai-agents-python/running_agents/: "If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop. If we exceed the max_turns passed, we raise a MaxTurnsExceeded exception."
- https://web.archive.org/web/20250629125109/https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027: "Gartner estimates only about 130 of the thousands of agentic AI vendors are real. ... Gartner Predicts Over 40% of Agentic AI Projects Will Be Canceled by End of 2027"

---

[All verified fixes & 1-command config auditor](../README.md)
