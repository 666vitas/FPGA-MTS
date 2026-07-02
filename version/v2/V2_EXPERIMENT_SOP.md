# V2_EXPERIMENT_SOP

> Active baseline: only the GitHub project `666vitas/FPGA-MTS` `v0.94` mainline plus `version/v2` documentation are valid. Do not read, reference, sync, copy, or modify any `weifang` or `version-weifang` directory for this route.

## 0. Current real D2-125 wiring model

Current analog optical and error chain:

```text
Laser
-> Rb / MTS optical path
-> PD
-> analog band-pass filter
-> Mini-Circuits RF amplifier
-> analog mixer x 4.6 MHz REF
-> MTS error
-> D2-125 Error Input
```

D2-125 practical states:

```text
Ramp
Unlock
Lock
```

Ramp state:

```text
D2-125 Auxiliary Servo Output
-> laser power supply Scan / PZT
-> triangular scan
-> sweep saturated absorption / MTS spectrum
```

Ramp is for finding peaks, observing the spectrum, and locating candidate lock points. It is not closed-loop locking.

Unlock state:

```text
D2-125 does not close the loop.
The user manually adjusts laser current, temperature, interference-filter angle, Scan offset, and optics.
Outputs should be treated as open-loop or safe-state outputs.
```

Lock state:

```text
MTS error
-> D2-125 Error Input
-> D2-125 internal PI/PID
-> Servo Output
-> tee splitter
   |-> laser power supply: slow current feedback
   `-> potentiometer gain adjust -> interference-filter laser: fast current feedback
```

The Servo Output is one main PID current-feedback signal. The tee splits the same voltage into two current-feedback branches. The potentiometer adjusts the fast branch gain; it does not change the feedback type.

Aux Servo Output in Lock state:

```text
D2-125 Auxiliary Servo Output
-> laser power supply Scan / PZT
-> auxiliary PI / slow Scan-PZT control
-> maintain lock center and compensate slow drift
```

## 1. Current allowed Red Pitaya wiring

Current active FPGA mainline:

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o
-> OUT1

same error_o / protected_error
-> pi_controller or pi_controller_seq
-> control_o
-> OUT2
```

Allowed current wiring:

```text
Red Pitaya IN1 <- PD + BPF + amplifier, within +/-1 V.
Red Pitaya IN2 <- external REF, within +/-1 V.
Red Pitaya OUT1 -> oscilloscope, or later D2-125 Error Input after a dedicated SOP.
Red Pitaya OUT2 -> oscilloscope only.
```

Current meanings:

```text
OUT1 = FPGA mixer+LPF error observation.
OUT2 = FPGA control candidate / shadow control / sequential PI candidate.
```

## 2. Current forbidden wiring

```text
OUT2 must not connect to the laser.
OUT2 must not connect to the D2-125 Servo Output tee.
OUT2 must not connect to the laser power supply Scan / PZT.
OUT2 must not be paralleled with any D2-125 output.
D2-125 DC Error must not be used as Red Pitaya IN1.
D2-125 Servo Output must not be used as Red Pitaya IN1.
IN1/IN2 must never exceed +/-1 V.
```

The current FPGA has not fully replaced D2-125 and has not independently completed a real laser closed loop.

## 3. v2B3 sequential PI oscilloscope SOP

Purpose:

```text
Verify that mode=1 sequential PI is timing-clean and safe on OUT2 while OUT2 is still connected only to the oscilloscope.
```

Pre-board checks:

```text
1. Confirm only v0.94 mainline sources are used.
2. Confirm red_pitaya_top is the Design Top.
3. Confirm pi_controller_seq.sv is in Design Sources.
4. Confirm tb_*.sv files are not in Design Sources.
5. Run Synthesis and Implementation manually.
6. Timing must pass: WNS >= 0 and TNS = 0.
7. Only after timing passes, Generate Bitstream.
```

Scope wiring:

```text
OUT1 -> CH2
OUT2 -> CH4
```

Normal phenomena:

```text
OUT1/CH2: FPGA mixer+LPF error remains visible.
OUT2/CH4: sequential PI candidate follows the error trend.
OUT2 may look close to P-only over a short time.
Small Ki may produce slow baseline movement only when same-sign error persists.
OUT2 remains limited and does not approach +/-1 V.
```

Stop conditions:

```text
OUT1 disappears.
OUT2 remains zero when mode=1 is expected.
OUT2 is exactly OUT1/2, suggesting fallback mode still active.
OUT2 randomly jumps.
OUT2 rapidly climbs or saturates.
OUT2 approaches +/-1 V.
Vivado timing fails.
Any attempt is made to connect OUT2 to laser, Servo Output, Aux Output, Scan/PZT, or current feedback.
```

Passing v2B3 does not mean the FPGA has locked the laser. It only means the OUT2 control candidate is safe enough to continue staged development.

## 4. Future OUT1 -> D2-125 Error Input SOP boundary

A later stage may test:

```text
FPGA OUT1 error
-> D2-125 Error Input
```

Purpose:

```text
Use FPGA mixer+LPF to replace the analog error-generation chain while D2-125 still performs the real lock.
```

Preconditions:

```text
OUT1 amplitude and offset are measured.
D2-125 Error Input range is confirmed.
OUT1 does not clip or disappear.
A quick rollback to the analog mixer error is available.
OUT2 remains on the oscilloscope only.
```

This test must not be confused with FPGA independent locking.

## 5. Future v2F low-gain single-branch closed-loop safety check

v2F is not a full D2-125 replacement. It is only a first low-gain single-branch real actuator test.

Before v2F, confirm:

```text
1. Which single actuator branch is being tested.
2. The D2-125 output is disconnected from that same terminal.
3. Red Pitaya OUT2 voltage range is safe for that input.
4. Feedback polarity is known or starts with a reversible low-gain test.
5. The potentiometer / feedback gain is initially low.
6. Kp is small.
7. Ki is zero at first.
8. output_limit is small.
9. enable defaults to safe/off where appropriate.
10. reset drives OUT2 to a documented safe value.
11. The user can immediately disconnect or return to D2-125.
```

Allowed v2F concept:

```text
Red Pitaya OUT2 -> one selected real feedback branch only
```

Forbidden v2F concept:

```text
Red Pitaya OUT2 -> fast current + slow current + Aux/Scan simultaneously
Red Pitaya OUT2 paralleled with D2-125 Servo Output
Red Pitaya OUT2 paralleled with D2-125 Aux Servo Output
```

## 6. Future v3 / v4 / v5 boundary

v3 begins the replacement of D2-125 workflow functions:

```text
ramp_generator
scan_lock_fsm
Ramp / Unlock / Lock state switching
Aux Servo Output replacement
slow Scan/PZT control
relock
lock quality judgment
```

v4/v5 are for host and AI:

```text
host spectrum selection
automatic peak recognition
AI / 1D-CNN peak recognition
Kp/Ki suggestions
lock/unlock judgment
automatic Rescan decision
```

AI is not the high-speed PID loop. The FPGA remains responsible for real-time mixer, LPF, PI/PID candidate, output limiting, and reset-safe actuator outputs.

## 7. Data to save after each experiment

For every experiment, save:

```text
Vivado timing screenshot or report if bitstream was generated.
Bit/bin source commit or file version.
Oscilloscope screenshot.
CSV waveform data.
Exact wiring photo or text record.
IN1/IN2 voltage range.
OUT1/OUT2 Vpp, RMS, offset.
Whether OUT2 was oscilloscope-only or connected to an actuator.
Pass / stop decision.
```

## 8. Historical notes

Older SOP sections that describe `D2-125 DC Error -> Red Pitaya IN1`, full direct D2 replacement, or simultaneous multi-branch actuator connection are historical only and must not be executed as the current route.
