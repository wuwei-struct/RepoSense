from .base import LanguageAdapter
from ..events.normalize import graph_node_to_unified_event


class PythonAdapter(LanguageAdapter):
    language_id = "python"
    display_name = "Python"
    file_matchers = ["**/*.py"]

    def detect_framework_hints(self, run_dir, findings=None, graph=None):
        out = set()
        for f in findings or []:
            m = f.get("meta") or {}
            matcher = str(m.get("ast.matcher") or "")
            pk = str(m.get("python.kind") or "")
            if "fastapi" in matcher:
                out.add("fastapi")
            if "flask" in matcher:
                out.add("flask")
            if "django" in matcher or "django" in pk:
                out.add("django")
            if "celery" in matcher or "celery" in pk:
                out.add("celery")
            if "cache" in matcher:
                out.add("redis" if "redis" in pk else "django")
        return sorted(list(out))

    def emit_events(self, run_dir, graph=None):
        events = []
        for n in (graph or {}).get("nodes", []):
            u = graph_node_to_unified_event(n)
            if not u:
                continue
            if u.get("language") == "python":
                events.append(u)
        return events

    def emit_api_surface(self, run_dir, api_surface=None):
        out = []
        for ep in (api_surface or {}).get("endpoints", []):
            if str(ep.get("source_kind") or "").startswith("python"):
                out.append(ep)
        return out

    def emit_entrypoints(self, run_dir, entrypoints=None):
        out = []
        for ep in (entrypoints or {}).get("entrypoints", []):
            src = (ep.get("source") or {}).get("path") or ""
            if str(src).endswith(".py"):
                out.append(ep)
        return out

    def capabilities(self):
        return {
            "event_kinds": ["api.route", "db.transaction", "queue.dispatch", "cache.read", "cache.write", "cache.invalidate"],
            "framework_hints": ["fastapi", "flask", "django", "celery", "redis"],
            "supports": {"findings": True, "events": True, "api_surface": True, "entrypoints": True},
        }
