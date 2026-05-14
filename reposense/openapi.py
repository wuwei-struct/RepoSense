import json
import re
def parse_openapi_json(text):
    try:
        obj = json.loads(text)
    except:
        return []
    paths = obj.get("paths", {})
    res = []
    for p, methods in paths.items():
        if isinstance(methods, dict):
            for m in methods.keys():
                if m.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                    res.append((m.upper(), p))
    return res
def parse_openapi_yaml_subset(text):
    lines = text.splitlines()
    res = []
    in_paths = False
    cur_path = None
    path_indent = None
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        if re.match(r"^\s*paths\s*:", line):
            in_paths = True
            path_indent = None
            cur_path = None
            continue
        if not in_paths:
            continue
        if re.match(r"^\S", line):
            in_paths = False
            cur_path = None
            path_indent = None
            continue
        m = re.match(r"^(\s*)(/.+?):\s*$", line)
        if m:
            cur_path = m.group(2)
            path_indent = len(m.group(1))
            continue
        if cur_path is not None:
            mm = re.match(r"^(\s*)(get|post|put|delete|patch|head|options)\s*:\s*$", line, re.IGNORECASE)
            if mm and len(mm.group(1)) > path_indent:
                res.append((mm.group(2).upper(), cur_path))
    return res

