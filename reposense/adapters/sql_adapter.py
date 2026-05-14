from .base import LanguageAdapter
from ..events.normalize import graph_node_to_unified_event


class SQLAdapter(LanguageAdapter):
    language_id = "sql"
    display_name = "SQL"
    file_matchers = ["**/*.sql"]

    def detect_framework_hints(self, run_dir, findings=None, graph=None):
        return ["sql"]

    def emit_events(self, run_dir, graph=None):
        out = []
        for n in (graph or {}).get("nodes", []):
            u = graph_node_to_unified_event(n)
            if not u:
                continue
            if u.get("language") == "sql":
                out.append(u)
        return out

    def capabilities(self):
        return {
            "event_kinds": ["db.transaction"],
            "framework_hints": ["sql"],
            "supports": {"findings": True, "events": True, "api_surface": False, "entrypoints": False},
        }
