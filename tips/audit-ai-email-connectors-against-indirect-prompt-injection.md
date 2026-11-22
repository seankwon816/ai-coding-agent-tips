# Audit AI email connectors against indirect prompt injection

**Checked on:** OWASP Top 10 for LLM Applications (LLM01) and NIST NVD CVE-2026-24301, 2026-11-21

## What goes wrong

When you ask an AI assistant to summarize an email, calendar invite, or PDF, the model reads your prompt and the untrusted document inside one shared token stream. Hidden text placed in white-on-white CSS, `0px` HTML spans, or invisible Unicode tag characters looks blank to a human reader, yet the model still parses it as instructions.

If that assistant has live OAuth access to Gmail, Cloud Drive, Calendar, or persistent Saved Memory, concealed instructions inside an external email can steer tool calls or write persistent rules without asking. NIST NVD CVE-2026-24301 (published August 18, 2026, patched by Microsoft in August 2026) documented command injection in Microsoft Copilot allowing unauthorized information disclosure over a network.

## Fix

Treat untrusted external documents as hostile input and run a 30-second connector audit across every AI assistant you use:

```text
30-Second AI Connector Security Audit Checklist

1. Trim unused OAuth connectors
   Open Settings > Connected Apps and disconnect idle Mail, Drive, and Calendar access.

2. Keep manual approval gates enabled
   Require explicit confirmation before sending emails, fetching external URLs, or writing to Saved Memory.

3. Strip hidden formatting before pasting
   Paste untrusted emails or web snippets as plain text (Cmd+Shift+V on Mac, Ctrl+Shift+V on Windows) to drop hidden HTML and 0px CSS.

4. Review Saved Memory monthly
   Inspect your assistant's saved rules and delete any instruction you did not add yourself.
```

To inspect an untrusted clipboard snippet for hidden zero-width or Unicode tag characters before sending it to an AI tool, run a quick local check:

```bash
pbpaste | python3 -c '
import sys, unicodedata
text = sys.stdin.read()
hidden = [
    (i, hex(ord(ch)), unicodedata.name(ch, "UNKNOWN"))
    for i, ch in enumerate(text)
    if unicodedata.category(ch) == "Cf" or 0xE0000 <= ord(ch) <= 0xE007F
]
print(f"hidden_chars={len(hidden)}")
for item in hidden[:10]:
    print(item)
'
```

## Source

- https://genai.owasp.org/llmrisk/llm01-prompt-injection/: "Indirect prompt injections occur when an LLM accepts input from external sources, such as websites or files."
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/: "Restrict the model's access privileges to the minimum necessary for its intended operations."
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/: "Implement human-in-the-loop controls for privileged operations to prevent unauthorized actions."
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/: "Separate and clearly denote untrusted content to limit its influence on user prompts."
- https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-24301: "Improper neutralization of special elements used in a command ('Command Injection') in Microsoft Copilot allows an unauthorized attacker to disclose information over a network."

---

[All verified fixes & 1-command config auditor](../README.md)
