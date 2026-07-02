# D2-125 Real Wiring and State Model

> Scope: this document records the current experimentally confirmed D2-125 wiring model for the active `v0.94` mainline only. Do not read, reference, sync, copy, or modify any `weifang` or `version-weifang` directory for this project route.

## 1. Current analog baseline chain

```text
Laser
-> Rb / MTS optical path
-> PD
-> analog band-pass filtering
-> Mini-Circuits RF amplifier
-> analog mixer x 4.6 MHz REF
-> MTS error
-> D2-125 Error Input
```

In the current analog baseline, the FPGA is not yet the independent lock controller. The D2-125 still performs the mature scan / unlock / lock workflow and drives the real laser actuators.

## 2. D2-125 operating states

The D2-125 must be described as a stateful servo system with three practical states:

```text
Ramp
Unlock
Lock
```

### 2.1 Ramp state

```text
D2-125 Auxiliary Servo Output
-> laser power supply Scan / PZT input
-> triangular scan of laser frequency
```

Ramp is used to scan the laser frequency through the saturated absorption / MTS spectrum. It is for finding peaks, observing spectral features, and locating a candidate lock point. Ramp is not closed-loop locking.

### 2.2 Unlock state

Unlock means the D2-125 is not performing closed-loop locking. It is used while manually adjusting laser current, temperature, interference-filter angle, Scan offset, and optical alignment. Feedback outputs in this state should be treated as open-loop or safe-state outputs, not as proof of lock.

### 2.3 Lock state

```text
MTS error
-> D2-125 Error Input
-> D2-125 internal PI/PID
-> D2-125 Servo Output
-> tee splitter
   |-> laser power supply: slow current feedback
   `-> potentiometer gain adjust -> interference-filter laser: fast current feedback
```

In Lock state, the D2-125 Servo Output is the main PID current-feedback signal. The tee does not create two different control algorithms. It splits the same Servo Output voltage into two current-feedback paths. The practical fast / slow difference comes from the downstream actuator path, laser power supply response, interference-filter laser input, and the potentiometer setting.

The potentiometer adjusts the gain of the fast current-feedback branch. It does not change the feedback type.

At the same time:

```text
D2-125 Auxiliary Servo Output
-> laser power supply Scan / PZT channel
```

In Ramp state, Aux outputs the triangular scan. In Lock state, Aux can act as auxiliary PI / slow Scan-PZT control for maintaining the lock center and compensating slow drift.

## 3. Correct Servo Output definition

The corrected model is:

```text
D2-125 Servo Output = main PID current-feedback output
```

After the tee:

```text
Branch 1: Servo Output -> laser power supply -> slow current feedback
Branch 2: Servo Output -> potentiometer -> interference-filter laser -> fast current feedback
```

Both branches ultimately adjust current. The fast / slow wording should not be interpreted as two separate D2-125 outputs or two separate PID cores.

## 4. Correct Aux Servo Output definition

```text
D2-125 Aux Servo Output = Scan / PZT auxiliary output
```

Its roles are state-dependent:

```text
Ramp state:
  Aux Servo Output -> triangular scan -> Scan/PZT -> sweep spectrum

Lock state:
  Aux Servo Output -> auxiliary PI / slow correction -> Scan/PZT -> maintain lock center and compensate slow drift
```

## 5. Current Red Pitaya / FPGA mainline status

Only the GitHub project `666vitas/FPGA-MTS` `v0.94` mainline is active.

Current wiring boundary:

```text
Red Pitaya IN1 <- pre-mixer PD/MTS signal after existing BPF + amplifier, within +/-1 V
Red Pitaya IN2 <- external REF, within +/-1 V
Red Pitaya OUT1 -> FPGA mixer+LPF error observation, oscilloscope first
Red Pitaya OUT2 -> FPGA control candidate / shadow control / sequential PI candidate, oscilloscope only for the current stage
```

Current effective FPGA chain:

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

Current limitations:

```text
OUT2 is not yet a real laser actuator output.
OUT2 must first stay on the oscilloscope.
The FPGA has not fully replaced D2-125.
The FPGA has not independently completed a real laser closed loop.
There is not yet a ramp_generator, scan_lock_fsm, relock logic, lock quality judgment, or AI/CNN lock supervisor in the active RTL.
```

## 6. Future Red Pitaya replacement mapping

The correct future mapping is:

| D2-125 function | Future FPGA / host replacement |
|---|---|
| Analog mixer/LPF error generation | FPGA error chain: `IN1 + IN2 -> mixer_core -> lpf_core -> OUT1/error` |
| `Servo Output -> potentiometer -> interference-filter laser` | FPGA fast current control, later and only as one low-gain branch |
| `Servo Output -> laser power supply slow current feedback` | FPGA slow current control, later stage |
| Aux Servo Output triangular scan in Ramp state | FPGA `ramp_generator` / triangle scan |
| Aux Servo Output slow Scan/PZT control in Lock state | FPGA slow scan/PZT control |
| Ramp / Unlock / Lock workflow | FPGA `scan_lock_fsm` plus host supervision |
| Manual peak selection and parameter tuning | Host software, later AI / 1D-CNN peak recognition and parameter suggestion |

## 7. Stage boundary for replacement

The near-term replacement must remain staged:

```text
v2B3:
  sequential PI candidate timing + OUT1/OUT2 oscilloscope verification.

v2F:
  only one low-gain real feedback branch may be tested.
  Do not simultaneously connect fast current, slow current, and Aux/Scan branches.

v3:
  ramp_generator, scan_lock_fsm, relock, lock quality judgment, and Aux/Scan replacement begin.

v4/v5:
  host spectrum selection, automatic peak recognition, AI / 1D-CNN, and parameter optimization.
```

## 8. Safety boundaries

```text
Red Pitaya OUT2 must not be paralleled with D2-125 Servo Output on the same feedback terminal.
Red Pitaya OUT2 must not be paralleled with D2-125 Aux Servo Output on Scan/PZT.
Before voltage range, polarity, feedback gain, and actuator response are confirmed, Red Pitaya output must not be connected to a real laser feedback terminal.
The default bitstream must keep actuator-facing outputs safe.
Every actuator output must have output_limit, enable gating, reset safe value, and a documented emergency stop path.
IN1 and IN2 must never exceed +/-1 V.
Current OUT2 remains oscilloscope-only until a later SOP explicitly allows one low-gain actuator connection.
```
