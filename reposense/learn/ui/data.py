import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..concept_graph import default_concept_graph_path


def _safe_read_json(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _norm_concept(raw: Dict[str, Any]) -> Dict[str, Any]:
    concept_id = str(
        raw.get("concept_id")
        or raw.get("concept")
        or raw.get("name")
        or raw.get("title")
        or ""
    ).strip()
    name = str(raw.get("name") or raw.get("title") or raw.get("concept") or concept_id)
    return {
        "concept_id": concept_id,
        "name": name,
        "category": str(raw.get("category") or ""),
        "summary": str(raw.get("summary") or raw.get("short_definition") or ""),
        "tags": [str(x) for x in (raw.get("tags") or [])],
        "learning_objectives": [str(x) for x in (raw.get("learning_objectives") or [])],
        "anti_patterns": [str(x) for x in (raw.get("anti_patterns") or [])],
        "prerequisites": [str(x) for x in (raw.get("prerequisites") or [])],
        "related": [str(x) for x in (raw.get("related") or [])],
    }


def load_concepts(concepts_path: Optional[str] = None) -> List[Dict[str, Any]]:
    path = Path(concepts_path or default_concept_graph_path()).resolve()
    data = _safe_read_json(path, {})
    concepts = [_norm_concept(c) for c in (data.get("concepts") or [])]
    concepts.sort(key=lambda x: (x.get("concept_id", ""), x.get("name", "")))
    return concepts


def _norm_index_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "case_id": str(row.get("case_id") or ""),
        "concept_id": str(row.get("concept_id") or ""),
        "level": int(row.get("level") or 0),
        "labels": [str(x) for x in (row.get("labels") or [])],
        "language": str(row.get("language") or ""),
    }


def load_cases_index(cases_dir: str) -> Dict[str, Any]:
    base = Path(cases_dir).resolve()
    raw = _safe_read_json(base / "cases_index.json", {})
    rows = [_norm_index_row(r) for r in (raw.get("cases") or [])]
    rows.sort(key=lambda x: (x.get("concept_id", ""), x.get("level", 0), x.get("case_id", "")))
    return {
        "total_cases": int(raw.get("total_cases") or len(rows)),
        "cases": rows,
    }


def _norm_case(case: Dict[str, Any]) -> Dict[str, Any]:
    explain = case.get("explain") or {}
    evidence_refs = case.get("evidence_refs") or []
    metadata = case.get("metadata") or {}
    return {
        "case_id": str(case.get("case_id") or ""),
        "concept_id": str(case.get("concept_id") or ""),
        "title": str(case.get("title") or ""),
        "level": int(case.get("level") or 0),
        "repo_ref": str(case.get("repo_ref") or ""),
        "labels": [str(x) for x in (case.get("labels") or [])],
        "metadata": metadata if isinstance(metadata, dict) else {},
        "rule_id": str(case.get("rule_id") or ""),
        "confidence": case.get("confidence"),
        "explain": {
            "what": str(explain.get("what") or case.get("what") or ""),
            "why": str(explain.get("why") or case.get("why") or ""),
            "how": str(explain.get("how") or case.get("how") or ""),
            "risk": str(explain.get("risk") or case.get("risk") or ""),
        },
        "closure": case.get("closure"),
        "evidence_refs": evidence_refs if isinstance(evidence_refs, list) else [],
    }


def load_case(cases_dir: str, case_id: str) -> Optional[Dict[str, Any]]:
    if not case_id:
        return None
    path = Path(cases_dir).resolve() / "cases" / f"{case_id}.json"
    raw = _safe_read_json(path, None)
    if raw is None:
        return None
    return _norm_case(raw)


def list_cases(
    cases_dir: str,
    concept_id: Optional[str] = None,
    level: Optional[int] = None,
    language: Optional[str] = None,
    label: Optional[str] = None,
    repo_ref: Optional[str] = None,
) -> List[Dict[str, Any]]:
    idx = load_cases_index(cases_dir)
    out: List[Dict[str, Any]] = []
    concept_id_l = str(concept_id or "").lower()
    language_l = str(language or "").lower()
    label_l = str(label or "").lower()
    repo_ref_l = str(repo_ref or "").lower()
    for row in idx["cases"]:
        if concept_id_l and row["concept_id"].lower() != concept_id_l:
            continue
        if level is not None and int(row["level"]) != int(level):
            continue
        if language_l and row["language"].lower() != language_l:
            continue
        if label_l:
            labels_l = [x.lower() for x in row.get("labels") or []]
            if label_l not in labels_l:
                continue
        case = load_case(cases_dir, row["case_id"])
        if not case:
            continue
        if repo_ref_l and str(case.get("repo_ref") or "").lower() != repo_ref_l:
            continue
        out.append(case)
    out.sort(key=lambda x: (int(x.get("level") or 0), str(x.get("title") or ""), str(x.get("case_id") or "")))
    return out
