import unittest

from reposense.studio.analysis_profiles import list_public_analysis_profiles
from reposense.studio.pipeline_status import build_pipeline_steps, transition_pipeline_step
from reposense.studio.public_run_payload import (
    build_public_run_payload,
    find_local_path_leaks,
)


class StudioWorkbenchPrivacyTest(unittest.TestCase):
    def test_profile_and_pipeline_payloads_do_not_leak_paths(self):
        steps = transition_pipeline_step(
            build_pipeline_steps(),
            "preparing",
            "failed",
            "/home/alice/private/repository",
            now=1,
        )
        payload = build_public_run_payload({
            "run_id": "run-1",
            "status": "failed",
            "phase": "preparing",
            "repo_label": "repository",
            "profile": list_public_analysis_profiles()[0],
            "pipeline": {
                "profile_id": "full_review",
                "steps": steps,
            },
            "log_path": r"C:\Users\alice\logs.txt",
            "workspace_path": r"\\server\share\studio",
        })
        self.assertEqual(find_local_path_leaks(payload), [])
        self.assertNotIn("log_path", payload)
        self.assertNotIn("workspace_path", payload)

    def test_safe_artifact_urls_remain_allowed(self):
        payload = build_public_run_payload({
            "run_id": "run-1",
            "artifact_groups": [{
                "artifacts": [{
                    "relative_path": "context_pack/REVIEW/README.md",
                    "url": "/runs/run-1/context_pack/REVIEW/README.md",
                }],
            }],
        })
        self.assertEqual(find_local_path_leaks(payload), [])
        self.assertEqual(
            payload["artifact_groups"][0]["artifacts"][0]["url"],
            "/runs/run-1/context_pack/REVIEW/README.md",
        )


if __name__ == "__main__":
    unittest.main()
