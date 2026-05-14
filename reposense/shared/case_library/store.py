import os
import json
from pathlib import Path


class CaseLibraryStore:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir).resolve()
        self.cases_dir = self.base_dir / "cases"
        self.index_path = self.base_dir / "cases_index.json"
        self.summary_path = self.base_dir / "extract_summary.json"

    def init(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.cases_dir.mkdir(parents=True, exist_ok=True)

    def write_cases(self, cases, summary):
        self.init()
        for c in sorted(cases, key=lambda x: str(x.get("case_id") or "")):
            p = self.cases_dir / f"{c['case_id']}.json"
            p.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        idx = {
            "total_cases": len(cases),
            "cases": [{"case_id": c["case_id"], "concept_id": c["concept_id"], "level": c["level"], "labels": c.get("labels") or [], "language": (c.get("metadata") or {}).get("language", "")} for c in sorted(cases, key=lambda x: str(x.get("case_id") or ""))]
        }
        self.index_path.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
        self.summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")

    def list_cases(self, concept_id=None, level=None, language=None):
        if not self.index_path.exists():
            return []
        idx = json.loads(self.index_path.read_text(encoding="utf-8"))
        rows = idx.get("cases") or []
        out = []
        for r in rows:
            if concept_id and str(r.get("concept_id") or "").lower() != str(concept_id).lower():
                continue
            if level is not None and int(r.get("level") or 0) != int(level):
                continue
            if language and str(r.get("language") or "").lower() != str(language).lower():
                continue
            fp = self.cases_dir / f"{r['case_id']}.json"
            if fp.exists():
                out.append(json.loads(fp.read_text(encoding="utf-8")))
        out.sort(key=lambda x: (str(x.get("concept_id") or ""), int(x.get("level") or 0), str(x.get("case_id") or "")))
        return out
