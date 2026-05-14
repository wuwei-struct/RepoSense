import http.server
import socketserver
import webbrowser
from urllib.parse import parse_qs, urlsplit

from .app import LearnUIApp


class _LearnTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def make_handler(app: LearnUIApp):
    class LearnUIHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query, keep_blank_values=True)
            result = app.route(parsed.path, query)
            headers = {}
            if len(result) == 4:
                status, content_type, body, headers = result
            else:
                status, content_type, body = result
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for k, v in headers.items():
                self.send_header(str(k), str(v))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            return

    return LearnUIHandler


def run_learn_ui_server(cases_dir: str, host: str = "127.0.0.1", port: int = 8000, open_browser: bool = False, concepts_path: str = None):
    app = LearnUIApp(cases_dir=cases_dir, concepts_path=concepts_path)
    handler = make_handler(app)
    with _LearnTCPServer((host, int(port)), handler) as httpd:
        url = f"http://{host}:{int(port)}/learn"
        print(f"Serving Learn UI from {cases_dir} at {url}")
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
