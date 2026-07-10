Param()

$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Fail([string]$stage, [string]$m) { Write-Host "[ERROR][$stage] $m" -ForegroundColor Red; exit 1 }

$repoRoot = (Get-Location).Path
$tempRoot = Join-Path $repoRoot ".tmp_test_runs\temp"
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
$env:TMP = $tempRoot
$env:TEMP = $tempRoot
$env:TMPDIR = $tempRoot

$fixtureRepo = Join-Path $repoRoot "tests\fixtures\repos\review_demo_full"
$contractPath = Join-Path $fixtureRepo "reposense.authz.yaml"
$canonicalRoot = Join-Path $repoRoot ".reposense_review_demo"
$buildOut = Join-Path $canonicalRoot "_build"
$currentDir = Join-Path $canonicalRoot "current"
$archiveRoot = Join-Path $repoRoot "docs\archive\local-artifacts\root-moved"
$movedLog = Join-Path $repoRoot "docs\archive\local-artifacts\MOVED_FROM_ROOT.md"

New-Item -ItemType Directory -Force -Path $canonicalRoot | Out-Null
New-Item -ItemType Directory -Force -Path $buildOut | Out-Null
New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null

if (-not (Test-Path $movedLog)) {
@"
# Moved From Root

## Moved files/directories

| original_path | new_path | reason |
|---|---|---|

## Already missing before migration

| original_path | observed_status | note |
|---|---|---|

## Not moved

| path | reason |
|---|---|

Notes:
- This flow performs non-destructive moves only (no delete).
- Missing historical files are not reconstructed.
"@ | Set-Content -Encoding UTF8 $movedLog
}

function Append-MoveLog([string]$src, [string]$dst, [string]$reason) {
  Add-Content -Encoding UTF8 -Path $movedLog -Value "| $src | $dst | $reason |"
}

function Move-Safe([string]$srcPath, [string]$reason) {
  if (-not (Test-Path $srcPath)) { return }
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $dstPath = Join-Path $archiveRoot "review-demo-current-$stamp"
  Move-Item -LiteralPath $srcPath -Destination $dstPath
  Append-MoveLog $srcPath $dstPath $reason
  Write-Info "Moved previous current demo: $srcPath -> $dstPath"
}

function Resolve-Python {
  $venvPy = Join-Path $repoRoot ".venv\Scripts\python.exe"
  if (Test-Path $venvPy) { return @{ Kind = "path"; Cmd = $venvPy; Display = $venvPy } }
  $preferred = "D:\安装\Python\python.exe"
  if (Test-Path $preferred) { return @{ Kind = "path"; Cmd = $preferred; Display = $preferred } }
  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd) { return @{ Kind = "name"; Cmd = "python"; Display = $pythonCmd.Source } }
  $pyCmd = Get-Command py -ErrorAction SilentlyContinue
  if ($pyCmd) { return @{ Kind = "py"; Cmd = "py"; Display = $pyCmd.Source } }
  return $null
}

function Invoke-RepoSense {
  Param([hashtable]$Py, [string[]]$RsArgs, [string]$Stage, [switch]$Capture)
  if ($Py.Kind -eq "py") {
    if ($Capture) {
      $out = & $Py.Cmd -3 -m reposense @RsArgs 2>&1
      if ($LASTEXITCODE -ne 0) { Fail $Stage (($out | Out-String).Trim()) }
      return ,$out
    }
    & $Py.Cmd -3 -m reposense @RsArgs
    if ($LASTEXITCODE -ne 0) { Fail $Stage "reposense command failed: $($RsArgs -join ' ')" }
    return @()
  }
  if ($Capture) {
    $out = & $Py.Cmd -m reposense @RsArgs 2>&1
    if ($LASTEXITCODE -ne 0) { Fail $Stage (($out | Out-String).Trim()) }
    return ,$out
  }
  & $Py.Cmd -m reposense @RsArgs
  if ($LASTEXITCODE -ne 0) { Fail $Stage "reposense command failed: $($RsArgs -join ' ')" }
  return @()
}

function Invoke-PythonCode {
  Param([hashtable]$Py, [string]$Code, [string]$Stage)
  if ($Py.Kind -eq "py") {
    & $Py.Cmd -3 -c $Code
  } else {
    & $Py.Cmd -c $Code
  }
  if ($LASTEXITCODE -ne 0) { Fail $Stage "python command failed" }
}

function Get-RunDirFromOutput([object[]]$Lines) {
  $jsonLines = $Lines | Where-Object {
    $s = [string]$_
    $s.StartsWith("{") -and $s.EndsWith("}")
  }
  foreach ($line in ($jsonLines | Select-Object -Last 5)) {
    try {
      $obj = $line | ConvertFrom-Json
      if ($obj.run_dir) { return [string]$obj.run_dir }
    } catch { continue }
  }
  return ""
}

function Select-ExplainPattern([string]$PatternsPath) {
  if (-not (Test-Path $PatternsPath)) { Fail "AI_EXPLAIN" "missing patterns.json: $PatternsPath" }
  $patternsObj = Get-Content $PatternsPath -Raw | ConvertFrom-Json
  $patterns = @($patternsObj.patterns)
  if ($patterns.Count -eq 0) { Fail "AI_EXPLAIN" "patterns.json has no patterns" }
  $selected = $patterns |
    Sort-Object `
      @{ Expression = { [string]$_.severity }; Descending = $false }, `
      @{ Expression = { [string]$_.status }; Descending = $false }, `
      @{ Expression = { [string]$_.pattern_id }; Descending = $false } |
    Select-Object -First 1
  if (-not $selected -or -not $selected.pattern_id) { Fail "AI_EXPLAIN" "unable to select explain target pattern" }
  return $selected
}

function Assert-Exists([string]$relPath) {
  $p = Join-Path $currentDir $relPath
  if (-not (Test-Path $p)) { Fail "ASSERT" "missing required review demo artifact: $p" }
}

if (-not (Test-Path $fixtureRepo)) { Fail "ENV" "fixture repo missing: $fixtureRepo" }
if (-not (Test-Path $contractPath)) { Fail "ENV" "authz contract missing: $contractPath" }

$py = Resolve-Python
if (-not $py) { Fail "ENV" "python interpreter not found" }
Write-Info "Python interpreter: $($py.Display)"

if (Test-Path $currentDir) {
  Move-Safe $currentDir "archive previous canonical review demo"
}

Write-Info "Running ci run for review demo fixture..."
$ciOut = Invoke-RepoSense $py @("ci", "run", "--repo", $fixtureRepo, "--out", $buildOut, "--profile", "demo", "--with-context-pack", "--json") "CI_RUN" -Capture
$runDir = Get-RunDirFromOutput $ciOut
if ([string]::IsNullOrWhiteSpace($runDir) -or -not (Test-Path $runDir)) {
  $latestRun = Get-ChildItem -Path $buildOut -Directory -Filter "run-*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $latestRun) { Fail "CI_RUN" "no run-* directory generated under $buildOut" }
  $runDir = $latestRun.FullName
}

Copy-Item -LiteralPath $runDir -Destination $currentDir -Recurse
Write-Info "Canonical review demo current: $currentDir"

Write-Info "Generating backend verifier report..."
Invoke-RepoSense $py @("backend", "report", $currentDir, "--json", "--markdown") "BACKEND_VERIFIER" | Out-Null

Write-Info "Generating patterns..."
Invoke-RepoSense $py @("ai", "patterns", $currentDir, "--json") "AI_PATTERNS" | Out-Null

Write-Info "Generating AI summary..."
Invoke-RepoSense $py @("ai", "summary", $currentDir, "--json", "--markdown") "AI_SUMMARY" | Out-Null

Write-Info "Generating AI risks..."
Invoke-RepoSense $py @("ai", "risks", $currentDir, "--json", "--markdown") "AI_RISKS" | Out-Null

$target = Select-ExplainPattern (Join-Path $currentDir "patterns.json")
$explainArgs = @("ai", "explain", $currentDir, "--pattern-id", [string]$target.pattern_id, "--json", "--markdown")
if ([string]$target.status -eq "suspected") { $explainArgs += "--with-drilldown" }
Write-Info "Generating AI explain for pattern $($target.pattern_id)..."
Invoke-RepoSense $py $explainArgs "AI_EXPLAIN" | Out-Null

Write-Info "Running health scan..."
Invoke-RepoSense $py @("health", "scan", $currentDir, "--repo", $fixtureRepo, "--json", "--markdown") "health scan" | Out-Null

Write-Info "Running authz scan..."
Invoke-RepoSense $py @("authz", "scan", $currentDir, "--repo", $fixtureRepo, "--json", "--markdown") "authz scan" | Out-Null

Write-Info "Running authz matrix..."
Invoke-RepoSense $py @("authz", "matrix", $currentDir, "--repo", $fixtureRepo, "--contract", $contractPath, "--json", "--markdown") "authz matrix" | Out-Null

Write-Info "Generating repository review report..."
Invoke-RepoSense $py @("review", "report", $currentDir, "--json", "--markdown") "review report" | Out-Null

Write-Info "Rebuilding Context Pack with REVIEW section..."
$ctxCode = "from reposense.context_pack import build_context_pack, zip_context_pack; build_context_pack(r'$($currentDir.Replace('\','\\'))'); zip_context_pack(r'$($currentDir.Replace('\','\\'))')"
Invoke-PythonCode $py $ctxCode "CONTEXT_PACK_REVIEW"

Write-Info "Refreshing run manifest..."
Invoke-RepoSense $py @("run", "manifest", $currentDir, "--json") "RUN_MANIFEST" | Out-Null

$required = @(
  "report.html",
  "backend_verifier_report.md",
  "backend_verifier_report.json",
  "repository_review_report.md",
  "repository_review_report.json",
  "review_risk_matrix.json",
  "human_review_required.md",
  "code_health.json",
  "code_health_summary.json",
  "maintainability_risks.json",
  "permission_surface.json",
  "permission_risks.json",
  "permission_risk_report.md",
  "human_permission_review_required.md",
  "authz_matrix_diff.json",
  "authz_matrix_report.md",
  "authz_negative_test_plan.md",
  "patterns.json",
  "pattern_summary.json",
  "ai_summary.md",
  "ai_risks\risks.md",
  "exports\context_pack.zip",
  "context_pack\REVIEW\README.md",
  "context_pack\REVIEW\ai_maintenance_constraints.md",
  "run_manifest.json"
)
foreach ($r in $required) { Assert-Exists $r }
$explainAny = Get-ChildItem -Path (Join-Path $currentDir "ai_explain") -Filter "explain.md" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $explainAny) { Fail "ASSERT" "missing ai_explain/*/explain.md" }

$currentRunMd = Join-Path $canonicalRoot "CURRENT_RUN.md"
$generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$content = @"
# Canonical Repository Review Demo

- canonical path: .reposense_review_demo/current/
- source fixture: tests/fixtures/repos/review_demo_full/
- generated_at: $generatedAt
- source build path: .reposense_review_demo/_build/

## Key outputs

- report.html
- backend_verifier_report.md
- repository_review_report.md
- review_risk_matrix.json
- human_review_required.md
- code_health_summary.json
- permission_risk_report.md
- authz_matrix_report.md
- authz_negative_test_plan.md
- context_pack/REVIEW/README.md
- exports/context_pack.zip
- run_manifest.json

## Screenshot pages

- .reposense_review_demo/current/report.html
- .reposense_review_demo/current/repository_review_report.md
- .reposense_review_demo/current/human_review_required.md
- .reposense_review_demo/current/code_health_summary.json
- .reposense_review_demo/current/permission_risk_report.md
- .reposense_review_demo/current/authz_matrix_report.md
- .reposense_review_demo/current/context_pack/REVIEW/README.md

## Known limitations

- Demo fixture is static and intentionally small.
- Findings are evidence-guided review signals, not correctness or security proof.
- The fixture is not executed as application code.
"@
[System.IO.File]::WriteAllText($currentRunMd, $content, (New-Object System.Text.UTF8Encoding($false)))

Write-Host ""
Write-Host "=== RepoSense Review Demo Completed ===" -ForegroundColor Green
Write-Host "current: $currentDir"
Write-Host "pointer: $currentRunMd"
