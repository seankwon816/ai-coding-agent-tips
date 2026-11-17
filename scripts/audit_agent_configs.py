#!/usr/bin/env python3
"""Zero-dependency local auditor for AI coding agent config and secret-leak hazards.

Checks local project configuration files (read-only) for:
1. Inline API secrets written into .claude/settings.local.json or .claude/settings.json
2. Missing .claude/ exclusions in .gitignore when local Claude settings exist
3. Dockerfile COPY . . / ADD . . builds lacking .claude/ exclusions in .dockerignore
4. CLAUDE.local.md silently shadowing a shared AGENTS.md without @AGENTS.md
5. Codebase-ownership prompts in CLAUDE.md/AGENTS.md and 0.0.0.0 HTTP binds in .mcp.json

Usage:
  python3 scripts/audit_agent_configs.py [PATH] [--json]
  curl -fsSL https://raw.githubusercontent.com/seankwon816/ai-coding-agent-tips/main/scripts/audit_agent_configs.py | python3 - .
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Iterable

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OpenAI/API key", re.compile(r"\bsk-[A-Za-z0-9_-]{12,}")),
    ("GitHub classic token", re.compile(r"\bghp_[A-Za-z0-9]{16,}")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{16,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{12,}")),
    ("Slack bot token", re.compile(r"\bxoxb-[0-9A-Za-z-]+")),
    ("Bearer/Authorization header", re.compile(r"\b(?:Bearer|Authorization:?)\s+[A-Za-z0-9._-]{12,}", re.I)),
    (
        "Inline key/token header or env",
        re.compile(
            r"(?:\b[A-Z0-9_]*(?:API[-_]?KEY|TOKEN|SECRET|PASSWORD)\b|X-[A-Z0-9-]*KEY)\s*[:=]\s*['\"]?(?!\$)[A-Za-z0-9._-]{10,}",
            re.I,
        ),
    ),
    ("URL with embedded credentials", re.compile(r"https?://[^/\s:@]+:[^/\s@]+@[^\s]+")),
)

OWNERSHIP_RE = re.compile(
    r"\b(?:owner\s+and\s+long-term\s+maintainer|you\s+own\s+this\s+codebase|long-term\s+maintainer\s+of\s+this\s+codebase)\b",
    re.I,
)
DOCKER_COPY_DOT_RE = re.compile(r"(?im)^\s*(?:COPY|ADD)(?:\s+--[^\s=]+=\S+)*\s+\.(?:\s|$)")


@dataclass
class Finding:
    code: str
    severity: str
    file: str
    summary: str
    fix: str


def redact_match(raw: str) -> str:
    cleaned = raw.strip()
    if len(cleaned) <= 8:
        return "[REDACTED]"
    return f"{cleaned[:4]}...{cleaned[-4:]} [REDACTED]"


def _collect_strings(obj: object) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for item in obj:
            yield from _collect_strings(item)
    elif isinstance(obj, dict):
        for val in obj.values():
            yield from _collect_strings(val)


def _ignore_covers_claude(ignore_path: Path) -> bool:
    if not ignore_path.is_file():
        return False
    for raw in ignore_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.split("#", 1)[0].strip().lstrip("/")
        if not line or line.startswith("!"):
            continue
        norm = line.rstrip("/")
        if norm in {
            ".claude",
            ".claude/*",
            ".claude/**",
            ".claude/settings.local.json",
            "**/.claude",
            "**/.claude/*",
            "**/.claude/**",
            "**/.claude/settings.local.json",
            "settings.local.json",
            "**/settings.local.json",
            "*.local.json",
        }:
            return True
    return False


def _iter_dockerfiles(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file() and (path.name == "Dockerfile" or path.name.startswith("Dockerfile.")):
            yield path


def _check_claude_settings(root: Path, findings: list[Finding]) -> None:
    for rel in (".claude/settings.local.json", ".claude/settings.json"):
        cfg_path = root / rel
        if not cfg_path.is_file():
            continue
        raw_text = cfg_path.read_text(encoding="utf-8", errors="ignore")
        strings_to_scan: list[str]
        try:
            parsed = json.loads(raw_text)
            perms = parsed.get("permissions") if isinstance(parsed, dict) else None
            if isinstance(perms, dict) and "allow" in perms:
                strings_to_scan = list(_collect_strings(perms.get("allow")))
            else:
                strings_to_scan = list(_collect_strings(parsed))
        except Exception:
            strings_to_scan = raw_text.splitlines()

        hit_labels: list[str] = []
        redacted_examples: list[str] = []
        for rule_str in strings_to_scan:
            for label, rx in SECRET_PATTERNS:
                m = rx.search(rule_str)
                if m:
                    hit_labels.append(label)
                    redacted_examples.append(redact_match(m.group(0)))
        if hit_labels:
            uniq_labels = ", ".join(dict.fromkeys(hit_labels))
            uniq_samples = ", ".join(dict.fromkeys(redacted_examples[:3]))
            findings.append(
                Finding(
                    code="CLAUDE_LOCAL_INLINE_SECRET",
                    severity="HIGH",
                    file=rel,
                    summary=f"Found {len(hit_labels)} inline credential pattern(s) ({uniq_labels}; e.g. {uniq_samples}).",
                    fix="Run /permissions in Claude Code, remove literal secret allow rules, and pass $ENV_VAR names instead.",
                )
            )


def _check_ignore_files(root: Path, findings: list[Finding]) -> None:
    claude_dir = root / ".claude"
    local_settings = claude_dir / "settings.local.json"
    if (claude_dir.is_dir() or local_settings.is_file()) and not _ignore_covers_claude(root / ".gitignore"):
        findings.append(
            Finding(
                code="UNIGNORED_CLAUDE_LOCAL_SETTINGS",
                severity="HIGH",
                file=".gitignore",
                summary=".claude/ exists without a .gitignore exclusion; future Option 2 rules can be committed by git add .",
                fix="Add '.claude/settings.local.json' (or '.claude/') to .gitignore before staging changes.",
            )
        )

    dockerignore_ok = _ignore_covers_claude(root / ".dockerignore")
    for df in sorted(_iter_dockerfiles(root)):
        df_text = df.read_text(encoding="utf-8", errors="ignore")
        if DOCKER_COPY_DOT_RE.search(df_text) and not dockerignore_ok:
            rel_df = str(df.relative_to(root))
            findings.append(
                Finding(
                    code="DOCKER_COPY_EXPOSES_CLAUDE_SETTINGS",
                    severity="HIGH",
                    file=rel_df,
                    summary=f"{rel_df} copies the working tree (COPY/ADD . .) while .dockerignore misses .claude exclusions.",
                    fix="Add '.claude/' and '.claude/settings.local.json' to .dockerignore.",
                )
            )


def _check_prompt_and_mcp_files(root: Path, findings: list[Finding]) -> None:
    local_md = root / "CLAUDE.local.md"
    agents_md = root / "AGENTS.md"
    if local_md.is_file() and agents_md.is_file():
        local_txt = local_md.read_text(encoding="utf-8", errors="ignore")
        if "@AGENTS.md" not in local_txt:
            findings.append(
                Finding(
                    code="CLAUDE_LOCAL_SHADOWS_AGENTS_MD",
                    severity="MEDIUM",
                    file="CLAUDE.local.md",
                    summary="CLAUDE.local.md exists alongside AGENTS.md without an @AGENTS.md import.",
                    fix="Add '@AGENTS.md' at the top of CLAUDE.local.md so shared repo instructions stay loaded.",
                )
            )

    for rel in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md"):
        fp = root / rel
        if not fp.is_file():
            continue
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        m = OWNERSHIP_RE.search(txt)
        if m:
            findings.append(
                Finding(
                    code="OWNERSHIP_PROMPT_BLOAT",
                    severity="MEDIUM",
                    file=rel,
                    summary=f"Contains codebase-ownership phrasing ('{m.group(0)}'), which can trigger unrequested refactors.",
                    fix="Remove codebase ownership phrasing and instruct scoped changes only.",
                )
            )

    for rel in (".mcp.json", "mcp.json"):
        fp = root / rel
        if not fp.is_file():
            continue
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        if "0.0.0.0" in txt:
            findings.append(
                Finding(
                    code="MCP_WILDCARD_BIND",
                    severity="HIGH",
                    file=rel,
                    summary=f"{rel} references wildcard address 0.0.0.0 instead of loopback.",
                    fix="Bind local HTTP MCP servers strictly to 127.0.0.1 and validate Origin headers.",
                )
            )


def audit_directory(target: Path | str) -> dict[str, object]:
    """Run all read-only config and security checks against target directory."""
    root = Path(target).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Directory not found: {root}")
    findings: list[Finding] = []
    _check_claude_settings(root, findings)
    _check_ignore_files(root, findings)
    _check_prompt_and_mcp_files(root, findings)
    return {
        "target": str(root),
        "status": "FAIL" if findings else "PASS",
        "finding_count": len(findings),
        "findings": [asdict(f) for f in findings],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Audit local AI coding agent configs for leak and bloat risks.")
    ap.add_argument("path", nargs="?", default=".", help="Project root directory to scan (default: .)")
    ap.add_argument("--json", action="store_true", help="Emit JSON output")
    args = ap.parse_args(argv)

    result = audit_directory(args.path)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[{result['status']}] Audited {result['target']} ({result['finding_count']} finding(s))")
        for f in result["findings"]:  # type: ignore[index]
            print(f"  - [{f['severity']}] {f['code']} ({f['file']}): {f['summary']}")
            print(f"    Fix: {f['fix']}")
    return 1 if result["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
