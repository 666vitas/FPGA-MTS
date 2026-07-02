# 当前状态总结

> Active baseline: only the GitHub project `666vitas/FPGA-MTS` `v0.94` mainline plus `version/v2` documentation are valid. Do not read, reference, sync, copy, or modify any `weifang` or `version-weifang` directory for this route.

## 0. 当前最新状态（2026-07-02 同步）

当前只使用 `v0.94` 主线。本文档早期 v1ab 记录只作为历史，不再作为当前执行路线。

当前 FPGA 已实现：

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

当前硬件意义：

```text
IN1 <- PD + BPF + amplifier, within +/-1 V
IN2 <- external REF, within +/-1 V
OUT1 -> FPGA mixer+LPF error observation
OUT2 -> FPGA control candidate / shadow control / sequential PI candidate
```

当前还没有完成：

```text
No complete D2-125 replacement.
No independent real FPGA laser closed loop.
No ramp_generator.
No scan_lock_fsm.
No relock logic.
No lock quality judgment.
No host-side spectrum selection for custom FPGA mode.
No AI / CNN automatic locking.
```

Current OUT2 remains oscilloscope-only. It must not be connected to the laser, D2-125 Servo Output tee, laser power supply Scan/PZT, or any D2-125 output in the current stage.

## 1. Correct D2-125 real wiring model

Current analog baseline:

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

Unlock state:

```text
D2-125 does not close the loop.
The user manually adjusts laser current, temperature, interference-filter angle, Scan offset, and optical alignment.
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

The Servo Output is one main PID current-feedback signal. The tee only splits it into two current-feedback branches. The potentiometer adjusts fast-branch gain; it does not change the feedback type.

Aux Servo Output:

```text
Ramp state: triangular scan to Scan/PZT.
Lock state: auxiliary PI / slow Scan-PZT correction for lock-center maintenance and slow drift compensation.
```

## 2. Current active files and meaning

| File | Current role |
|---|---|
| `v0.94/rtl/red_pitaya_top.sv` | Routes `laser_lock_core` outputs to OUT1/OUT2 |
| `v0.94/rtl/laser_lock_core.sv` | IN1/IN2 mixer + LPF + output_protect + OUT2 control candidate |
| `v0.94/rtl/mixer_core.sv` | Digital multiplier for PD/MTS and REF |
| `v0.94/rtl/lpf_core.sv` | Post-mixer low-pass filter |
| `v0.94/rtl/output_protect.sv` | Reset / output safety protection |
| `v0.94/rtl/pi_controller.sv` | Full PI core kept as algorithm reference / later path |
| `v0.94/rtl/pi_controller_seq.sv` | Current timing-oriented sequential PI candidate |

## 3. Current allowed wiring

```text
Red Pitaya IN1 <- PD + BPF + amplifier, within +/-1 V.
Red Pitaya IN2 <- external REF, within +/-1 V.
Red Pitaya OUT1 -> oscilloscope, or later D2-125 Error Input after a dedicated SOP.
Red Pitaya OUT2 -> oscilloscope only.
```

## 4. Current forbidden wiring

```text
OUT2 must not connect to the laser.
OUT2 must not connect to the D2-125 Servo Output tee.
OUT2 must not connect to laser power supply Scan/PZT.
OUT2 must not be paralleled with any D2-125 output.
D2-125 DC Error must not be used as Red Pitaya IN1.
D2-125 Servo Output must not be used as Red Pitaya IN1.
IN1/IN2 must never exceed +/-1 V.
```

## 5. Correct future replacement mapping

| D2-125 function | Future FPGA / host replacement |
|---|---|
| Analog mixer/LPF error generation | FPGA error chain |
| Servo Output -> potentiometer -> fast current feedback | FPGA fast current control, later one low-gain branch |
| Servo Output -> laser power supply slow current feedback | FPGA slow current control, later stage |
| Aux Servo Output triangular scan | FPGA `ramp_generator` |
| Aux Servo Output Lock-state Scan/PZT slow control | FPGA slow scan / PZT control |
| Ramp / Unlock / Lock state switching | FPGA `scan_lock_fsm` plus host supervision |
| Manual peak selection and tuning | Host workflow, later AI / 1D-CNN |

## 6. Near-term development boundary

```text
v2B3:
  Sequential PI timing and OUT1/OUT2 oscilloscope validation.

v2F:
  Only one low-gain branch may be tested.
  Do not simultaneously connect fast current, slow current, and Aux/Scan/PZT.

v3:
  ramp_generator, scan_lock_fsm, relock, lock quality judgment, and Aux/Scan replacement.

v4/v5:
  host spectrum selection, automatic peak recognition, AI/CNN, and parameter suggestions.
```

## 7. Safety summary

```text
Current OUT2 is a candidate output, not an actuator output.
Default bitstream must keep actuator-facing outputs safe.
All future actuator outputs must have output_limit, enable gating, reset safe value, and an emergency stop route.
No Red Pitaya output may be paralleled with a D2-125 output.
```
