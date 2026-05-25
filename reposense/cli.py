import argparse
import sys
import os
import json
from .scan import run_scan
from .report import show_report
from .query import run_query
from .verifier import run_verify
from .explain import run_explain
from .diff import run_diff
from .sarif import run_export_sarif
from .gate import run_gate_policy
from .rules_qa import run_rules_check, run_rules_coverage
from .selfcheck import run_selfcheck
from .learn.concept_graph import load_concept_graph, ConceptGraph, default_concept_graph_path
from .learn.concept_graph import load_concept_map, check_graph_and_map
from .learn.site_builder import build_site
from .learn.case_extractor import extract_cases
from .learn.extract_cases import run_extract_cases
from .learn.library import library_init, library_add, library_stats, library_verify
from .learn.path import toposort, pick_cases_for_concepts
from .learn.ui.serve import run_learn_ui_server
from .shared.case_library.store import CaseLibraryStore
from .context_pack import run_context_pack
from .arch_views import build_arch_views
from .arch_verify import verify_arch_views
from .context_brief import build_brief
from .context_diff import build_context_diff
from .specs import export_graph_json, check_specs, compile_rulesets
from .cases_check import cases_check
from .analysis.ai.pattern_export import export_patterns
from .analysis.ai.summary_export import export_ai_summary
from .analysis.ai.drilldown_export import export_drilldown
from .analysis.ai.explain_export import export_ai_explain
from .analysis.ai.risks_export import export_ai_risks
from .analysis.ai.ask_export import export_ai_ask
from .analysis.reports.backend_verifier_report import export_backend_verifier_report
def main():
    if "--version" in sys.argv or "-V" in sys.argv:
        try:
            from . import __version__ as v
        except Exception:
            v = "0.1.0"
        print(v)
        sys.exit(0)
    parser = argparse.ArgumentParser(prog="reposense")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    p_scan = subparsers.add_parser("scan")
    p_scan.add_argument("input")
    p_scan.add_argument("--out", required=True)
    p_scan.add_argument("--ruleset", required=True)
    p_scan.add_argument("--budget", required=True)
    p_scan.add_argument("--base")
    p_scan.add_argument("--specs")
    p_show = subparsers.add_parser("show")
    p_show.add_argument("run_dir")
    p_show.add_argument("--open", action="store_true")
    p_query = subparsers.add_parser("query")
    p_query.add_argument("run_dir")
    p_query.add_argument("entity", choices=["concepts", "findings", "evidence", "events", "graph"])
    p_query.add_argument("--json", action="store_true")
    p_verify = subparsers.add_parser("verify")
    p_verify.add_argument("run_dir")
    p_verify.add_argument("--json", action="store_true")
    p_verify.add_argument("--strict", action="store_true")
    p_explain = subparsers.add_parser("explain")
    p_explain.add_argument("run_dir")
    p_explain.add_argument("subject", choices=["event","finding"])
    p_explain.add_argument("id")
    p_explain.add_argument("--json", action="store_true")
    p_diff = subparsers.add_parser("diff")
    p_diff.add_argument("runA")
    p_diff.add_argument("runB")
    p_diff.add_argument("--json", action="store_true")
    # baseline save and diff
    p_base = subparsers.add_parser("baseline")
    sub_b = p_base.add_subparsers(dest="b_sub")
    p_b_save = sub_b.add_parser("save")
    p_b_save.add_argument("run_dir")
    p_b_save.add_argument("--out", required=True)
    p_b_diff = subparsers.add_parser("bdiff")
    p_b_diff.add_argument("--base", required=True)
    p_b_diff.add_argument("--new", required=True)
    p_b_diff.add_argument("--out", required=True)
    p_b_diff.add_argument("--markdown")
    p_export = subparsers.add_parser("export")
    p_export.add_argument("format", choices=["sarif"])
    p_export.add_argument("run_dir")
    p_export.add_argument("--out", required=True)
    p_patch = subparsers.add_parser("patch")
    sub_patch = p_patch.add_subparsers(dest="patch_sub")
    p_p_exp = sub_patch.add_parser("exports")
    p_p_exp.add_argument("run_dir")
    p_ci = subparsers.add_parser("ci")
    sub_ci = p_ci.add_subparsers(dest="ci_sub")
    p_ci_run = sub_ci.add_parser("run")
    p_ci_run.add_argument("--repo")
    p_ci_run.add_argument("--profile", default="demo")
    p_ci_run.add_argument("--out")
    p_ci_run.add_argument("--ruleset")
    p_ci_run.add_argument("--budget")
    p_ci_run.add_argument("--gate")
    p_ci_run.add_argument("--with-context-pack", action="store_true")
    p_ci_run.add_argument("--json", action="store_true")
    p_ci_run.add_argument("--baseline-in")
    p_ci_run.add_argument("--baseline-out")
    p_ci_run.add_argument("--redact", action="store_true")
    p_ci_run.add_argument("--no-redact", action="store_true")
    # ruleset info
    p_rs = subparsers.add_parser("ruleset")
    sub_rs = p_rs.add_subparsers(dest="rs_sub")
    p_rsi = sub_rs.add_parser("info")
    p_rsi.add_argument("ruleset_dir")
    p_rsi.add_argument("--json", action="store_true")
    # run info
    p_run = subparsers.add_parser("run")
    sub_run = p_run.add_subparsers(dest="run_sub")
    p_ri = sub_run.add_parser("info")
    p_ri.add_argument("run_dir")
    p_ri.add_argument("--json", action="store_true")
    p_rm = sub_run.add_parser("manifest")
    p_rm.add_argument("run_dir")
    p_rm.add_argument("--json", action="store_true")
    p_ru = sub_run.add_parser("upgrade")
    p_ru.add_argument("run_dir")
    p_ru.add_argument("--inplace", action="store_true")
    p_ru.add_argument("--out")
    p_ru.add_argument("--strict", action="store_true")
    p_ru.add_argument("--json", action="store_true")
    # docs check
    p_docs = subparsers.add_parser("docs")
    sub_docs = p_docs.add_subparsers(dest="docs_sub")
    p_dc = sub_docs.add_parser("check")
    p_gate = subparsers.add_parser("gate")
    p_gate.add_argument("run_dir")
    p_gate.add_argument("--policy")
    p_gate.add_argument("--json", action="store_true")
    p_gate.add_argument("--gate", help="quality gate config path")
    p_gate.add_argument("--baseline")
    p_rules = subparsers.add_parser("rules")
    sub_r = p_rules.add_subparsers(dest="sub")
    p_rc = sub_r.add_parser("check")
    p_rc.add_argument("ruleset_dir")
    p_rc.add_argument("--json", action="store_true")
    p_cov = sub_r.add_parser("coverage")
    p_cov.add_argument("ruleset_dir")
    p_cov.add_argument("--fixtures", required=True)
    p_cov.add_argument("--json", action="store_true")
    p_self = subparsers.add_parser("selfcheck")
    p_self.add_argument("run_dir")
    p_self.add_argument("--policy")
    p_self.add_argument("--sarif", action="store_true")
    p_self.add_argument("--strict", action="store_true")
    p_ai = subparsers.add_parser("ai")
    sub_ai = p_ai.add_subparsers(dest="ai_sub")
    p_ai_patterns = sub_ai.add_parser("patterns")
    p_ai_patterns.add_argument("run_dir")
    p_ai_patterns.add_argument("--out")
    p_ai_patterns.add_argument("--json", action="store_true")
    p_ai_summary = sub_ai.add_parser("summary")
    p_ai_summary.add_argument("run_dir")
    p_ai_summary.add_argument("--out")
    p_ai_summary.add_argument("--json", action="store_true")
    p_ai_summary.add_argument("--markdown", action="store_true")
    p_ai_drill = sub_ai.add_parser("drilldown")
    p_ai_drill.add_argument("run_dir")
    p_ai_drill.add_argument("--pattern-id")
    p_ai_drill.add_argument("--finding-id")
    p_ai_drill.add_argument("--event-id")
    p_ai_drill.add_argument("--context-lines", type=int, default=25)
    p_ai_drill.add_argument("--max-files", type=int, default=5)
    p_ai_drill.add_argument("--max-snippets", type=int, default=8)
    p_ai_drill.add_argument("--max-lines-per-snippet", type=int, default=80)
    p_ai_drill.add_argument("--max-total-chars", type=int, default=12000)
    p_ai_drill.add_argument("--json", action="store_true")
    p_ai_drill.add_argument("--markdown", action="store_true")
    p_ai_explain = sub_ai.add_parser("explain")
    p_ai_explain.add_argument("run_dir")
    p_ai_explain.add_argument("--pattern-id")
    p_ai_explain.add_argument("--finding-id")
    p_ai_explain.add_argument("--event-id")
    p_ai_explain.add_argument("--with-drilldown", action="store_true")
    p_ai_explain.add_argument("--no-drilldown", action="store_true")
    p_ai_explain.add_argument("--json", action="store_true")
    p_ai_explain.add_argument("--markdown", action="store_true")
    p_ai_risks = sub_ai.add_parser("risks")
    p_ai_risks.add_argument("run_dir")
    p_ai_risks.add_argument("--with-drilldown", action="store_true")
    p_ai_risks.add_argument("--no-drilldown", action="store_true")
    p_ai_risks.add_argument("--max-auto-drilldowns", type=int, default=5)
    p_ai_risks.add_argument("--severity-threshold", default="medium", choices=["low", "medium", "high"])
    p_ai_risks.add_argument("--json", action="store_true")
    p_ai_risks.add_argument("--markdown", action="store_true")
    p_ai_ask = sub_ai.add_parser("ask")
    p_ai_ask.add_argument("run_dir")
    p_ai_ask.add_argument("question")
    p_ai_ask.add_argument("--with-drilldown", action="store_true")
    p_ai_ask.add_argument("--no-drilldown", action="store_true")
    p_ai_ask.add_argument("--json", action="store_true")
    p_ai_ask.add_argument("--markdown", action="store_true")
    p_learn = subparsers.add_parser("learn")
    sub_l = p_learn.add_subparsers(dest="sub")
    p_lb = sub_l.add_parser("build")
    p_lb.add_argument("run_dir")
    p_lb.add_argument("--out", required=True)
    p_lb.add_argument("--concept-graph", required=True)
    p_lb.add_argument("--max-cases-per-concept", type=int, default=30)
    p_lc = sub_l.add_parser("concept")
    p_lc.add_argument("concept")
    p_lc.add_argument("--from", dest="from_run", required=True)
    p_lc.add_argument("--max", type=int, default=10)
    p_lc.add_argument("--json", action="store_true")
    p_lc.add_argument("--concept-graph", required=True)
    p_lall = sub_l.add_parser("concepts")
    p_lall.add_argument("--json", action="store_true")
    p_lall.add_argument("--graph")
    p_lcases = sub_l.add_parser("cases")
    p_lcases.add_argument("concept_id_or_concept")
    p_lcases.add_argument("--from", dest="from_run")
    p_lcases.add_argument("--dir")
    p_lcases.add_argument("--level")
    p_lcases.add_argument("--language")
    p_lcases.add_argument("--max", type=int, default=10)
    p_lcases.add_argument("--json", action="store_true")
    p_lcases.add_argument("--graph")
    p_lserve = sub_l.add_parser("serve")
    p_lserve.add_argument("learn_dir", nargs="?")
    p_lserve.add_argument("--dir")
    p_lserve.add_argument("--host", default="127.0.0.1")
    p_lserve.add_argument("--port", type=int, default=8000)
    p_lserve.add_argument("--open", action="store_true")
    p_lex = sub_l.add_parser("extract-cases")
    p_lex.add_argument("run_dir")
    p_lex.add_argument("--out", required=True)
    p_lex.add_argument("--min-confidence", type=float, default=0.8)
    p_lex.add_argument("--json", action="store_true")
    p_lex.add_argument("--graph")
    p_lex.add_argument("--case-spec", action="store_true")
    p_lgraph = sub_l.add_parser("graph")
    sub_lg = p_lgraph.add_subparsers(dest="graph_sub")
    p_lg_check = sub_lg.add_parser("check")
    p_lg_check.add_argument("--graph", required=True)
    p_lg_check.add_argument("--map", required=True)
    p_lg_check.add_argument("--json", action="store_true")
    p_lpath = sub_l.add_parser("path")
    p_lpath.add_argument("concept")
    p_lpath.add_argument("--graph", required=True)
    p_lpath.add_argument("--map")
    p_lpath.add_argument("--max-depth", type=int, default=4)
    p_lpath.add_argument("--json", action="store_true")
    p_lpath.add_argument("--from")
    p_lpath.add_argument("--lib")
    p_ctx = subparsers.add_parser("context")
    sub_ctx = p_ctx.add_subparsers(dest="ctx_sub")
    p_pack = sub_ctx.add_parser("pack")
    p_pack.add_argument("run_dir")
    p_pack.add_argument("--out", required=True)
    p_pack.add_argument("--zip", action="store_true")
    p_pack.add_argument("--include-evidence", action="store_true")
    p_pack.add_argument("--include-learn", action="store_true")
    p_pack.add_argument("--learn-graph")
    p_pack.add_argument("--include-brief", action="store_true")
    p_pack.add_argument("--base-pack")
    p_br = sub_ctx.add_parser("brief")
    p_br.add_argument("run_dir")
    p_br.add_argument("--out", required=True)
    p_br.add_argument("--max-items", type=int, default=20)
    p_br.add_argument("--json", action="store_true")
    p_cdiff = sub_ctx.add_parser("diff")
    p_cdiff.add_argument("packA")
    p_cdiff.add_argument("packB")
    p_cdiff.add_argument("--out", required=True)
    p_cdiff.add_argument("--json", action="store_true")
    p_arch = subparsers.add_parser("arch")
    sub_a = p_arch.add_subparsers(dest="arch_sub")
    p_ab = sub_a.add_parser("build")
    p_ab.add_argument("run_dir")
    p_ab.add_argument("--out")
    p_ab.add_argument("--json", action="store_true")
    p_av = sub_a.add_parser("verify")
    p_av.add_argument("run_dir")
    p_av.add_argument("--json", action="store_true")
    p_covr = subparsers.add_parser("coverage")
    p_covr.add_argument("run_dir")
    p_covr.add_argument("--top", type=int, default=20)
    p_llib = sub_l.add_parser("library")
    sub_ll = p_llib.add_subparsers(dest="lib_sub")
    p_lib_init = sub_ll.add_parser("init")
    p_lib_init.add_argument("lib_dir")
    p_lib_add = sub_ll.add_parser("add")
    p_lib_add.add_argument("run_dir")
    p_lib_add.add_argument("--lib", required=True)
    p_lib_add.add_argument("--min-confidence", type=float, default=0.8)
    p_lib_add.add_argument("--graph", required=True)
    p_lib_add.add_argument("--map")
    p_lib_stats = sub_ll.add_parser("stats")
    p_lib_stats.add_argument("--lib", required=True)
    p_lib_stats.add_argument("--json", action="store_true")
    p_lib_verify = sub_ll.add_parser("verify")
    p_lib_verify.add_argument("--lib", required=True)
    p_lib_verify.add_argument("--json", action="store_true")
    p_specs = subparsers.add_parser("specs")
    sub_sp = p_specs.add_subparsers(dest="specs_sub")
    p_sg = sub_sp.add_parser("graph")
    sub_sgg = p_sg.add_subparsers(dest="graph_sub")
    p_sgb = sub_sgg.add_parser("build")
    p_sgb.add_argument("--specs", required=True)
    p_sgb.add_argument("--out", required=True)
    p_scheck = sub_sp.add_parser("check")
    p_scheck.add_argument("--specs", required=True)
    p_scheck.add_argument("--json", action="store_true")
    p_scheck.add_argument("--strict-schema", action="store_true")
    p_scomp = sub_sp.add_parser("compile")
    sub_sc = p_scomp.add_subparsers(dest="compile_sub")
    p_scr = sub_sc.add_parser("rulesets")
    p_scr.add_argument("--specs", required=True)
    p_scr.add_argument("--out", required=True)
    p_scr.add_argument("--json", action="store_true")
    p_cases = subparsers.add_parser("cases")
    sub_ca = p_cases.add_subparsers(dest="cases_sub")
    p_ccheck = sub_ca.add_parser("check")
    p_ccheck.add_argument("path")
    p_ccheck.add_argument("--json", action="store_true")
    p_ccheck.add_argument("--strict-schema", action="store_true")
    p_studio = subparsers.add_parser("studio")
    sub_studio = p_studio.add_subparsers(dest="studio_sub")
    p_serve = sub_studio.add_parser("serve")
    p_serve.add_argument("--port", type=int, default=8010)
    p_backend = subparsers.add_parser("backend")
    sub_backend = p_backend.add_subparsers(dest="backend_sub")
    p_backend_report = sub_backend.add_parser("report")
    p_backend_report.add_argument("run_dir")
    p_backend_report.add_argument("--json", action="store_true")
    p_backend_report.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    if args.cmd == "scan":
        run_scan(args.input, args.out, args.ruleset, args.budget, base_run_dir=args.base, specs_dir=args.specs)
    elif args.cmd == "context":
        if args.ctx_sub == "pack":
            try:
                from .context_pack import run_context_pack
                rc = run_context_pack(args.run_dir, args.out, zip=args.zip, include_evidence=args.include_evidence, include_learn=args.include_learn, learn_graph=args.learn_graph, include_brief=args.include_brief, base_pack=args.base_pack)
                sys.exit(0 if rc == 0 else rc)
            except Exception as e:
                print(str(e))
                sys.exit(1)
        elif args.ctx_sub == "brief":
            out_dir = build_brief(args.run_dir, args.out, max_items=args.max_items, as_json=args.json)
            if not args.json:
                print(out_dir)
        elif args.ctx_sub == "diff":
            out_dir = build_context_diff(args.packA, args.packB, args.out, as_json=args.json)
            if not args.json:
                print(out_dir)
    elif args.cmd == "gate":
        if getattr(args, "gate", None):
            from .quality_gate import load_gate_config, collect_metrics, evaluate, write_quality_gate
            from .baseline import compute_diff as _compute_diff
            import json as _json
            cfg = load_gate_config(args.gate)
            mets = collect_metrics(args.run_dir)
            bdiff = None
            bpaths = None
            if getattr(args, "baseline", None):
                try:
                    tmp_out = os.path.join(args.run_dir, "baseline_diff.json")
                    # copy baseline_in
                    try:
                        data = _json.load(open(args.baseline, "r", encoding="utf-8"))
                        _json.dump(data, open(os.path.join(args.run_dir, "baseline_in.json"), "w", encoding="utf-8"))
                    except Exception:
                        pass
                    bdiff = _compute_diff(args.baseline, args.run_dir, tmp_out, out_md_path=os.path.join(args.run_dir, "baseline_diff.md"))
                    bpaths = {"baseline_in": os.path.join(args.run_dir, "baseline_in.json"), "diff_json": tmp_out, "diff_md": os.path.join(args.run_dir, "baseline_diff.md")}
                except Exception:
                    bdiff = None
            obj = evaluate(mets, cfg, baseline_diff=bdiff, baseline_paths=bpaths)
            write_quality_gate(args.run_dir, obj)
            print(json.dumps(obj))
            sys.exit(2 if obj.get("status") == "fail" else 0)
        else:
            # default to prod_lite if no explicit --gate; or use legacy policy if provided
            if getattr(args, "policy", None):
                from .gate import run_gate_policy
                ok = run_gate_policy(args.run_dir, args.policy, args.json)
                sys.exit(0 if ok else 2)
            else:
                from .quality_gate import load_gate_config, collect_metrics, evaluate, write_quality_gate
                base = os.path.dirname(os.path.dirname(__file__))
                try:
                    mcfg = json.load(open(os.path.join(args.run_dir, "meta", "config.json"), "r", encoding="utf-8"))
                    default_gate = mcfg.get("gate_path") or os.path.join(base, "presets", "gates", "prod_lite.json")
                except Exception:
                    default_gate = os.path.join(base, "presets", "gates", "prod_lite.json")
                cfg = load_gate_config(default_gate)
                obj = evaluate(collect_metrics(args.run_dir), cfg)
                write_quality_gate(args.run_dir, obj)
                print(json.dumps(obj))
                sys.exit(2 if obj.get("status") == "fail" else 0)
    elif args.cmd == "show":
        show_report(args.run_dir, args.open)
    elif args.cmd == "query":
        run_query(args.run_dir, args.entity, args.json)
    elif args.cmd == "verify":
        run_verify(args.run_dir, args.json, strict=getattr(args, "strict", False))
    elif args.cmd == "explain":
        run_explain(args.run_dir, args.subject, args.id, args.json)
    elif args.cmd == "diff":
        run_diff(args.runA, args.runB, args.json)
    elif args.cmd == "export":
        if args.format == "sarif":
            run_export_sarif(args.run_dir, args.out)
    elif args.cmd == "baseline":
        if args.b_sub == "save":
            from .baseline import save_baseline
            save_baseline(args.run_dir, args.out)
    elif args.cmd == "bdiff":
        from .baseline import compute_diff
        compute_diff(args.base, args.new, args.out, out_md_path=args.markdown)
    elif args.cmd == "patch":
        if args.patch_sub == "exports":
            from .patch_exports import run_patch_exports
            rc = run_patch_exports(args.run_dir)
            if rc != 0:
                sys.exit(rc)
    elif args.cmd == "ci":
        if args.ci_sub == "run":
            from .ci import run_ci
            repo = args.repo or os.getcwd()
            outd = args.out or os.path.join(repo, ".reposense_ci")
            red = None
            if getattr(args, "redact", False):
                red = True
            if getattr(args, "no_redact", False):
                red = False
            code = run_ci(repo, outd, profile=args.profile, ruleset=args.ruleset, budget=args.budget, gate=args.gate, with_context_pack=args.with_context_pack, json_stdout=args.json, baseline_in=args.baseline_in, baseline_out=args.baseline_out, redact=red)
            if code != 0:
                sys.exit(code)
    elif args.cmd == "ruleset":
        if args.rs_sub == "info":
            from .versioning import ruleset_fingerprint
            rid = os.path.basename(args.ruleset_dir)
            fp = ruleset_fingerprint(args.ruleset_dir)
            data = {"ruleset_id": rid, "ruleset_fingerprint": fp}
            print(json.dumps(data) if args.json else f"{rid} {fp}")
    elif args.cmd == "run":
        if args.run_sub == "info":
            try:
                qg = json.load(open(os.path.join(args.run_dir, "quality_gate.json"), "r", encoding="utf-8"))
            except Exception:
                qg = {}
            out = {
                "baseline_used": bool(qg.get("baseline_used")),
                "baseline_compatible": bool(qg.get("baseline_compatible", True)),
                "paths": {
                    "report": os.path.join(args.run_dir, "report.json"),
                    "sarif": os.path.join(args.run_dir, "exports", "report.sarif.json"),
                    "quality_gate": os.path.join(args.run_dir, "quality_gate.json"),
                    "baseline_diff": os.path.join(args.run_dir, "baseline_diff.json"),
                    "baseline_in": os.path.join(args.run_dir, "baseline_in.json"),
                    "run_manifest": os.path.join(args.run_dir, "run_manifest.json"),
                }
            }
            print(json.dumps(out) if args.json else f"baseline_used={out['baseline_used']} compatible={out['baseline_compatible']}")
        elif args.run_sub == "manifest":
            from .run_manifest import build_run_manifest
            obj = build_run_manifest(args.run_dir, write=True)
            print(json.dumps(obj) if getattr(args, "json", False) else os.path.join(args.run_dir, "run_manifest.json"))
        elif args.run_sub == "upgrade":
            from .run_upgrade import upgrade_run
            code = upgrade_run(args.run_dir, out_dir=args.out, inplace=args.inplace or (args.out is None), strict=args.strict, patch_exports=True)
            if args.json:
                print(json.dumps({"ok": code == 0}))
            if code != 0:
                sys.exit(code)
    elif args.cmd == "docs":
        if args.docs_sub == "check":
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "schema")
            req = ["report.json.md","event_graph.json.md","api_surface.json.md","entrypoints.json.md","coverage.json.md","quality_gate.json.md","ci_summary.json.md","run_manifest.json.md","baseline_in.json.md","baseline_diff.json.md","exports_report.sarif.json.md"]
            miss = [x for x in req if not os.path.isfile(os.path.join(base, x))]
            if miss:
                print(json.dumps({"missing": miss}))
                sys.exit(2)
            else:
                print(json.dumps({"ok": True}))
    elif args.cmd == "rules":
        if args.sub == "check":
            run_rules_check(args.ruleset_dir, args.json)
        elif args.sub == "coverage":
            run_rules_coverage(args.ruleset_dir, args.fixtures, args.json)
    elif args.cmd == "coverage":
        try:
            import json as _json
            p = os.path.join(args.run_dir, "coverage.json")
            d = _json.load(open(p, "r", encoding="utf-8"))
            walk = d.get("walk", {})
            skipped = walk.get("skipped", {})
            incl = walk.get("included_files", 0)
            items = sorted(skipped.items(), key=lambda x: x[1], reverse=True)[: args.top]
            out = {"included_files": incl, "skipped_top": items}
            print(_json.dumps(out))
        except Exception as e:
            print(str(e))
            sys.exit(2)
    elif args.cmd == "selfcheck":
        ok = run_selfcheck(args.run_dir, args.policy, args.sarif, args.strict)
        if not ok:
            sys.exit(2)
    elif args.cmd == "ai":
        if args.ai_sub == "patterns":
            res = export_patterns(args.run_dir, out_dir=args.out)
            if args.json:
                print(json.dumps({"ok": True, "patterns_path": res["patterns_path"], "summary_path": res["summary_path"], "summary": res["summary"]}, ensure_ascii=False))
            else:
                sm = res.get("summary") or {}
                print(f"patterns={int(sm.get('total_patterns') or 0)}")
                print(res["patterns_path"])
                print(res["summary_path"])
        elif args.ai_sub == "summary":
            # default: print markdown; write files when requested or --out is provided
            write_files = bool(args.out or args.json or args.markdown)
            res = export_ai_summary(
                args.run_dir,
                out_dir=args.out,
                write_json_file=write_files,
                write_markdown_file=write_files,
            )
            print(res["markdown"])
            if args.json:
                print(json.dumps({"ok": True, "json_path": res["json_path"], "markdown_path": res["markdown_path"], "summary": res["summary"]}, ensure_ascii=False))
        elif args.ai_sub == "drilldown":
            pairs = [
                ("pattern", str(getattr(args, "pattern_id", "") or "").strip()),
                ("finding", str(getattr(args, "finding_id", "") or "").strip()),
                ("event", str(getattr(args, "event_id", "") or "").strip()),
            ]
            chosen = [(k, v) for k, v in pairs if v]
            if len(chosen) != 1:
                print("exactly one of --pattern-id/--finding-id/--event-id is required")
                sys.exit(2)
            target_type, target_id = chosen[0]
            budget = {
                "context_lines": args.context_lines,
                "max_files": args.max_files,
                "max_snippets": args.max_snippets,
                "max_lines_per_snippet": args.max_lines_per_snippet,
                "max_total_chars": args.max_total_chars,
            }
            res = export_drilldown(args.run_dir, target_type=target_type, target_id=target_id, budget=budget)
            pack = res.get("pack") or {}
            print(
                "drilldown request_id={rid} files={files} snippets={snippets}".format(
                    rid=str(res.get("request_id") or ""),
                    files=len(pack.get("selected_files") or []),
                    snippets=len(pack.get("selected_snippets") or []),
                )
            )
            print(res.get("json_path") or "")
            print(res.get("markdown_path") or "")
            if args.markdown:
                print(res.get("markdown") or "")
            if args.json:
                print(json.dumps({"ok": True, "request_id": res.get("request_id"), "json_path": res.get("json_path"), "markdown_path": res.get("markdown_path"), "pack": pack}, ensure_ascii=False))
        elif args.ai_sub == "explain":
            pairs = [
                ("pattern", str(getattr(args, "pattern_id", "") or "").strip()),
                ("finding", str(getattr(args, "finding_id", "") or "").strip()),
                ("event", str(getattr(args, "event_id", "") or "").strip()),
            ]
            chosen = [(k, v) for k, v in pairs if v]
            if len(chosen) != 1:
                print("exactly one of --pattern-id/--finding-id/--event-id is required")
                sys.exit(2)
            if args.with_drilldown and args.no_drilldown:
                print("--with-drilldown and --no-drilldown cannot be used together")
                sys.exit(2)
            target_type, target_id = chosen[0]
            try:
                res = export_ai_explain(
                    args.run_dir,
                    target_type=target_type,
                    target_id=target_id,
                    with_drilldown=bool(args.with_drilldown),
                    no_drilldown=bool(args.no_drilldown),
                )
            except ValueError as e:
                print(str(e))
                sys.exit(2)
            print(f"explain request_id={res.get('request_id')} mode={str((res.get('result') or {}).get('mode') or '')}")
            print(res.get("json_path") or "")
            print(res.get("markdown_path") or "")
            if args.markdown:
                print(res.get("markdown") or "")
            if args.json:
                print(json.dumps({"ok": True, "request_id": res.get("request_id"), "json_path": res.get("json_path"), "markdown_path": res.get("markdown_path"), "result": res.get("result")}, ensure_ascii=False))
        elif args.ai_sub == "risks":
            if args.with_drilldown and args.no_drilldown:
                print("--with-drilldown and --no-drilldown cannot be used together")
                sys.exit(2)
            res = export_ai_risks(
                args.run_dir,
                with_drilldown=bool(args.with_drilldown),
                no_drilldown=bool(args.no_drilldown),
                max_auto_drilldowns=int(args.max_auto_drilldowns or 5),
                severity_threshold=str(args.severity_threshold or "medium"),
            )
            report = res.get("report") or {}
            print(f"risks report_id={str(report.get('report_id') or '')} mode={str(report.get('mode') or '')}")
            print(res.get("json_path") or "")
            print(res.get("markdown_path") or "")
            if args.markdown:
                print(res.get("markdown") or "")
            if args.json:
                print(json.dumps({"ok": True, "json_path": res.get("json_path"), "markdown_path": res.get("markdown_path"), "report": report}, ensure_ascii=False))
        elif args.ai_sub == "ask":
            if args.with_drilldown and args.no_drilldown:
                print("--with-drilldown and --no-drilldown cannot be used together")
                sys.exit(2)
            try:
                res = export_ai_ask(
                    args.run_dir,
                    question=args.question,
                    with_drilldown=bool(args.with_drilldown),
                    no_drilldown=bool(args.no_drilldown),
                )
            except ValueError as e:
                print(str(e))
                sys.exit(2)
            ans = res.get("answer") or {}
            print(f"ask request_id={str(ans.get('request_id') or '')} type={str(ans.get('question_type') or '')} mode={str(ans.get('mode') or '')}")
            print(res.get("json_path") or "")
            print(res.get("markdown_path") or "")
            if args.markdown:
                print(res.get("markdown") or "")
            if args.json:
                print(json.dumps({"ok": True, "json_path": res.get("json_path"), "markdown_path": res.get("markdown_path"), "answer": ans}, ensure_ascii=False))
    elif args.cmd == "learn":
        if args.sub == "build":
            build_site(args.run_dir, args.out, args.concept_graph, args.max_cases_per_concept)
        elif args.sub == "concept":
            cg = ConceptGraph(load_concept_graph(args.concept_graph))
            info = cg.get(args.concept)
            if not info:
                print("error=concept not found; available=" + ",".join(cg.all_concepts()))
                sys.exit(2)
            cases = [c for c in extract_cases(args.from_run) if c["concept"] == str(args.concept).lower()]
            cases.sort(key=lambda x: x["difficulty"])
            cases = cases[: args.max]
            out = {"short_definition": info.get("short_definition"), "prerequisites": info.get("prerequisites", []), "related": info.get("related", []), "cases": [{"eid": f"E{c['primary_eid']}", "path": c["evidence_refs"][0]["path"] if c["evidence_refs"] else "", "start_line": c["evidence_refs"][0]["start_line"] if c["evidence_refs"] else 0, "snippet": (c["evidence_refs"][0]["snippet"].splitlines()[0] if c["evidence_refs"] and c["evidence_refs"][0].get("snippet") else ""), "parse_level": c["evidence_refs"][0]["parse_level"] if c["evidence_refs"] else ""} for c in cases]}
            if args.json:
                print(json.dumps(out))
            else:
                print("definition: " + (out["short_definition"] or ""))
                print("prerequisites: " + ", ".join(out["prerequisites"]))
                print("related: " + ", ".join(out["related"]))
                print("cases:")
                for e in out["cases"]:
                    print(f"- {e['eid']} {e['path']}:{e['start_line']} [{e['parse_level']}] {e['snippet']}")
        elif args.sub == "concepts":
            cg = ConceptGraph(load_concept_graph(args.graph or default_concept_graph_path()))
            concepts = cg.graph.get("concepts", [])
            if args.json:
                import json as _json
                print(_json.dumps(concepts))
            else:
                for c in concepts:
                    nm = c.get("concept") or c.get("name") or c.get("title") or c.get("concept_id")
                    print(f"{c.get('concept_id') or nm} {nm}")
        elif args.sub == "cases":
            if args.from_run:
                cg = ConceptGraph(load_concept_graph(args.graph or default_concept_graph_path()))
                key = args.concept_id_or_concept
                info = cg.get(key)
                if not info:
                    print("error=concept not found; available=" + ",".join(cg.all_concepts()))
                    sys.exit(2)
                cid = str(info.get("concept_id") or key).lower()
                concept = str(info.get("concept") or info.get("name") or "").lower()
                cands = set([x for x in [concept, cid, cid.split(".")[-1], key.lower()] if x])
                cases = [c for c in extract_cases(args.from_run) if str(c.get("concept") or "").lower() in cands]
                if args.level:
                    try:
                        lvl = int(args.level)
                        cases = [c for c in cases if c["difficulty"] == lvl]
                    except:
                        pass
                cases.sort(key=lambda x: x["difficulty"])
                cases = cases[: args.max]
            else:
                lib_dir = args.dir or ".reposense_learn_cases"
                store = CaseLibraryStore(lib_dir)
                lvl = int(args.level) if args.level else None
                cases = store.list_cases(concept_id=args.concept_id_or_concept, level=lvl, language=args.language)[: args.max]
            if args.json:
                import json as _json
                print(_json.dumps(cases))
            else:
                for c in cases:
                    if "fid" in c:
                        print(f"{c['fid']} {c['rule_id']} conf={c['confidence']} refs={len(c['evidence_refs'])}")
                    else:
                        print(f"{c['case_id']} {c['concept_id']} level={c['level']} refs={len(c['evidence_refs'])}")
        elif args.sub == "serve":
            cases_dir = args.dir or args.learn_dir or ".reposense_learn_cases"
            run_learn_ui_server(
                cases_dir=cases_dir,
                host=args.host,
                port=args.port,
                open_browser=args.open,
            )
        elif args.sub == "extract-cases":
            run_extract_cases(args.run_dir, args.out, args.min_confidence, args.graph or default_concept_graph_path(), args.json, case_spec=args.case_spec)
        elif args.sub == "graph":
            if args.graph_sub == "check":
                import json as _json
                res = check_graph_and_map(load_concept_graph(args.graph), load_concept_map(args.map))
                print(_json.dumps(res) if args.json else f"ok={res['ok']} errors={len(res['errors'])}")
        elif args.sub == "library":
            if args.lib_sub == "init":
                library_init(args.lib_dir)
            elif args.lib_sub == "add":
                library_add(args.run_dir, args.lib, args.min_confidence, args.graph, args.map)
            elif args.lib_sub == "stats":
                import json as _json
                res = library_stats(args.lib)
                print(_json.dumps(res) if args.json else f"cases={res['cases']}")
            elif args.lib_sub == "verify":
                import json as _json
                res = library_verify(args.lib)
                print(_json.dumps(res) if args.json else f"ok={res['ok']} errors={len(res['errors'])}")
        elif args.sub == "path":
            import json as _json
            graph = load_concept_graph(args.graph)
            cg = ConceptGraph(graph)
            info = cg.get(args.concept)
            if not info:
                print("error=concept not found")
                sys.exit(2)
            start_id = (info.get("concept_id") or info["concept"]).lower()
            order = toposort(graph, start_id, args.max_depth)
            picks = pick_cases_for_concepts(order, graph, run_dir=args.__dict__.get("from"), lib_dir=args.lib, max_per=3)
            out = {"order": order, "picks": picks}
            print(_json.dumps(out) if args.json else f"steps={len(order)}")
    elif args.cmd == "context":
        if args.ctx_sub == "pack":
            res = run_context_pack(args.run_dir, args.out, make_zip=args.zip, include_evidence=args.include_evidence, include_learn=args.include_learn, learn_graph=args.learn_graph, include_brief=args.include_brief, base_pack=args.base_pack)
            import json as _json
            print(_json.dumps(res))
        elif args.ctx_sub == "brief":
            out_dir = build_brief(args.run_dir, args.out, max_items=args.max_items, as_json=args.json)
            if not args.json:
                print(out_dir)
        elif args.ctx_sub == "diff":
            out_dir = build_context_diff(args.packA, args.packB, args.out, as_json=args.json)
            if not args.json:
                print(out_dir)
    elif args.cmd == "arch":
        if args.arch_sub == "build":
            out_dir = build_arch_views(args.run_dir, args.out)
            if args.json:
                import json as _json
                print(_json.dumps({"ok": True, "out_dir": out_dir}))
            else:
                print(out_dir)
        elif args.arch_sub == "verify":
            ok = verify_arch_views(args.run_dir, args.json)
            if not ok and not args.json:
                sys.exit(2)
    elif args.cmd == "specs":
        if args.specs_sub == "graph":
            if args.graph_sub == "build":
                export_graph_json(args.specs, args.out)
                print(args.out)
        elif args.specs_sub == "check":
            res = check_specs(args.specs, strict_schema=args.strict_schema)
            import json as _json
            print(_json.dumps(res) if args.json else f"ok={res['ok']} errors={len(res['errors'])}")
        elif args.specs_sub == "compile":
            if args.compile_sub == "rulesets":
                compile_rulesets(args.specs, args.out)
                if args.json:
                    import json as _json
                    print(_json.dumps({"ok": True, "out": args.out}))
                else:
                    print(args.out)
    elif args.cmd == "cases":
        if args.cases_sub == "check":
            ok = cases_check(args.path, as_json=args.json, strict_schema=args.strict_schema)
            if not ok and not args.json:
                sys.exit(2)
    elif args.cmd == "studio":
        if args.studio_sub == "serve":
            from .studio.server import run_server
            run_server(args.port)
    elif args.cmd == "backend":
        if args.backend_sub == "report":
            res = export_backend_verifier_report(
                args.run_dir,
                write_json=True,
                write_markdown=True,
            )
            rpt = res.get("report") or {}
            meta = rpt.get("metadata") or {}
            print(
                "backend_verifier findings={f} events={e} edges={g}".format(
                    f=int(meta.get("findings_count") or 0),
                    e=int(meta.get("events_count") or 0),
                    g=int(meta.get("graph_edges") or 0),
                )
            )
            print(res.get("json_path") or "")
            print(res.get("markdown_path") or "")
            if args.markdown:
                print(res.get("markdown") or "")
            if args.json:
                print(json.dumps({"ok": True, "json_path": res.get("json_path"), "markdown_path": res.get("markdown_path"), "report": rpt}, ensure_ascii=False))

