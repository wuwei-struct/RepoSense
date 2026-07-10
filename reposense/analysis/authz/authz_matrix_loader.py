import os

import yaml

from .authz_matrix_schema import normalize_expected_route


def find_contract(repo_path, explicit_path=None):
    if explicit_path:
        return explicit_path if os.path.isfile(explicit_path) else None
    candidate = os.path.join(repo_path, "reposense.authz.yaml")
    return candidate if os.path.isfile(candidate) else None


def load_authz_contract(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError("invalid authz contract yaml: " + str(e))
    except OSError as e:
        raise ValueError("cannot read authz contract: " + str(e))
    if not isinstance(raw, dict):
        raw = {}
    routes = raw.get("routes") if isinstance(raw.get("routes"), dict) else {}
    normalized = [normalize_expected_route(k, v) for k, v in sorted(routes.items(), key=lambda kv: str(kv[0]))]
    return {
        "version": "authz_matrix_contract_v1",
        "source_path": path,
        "resources": raw.get("resources") if isinstance(raw.get("resources"), dict) else {},
        "routes": normalized,
        "limitations": ["Unrecognized fields are preserved only at route level and are not enforced in the MVP."],
    }

