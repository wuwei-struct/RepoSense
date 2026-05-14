import ast


def _node_lines(node):
    s = getattr(node, "lineno", 1) or 1
    e = getattr(node, "end_lineno", None) or s
    return int(s), int(e)


def _const_str(expr, consts):
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.Name):
        return consts.get(expr.id)
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        a = _const_str(expr.left, consts)
        b = _const_str(expr.right, consts)
        if isinstance(a, str) and isinstance(b, str):
            return a + b
    return None


def _collect_module_consts(mod):
    out = {}
    for n in getattr(mod, "body", []) or []:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = _const_str(n.value, out)
            if isinstance(v, str):
                out[n.targets[0].id] = v
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            v = _const_str(n.value, out)
            if isinstance(v, str):
                out[n.target.id] = v
    return out


def _get_call_name(call):
    if not isinstance(call, ast.Call):
        return None
    fn = call.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return None


def _get_attr_call_target_and_name(call):
    if not isinstance(call, ast.Call):
        return None, None
    fn = call.func
    if isinstance(fn, ast.Attribute):
        if isinstance(fn.value, ast.Name):
            return fn.value.id, fn.attr
    return None, None


def analyze_python_source(src_text):
    mod = ast.parse(src_text)
    consts = _collect_module_consts(mod)
    scopes = []
    for n in ast.walk(mod):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            s, e = _node_lines(n)
            nm = getattr(n, "name", "")
            scopes.append({"kind": "function" if not isinstance(n, ast.ClassDef) else "class", "name": nm, "start": s, "end": e})
    scopes.append({"kind": "module", "name": "", "start": 1, "end": max([getattr(mod, "end_lineno", None) or 1] + [sc["end"] for sc in scopes])})
    fastapi_apps = set()
    fastapi_routers = set()
    flask_apps = set()
    flask_blueprints = set()
    celery_apps = set()
    redis_instances = set()
    for n in getattr(mod, "body", []) or []:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Call):
            tgt = n.targets[0].id
            cn = _get_call_name(n.value)
            if cn == "FastAPI":
                fastapi_apps.add(tgt)
            if cn == "APIRouter":
                fastapi_routers.add(tgt)
            if cn == "Flask":
                flask_apps.add(tgt)
            if cn == "Blueprint":
                flask_blueprints.add(tgt)
            if cn == "Celery":
                celery_apps.add(tgt)
            if isinstance(n.value.func, ast.Attribute) and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id in ("redis",):
                if n.value.func.attr in ("Redis", "StrictRedis"):
                    redis_instances.add(tgt)
    return {
        "mod": mod,
        "consts": consts,
        "scopes": scopes,
        "fastapi_apps": fastapi_apps,
        "fastapi_routers": fastapi_routers,
        "flask_apps": flask_apps,
        "flask_blueprints": flask_blueprints,
        "celery_apps": celery_apps,
        "redis_instances": redis_instances,
    }

def _scope_for_line(ctx, line):
    best = None
    for sc in ctx["scopes"]:
        if sc["start"] <= line <= sc["end"]:
            if best is None or (sc["end"] - sc["start"] < best["end"] - best["start"]):
                best = sc
    return best or {"kind": "module", "name": "", "start": 1, "end": line}


def match_fastapi_routes(ctx):
    out = []
    mod = ctx["mod"]
    consts = ctx["consts"]
    methods = {"get", "post", "put", "delete", "patch", "options", "head"}
    for n in ast.walk(mod):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list or []:
                if not isinstance(d, ast.Call):
                    continue
                base, m = _get_attr_call_target_and_name(d)
                if not base or m not in methods:
                    continue
                if base not in ctx["fastapi_apps"] and base not in ctx["fastapi_routers"]:
                    continue
                p = None
                if d.args:
                    p = _const_str(d.args[0], consts)
                if not p:
                    for kw in d.keywords or []:
                        if kw.arg in ("path",):
                            p = _const_str(kw.value, consts)
                if not p:
                    continue
                s, e = _node_lines(d)
                sc = _scope_for_line(ctx, s)
                out.append({"api_method": m.upper(), "api_path": p, "start_line": s, "end_line": e, "node": d, "scope": sc})
    return out


def match_flask_routes(ctx):
    out = []
    mod = ctx["mod"]
    consts = ctx["consts"]
    for n in ast.walk(mod):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list or []:
                if not isinstance(d, ast.Call):
                    continue
                base, attr = _get_attr_call_target_and_name(d)
                if not base or attr != "route":
                    continue
                if base not in ctx["flask_apps"] and base not in ctx["flask_blueprints"]:
                    continue
                p = _const_str(d.args[0], consts) if d.args else None
                if not p:
                    continue
                ms = None
                for kw in d.keywords or []:
                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        vals = []
                        for el in kw.value.elts:
                            v = _const_str(el, consts)
                            if isinstance(v, str):
                                vals.append(v.upper())
                        if vals:
                            ms = vals
                if not ms:
                    ms = ["GET"]
                s, e = _node_lines(d)
                sc = _scope_for_line(ctx, s)
                for m in ms:
                    out.append({"api_method": m, "api_path": p, "start_line": s, "end_line": e, "node": d, "scope": sc})
    return out


def match_django_transaction_atomic(ctx):
    out = []
    mod = ctx["mod"]
    for n in ast.walk(mod):
        if isinstance(n, ast.With):
            for it in n.items or []:
                ce = it.context_expr
                if isinstance(ce, ast.Call) and isinstance(ce.func, ast.Attribute) and isinstance(ce.func.value, ast.Name):
                    if ce.func.value.id == "transaction" and ce.func.attr == "atomic":
                        s, e = _node_lines(n)
                        sc = _scope_for_line(ctx, s)
                        out.append({"kind":"django_atomic","tx.kind":"django_atomic","start_line": s, "end_line": e, "node": n, "scope": sc})
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list or []:
                base = None
                attr = None
                if isinstance(d, ast.Attribute) and isinstance(d.value, ast.Name):
                    base = d.value.id
                    attr = d.attr
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name):
                    base = d.func.value.id
                    attr = d.func.attr
                if base == "transaction" and attr == "atomic":
                    s, e = _node_lines(d)
                    sc = _scope_for_line(ctx, s)
                    out.append({"kind":"django_atomic","tx.kind":"django_atomic","start_line": s, "end_line": e, "node": d, "scope": sc})
    return out


def match_celery(ctx):
    out = []
    mod = ctx["mod"]
    task_defs = []
    for n in ast.walk(mod):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_task = False
            for d in n.decorator_list or []:
                if isinstance(d, ast.Name) and d.id == "shared_task":
                    is_task = True
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "shared_task":
                    is_task = True
                if isinstance(d, ast.Attribute) and isinstance(d.value, ast.Name) and d.value.id in ctx["celery_apps"] and d.attr == "task":
                    is_task = True
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name) and d.func.value.id in ctx["celery_apps"] and d.func.attr == "task":
                    is_task = True
            if is_task:
                s, e = _node_lines(n)
                sc = _scope_for_line(ctx, s)
                task_defs.append((n.name, s, e, n))
                out.append({"kind": "celery_task", "start_line": s, "end_line": e, "node": n, "scope": sc})
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr in ("delay", "apply_async"):
                s, e = _node_lines(n)
                sc = _scope_for_line(ctx, s)
                task = None
                if isinstance(n.func.value, ast.Name):
                    task = n.func.value.id
                out.append({"kind": "celery_dispatch", "queue.kind": f"celery_{n.func.attr}", "queue.task": task, "start_line": s, "end_line": e, "node": n, "scope": sc})
    return out


def match_cache(ctx):
    out = []
    mod = ctx["mod"]
    cache_ops = {"get", "set", "add", "delete", "incr", "decr"}
    redis_ops = {"get", "set", "setnx", "hget", "hset", "lpush", "rpush", "publish", "xadd"}
    for n in ast.walk(mod):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
            base = n.func.value.id
            op = n.func.attr
            if base == "cache" and op in cache_ops:
                s, e = _node_lines(n)
                sc = _scope_for_line(ctx, s)
                out.append({"kind": "django_cache_op", "cache.backend": "django_cache", "cache.op": op, "start_line": s, "end_line": e, "node": n, "scope": sc})
            if (base in ctx["redis_instances"] or "redis" in base.lower()) and op in redis_ops:
                s, e = _node_lines(n)
                sc = _scope_for_line(ctx, s)
                out.append({"kind": "redis_op", "cache.backend": "redis", "cache.op": op, "start_line": s, "end_line": e, "node": n, "scope": sc})
    return out
