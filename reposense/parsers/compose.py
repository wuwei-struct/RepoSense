import re
def parse_compose(text):
    lines = text.splitlines()
    res = []
    in_services = False
    current_service = None
    base_indent = None
    def make_hit(concept, i, line, kind=None):
        meta = {"service_name": current_service} if current_service else {}
        if kind:
            tmap = {"Cache":"cache","Queue":"queue","KV/Storage":"storage"}
            meta["infra_kind"] = kind.lower()
            meta["infra_type"] = tmap.get(concept)
        return (concept, i, i, line.strip(), meta)
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("services:"):
            in_services = True
            base_indent = len(line) - len(line.lstrip())
            current_service = None
            continue
        if in_services:
            if line.strip() == "" or line.strip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent:
                in_services = False
                current_service = None
                base_indent = None
            else:
                if ":" in line and not line.strip().startswith("-") and re.match(r'^\s*[A-Za-z0-9_.-]+\s*:', line):
                    current_service = line.strip().split(":")[0]
        # hits
        m = re.search(r'\bimage:\s*(redis|memcached)\b', line, re.I)
        if m:
            res.append(make_hit("Cache", i, line, m.group(1)))
        m = re.search(r'\bimage:\s*(rabbitmq|kafka|nats)\b', line, re.I)
        if m:
            res.append(make_hit("Queue", i, line, m.group(1)))
        m = re.search(r'\bimage:\s*(redis|postgres|mysql|mongo)\b', line, re.I)
        if m:
            res.append(make_hit("KV/Storage", i, line, m.group(1)))
        if re.match(r'^\s*ports\s*:', line):
            res.append(make_hit("External IO", i, line))
    return res
