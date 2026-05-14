import re
def parse_sql_ddl(text):
    lines = text.splitlines()
    res = []
    for i, line in enumerate(lines, 1):
        m = re.search(r'\bCREATE\s+TABLE\s+([A-Za-z0-9_]+)', line, re.I)
        if m:
            res.append(("Storage", i, i, line.strip(), {"table_names": [m.group(1)]}))
        m = re.search(r'\bCREATE\s+INDEX\s+([A-Za-z0-9_]+)', line, re.I)
        if m:
            res.append(("Index", i, i, line.strip(), {"index_names": [m.group(1)]}))
    return res

