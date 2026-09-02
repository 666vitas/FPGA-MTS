# FIRST_LOCK timing evidence baseline

Status: NOT CURRENT — evidence inventory only  
Date: 2026-09-02  
Gate: LOCK-MVP-L1

## Scope and limitation

This document does **not** claim a new Vivado run. The active Gate prohibits
automatic synthesis, implementation, bitstream generation, and board access.
It records the available routed reports so that the user can produce a directly
comparable current baseline after the XDC/I/O review. A timing signoff requires
all of WNS >= 0, TNS = 0, WHS >= 0, THS = 0, and zero unexplained unconstrained
paths.

## Confirmed project identity

- XPR: `v0.94/project/redpitaya.xpr`
- Top: `red_pitaya_top`
- Part: `xc7z010clg400-1` (7z010, CLG400, speed grade -1)
- Active constraint set: `constrs_1`
- RTL source: `v0.94/rtl/red_pitaya_top.sv`
- Existing report tool version: Vivado 2020.1, build 2902540.

The task instruction names Vivado 2020.2, but the currently resolved local
executable and the available reports identify 2020.1. The user must resolve
this environment discrepancy before treating a new run as 2020.2 evidence.

## Available routed evidence

`version/STATUS.md` records an automated routed run dated 2026-07-26 with
WNS=0.142 ns, TNS=0, WHS=0.053 ns, THS=0. It also records that complete timing
signoff remains incomplete because `check_timing` reports 19 unconstrained
internal endpoints, 17 no-input-delay ports, 42 no-output-delay ports and
daisy/DNA no-clock items.

The retained detailed reports at `v0.94/timing_for_codex/` are older and must
not be substituted for a fresh run. For example, `01_timing_summary.rpt`
(2026-07-24) reports WNS=-0.387 ns, TNS=-5.015 ns, WHS=0.052 ns, THS=0 with
19 unconstrained internal endpoints. Its worst setup path is within
`i_laser_lock_core/i_lpf_core` and has 19 logic levels. This is historical
diagnostic evidence, not a current result.

## Required user-run baseline

Open `v0.94/project/redpitaya.xpr` in the verified installed Vivado version.
Before any RTL change, run the following after opening the existing routed run:

```tcl
get_property PART [current_project]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 200 -nworst 50
check_timing -verbose
report_clocks
report_clock_interaction
report_utilization -hierarchical
report_drc
```

Run `help report_cdc`, `help report_methodology`, and `help report_design_analysis`
first; only execute each command if that exact Vivado version supports it.
For every no-clock, unconstrained internal endpoint, and missing I/O delay,
record the interface semantics and physical evidence before adding any
exception. Do not use blanket false-path, multicycle, max-delay, clock-period,
or frequency changes to make reports appear clean.

## FIRST_LOCK RTL review

The active L1 path is not the old host-driven `SCAN -> HOLD` sequence. In
`custom_register_bank.sv`, an accepted FPGA acquisition trigger captures the
actual `trigger_out2_sample_w` into `lock_bias_o` and atomically selects
`MODE_P_LOCK`/enable. In `out2_lock_controller`, SCAN drives `scan_i`; the
P_LOCK fallback drives `lock_bias_i` while the registered P pipeline becomes
valid. This is the designed no-zero-intermediate path for FIRST_LOCK.

The legacy `REG_CAPTURE_LOCK_POINT` and manual HOLD path remain diagnostics,
not normal L1 acquisition. No RTL change is justified until a reproducible RTL
simulation, routed-report evidence, or user hardware measurement demonstrates
a real regression.
