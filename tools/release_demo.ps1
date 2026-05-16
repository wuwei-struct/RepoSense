Param()

$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-WarnMsg([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail([string]$m) { Write-Host "[ERROR] $m" -ForegroundColor Red; exit 1 }

$repoRoot = (Get-Location).Path
$tmpRoot = Join-Path $repoRoot ".tmp_test_runs\temp"
New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null
$env:TMP = $tmpRoot
$env:TEMP = $tmpRoot
$env:TMPDIR = $tmpRoot

$archiveRoot = Join-Path $repoRoot "docs\archive\local-artifacts\root-moved"
New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null
$movedLog = Join-Path $repoRoot "docs\archive\local-artifacts\MOVED_FROM_ROOT.md"
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

function Append-MissingLog([string]$src, [string]$note) {
  Add-Content -Encoding UTF8 -Path $movedLog -Value "| $src | missing | $note |"
}

function Move-Safe([string]$srcPath, [string]$reason) {
  if (-not (Test-Path $srcPath)) {
    Append-MissingLog $srcPath "path not found at release demo migration time"
    return $null
  }
  $name = Split-Path -Leaf $srcPath
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $dstPath = Join-Path $archiveRoot "$name-$stamp"
  Move-Item -LiteralPath $srcPath -Destination $dstPath
  Append-MoveLog $srcPath $dstPath $reason
  Write-Info "Moved: $srcPath -> $dstPath"
  return $dstPath
}

function Resolve-Python {
  $venvPy = Join-Path $repoRoot ".venv\Scripts\python.exe"
  if (Test-Path $venvPy) { return $venvPy }
  $preferred = "D:\安装\Python\python.exe"
  if (Test-Path $preferred) { return $preferred }
  $pyCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pyCmd) { return "python" }
  $py3Cmd = Get-Command py -ErrorAction SilentlyContinue
  if ($py3Cmd) { return "py -3" }
  return $null
}

function Invoke-RepoSense([string]$pythonCmd, [string[]]$rsArgs) {
  if ($pythonCmd -eq "py -3") {
    & py -3 -m reposense @rsArgs
  } elseif ($pythonCmd -eq "python") {
    & python -m reposense @rsArgs
  } else {
    & $pythonCmd -m reposense @rsArgs
  }
  if ($LASTEXITCODE -ne 0) {
    Fail "reposense command failed: $($rsArgs -join ' ')"
  }
}

function Ensure-Learn-NonEmpty([string]$pythonCmd, [string]$runDir) {
  $learnIndex = Join-Path $runDir "learn\index.html"
  if (-not (Test-Path $learnIndex)) {
    Fail "missing learn/index.html in $runDir"
  }
  $len = (Get-Item $learnIndex).Length
  if ($len -ge 900) {
    Write-Info "Learn index is non-empty (length=$len)"
    return
  }

  Write-WarnMsg "Learn index looks empty (length=$len). Rebuilding learn site with release concept graph."
  $casesOut = Join-Path $runDir "learn_cases"
  Invoke-RepoSense $pythonCmd @("learn","extract-cases",$runDir,"--out",$casesOut,"--json")

  $idxPath = Join-Path $casesOut "cases_index.json"
  if (-not (Test-Path $idxPath)) {
    Fail "learn cases index not found: $idxPath"
  }
  $idx = Get-Content $idxPath -Raw | ConvertFrom-Json
  $conceptIds = @()
  if ($idx.by_concept -and $idx.by_concept.PSObject -and $idx.by_concept.PSObject.Properties) {
    $conceptIds = @($idx.by_concept.PSObject.Properties.Name)
  }
  if ($conceptIds.Count -eq 0 -and $idx.cases) {
    $conceptIds = @($idx.cases | ForEach-Object { [string]$_.concept_id } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  }
  if ($conceptIds.Count -gt 0) {
    $conceptIds = @($conceptIds | Sort-Object -Unique)
  }
  if ($conceptIds.Count -eq 0) {
    Fail "learn rebuild aborted: no concept ids extracted from cases_index.json"
  }

  $concepts = @()
  foreach ($cid in $conceptIds) {
    $concepts += [ordered]@{
      concept_id = $cid
      concept = $cid
      title = $cid
      short_definition = "Release demo concept for $cid"
      category = "Release Demo"
      prerequisites = @()
      related = @()
    }
  }
  $graphObj = [ordered]@{
    schema_version = "1.0"
    concepts = $concepts
  }
  $graphPath = Join-Path $runDir "learn_concept_graph_for_release.json"
  $graphJson = $graphObj | ConvertTo-Json -Depth 8
  [System.IO.File]::WriteAllText($graphPath, $graphJson, (New-Object System.Text.UTF8Encoding($false)))

  Invoke-RepoSense $pythonCmd @("learn","build",$runDir,"--out",(Join-Path $runDir "learn"),"--concept-graph",$graphPath)

  $len2 = (Get-Item $learnIndex).Length
  if ($len2 -lt 900) {
    Fail "learn/index.html still looks empty after rebuild (length=$len2)"
  }
  Write-Info "Learn index rebuilt and non-empty (length=$len2)"
}

$canonicalRoot = Join-Path $repoRoot ".reposense_release_demo"
$currentDir = Join-Path $canonicalRoot "current"
$buildOut = Join-Path $canonicalRoot "_build"
New-Item -ItemType Directory -Force -Path $canonicalRoot | Out-Null
New-Item -ItemType Directory -Force -Path $buildOut | Out-Null

if (Test-Path $currentDir) {
  Move-Safe $currentDir "archive previous canonical release demo"
}

$legacyCandidates = @(
  ".reposense_demo_release_assets_current",
  ".reposense_demo_release_assets",
  ".reposense_demo_localvenv",
  ".reposense_demo_localvenv_fix",
  ".reposense_demo_prod05"
)
foreach ($d in $legacyCandidates) {
  $p = Join-Path $repoRoot $d
  if (Test-Path $p) {
    Move-Safe $p "archive legacy demo output directory"
  } else {
    Append-MissingLog $p "legacy demo directory not present"
  }
}

Write-Info "Building demo run via tools/demo_run.ps1 ..."
& powershell -ExecutionPolicy Bypass -File "tools/demo_run.ps1" -Out $buildOut
if ($LASTEXITCODE -ne 0) {
  Fail "tools/demo_run.ps1 failed"
}

$latestRun = Get-ChildItem -Path $buildOut -Directory -Filter "run-*" | Sort-Object Name -Descending | Select-Object -First 1
if (-not $latestRun) {
  Fail "no run-* directory found under $buildOut"
}

Copy-Item -LiteralPath $latestRun.FullName -Destination $currentDir -Recurse
Write-Info "Copied canonical run: $($latestRun.FullName) -> $currentDir"

$py = Resolve-Python
if (-not $py) {
  Fail "python interpreter not found for backend/learn post-steps"
}

$backendJson = Join-Path $currentDir "backend_verifier_report.json"
$backendMd = Join-Path $currentDir "backend_verifier_report.md"
if ((-not (Test-Path $backendJson)) -or (-not (Test-Path $backendMd))) {
  Write-Info "Generating backend verifier report..."
  Invoke-RepoSense $py @("backend","report",$currentDir,"--json","--markdown")
}

Ensure-Learn-NonEmpty $py $currentDir

$required = @(
  "report.html",
  "patterns.json",
  "pattern_summary.json",
  "ai_summary.md",
  "ai_risks\risks.md",
  "run_manifest.json",
  "exports\context_pack.zip",
  "learn\index.html",
  "backend_verifier_report.json",
  "backend_verifier_report.md"
)
foreach ($r in $required) {
  $p = Join-Path $currentDir $r
  if (-not (Test-Path $p)) {
    Fail "missing required artifact in canonical demo: $p"
  }
}
$explainAny = Get-ChildItem -Path (Join-Path $currentDir "ai_explain") -Filter "explain.md" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $explainAny) {
  Fail "missing ai_explain/*/explain.md in canonical demo"
}

$currentRunMd = Join-Path $canonicalRoot "CURRENT_RUN.md"
$generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$reportPath = ".reposense_release_demo/current/report.html"
$learnPath = ".reposense_release_demo/current/learn/index.html"
$currentRunText = @(
  '# Canonical Release Demo Run',
  '',
  '- canonical path: .reposense_release_demo/current/',
  "- generated_at: $generatedAt",
  '- source build path: .reposense_release_demo/_build/',
  "- copied from: $($latestRun.FullName)",
  '',
  '## Key outputs',
  '',
  '- report.html',
  '- learn/index.html',
  '- backend_verifier_report.json',
  '- backend_verifier_report.md',
  '- patterns.json',
  '- pattern_summary.json',
  '- ai_summary.md',
  '- ai_risks/risks.md',
  '- ai_explain/*/explain.md',
  '- exports/context_pack.zip',
  '- run_manifest.json',
  '',
  '## Screenshot pages',
  '',
  "- $reportPath",
  "- $learnPath"
)
$currentRunText -join "`r`n" | Set-Content -Encoding UTF8 $currentRunMd

Write-Host ""
Write-Host "=== Canonical release demo ready ===" -ForegroundColor Green
Write-Host "current: .reposense_release_demo/current/"
Write-Host "report:  .reposense_release_demo/current/report.html"
Write-Host "learn:   .reposense_release_demo/current/learn/index.html"
Write-Host "marker:  .reposense_release_demo/CURRENT_RUN.md"
