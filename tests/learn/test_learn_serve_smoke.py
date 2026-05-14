import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request

from tests.learn._learn_ui_fixture import build_learn_ui_fixture


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _wait_http_ok(url, timeout_sec=6.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            time.sleep(0.1)
    raise AssertionError(f"server not ready: {url}")


class LearnServeSmokeTest(unittest.TestCase):
    def test_learn_serve_can_start_and_load_cases_dir(self):
        fx = build_learn_ui_fixture()
        port = _free_port()
        cmd = [
            sys.executable,
            "-m",
            "reposense",
            "learn",
            "serve",
            "--dir",
            fx["cases_dir"],
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        try:
            html = _wait_http_ok(f"http://127.0.0.1:{port}/learn")
            self.assertIn("Concept Navigator", html)
            self.assertIn("Case Browser", html)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
            shutil.rmtree(fx["root"], ignore_errors=True)

    def test_learn_serve_empty_dir_shows_empty_state(self):
        empty_root = tempfile.mkdtemp(prefix="learn-serve-empty-")
        port = _free_port()
        cmd = [
            sys.executable,
            "-m",
            "reposense",
            "learn",
            "serve",
            "--dir",
            empty_root,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        try:
            html = _wait_http_ok(f"http://127.0.0.1:{port}/learn/cases")
            self.assertIn("No cases found", html)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
            shutil.rmtree(empty_root, ignore_errors=True)

