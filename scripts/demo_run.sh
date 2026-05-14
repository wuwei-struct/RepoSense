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
echo "Artifacts:"
echo "report: $R2_DIR/report.html"
echo "learn: $R2_DIR/learn/index.html"
echo "sarif: $R2_DIR/exports/report.sarif.json"
echo "context_pack: $R2_DIR/exports/context_pack.zip"
echo "gate: $R2_DIR/quality_gate.json"
echo "baseline_in: $R2_DIR/baseline_in.json"
echo "baseline_diff_json: $R2_DIR/baseline_diff.json"
echo "baseline_diff_md: $R2_DIR/baseline_diff.md"
# existence check
[ -f "$R2_DIR/report.html" ] || { echo "missing report.html"; exit 1; }
[ -f "$R2_DIR/learn/index.html" ] || { echo "missing learn/index.html"; exit 1; }
[ -f "$R2_DIR/exports/report.sarif.json" ] || { echo "missing exports/report.sarif.json"; exit 1; }
[ -f "$R2_DIR/exports/context_pack.zip" ] || { echo "missing exports/context_pack.zip"; exit 1; }
[ -f "$R2_DIR/quality_gate.json" ] || { echo "missing quality_gate.json"; exit 1; }
[ -f "$R2_DIR/baseline_diff.md" ] || { echo "missing baseline_diff.md"; exit 1; }
