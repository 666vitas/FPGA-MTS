Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: STATUS
Last-Updated: 2026-07-26
Supersedes: version/history/STATUS_HISTORY_D1_THROUGH_2026-07-24.md
Superseded-By: NONE

# STATUS

## Current Stage

`LOCK-MVP / FPGA realtime ERROR-crossing acquisition`

## Current Gate

`LOCK-MVP-L1 / Realtime ERROR crossing before scan-to-P_LOCK`

## Current Facts

- [ROUTED TIMING PASS ON CONSTRAINED PATHS] User-supplied Vivado 2020.1 implementation reports show WNS `+0.209 ns`, TNS `0`, `0` setup failing endpoints, WHS `+0.050 ns`, THS `0`, `0` hold failing endpoints, TPWS `0`, and `0` failed routes.
- [TIMING COVERAGE NOT CLEAN] `check_timing` still reports `52` no-clock pins, `19` unconstrained internal endpoints, `17` inputs without delay, and `42` outputs without delay.
- [METHODOLOGY BLOCKER] `report_methodology` contains `5` critical warnings: `TIMING-6 x2`, `TIMING-7 x2`, and `TIMING-17 x1`.
- [CURRENT WORST CUSTOM PATH] `i_out2_lock_controller/s5_lock_limit_reg[12] -> control_o_reg[5]`, `16` logic levels, slack `+0.209 ns`; new acquisition logic must not be inserted into this output combinational path.
- [UTILIZATION] Routed design uses `6819` LUTs, `7688` FFs, `38` RAMB36, and `12` DSPs. Device capacity is not the present blocker.
- [HARDWARE VERIFIED] The board can scan and produce an observable FPGA mixer+LPF error signal on OUT1.
- [HARDWARE NOT VERIFIED] No real scan-to-lock transition, Kp=0 hold, Kp=4 negative feedback, 60-second lock, or absence of spectral shift has been demonstrated.
- [ROOT CAUSE IN OLD SIMPLE] The production SIMPLE trigger previously used only scan direction plus historical OUT2 target window. It accepted an ERROR crossing direction field but did not use it in the trigger condition.
- [CODE UPDATED ON FEATURE BRANCH] `feature/realtime-error-crossing-l1` adds realtime ERROR crossing qualification with a fixed 4-count hysteresis, source-side history, requested crossing direction, and event crossing-direction readback.
- [TEST UPDATED, NOT RUN] `tb_simple_lock_acquisition` now covers guard-window-only rejection, hysteresis, both ERROR crossing directions, wrong scan direction, atomic bias capture, and Kp=0/Kp=4 state transitions. No simulator or Vivado run has yet verified this branch.
- [HOST CONTRACT RETAINED] The existing host already writes independent scan direction and ERROR crossing direction fields, so this first RTL correction does not require a new normal-operation GUI workflow.

## Current Blockers

1. Run the updated RTL regression and fix any compile or behavioral failure.
2. Identify and classify the `19` unconstrained internal endpoints and `52` no-clock pins.
3. Resolve or explicitly justify the `TIMING-6`, `TIMING-7`, and `TIMING-17` methodology critical warnings.
4. Re-run synthesis and implementation after the realtime crossing change.
5. Do not generate the production locking bitstream until the modified branch passes both regression and routed timing coverage review.

## Forbidden Scope

- Do not add machine learning, automatic relock, PSD, IQ reconstruction, fast/slow dual actuator control, or large GUI redesign.
- Do not add PI/Ki before realtime crossing and P-only acquisition are proven on hardware.
- Do not use blanket false paths, multicycle constraints, lower clock frequency, or relaxed constraints to hide unconstrained or failing functional paths.
- Do not delete D1, legacy HOLD, or CAPTURE_LOCK_POINT source yet; remove them only from the normal workflow after the replacement path is verified.
- Do not claim bitstream, burn, scan-to-lock, or real lock success from timing and simulation alone.

## Unique Next Action

Run the updated `tb_simple_lock_acquisition` and the full existing RTL/Host regression on branch `feature/realtime-error-crossing-l1`.

If regression passes, generate the following additional reports before a new bitstream:

```text
par_clk -> pll_adc_clk timing
pll_adc_clk -> par_clk timing
clock interaction
unconstrained timing paths with object names
```

Then reset `synth_1`/`impl_1`, implement the modified RTL, and return the new timing summary, worst setup path, methodology report, and unconstrained-path report.
