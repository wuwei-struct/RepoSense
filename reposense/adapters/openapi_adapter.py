from .base import LanguageAdapter


class OpenAPIAdapter(LanguageAdapter):
    language_id = "openapi"
    display_name = "OpenAPI"
    file_matchers = ["**/*.yaml", "**/*.yml", "**/*.json"]

    def detect_framework_hints(self, run_dir, findings=None, graph=None):
        for f in findings or []:
            m = f.get("meta") or {}
            if str(m.get("evidence_strength") or "") == "openapi" or m.get("http.method"):
                return ["openapi"]
        return []

    def emit_api_surface(self, run_dir, api_surface=None):
        out = []
        for ep in (api_surface or {}).get("endpoints", []):
            if str(ep.get("source_kind") or "") == "openapi":
                out.append(ep)
        return out

    def capabilities(self):
        return {
            "event_kinds": ["api.route"],
            "framework_hints": ["openapi"],
            "supports": {"findings": True, "events": False, "api_surface": True, "entrypoints": False},
        }
