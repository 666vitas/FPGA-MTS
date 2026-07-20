[CmdletBinding()]
param(
    [ValidateSet("All", "Rules", "Host")]
    [string]$Scope = "All",

    [switch]$FullHost,

    [string]$PythonPath,

    [ValidateRange(1, 3600)]
    [int]$TimeoutSeconds = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$hostRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot "software\redpitaya_lock_host"))

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Invoke-ExternalChecked {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [bool]$QtOffscreen = $false
    )

    Write-Step $Label
    $payload = [pscustomobject]@{
        FilePath = $FilePath
        Arguments = $Arguments
        WorkingDirectory = $WorkingDirectory
        QtOffscreen = $QtOffscreen
    }

    $job = Start-Job -ScriptBlock {
        param($Data)

        $ErrorActionPreference = "Stop"
        Set-Location -LiteralPath $Data.WorkingDirectory
        if ($Data.QtOffscreen) {
            $env:QT_QPA_PLATFORM = "offscreen"
        }
        $env:PYTHONUTF8 = "1"

        $commandArguments = @($Data.Arguments)
        $commandOutput = & $Data.FilePath @commandArguments 2>&1
        $commandExitCode = $LASTEXITCODE
        foreach ($line in $commandOutput) {
            Write-Output ([string]$line)
        }
        [pscustomobject]@{ VerifyExitCode = [int]$commandExitCode }
    } -ArgumentList $payload

    try {
        $null = Wait-Job -Job $job -Timeout $TimeoutSeconds
        if ($job.State -eq "Running") {
            Stop-Job -Job $job
            throw "$Label timed out after $TimeoutSeconds seconds."
        }
        if ($job.State -eq "Failed") {
            $reason = $job.ChildJobs[0].JobStateInfo.Reason
            throw "$Label failed to start or execute: $reason"
        }

        $records = @(Receive-Job -Job $job)
        $exitRecord = $null
        foreach ($record in $records) {
            if ($record.PSObject.Properties.Name -contains "VerifyExitCode") {
                $exitRecord = $record
            } else {
                Write-Host ([string]$record)
            }
        }

        Assert-Condition ($null -ne $exitRecord) "$Label did not report an exit code."
        Assert-Condition ([int]$exitRecord.VerifyExitCode -eq 0) "$Label returned exit code $($exitRecord.VerifyExitCode)."
    } finally {
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
}

function Test-PowerShellSyntax {
    param([string]$Path)

    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors.Count -gt 0) {
        $details = ($errors | ForEach-Object { $_.Message }) -join "; "
        throw "PowerShell syntax error in $Path`: $details"
    }
}

function Invoke-RulesVerification {
    Write-Step "Rules: git diff --check"
    & git -C $repoRoot diff --check
    Assert-Condition ($LASTEXITCODE -eq 0) "git diff --check failed."

    $activeRuleDocs = @(
        "AGENTS.md",
        "version\STATUS.md",
        "version\CURRENT_REVIEW_MANIFEST.md",
        "version\rules\20_FPGA_MTS_ENGINEERING_WORKFLOW.md"
    )
    $navigationDocs = @("README.md")
    $requiredPaths = @(
        "AGENTS.md",
        "README.md",
        "version\STATUS.md",
        "version\CURRENT_REVIEW_MANIFEST.md",
        "version\rules\20_FPGA_MTS_ENGINEERING_WORKFLOW.md",
        "version\HARDWARE_VALIDATION.md",
        "version\history\README.md",
        "version\history\STATUS_HISTORY_THROUGH_2026-07-18.md",
        "version\history\SKILL_USAGE_GUIDE_LEGACY.md",
        "version\history\CURRENT_MAINLINE_REVIEW_LEGACY.md",
        "v0.94\rtl",
        "v0.94\sim",
        "v0.94\project\redpitaya.xpr",
        "software\redpitaya_lock_host\redpitaya_lock_host",
        "software\redpitaya_lock_host\tests",
        "software\redpitaya_lock_host\scripts",
        "software\redpitaya_lock_host\docs\HARDWARE_CALIBRATION_SOP.md",
        "software\redpitaya_lock_host\docs\DEVELOPMENT_LOG.md",
        "scripts\verify.ps1"
    )

    Write-Step "Rules: required paths"
    foreach ($relativePath in $requiredPaths) {
        $absolutePath = Join-Path $repoRoot $relativePath
        Assert-Condition (Test-Path -LiteralPath $absolutePath) "Required path is missing: $relativePath"
        Write-Host "OK  $relativePath"
    }

    Write-Step "Rules: conflict markers"
    foreach ($relativePath in @($activeRuleDocs + $navigationDocs)) {
        $absolutePath = Join-Path $repoRoot $relativePath
        $matches = @(Select-String -LiteralPath $absolutePath -Pattern "^(<<<<<<<|=======|>>>>>>>)")
        Assert-Condition ($matches.Count -eq 0) "Conflict marker found in $relativePath."
    }
    Write-Host "No active conflict markers found."

    Write-Step "Rules: historical sources are not active"
    $historicalNames = @(
        "SKILL_USAGE_GUIDE.md",
        "CURRENT_MAINLINE_REVIEW.md",
        "AI_REVIEW_README.md",
        "AI_STRICT_REVIEW_ENTRY.md"
    )
    foreach ($relativePath in @($activeRuleDocs + $navigationDocs)) {
        $text = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $repoRoot $relativePath)
        foreach ($historicalName in $historicalNames) {
            Assert-Condition (-not $text.Contains($historicalName)) "$relativePath still references historical source $historicalName."
        }
    }
    Write-Host "No historical compatibility file is declared by active documents."

    Write-Step "Rules: STATUS shape"
    $statusPath = Join-Path $repoRoot "version\STATUS.md"
    $statusLines = @(Get-Content -Encoding utf8 -LiteralPath $statusPath)
    $currentEntries = @($statusLines | Where-Object { $_ -match "^## " })
    Assert-Condition ($currentEntries.Count -eq 1) "STATUS.md must contain exactly one current entry."
    foreach ($heading in @(
        "### Stage",
        "### Current Gate",
        "### Current Blocker",
        "### Verified",
        "### Not Verified",
        "### Forbidden Scope",
        "### Unique Next Experiment"
    )) {
        Assert-Condition ($statusLines -contains $heading) "STATUS.md is missing heading: $heading"
    }
    Write-Host "STATUS.md contains one current Gate and all required sections."

    Write-Step "Rules: active local skills"
    $expectedSkills = @("diagnose", "tdd", "zoom-out")
    $actualSkills = @(
        Get-ChildItem -LiteralPath (Join-Path $repoRoot ".agents\skills") -Directory |
            Sort-Object Name |
            ForEach-Object { $_.Name }
    )
    Assert-Condition (($actualSkills -join "|") -eq ($expectedSkills -join "|")) "Active skill set differs from diagnose/tdd/zoom-out: $($actualSkills -join ', ')"
    foreach ($skill in $expectedSkills) {
        Assert-Condition (Test-Path -LiteralPath (Join-Path $repoRoot ".agents\skills\$skill\SKILL.md")) "Missing SKILL.md for $skill."
    }
    Write-Host "Active skills: $($actualSkills -join ', ')"

    Write-Step "Rules: PowerShell syntax"
    $powerShellFiles = @(
        Get-ChildItem -LiteralPath (Join-Path $repoRoot "scripts") -File -Filter "verify*.ps1"
    ) + @(
        Get-Item -LiteralPath (Join-Path $hostRoot "run_tests_takeover.ps1")
    )
    foreach ($file in $powerShellFiles) {
        Test-PowerShellSyntax $file.FullName
        Write-Host "OK  $($file.FullName.Substring($repoRoot.Length + 1))"
    }
}

function Resolve-PythonExecutable {
    if ($PythonPath) {
        $candidate = if ([IO.Path]::IsPathRooted($PythonPath)) {
            [IO.Path]::GetFullPath($PythonPath)
        } else {
            [IO.Path]::GetFullPath((Join-Path $repoRoot $PythonPath))
        }
    } else {
        $candidate = Join-Path $hostRoot ".venv\Scripts\python.exe"
    }

    Assert-Condition (Test-Path -LiteralPath $candidate -PathType Leaf) "Python executable not found: $candidate"
    return $candidate
}

function Invoke-HostVerification {
    $python = Resolve-PythonExecutable
    Write-Host "Using Python: $python"

    Invoke-ExternalChecked `
        -Label "Host: tabnanny" `
        -FilePath $python `
        -Arguments @("-m", "tabnanny", "redpitaya_lock_host", "tests", "scripts") `
        -WorkingDirectory $hostRoot `
        -QtOffscreen $true

    $pythonFiles = @(
        Get-ChildItem -LiteralPath `
            (Join-Path $hostRoot "redpitaya_lock_host"), `
            (Join-Path $hostRoot "tests"), `
            (Join-Path $hostRoot "scripts") `
            -Recurse -File -Filter "*.py" |
            Sort-Object FullName |
            ForEach-Object { $_.FullName.Substring($hostRoot.Length + 1) }
    )
    Assert-Condition ($pythonFiles.Count -gt 0) "No host Python files were found."
    Invoke-ExternalChecked `
        -Label "Host: py_compile ($($pythonFiles.Count) files)" `
        -FilePath $python `
        -Arguments (@("-m", "py_compile") + $pythonFiles) `
        -WorkingDirectory $hostRoot `
        -QtOffscreen $true

    Invoke-ExternalChecked `
        -Label "Host: pytest collect-only" `
        -FilePath $python `
        -Arguments @("-X", "faulthandler", "-m", "pytest", "--collect-only", "-q", "tests") `
        -WorkingDirectory $hostRoot `
        -QtOffscreen $true

    Invoke-ExternalChecked `
        -Label "Host: targeted pytest" `
        -FilePath $python `
        -Arguments @(
            "-X", "faulthandler", "-m", "pytest", "-q",
            "tests/test_custom_fpga_backend.py",
            "tests/test_operator_voltage_diagnostics.py",
            "-k", "status or identity or calibration or scan or hold or lock or decimation"
        ) `
        -WorkingDirectory $hostRoot `
        -QtOffscreen $true

    if ($FullHost) {
        Invoke-ExternalChecked `
            -Label "Host: full pytest" `
            -FilePath $python `
            -Arguments @("-X", "faulthandler", "-m", "pytest", "-q", "tests") `
            -WorkingDirectory $hostRoot `
            -QtOffscreen $true
    }
}

try {
    if ($Scope -in @("All", "Rules")) {
        Invoke-RulesVerification
    }
    if ($Scope -in @("All", "Host")) {
        Invoke-HostVerification
    }

    Write-Host "`nVERIFICATION PASSED (Scope=$Scope, FullHost=$FullHost)" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "`nVERIFICATION FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
