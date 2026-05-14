class LanguageAdapter:
    language_id = "unknown"
    display_name = "Unknown"
    file_matchers = []

    def detect_framework_hints(self, run_dir, findings=None, graph=None):
        return []

    def emit_findings(self, run_dir, findings=None):
        return []

    def emit_events(self, run_dir, graph=None):
        return []

    def emit_api_surface(self, run_dir, api_surface=None):
        return []

    def emit_entrypoints(self, run_dir, entrypoints=None):
        return []

    def capabilities(self):
        return {
            "event_kinds": [],
            "framework_hints": [],
            "supports": {
                "findings": False,
                "events": False,
                "api_surface": False,
                "entrypoints": False,
            },
        }
