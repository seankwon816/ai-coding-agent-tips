"""Repository hygiene and Markdown integrity tests for ai-coding-agent-tips."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
TIPS_DIR = REPO_ROOT / "tips"

PRODUCT_RE = re.compile(r"\b(?:for[- ]?agent|clev[- ]?agent)\b|foragent\.io|clevagent\.io|foragent-skills", re.I)
SRC_LINE_RE = re.compile(r'^- \S+: ".*"\s*$', re.M)


class RepoIntegrityTest(unittest.TestCase):
    def test_all_tips_are_linked_in_readme_and_count_matches(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        tip_files = sorted(p.name for p in TIPS_DIR.glob("*.md") if not p.name.startswith("_"))
        linked = set(re.findall(r"tips/([a-z0-9\-]+\.md)", readme))
        self.assertEqual(set(tip_files), linked, "README.md tip links must exactly match tips/*.md")

        m_count = re.search(r"(?m)^## Verified Field Fixes \((\d+)\)$", readme)
        self.assertIsNotNone(m_count, "README.md must display total verified tip count")
        self.assertEqual(int(m_count.group(1)), len(tip_files))

    def test_readme_tables_have_no_stray_blank_lines(self) -> None:
        lines = README_PATH.read_text(encoding="utf-8").splitlines()
        for idx in range(1, len(lines) - 1):
            prev_l = lines[idx - 1].strip()
            curr_l = lines[idx].strip()
            next_l = lines[idx + 1].strip()
            if prev_l.startswith("|") and curr_l == "" and next_l.startswith("|"):
                self.fail(f"Blank line breaks Markdown table at README.md line {idx + 1}: {next_l}")

    def test_no_em_or_en_dashes_or_product_mentions(self) -> None:
        paths = [
            README_PATH,
            REPO_ROOT / "CONTRIBUTING.md",
            *sorted((REPO_ROOT / "rules").glob("*.md")),
            *sorted((REPO_ROOT / "scripts").glob("*.py")),
            *sorted(TIPS_DIR.glob("*.md")),
        ]
        for p in paths:
            txt = p.read_text(encoding="utf-8")
            self.assertNotIn("\u2014", txt, f"Em dash found in {p.relative_to(REPO_ROOT)}")
            self.assertNotIn("\u2013", txt, f"En dash found in {p.relative_to(REPO_ROOT)}")
            self.assertIsNone(PRODUCT_RE.search(txt), f"Product mention found in {p.relative_to(REPO_ROOT)}")

    def test_every_tip_has_required_sections_sources_and_backlink(self) -> None:
        for p in sorted(TIPS_DIR.glob("*.md")):
            if p.name.startswith("_"):
                continue
            txt = p.read_text(encoding="utf-8")
            self.assertIn("## What goes wrong", txt, f"{p.name} missing '## What goes wrong'")
            self.assertIn("## Fix", txt, f"{p.name} missing '## Fix'")
            self.assertIn("## Source", txt, f"{p.name} missing '## Source'")
            self.assertTrue(SRC_LINE_RE.search(txt), f"{p.name} missing verifiable source quote line")
            self.assertIn("../README.md", txt, f"{p.name} missing backlink to ../README.md")


if __name__ == "__main__":
    unittest.main()
