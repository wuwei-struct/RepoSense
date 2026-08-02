import unittest
from reposense.studio.review_pipeline import PipelineContext, build_review_pipeline


class StudioExportArtifactsTest(unittest.TestCase):
    def test_export_stage_outputs(self):
        context = PipelineContext(
            "full_review", "python", "repo", "run", "rules", "budget", "specs", "gate"
        )
        stages = build_review_pipeline(context)
        context_stage = next(stage for stage in stages if stage.step_id == "building_context_pack")
        final_stage = next(stage for stage in stages if stage.step_id == "finalizing")
        self.assertEqual(context_stage.action, "context_pack")
        self.assertIn("exports/context_pack.zip", context_stage.required_artifacts)
        self.assertIn("exports/report.sarif.json", final_stage.required_artifacts)
        self.assertIn("run_manifest.json", final_stage.required_artifacts)


if __name__ == "__main__":
    unittest.main()
