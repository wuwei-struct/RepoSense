[CmdletBinding()]
param(
  [string]$CaseId,
  [string]$RepoPath,
  [switch]$AllowNetwork,
  [switch]$SkipClone,
  [switch]$KeepWorkspace,
  [switch]$ContinueOnCaseFailure
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn([string]$Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Fail([string]$Stage, [string]$Message) { throw "[$Stage] $Message" }

$repoRoot = (Get-Location).Path
$configPath = Join-Path $repoRoot "tools\validation\real_repo_cases.json"
$validatorPath = Join-Path $repoRoot "tools\validation\real_repo_smoke.py"
$queueCacheValidatorPath = Join-Path $repoRoot "tools\validation\queue_cache_validation.py"
$queueReliabilityValidatorPath = Join-Path $repoRoot "tools\validation\queue_retry_idempotency_validation.py"
$typeormValidatorPath = Join-Path $repoRoot "tools\validation\typeorm_db_validation.py"
$typescriptTransactionValidatorPath = Join-Path $repoRoot "tools\validation\typescript_transaction_validation.py"
$smokeRoot = Join-Path $repoRoot ".reposense_real_repo_smoke"
$currentRoot = Join-Path $smokeRoot "current"
$workspaceRoot = Join-Path $smokeRoot "workspaces"
$workspaceHistory = Join-Path $smokeRoot "workspace-history"
$buildRoot = Join-Path $smokeRoot "_build"
$historyRoot = Join-Path $smokeRoot "history"
$tempRoot = Join-Path $repoRoot ".tmp_test_runs\temp"

foreach ($path in @($smokeRoot, $workspaceRoot, $workspaceHistory, $buildRoot, $historyRoot, $tempRoot)) {
  New-Item -ItemType Directory -Force -Path $path | Out-Null
}
$env:TMP = $tempRoot
$env:TEMP = $tempRoot
$env:TMPDIR = $tempRoot

function Resolve-Python {
  $venv = Join-Path $repoRoot ".venv\Scripts\python.exe"
  if (Test-Path $venv) { return @{ Cmd = $venv; Prefix = @(); Display = $venv } }
  $preferred = "D:\安装\Python\python.exe"
  if (Test-Path $preferred) { return @{ Cmd = $preferred; Prefix = @(); Display = $preferred } }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) { return @{ Cmd = "python"; Prefix = @(); Display = $python.Source } }
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return @{ Cmd = "py"; Prefix = @("-3"); Display = $py.Source } }
  return $null
}

$python = Resolve-Python
if (-not $python) { Fail "ENV" "Python interpreter not found." }
if (-not (Test-Path $configPath)) { Fail "CONFIG" "Missing case config: $configPath" }
if (-not (Test-Path $validatorPath)) { Fail "CONFIG" "Missing validator: $validatorPath" }
if (-not (Test-Path $queueCacheValidatorPath)) { Fail "CONFIG" "Missing queue/cache validator: $queueCacheValidatorPath" }
if (-not (Test-Path $queueReliabilityValidatorPath)) { Fail "CONFIG" "Missing queue reliability validator: $queueReliabilityValidatorPath" }
if (-not (Test-Path $typeormValidatorPath)) { Fail "CONFIG" "Missing TypeORM validator: $typeormValidatorPath" }
if (-not (Test-Path $typescriptTransactionValidatorPath)) { Fail "CONFIG" "Missing TypeScript transaction validator: $typescriptTransactionValidatorPath" }
Write-Info "Python interpreter: $($python.Display)"

function Write-Utf8Json([string]$Path, [object]$Value) {
  $json = $Value | ConvertTo-Json -Depth 20
  [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}

function Get-OutputSummary([object[]]$Output) {
  $lines = @($Output | ForEach-Object { [string]$_ })
  if ($lines.Count -gt 20) { $lines = $lines[($lines.Count - 20)..($lines.Count - 1)] }
  $text = ($lines -join "`n").Trim()
  if ($text.Length -gt 4000) { return $text.Substring($text.Length - 4000) }
  return $text
}

function Invoke-LoggedCommand {
  param(
    [string]$Stage,
    [string]$Command,
    [string[]]$Arguments,
    [System.Collections.Generic.List[object]]$StageRecords,
    [int[]]$AllowedExitCodes = @(0)
  )
  $watch = [System.Diagnostics.Stopwatch]::StartNew()
  $previousErrorAction = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    $output = @(& $Command @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousErrorAction
  }
  $watch.Stop()
  $ok = $AllowedExitCodes -contains $exitCode
  $StageRecords.Add([pscustomobject]@{
    stage = $Stage
    ok = $ok
    exit_code = $exitCode
    duration_ms = [int]$watch.ElapsedMilliseconds
    output_summary = Get-OutputSummary $output
  }) | Out-Null
  if (-not $ok) { Fail $Stage "Command failed with exit code $exitCode. $(Get-OutputSummary $output)" }
  return ,$output
}

function Invoke-Python {
  param(
    [string]$Stage,
    [string[]]$Arguments,
    [System.Collections.Generic.List[object]]$StageRecords,
    [int[]]$AllowedExitCodes = @(0)
  )
  $allArgs = @($python.Prefix) + $Arguments
  return Invoke-LoggedCommand $Stage $python.Cmd $allArgs $StageRecords $AllowedExitCodes
}

function Invoke-RepoSense {
  param(
    [string]$Stage,
    [string[]]$Arguments,
    [System.Collections.Generic.List[object]]$StageRecords,
    [int[]]$AllowedExitCodes = @(0)
  )
  return Invoke-Python $Stage (@("-m", "reposense") + $Arguments) $StageRecords $AllowedExitCodes
}

function Archive-PreviousCurrent {
  if (-not (Test-Path $currentRoot)) { return }
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $baseName = "current-$stamp"
  $localHistory = Join-Path $historyRoot $baseName
  $suffix = 1
  while (Test-Path $localHistory) {
    $localHistory = Join-Path $historyRoot "$baseName-$suffix"
    $suffix++
  }
  Move-Item -LiteralPath $currentRoot -Destination $localHistory
  Write-Info "Moved previous full local result to $localHistory"
}

Archive-PreviousCurrent
New-Item -ItemType Directory -Force -Path (Join-Path $currentRoot "cases") | Out-Null

$config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$configuredCases = @($config.cases)

if ($RepoPath) {
  if ([string]::IsNullOrWhiteSpace($CaseId)) { $CaseId = "local-review-demo" }
  $configured = @($configuredCases | Where-Object { $_.case_id -eq $CaseId } | Select-Object -First 1)
  if ($configured.Count -gt 0) {
    $selectedCases = @($configured[0])
  } else {
    $selectedCases = @([pscustomobject]@{
      case_id = $CaseId
      name = "Local repository smoke: $CaseId"
      language = "mixed"
      repository_url = "local fixture"
      default_branch = "n/a"
      commit_sha = "local-fixture"
      license = "RepoSense test fixture"
      expected_capabilities = @("local_static_analysis")
      max_repository_size_mb = 50
      enabled = $true
      notes = "Local no-network validation path."
    })
  }
} elseif ($CaseId) {
  $selectedCases = @($configuredCases | Where-Object { $_.case_id -eq $CaseId -and $_.enabled })
  if ($selectedCases.Count -eq 0) { Fail "CONFIG" "Unknown or disabled CaseId: $CaseId" }
} else {
  $selectedCases = @($configuredCases | Where-Object { $_.enabled })
}

function Get-RepositorySizeMb([string]$Path) {
  $bytes = (Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "[\\/]\.git[\\/]" } |
    Measure-Object -Property Length -Sum).Sum
  if (-not $bytes) { $bytes = 0 }
  return [math]::Round(([double]$bytes / 1MB), 2)
}

function Resolve-CaseRepository([object]$Case, [System.Collections.Generic.List[object]]$StageRecords) {
  if ($RepoPath) {
    $resolved = (Resolve-Path -LiteralPath $RepoPath -ErrorAction Stop).Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Container)) { Fail "SOURCE" "RepoPath is not a directory: $RepoPath" }
    return @{ Path = $resolved; Mode = "local_path"; ManagedWorkspace = $false; Commit = "local-fixture" }
  }

  $workspace = Join-Path $workspaceRoot ([string]$Case.case_id)
  if (Test-Path $workspace) {
    $previousErrorAction = $ErrorActionPreference
    try {
      $ErrorActionPreference = "Continue"
      $headOutput = @(& git -C $workspace rev-parse HEAD 2>&1)
      $headCode = $LASTEXITCODE
    } finally {
      $ErrorActionPreference = $previousErrorAction
    }
    $head = if ($headCode -eq 0) { ([string]($headOutput | Select-Object -Last 1)).Trim() } else { "" }
    if ($headCode -eq 0 -and $head -eq [string]$Case.commit_sha) {
      return @{ Path = $workspace; Mode = "existing_workspace"; ManagedWorkspace = $true; Commit = $head }
    }
    if ($SkipClone -or -not $AllowNetwork) {
      Fail "SOURCE" "Existing workspace is not at pinned commit $($Case.commit_sha), and network refresh is disabled."
    }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $oldWorkspace = Join-Path $workspaceHistory ("$($Case.case_id)-$stamp")
    Move-Item -LiteralPath $workspace -Destination $oldWorkspace
    Write-Info "Moved mismatched workspace to $oldWorkspace"
  }

  if ($SkipClone) { Fail "SOURCE" "SkipClone requested but workspace is missing: $workspace" }
  if (-not $AllowNetwork) { Fail "SOURCE" "No local workspace for $($Case.case_id). Re-run with -AllowNetwork or -RepoPath." }

  New-Item -ItemType Directory -Force -Path $workspace | Out-Null
  Invoke-LoggedCommand "git_init" "git" @("-C", $workspace, "init") $StageRecords | Out-Null
  Invoke-LoggedCommand "git_remote" "git" @("-C", $workspace, "remote", "add", "origin", [string]$Case.repository_url) $StageRecords | Out-Null
  Invoke-LoggedCommand "git_fetch_pinned_commit" "git" @("-C", $workspace, "fetch", "--depth", "1", "origin", [string]$Case.commit_sha) $StageRecords | Out-Null
  Invoke-LoggedCommand "git_checkout_pinned_commit" "git" @("-C", $workspace, "checkout", "--detach", "FETCH_HEAD") $StageRecords | Out-Null
  $head = (& git -C $workspace rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0 -or $head -ne [string]$Case.commit_sha) {
    Fail "SOURCE" "Pinned commit verification failed for $($Case.case_id). Expected $($Case.commit_sha), got $head."
  }
  return @{ Path = $workspace; Mode = "network_clone"; ManagedWorkspace = $true; Commit = $head }
}

$caseFailures = [System.Collections.Generic.List[string]]::new()

foreach ($case in $selectedCases) {
  $caseIdValue = [string]$case.case_id
  $caseDir = Join-Path $currentRoot ("cases\" + $caseIdValue)
  $runTarget = Join-Path $caseDir "run"
  New-Item -ItemType Directory -Force -Path $caseDir | Out-Null
  $stageRecords = [System.Collections.Generic.List[object]]::new()
  $caseWatch = [System.Diagnostics.Stopwatch]::StartNew()
  $failedStage = ""
  $source = $null
  $sourceMeta = $null
  $runDir = ""

  try {
    Write-Info "Starting real repository smoke case: $caseIdValue"
    $source = Resolve-CaseRepository $case $stageRecords
    $sizeMb = Get-RepositorySizeMb $source.Path
    if ($sizeMb -gt [double]$case.max_repository_size_mb) {
      Fail "SIZE_BUDGET" "Repository size $sizeMb MB exceeds budget $($case.max_repository_size_mb) MB."
    }
    $sourceMeta = [ordered]@{
      case_id = $caseIdValue
      name = [string]$case.name
      language = [string]$case.language
      repository_url = [string]$case.repository_url
      default_branch = [string]$case.default_branch
      commit_sha = [string]$case.commit_sha
      resolved_commit = [string]$source.Commit
      license = [string]$case.license
      expected_capabilities = @($case.expected_capabilities)
      source_mode = [string]$source.Mode
      source_path = if ($source.ManagedWorkspace) { ".reposense_real_repo_smoke/workspaces/$caseIdValue/" } else { [string]$RepoPath }
      repository_size_mb = $sizeMb
      max_repository_size_mb = [double]$case.max_repository_size_mb
      target_code_executed = $false
    }
    Write-Utf8Json (Join-Path $caseDir "source-meta.json") $sourceMeta

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $caseBuild = Join-Path $buildRoot "$caseIdValue-$stamp"
    New-Item -ItemType Directory -Force -Path $caseBuild | Out-Null
    $ciOutput = Invoke-RepoSense "ci_run" @("ci", "run", "--repo", $source.Path, "--out", $caseBuild, "--profile", "demo", "--with-context-pack", "--json") $stageRecords @(0, 2)
    $latest = Get-ChildItem -LiteralPath $caseBuild -Directory -Filter "run-*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { Fail "ci_run" "No run-* directory generated under $caseBuild." }
    Copy-Item -LiteralPath $latest.FullName -Destination $runTarget -Recurse
    $runDir = $runTarget

    Invoke-RepoSense "backend_report" @("backend", "report", $runDir, "--json", "--markdown") $stageRecords | Out-Null
    Invoke-RepoSense "patterns" @("ai", "patterns", $runDir, "--json") $stageRecords | Out-Null
    Invoke-RepoSense "ai_summary" @("ai", "summary", $runDir, "--json", "--markdown") $stageRecords | Out-Null
    Invoke-RepoSense "ai_risks" @("ai", "risks", $runDir, "--json", "--markdown") $stageRecords | Out-Null
    Invoke-RepoSense "health_scan" @("health", "scan", $runDir, "--repo", $source.Path, "--json", "--markdown") $stageRecords | Out-Null
    Invoke-RepoSense "authz_scan" @("authz", "scan", $runDir, "--repo", $source.Path, "--json", "--markdown") $stageRecords | Out-Null
    $localContract = Join-Path $source.Path "reposense.authz.yaml"
    if ($RepoPath -and (Test-Path $localContract)) {
      Invoke-Python "authz_matrix_inferred" @($validatorPath, "inferred-authz", "--run-dir", $runDir) $stageRecords | Out-Null
    } else {
      Invoke-RepoSense "authz_matrix_inferred" @("authz", "matrix", $runDir, "--repo", $source.Path, "--json", "--markdown") $stageRecords | Out-Null
    }
    Invoke-Python "queue_cache_validation" @(
      $queueCacheValidatorPath,
      "--run-dir", $runDir,
      "--repo-path", $source.Path,
      "--case-id", $caseIdValue,
      "--commit", [string]$source.Commit,
      "--case-dir", $caseDir
    ) $stageRecords | Out-Null
    Invoke-Python "queue_retry_idempotency_validation" @(
      $queueReliabilityValidatorPath,
      "--run-dir", $runDir,
      "--repo-path", $source.Path,
      "--case-id", $caseIdValue,
      "--commit", [string]$source.Commit,
      "--case-dir", $caseDir
    ) $stageRecords | Out-Null
    Invoke-Python "typeorm_db_validation" @(
      $typeormValidatorPath,
      "--run-dir", $runDir,
      "--repo", $source.Path,
      "--case-id", $caseIdValue,
      "--commit-sha", [string]$source.Commit,
      "--case-dir", $caseDir
    ) $stageRecords | Out-Null
    Invoke-Python "typescript_transaction_validation" @(
      $typescriptTransactionValidatorPath,
      "--run-dir", $runDir,
      "--repo", $source.Path,
      "--case-id", $caseIdValue,
      "--commit-sha", [string]$source.Commit,
      "--case-dir", $caseDir
    ) $stageRecords | Out-Null
    Invoke-RepoSense "repository_review" @("review", "report", $runDir, "--json", "--markdown") $stageRecords | Out-Null
    Invoke-RepoSense "quality_gate" @("gate", $runDir, "--json") $stageRecords @(0, 2) | Out-Null

    $contextCode = "import sys; from reposense.context_pack import build_context_pack, zip_context_pack; build_context_pack(sys.argv[1]); zip_context_pack(sys.argv[1])"
    Invoke-Python "context_pack_review" @("-c", $contextCode, $runDir) $stageRecords | Out-Null
    Invoke-RepoSense "run_manifest" @("run", "manifest", $runDir, "--json") $stageRecords | Out-Null
    Invoke-RepoSense "verify_strict" @("verify", $runDir, "--strict", "--json") $stageRecords | Out-Null
  } catch {
    $failedStage = if ($stageRecords.Count -gt 0) { [string]$stageRecords[$stageRecords.Count - 1].stage } else { "setup" }
    $caseFailures.Add($caseIdValue) | Out-Null
    Write-Warn "Case $caseIdValue failed at ${failedStage}: $($_.Exception.Message)"
  } finally {
    $caseWatch.Stop()
    $pipelineMeta = [ordered]@{
      case_id = $caseIdValue
      completed = [string]::IsNullOrWhiteSpace($failedStage)
      failed_stage = $failedStage
      duration_ms = [int]$caseWatch.ElapsedMilliseconds
      stages = @($stageRecords)
      target_code_executed = $false
    }
    Write-Utf8Json (Join-Path $caseDir "pipeline-meta.json") $pipelineMeta

    if ($sourceMeta -and $runDir -and (Test-Path $runDir)) {
      $validatorArgs = @(
        $validatorPath, "validate",
        "--case-id", $caseIdValue,
        "--case-dir", $caseDir,
        "--run-dir", $runDir,
        "--repo-path", $source.Path,
        "--source-meta", (Join-Path $caseDir "source-meta.json"),
        "--pipeline-meta", (Join-Path $caseDir "pipeline-meta.json")
      )
      try {
        Invoke-Python "validation_summary" $validatorArgs $stageRecords @(0, 2) | Out-Null
      } catch {
        $caseFailures.Add($caseIdValue) | Out-Null
        Write-Warn "Validation summary failed for ${caseIdValue}: $($_.Exception.Message)"
      }
    }

    if ($source -and $source.ManagedWorkspace -and -not $KeepWorkspace -and (Test-Path $source.Path)) {
      $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
      $destination = Join-Path $workspaceHistory "$caseIdValue-$stamp"
      Move-Item -LiteralPath $source.Path -Destination $destination
      Write-Info "Moved managed workspace to local ignored history: $destination"
    }
  }

  if ($failedStage -and -not $ContinueOnCaseFailure) { break }
}

$summaryStages = [System.Collections.Generic.List[object]]::new()
$summaryArgs = @($validatorPath, "summary", "--root", $currentRoot, "--config", $configPath)
Invoke-Python "overall_summary" $summaryArgs $summaryStages @(0, 2) | Out-Null

$repoSenseCommit = (& git rev-parse --short HEAD 2>$null).Trim()
if ($LASTEXITCODE -ne 0) { $repoSenseCommit = "unknown" }
$summary = Get-Content (Join-Path $currentRoot "summary.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$caseLines = @($summary.cases | ForEach-Object { "- $($_.case_id): commit=$($_.commit_sha), pipeline=$($_.pipeline_completed), evidence=$($_.evidence_integrity_passed)" })
$pointer = @(
  "# Current Real Repository Review Smoke",
  "",
  "- generated_at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')",
  "- RepoSense commit: $repoSenseCommit",
  "- canonical output path: .reposense_real_repo_smoke/current/",
  "- status: $($summary.status)",
  "- target repository code executed: false",
  "",
  "## Cases",
  ""
) + $caseLines + @(
  "",
  "## Manual review entry points",
  "",
  "- summary.md",
  "- cases/<case_id>/validation.md",
  "- cases/<case_id>/triage-template.json",
  "",
  "The smoke validates evidence-guided outputs. It does not prove repository safety or correctness."
)
[System.IO.File]::WriteAllText((Join-Path $currentRoot "CURRENT_RUN.md"), ($pointer -join [Environment]::NewLine) + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))

Write-Host ""
Write-Host "=== RepoSense Real Repository Review Smoke ===" -ForegroundColor Green
Write-Host "output: $currentRoot"
Write-Host "status: $($summary.status)"
Write-Host "cases: $($summary.case_count)"

if ($caseFailures.Count -gt 0 -or $summary.status -ne "complete") { exit 2 }
exit 0
