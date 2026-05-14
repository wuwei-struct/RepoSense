import html
import json
from collections import defaultdict
from typing import Dict, List, Tuple
from urllib.parse import quote

from .data import load_case, load_cases_index, load_concepts, list_cases


def _h(value) -> str:
    return html.escape(str(value or ""), quote=True)


def _to_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default


class LearnUIApp:
    def __init__(self, cases_dir: str, concepts_path: str = None, analyze_url: str = "/studio"):
        self.cases_dir = cases_dir
        self.concepts_path = concepts_path
        self.analyze_url = analyze_url

    def route(self, path: str, query: Dict[str, List[str]]) -> Tuple[int, str, bytes]:
        if path == "/":
            return self._redirect("/learn")
        if path == "/healthz":
            return 200, "text/plain; charset=utf-8", b"ok"
        if path in ("/learn", "/learn/concepts"):
            return self._html(self._render_concepts_page(query))
        if path.startswith("/learn/concepts/") and path.endswith("/cases"):
            concept_id = path[len("/learn/concepts/") : -len("/cases")]
            return self._html(self._render_cases_page(query, concept_from_path=concept_id))
        if path.startswith("/learn/concepts/"):
            concept_id = path[len("/learn/concepts/") :]
            status = 200 if self._has_concept(concept_id) else 404
            return self._html(self._render_concept_detail_page(concept_id), status=status)
        if path == "/learn/cases":
            return self._html(self._render_cases_page(query, concept_from_path=None))
        if path.startswith("/learn/cases/"):
            case_id = path[len("/learn/cases/") :]
            status = 200 if load_case(self.cases_dir, case_id) else 404
            return self._html(self._render_case_detail_page(case_id), status=status)
        return self._html(self._render_not_found(path), status=404)

    def _redirect(self, location: str):
        body = f"<html><body><a href=\"{_h(location)}\">Redirect</a></body></html>".encode("utf-8")
        return 302, "text/html; charset=utf-8", body, {"Location": location}

    def _html(self, text: str, status: int = 200):
        return status, "text/html; charset=utf-8", text.encode("utf-8")

    def _layout(self, title: str, content: str) -> str:
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_h(title)}</title>
  <style>
    :root {{ --bg:#f7f8fa; --surface:#fff; --line:#d7dce5; --text:#1f2937; --muted:#6b7280; --accent:#0f766e; --chip:#ecfeff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font:14px/1.5 "Segoe UI", "Noto Sans", sans-serif; }}
    a {{ color:#0b5cab; text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    .topbar {{ background:var(--surface); border-bottom:1px solid var(--line); padding:12px 20px; position:sticky; top:0; z-index:1; }}
    .topbar .row {{ max-width:1100px; margin:0 auto; display:flex; justify-content:space-between; gap:12px; align-items:center; }}
    .brand {{ font-weight:700; }}
    .nav a {{ margin-left:10px; }}
    .container {{ max-width:1100px; margin:16px auto; padding:0 20px 28px; }}
    .card {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px; margin-bottom:12px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }}
    .title {{ margin:0 0 8px; font-size:20px; }}
    .muted {{ color:var(--muted); }}
    .chips {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }}
    .chip {{ border:1px solid #bde5f0; background:var(--chip); border-radius:999px; padding:2px 8px; font-size:12px; }}
    .stats {{ margin-top:8px; font-size:12px; color:var(--muted); display:flex; gap:10px; flex-wrap:wrap; }}
    form.filter {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:8px; }}
    form.filter input, form.filter select {{ width:100%; padding:6px 8px; border:1px solid var(--line); border-radius:6px; background:#fff; }}
    form.filter button {{ padding:6px 10px; border:1px solid #0e6761; border-radius:6px; background:var(--accent); color:#fff; cursor:pointer; }}
    .section-title {{ margin:0 0 8px; font-size:17px; }}
    pre {{ margin:0; padding:10px; border:1px solid var(--line); border-radius:6px; overflow:auto; background:#f9fafb; }}
    .btn {{ border:1px solid #0e6761; border-radius:6px; background:var(--accent); color:#fff; padding:6px 10px; cursor:pointer; }}
    .empty {{ padding:18px; border:1px dashed var(--line); border-radius:8px; background:#fff; color:var(--muted); }}
    @media (max-width:900px) {{ form.filter {{ grid-template-columns:1fr 1fr; }} .container {{ padding:0 12px 20px; }} }}
  </style>
  <script>
    function copySummary(caseId) {{
      var el = document.getElementById('copy-summary-' + caseId);
      if (!el) return;
      navigator.clipboard.writeText(el.textContent || '').then(function() {{
        var status = document.getElementById('copy-status-' + caseId);
        if (status) status.textContent = 'Copied';
      }});
    }}
  </script>
</head>
<body>
  <div class="topbar">
    <div class="row">
      <div class="brand"><a href="/learn">RepoSense Learn</a></div>
      <div class="nav"><a href="/learn/concepts">Concept Navigator</a><a href="/learn/cases">Case Browser</a><a href="{_h(self.analyze_url)}">Analyze my repo</a></div>
    </div>
  </div>
  <div class="container">
    {content}
  </div>
</body>
</html>"""

    def _concept_stats(self):
        concepts = load_concepts(self.concepts_path)
        idx = load_cases_index(self.cases_dir)
        stats = defaultdict(lambda: {"count": 0, "levels": {1: 0, 2: 0, 3: 0}, "languages": defaultdict(int)})
        for row in idx["cases"]:
            cid = str(row.get("concept_id") or "")
            lvl = int(row.get("level") or 0)
            stats[cid]["count"] += 1
            if lvl in (1, 2, 3):
                stats[cid]["levels"][lvl] += 1
            lg = str(row.get("language") or "unknown")
            stats[cid]["languages"][lg] += 1
        return concepts, idx, stats

    def _has_concept(self, concept_id: str) -> bool:
        concepts = load_concepts(self.concepts_path)
        return any(str(c.get("concept_id") or "") == str(concept_id) for c in concepts)

    def _render_concepts_page(self, query: Dict[str, List[str]]) -> str:
        q = str((query.get("q") or [""])[0]).strip().lower()
        tag_filter = str((query.get("tag") or [""])[0]).strip().lower()
        sort_mode = str((query.get("sort") or [""])[0]).strip().lower()
        concepts, idx, stats = self._concept_stats()
        if not concepts:
            return self._layout("Learn Concepts", "<h1 class=\"title\">Concept Navigator</h1><div class=\"empty\">Concept data is missing. Please provide concepts.json.</div>")

        all_tags = sorted({t for c in concepts for t in c.get("tags") or []})
        visible = []
        for c in concepts:
            cid = c["concept_id"].lower()
            text = " ".join([cid, c.get("name", "").lower(), " ".join([x.lower() for x in (c.get("tags") or [])])])
            if q and q not in text:
                continue
            if tag_filter and tag_filter not in [x.lower() for x in (c.get("tags") or [])]:
                continue
            visible.append(c)

        if sort_mode == "cases_desc":
            visible.sort(key=lambda c: (-stats[c["concept_id"]]["count"], c["concept_id"]))
        else:
            visible.sort(key=lambda c: c["concept_id"])

        cards = []
        for c in visible:
            st = stats[c["concept_id"]]
            tags = "".join([f"<span class=\"chip\">{_h(t)}</span>" for t in c.get("tags") or []])
            cards.append(
                f"""
<div class="card">
  <h2 class="section-title"><a href="/learn/concepts/{quote(c['concept_id'])}">{_h(c['name'])}</a></h2>
  <div class="muted">{_h(c['summary'])}</div>
  <div class="chips">{tags}</div>
  <div class="stats">
    <span>cases: {st['count']}</span>
    <span>L1/L2/L3: {st['levels'][1]}/{st['levels'][2]}/{st['levels'][3]}</span>
    <span>prerequisites: {len(c.get('prerequisites') or [])}</span>
    <span>related: {len(c.get('related') or [])}</span>
  </div>
</div>"""
            )

        content = f"""
<h1 class="title">Concept Navigator</h1>
<div class="card">
  <form class="filter" method="get" action="/learn/concepts">
    <input type="text" name="q" placeholder="search concept_id/name/tag" value="{_h(q)}" />
    <select name="tag">
      <option value="">all tags</option>
      {''.join([f'<option value="{_h(t)}"' + (' selected' if t.lower()==tag_filter else '') + f'>{_h(t)}</option>' for t in all_tags])}
    </select>
    <select name="sort">
      <option value="">sort: concept_id</option>
      <option value="cases_desc"{' selected' if sort_mode=='cases_desc' else ''}>sort: cases desc</option>
    </select>
    <button type="submit">Apply</button>
  </form>
</div>
<div class="grid">{''.join(cards) if cards else '<div class="empty">No concepts matched the current filters.</div>'}</div>
<div class="muted">total concepts: {len(concepts)}, total cases: {idx['total_cases']}</div>
"""
        return self._layout("Learn Concepts", content)

    def _render_concept_detail_page(self, concept_id: str) -> str:
        concepts, _idx, stats = self._concept_stats()
        by_id = {c["concept_id"]: c for c in concepts}
        concept = by_id.get(concept_id)
        if not concept:
            return self._layout("Concept Not Found", f"<h1 class=\"title\">Concept not found</h1><div class=\"empty\">concept_id={_h(concept_id)}</div>")
        st = stats[concept_id]

        def _list_items(items: List[str], as_links: bool = False) -> str:
            if not items:
                return "<div class=\"muted\">none</div>"
            if as_links:
                return "<div class=\"chips\">" + "".join([f"<a class=\"chip\" href=\"/learn/concepts/{quote(x)}\">{_h(x)}</a>" for x in items]) + "</div>"
            return "<ul>" + "".join([f"<li>{_h(x)}</li>" for x in items]) + "</ul>"

        lang_items = sorted((st["languages"] or {}).items(), key=lambda x: x[0])
        language_summary = ", ".join([f"{k}:{v}" for k, v in lang_items]) if lang_items else "none"
        cases_link = f"/learn/concepts/{quote(concept_id)}/cases"

        content = f"""
<h1 class="title">{_h(concept['name'])}</h1>
<div class="card">
  <div class="muted">{_h(concept.get('summary'))}</div>
  <div class="stats">
    <span>concept_id: {_h(concept_id)}</span>
    <span>cases: {st['count']}</span>
    <span>L1/L2/L3: {st['levels'][1]}/{st['levels'][2]}/{st['levels'][3]}</span>
    <span>languages: {_h(language_summary)}</span>
  </div>
</div>
<div class="card"><h2 class="section-title">Learning Objectives</h2>{_list_items(concept.get('learning_objectives') or [])}</div>
<div class="card"><h2 class="section-title">Anti Patterns</h2>{_list_items(concept.get('anti_patterns') or [])}</div>
<div class="card"><h2 class="section-title">Prerequisites</h2>{_list_items(concept.get('prerequisites') or [], as_links=True)}</div>
<div class="card"><h2 class="section-title">Related</h2>{_list_items(concept.get('related') or [], as_links=True)}</div>
<div class="card"><h2 class="section-title">Cases</h2><a href="{cases_link}">View cases</a></div>
"""
        return self._layout(f"Concept {concept_id}", content)

    def _render_cases_page(self, query: Dict[str, List[str]], concept_from_path: str = None) -> str:
        concept_id = concept_from_path or str((query.get("concept_id") or [""])[0]).strip()
        level = _to_int((query.get("level") or [""])[0], None)
        language = str((query.get("language") or [""])[0]).strip()
        label = str((query.get("label") or [""])[0]).strip()
        repo_ref = str((query.get("repo_ref") or [""])[0]).strip()

        idx = load_cases_index(self.cases_dir)
        cases = list_cases(
            self.cases_dir,
            concept_id=concept_id or None,
            level=level,
            language=language or None,
            label=label or None,
            repo_ref=repo_ref or None,
        )

        levels = sorted({int(r.get("level") or 0) for r in idx["cases"]})
        languages = sorted({str(r.get("language") or "") for r in idx["cases"] if str(r.get("language") or "")})
        labels = sorted({x for r in idx["cases"] for x in (r.get("labels") or [])})

        cards = []
        for c in cases:
            meta = c.get("metadata") or {}
            closure_val = meta.get("has_closure")
            distributed_val = meta.get("distributed_signal")
            extra_meta = []
            if closure_val is not None:
                extra_meta.append(f"<span>closure: {_h(closure_val)}</span>")
            if distributed_val is not None:
                extra_meta.append(f"<span>distributed: {_h(distributed_val)}</span>")
            cards.append(
                f"""
<div class="card">
  <h2 class="section-title"><a href="/learn/cases/{quote(c['case_id'])}">{_h(c.get('title') or c['case_id'])}</a></h2>
  <div class="stats">
    <span>level: {c.get('level')}</span>
    <span>language: {_h((meta.get('language') or 'unknown'))}</span>
    <span>repo_ref: {_h(c.get('repo_ref'))}</span>
    <span>evidence: {len(c.get('evidence_refs') or [])}</span>
    {''.join(extra_meta)}
  </div>
  <div class="chips">{''.join([f'<span class="chip">{_h(lb)}</span>' for lb in (c.get('labels') or [])])}</div>
  <div class="muted">{_h((c.get('explain') or {}).get('what'))}</div>
</div>"""
            )

        empty_msg = "No cases found. Run: reposense learn extract-cases" if idx["total_cases"] == 0 else "No cases matched the current filters."
        content = f"""
<h1 class="title">Case Browser</h1>
<div class="card">
  <form class="filter" method="get" action="/learn/cases">
    <input type="text" name="concept_id" placeholder="concept_id" value="{_h(concept_id)}" />
    <select name="level"><option value="">all levels</option>{''.join([f'<option value="{lv}"' + (' selected' if level==lv else '') + f'>L{lv}</option>' for lv in levels])}</select>
    <select name="language"><option value="">all languages</option>{''.join([f'<option value="{_h(lg)}"' + (' selected' if language==lg else '') + f'>{_h(lg)}</option>' for lg in languages])}</select>
    <select name="label"><option value="">all labels</option>{''.join([f'<option value="{_h(lb)}"' + (' selected' if label==lb else '') + f'>{_h(lb)}</option>' for lb in labels])}</select>
    <input type="text" name="repo_ref" placeholder="repo_ref" value="{_h(repo_ref)}" />
    <button type="submit">Apply</button>
  </form>
</div>
{''.join(cards) if cards else f'<div class="empty">{_h(empty_msg)}</div>'}
<div class="muted">total cases: {idx['total_cases']}</div>
"""
        return self._layout("Learn Cases", content)

    def _render_case_detail_page(self, case_id: str) -> str:
        case = load_case(self.cases_dir, case_id)
        if not case:
            return self._layout("Case Not Found", f"<h1 class=\"title\">Case not found</h1><div class=\"empty\">case_id={_h(case_id)}</div>")

        explain = case.get("explain") or {}
        copy_text = "\n".join(
            [
                f"what: {explain.get('what') or ''}",
                f"why: {explain.get('why') or ''}",
                f"how: {explain.get('how') or ''}",
                f"risk: {explain.get('risk') or ''}",
            ]
        )
        evid_blocks = []
        for idx, e in enumerate(case.get("evidence_refs") or []):
            path = e.get("path") or e.get("file") or ""
            start = e.get("start_line") or e.get("line_start") or 0
            end = e.get("end_line") or e.get("line_end") or 0
            snippet = e.get("snippet") or ""
            rule_id = e.get("rule_id") or case.get("rule_id") or ""
            evid_blocks.append(
                f"""
<div class="card">
  <div class="stats"><span>file: {_h(path)}</span><span>lines: {start}-{end}</span><span>rule_id: {_h(rule_id)}</span></div>
  <details>
    <summary>snippet #{idx + 1}</summary>
    <pre>{_h(snippet)}</pre>
  </details>
</div>"""
            )

        content = f"""
<h1 class="title">{_h(case.get('title') or case.get('case_id'))}</h1>
<div class="card">
  <div class="stats">
    <span>case_id: {_h(case.get('case_id'))}</span>
    <span>concept: <a href="/learn/concepts/{quote(case.get('concept_id') or '')}">{_h(case.get('concept_id'))}</a></span>
    <span>level: {case.get('level')}</span>
    <span>repo_ref: {_h(case.get('repo_ref'))}</span>
  </div>
  <div class="chips">{''.join([f'<span class="chip">{_h(lb)}</span>' for lb in (case.get('labels') or [])])}</div>
</div>
<div class="card"><h2 class="section-title">Explain</h2>
  <p><strong>what:</strong> {_h(explain.get('what'))}</p>
  <p><strong>why:</strong> {_h(explain.get('why'))}</p>
  <p><strong>how:</strong> {_h(explain.get('how'))}</p>
  <p><strong>risk:</strong> {_h(explain.get('risk'))}</p>
  <button class="btn" onclick="copySummary('{_h(case.get('case_id'))}')">Copy summary</button>
  <span id="copy-status-{_h(case.get('case_id'))}" class="muted"></span>
  <pre id="copy-summary-{_h(case.get('case_id'))}" style="display:none;">{_h(copy_text)}</pre>
</div>
<div class="card"><h2 class="section-title">Metadata</h2><pre>{_h(json.dumps(case.get('metadata') or {}, ensure_ascii=False, sort_keys=True, indent=2))}</pre></div>
{('<div class="card"><h2 class="section-title">Closure</h2><pre>' + _h(json.dumps(case.get('closure'), ensure_ascii=False, sort_keys=True, indent=2)) + '</pre></div>') if case.get('closure') is not None else ''}
<div><h2 class="section-title">Evidence</h2>{''.join(evid_blocks) if evid_blocks else '<div class="empty">No evidence refs.</div>'}</div>
"""
        return self._layout(f"Case {case_id}", content)

    def _render_not_found(self, path: str) -> str:
        return self._layout("Not Found", f"<h1 class=\"title\">Not Found</h1><div class=\"empty\">path={_h(path)}</div>")
