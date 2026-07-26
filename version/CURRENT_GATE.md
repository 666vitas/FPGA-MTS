Status: ACTIVE
Effective-Gate: LOCK-MVP-L1
Authority: CURRENT_GATE
Last-Updated: 2026-07-26
Supersedes: CURRENT_GATE_PROPOSED.md
Superseded-By: NONE

# CURRENT GATE — LOCK-MVP-L1 FPGA Realtime ERROR-Crossing Acquisition

## 1. Current evidence

The user supplied a routed Vivado 2020.1 report set for `red_pitaya_top` / `xc7z010clg400-1`.

Constrained timing paths pass:

```text
WNS  = +0.209 ns
TNS  =  0.000 ns
Setup failing endpoints = 0
WHS  = +0.050 ns
THS  =  0.000 ns
Hold failing endpoints  = 0
TPWS =  0.000 ns
Failed routes = 0
```

However timing coverage is not sign-off clean:

```text
no_clock                         = 52
unconstrained_internal_endpoints = 19
no_input_delay                   = 17
no_output_delay                  = 42
methodology critical warnings    = 5
```

The full analysis is recorded in:

`docs/verification/VIVADO_SIMPLE_ITER2_2026-07-26.md`

## 2. Why the old gate is closed

The previous blocker was the negative setup slack in the ramp output path. The new routed report shows that the constrained setup and hold paths now pass, and the worst path has moved to the custom OUT2 lock controller.

Therefore the project may leave the `ramp timing repair` gate.

## 3. Why the old SIMPLE lock semantics are rejected

The former SIMPLE trigger used:

```text
ARMED
AND scan direction matches
AND OUT2 is inside the historical target window
```

It did not require the current realtime ERROR to cross the requested setpoint. This means a historical PZT count could trigger after PZT hysteresis, scan-direction offset, drift, or scan-to-static displacement had moved the real zero crossing.

The target OUT2 is now treated only as a **guard region**. The current realtime ERROR crossing is the required final trigger condition.

## 4. Gate objective

Verify the minimum timing-light realtime acquisition path:

```text
SCAN
→ aligned capture
→ user selects a target zero-crossing region
→ host preloads guard center/window, scan direction, ERROR crossing direction,
  setpoint, limits, polarity, and Kp
→ FPGA enters ARMED
→ FPGA sees the requested source side of ERROR inside the guard
→ FPGA sees the requested destination side after a 4-count hysteresis band
→ FPGA captures current OUT2 and current ERROR
→ FPGA atomically enters P_LOCK
→ hardware later verifies Kp=0 continuity and Kp=4 negative feedback
```

## 5. Implemented in this branch

Branch: `feature/realtime-error-crossing-l1`

### RTL

`v0.94/rtl/simple_lock_acquisition.sv`

- adds realtime ERROR relative-to-setpoint comparison;
- adds fixed `±4` count hysteresis for the first gate;
- requires source-side history before destination-side trigger;
- requires the configured `NEG_TO_POS` or `POS_TO_NEG` direction;
- keeps scan direction and OUT2 guard checks;
- stores event scan direction and ERROR crossing direction at the trigger;
- exposes realtime-crossing capability in `CONFIG_VALIDATION[16]`;
- exposes source-side armed state in `ACQ_STATE[16]`.

### Simulation

`v0.94/sim/tb_simple_lock_acquisition.sv`

Adds coverage for:

- no request;
- non-SCAN request;
- saturation;
- wrong scan direction;
- guard-window hit without ERROR source-side history;
- hysteresis deadband;
- `NEG_TO_POS` trigger;
- `POS_TO_NEG` trigger;
- event direction readback;
- atomic OUT2/error capture;
- Kp=0 and Kp=4 transitions.

These tests are written but have not yet been run.

## 6. Allowed scope

- fix compile or behavioral issues in realtime crossing RTL/tests;
- run existing SIMPLE, D1, register bank, OUT2 controller, ramp, and Host regressions;
- classify the no-clock and unconstrained endpoints;
- correct real clock/CDC constraints when supported by evidence;
- re-run synthesis and implementation;
- update documentation and register-bit descriptions for the new readback bits.

## 7. Forbidden scope

- no machine learning;
- no automatic relock;
- no PSD or IQ redesign;
- no full Linien copy;
- no PI/Ki yet;
- no P-gain soft-start yet;
- no lock supervisor yet;
- no large GUI redesign;
- no blanket false path, multicycle, clock reduction, or relaxed timing constraints;
- no production bitstream until this branch is simulated and re-implemented.

## 8. Acceptance conditions

### Automatic regression

- updated `tb_simple_lock_acquisition` passes;
- existing SIMPLE/D1/register bank/OUT2/ramp testbenches pass;
- Host tests pass;
- no stale-target or readback safety regression;
- event crossing direction is coherent with the trigger sample.

### Timing coverage

- WNS >= 0;
- TNS = 0;
- WHS >= 0;
- THS = 0;
- setup failing endpoints = 0;
- hold failing endpoints = 0;
- failed routes = 0;
- all 19 unconstrained endpoints classified;
- TIMING-6/7/17 either fixed or documented with evidence-backed exceptions.

### Hardware gate after a new bitstream

- OUT2 continues scanning until the current ERROR performs the requested crossing;
- historical guard-center hit alone does not switch mode;
- trigger event reports the actual current OUT2 and ERROR;
- Kp=0 transition does not create an obvious digital OUT2 jump;
- no claim of lock until nonzero Kp reduces the measured error.

## 9. Unique next action

Run the updated regression first. Do not open Vivado or generate a bitstream until the RTL and Host tests pass.

After regression, run:

```tcl
open_run impl_1
report_timing -from [get_clocks par_clk] -to [get_clocks pll_adc_clk] -max_paths 50
report_timing -from [get_clocks pll_adc_clk] -to [get_clocks par_clk] -max_paths 50
report_clock_interaction
report_timing -unconstrained -max_paths 200
```

Then reset and re-run synthesis/implementation for the modified RTL.
