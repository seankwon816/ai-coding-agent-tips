# Trim agent tool results to a 5-field allowlist to raise solve rate and cut token spend

**Checked on:** 24-job issue-triage tool-projection benchmark, 2026-11-21

## What goes wrong

Returning raw REST or MCP JSON payloads from list tools floods the agent's context with URLs, avatar objects, reaction counters, and full markdown bodies. Long noisy payloads do not just inflate token bills; they pull the model toward the loudest unrelated item in the list and trigger retry loops.

In a 24-job A/B issue-triage benchmark, giving the model full issue JSON solved 9 of 24 jobs (37.5%) and averaged 1,421 tokens per turn (5,475 tokens per job), looping up to 6 turns on failed runs. Trimming each list result to 5 fields (`number`, `title`, `labels`, comment count, and the first 300 characters of `body`) solved 17 of 24 jobs (70.8%), finished every job within 3 turns, and cut average spend to 673 tokens per turn (2,020 tokens per job).

## Fix

Project list-tool responses through an explicit field allowlist and character cap before returning them to the model. Keep a separate single-item fetch tool for when the agent actually needs a full record.

Python wrapper for an issue or ticket list tool:

```python
from typing import Any

MAX_BODY_CHARS = 300


def project_issue(item: dict[str, Any]) -> dict[str, Any]:
    body = (item.get("body") or "").strip()
    return {
        "number": item.get("number"),
        "title": item.get("title"),
        "labels": [lb["name"] for lb in (item.get("labels") or []) if isinstance(lb, dict) and "name" in lb],
        "comments": item.get("comments", 0),
        "body_preview": body[:MAX_BODY_CHARS],
    }


def list_issues_compact(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [project_issue(item) for item in raw_items]
```

TypeScript equivalent for an MCP tool handler:

```ts
type CompactIssue = {
  number: number;
  title: string;
  labels: string[];
  comments: number;
  bodyPreview: string;
};

export function projectIssues(items: any[]): CompactIssue[] {
  return items.map((item) => ({
    number: item.number,
    title: item.title,
    labels: (item.labels ?? []).map((l: { name: string }) => l.name),
    comments: item.comments ?? 0,
    bodyPreview: String(item.body ?? "").trim().slice(0, 300),
  }));
}
```

## Source

- https://dev.to/aheadkit/i-trimmed-my-agents-tool-results-to-five-fields-it-solved-more-not-fewer-27d5: "Across both runs, the full results solved 9 of 24 jobs. The trimmed results solved 17 of 24. That is 37.5 percent against 70.8"
- https://dev.to/aheadkit/i-trimmed-my-agents-tool-results-to-five-fields-it-solved-more-not-fewer-27d5: "The trimmed arm never needed a fourth turn on any job. Every job ended in three: list, one second look, answer."
- https://dev.to/aheadkit/i-trimmed-my-agents-tool-results-to-five-fields-it-solved-more-not-fewer-27d5: "The average across the run is 1,421 tokens per turn against 673, and 5,475 per job against 2,020."
