import unittest
import threading
import time
import os
import socket
import socketserver
from reposense.studio.server import StudioHandler, workspace


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class StudioRunsStaticPathsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = get_free_port()
        cls.server = ThreadedTCPServer(("127.0.0.1", cls.port), StudioHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        time.sleep(0.5)
        # prepare a run dir with minimal files
        cls.run_id = "run-test-static"
        run_dir = workspace.get_run_dir(cls.run_id)
        os.makedirs(run_dir, exist_ok=True)
        # report.html + report.json + assets
        os.makedirs(os.path.join(run_dir, "assets"), exist_ok=True)
        with open(os.path.join(run_dir, "assets", "x.css"), "w", encoding="utf-8") as f:
            f.write("body{background:#fff}")
        with open(os.path.join(run_dir, "report.html"), "w", encoding="utf-8") as f:
            f.write("<html><body>ok</body></html>")
        with open(os.path.join(run_dir, "report.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        # exports
        os.makedirs(os.path.join(run_dir, "exports"), exist_ok=True)
        with open(os.path.join(run_dir, "exports", "report.sarif.json"), "w", encoding="utf-8") as f:
            f.write("{}")
        # context_pack
        os.makedirs(os.path.join(run_dir, "context_pack"), exist_ok=True)
        with open(os.path.join(run_dir, "context_pack", "manifest.json"), "w", encoding="utf-8") as f:
            f.write("{}")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_static_paths_under_runs(self):
        import requests
        base = f"http://127.0.0.1:{self.port}"
        rid = self.run_id
        # report.html
        r = requests.get(f"{base}/runs/{rid}/report.html", timeout=2)
        self.assertEqual(r.status_code, 200)
        # assets
        r = requests.get(f"{base}/runs/{rid}/assets/x.css", timeout=2)
        self.assertEqual(r.status_code, 200)
        # exports
        r = requests.get(f"{base}/runs/{rid}/exports/report.sarif.json", timeout=2)
        self.assertEqual(r.status_code, 200)
        # context_pack
        r = requests.get(f"{base}/runs/{rid}/context_pack/manifest.json", timeout=2)
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()

