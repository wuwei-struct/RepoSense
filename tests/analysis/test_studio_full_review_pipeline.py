import os
import tempfile
import unittest

from reposense.studio.review_pipeline import (
    PipelineContext,
    PipelineStageError,
    build_review_pipeline,
    execute_review_pipeline,
)


def _context(root, profile_id="full_review"):
    return PipelineContext(
        profile_id=profile_id,
        python="python",
        repo_path=os.path.join(root, "repo"),
        run_dir=os.path.join(root, "run"),
        ruleset_path=os.path.join(root, "ruleset"),
        budget_path=os.path.join(root, "budget.json"),
        specs_path=os.path.join(root, "specs"),
        gate_path=os.path.join(root, "gate.json"),
    )


class StudioFullReviewPipelineTest(unittest.TestCase):
    def test_full_review_stage_order_and_fixed_argv(self):
        with tempfile.TemporaryDirectory() as td:
            stages = build_review_pipeline(_context(td))
        self.assertEqual([stage.step_id for stage in stages], [
            "preparing", "scanning_facts", "building_event_graph",
            "detecting_patterns", "analyzing_code_health", "reviewing_permissions",
            "correlating_transactions", "reviewing_queue_reliability",
            "building_repository_review", "building_context_pack",
            "strict_verification", "quality_gate", "finalizing",
        ])
        commands = [command for stage in stages for _, command in stage.commands]
        self.assertTrue(commands)
        self.assertTrue(all(isinstance(command, tuple) for command in commands))
        self.assertFalse(any("shell" in token.lower() for command in commands for token in command))
        strict = next(stage for stage in stages if stage.step_id == "strict_verification")
        self.assertIn("run", strict.commands[1][1])
        self.assertIn("--strict", strict.commands[-1][1])

    def test_quick_scan_skips_review_only_stages(self):
        with tempfile.TemporaryDirectory() as td:
            stages = build_review_pipeline(_context(td, "quick_scan"))
        skipped = {stage.step_id for stage in stages if stage.skipped}
        self.assertEqual(skipped, {
            "detecting_patterns",
            "analyzing_code_health",
            "reviewing_permissions",
            "building_repository_review",
        })

    def test_stage_failure_preserves_completed_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            context = _context(td)
            os.makedirs(context.run_dir)
            marker = os.path.join(context.run_dir, "completed-stage.txt")
            updates = []

            def run_command(step_id, _label, _command):
                if step_id == "scanning_facts":
                    with open(marker, "w", encoding="utf-8") as handle:
                        handle.write("preserved")
                    raise RuntimeError("controlled failure")

            with self.assertRaises(PipelineStageError):
                execute_review_pipeline(
                    context,
                    run_command,
                    lambda *args: updates.append(args),
                )
            self.assertTrue(os.path.isfile(marker))
            self.assertEqual(updates[-1][0], "scanning_facts")


if __name__ == "__main__":
    unittest.main()
