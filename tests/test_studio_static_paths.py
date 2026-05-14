import unittest
import threading
import time
import requests
import socket
import socketserver
from reposense.studio.server import StudioHandler

class StudioStaticPathsTest(unittest.TestCase):
    server = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        cls.port = s.getsockname()[1]
        s.close()

        class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            allow_reuse_address = True
            daemon_threads = True

        cls.server = ThreadedTCPServer(("127.0.0.1", cls.port), StudioHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def test_static_index(self):
        resp = requests.get(f"http://127.0.0.1:{self.port}/", timeout=2)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("RepoSense Studio", resp.text)

    def test_static_css(self):
        resp = requests.get(f"http://127.0.0.1:{self.port}/static/reposense.css", timeout=2)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("color", resp.text)

if __name__ == '__main__':
    unittest.main()
