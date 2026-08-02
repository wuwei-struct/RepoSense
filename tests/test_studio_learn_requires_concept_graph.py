import unittest
from reposense.studio.review_pipeline import PipelineContext, build_review_pipeline


class StudioLearnRequiresConceptGraphTest(unittest.TestCase):
    def test_learn_always_has_concept_graph(self):
        context = PipelineContext(
            "full_review", "python", "repo", "run", "rules", "budget", "specs", "gate"
        )
        final_stage = next(
            stage for stage in build_review_pipeline(context) if stage.step_id == "finalizing"
        )
        learn_cmd = next(command for label, command in final_stage.commands if label == "Learn site")
        self.assertIn("--concept-graph", learn_cmd)
        cg_idx = learn_cmd.index("--concept-graph") + 1
        cg_path = learn_cmd[cg_idx]
        self.assertTrue(cg_path.endswith("concepts.json"))
        self.assertNotIn("--specs", learn_cmd)


if __name__ == "__main__":
    unittest.main()
