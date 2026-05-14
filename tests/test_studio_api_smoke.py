import unittest
import threading
import time
import os
import shutil
import tempfile
import json
import zipfile
import requests
import socket
from reposense.studio.server import StudioHandler
from reposense.studio.workspace import WorkspaceManager
import socketserver

# Use a random free port for testing to avoid conflicts
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

TEST_PORT = get_free_port()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class StudioApiSmokeTest(unittest.TestCase):
    server = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        # Start server in thread
        cls.server = ThreadedTCPServer(("127.0.0.1", TEST_PORT), StudioHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(0.5) # wait for start

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def setUp(self):
        self.base_url = f"http://127.0.0.1:{TEST_PORT}"
        self.tmp_dir = tempfile.mkdtemp()
        self.zip_path = os.path.join(self.tmp_dir, "test.zip")
        with zipfile.ZipFile(self.zip_path, 'w') as z:
            z.writestr("test.txt", "content")

    def tearDown(self):
        try:
            import gc
            gc.collect()
            shutil.rmtree(self.tmp_dir)
        except:
            pass

    def test_import_zip(self):
        url = f"{self.base_url}/api/projects/import-zip"
        with open(self.zip_path, 'rb') as f:
            files = {'file': f}
            # Use short timeout to fail fast if hung
            resp = requests.post(url, files=files, timeout=2)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("project_id", data)
        return data["project_id"]

    def test_start_run_and_status(self):
        # Create a new zip for this test
        zip_path_2 = os.path.join(self.tmp_dir, "test2.zip")
        with zipfile.ZipFile(zip_path_2, 'w') as z:
            z.writestr("test.txt", "content")
            
        url_import = f"{self.base_url}/api/projects/import-zip"
        with open(zip_path_2, 'rb') as f:
            files = {'file': f}
            resp = requests.post(url_import, files=files, timeout=2)
        self.assertEqual(resp.status_code, 200)
        pid = resp.json()["project_id"]
        
        # Start run
        url = f"{self.base_url}/api/runs"
        payload = {
            "project_id": pid,
            "ruleset": "rulesets/basic",
            "budget": "presets/default.json",
            "specs": "specs"
        }
        resp = requests.post(url, json=payload, timeout=2)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("run_id", body)
        self.assertIn("id", body)
        run_id = body["run_id"]
        
        # Check status must respond at least once quickly (no deadlock)
        url_status = f"{self.base_url}/api/runs/{run_id}"
        ok = False
        for _ in range(10):
            try:
                resp_status = requests.get(url_status, timeout=2)
                if resp_status.status_code == 200:
                    status = resp_status.json()
                    self.assertIn(status["status"], ["running", "completed", "failed"])
                    self.assertIn("phase", status)
                    lines = status.get("logs_tail", [])
                    if any("specs graph build" in s or ("learn build" in s and "--concept-graph" in s) for s in lines):
                        # saw concept graph related invocation
                        pass
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(0.2)
        if not ok:
            self.fail("status endpoint did not respond in time (possible deadlock)")
        # Global runs list also must respond quickly
        resp_list = requests.get(f"{self.base_url}/api/runs", timeout=2)
        self.assertEqual(resp_list.status_code, 200)

    def test_get_runs_list(self):
        resp = requests.get(f"{self.base_url}/api/runs", timeout=2)
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)
    
    def test_run_status_404_is_json(self):
        url_status = f"{self.base_url}/api/runs/nonexistent-run-id"
        resp = requests.get(url_status, timeout=2)
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertIn("error", data)
        self.assertIn("message", data)

if __name__ == '__main__':
    unittest.main()
