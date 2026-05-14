from .base import LanguageAdapter
from ..events.normalize import graph_node_to_unified_event


class JavaAdapter(LanguageAdapter):
    language_id = "java"
    display_name = "Java"
    file_matchers = ["**/*.java"]

    def detect_framework_hints(self, run_dir, findings=None, graph=None):
        out = set()
        for f in findings or []:
            m = f.get("meta") or {}
            if str(m.get("language") or "").lower() == "java":
                fw = str(m.get("framework") or "").lower()
                if fw:
                    out.add("spring")
                jk = str(m.get("java.kind") or "").lower()
                if "spring" in jk or "route" in jk:
                    out.add("spring_mvc")
                    out.add("spring_boot")
                if str(m.get("tx.kind") or "").lower() == "java_transactional":
                    out.add("spring")
                jk2 = str(m.get("java.kind") or "").lower()
                if "queue" in jk2 or str(m.get("queue.system") or "").lower() in ("kafka", "rabbitmq"):
                    qs = str(m.get("queue.system") or "").lower()
                    if qs == "kafka":
                        out.add("spring_kafka")
                    if qs == "rabbitmq":
                        out.add("spring_rabbit")
                if "db" in jk2:
                    ds = str(m.get("db_style") or "").lower()
                    if "mybatis" in ds or "sql_session" in ds:
                        out.add("mybatis")
                    if "jpa" in ds or "entity_manager" in ds:
                        out.add("jpa")
        return sorted(list(out))

    def emit_events(self, run_dir, graph=None):
        out = []
        for n in (graph or {}).get("nodes", []):
            u = graph_node_to_unified_event(n)
            if not u:
                continue
            if u.get("language") == "java":
                out.append(u)
        return out

    def emit_api_surface(self, run_dir, api_surface=None):
        out = []
        for ep in (api_surface or {}).get("endpoints", []):
            sk = str(ep.get("source_kind") or "")
            if sk.startswith("java") or str((ep.get("source") or {}).get("path") or "").lower().endswith(".java"):
                out.append(ep)
        return out

    def capabilities(self):
        return {
            "event_kinds": ["api.route", "db.transaction", "queue.dispatch", "queue.consume", "db.read", "db.write"],
            "framework_hints": ["spring_mvc", "spring_boot", "spring", "spring_kafka", "spring_rabbit", "jpa", "mybatis"],
            "supports": {"findings": True, "events": True, "api_surface": True, "entrypoints": False},
        }
