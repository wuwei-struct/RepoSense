import unittest

from reposense.studio.public_run_payload import (
    build_public_run_list_item,
    build_public_run_payload,
    find_local_path_leaks,
)


class StudioPublicRunPayloadTest(unittest.TestCase):
    def test_internal_paths_are_not_public(self):
        state = {
            "run_id": "run-123",
            "status": "failed",
            "phase": "failed",
            "log_path": r"C:\Users\alice\.reposense_studio\runs\run-123\logs.txt",
            "repo_path": "E:/projects/private-repo",
            "workspace_path": "/home/alice/.reposense_studio",
            "run_dir": "/tmp/run-123",
            "output_paths": {"report": "file:///Users/alice/report.html"},
            "project_id": "internal-project",
            "error_message": "Failed under /home/alice/private-repo",
            "logs_tail": [
                "scan started",
                r"reading \\server\share\private\repo",
            ],
            "summary": {"review_decision": "WARN"},
            "artifact_groups": [{
                "group_id": "review",
                "artifacts": [{
                    "relative_path": "report.html",
                    "url": "/runs/run-123/report.html",
                }],
            }],
        }

        payload = build_public_run_payload(state)

        for field in (
            "log_path",
            "repo_path",
            "workspace_path",
            "run_dir",
            "output_paths",
            "project_id",
        ):
            self.assertNotIn(field, payload)
        self.assertEqual(payload["logs_tail"], ["scan started"])
        self.assertNotIn("/home/alice", payload["error_message"])
        self.assertEqual(
            payload["artifact_groups"][0]["artifacts"][0]["url"],
            "/runs/run-123/report.html",
        )
        self.assertEqual(find_local_path_leaks(payload), [])

    def test_path_detection_distinguishes_public_urls_and_routes(self):
        unsafe = {
            "windows": r"C:\Users\alice\repo",
            "windows_slash": "E:/projects/repo",
            "unc": r"\\server\share\repo",
            "home": "/home/alice/repo",
            "users": "/Users/alice/repo",
            "tmp": "/tmp/run",
            "file_uri": "file:///home/alice/repo",
        }
        self.assertEqual(len(find_local_path_leaks(unsafe)), len(unsafe))
        safe = {
            "remote": "https://example.com/path",
            "api": "/api/runs/run-1",
            "artifact_url": "/runs/run-1/report.html",
            "relative_path": "context_pack/REVIEW/README.md",
            "route": "/api/orders/:id",
        }
        self.assertEqual(find_local_path_leaks(safe), [])

    def test_sections_with_nested_paths_degrade_without_api_failure(self):
        payload = build_public_run_payload({
            "run_id": "run-bad",
            "status": "completed",
            "review": {"top_risks": [{"source_path": "/opt/private/repo.ts"}]},
            "summary": {"review_decision": "WARN"},
        })
        self.assertEqual(payload["review"], {})
        self.assertIn("review_omitted_local_path", payload["warnings"])
        self.assertEqual(payload["summary"]["review_decision"], "WARN")

    def test_list_and_detail_are_stable_and_share_contract(self):
        state = {
            "run_id": "run-stable",
            "status": "completed",
            "phase": "done",
            "created_at": 123,
            "updated_at": 456,
            "log_path": "/tmp/private/log.txt",
        }
        first = build_public_run_payload(state)
        second = build_public_run_payload(state)
        self.assertEqual(first, second)
        item = build_public_run_list_item(state)
        self.assertEqual(item["run_id"], first["run_id"])
        self.assertNotIn("logs_tail", item)
        self.assertEqual(find_local_path_leaks(item), [])

    def test_malformed_internal_state_degrades_without_paths(self):
        payload = build_public_run_payload(None)
        self.assertIn("invalid_internal_run_state", payload["warnings"])
        self.assertEqual(find_local_path_leaks(payload), [])

        malformed = build_public_run_payload({
            "run_id": "run-malformed",
            "updated_at": "/tmp/private",
            "created_at": r"C:\Users\alice\private",
        })
        self.assertEqual(malformed["updated_at"], 0)
        self.assertEqual(malformed["start_time"], 0)
        self.assertEqual(find_local_path_leaks(malformed), [])


if __name__ == "__main__":
    unittest.main()
