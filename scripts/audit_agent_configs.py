#!/usr/bin/env python3
"""Zero-dependency local auditor for AI coding agent config and secret-leak hazards.

Checks local project configuration files (read-only) for:
1. Inline API secrets written into .claude/settings.local.json or .claude/settings.json
2. Missing .claude/ exclusions in .gitignore when local Claude settings exist
3. Dockerfile COPY . . / ADD . . builds lacking .claude/ exclusions in .dockerignore
4. CLAUDE.local.md silently shadowing a shared AGENTS.md without @AGENTS.md
5. Codebase-ownership prompts in CLAUDE.md/AGENTS.md and wildcard/inline-secret/unpinned-npx traps in .mcp.json
6. Blocking Claude Code hooks using non-blocking exit 1 or out-of-range autoCompactWindow values
7. Claude Code sandbox gaps: unmirrored filesystem.denyRead paths (bypassed by built-in Read), allowUnsandboxedCommands/excludedCommands escape hatches, and bypassPermissions defaults
8. Blanket wildcard permissions.allow rules (Bash, Bash(*), WebFetch(*), mcp__*, *) that remove action approval gates

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
BLOCKING_HOOK_EVENTS = (
    "PreToolUse",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "TaskCompleted",
    "TaskCreated",
    "TeammateIdle",
    "ConfigChange",
    "ElicitationResult",
)
HOOK_EXIT1_RE = re.compile(r"(?:^|[;&|]\s*|\bthen\s+)exit\s+1\b")
HOOK_EXIT2_RE = re.compile(r"\bexit\s+2\b")
COMPACT_ENV_RE = re.compile(r"^(\d+)([kKmM])?$")
MCP_CREDENTIAL_KEY_RE = re.compile(r"(?:API[-_]?KEY|TOKEN|SECRET|PASSWORD|AUTHORIZATION)$", re.I)
BROAD_ALLOW_WILDCARD_RE = re.compile(
    r"^(?:\*|Bash(?:\((?:\*|\*:\*|:\*)\))?|WebFetch(?:\((?:\*|domain:\*)\))?|mcp__\*+(?:__\*+)?)$"
)
PLACEHOLDER_SECRET_RE = re.compile(r"^(?:\$\{[^}]+\}|\$[A-Z0-9_]+|<[^>]+>|(?:YOUR|REPLACE|EXAMPLE|DUMMY|TEST)[-_A-Z0-9]*|x{4,})$", re.I)


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


def _is_valid_compact_window_num(val: object) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and 100000 <= val <= 1000000


def _is_valid_compact_env(raw: object) -> bool:
    if not isinstance(raw, str):
        return False
    m = COMPACT_ENV_RE.match(raw.strip())
    if not m:
        return False
    tokens = int(m.group(1))
    suffix = (m.group(2) or "").lower()
    if suffix == "k":
        tokens *= 1000
    elif suffix == "m":
        tokens *= 1000000
    return 100000 <= tokens <= 1000000


def _check_claude_hooks(rel: str, parsed: dict[str, object], findings: list[Finding]) -> None:
    hooks = parsed.get("hooks")
    if not isinstance(hooks, dict):
        return
    for event in BLOCKING_HOOK_EVENTS:
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            nested = entry.get("hooks")
            hook_objs = nested if isinstance(nested, list) else ([entry] if "command" in entry else [])
            for hook in hook_objs:
                if not isinstance(hook, dict) or hook.get("type", "command") != "command":
                    continue
                if hook.get("onFailure") == "block":
                    continue
                cmd = hook.get("command")
                if not isinstance(cmd, str):
                    continue
                if HOOK_EXIT1_RE.search(cmd) and not HOOK_EXIT2_RE.search(cmd):
                    findings.append(
                        Finding(
                            code="HOOK_EXIT1_NONBLOCKING",
                            severity="HIGH",
                            file=rel,
                            summary=f"{event} command hook uses 'exit 1' without 'exit 2' or onFailure:'block', so Claude Code treats failures as non-blocking errors.",
                            fix="Replace 'exit 1' with '1>&2 || exit 2' (or set onFailure to 'block') so failing gates stop the action.",
                        )
                    )


def _check_claude_compact_window(rel: str, parsed: dict[str, object], findings: list[Finding]) -> None:
    if "autoCompactWindow" in parsed and not _is_valid_compact_window_num(parsed["autoCompactWindow"]):
        val = parsed["autoCompactWindow"]
        findings.append(
            Finding(
                code="INVALID_AUTO_COMPACT_WINDOW",
                severity="MEDIUM",
                file=rel,
                summary=f"autoCompactWindow={val!r} is outside Claude Code's valid 100000..1000000 token range.",
                fix="Set autoCompactWindow to a token count between 100000 and 1000000 (for example 400000).",
            )
        )
    model_settings = parsed.get("modelSettings")
    if isinstance(model_settings, dict):
        for model_name, cfg in model_settings.items():
            if not isinstance(cfg, dict) or "autoCompactWindow" not in cfg:
                continue
            val = cfg["autoCompactWindow"]
            if val != "auto" and not _is_valid_compact_window_num(val):
                findings.append(
                    Finding(
                        code="INVALID_AUTO_COMPACT_WINDOW",
                        severity="MEDIUM",
                        file=rel,
                        summary=f"modelSettings.{model_name}.autoCompactWindow={val!r} must be 'auto' or 100000..1000000 tokens.",
                        fix="Use 'auto' or an integer token count between 100000 and 1000000.",
                    )
                )
    env_cfg = parsed.get("env")
    if isinstance(env_cfg, dict) and "CLAUDE_CODE_AUTO_COMPACT_WINDOW" in env_cfg:
        raw_env = env_cfg["CLAUDE_CODE_AUTO_COMPACT_WINDOW"]
        if not _is_valid_compact_env(raw_env):
            findings.append(
                Finding(
                    code="INVALID_AUTO_COMPACT_WINDOW",
                    severity="MEDIUM",
                    file=rel,
                    summary=f"env.CLAUDE_CODE_AUTO_COMPACT_WINDOW={raw_env!r} is invalid or outside 100000..1000000 (bare numbers mean raw tokens, not thousands).",
                    fix="Set CLAUDE_CODE_AUTO_COMPACT_WINDOW to '400000' or '400k'.",
                )
            )


def _normalize_deny_path(raw: str) -> str:
    p = raw.strip()
    for suffix in ("/**", "/*", "/"):
        if p.endswith(suffix) and len(p) > len(suffix):
            p = p[: -len(suffix)]
    return p


def _read_deny_covers(read_patterns: list[str], target: str) -> bool:
    norm_target = _normalize_deny_path(target)
    if not norm_target:
        return True
    for pat in read_patterns:
        raw_pat = pat.strip()
        norm_pat = _normalize_deny_path(raw_pat)
        if norm_pat == norm_target:
            return True
        if raw_pat.endswith(("/**", "/*")) and norm_target.startswith(norm_pat + "/"):
            return True
    return False


def _check_claude_sandbox(rel: str, parsed: dict[str, object], findings: list[Finding]) -> None:
    perms = parsed.get("permissions")
    read_deny_patterns: list[str] = []
    if isinstance(perms, dict):
        if perms.get("defaultMode") == "bypassPermissions":
            findings.append(
                Finding(
                    code="PERMISSIONS_BYPASS_DEFAULT",
                    severity="HIGH",
                    file=rel,
                    summary=f"{rel} sets permissions.defaultMode='bypassPermissions', skipping prompts for built-in tools and unsandboxed retries.",
                    fix="Reserve bypassPermissions for ephemeral containers/VMs; locally use sandbox + autoAllowBashIfSandboxed or dontAsk.",
                )
            )
        allow_list = perms.get("allow")
        if isinstance(allow_list, list):
            broad_rules = [
                rule.strip()
                for rule in allow_list
                if isinstance(rule, str) and BROAD_ALLOW_WILDCARD_RE.match(rule.strip())
            ]
            if broad_rules:
                preview = ", ".join(dict.fromkeys(broad_rules[:4]))
                findings.append(
                    Finding(
                        code="PERMISSIONS_BROAD_ALLOW_WILDCARD",
                        severity="HIGH",
                        file=rel,
                        summary=f"{rel} grants blanket permissions.allow wildcard(s) ({preview}), letting untrusted tool data trigger actions without confirmation.",
                        fix="Replace blanket wildcards with scoped permissions.allow entries and enforce permissions.ask or permissions.deny gates for shell, network, and MCP side effects.",
                    )
                )
        deny_list = perms.get("deny")
        if isinstance(deny_list, list):
            for rule in deny_list:
                if isinstance(rule, str):
                    m = re.match(r"^Read\((.+)\)$", rule.strip())
                    if m:
                        read_deny_patterns.append(m.group(1).strip())

    sandbox = parsed.get("sandbox")
    if not isinstance(sandbox, dict):
        return

    if sandbox.get("enabled") is True and sandbox.get("allowUnsandboxedCommands") is not False:
        findings.append(
            Finding(
                code="SANDBOX_UNSANDBOXED_FALLBACK",
                severity="HIGH",
                file=rel,
                summary=f"{rel} enables sandbox without setting allowUnsandboxedCommands: false, allowing blocked commands to retry outside the sandbox.",
                fix="Set sandbox.allowUnsandboxedCommands to false (and failIfUnavailable to true) in managed or user settings.",
            )
        )

    excluded = sandbox.get("excludedCommands")
    if isinstance(excluded, list):
        excl_items = [str(c).strip() for c in excluded if isinstance(c, str) and c.strip()]
        if excl_items:
            preview = ", ".join(excl_items[:4])
            findings.append(
                Finding(
                    code="SANDBOX_EXCLUDED_COMMANDS",
                    severity="MEDIUM",
                    file=rel,
                    summary=f"{rel} lists sandbox.excludedCommands ({preview}), which bypass OS sandbox boundaries completely.",
                    fix="Remove broad entries from sandbox.excludedCommands or lock sandbox policy in managed settings.",
                )
            )

    denied_paths: list[str] = []
    fs_cfg = sandbox.get("filesystem")
    if isinstance(fs_cfg, dict) and isinstance(fs_cfg.get("denyRead"), list):
        for p in fs_cfg["denyRead"]:
            if isinstance(p, str) and p.strip():
                denied_paths.append(p.strip())
    cred_cfg = sandbox.get("credentials")
    if isinstance(cred_cfg, dict) and isinstance(cred_cfg.get("files"), list):
        for item in cred_cfg["files"]:
            if isinstance(item, dict) and item.get("mode") == "deny" and isinstance(item.get("path"), str) and item["path"].strip():
                denied_paths.append(item["path"].strip())

    unmirrored = [p for p in dict.fromkeys(denied_paths) if not _read_deny_covers(read_deny_patterns, p)]
    if unmirrored:
        preview = ", ".join(unmirrored[:4])
        findings.append(
            Finding(
                code="SANDBOX_DENYREAD_UNMIRRORED",
                severity="HIGH",
                file=rel,
                summary=f"{rel} blocks bash reads for {preview} in sandbox config without matching Read(...) rules in permissions.deny (built-in Read runs outside the sandbox).",
                fix="Mirror every sandbox denyRead path in permissions.deny (for example 'Read(~/.ssh/**)' and 'Read(~/.aws/**)').",
            )
        )


def _check_claude_settings(root: Path, findings: list[Finding]) -> None:
    for rel in (".claude/settings.local.json", ".claude/settings.json"):
        cfg_path = root / rel
        if not cfg_path.is_file():
            continue
        raw_text = cfg_path.read_text(encoding="utf-8", errors="ignore")
        parsed: object = None
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

        if isinstance(parsed, dict):
            _check_claude_hooks(rel, parsed, findings)
            _check_claude_compact_window(rel, parsed, findings)
            _check_claude_sandbox(rel, parsed, findings)

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


def _is_pinned_npm_spec(pkg: str) -> bool:
    if pkg.startswith((".", "/", "~", "http://", "https://", "git+", "file:")):
        return True
    if pkg.startswith("@"):
        return "/" in pkg and "@" in pkg.split("/", 1)[1]
    return "@" in pkg


def _check_mcp_file(rel: str, fp: Path, findings: list[Finding]) -> None:
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

    parsed: object = None
    try:
        parsed = json.loads(txt)
        strings_to_scan = list(_collect_strings(parsed))
    except Exception:
        strings_to_scan = txt.splitlines()

    hit_labels: list[str] = []
    redacted_examples: list[str] = []
    matched_secret_vals: set[str] = set()
    for raw_val in strings_to_scan:
        for label, rx in SECRET_PATTERNS:
            m = rx.search(raw_val)
            if m:
                hit_labels.append(label)
                redacted_examples.append(redact_match(m.group(0)))
                matched_secret_vals.add(raw_val.strip())

    servers = parsed.get("mcpServers") if isinstance(parsed, dict) else None
    if isinstance(servers, dict):
        for srv_name, cfg in servers.items():
            if not isinstance(cfg, dict):
                continue
            for block_name in ("env", "headers"):
                block = cfg.get(block_name)
                if not isinstance(block, dict):
                    continue
                for k, v in block.items():
                    if not isinstance(k, str) or not isinstance(v, str):
                        continue
                    v_clean = v.strip()
                    if not v_clean or v_clean in matched_secret_vals:
                        continue
                    if MCP_CREDENTIAL_KEY_RE.search(k.strip()) and not PLACEHOLDER_SECRET_RE.match(v_clean):
                        hit_labels.append(f"{srv_name}.{block_name}.{k}")
                        redacted_examples.append(redact_match(v_clean))

            cmd = str(cfg.get("command") or "").strip()
            cmd_name = Path(cmd).name.lower() if cmd else ""
            args = cfg.get("args")
            if cmd_name in ("npx", "npx.cmd") and isinstance(args, list):
                str_args = [a for a in args if isinstance(a, str)]
                if any(a in ("-y", "--yes") for a in str_args):
                    pkgs = [a for a in str_args if not a.startswith("-")]
                    if pkgs and not _is_pinned_npm_spec(pkgs[0]):
                        findings.append(
                            Finding(
                                code="MCP_UNPINNED_NPX",
                                severity="MEDIUM",
                                file=rel,
                                summary=f"{rel} server '{srv_name}' launches '{pkgs[0]}' via npx -y without a pinned @version.",
                                fix="Pin exact package versions (pkg@1.2.3) or isolate sessions with managed-mcp.json and --strict-mcp-config.",
                            )
                        )

    if hit_labels:
        uniq_labels = ", ".join(dict.fromkeys(hit_labels[:4]))
        uniq_samples = ", ".join(dict.fromkeys(redacted_examples[:3]))
        findings.append(
            Finding(
                code="MCP_INLINE_SECRET",
                severity="HIGH",
                file=rel,
                summary=f"Found {len(hit_labels)} inline credential(s) in {rel} ({uniq_labels}; e.g. {uniq_samples}).",
                fix="Move static tokens out of .mcp.json env/headers into headersHelper scripts or ${ENV_VAR} references.",
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
        if fp.is_file():
            _check_mcp_file(rel, fp, findings)


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
