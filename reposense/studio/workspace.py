import os
import shutil
import uuid
import time
import zipfile
from pathlib import Path
import json

class WorkspaceManager:
    def __init__(self, base_dir=".reposense_studio"):
        self.base_dir = os.path.abspath(base_dir)
        self.projects_dir = os.path.join(self.base_dir, "projects")
        self.runs_dir = os.path.join(self.base_dir, "runs")
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.runs_dir, exist_ok=True)

    def import_zip(self, zip_path):
        project_id = str(uuid.uuid4())
        project_path = os.path.join(self.projects_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(project_path)
            return project_id
        except Exception as e:
            shutil.rmtree(project_path, ignore_errors=True)
            raise e

    def import_local_path(self, repo_path):
        project_id = str(uuid.uuid4())
        project_path = os.path.join(self.projects_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        marker = os.path.join(project_path, "source_path.txt")
        try:
            with open(marker, "w", encoding="utf-8") as f:
                f.write(repo_path)
            return project_id
        except Exception as e:
            shutil.rmtree(project_path, ignore_errors=True)
            raise e

    def create_run(self, project_id):
        run_id = f"run-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        run_dir = os.path.join(self.runs_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)
        # initialize state file
        state = {
            "run_id": run_id,
            "project_id": project_id,
            "status": "queued",
            "phase": "queued",
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "error_message": "",
            "log_path": os.path.join(run_dir, "logs.txt"),
            "output_paths": {},
        }
        try:
            with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
        except Exception:
            pass
        return run_id, run_dir

    def get_project_path(self, project_id):
        project_path = os.path.join(self.projects_dir, project_id)
        marker = os.path.join(project_path, "source_path.txt")
        if os.path.isfile(marker):
            try:
                with open(marker, "r", encoding="utf-8") as f:
                    p = (f.read() or "").strip()
                if p:
                    return p
            except Exception:
                pass
        return project_path
    
    def get_run_dir(self, run_id):
        return os.path.join(self.runs_dir, run_id)

    def write_run_state(self, run_id, state):
        run_dir = self.get_run_dir(run_id)
        try:
            p = os.path.join(run_dir, "run.json")
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
            try:
                os.replace(tmp, p)
            except Exception:
                # Fallback rename on some platforms
                shutil.move(tmp, p)
        except Exception:
            pass

    def ensure_run_dir(self, run_id):
        rd = self.get_run_dir(run_id)
        os.makedirs(rd, exist_ok=True)
        return rd

    def read_run_state(self, run_id):
        p = os.path.join(self.get_run_dir(run_id), "run.json")
        if not os.path.exists(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def list_runs(self):
        items = []
        try:
            for nm in sorted(os.listdir(self.runs_dir)):
                run_id = nm
                p = os.path.join(self.runs_dir, nm, "run.json")
                if not os.path.isfile(p):
                    continue
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        st = json.load(f)
                    items.append({
                        "run_id": st.get("run_id", run_id),
                        "status": st.get("status", ""),
                        "phase": st.get("phase", ""),
                        "start_time": st.get("created_at", int(time.time())),
                        "updated_at": st.get("updated_at", st.get("created_at", int(time.time()))),
                    })
                except Exception:
                    pass
            items.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        except Exception:
            pass
        return items
