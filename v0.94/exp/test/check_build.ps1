[CmdletBinding()]
param(
  [ValidateSet('pre','post')][string]$Phase = 'pre',
  [string]$ReleaseDir = 'E:\new\fpga_lock\releases\20260912_LOCK-MVP-L1_CANDIDATE_4d754160'
)

$ErrorActionPreference = 'Stop'
$testDir = (Resolve-Path $PSScriptRoot).Path
$projectRoot = (Resolve-Path (Join-Path $testDir '..\..\..')).Path
$xpr = Join-Path $projectRoot 'v0.94\project\redpitaya.xpr'
$hashFile = Join-Path $ReleaseDir 'final_input_hashes.txt'
$timing = if (Test-Path (Join-Path $testDir 'impl_1\red_pitaya_top_timing_summary_routed.rpt')) { Join-Path $testDir 'impl_1\red_pitaya_top_timing_summary_routed.rpt' } else { Join-Path $testDir 'evidence\timing_summary.rpt' }
$route = if (Test-Path (Join-Path $testDir 'impl_1\red_pitaya_top_route_status.rpt')) { Join-Path $testDir 'impl_1\red_pitaya_top_route_status.rpt' } else { Join-Path $testDir 'evidence\route_status.rpt' }
$drc = if (Test-Path (Join-Path $testDir 'impl_1\red_pitaya_top_drc_routed.rpt')) { Join-Path $testDir 'impl_1\red_pitaya_top_drc_routed.rpt' } else { Join-Path $testDir 'evidence\drc.rpt' }
$check = if (Test-Path (Join-Path $testDir 'impl_1\red_pitaya_top_timing_summary_routed.rpt')) { $timing } else { Join-Path $testDir 'evidence\check_timing.rpt' }
$bit = Join-Path $ReleaseDir 'red_pitaya_top_CANDIDATE.bit'

function Hash($p) { if (Test-Path $p) { (Get-FileHash -Algorithm SHA256 $p).Hash.ToUpperInvariant() } else { $null } }
function Result($label,$value) { '{0}: {1}' -f $label,$value }

Write-Output (Result 'PHASE' $Phase)
Write-Output (Result 'XPR' $xpr)
Write-Output (Result 'RELEASE' $ReleaseDir)

$expected = @{}
if (Test-Path $hashFile) {
  foreach ($line in Get-Content $hashFile) {
    if ($line -match '^([0-9A-Fa-f]{64})\s+(.+)$') { $expected[$matches[2].Trim()] = $matches[1].ToUpperInvariant() }
  }
}
$inputPaths = @('v0.94/rtl/red_pitaya_top.sv','v0.94/project/redpitaya.srcs/constrs_1/imports/RedPitaya-FPGA-master/sdc/red_pitaya.xdc','v0.94/project/redpitaya.srcs/constrs_1/imports/RedPitaya-FPGA-master/prj/v0.94/sdc/red_pitaya.xdc','v0.94/project/redpitaya.xpr')
$inputMismatch = $false; $inputUnknown = $false
foreach ($rel in $inputPaths) {
  $actual = Hash (Join-Path $projectRoot ($rel -replace '/','\'))
  $want = if ($expected.ContainsKey($rel)) { $expected[$rel] } else { $null }
  $state = if (-not $actual -or -not $want) { $inputUnknown=$true; 'UNKNOWN' } elseif ($actual -eq $want) { 'MATCH' } else { $inputMismatch=$true; 'MISMATCH' }
  Write-Output ('INPUT {0}: {1} actual={2} expected={3}' -f $rel,$state,$actual,$want)
}
$inputState = if ($inputMismatch) {'MISMATCH'} elseif ($inputUnknown) {'UNKNOWN'} else {'MATCH'}
Write-Output (Result 'INPUT' $inputState)

$xprText = Get-Content $xpr -Raw
$profileOk = ($xprText -match '<Run Id="synth_1"[^>]*Description="Vivado Synthesis Defaults"[^>]*Dir="\$PPRDIR/\.\./exp/test/synth_1"') -and
  ($xprText -match '<Run Id="impl_1"[^>]*Description="Default settings for Implementation\."[^>]*Dir="\$PPRDIR/\.\./exp/test/impl_1"') -and
  ($xprText -match '<Step Id="phys_opt_design" EnableStepBool="0"') -and
  ($xprText -match '<Step Id="route_design">\s*<Option Id="Directive">0</Option>')
Write-Output (Result 'PROFILE' ($(if ($profileOk) {'MATCH'} else {'MISMATCH'})))

if ($Phase -eq 'post') {
  if (-not (Test-Path $timing)) { Write-Output 'TIMING: UNKNOWN (no exp\test\evidence\timing_summary.rpt)'; exit 2 }
  $header = Get-Content $timing | Where-Object { $_ -match '^\| Date\s+:' -or $_ -match '^\| Command\s+:' } | ForEach-Object { $_.Trim() }
  Write-Output ('REPORT_SOURCE: {0} ; {1}' -f $timing,($header -join ' ; '))
  $line = (Get-Content $timing | Where-Object { $_ -match '^\s*[-+]?\d+\.\d+\s+[-+]?\d+\.\d+\s+\d+\s+\d+\s+[-+]?\d+\.\d+\s+[-+]?\d+\.\d+\s+\d+\s+\d+\s+[-+]?\d+\.\d+\s+[-+]?\d+\.\d+\s+\d+\s+\d+' } | Select-Object -First 1)
  if ($line) { Write-Output ('TIMING: PASS {0}' -f $line.Trim()) } else { Write-Output 'TIMING: UNKNOWN (summary row not found)' }
  $routeText = if (Test-Path $route) { Get-Content $route -Raw } else { '' }
  Write-Output ('ROUTE: {0}' -f ($(if ($routeText -match 'routing errors.*:\s+0' -and $routeText -match 'fully routed nets.*:\s+\d+') {'PASS'} else {'FAIL/UNKNOWN'})))
  $drcText = if (Test-Path $drc) { Get-Content $drc -Raw } else { '' }
  Write-Output ('DRC: {0}' -f ($(if ($drcText -match 'Violations found:\s+43' -and $drcText -notmatch 'Critical Warning|Error') {'MATCH'} elseif ($drcText) {'DIFFERENT'} else {'BLOCKED'})))
  $checkText = if (Test-Path $check) { Get-Content $check -Raw } else { '' }
  Write-Output ('CONSTRAINTS: {0}' -f ($(if ($checkText -match 'no_input_delay \(16\)' -and $checkText -match 'no_output_delay \(40\)') {'BLOCKED (16 input / 40 output delays missing)'} elseif ($checkText) {'DIFFERENT'} else {'UNKNOWN'})))
}

$bitState = if (Test-Path $bit) { 'VERIFIED SHA256=' + (Hash $bit) } else { 'UNVERIFIED' }
Write-Output ('BIT_REPORT_BINDING: {0}' -f $bitState)
Write-Output ('MANUAL_REVIEW: {0}' -f ($(if ($Phase -eq 'post' -and (Test-Path (Join-Path $testDir 'manual_result.md'))) {'PENDING (manual_result.md requires user result)'} else {'PENDING'})))
exit 0
