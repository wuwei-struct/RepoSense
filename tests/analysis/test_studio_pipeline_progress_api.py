import unittest

from reposense.studio.pipeline_status import (
    build_pipeline_steps,
    build_public_pipeline,
    transition_pipeline_step,
)


class StudioPipelineProgressApiTest(unittest.TestCase):
    def test_progress_contract_tracks_timestamps_and_artifacts(self):
        steps = build_pipeline_steps()
        steps = transition_pipeline_step(
            steps,
            "scanning_facts",
            "running",
            artifact_ids=["main_html_report"],
            now=10,
        )
        steps = transition_pipeline_step(
            steps,
            "scanning_facts",
            "passed",
            artifact_ids=["main_html_report"],
            now=20,
        )
        public = build_public_pipeline({"profile_id": "full_review"}, steps, "scanning_facts")
        step = next(item for item in public["steps"] if item["step_id"] == "scanning_facts")
        self.assertEqual(step["status"], "passed")
        self.assertEqual(step["started_at"], 10)
        self.assertEqual(step["finished_at"], 20)
        self.assertEqual(step["artifact_ids"], ["main_html_report"])

    def test_progress_omits_private_path_messages_and_degrades_malformed_state(self):
        steps = transition_pipeline_step(
            build_pipeline_steps(),
            "preparing",
            "failed",
            r"C:\Users\alice\private\traceback.txt",
            now=1,
        )
        public = build_public_pipeline({"profile_id": "full_review"}, steps, "preparing")
        self.assertEqual(public["steps"][0]["message"], "")
        malformed = build_public_pipeline({}, [{"step_id": "x", "status": "invalid"}], "x")
        self.assertEqual(malformed["steps"][0]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
