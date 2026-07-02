# Custom FPGA Lock Workflow

Custom FPGA Observe Mode serves the real current wiring:

```text
IN1 <- PD/MTS after analog BPF + amplifier, must be < +/-1 V
IN2 <- 4.6 MHz REF, must be < +/-1 V
OUT1 -> FPGA laser_error -> oscilloscope
OUT2 -> FPGA laser_control -> oscilloscope
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

## Future FPGA Interface

`custom_fpga_backend.py` only defines future method names. Real hardware read/write is not implemented and must wait for FPGA-side register/debug support.
