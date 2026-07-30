import json
import os
import socket
import socketserver
import tempfile
import threading
import unittest
import urllib.request

import reposense.studio.server as studio_server
from reposense.studio.jobs import JobManager
from reposense.studio.public_run_payload import find_local_path_leaks
from reposense.studio.workspace import WorkspaceManager


class _ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class StudioRunApiPathPrivacyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_workspace = studio_server.workspace
        self.old_jobs = studio_server.jobs
        studio_server.workspace = WorkspaceManager(
            base_dir=os.path.join(self.temp.name, "studio")
        )
        studio_server.jobs = JobManager(studio_server.workspace)
        run_id, run_dir = studio_server.workspace.create_run("project")
        self.run_id = run_id
        state_path = os.path.join(run_dir, "run.json")
        with open(state_path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
        state.update({
            "status": "completed",
            "phase": "done",
            "repo_path": r"C:\Users\alice\private",
            "workspace_path": "/home/alice/.reposense_studio",
            "output_paths": {"run_dir": r"\\server\share\runs"},
        })
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        with open(os.path.join(run_dir, "report.html"), "w", encoding="utf-8") as handle:
            handle.write("<html>report</html>")

        self.port = _free_port()
        self.server = _ThreadedServer(
            ("127.0.0.1", self.port), studio_server.StudioHandler
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        studio_server.workspace = self.old_workspace
        studio_server.jobs = self.old_jobs
        self.temp.cleanup()

    def test_run_list_has_no_local_paths(self):
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/api/runs"
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        item = next(row for row in payload if row["run_id"] == self.run_id)
        self.assertEqual(find_local_path_leaks(item), [])
        self.assertNotIn("log_path", item)
        artifacts = [
            artifact
            for group in item["artifact_groups"]
            for artifact in group["artifacts"]
        ]
        report = next(
            artifact for artifact in artifacts
            if artifact["artifact_id"] == "main_html_report"
        )
        self.assertEqual(report["url"], f"/runs/{self.run_id}/report.html")


if __name__ == "__main__":
    unittest.main()
