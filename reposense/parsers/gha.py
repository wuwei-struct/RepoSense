import re
def parse_workflow(text):
    lines = text.splitlines()
    res = []
    for i, line in enumerate(lines, 1):
        if re.search(r'^\s*on:\s*', line):
            pass
        if re.search(r'cron:\s*["\']?[^"\']+["\']?', line, re.I):
            res.append(("Scheduling", i, i, "cron"))
        if re.search(r'\${{\s*secrets\.[A-Za-z0-9_]+\s*}}', line):
            res.append(("Secrets/Config", i, i, "secrets"))
        if re.search(r'^\s*env\s*:', line):
            res.append(("Secrets/Config", i, i, "env"))
        if re.search(r'uses:\s*actions/cache@', line, re.I):
            res.append(("Cache", i, i, "cache"))
        if re.search(r'^\s*concurrency\s*:', line):
            res.append(("Concurrency", i, i, "concurrency"))
        if re.search(r'uses:\s*actions/checkout@', line, re.I) or re.search(r'uses:\s*actions/upload|actions/download', line, re.I) or re.search(r'\bcurl\b|\bwget\b', line, re.I):
            res.append(("External IO", i, i, "external"))
    return res

