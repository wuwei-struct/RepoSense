import unittest


class NarrativeUpgradeContextSectionsTest(unittest.TestCase):
    def test_upgrade_context_markers_in_core_docs(self):
        checks = {
            "README.md": ["upgrade-context", "upgrade context", "Context Pack", "AI-assisted", "side-effect"],
            "README.zh-CN.md": ["升级上下文", "副作用", "AI 辅助开发"],
            "docs/positioning/BACKEND_VERIFIER.md": ["Upgrade Context", "AI-assisted", "Context Pack"],
            "docs/context-pack/CONTEXT_PACK_SPEC.md": ["Context Pack as Upgrade Handoff", "AI-assisted upgrade", "side-effect"],
            "docs/FACTS_PATTERNS_INSIGHTS.md": ["Context Pack", "upgrade-ready handoff context"],
        }
        for path, markers in checks.items():
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            for marker in markers:
                self.assertIn(marker, text, f"{path} missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()

