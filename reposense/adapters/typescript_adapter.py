from .base import LanguageAdapter
from ..events.normalize import graph_node_to_unified_event


class TypeScriptAdapter(LanguageAdapter):
    language_id = "typescript"
    display_name = "TypeScript"
    file_matchers = ["**/*.ts", "**/*.tsx", "**/*.mts", "**/*.cts"]

    def detect_framework_hints(self, run_dir, findings=None, graph=None):
        out = set()
        for f in findings or []:
            m = f.get("meta") or {}
            if str(m.get("language") or "").lower() == "typescript":
                fw = str(m.get("framework") or "").lower()
                if fw:
                    out.add(fw)
                tk = str(m.get("ts.kind") or "").lower()
                if "express" in tk:
                    out.add("express")
                if "nest" in tk:
                    out.add("nestjs")
                if "prisma" in tk:
                    out.add("prisma")
                if "typeorm" in tk:
                    out.add("typeorm")
                if "queue" in tk:
                    out.add("bullmq")
                if "cache" in tk:
                    out.add("redis")
                if "bull" in fw:
                    out.add(fw)
                if fw in ("redis", "ioredis"):
                    out.add(fw)
        return sorted(list(out))

    def emit_events(self, run_dir, graph=None):
        out = []
        for n in (graph or {}).get("nodes", []):
            u = graph_node_to_unified_event(n)
            if not u:
                continue
            if u.get("language") == "typescript":
                out.append(u)
        return out

    def emit_api_surface(self, run_dir, api_surface=None):
        out = []
        for ep in (api_surface or {}).get("endpoints", []):
            sk = str(ep.get("source_kind") or "")
            if "typescript" in sk:
                out.append(ep)
        return out

    def capabilities(self):
        return {
            "event_kinds": ["api.route", "db.transaction", "queue.dispatch", "queue.consume", "cache.read", "cache.write", "cache.invalidate"],
            "framework_hints": ["express", "nestjs", "prisma", "typeorm", "bull", "bullmq", "redis", "ioredis"],
            "supports": {"findings": True, "events": True, "api_surface": True, "entrypoints": False},
        }
