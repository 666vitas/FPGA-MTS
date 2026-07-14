[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path

function Test-RepoPath([string[]]$relativePaths) {
    foreach ($relativePath in $relativePaths) {
        $fullPath = Join-Path $repoRoot $relativePath
        [pscustomobject]@{ Path = $relativePath; Exists = (Test-Path -LiteralPath $fullPath) }
    }
}

Write-Output "CURRENT_PATH=$((Get-Location).Path)"
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "BRANCH=$(& git -C $repoRoot branch --show-current)"
Write-Output "HEAD=$(& git -C $repoRoot rev-parse HEAD 2>$null)"
Write-Output 'GIT_STATUS'
& git -C $repoRoot status --short --branch

$required = @(
    'AGENTS.md',
    'AI_REVIEW_README.md',
    'version/AI_STRICT_REVIEW_ENTRY.md',
    'version/CURRENT_REVIEW_MANIFEST.md',
    'version/STATUS.md',
    'v0.94/project/redpitaya.xpr',
    'v0.94/rtl',
    'v0.94/sim',
    'software/redpitaya_lock_host',
    'software/redpitaya_lock_host/redpitaya_lock_host',
    'software/redpitaya_lock_host/scripts',
    'software/redpitaya_lock_host/tests',
    'software/redpitaya_lock_host/docs',
    '.agents/skills/mts-redpitaya-project/SKILL.md'
)
Write-Output 'REQUIRED_PATHS'
foreach ($item in (Test-RepoPath $required)) {
    Write-Output ("{0}={1}" -f $item.Path, $item.Exists)
}

$pythonPath = Join-Path $repoRoot 'software/redpitaya_lock_host/.venv/Scripts/python.exe'
Write-Output "PYTHON_VENV_EXISTS=$(Test-Path -LiteralPath $pythonPath)"
Write-Output "VIVADO_PROJECT_EXISTS=$(Test-Path -LiteralPath (Join-Path $repoRoot 'v0.94/project/redpitaya.xpr'))"

$scanFiles = @(
    (Join-Path $repoRoot 'version/AI_STRICT_REVIEW_ENTRY.md'),
    (Join-Path $repoRoot 'v0.94/rtl'),
    (Join-Path $repoRoot 'software/redpitaya_lock_host')
)
$conflicts = foreach ($path in $scanFiles) {
    if (Test-Path -LiteralPath $path) {
        Get-ChildItem -LiteralPath $path -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\.venv[\\/]|__pycache__[\\/]' } |
            Select-String -Pattern '^(<<<<<<<|=======|>>>>>>>)' -ErrorAction SilentlyContinue
    }
}
Write-Output "UNRESOLVED_MERGE_MARKERS=$([bool]$conflicts)"
if ($conflicts) { $conflicts | Select-Object Path, LineNumber, Line | Format-Table -AutoSize | Out-String | Write-Output }

$rtlFiles = Get-ChildItem (Join-Path $repoRoot 'v0.94/rtl') -File -ErrorAction SilentlyContinue
$pythonFiles = Get-ChildItem (Join-Path $repoRoot 'software/redpitaya_lock_host') -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -eq '.py' -and $_.FullName -notmatch '\\.venv[\\/]|__pycache__[\\/]' }
$rtlMagic = ($rtlFiles | Select-String -Pattern '4D545330' -AllMatches).Count -gt 0
$pyMagic = ($pythonFiles | Select-String -Pattern '4D545330' -AllMatches).Count -gt 0
$rtlVersion = ($rtlFiles | Select-String -Pattern '00030001' -AllMatches).Count -gt 0
$pyVersion = ($pythonFiles | Select-String -Pattern '00030001' -AllMatches).Count -gt 0
Write-Output "MAGIC_RTL=$rtlMagic MAGIC_PYTHON=$pyMagic MAGIC_MATCH=$($rtlMagic -and $pyMagic)"
Write-Output "VERSION_RTL=$rtlVersion VERSION_PYTHON=$pyVersion VERSION_MATCH=$($rtlVersion -and $pyVersion)"

$tempPattern = '\.(jou|log|rpt|str)$|(^|[\\/])\.Xil([\\/]|$)|(^|[\\/])cache([\\/]|$)|usage_statistics'
$tempStatus = & git -C $repoRoot status --short
$tempFiles = $tempStatus | Where-Object { $_ -match $tempPattern }
Write-Output "VIVADO_TEMP_FILES_IN_STATUS=$([bool]$tempFiles)"
if ($tempFiles) { $tempFiles }

Write-Output 'READ_ONLY_CHECK_COMPLETE'
