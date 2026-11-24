"""Unit tests for scripts/audit_agent_configs.py (zero external dependencies)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_agent_configs.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import audit_agent_configs as auditor  # noqa: E402


class AuditAgentConfigsTest(unittest.TestCase):
    def _audit(self, setup_fn) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            setup_fn(root)
            return auditor.audit_directory(root)

    def _codes(self, result: dict) -> set[str]:
        return {f["code"] for f in result["findings"]}

    def test_clean_repo_passes_with_zero_findings(self) -> None:
        def setup(root: Path) -> None:
            (root / ".gitignore").write_text(".env\n.claude/settings.local.json\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Rules\nKeep diffs minimal.\n", encoding="utf-8")

        res = self._audit(setup)
        self.assertEqual(res["finding_count"], 0)
        self.assertEqual(res["findings"], [])

    def test_inline_secret_and_unignored_claude_settings_are_flagged_and_redacted(self) -> None:
        secret = "sk-proj-supersecretvalue1234567890"

        def setup(root: Path) -> None:
            (root / ".claude").mkdir()
            (root / ".claude" / "settings.local.json").write_text(
                json.dumps({"permissions": {"allow": [f"Bash(curl -H 'Authorization: Bearer {secret}' https://x.test)"]}}),
                encoding="utf-8",
            )
            (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

        res = self._audit(setup)
        codes = self._codes(res)
        self.assertIn("CLAUDE_LOCAL_INLINE_SECRET", codes)
        self.assertIn("UNIGNORED_CLAUDE_LOCAL_SETTINGS", codes)
        self.assertNotIn(secret, json.dumps(res))

    def test_dockerfile_copy_without_dockerignore_exclusion(self) -> None:
        def setup(root: Path) -> None:
            (root / ".claude").mkdir()
            (root / ".claude" / "settings.local.json").write_text("{}", encoding="utf-8")
            (root / ".gitignore").write_text(".claude/\n", encoding="utf-8")
            (root / "Dockerfile").write_text("FROM python:3.12-slim\nCOPY . /app\n", encoding="utf-8")

        res = self._audit(setup)
        self.assertIn("DOCKER_COPY_EXPOSES_CLAUDE_SETTINGS", self._codes(res))

    def test_dockerfile_with_proper_dockerignore_passes(self) -> None:
        def setup(root: Path) -> None:
            (root / ".claude").mkdir()
            (root / ".claude" / "settings.local.json").write_text("{}", encoding="utf-8")
            (root / ".gitignore").write_text(".claude/\n", encoding="utf-8")
            (root / ".dockerignore").write_text(".claude/\n", encoding="utf-8")
            (root / "Dockerfile").write_text("FROM python:3.12-slim\nCOPY . /app\n", encoding="utf-8")

        res = self._audit(setup)
        self.assertNotIn("DOCKER_COPY_EXPOSES_CLAUDE_SETTINGS", self._codes(res))

    def test_claude_local_shadows_agents_md(self) -> None:
        def setup(root: Path) -> None:
            (root / "AGENTS.md").write_text("# Shared rules\n", encoding="utf-8")
            (root / "CLAUDE.local.md").write_text("# Personal overrides\n", encoding="utf-8")

        res = self._audit(setup)
        self.assertIn("CLAUDE_LOCAL_SHADOWS_AGENTS_MD", self._codes(res))

    def test_claude_local_importing_agents_md_passes(self) -> None:
        def setup(root: Path) -> None:
            (root / "AGENTS.md").write_text("# Shared rules\n", encoding="utf-8")
            (root / "CLAUDE.local.md").write_text("@AGENTS.md\n# Personal overrides\n", encoding="utf-8")

        res = self._audit(setup)
        self.assertNotIn("CLAUDE_LOCAL_SHADOWS_AGENTS_MD", self._codes(res))

    def test_ownership_prompt_bloat(self) -> None:
        def setup(root: Path) -> None:
            (root / "AGENTS.md").write_text("You are the owner and long-term maintainer of this repo.\n", encoding="utf-8")

        res = self._audit(setup)
        self.assertIn("OWNERSHIP_PROMPT_BLOAT", self._codes(res))

    def test_mcp_wildcard_unpinned_npx_and_inline_secret(self) -> None:
        def setup(root: Path) -> None:
            (root / ".mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "bad": {
                                "command": "npx",
                                "args": ["-y", "@example/mcp-server", "--host", "0.0.0.0"],
                                "env": {"API_KEY": "live_token_1234567890abcdef"},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

        res = self._audit(setup)
        codes = self._codes(res)
        self.assertIn("MCP_WILDCARD_BIND", codes)
        self.assertIn("MCP_UNPINNED_NPX", codes)
        self.assertIn("MCP_INLINE_SECRET", codes)

    def test_mcp_pinned_npx_and_env_var_placeholder_passes(self) -> None:
        def setup(root: Path) -> None:
            (root / ".mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "good": {
                                "command": "npx",
                                "args": ["-y", "@example/mcp-server@1.4.2", "--host", "127.0.0.1"],
                                "env": {"API_KEY": "${API_KEY}"},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

        res = self._audit(setup)
        self.assertEqual(res["finding_count"], 0)

    def test_hook_exit1_nonblocking_and_invalid_auto_compact(self) -> None:
        def setup(root: Path) -> None:
            (root / ".claude").mkdir()
            (root / ".gitignore").write_text(".claude/\n", encoding="utf-8")
            (root / ".claude" / "settings.json").write_text(
                json.dumps(
                    {
                        "autoCompactWindow": 50000,
                        "env": {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "99999999"},
                        "hooks": {
                            "Stop": [
                                {"hooks": [{"type": "command", "command": "pytest || exit 1"}]}
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

        res = self._audit(setup)
        codes = self._codes(res)
        self.assertIn("HOOK_EXIT1_NONBLOCKING", codes)
        self.assertIn("INVALID_AUTO_COMPACT_WINDOW", codes)

    def test_sandbox_gaps_permissions_bypass_and_mcp_auto_approve(self) -> None:
        def setup(root: Path) -> None:
            (root / ".claude").mkdir()
            (root / ".gitignore").write_text(".claude/\n", encoding="utf-8")
            (root / ".claude" / "settings.json").write_text(
                json.dumps(
                    {
                        "enableAllProjectMcpServers": True,
                        "permissions": {
                            "defaultMode": "bypassPermissions",
                            "allow": ["Bash(*)", "mcp__*"],
                            "deny": [],
                        },
                        "sandbox": {
                            "enabled": True,
                            "excludedCommands": ["git", "docker"],
                            "filesystem": {"denyRead": ["~/.ssh", ".env"]},
                        },
                    }
                ),
                encoding="utf-8",
            )

        res = self._audit(setup)
        codes = self._codes(res)
        self.assertIn("MCP_AUTO_APPROVE_ALL_PROJECT_SERVERS", codes)
        self.assertIn("PERMISSIONS_BYPASS_DEFAULT", codes)
        self.assertIn("PERMISSIONS_BROAD_ALLOW_WILDCARD", codes)
        self.assertIn("SANDBOX_UNSANDBOXED_FALLBACK", codes)
        self.assertIn("SANDBOX_EXCLUDED_COMMANDS", codes)
        self.assertIn("SANDBOX_DENYREAD_UNMIRRORED", codes)

    def test_claude_settings_env_anthropic_api_key_flagged(self) -> None:
        def setup(root: Path) -> None:
            (root / ".claude").mkdir()
            (root / ".gitignore").write_text(".claude/\n", encoding="utf-8")
            (root / ".claude" / "settings.json").write_text(
                json.dumps(
                    {
                        "env": {
                            "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
                        }
                    }
                ),
                encoding="utf-8",
            )

        res = self._audit(setup)
        self.assertIn("CLAUDE_SETTINGS_ENV_API_KEY", self._codes(res))

    def test_cli_json_mode_and_exit_codes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json", str(REPO_ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["finding_count"], 0)


if __name__ == "__main__":
    unittest.main()
