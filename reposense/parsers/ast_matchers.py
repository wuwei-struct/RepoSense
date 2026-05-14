def _node_lines(node, text):
    s = node.start_point[0] + 1
    e = node.end_point[0] + 1
    lines = text.decode("utf-8").splitlines()
    return s, e, "\n".join(lines[s-1:e])
def _is_string_node(n, lang):
    t = n.type
    if lang in ["javascript", "typescript"]:
        return t in ["string", "template_string"]
    if lang == "python":
        return t in ["string"]
    return False
def _text_of(n, text):
    return text[n.start_byte:n.end_byte].decode("utf-8")
def express_route(tree, source_bytes, lang):
    if lang not in ["javascript", "typescript"]:
        return []
    meths = {"get","post","put","delete","patch","options","head","all"}
    hits = []
    def walk(n):
        for ch in n.children:
            walk(ch)
        if n.type in ["call_expression"]:
            fn = None
            if hasattr(n, "child_by_field_name"):
                fn = n.child_by_field_name("function")
            if not fn or fn.type not in ["member_expression"]:
                return
            obj = fn.child_by_field_name("object")
            prop = fn.child_by_field_name("property")
            if not obj or not prop:
                return
            obj_name = _text_of(obj, source_bytes)
            method = _text_of(prop, source_bytes)
            if obj_name not in ["app","router"] or method.lower() not in meths:
                return
            args = n.child_by_field_name("arguments")
            if not args:
                return
            strlit = None
            for c in args.children:
                if _is_string_node(c, lang):
                    strlit = c
                    break
            if not strlit:
                return
            s,e,snip = _node_lines(n, source_bytes)
            hits.append({"node": n, "start_line": s, "end_line": e, "snippet": snip, "api_method": method.upper(), "api_path": _text_of(strlit, source_bytes).strip('"').strip("'"), "matcher": "express_route"})
    walk(tree.root_node)
    return hits
def fastapi_route(tree, source_bytes, lang):
    if lang != "python":
        return []
    meths = {"get","post","put","delete","patch","options","head"}
    hits = []
    def walk(n):
        for ch in n.children:
            walk(ch)
        if n.type == "decorated_definition":
            decs = [c for c in n.children if c.type == "decorator"]
            for d in decs:
                call = None
                for c in d.children:
                    if c.type in ["call"]:
                        call = c
                        break
                if not call:
                    continue
                fn = call.child_by_field_name("function")
                if not fn:
                    continue
                # attribute: app.get / router.post
                if fn.type != "attribute":
                    continue
                obj = fn.child_by_field_name("object")
                attr = fn.child_by_field_name("attribute")
                if not obj or not attr:
                    continue
                obj_name = _text_of(obj, source_bytes)
                method = _text_of(attr, source_bytes).lower()
                if obj_name not in ["app","router"] or method not in meths:
                    continue
                args = call.child_by_field_name("arguments")
                strlit = None
                if args:
                    for c in args.children:
                        if _is_string_node(c, lang):
                            strlit = c
                            break
                s,e,snip = _node_lines(d, source_bytes)
                path_val = _text_of(strlit, source_bytes).strip('"').strip("'") if strlit else ""
                hits.append({"node": d, "start_line": s, "end_line": e, "snippet": snip, "api_method": method.upper(), "api_path": path_val, "matcher": "fastapi_route"})
    walk(tree.root_node)
    return hits
def py_lock(tree, source_bytes, lang):
    if lang != "python":
        return []
    hits = []
    def walk(n):
        for ch in n.children:
            walk(ch)
        if n.type == "call":
            fn = n.child_by_field_name("function")
            if not fn:
                return
            if fn.type == "attribute":
                obj = fn.child_by_field_name("object")
                attr = fn.child_by_field_name("attribute")
                if obj and attr:
                    mod = _text_of(obj, source_bytes)
                    name = _text_of(attr, source_bytes)
                    if name == "Lock" and mod in ["threading","asyncio"]:
                        s,e,snip = _node_lines(n, source_bytes)
                        hits.append({"node": n, "start_line": s, "end_line": e, "snippet": snip, "lock_mod": mod, "matcher": "py_lock"})
    walk(tree.root_node)
    return hits
def js_concurrency(tree, source_bytes, lang):
    if lang not in ["javascript","typescript"]:
        return []
    hits = []
    def walk(n):
        for ch in n.children:
            walk(ch)
        if n.type == "call_expression":
            fn = n.child_by_field_name("function")
            if fn and fn.type == "member_expression":
                obj = fn.child_by_field_name("object")
                prop = fn.child_by_field_name("property")
                if obj and prop:
                    on = _text_of(obj, source_bytes)
                    pn = _text_of(prop, source_bytes)
                    if on == "Promise" and pn in ["all","race"]:
                        s,e,snip = _node_lines(n, source_bytes)
                        hits.append({"node": n, "start_line": s, "end_line": e, "snippet": snip, "method": pn, "matcher": "js_concurrency"})
    walk(tree.root_node)
    return hits
