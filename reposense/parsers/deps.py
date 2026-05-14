import json
import re
def parse_deps_manifest(path, text):
    res = []
    if path.endswith("package.json"):
        try:
            obj = json.loads(text)
        except:
            return res
        dep = obj.get("dependencies", {})
        dev = obj.get("devDependencies", {})
        names = list(dep.keys()) + list(dev.keys())
        for n in names:
            res.append(("Config", 1, 1, n, {"evidence_strength": "presence_only", "dependency": n}))
        return res
    if path.endswith("requirements.txt"):
        for i, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r'[<>=!~]', line)[0].strip()
            res.append(("Config", i, i, line, {"evidence_strength": "presence_only", "dependency": name}))
        return res
    if path.endswith("go.mod"):
        for i, line in enumerate(text.splitlines(), 1):
            m = re.search(r'^\s*require\s+([^\s]+)\s', line)
            if m:
                res.append(("Config", i, i, line.strip(), {"evidence_strength": "presence_only", "dependency": m.group(1)}))
        return res
    return res

