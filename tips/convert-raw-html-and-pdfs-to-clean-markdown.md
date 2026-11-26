# Cut AI input token bloat by 80% with clean Markdown

**Checked on:** Cloudflare Blog (Feb 12, 2026), Anthropic Claude Platform PDF Support Docs, and Anthropic Engineering (Sep 2025), 2026-11-26

## What goes wrong

Pasting raw HTML web pages or uploading text-heavy PDFs directly into an AI coding agent burns most of your context window on layout noise instead of facts.

In Cloudflare's Markdown for Agents benchmark, the exact same web page consumed 16,180 tokens in raw HTML versus 3,150 tokens in Markdown (an 80% reduction, 5.1x density). Even a single HTML heading (`<h2 class="section-title" id="about">About Us</h2>`) burned 12 to 15 tokens compared to roughly 3 tokens for `## About Us`.

Uploading text PDFs adds a second hidden tax. Anthropic's Claude Platform PDF Support docs note that every PDF page consumes 1,500 to 3,000 text tokens plus up to 1,568 visual image tokens because each page is also rendered as an image. As irrelevant tokens accumulate, model recall degrades through context rot.

## Fix

Run this 3-rule input checklist before pasting web pages or uploading documents into an agent session:

```text
3-Rule Markdown Input Checklist & Cleanup Prompt:

1. Convert Text Docs To Clean Markdown (.md)
   - Turn long text PDFs, specs, API docs, and web articles into plain .md files first.
   - Headings, bullet lists, and tables stay intact at a fraction of the token cost
     (Cloudflare: 16,180 HTML tokens -> 3,150 Markdown tokens, -80%).

2. Strip Page Boilerplate Before Pasting
   - Drop navigation menus, cookie banners, footers, CSS classes, and inline scripts.
   - Higher signal-to-noise ratio slows context rot and keeps recall sharp.

3. Reserve Native PDF Uploads Only For Visuals
   - Keep direct PDF mode only for pages with charts, system diagrams, scanned pages,
     or merged tables where visual layout carries meaning
     (Anthropic PDF docs: 1,500-3,000 text tokens + up to 1,568 image tokens/page).
```

Copy-paste cleanup prompt when converting messy source text into a reusable `.md` reference:

```text
Convert the source below into clean Markdown. Keep all headings, numbers, tables, and facts intact. Strip navigation menus, footers, and boilerplate. Do not summarize.
```

## Source

- https://blog.cloudflare.com/markdown-for-agents/: "This blog post you're reading takes 16,180 tokens in HTML and 3,150 tokens when converted to Markdown. That's a 80% reduction in token usage ... A simple ## About Us on a page in Markdown costs roughly 3 tokens ... burns 12-15"
- https://docs.anthropic.com/en/docs/build-with-claude/pdf-support: "Each page typically uses 1,500 ... 3,000 tokens depending on content density. ... Each page's image uses at most 1,568 visual tokens on every model"
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents: "context rot ... as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases"

---

[All verified fixes & 1-command config auditor](../README.md)
