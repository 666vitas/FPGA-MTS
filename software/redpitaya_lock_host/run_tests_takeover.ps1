# Claude Takeover Test Runner — 2026-07-15
# Run from: E:\new\fpga_lock\v94\software\redpitaya_lock_host\
# Prerequisites: .venv with PySide6, pytest, numpy; QT_QPA_PLATFORM=offscreen
#
# Usage from PowerShell:
#   .\run_tests_takeover.ps1
#   .\run_tests_takeover.ps1 -Slow  # include slow/legacy tests

param(
    [switch]$Slow = $false
)

$ErrorActionPreference = "Stop"
$venvPython = ".\.venv\Scripts\python.exe"
$timeout = 180  # seconds per group
$testDir = "tests"
$targetFile = "$testDir\test_custom_fpga_backend.py"

if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: $venvPython not found" -ForegroundColor Red
    exit 1
}

Write-Host "=== STEP 1: tabnanny syntax check ===" -ForegroundColor Cyan
& $venvPython -m tabnanny redpitaya_lock_host\main_window.py
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: main_window.py syntax" -ForegroundColor Red }
& $venvPython -m tabnanny $targetFile
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: test file syntax" -ForegroundColor Red }

Write-Host "`n=== STEP 2: py_compile check ===" -ForegroundColor Cyan
& $venvPython -c "import py_compile; py_compile.compile('redpitaya_lock_host/main_window.py', doraise=True); print('main_window.py OK')"
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: main_window.py compile" -ForegroundColor Red }
& $venvPython -c "import py_compile; py_compile.compile('$targetFile', doraise=True); print('test_custom_fpga_backend.py OK')"
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: test file compile" -ForegroundColor Red }

Write-Host "`n=== STEP 3: pytest collect-only ===" -ForegroundColor Cyan
& $venvPython -m pytest --co -q $targetFile 2>&1
if ($LASTEXITCODE -eq 5) {
    Write-Host "No tests collected — may indicate import errors" -ForegroundColor Red
}

Write-Host "`n=== STEP 4: single test sanity ===" -ForegroundColor Cyan
$singleTest = "test_status_payload_rejects_zero_magic_string"
Write-Host "Running: $singleTest"
$job = Start-Job -ScriptBlock {
    param($py, $file, $test)
    & $py -X faulthandler -m pytest -x -vv -s "$file" -k "$test" 2>&1
} -ArgumentList $venvPython, $targetFile, $singleTest
Wait-Job $job -Timeout 60
$output = Receive-Job $job 2>&1
Remove-Job $job -Force
$output | ForEach-Object { $_ }
if ($output -match "1 passed") {
    Write-Host "Single test PASSED" -ForegroundColor Green
} else {
    Write-Host "Single test FAILED or TIMED OUT" -ForegroundColor Red
}

Write-Host "`n=== STEP 5: locate hanging test (binary search) ===" -ForegroundColor Cyan
Write-Host "Running tests in groups of 10 with $timeout s timeout..."

# Collect all test names
$allTests = & $venvPython -m pytest --co -q $targetFile 2>&1 | Select-String "test_" | ForEach-Object { $_.Line.Trim() }
Write-Host "Total tests collected: $($allTests.Count)"

# Group into batches of 10
$batchSize = 10
$batchNum = 0
for ($i = 0; $i -lt $allTests.Count; $i += $batchSize) {
    $batchNum++
    $batch = $allTests[$i..([Math]::Min($i + $batchSize - 1, $allTests.Count - 1))]
    $testPattern = ($batch -join " or ")
    Write-Host "Batch $batchNum ($(($batch | Measure-Object).Count) tests): tests $($i+1)-$([Math]::Min($i+$batchSize, $allTests.Count))"

    $job = Start-Job -ScriptBlock {
        param($py, $file, $pattern)
        & $py -X faulthandler -m pytest -x -vv -s "$file" -k "$pattern" 2>&1
    } -ArgumentList $venvPython, $targetFile, $testPattern
    Wait-Job $job -Timeout $timeout

    if ($job.State -eq 'Running') {
        Write-Host "  BATCH $batchNum TIMED OUT after ${timeout}s" -ForegroundColor Red
        Write-Host "  Tests in this batch:" -ForegroundColor Yellow
        $batch | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
        Stop-Job $job
        Remove-Job $job -Force
        Write-Host "  Stopping — found the hanging batch. Investigate these tests individually." -ForegroundColor Red
        break
    }

    $output = Receive-Job $job 2>&1
    Remove-Job $job -Force

    $passed = ($output | Select-String "passed").Matches.Value
    $failed = ($output | Select-String "failed").Matches.Value
    if ($passed) { Write-Host "  $passed" -ForegroundColor Green }
    if ($failed) {
        Write-Host "  $failed" -ForegroundColor Red
        $output | Select-String "FAILED|ERROR" | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    }
}

Write-Host "`n=== STEP 6: full suite ===" -ForegroundColor Cyan
Write-Host "Running full test suite..."
$job = Start-Job -ScriptBlock {
    param($py, $file)
    & $py -X faulthandler -m pytest -x -vv -s "$file" 2>&1
} -ArgumentList $venvPython, $targetFile
Wait-Job $job -Timeout 300
if ($job.State -eq 'Running') {
    Write-Host "FULL SUITE TIMED OUT after 300s" -ForegroundColor Red
    Stop-Job $job
}
$output = Receive-Job $job 2>&1
Remove-Job $job -Force
$output | ForEach-Object { $_ }

if ($Slow) {
    Write-Host "`n=== STEP 7: other test files ===" -ForegroundColor Cyan
    & $venvPython -X faulthandler -m pytest -x -v "$testDir\test_custom_fpga_workflow.py" 2>&1
    & $venvPython -X faulthandler -m pytest -x -v "$testDir\test_waveform_preview.py" 2>&1
}

Write-Host "`n=== DONE ===" -ForegroundColor Green
Write-Host "Main diff applied: git diff HEAD -- redpitaya_lock_host/main_window.py"
