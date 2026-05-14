Param(
  [string]$Repo = "tests/fixtures/repos/java_api_queue_db_closure_min",
  [string]$Out = ".reposense_demo",
  [string]$Profile = "demo",
  [switch]$OpenReport,
  [switch]$OpenLearn
)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$tempRoot = Join-Path $repoRoot ".tmp_test_runs\temp"
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$env:TMP = $tempRoot
$env:TEMP = $tempRoot
$env:TMPDIR = $tempRoot

function Fail-Stage {
  Param(
    [string]$Stage,
    [string]$Message
  )
  Write-Host "[ERROR][$Stage] $Message" -ForegroundColor Red
  exit 1
}

function Resolve-Python {
  $venvPy = Join-Path (Get-Location) ".venv\Scripts\python.exe"
  if (Test-Path $venvPy) {
    return @{ Kind = "path"; Cmd = $venvPy; Display = $venvPy }
  }

  function Test-RepoSenseCLI {
    Param([hashtable]$Candidate)
    try {
      if ($Candidate.Kind -eq "py") {
        & $Candidate.Cmd -3 -m reposense --help *> $null
      } else {
        & $Candidate.Cmd -m reposense --help *> $null
      }
      return ($LASTEXITCODE -eq 0)
    } catch {
      return $false
    }
  }

  $candidates = @()
  $preferred = "D:\安装\Python\python.exe"
  if (Test-Path $preferred) {
    $candidates += @{ Kind = "path"; Cmd = $preferred; Display = $preferred }
  }

  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd) {
    $candidates += @{ Kind = "name"; Cmd = "python"; Display = $pythonCmd.Source }
  }

  $pyCmd = Get-Command py -ErrorAction SilentlyContinue
  if ($pyCmd) {
    $candidates += @{ Kind = "py"; Cmd = "py"; Display = $pyCmd.Source }
  }

  foreach ($candidate in $candidates) {
    if (Test-RepoSenseCLI -Candidate $candidate) {
      return $candidate
    }
    Write-Host "[WARN][ENV] skip python candidate (reposense CLI unavailable): $($candidate.Display)" -ForegroundColor Yellow
  }

  return $null
}

function Invoke-RepoSense {
  Param(
    [hashtable]$Py,
    [string[]]$RsArgs,
    [string]$Stage,
    [switch]$Capture
  )

  if ($Py.Kind -eq "py") {
    if ($Capture) {
      $out = & $Py.Cmd -3 -m reposense @RsArgs 2>&1
      if ($LASTEXITCODE -ne 0) {
        $msg = ($out | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($msg)) { $msg = "command failed" }
        Fail-Stage -Stage $Stage -Message $msg
      }
      return ,$out
    }

    & $Py.Cmd -3 -m reposense @RsArgs
    if ($LASTEXITCODE -ne 0) { Fail-Stage -Stage $Stage -Message "reposense command failed: $($RsArgs -join ' ')" }
    return @()
  }

  if ($Capture) {
    $out = & $Py.Cmd -m reposense @RsArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
      $msg = ($out | Out-String).Trim()
      if ([string]::IsNullOrWhiteSpace($msg)) { $msg = "command failed" }
      Fail-Stage -Stage $Stage -Message $msg
    }
    return ,$out
  }

  & $Py.Cmd -m reposense @RsArgs
  if ($LASTEXITCODE -ne 0) { Fail-Stage -Stage $Stage -Message "reposense command failed: $($RsArgs -join ' ')" }
  return @()
}

function Invoke-PythonVersion {
  Param([hashtable]$Py)
  if ($Py.Kind -eq "py") {
    & $Py.Cmd -3 --version
    if ($LASTEXITCODE -ne 0) { Fail-Stage -Stage "ENV" -Message "failed to query python version" }
    return
  }
  & $Py.Cmd --version
  if ($LASTEXITCODE -ne 0) { Fail-Stage -Stage "ENV" -Message "failed to query python version" }
}

function Get-RunDirFromOutput {
  Param([object[]]$Lines)
  $jsonLines = $Lines | Where-Object {
    $s = [string]$_
    $s.StartsWith("{") -and $s.EndsWith("}")
  }

  foreach ($line in ($jsonLines | Select-Object -Last 5)) {
    try {
      $obj = $line | ConvertFrom-Json
      if ($obj.run_dir) {
        return [string]$obj.run_dir
      }
    } catch {
      continue
    }
  }
  return ""
}

function Select-ExplainPattern {
  Param([string]$PatternsPath)
  if (-not (Test-Path $PatternsPath)) {
    Fail-Stage -Stage "AI_EXPLAIN" -Message "missing patterns.json: $PatternsPath"
  }

  $patternsObj = Get-Content $PatternsPath -Raw | ConvertFrom-Json
  $patterns = @($patternsObj.patterns)
  if ($patterns.Count -eq 0) {
    Fail-Stage -Stage "AI_EXPLAIN" -Message "patterns.json has no patterns"
  }

  function SeverityWeight([string]$s) {
    switch ($s) {
      "high" { return 3 }
      "medium" { return 2 }
      "low" { return 1 }
      default { return 0 }
    }
  }

  function StatusWeight([string]$s) {
    switch ($s) {
      "confirmed" { return 2 }
      "suspected" { return 1 }
      default { return 0 }
    }
  }

  $selected = $patterns |
    Sort-Object `
      @{ Expression = { SeverityWeight([string]$_.severity) }; Descending = $true }, `
      @{ Expression = { StatusWeight([string]$_.status) }; Descending = $true }, `
      @{ Expression = { [double]($_.confidence) }; Descending = $true }, `
      @{ Expression = { [string]$_.pattern_id }; Descending = $false } |
    Select-Object -First 1

  if (-not $selected -or -not $selected.pattern_id) {
    Fail-Stage -Stage "AI_EXPLAIN" -Message "unable to select explain target pattern"
  }

  return $selected
}

Write-Host "=== RepoSense Demo Run ==="
Write-Host "Repo: $Repo"
Write-Host "Out:  $Out"
Write-Host "Profile: $Profile"

$py = Resolve-Python
if (-not $py) {
  Fail-Stage -Stage "ENV" -Message "python interpreter not found (checked D:\安装\Python\python.exe, python, py -3)"
}
Write-Host "Python interpreter: $($py.Display)"
Invoke-PythonVersion -Py $py

if (-not (Test-Path $Repo)) {
  Fail-Stage -Stage "ENV" -Message "repo path does not exist: $Repo"
}

New-Item -ItemType Directory -Path $Out -Force | Out-Null

$ciOut = Invoke-RepoSense -Py $py -RsArgs @("ci", "run", "--repo", $Repo, "--out", $Out, "--profile", $Profile, "--with-context-pack", "--json") -Stage "CI_RUN" -Capture
$runDir = Get-RunDirFromOutput -Lines $ciOut
if ([string]::IsNullOrWhiteSpace($runDir) -or -not (Test-Path $runDir)) {
  Fail-Stage -Stage "CI_RUN" -Message "failed to resolve run_dir from ci output"
}
Write-Host "run_dir: $runDir"

Invoke-RepoSense -Py $py -RsArgs @("learn", "build", $runDir, "--out", (Join-Path $runDir "learn"), "--concept-graph", "scripts/concept_graph_demo.json") -Stage "CI_RUN" | Out-Null
Invoke-RepoSense -Py $py -RsArgs @("ai", "patterns", $runDir, "--json") -Stage "AI_PATTERNS" | Out-Null
Invoke-RepoSense -Py $py -RsArgs @("ai", "summary", $runDir, "--json", "--markdown") -Stage "AI_SUMMARY" | Out-Null
Invoke-RepoSense -Py $py -RsArgs @("ai", "risks", $runDir, "--json", "--markdown") -Stage "AI_RISKS" | Out-Null

$patternsPath = Join-Path $runDir "patterns.json"
$target = Select-ExplainPattern -PatternsPath $patternsPath
$explainArgs = @("ai", "explain", $runDir, "--pattern-id", [string]$target.pattern_id, "--json", "--markdown")
if ([string]$target.status -eq "suspected") {
  $explainArgs += "--with-drilldown"
}
Invoke-RepoSense -Py $py -RsArgs $explainArgs -Stage "AI_EXPLAIN" | Out-Null

Invoke-RepoSense -Py $py -RsArgs @("patch", "exports", $runDir) -Stage "PATCH_EXPORTS" | Out-Null
Invoke-RepoSense -Py $py -RsArgs @("run", "manifest", $runDir, "--json") -Stage "RUN_MANIFEST" | Out-Null

$reportPath = Join-Path $runDir "report.html"
$learnPath = Join-Path $runDir "learn\index.html"
$summaryPath = Join-Path $runDir "ai_summary.md"
$risksPath = Join-Path $runDir "ai_risks\risks.md"
$manifestPath = Join-Path $runDir "run_manifest.json"

$explainFile = Get-ChildItem -Path (Join-Path $runDir "ai_explain") -Filter "explain.md" -Recurse -ErrorAction SilentlyContinue |
  Sort-Object FullName |
  Select-Object -First 1
if (-not $explainFile) {
  Fail-Stage -Stage "AI_EXPLAIN" -Message "no explain.md generated under ai_explain"
}

$mustExist = @(
  @{ Stage = "CI_RUN"; Path = $reportPath },
  @{ Stage = "CI_RUN"; Path = $learnPath },
  @{ Stage = "AI_PATTERNS"; Path = $patternsPath },
  @{ Stage = "AI_SUMMARY"; Path = $summaryPath },
  @{ Stage = "AI_RISKS"; Path = $risksPath },
  @{ Stage = "AI_EXPLAIN"; Path = $explainFile.FullName },
  @{ Stage = "RUN_MANIFEST"; Path = $manifestPath }
)

foreach ($item in $mustExist) {
  if (-not (Test-Path $item.Path)) {
    Fail-Stage -Stage $item.Stage -Message "missing required artifact: $($item.Path)"
  }
}

Write-Host ""
Write-Host "=== Demo Completed ===" -ForegroundColor Green
Write-Host "run_dir: $runDir"
Write-Host "report.html: $reportPath"
Write-Host "learn/index.html: $learnPath"
Write-Host "patterns.json: $patternsPath"
Write-Host "ai_summary.md: $summaryPath"
Write-Host "ai_risks/risks.md: $risksPath"
Write-Host "ai_explain/explain.md: $($explainFile.FullName)"
Write-Host "run_manifest.json: $manifestPath"
Write-Host "selected_explain_pattern: $($target.pattern_id) (severity=$($target.severity), status=$($target.status))"

if ($OpenReport) {
  Start-Process $reportPath | Out-Null
}
if ($OpenLearn) {
  Start-Process $learnPath | Out-Null
}
