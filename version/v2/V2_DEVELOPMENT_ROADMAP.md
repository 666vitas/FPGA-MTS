# V2_DEVELOPMENT_ROADMAP

> Active baseline: only the GitHub project `666vitas/FPGA-MTS` `v0.94` mainline plus `version/v2` documentation are valid for this roadmap. Do not read, reference, sync, copy, or modify any `weifang` or `version-weifang` directory for this route.

## 0. Current D2-125 real wiring model

The current experimentally confirmed analog baseline is:

```text
Laser
-> Rb / MTS optical path
-> PD
-> analog BPF
-> Mini-Circuits amplifier
-> analog mixer x 4.6 MHz REF
-> MTS error
-> D2-125 Error Input
```

The D2-125 should be modeled as a stateful system:

```text
Ramp
Unlock
Lock
```

Ramp state:

```text
D2-125 Auxiliary Servo Output
-> laser power supply Scan / PZT
-> triangular scan of laser frequency
```

Ramp is used to sweep the spectrum, find peaks, and locate a candidate lock point. It is not closed-loop locking.

Unlock state:

```text
D2-125 does not close the loop.
The user manually adjusts current, temperature, interference-filter angle, Scan offset, and optics.
Feedback outputs are treated as open-loop or safe-state outputs.
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

The Servo Output is one main PID current-feedback output. The tee only splits it into two current-feedback branches. The potentiometer adjusts fast-branch gain; it does not change the feedback type.

At the same time:

```text
D2-125 Aux Servo Output
-> laser power supply Scan / PZT
```

In Ramp state, Aux outputs the triangular scan. In Lock state, Aux can provide auxiliary PI / slow Scan-PZT control for maintaining the lock center and compensating slow drift.

## 1. Current Red Pitaya / FPGA mainline status

The active FPGA chain is still:

```text
Red Pitaya IN1 <- pre-mixer PD/MTS signal after BPF + amplifier, within +/-1 V
Red Pitaya IN2 <- external REF, within +/-1 V

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

Current meaning:

```text
OUT1 = FPGA mixer+LPF error observation.
OUT2 = FPGA control candidate / shadow control / sequential PI candidate.
OUT2 remains oscilloscope-only in the current stage.
```

Current limitations:

```text
The FPGA has not fully replaced D2-125.
The FPGA has not independently completed a real laser closed loop.
There is not yet ramp_generator / scan_lock_fsm / relock / lock quality judgment.
There is not yet host peak selection or AI/CNN automatic lock supervisor.
```

## 2. Current v2B3 status

`pi_controller_seq.sv` is the current sequential PI candidate path. It is selected by the top-level mode when `LASER_LOCK_CONTROL_PATH_MODE=1`. This means:

```text
CONTROL_PATH_MODE=0: timing-safe P-only fallback.
CONTROL_PATH_MODE=1: sequential PI candidate.
CONTROL_PATH_MODE=2: legacy complete PI, reference/simulation only.
```

Even if Vivado timing is clean, v2B3 is not yet a real laser lock. It must first pass OUT1/OUT2 oscilloscope verification:

```text
OUT1 -> oscilloscope: FPGA error remains visible.
OUT2 -> oscilloscope: sequential PI candidate is safe, limited, and explainable.
OUT2 must not connect to laser, D2-125 Servo Output, D2-125 Aux Output, Scan/PZT, or current feedback in this stage.
```

## 3. Correct D2-125 replacement mapping

| D2-125 function | Future Red Pitaya / host replacement |
|---|---|
| Analog mixer/LPF error generation | FPGA error chain: `mixer_core -> lpf_core -> OUT1/error` |
| Servo Output -> potentiometer -> interference-filter laser fast current feedback | FPGA fast current control, later as one low-gain branch only |
| Servo Output -> laser power supply slow current feedback | FPGA slow current control, later stage |
| Aux Servo Output triangular scan in Ramp state | FPGA `ramp_generator` / triangle scan |
| Aux Servo Output auxiliary Scan/PZT control in Lock state | FPGA slow scan / PZT control |
| Ramp / Unlock / Lock transitions | FPGA `scan_lock_fsm` plus host supervision |
| Manual lock-point choice and tuning | Host software, later AI / 1D-CNN peak recognition and parameter suggestion |

## 4. Updated stage plan

| Stage | Goal | Allowed actuator connection? | Notes |
|---|---|---|---|
| v2B3 | sequential PI timing + OUT1/OUT2 oscilloscope validation | No | OUT2 is still a control candidate only |
| v2D | FPGA error observation and possible later OUT1-to-D2 Error Input comparison | No for OUT2 | Confirms FPGA error chain usefulness |
| v2E | OUT2 open-loop observation against real error / D2 behavior | No | Compare polarity, limit, noise, and trend on oscilloscope only |
| v2F | one low-gain single-branch closed-loop test | Yes, one branch only after explicit SOP | Not full D2-125 replacement |
| v3 | ramp_generator, scan_lock_fsm, Aux/Scan replacement, relock, lock quality | Later | Replaces Ramp/Unlock/Lock workflow gradually |
| v4 | host-assisted spectrum selection and lock workflow | Later | Host controls parameters and records data |
| v5 | AI / 1D-CNN peak recognition, parameter suggestion, relock supervisor | Later | AI is slow supervisor, not high-speed PID |

## 5. v2F boundary: single low-gain branch only

v2F must not be described as a full D2-125 replacement. It is only the first low-gain real actuator experiment.

Rules:

```text
Only one real feedback branch may be connected in v2F.
Do not simultaneously connect fast current, slow current, and Aux/Scan/PZT.
D2-125 output must be disconnected from the same actuator terminal before Red Pitaya OUT2 is connected there.
Kp, Ki, enable, output_limit, polarity, and reset-safe behavior must be reviewed before connection.
OUT2 must first pass oscilloscope-only validation.
```

## 6. v3 boundary: scan and D2 workflow replacement

v3 begins only after v2F single-branch safety is understood.

v3 work may include:

```text
ramp_generator
scan_lock_fsm
Ramp / Unlock / Lock state machine
Aux Servo Output replacement
Scan/PZT slow control
relock logic
lock quality judgment
```

These items are not part of current v2B3/v2D/v2E.

## 7. v4/v5 boundary: host and AI

v4/v5 are where host automation and AI become the innovation layer:

```text
v4: host spectrum selection, parameter panel, data logging, lock workflow UI.
v5: AI / 1D-CNN peak recognition, Vlock recommendation, Kp/Ki suggestion, lock/unlock decision, Rescan trigger.
```

AI must not be placed in the high-speed PID loop. The FPGA remains responsible for real-time mixer, LPF, P/PI, output limiting, and reset-safe actuator outputs. The host and AI act as a slow supervisor.

## 8. Permanent safety boundaries

```text
IN1/IN2 must remain within +/-1 V.
OUT2 must not be paralleled with D2-125 Servo Output on the same feedback terminal.
OUT2 must not be paralleled with D2-125 Aux Servo Output on Scan/PZT.
Before voltage range, polarity, feedback gain, and actuator response are confirmed, Red Pitaya output must not connect to a real laser feedback terminal.
Default bitstream must keep actuator-facing outputs safe.
All actuator outputs need output_limit, enable gating, reset safe value, and an emergency stop path.
Current OUT2 remains oscilloscope-only until a later SOP explicitly permits one low-gain branch.
```

## 9. Historical notes

Older notes that describe `D2-125 DC Error -> Red Pitaya IN1`, full direct D2 replacement, or simultaneous multi-actuator control are historical only. They must not be used as the current execution route.
