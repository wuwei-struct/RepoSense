Param()
$ErrorActionPreference = "Stop"
$OUT = "./_demo_out"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null
Write-Host "Note: _demo_out is run artifact; do not commit"
function Get-RunDirFromCiOutput($raw) {
  $line = $raw | Where-Object { $_ -match '^\s*\{.*\}\s*$' } | Select-Object -Last 1
  if ([string]::IsNullOrEmpty($line)) { return "" }
  try { return (ConvertFrom-Json $line).run_dir } catch { return "" }
}
Write-Host "Running demo baseline..."
$r1 = python -m reposense ci run --repo "tests/fixtures/repos/demo_showcase" --out $OUT --profile demo --with-context-pack --json
if ($LASTEXITCODE -ne 0) { Write-Error "ci baseline failed"; exit 1 }
$r1dir = Get-RunDirFromCiOutput $r1
if ([string]::IsNullOrEmpty($r1dir) -or -not (Test-Path $r1dir)) { Write-Error "baseline run_dir invalid: '$r1dir'"; exit 1 }
python -m reposense baseline save $r1dir --out "$OUT/baseline.json"
if ($LASTEXITCODE -ne 0) { Write-Error "baseline save failed"; exit 1 }
Write-Host "Running demo regress..."
$r2 = python -m reposense ci run --repo "tests/fixtures/repos/demo_showcase_regress" --out $OUT --profile demo --with-context-pack --baseline-in "$OUT/baseline.json" --json
if ($LASTEXITCODE -ne 0) { Write-Error "ci regress failed"; exit 1 }
$r2dir = Get-RunDirFromCiOutput $r2
if ([string]::IsNullOrEmpty($r2dir) -or -not (Test-Path $r2dir)) { Write-Error "regress run_dir invalid: '$r2dir'"; exit 1 }
python -m reposense learn build $r2dir --out "$r2dir/learn" --concept-graph "scripts/concept_graph_demo.json"
if ($LASTEXITCODE -ne 0) { Write-Error "learn build failed"; exit 1 }
Write-Host "Artifacts:"
Write-Host ("report: " + $r2dir + "/report.html")
Write-Host ("learn: " + $r2dir + "/learn/index.html")
Write-Host ("sarif: " + $r2dir + "/exports/report.sarif.json")
Write-Host ("context_pack: " + $r2dir + "/exports/context_pack.zip")
Write-Host ("gate: " + $r2dir + "/quality_gate.json")
Write-Host ("baseline_in: " + $r2dir + "/baseline_in.json")
Write-Host ("baseline_diff_json: " + $r2dir + "/baseline_diff.json")
Write-Host ("baseline_diff_md: " + $r2dir + "/baseline_diff.md")
if (-not (Test-Path ("$r2dir/report.html"))) { Write-Error "missing report.html"; exit 1 }
if (-not (Test-Path ("$r2dir/learn/index.html"))) { Write-Error "missing learn/index.html"; exit 1 }
if (-not (Test-Path ("$r2dir/exports/report.sarif.json"))) { Write-Error "missing exports/report.sarif.json"; exit 1 }
if (-not (Test-Path ("$r2dir/exports/context_pack.zip"))) { Write-Error "missing exports/context_pack.zip"; exit 1 }
if (-not (Test-Path ("$r2dir/quality_gate.json"))) { Write-Error "missing quality_gate.json"; exit 1 }
if (-not (Test-Path ("$r2dir/baseline_diff.md"))) { Write-Error "missing baseline_diff.md"; exit 1 }
