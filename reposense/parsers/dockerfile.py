import re
def parse_dockerfile(text):
    lines = text.splitlines()
    res = []
    for i, line in enumerate(lines, 1):
        if re.match(r'^\s*(COPY|ADD)\b', line, re.I) or re.match(r'^\s*VOLUME\b', line, re.I):
            res.append(("FileSystem", i, i, line.strip()))
        if re.match(r'^\s*RUN\b', line, re.I) and re.search(r'\bcurl\b|\bwget\b|\bapt(-get)?\b|\byum\b|\bdnf\b|\bapk\b|\bgit\s+clone\b', line, re.I):
            res.append(("External IO", i, i, line.strip()))
        if re.match(r'^\s*(ENV|ARG)\b', line, re.I) and re.search(r'(secret|token|key|password)', line, re.I):
            res.append(("Secrets/Config", i, i, line.strip()))
    return res

