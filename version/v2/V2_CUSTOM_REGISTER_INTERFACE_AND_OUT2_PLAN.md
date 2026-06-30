# V2 Custom Register Interface And OUT2 Scan/Lock Plan

## Current Boundary

This is a planning document only.

```text
Codex did not modify RTL.
Codex did not operate Vivado.
Codex did not synthesize, implement, generate bit/bin, or program Red Pitaya.
```

Current top-level review:

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 3
LASER_LOCK_CONTROL_PATH_MODE = 1
OUT1 / DAC A = laser_error
OUT2 / DAC B = laser_control
```

`sys_bus_interconnect` has 8 regions. The reviewed top-level uses:

```text
sys[0] red_pitaya_hk / housekeeper
sys[1] red_pitaya_scope
sys[2] red_pitaya_asg
sys[3] red_pitaya_pid
sys[4] red_pitaya_ams
sys[5] red_pitaya_daisy
sys[6] sys_bus_stub
sys[7] sys_bus_stub
```

Planning judgement: `sys[6]` is the preferred future slot for
`laser_lock_register_bank` because it is currently stubbed and does not
displace scope, ASG, PID, AMS, housekeeper, or daisy logic. `sys[7]` should
remain as a spare slot unless `sys[6]` later proves unavailable.

## Host Mode Boundary

Official SCPI Mode:

```text
Uses redpitaya_scpi on port 5000.
Can control official ASG OUT1/OUT2.
Can acquire IN1/IN2 through official ACQ.
Starting redpitaya_scpi may load the official overlay and overwrite the custom bitstream.
```

Custom FPGA Mode:

```text
Assumes the custom bitstream is already loaded.
OUT1 is FPGA laser_error.
OUT2 is FPGA laser_control.
Official SCPI ASG commands are not the custom FPGA OUT1/OUT2 control path.
Future parameter control needs a register/debug/AXI interface.
```

## Proposed Register Bank

Future RTL file:

```text
v0.94/rtl/laser_lock_register_bank.sv
```

Future top-level attachment:

```text
red_pitaya_top.sv sys[6]
```

Register map:

```text
0x00 REG_MAGIC_VERSION
0x04 REG_CONTROL
0x08 REG_OUT2_MODE
0x0C REG_SCAN_AMP
0x10 REG_SCAN_OFFSET
0x14 REG_SCAN_STEP
0x18 REG_VLOCK_VALUE
0x1C REG_KP
0x20 REG_KI
0x24 REG_PID_OFFSET
0x28 REG_OUTPUT_LIMIT
0x2C REG_POLARITY
0x30 REG_STATUS
0x34 REG_ERROR_SAMPLE
0x38 REG_CONTROL_SAMPLE
0x3C REG_INTEGRATOR_LOW
0x40 REG_INTEGRATOR_HIGH
0x44 REG_ERROR_ABS_PEAK
0x48 REG_CONTROL_ABS_PEAK
```

DAC signed 14-bit planning scale:

```text
+8191 ~= +1 V
0 ~= 0 V
-8192 ~= -1 V
0.05 V ~= 410 counts
0.10 V ~= 819 counts
0.20 V ~= 1638 counts
```

## Proposed RTL Blocks

Future files:

```text
triangle_scan_gen.sv
scan_lock_control.sv
out2_output_mux.sv
debug_status_sampler.sv
```

Responsibilities:

```text
triangle_scan_gen:
  Generate bounded triangle scan in signed 14-bit DAC counts.

scan_lock_control:
  Own OUT2 mode transitions, capture Vlock, reset integrator, and expose flags.

out2_output_mux:
  Select SAFE / SCAN / HOLD / P_LOCK / PI_LOCK output into DAC B path.

debug_status_sampler:
  Sample error, control, integrator, peaks, saturation, clip, and lock flags.
```

OUT2 mode plan:

```text
0 SAFE:   OUT2 = 0
1 SCAN:   OUT2 = triangle(scan_amp, scan_offset, scan_step)
2 HOLD:   OUT2 = captured_vlock
3 P_LOCK: OUT2 = captured_vlock + Kp * error
4 PI_LOCK: OUT2 = captured_vlock + Kp * error + Ki * integral(error)
5 RESCAN: reset integrator, clear lock flag, return to SCAN
```

Important meaning:

```text
scan OUT2 is triangle.
lock OUT2 is not triangle.
lock OUT2 = Vlock + P/PI(error).
```

## Future Host Custom FPGA Control Panel

Future controls, not implemented now:

```text
SAFE
Start Scan
Capture Vlock / Hold
Enable P Lock
Enable PI Lock
Reset Integrator
Reverse Polarity
Rescan
```

Future parameters:

```text
scan_amp_v
scan_freq_hz
scan_offset_v
Kp
Ki
output_limit_v
pid_offset_v
polarity
```

Future status display:

```text
current_mode
error_sample
control_sample
vlock_value
sat_flag
adc_clip_flag
lock_flag
integrator_sample
```

Host safety rules:

```text
output_limit_v > 0.2 V: require explicit confirmation
output_limit_v > 0.5 V: forbidden or require a very strong interlock
No captured Vlock: P_LOCK and PI_LOCK disabled
No successful P_LOCK: PI_LOCK disabled
D2-125 Aux Servo Output still connected to laser Scan: do not suggest connecting RP OUT2 to Scan/PZT
```

## Stage Split

```text
v2B3-close:
  Record timing clean and close the sequential PI timing candidate.

v2PZT-DOC:
  Finish register map, safety rules, and first experiment SOP before RTL edits.

v2PZT-RTL-SAFE-SCAN-HOLD:
  Add register bank, SAFE/SCAN/HOLD, triangle scan, Vlock capture, and status sampler.

v2PZT-RTL-PLOCK:
  Add bounded P lock around captured Vlock.

v2PZT-RTL-PILOCK:
  Add bounded PI lock with resettable integrator and anti-windup.

v2HOST-REG:
  Add host Custom FPGA Control Panel using the register interface.
```

## First Experiment SOP

Scope-only and low-risk first:

```text
1. IN1 <- PD BPF/amp signal, verified within +/-1 V.
2. IN2 <- REF signal, verified within +/-1 V.
3. OUT1 -> oscilloscope CH2: FPGA error.
4. OUT2 -> oscilloscope CH4: do not connect to laser yet.
5. SAFE: confirm OUT2 = 0.
6. SCAN: confirm small triangle on OUT2.
7. Disconnect D2-125 Aux Servo Output from laser Scan.
8. Only after step 7, connect RP OUT2 to laser power Scan/PZT.
9. Confirm spectrum sweep.
10. Near a zero crossing, Capture Vlock.
11. HOLD.
12. Later, after review, P_LOCK then PI_LOCK.
```

Stop conditions:

```text
IN1 or IN2 exceeds +/-1 V.
OUT1 error disappears or saturates unexpectedly.
OUT2 exceeds the planned output limit.
OUT2 approaches +/-1 V.
OUT2 jumps randomly or ramps without explanation.
Spectrum sweep direction is unknown.
D2-125 Aux/Scan path is still connected while RP OUT2 is being considered.
Any operator is unsure which device owns laser Scan/PZT.
```
