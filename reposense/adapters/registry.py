from .python_adapter import PythonAdapter
from .sql_adapter import SQLAdapter
from .openapi_adapter import OpenAPIAdapter
from .typescript_adapter import TypeScriptAdapter
from .java_adapter import JavaAdapter

_REGISTRY = {}


def register_adapter(adapter):
    _REGISTRY[str(adapter.language_id)] = adapter


def _init_defaults():
    if _REGISTRY:
        return
    register_adapter(PythonAdapter())
    register_adapter(SQLAdapter())
    register_adapter(OpenAPIAdapter())
    register_adapter(TypeScriptAdapter())
    register_adapter(JavaAdapter())


def list_registered_languages():
    _init_defaults()
    return sorted(list(_REGISTRY.keys()))


def get_adapter(language_id):
    _init_defaults()
    return _REGISTRY.get(str(language_id or "").lower())


def get_capability_matrix():
    _init_defaults()
    data = {}
    for lid in list_registered_languages():
        ad = _REGISTRY[lid]
        caps = ad.capabilities() or {}
        data[lid] = {
            "display_name": ad.display_name,
            "event_kinds": sorted(list(caps.get("event_kinds") or [])),
            "framework_hints": sorted(list(caps.get("framework_hints") or [])),
            "supports": caps.get("supports") or {},
        }
    return data
