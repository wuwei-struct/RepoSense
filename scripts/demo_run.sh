#!/usr/bin/env bash
set -euo pipefail
OUT="${OUT:-./_demo_out}"
mkdir -p "$OUT"
echo "Note: _demo_out is run artifact; do not commit"
extract_run_dir() {
  python -c "import sys,json; lines=[x.strip() for x in sys.stdin.read().splitlines() if x.strip()]; obj=None
for ln in lines:
    if ln.startswith('{') and ln.endswith('}'):
        try:
            o=json.loads(ln)
            if isinstance(o, dict) and o.get('run_dir'):
                obj=o
        except Exception:
            pass
print((obj or {}).get('run_dir',''))"
}
echo "Running demo baseline..."
R1_JSON=$(python -m reposense ci run --repo "tests/fixtures/repos/demo_showcase" --out "$OUT" --profile demo --with-context-pack --json)
R1_DIR=$(echo "$R1_JSON" | extract_run_dir)
if [ -z "${R1_DIR:-}" ] || [ ! -d "$R1_DIR" ]; then
  echo "error: baseline run_dir invalid: '$R1_DIR'"
  exit 1
fi
python -m reposense baseline save "$R1_DIR" --out "$OUT/baseline.json"
echo "Running demo regress..."
R2_JSON=$(python -m reposense ci run --repo "tests/fixtures/repos/demo_showcase_regress" --out "$OUT" --profile demo --with-context-pack --baseline-in "$OUT/baseline.json" --json)
R2_DIR=$(echo "$R2_JSON" | extract_run_dir)
if [ -z "${R2_DIR:-}" ] || [ ! -d "$R2_DIR" ]; then
  echo "error: regress run_dir invalid: '$R2_DIR'"
  exit 1
fi
python -m reposense learn build "$R2_DIR" --out "$R2_DIR/learn" --concept-graph "scripts/concept_graph_demo.json"
python -m reposense ai patterns "$R2_DIR" --json
python -m reposense ai summary "$R2_DIR" --json --markdown
python -m reposense ai risks "$R2_DIR" --json --markdown
PATTERN_ID=$(R2_DIR="$R2_DIR" python - << 'PY'
import json, os, sys
run_dir = os.environ.get("R2_DIR")
p = os.path.join(run_dir, "patterns.json")
data = json.load(open(p, "r", encoding="utf-8"))
rows = data.get("patterns") or []
if not rows:
    sys.exit(1)
rows = sorted(rows, key=lambda x: (
    {"high": 3, "medium": 2, "low": 1}.get(str(x.get("severity", "")).lower(), 0),
    {"confirmed": 2, "suspected": 1}.get(str(x.get("status", "")).lower(), 0),
    float(x.get("confidence", 0.0)),
    str(x.get("pattern_id") or ""),
), reverse=True)
print(rows[0]["pattern_id"])
PY
)
if [ -z "${PATTERN_ID:-}" ]; then
  echo "missing explain pattern id"
  exit 1
fi
python -m reposense ai explain "$R2_DIR" --pattern-id "$PATTERN_ID" --json --markdown || python -m reposense ai explain "$R2_DIR" --pattern-id "$PATTERN_ID" --json --markdown --with-drilldown
python -m reposense patch exports "$R2_DIR"
python -m reposense run manifest "$R2_DIR" --json
echo "Artifacts:"
echo "report: $R2_DIR/report.html"
echo "learn: $R2_DIR/learn/index.html"
echo "patterns: $R2_DIR/patterns.json"
echo "ai_summary: $R2_DIR/ai_summary.md"
echo "ai_risks: $R2_DIR/ai_risks/risks.md"
echo "run_manifest: $R2_DIR/run_manifest.json"
echo "sarif: $R2_DIR/exports/report.sarif.json"
echo "context_pack: $R2_DIR/exports/context_pack.zip"
echo "gate: $R2_DIR/quality_gate.json"
echo "baseline_in: $R2_DIR/baseline_in.json"
echo "baseline_diff_json: $R2_DIR/baseline_diff.json"
echo "baseline_diff_md: $R2_DIR/baseline_diff.md"
# existence check
[ -f "$R2_DIR/report.html" ] || { echo "missing report.html"; exit 1; }
[ -f "$R2_DIR/learn/index.html" ] || { echo "missing learn/index.html"; exit 1; }
[ -f "$R2_DIR/patterns.json" ] || { echo "missing patterns.json"; exit 1; }
[ -f "$R2_DIR/ai_summary.md" ] || { echo "missing ai_summary.md"; exit 1; }
[ -f "$R2_DIR/ai_risks/risks.md" ] || { echo "missing ai_risks/risks.md"; exit 1; }
[ -f "$R2_DIR/run_manifest.json" ] || { echo "missing run_manifest.json"; exit 1; }
[ -d "$R2_DIR/ai_explain" ] || { echo "missing ai_explain"; exit 1; }
[ -f "$(find "$R2_DIR/ai_explain" -name explain.md | head -n 1)" ] || { echo "missing ai_explain/*/explain.md"; exit 1; }
[ -f "$R2_DIR/exports/report.sarif.json" ] || { echo "missing exports/report.sarif.json"; exit 1; }
[ -f "$R2_DIR/exports/context_pack.zip" ] || { echo "missing exports/context_pack.zip"; exit 1; }
[ -f "$R2_DIR/quality_gate.json" ] || { echo "missing quality_gate.json"; exit 1; }
[ -f "$R2_DIR/baseline_diff.md" ] || { echo "missing baseline_diff.md"; exit 1; }
