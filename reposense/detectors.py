import os
import re
from .scanner import read_lines_limited
from .utils import snippet_with_context, clamp_text_bytes, clamp_lines
from .openapi import parse_openapi_json, parse_openapi_yaml_subset
from .parsers.gha import parse_workflow
from .parsers.dockerfile import parse_dockerfile
from .parsers.compose import parse_compose
from .parsers.sql_ddl import parse_sql_ddl
from .parsers.deps import parse_deps_manifest
from .parsers.ast_treesitter import parse_ast, run_matcher, lang_from_ext, AST_AVAILABLE
from .parsers.python_stdast import analyze_python_source, match_fastapi_routes, match_flask_routes, match_django_transaction_atomic, match_celery, match_cache
from .parsers.typescript_minimal import detect_ts_express_routes, detect_ts_nest_routes, detect_ts_prisma_transactions, detect_ts_typeorm_transactions, detect_ts_queue_dispatch, detect_ts_queue_consume, detect_ts_cache_ops
from .parsers.java_minimal import detect_java_spring_routes, detect_java_transactions, detect_java_queue_events, detect_java_db_ops
def run_detectors(ruleset, files, budget):
    results = []
    warnings = []
    max_findings = int((budget or {}).get("max_findings", 100000))
    py_cache = {}
    for f in files:
        if len(results) >= max_findings:
            warnings.append("max_findings_reached")
            break
        rr = read_lines_limited(f["path"], budget or {})
        if rr.get("binary"):
            warnings.append("binary_skipped")
            continue
        lines = rr.get("lines") or []
        encoding = rr.get("encoding")
        truncated = bool(rr.get("truncated"))
        ext = os.path.splitext(f["path"])[1].lower()
        if ext in (".ts", ".tsx", ".mts", ".cts"):
            ts_hits = []
            text_blob = "\n".join(lines)
            queue_hit_count = 0
            cache_hit_count = 0
            for h in detect_ts_express_routes(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                ts_hits.append({
                    "concept": "API",
                    "confidence": 0.82,
                    "rule_id": "ts_express_route_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "api_method": h["method"],
                    "api_path": h["path"],
                    "meta": {
                        "language": "typescript",
                        "framework": "express",
                        "ts.kind": "route_express",
                        "symbol": h.get("symbol") or "",
                        "http.method": h["method"],
                        "http.path": h["path"],
                        "evidence_strength": "typescript_l2",
                        "detector": "ts_express_route",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for h in detect_ts_nest_routes(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                ts_hits.append({
                    "concept": "API",
                    "confidence": 0.84,
                    "rule_id": "ts_nest_route_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "api_method": h["method"],
                    "api_path": h["path"],
                    "meta": {
                        "language": "typescript",
                        "framework": "nestjs",
                        "ts.kind": "route_nestjs",
                        "symbol": h.get("symbol") or "",
                        "controller_prefix": h.get("controller_prefix") or "/",
                        "http.method": h["method"],
                        "http.path": h["path"],
                        "evidence_strength": "typescript_l2",
                        "detector": "ts_nest_route",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for h in detect_ts_prisma_transactions(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                ts_hits.append({
                    "concept": "Transaction",
                    "confidence": 0.83,
                    "rule_id": "ts_prisma_transaction_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "meta": {
                        "language": "typescript",
                        "framework": "prisma",
                        "ts.kind": "transaction_prisma",
                        "tx.kind": "ts_prisma_transaction",
                        "transaction_style": h.get("transaction_style"),
                        "callee_expr": h.get("callee_expr"),
                        "evidence_strength": "typescript_l2",
                        "detector": "ts_prisma_transaction",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for h in detect_ts_typeorm_transactions(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                ts_hits.append({
                    "concept": "Transaction",
                    "confidence": 0.83,
                    "rule_id": "ts_typeorm_transaction_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "meta": {
                        "language": "typescript",
                        "framework": "typeorm",
                        "ts.kind": "transaction_typeorm",
                        "tx.kind": "ts_typeorm_transaction",
                        "transaction_style": h.get("transaction_style"),
                        "callee_expr": h.get("callee_expr"),
                        "evidence_strength": "typescript_l2",
                        "detector": "ts_typeorm_transaction",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for h in detect_ts_queue_dispatch(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                queue_hit_count += 1
                ts_hits.append({
                    "concept": "Queue",
                    "confidence": 0.81,
                    "rule_id": "ts_queue_dispatch_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "meta": {
                        "language": "typescript",
                        "framework": h.get("framework") or "bullmq",
                        "ts.kind": "queue_dispatch",
                        "queue.kind": "ts_queue_dispatch",
                        "queue_name": h.get("queue_name") or "",
                        "queue.task": h.get("job_name") or "",
                        "job_name": h.get("job_name") or "",
                        "callee_expr": h.get("callee_expr"),
                        "evidence_strength": "typescript_l2",
                        "detector": "ts_queue_dispatch",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for h in detect_ts_queue_consume(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                queue_hit_count += 1
                ts_hits.append({
                    "concept": "Queue",
                    "confidence": 0.81,
                    "rule_id": "ts_queue_consume_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "meta": {
                        "language": "typescript",
                        "framework": h.get("framework") or "bullmq",
                        "ts.kind": "queue_consume",
                        "queue.kind": "ts_queue_consume",
                        "queue_name": h.get("queue_name") or "",
                        "queue.task": h.get("job_name") or "",
                        "job_name": h.get("job_name") or "",
                        "consumer_style": h.get("consumer_style") or "",
                        "callee_expr": h.get("callee_expr"),
                        "evidence_strength": "typescript_l2",
                        "detector": "ts_queue_consume",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for h in detect_ts_cache_ops(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                cache_hit_count += 1
                ts_hits.append({
                    "concept": "Cache",
                    "confidence": 0.8,
                    "rule_id": "ts_cache_ops_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "meta": {
                        "language": "typescript",
                        "framework": h.get("framework") or "redis",
                        "ts.kind": "cache_op",
                        "cache.backend": h.get("framework") or "redis",
                        "cache.op": h.get("cache_op") or "",
                        "cache.kind": h.get("event_kind") or "",
                        "key_literal": h.get("key_literal") or "",
                        "key_expr": h.get("key_expr") or "",
                        "callee_expr": h.get("callee_expr"),
                        "evidence_strength": "typescript_l2",
                        "detector": "ts_cache_ops",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for it in ts_hits:
                if len(results) >= max_findings:
                    warnings.append("max_findings_reached")
                    break
                results.append(it)
            has_bull_hint = ("bullmq" in text_blob.lower()) or ("from 'bull'" in text_blob.lower()) or ('from "bull"' in text_blob.lower())
            has_redis_hint = ("ioredis" in text_blob.lower()) or ("redis" in text_blob.lower())
            if has_bull_hint and queue_hit_count == 0:
                warnings.append({"type": "unsupported_detected", "language": "typescript", "framework": "bullmq", "path": f["path"], "reason": "saw_bull_import_but_no_explicit_worker_or_add_pattern"})
            if has_redis_hint and cache_hit_count == 0:
                warnings.append({"type": "unsupported_detected", "language": "typescript", "framework": "redis", "path": f["path"], "reason": "saw_redis_hint_but_no_explicit_cache_op_pattern"})
        if ext == ".java":
            java_hits = []
            for h in detect_java_spring_routes(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                java_hits.append({
                    "concept": "API",
                    "confidence": 0.84,
                    "rule_id": "java_spring_route_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "api_method": h.get("method"),
                    "api_path": h.get("path"),
                    "meta": {
                        "language": "java",
                        "framework": h.get("framework") or "spring",
                        "java.kind": "route_spring",
                        "http.method": h.get("method"),
                        "http.path": h.get("path"),
                        "controller_class": h.get("controller_class") or "",
                        "handler_method": h.get("handler_method") or "",
                        "annotation_kind": h.get("annotation_kind") or "",
                        "scope": {
                            "kind": "function",
                            "name": h.get("handler_method") or "",
                            "start_line": s,
                            "end_line": e,
                        },
                        "evidence_strength": "java_l2",
                        "source_kind": "java_l2",
                        "detector": "java_spring_route",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for h in detect_java_transactions(lines):
                s = int(h["start_line"])
                e = int(h["end_line"])
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                scope_kind = h.get("scope") or "method"
                java_hits.append({
                    "concept": "Transaction",
                    "confidence": 0.83,
                    "rule_id": "java_transactional_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "meta": {
                        "language": "java",
                        "framework": h.get("framework") or "spring",
                        "java.kind": "transaction_transactional",
                        "tx.kind": "java_transactional",
                        "transaction_style": h.get("transaction_style") or "@Transactional",
                        "scope_kind": scope_kind,
                        "class_name": h.get("class_name") or "",
                        "method_name": h.get("method_name") or "",
                        "annotation_source": h.get("annotation_source") or "unknown",
                        "scope": {
                            "kind": "class" if scope_kind == "class" else "function",
                            "name": (h.get("class_name") or "") if scope_kind == "class" else (h.get("method_name") or ""),
                            "start_line": s,
                            "end_line": e,
                        },
                        "evidence_strength": "java_l2",
                        "source_kind": "java_l2",
                        "detector": "java_transactional",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            jq = detect_java_queue_events(lines)
            for h in (jq.get("events") or []):
                s = int(h.get("start_line") or 0)
                e = int(h.get("end_line") or s)
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                if h.get("event_kind") == "queue.consume":
                    java_hits.append({
                        "concept": "Queue",
                        "confidence": float(h.get("confidence") or 0.82),
                        "rule_id": "java_queue_consume_l2",
                        "rule_version": 1,
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": s,
                        "end_line": e,
                        "snippet": sn,
                        "meta": {
                            "language": "java",
                            "framework": h.get("framework") or "spring_kafka",
                            "java.kind": "queue_consume",
                            "queue.kind": "java_queue_consume",
                            "queue.system": h.get("queue_system") or "",
                            "queue_name": h.get("queue_name") or "",
                            "topic_name": h.get("topic_name") or "",
                            "listener_style": h.get("listener_style") or "",
                            "queue.task": h.get("topic_name") or h.get("queue_name") or "",
                            "class_name": h.get("class_name") or "",
                            "method_name": h.get("method_name") or "",
                            "scope": {"kind": "function", "name": h.get("method_name") or "", "start_line": s, "end_line": e},
                            "evidence_strength": "java_l2",
                            "source_kind": "java_l2",
                            "detector": "java_queue_consume",
                            "parse_level": "L2",
                            "encoding": encoding,
                            "truncated": truncated
                        }
                    })
                elif h.get("event_kind") == "queue.dispatch":
                    java_hits.append({
                        "concept": "Queue",
                        "confidence": float(h.get("confidence") or 0.82),
                        "rule_id": "java_queue_dispatch_l2",
                        "rule_version": 1,
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": s,
                        "end_line": e,
                        "snippet": sn,
                        "meta": {
                            "language": "java",
                            "framework": h.get("framework") or "spring_kafka",
                            "java.kind": "queue_dispatch",
                            "queue.kind": "java_queue_dispatch",
                            "queue.system": h.get("queue_system") or "",
                            "queue_name": h.get("queue_name") or "",
                            "topic_name": h.get("topic_name") or "",
                            "exchange": h.get("exchange") or "",
                            "routing_key": h.get("routing_key") or "",
                            "dispatch_style": h.get("dispatch_style") or "",
                            "callee_expr": h.get("callee_expr") or "",
                            "queue.task": h.get("topic_name") or h.get("queue_name") or "",
                            "class_name": h.get("class_name") or "",
                            "method_name": h.get("method_name") or "",
                            "scope": {"kind": "module", "name": "", "start_line": s, "end_line": e},
                            "evidence_strength": "java_l2",
                            "source_kind": "java_l2",
                            "detector": "java_queue_dispatch",
                            "parse_level": "L2",
                            "encoding": encoding,
                            "truncated": truncated
                        }
                    })
            for u in (jq.get("unsupported") or []):
                uu = dict(u)
                uu["path"] = f["path"]
                uu["line_start"] = int(uu.get("line_start") or 0)
                warnings.append(uu)
            for h in detect_java_db_ops(lines):
                s = int(h.get("start_line") or 0)
                e = int(h.get("end_line") or s)
                sn = snippet_with_context(lines, s, e, 8)
                sn = clamp_text_bytes(clamp_lines(sn, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                java_hits.append({
                    "concept": "DB",
                    "confidence": float(h.get("confidence") or 0.8),
                    "rule_id": "java_db_ops_l2",
                    "rule_version": 1,
                    "parse_level": "L2",
                    "path": f["path"],
                    "start_line": s,
                    "end_line": e,
                    "snippet": sn,
                    "meta": {
                        "language": "java",
                        "framework": "jpa" if str(h.get("db_style") or "").startswith(("jpa", "entity_manager")) else "mybatis",
                        "java.kind": "db_op",
                        "db.kind": h.get("event_kind"),
                        "db.op": h.get("db_op") or "",
                        "db_style": h.get("db_style") or "",
                        "entity_hint": h.get("entity_hint") or "",
                        "repo_symbol": h.get("repo_symbol") or "",
                        "mapper_symbol": h.get("mapper_symbol") or "",
                        "statement_hint": h.get("statement_hint") or "",
                        "callee_expr": h.get("callee_expr") or "",
                        "class_name": h.get("class_name") or "",
                        "method_name": h.get("method_name") or "",
                        "scope": {"kind": "module", "name": "", "start_line": s, "end_line": e},
                        "evidence_strength": "java_l2",
                        "source_kind": "java_l2",
                        "detector": "java_db_ops",
                        "parse_level": "L2",
                        "encoding": encoding,
                        "truncated": truncated
                    }
                })
            for it in java_hits:
                if len(results) >= max_findings:
                    warnings.append("max_findings_reached")
                    break
                results.append(it)
        level_map = {}
        for rule in ruleset["rules"]:
            globs = rule.get("globs", rule.get("include_globs", []))
            exclude_globs = rule.get("exclude_globs", [])
            if globs and ("**/*" not in globs):
                ext = os.path.splitext(f["path"])[1].lower()
                allowed_exts = [g.split(".")[-1].lower() for g in globs if g.startswith("**/*.")]
                if allowed_exts and ext.strip(".") not in allowed_exts and not any(glob_match(f["path"], g) for g in globs):
                    continue
                if not allowed_exts and not any(glob_match(f["path"], g) for g in globs):
                    continue
            if exclude_globs and any(glob_match(f["path"], g) for g in exclude_globs):
                continue
            parse_level = rule.get("parse_level", "L1")
            conf_base = float(rule.get("confidence_base", 0.3))
            kind = rule.get("kind", "text")
            if kind == "openapi":
                ext = os.path.splitext(f["path"])[1].lower()
                apis = []
                text = "\n".join(lines)
                if ext == ".json":
                    apis = parse_openapi_json(text)
                if ext in [".yaml", ".yml"]:
                    apis = parse_openapi_yaml_subset(text)
                for m, pth in apis:
                    results.append({
                        "concept": rule.get("concept", "API"),
                        "confidence": max(conf_base, 0.85),
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": 1,
                        "end_line": 1,
                        "snippet": f"{m} {pth}",
                        "api_method": m,
                        "api_path": pth,
                        "meta": {"http.method": m, "http.path": pth, "evidence_strength": "openapi", "encoding": encoding, "truncated": truncated}
                    })
                continue
            if kind == "sql_tx":
                ext = os.path.splitext(f["path"])[1].lower()
                if ext != ".sql":
                    continue
                begin_line = None
                commit_line = None
                for i, line in enumerate(lines, start=1):
                    u = line.strip().upper()
                    if begin_line is None and u.startswith("BEGIN"):
                        begin_line = i
                    if u.startswith("COMMIT"):
                        commit_line = i
                if begin_line and commit_line and begin_line <= commit_line:
                    snip = snippet_with_context(lines, begin_line, commit_line, int(rule.get("snippet", 5)))
                    snip = clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                    results.append({
                        "concept": rule.get("concept", "Transaction"),
                        "confidence": max(conf_base, 0.8),
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": rule.get("parse_level", "L2"),
                        "path": f["path"],
                        "start_line": begin_line,
                        "end_line": commit_line,
                        "snippet": snip,
                        "meta": {"tx.kind": "sql_begin_commit", "evidence_strength": "text", "encoding": encoding, "truncated": truncated}
                    })
                continue
            if kind == "gha":
                text = "\n".join(lines)
                hits = parse_workflow(text)
                for concept, s, e, snip in hits:
                    results.append({
                        "concept": concept,
                        "confidence": max(conf_base, 0.65 if concept == "External IO" else 0.6),
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": s,
                        "end_line": e,
                        "snippet": clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                    })
                continue
            if kind == "dockerfile":
                text = "\n".join(lines)
                hits = parse_dockerfile(text)
                for concept, s, e, snip in hits:
                    results.append({
                        "concept": concept,
                        "confidence": max(conf_base, 0.6),
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": s,
                        "end_line": e,
                        "snippet": clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                    })
                continue
            if kind == "compose":
                text = "\n".join(lines)
                hits = parse_compose(text)
                for concept, s, e, snip, meta in hits:
                    results.append({
                        "concept": concept,
                        "confidence": max(conf_base, 0.6),
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": s,
                        "end_line": e,
                        "snippet": clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes")),
                        "meta": {"encoding": encoding, "truncated": truncated, **(meta or {})}
                    })
                continue
            if kind == "sql_ddl":
                text = "\n".join(lines)
                hits = parse_sql_ddl(text)
                for concept, s, e, snip, meta in hits:
                    results.append({
                        "concept": concept,
                        "confidence": max(conf_base, 0.65 if concept == "Index" else 0.6),
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": s,
                        "end_line": e,
                        "snippet": clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes")),
                        "meta": {"encoding": encoding, "truncated": truncated, **(meta or {})}
                    })
                continue
            if kind == "deps":
                text = "\n".join(lines)
                hits = parse_deps_manifest(f["path"], text)
                for concept, s, e, snip, meta in hits:
                    results.append({
                        "concept": concept,
                        "confidence": min(max(conf_base, 0.5), 0.65),
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": "L2",
                        "path": f["path"],
                        "start_line": s,
                        "end_line": e,
                        "snippet": clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes")),
                        "meta": {"encoding": encoding, "truncated": truncated, **(meta or {})}
                    })
                continue
            if kind == "ast":
                lang = lang_from_ext(f["path"])
                text = "\n".join(lines)
                tree, w = parse_ast(f["path"], text, lang, budget)
                if w:
                    warnings.extend(w)
                if not tree:
                    continue
                matcher = rule.get("matcher")
                hits = run_matcher(matcher, tree, text.encode("utf-8"), lang)
                for h in hits:
                    meta = {"ast.matcher": matcher, "evidence_strength": "ast"}
                    if h.get("api_method"):
                        meta["http.method"] = h["api_method"]
                    if h.get("api_path"):
                        meta["http.path"] = h["api_path"]
                    conf = float(rule.get("confidence", max(conf_base, 0.84)))
                    results.append({
                        "concept": rule.get("concept"),
                        "confidence": conf,
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": "L3",
                        "path": f["path"],
                        "start_line": h["start_line"],
                        "end_line": h["end_line"],
                        "snippet": clamp_text_bytes(clamp_lines(h["snippet"], (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes")),
                        "meta": {"encoding": encoding, "truncated": truncated, **meta},
                        "api_method": h.get("api_method"),
                        "api_path": h.get("api_path"),
                        "node_type": h["node"].type if h.get("node") else None
                    })
                continue
            if kind == "python_ast":
                ext = os.path.splitext(f["path"])[1].lower()
                if ext != ".py":
                    continue
                text = "\n".join(lines)
                ctx = py_cache.get(f["path"])
                if ctx is None:
                    try:
                        ctx = analyze_python_source(text)
                        py_cache[f["path"]] = ctx
                    except Exception as e:
                        warnings.append({"type": "ast_parse_error", "path": f["path"], "reason": "ast_parse_error", "error": str(e), "encoding": encoding, "truncated": truncated})
                        py_cache[f["path"]] = False
                        continue
                if ctx is False:
                    continue
                matcher = rule.get("matcher")
                hits = []
                if matcher == "py_fastapi_route":
                    hits = match_fastapi_routes(ctx)
                elif matcher == "py_flask_route":
                    hits = match_flask_routes(ctx)
                elif matcher == "py_django_atomic":
                    hits = match_django_transaction_atomic(ctx)
                elif matcher == "py_celery":
                    hits = match_celery(ctx)
                elif matcher == "py_cache":
                    hits = match_cache(ctx)
                for h in hits:
                    meta = {"ast.matcher": matcher, "evidence_strength": "python_ast", "encoding": encoding, "truncated": truncated}
                    if h.get("api_method"):
                        meta["http.method"] = h["api_method"]
                    if h.get("api_path"):
                        meta["http.path"] = h["api_path"]
                    if h.get("kind"):
                        meta["python.kind"] = h["kind"]
                    if h.get("scope"):
                        sc = h.get("scope") or {}
                        meta["scope"] = {
                            "kind": sc.get("kind"),
                            "name": sc.get("name"),
                            "start_line": sc.get("start"),
                            "end_line": sc.get("end"),
                        }
                    if h.get("cache.backend"):
                        meta["cache.backend"] = h.get("cache.backend")
                    if h.get("cache.op"):
                        meta["cache.op"] = h.get("cache.op")
                    if h.get("queue.kind"):
                        meta["queue.kind"] = h.get("queue.kind")
                    if h.get("queue.task"):
                        meta["queue.task"] = h.get("queue.task")
                    if h.get("tx.kind"):
                        meta["tx.kind"] = h.get("tx.kind")
                    conf = float(rule.get("confidence", max(conf_base, 0.86)))
                    snip = snippet_with_context(lines, int(h["start_line"]), int(h["end_line"]), int(rule.get("snippet", 8)))
                    snip = clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                    results.append({
                        "concept": rule.get("concept"),
                        "confidence": conf,
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": rule.get("parse_level", "L3"),
                        "path": f["path"],
                        "start_line": int(h["start_line"]),
                        "end_line": int(h["end_line"]),
                        "snippet": snip,
                        "meta": meta,
                        "api_method": h.get("api_method"),
                        "api_path": h.get("api_path"),
                        "node_type": "python_ast"
                    })
                    if len(results) >= max_findings:
                        warnings.append("max_findings_reached")
                        break
                continue
            # text detector with signals/gating/scoring
            text_blob = "\n".join(lines)
            meta_cfg = rule.get("meta") or {}
            sig = (meta_cfg.get("signals") or {})
            gating = (meta_cfg.get("gating") or {})
            scoring = (meta_cfg.get("scoring") or {})
            if sig or gating or scoring:
                hits = []
                signals_hit = []
                markers_hit = []
                anti_hit = []
                def compile_kw(kw):
                    return re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE | re.MULTILINE)
                strong = [(kw, compile_kw(kw)) for kw in (sig.get("strong") or [])]
                medium = [(kw, compile_kw(kw)) for kw in (sig.get("medium") or [])]
                negative = [(kw, compile_kw(kw)) for kw in (sig.get("negative") or [])]
                # gather matches
                def collect(group, weight):
                    for sid, rgx in group:
                        for m in rgx.finditer(text_blob):
                            start = text_blob.count("\n", 0, m.start()) + 1
                            end = text_blob.count("\n", 0, m.end()) + 1
                            snip = snippet_with_context(lines, start, end, int(rule.get("snippet", 10)))
                            snip = clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                            signals_hit.append({"id": sid, "weight": weight, "excerpt": snip})
                            hits.append((start, end, snip))
                            # marker record
                            if weight > 0:
                                markers_hit.append(sid)
                            else:
                                anti_hit.append(sid)
                collect(strong, float(scoring.get("weight_strong", 0.5)))
                collect(medium, float(scoring.get("weight_medium", 0.35)))
                collect(negative, -abs(float(scoring.get("penalty_negative", 0.3))))
                # gating
                req = gating.get("required_markers_all") or []
                anti_block = set(gating.get("anti_patterns_block_if") or [])
                gating_passed = True
                if req:
                    for rmk in req:
                        if rmk not in markers_hit:
                            gating_passed = False
                            break
                if gating_passed and anti_block and any(a in anti_block for a in anti_hit):
                    gating_passed = False
                # score
                score = 0.0
                for sh in signals_hit:
                    score += float(sh["weight"])
                # clamp 0..1 and mix with base
                score = max(0.0, min(1.0, score))
                conf = score if score > conf_base else conf_base
                if gating_passed and hits:
                    s0 = hits[0]
                    results.append({
                        "concept": rule.get("concept"),
                        "confidence": conf,
                        "rule_id": rule.get("rule_id"),
                        "rule_version": rule.get("rule_version"),
                        "parse_level": parse_level,
                        "path": f["path"],
                        "start_line": s0[0],
                        "end_line": s0[1],
                        "snippet": s0[2],
                        "meta": {
                            "signals_hit": signals_hit,
                            "markers_hit": sorted(list(set(markers_hit))),
                            "anti_patterns_hit": sorted(list(set(anti_hit))),
                            "score": score,
                            "gating_passed": True,
                            "evidence_strength": "text",
                            "encoding": encoding,
                            "truncated": truncated
                        }
                    })
                else:
                    warnings.append("text_gating_blocked")
                continue
            # legacy text regex patterns
            if rule.get("patterns"):
                for pat in rule["patterns"]:
                    val = pat.get("value") or pat.get("regex")
                    if (pat.get("type") == "regex") or val:
                        try:
                            regex = re.compile(val if val else pat["value"], re.IGNORECASE | re.MULTILINE)
                        except Exception:
                            continue
                        for m in regex.finditer(text_blob):
                            start = text_blob.count("\n", 0, m.start()) + 1
                            end = text_blob.count("\n", 0, m.end()) + 1
                            snip = snippet_with_context(lines, start, end, int(rule.get("snippet", 10)))
                            snip = clamp_text_bytes(clamp_lines(snip, (budget or {}).get("max_snippet_lines")), (budget or {}).get("max_snippet_bytes"))
                            results.append({
                                "concept": rule.get("concept"),
                                "confidence": conf_base,
                                "rule_id": rule.get("rule_id"),
                                "rule_version": rule.get("rule_version"),
                                "parse_level": parse_level,
                                "path": f["path"],
                                "start_line": start,
                                "end_line": end,
                                "snippet": snip,
                                "meta": {"encoding": encoding, "truncated": truncated, "evidence_strength": "text"}
                            })
    return results, warnings
def glob_match(path, pattern):
    from fnmatch import fnmatch
    norm = path.replace("\\", "/")
    return fnmatch(norm, pattern)

