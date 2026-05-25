import http.server
import socketserver
import json
import os
import shutil
import tempfile
import urllib.parse
from pathlib import Path
from .workspace import WorkspaceManager
from .jobs import JobManager

PORT = 8010
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "webui")

workspace = WorkspaceManager()
jobs = JobManager(workspace)


def resolve_local_repo_path(repo_path):
    raw = str(repo_path or "").strip()
    if not raw:
        raise ValueError("repo_path is required")
    if raw.startswith("\\\\"):
        raise ValueError("UNC/network paths are not supported in Studio local path mode")
    try:
        p = Path(raw).expanduser().resolve()
    except Exception:
        raise ValueError("invalid repo_path")
    if not p.exists():
        raise ValueError(f"repo_path not found: {p}")
    if not p.is_dir():
        raise ValueError(f"repo_path is not a directory: {p}")
    return str(p)

class StudioHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve API
        if self.path.startswith("/api/"):
            self.handle_api()
            return
            
        # Serve Run Artifacts under /runs/<run_id>/...
        # Prefix mapping + default fallback:
        # - learn/ -> run_dir/learn_site/...
        # - exports/ -> run_dir/exports/...
        # - context_pack/ -> run_dir/context_pack/...
        # - otherwise -> run_dir/<rest>
        if self.path.startswith("/runs/"):
            parts = self.path.strip("/").split("/")
            if len(parts) >= 2:
                run_id = parts[1]
                rest = "/".join(parts[2:]) if len(parts) >= 3 else ""
                run_dir = workspace.get_run_dir(run_id)
                if not os.path.exists(run_dir):
                    self.send_error(404, "Run not found")
                    return
                # Redirect /runs/<id> or /runs/<id>/ to report.html
                if rest == "" or rest == "/":
                    self.send_response(302)
                    self.send_header("Location", f"/runs/{run_id}/report.html")
                    self.end_headers()
                    return
                # Special case legacy /runs/<id>/report/ -> report.html
                if rest == "report":
                    self.send_response(302)
                    self.send_header("Location", f"/runs/{run_id}/report.html")
                    self.end_headers()
                    return
                # Prefix mapping
                if rest.startswith("learn/"):
                    base = os.path.join(run_dir, "learn_site")
                    rel = rest[len("learn/"):]
                    if rel == "" or rel == "/":
                        self.send_response(302)
                        self.send_header("Location", f"/runs/{run_id}/learn/index.html")
                        self.end_headers()
                        return
                    target = os.path.join(base, rel)
                    if os.path.exists(target) and os.path.isfile(target):
                        self.serve_file(target)
                        return
                elif rest.startswith("exports/"):
                    base = os.path.join(run_dir, "exports")
                    rel = rest[len("exports/"):]
                    target = os.path.join(base, rel)
                    if os.path.exists(target) and os.path.isfile(target):
                        self.serve_file(target)
                        return
                elif rest.startswith("context_pack/"):
                    base = os.path.join(run_dir, "context_pack")
                    rel = rest[len("context_pack/"):]
                    target = os.path.join(base, rel)
                    if os.path.exists(target) and os.path.isfile(target):
                        self.serve_file(target)
                        return
                # Default fallback: serve from run_dir/<rest>
                target = os.path.join(run_dir, rest)
                if os.path.exists(target) and os.path.isfile(target):
                    self.serve_file(target)
                    return

        # Serve WebUI Static
        # Map / -> webui/studio/index.html
        # Map /static/... -> webui/static/...
        # Map /studio/... -> webui/studio/...
        if self.path == "/" or self.path == "/studio" or self.path == "/studio/":
            self.serve_file(os.path.join(STATIC_DIR, "studio", "index.html"))
            return
        
        # Fallback to serving from STATIC_DIR parent logic
        # But we need to map URLs carefully
        # Simple hack: if file exists in webui/studio, serve it
        # if file exists in webui/static, serve it
        
        path = self.path.lstrip("/")
        
        # Check studio/
        p1 = os.path.join(STATIC_DIR, "studio", path)
        if os.path.exists(p1) and os.path.isfile(p1):
            self.serve_file(p1)
            return

        # Check static/ (e.g. reposense.css)
        if path.startswith("static/"):
            p2 = os.path.join(STATIC_DIR, path)
            if os.path.exists(p2) and os.path.isfile(p2):
                self.serve_file(p2)
                return

        self.send_error(404, "File not found")

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.handle_api_post()
            return
        self.send_error(404, "Not found")

    def handle_api(self):
        if self.path == "/api/profiles":
            try:
                from ..profiles import list_profiles
                edition = os.environ.get("REPOSENSE_EDITION", "oss")
                self.send_json(list_profiles(edition=edition))
            except Exception as e:
                self.send_json_error(500, {"error": "profiles_list_failed", "message": str(e)})
            return
        if self.path == "/api/runs":
            # combine persisted runs with in-memory
            persisted = workspace.list_runs()
            mem = {rid: j for rid, j in [(r["run_id"], r) for r in jobs.get_all_jobs()]}
            # overlay in-memory status where available
            out = []
            for pr in persisted:
                rid = pr["run_id"]
                if rid in mem:
                    m = mem[rid]
                    pr = {
                        "run_id": rid,
                        "status": m.get("status", pr.get("status")),
                        "phase": m.get("phase", pr.get("phase")),
                        "start_time": pr.get("start_time"),
                    }
                # attach lightweight summary if artifacts exist
                try:
                    run_dir = workspace.get_run_dir(rid)
                    cov = {}
                    rep = {}
                    graph = {}
                    gate = {}
                    p_cov = os.path.join(run_dir, "coverage.json")
                    p_rep = os.path.join(run_dir, "report.json")
                    p_graph = os.path.join(run_dir, "event_graph.json")
                    p_gate = os.path.join(run_dir, "quality_gate.json")
                    if os.path.isfile(p_cov):
                        with open(p_cov, "r", encoding="utf-8") as f:
                            cov = json.load(f)
                    if os.path.isfile(p_rep):
                        with open(p_rep, "r", encoding="utf-8") as f:
                            rep = json.load(f)
                    if os.path.isfile(p_graph):
                        with open(p_graph, "r", encoding="utf-8") as f:
                            graph = json.load(f)
                    if os.path.isfile(p_gate):
                        with open(p_gate, "r", encoding="utf-8") as f:
                            gate = json.load(f)
                    skip = (cov.get("walk") or {}).get("skipped") or {}
                    top_skip = None
                    if skip:
                        top_skip = sorted(skip.items(), key=lambda x: x[1], reverse=True)[0][0]
                    pr["summary"] = {
                        "findings_count": len(rep.get("findings", [])) if rep else 0,
                        "events_count": len((graph.get("nodes") or [])) if graph else 0,
                        "graph_edges": len((graph.get("edges") or [])) if graph else 0,
                        "top_skip_reason": top_skip,
                        "truncation": {
                            "budget_cut": bool(((cov.get("walk") or {}).get("budget_cut_reached"))),
                            "findings_truncated": any(x == "max_findings_reached" for x in (cov.get("warnings") or [])),
                        }
                    }
                    if gate:
                        reg = gate.get("regressions") or {}
                        pr["summary"]["baseline_used"] = bool(gate.get("baseline_used"))
                        pr["summary"]["regressions"] = {"total": reg.get("total",0), "added_error": reg.get("added_error",0), "severity_upgrades": reg.get("severity_upgrades",0), "added_warning": reg.get("added_warning",0)}
                        pr["summary"]["baseline_compatible"] = bool(gate.get("baseline_compatible", True))
                except Exception:
                    pass
                out.append(pr)
            # include any purely in-memory not yet persisted
            for rid, m in mem.items():
                if not any(x["run_id"] == rid for x in out):
                    out.append({
                        "run_id": rid,
                        "status": m.get("status", ""),
                        "phase": m.get("phase", ""),
                        "start_time": m.get("start_time", 0),
                    })
            out.sort(key=lambda x: x.get("start_time", 0), reverse=True)
            self.send_json(out)
        elif self.path.startswith("/api/runs/"):
            run_id = self.path.split("/")[-1]
            status = jobs.get_job_status(run_id)
            if status:
                if "logs_tail" not in status:
                    status["logs_tail"] = status.get("logs", [])
                status.setdefault("phase", "")
                status.setdefault("status", "")
                self.send_json(status)
                return
            # fallback to persisted state
            st = workspace.read_run_state(run_id)
            if st:
                out = {
                    "run_id": st.get("run_id", run_id),
                    "status": st.get("status", ""),
                    "phase": st.get("phase", ""),
                    "logs_tail": [],
                    "error_message": st.get("error_message", ""),
                    "updated_at": st.get("updated_at", 0),
                    "log_path": st.get("log_path", ""),
                }
                self.send_json(out)
            else:
                self.send_json_error(404, {"error": "run_not_found", "message": "Run not found"})
        else:
            self.send_error(404, "API endpoint not found")

    def handle_api_post(self):
        if self.path == "/api/projects/import-zip":
            # Very basic multipart parsing for zip
            content_type = self.headers.get('Content-Type', '')
            if not 'multipart/form-data' in content_type:
                self.send_error(400, "Expected multipart/form-data")
                return
                
            # Manual multipart parsing since cgi is deprecated
            boundary = content_type.split("boundary=")[1].encode()
            
            # Read all body
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            
            # Find file content
            # This is a very naive parser for the sake of not adding dependencies
            # Structure:
            # --boundary
            # Content-Disposition: form-data; name="file"; filename="..."
            # ...
            # <content>
            # --boundary--
            
            parts = body.split(b"--" + boundary)
            file_content = None
            
            for part in parts:
                if b'name="file"' in part and b'filename="' in part:
                    # Found file part
                    # Split headers and content
                    headers_end = part.find(b"\r\n\r\n")
                    if headers_end != -1:
                        # Extract content (removing trailing \r\n)
                        file_content = part[headers_end+4:-2]
                        break
            
            if not file_content:
                self.send_error(400, "File not found in body")
                return

            # Save to temp
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name
            
            try:
                project_id = workspace.import_zip(tmp_path)
                os.remove(tmp_path)
                self.send_json({"project_id": project_id})
            except Exception as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                self.send_error(500, str(e))

        elif self.path == "/api/runs":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            
            project_id = data.get("project_id")
            ruleset = data.get("ruleset", "rulesets/specs_v2")
            budget = data.get("budget", "presets/default.json")
            specs = data.get("specs", "specs")
            
            try:
                run_id = jobs.start_run(project_id, ruleset, budget, specs)
                self.send_json({"run_id": run_id, "id": run_id, "status": "queued"})
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == "/api/projects/import-path":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body or b"{}")
            except Exception:
                self.send_json_error(400, {"error": "invalid_json", "message": "invalid JSON body"})
                return
            try:
                repo_path = resolve_local_repo_path(data.get("repo_path"))
                project_id = workspace.import_local_path(repo_path)
                self.send_json({"project_id": project_id, "repo_path": repo_path})
            except ValueError as e:
                self.send_json_error(400, {"error": "invalid_repo_path", "message": str(e)})
            except Exception as e:
                self.send_json_error(500, {"error": "import_path_failed", "message": str(e)})
        else:
            self.send_error(404, "API endpoint not found")

    def send_json(self, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(payload)
            self.wfile.flush()
        except Exception:
            pass
    def send_json_error(self, code, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(payload)
            self.wfile.flush()
        except Exception:
            pass

    def serve_file(self, path):
        self.send_response(200)
        # mime types
        ext = os.path.splitext(path)[1]
        mime = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".svg": "image/svg+xml"
        }.get(ext, "application/octet-stream")
        
        self.send_header("Content-Type", mime)
        self.end_headers()
        with open(path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

def run_server(port=PORT):
    try:
        import reposense.studio.jobs as jobs_mod
        print(f"[studio] jobs.py = {getattr(jobs_mod, '__file__', 'unknown')}")
    except Exception:
        pass
    print(f"Starting RepoSense Studio at http://127.0.0.1:{port}")
    with socketserver.TCPServer(("127.0.0.1", port), StudioHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
