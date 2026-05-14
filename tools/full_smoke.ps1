Param(
  [string]$Out = ".reposense_demo_smoke",
  [switch]$SkipFullUnittest
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$tempRoot = Join-Path $repoRoot ".tmp_test_runs\temp"
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$env:TMP = $tempRoot
$env:TEMP = $tempRoot
$env:TMPDIR = $tempRoot

function Resolve-Python {
  $venv = Join-Path (Get-Location) ".venv\Scripts\python.exe"
  if (Test-Path $venv) { return $venv }
  $preferred = "D:\安装\Python\python.exe"
  if (Test-Path $preferred) { return $preferred }
  $p = Get-Command python -ErrorAction SilentlyContinue
  if ($p) { return "python" }
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return "py -3" }
  throw "Python not found"
}

function Invoke-Step {
  Param([string]$Name, [scriptblock]$Body)
  Write-Host "== $Name =="
  & $Body
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] $Name" -ForegroundColor Red
    exit $LASTEXITCODE
  }
}

$py = Resolve-Python
Write-Host "Python: $py"

if ($py -eq "py -3") {
  $run = { param($args) & py -3 @args }
} elseif ($py -eq "python") {
  $run = { param($args) & python @args }
} else {
  $exe = $py
  $run = { param($args) & $exe @args }
}

Invoke-Step "export_oss tests" {
  & $run @("-m", "unittest", "-v",
    "tests.test_export_oss_manifest_has_sha256",
    "tests.test_export_oss_smoke_fails_on_bad_cmd",
    "tests.test_export_oss_smoke_flag_wires_command",
    "tests.test_export_oss_snapshot_can_run_smoke",
    "tests.test_export_oss_snapshot_contains_pyproject")
}

Invoke-Step "docs+demo tests" {
  & $run @("-m", "unittest", "-v",
    "tests.analysis.test_demo_run_smoke",
    "tests.analysis.test_docs_entrypoints_exist",
    "tests.analysis.test_readme_product_sections")
}

if (-not $SkipFullUnittest) {
  Invoke-Step "full unittest" {
    & $run @("-m", "unittest", "-v")
  }
}

Invoke-Step "demo run" {
  powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1 -Out $Out
}

Write-Host ""
Write-Host "Smoke completed." -ForegroundColor Green
Write-Host "Demo output root: $Out"
