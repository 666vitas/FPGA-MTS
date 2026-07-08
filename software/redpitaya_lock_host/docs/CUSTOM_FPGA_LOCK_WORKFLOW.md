# Custom FPGA Lock Workflow

Custom FPGA Observe Mode serves the real current wiring:

```text
IN1 <- PD/MTS after analog BPF + amplifier, must be < +/-1 V
IN2 <- 4.6 MHz REF, must be < +/-1 V
OUT1 -> FPGA laser_error -> oscilloscope
OUT2 -> FPGA selected_out2 -> oscilloscope
```

OUT2 is scope-only at the current stage. Do not connect OUT2 to laser scan/PZT, D2-125, or Scan/PZT.

## Manual Readings

Record these oscilloscope values:

- OUT1 error Vpp/min/max
- OUT2 control Vpp/min/max
- PD / saturated absorption Vpp
- REF amplitude
- notes

The GUI computes OUT2/OUT1 Vpp ratio and flags dangerous conditions:

- OUT2 abs(max/min) >= 0.8 V: danger.
- OUT2 Vpp too large: danger.
- OUT1 nearly zero: warning.
- OUT2 rapidly climbing or randomly jumping: stop experiment.

## Current FPGA Interface

`custom_fpga_backend.py` now implements the SSH + `/dev/mem` register path for `SAFE`, `SCAN`, `HOLD`, `P_LOCK`, and `PI_LOCK` candidate modes. v3REG-0 `SAFE/SCAN` has board evidence from the user. `HOLD/P_LOCK/PI_LOCK` are not yet timing/bitstream/board verified, so they remain scope-only candidates.

Do not connect OUT2 to PZT, Scan input, laser current modulation, D2-125 Servo Output, or D2-125 Aux Output during this stage.
