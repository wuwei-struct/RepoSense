import re


def normalize_path(path):
    s = str(path or "").strip()
    if not s:
        return "/"
    if "?" in s:
        s = s.split("?", 1)[0]
    if "#" in s:
        s = s.split("#", 1)[0]
    s = s.replace("\\", "/")
    s = re.sub(r"/+", "/", s)
    s = re.sub(r"<([a-zA-Z_][a-zA-Z0-9_]*)>", r"{\1}", s)
    s = re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", r"{\1}", s)
    s = re.sub(r"\{([^\}]+)\}", lambda m: "{" + m.group(1).strip() + "}", s)
    if not s.startswith("/"):
        s = "/" + s
    if s != "/" and s.endswith("/"):
        s = s[:-1]
    return s


def split_segments(path):
    n = normalize_path(path)
    if n == "/":
        return []
    return [x for x in n.strip("/").split("/") if x != ""]


def is_placeholder(seg):
    if re.fullmatch(r"\{[^{}]+\}", seg or ""):
        return True
    if re.fullmatch(r":[a-zA-Z_][a-zA-Z0-9_]*", seg or ""):
        return True
    return False


def template_match(endpoint_path, caller_path):
    e = split_segments(endpoint_path)
    c = split_segments(caller_path)
    if len(e) != len(c):
        return False
    used = False
    for es, cs in zip(e, c):
        if is_placeholder(es):
            used = True
            continue
        if es != cs:
            return False
    return used
