import os
import json
import shutil
from pathlib import Path
from .concept_graph import load_concept_graph, ConceptGraph
from .case_extractor import extract_cases

def _slug(s):
    import re
    return re.sub(r'[^a-z0-9_-]', '_', str(s).lower())

def _safe_outdir(out_dir):
    p = Path(out_dir).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p

def copy_assets(out_dir):
    # reposense/learn/site_builder.py -> reposense/learn/ -> reposense/ -> root -> webui/static
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src = os.path.join(base_dir, "webui", "static")
    dst = os.path.join(out_dir, "assets")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    if os.path.exists(src):
        shutil.copytree(src, dst)

def create_evidence_card(e):
    lines = (e.get("snippet") or "").splitlines()
    start = e.get("start_line", 0)
    code_html = ""
    for i, line in enumerate(lines):
        code_html += f"""<div class="snippet-line">
          <div class="snippet-ln">{start + i}</div>
          <div class="snippet-code">{line}</div>
        </div>"""
    
    return f"""
        <div class="evidence-card">
          <div class="evidence-header">
            <span class="evidence-path">{e.get('path', '')}</span>
            <span class="badge">{e.get('parse_level', '')}</span>
          </div>
          <div class="snippet-block" style="border:none;margin:0;border-radius:0">
            {code_html}
          </div>
        </div>
    """

def build_site(run_dir=None, out_dir=None, concept_graph_path=None, max_cases_per_concept=30, lib_dir=None, specs_dir=None):
    outp = _safe_outdir(out_dir)
    copy_assets(outp)
    
    # write favicon to reduce 404 noise
    try:
        fav = outp / "favicon.ico"
        if not fav.exists():
            fav.write_bytes(b"")
    except:
        pass

    cg = ConceptGraph(load_concept_graph(concept_graph_path))
    cases = []
    if lib_dir:
        # read from library casebank.jsonl
        from pathlib import Path
        cb = Path(lib_dir).resolve() / "casebank.jsonl"
        if cb.exists():
            for ln in cb.read_text(encoding="utf-8").splitlines():
                try:
                    item = json.loads(ln)
                    best = item.get("sources", [])[0] if item.get("sources") else {}
                    cases.append({
                        "concept": cg.get(item["concept_id"])["concept"].lower(),
                        "difficulty": item.get("level", 1),
                        "fid": 0,
                        "rule_id": item.get("rule_id"),
                        "confidence": item.get("confidence"),
                        "primary_eid": best.get("primary_eid"),
                        "evidence_refs": best.get("evidence_refs") or []
                    })
                except:
                    pass
    else:
        cases = extract_cases(run_dir)

    by_concept = {}
    for c in cases:
        by_concept.setdefault(c["concept"], []).append(c)
    for k in by_concept:
        by_concept[k].sort(key=lambda x: x["difficulty"])

    # write casebank.jsonl
    cb = outp / "casebank.jsonl"
    with cb.open("w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")

    # learn_manifest
    lm = {
        "run_dir": run_dir,
        "warnings": []
    }
    (outp / "learn_manifest.json").write_text(json.dumps(lm), encoding="utf-8")

    # write index.html
    idx = outp / "index.html"
    cats = cg.by_category()
    
    html = ["""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>RepoSense Learn</title>
  <link rel='stylesheet' href='assets/reposense.css'>
</head>
<body>
  <div class="topbar">
    <div style="display:flex;align-items:center">
      <div class="logo">RepoSense Learn</div>
    </div>
  </div>
  <div class="app-container">
    <div class="main-content" style="max-width:1200px;margin:0 auto">
      <h1>Concepts</h1>
"""]
    
    for cat, concepts in cats.items():
        html.append(f'<h2>{cat}</h2><div class="concept-grid">')
        for c in concepts:
            slug = _slug(c)
            info = cg.get(c)
            count = len(by_concept.get(slug, []))
            html.append(f"""
            <a href='concepts/{slug}.html' style="text-decoration:none;color:inherit">
              <div class="concept-card">
                <div class="concept-title">{c}</div>
                <div class="concept-summary">{info.get('short_definition', '')}</div>
                <div>
                  <span class="badge primary">{count} Cases</span>
                </div>
              </div>
            </a>
            """)
        html.append("</div>")
    
    html.append("""
    </div>
  </div>
</body>
</html>""")
    idx.write_text("\n".join(html), encoding="utf-8")

    # per concept
    (outp / "concepts").mkdir(exist_ok=True)
    for c in cg.all_concepts():
        info = cg.get(c)
        slug = _slug(c)
        lst = by_concept.get(slug, [])[:max_cases_per_concept]
        page = outp / "concepts" / f"{slug}.html"
        
        lines = ["""<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>""" + c + """ - RepoSense Learn</title>
  <link rel='stylesheet' href='../assets/reposense.css'>
</head>
<body>
  <div class="topbar">
    <div style="display:flex;align-items:center">
      <div class="logo"><a href="../index.html" style="text-decoration:none;color:var(--color-primary)">RepoSense Learn</a></div>
      <div style="margin-left:16px;color:var(--color-text-muted)">/ """ + c + """</div>
    </div>
  </div>
  <div class="app-container">
    <div class="main-content" style="max-width:1200px;margin:0 auto">
      <div class="two-col-layout">
        <div>
"""]
        lines.append(f"<h1>{info.get('title', c)} ({c})</h1>")
        if info.get("short_definition"):
            lines.append(f"<p>{info['short_definition']}</p>")

        # from specs, enrich fields
        if specs_dir:
            sp = Path(specs_dir).resolve() / "concepts" / ( (info.get("concept_id") or c) + ".yaml")
            if sp.exists():
                try:
                    import yaml
                    specdoc = yaml.safe_load(sp.read_text(encoding="utf-8")) or {}
                    lines.append("<h2>What</h2><div>"+str(((specdoc.get("definition") or {}).get("what") or "N/A"))+"</div>")
                    lines.append("<h2>Why</h2><div>"+str(((specdoc.get("definition") or {}).get("why") or "N/A"))+"</div>")
                    ng = (specdoc.get("definition") or {}).get("non_goals") or []
                    lines.append("<h2>Non-goals</h2><ul>"+ "".join("<li>"+str(x)+"</li>" for x in ng) +"</ul>")
                    cons = specdoc.get("consequences_if_missing") or []
                    lines.append("<h2>Consequences</h2><ul>"+ "".join("<li>"+str(x)+"</li>" for x in cons) +"</ul>")
                    objs = (specdoc.get("learning") or {}).get("objectives") or []
                    lines.append("<h2>Objectives</h2><ul>"+ "".join("<li>"+str(x)+"</li>" for x in objs) +"</ul>")
                except:
                    pass

        if info.get("prerequisites"):
            lines.append("<p><strong>Prerequisites:</strong> " + ", ".join(f"<span class='badge'>{x}</span>" for x in info["prerequisites"]) + "</p>")
        if info.get("related"):
            lines.append("<p><strong>Related:</strong> " + ", ".join(f"<a href='{_slug(x)}.html'>{x}</a>" for x in info["related"]) + "</p>")
        
        lines.append("</div><div>") # End left col, start right col
        
        lines.append("<h2>Cases</h2>")
        for case in lst:
            if not case["evidence_refs"]:
                continue
            
            lines.append(f"""
            <div class="card">
              <div style="font-weight:600;margin-bottom:8px">Level {case['difficulty']} Case</div>
              {create_evidence_card(case["evidence_refs"][0])}
            </div>
            """)
            
        lines.append("""
        </div>
      </div>
    </div>
  </div>
</body>
</html>""")
        page.write_text("\n".join(lines), encoding="utf-8")
