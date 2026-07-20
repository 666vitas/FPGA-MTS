# HISTORICAL COMPATIBILITY WRAPPER
# Canonical entry: E:\new\fpga_lock\v94\scripts\verify.ps1 -Scope Host

[CmdletBinding()]
param(
    [switch]$Slow,
    [string]$PythonPath,
    [ValidateRange(1, 3600)]
    [int]$TimeoutSeconds = 300
)

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$verifyScript = Join-Path $repoRoot "scripts\verify.ps1"

Write-Warning "run_tests_takeover.ps1 is historical; forwarding to scripts\verify.ps1 -Scope Host."
$verifyParameters = @{
    Scope = "Host"
    TimeoutSeconds = $TimeoutSeconds
}
if ($Slow) {
    $verifyParameters.FullHost = $true
}
if ($PythonPath) {
    $verifyParameters.PythonPath = $PythonPath
}

try {
    & $verifyScript @verifyParameters
    exit $LASTEXITCODE
} catch {
    Write-Error $_
    exit 1
}
