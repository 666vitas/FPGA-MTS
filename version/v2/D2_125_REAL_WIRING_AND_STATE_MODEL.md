<<<<<<< HEAD
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
=======
# D2-125 真实接线与状态模型

## 1. 当前模拟链路总图

当前项目仍以 D2-125 真实实验链路作为安全基准。Red Pitaya / FPGA 目前只做观察和候选控制输出，不完整替代 D2-125。

当前可理解为：

```text
PD + BPF + Amp
-> Red Pitaya IN1
-> mixer_core + lpf_core + output_protect
-> OUT1 / error_o 观察

REF
-> Red Pitaya IN2

error_o / protected_error
-> pi_controller 或 pi_controller_seq
-> OUT2 / control_o candidate
-> 目前只接示波器
```

D2-125 真实链路仍负责实际 Ramp / Unlock / Lock 工作流，以及真实 Servo Output 和 Aux Servo Output 的实验控制。

## 2. D2-125 的 Ramp / Unlock / Lock 三种状态

### Ramp

Ramp 状态用于扫谱和寻找谱线。D2-125 通过 Aux Servo Output / Scan/PZT 相关输出给激光器扫描端提供慢速扫描量，让激光频率扫过目标谱线。

当前 Red Pitaya 还没有实现可上板使用的 `ramp_generator`，也没有实现完整 `scan_lock_fsm`。

### Unlock

Unlock 状态表示系统尚未处于稳定锁定。此时可以观察 error signal、scan 波形和候选 control 输出，但不能把当前 OUT2 当作真实锁定控制量。

当前 OUT2 是 `control_o / sequential PI candidate`，仍只允许接示波器。

### Lock

Lock 状态表示 D2-125 已经通过自己的模拟控制链路维持锁定。当前 FPGA 还没有独立完成真实激光闭环，因此不能声称 FPGA 已经替代 D2-125 完成 Lock。

## 3. Servo Output 三通两路电流反馈的真实定义

D2-125 Servo Output 是真实控制输出，经过三通后进入两路电流反馈相关链路。它属于真实执行器控制路径，不是 Red Pitaya OUT2 当前可以直接并联或替代的安全节点。

当前禁止：

```text
OUT2 接 D2-125 Servo Output 三通
OUT2 和 D2-125 输出并联
OUT2 接激光器电流反馈执行器
OUT2 接任何未确认输入范围和极性的真实执行器
```

## 4. Aux Servo Output 在 Ramp 和 Lock 状态下的真实作用

在 Ramp 状态下，Aux Servo Output / Scan/PZT 相关输出提供带 DC offset 的慢速扫描量，用于扫过谱线。

在 Lock 状态下，Aux Servo Output 不再是大幅扫描，而更接近锁定点附近的保持量和小幅慢控制扰动。

Aux Output 的实测数据见：

```text
version/v2/V2_AUX_PZT_EXPERIMENT_RECORD.md
```

当前已记录的关键数值：

```text
Ramp / Unlock：
约 0.81 V offset + 0.063~0.117 Vpp triangle，主频约 52.7 Hz。

Lock：
约 0.813 V hold + 0.0169 Vpp residual / slow correction。
```

因此，未来 Red Pitaya 替代 Aux Servo Output 时，不能只输出从 0 V 开始的三角波，而应考虑：

```text
scan_offset + triangle
Capture Vlock
HOLD
P_LOCK
PI_LOCK
slow_scan_output_limit
```

这些功能当前还没有进入可接 Scan/PZT 的阶段。

当前 v2B3 / v2B3_scope_safe 阶段仍然不能用 OUT2 接 Scan/PZT。Red Pitaya OUT2 不能和 D2-125 Aux Output 同时并联到 Scan/PZT，也不能和 D2-125 Servo Output 并联。

## 5. Red Pitaya 未来替代映射

未来替代路线应分阶段推进：

| D2-125 功能 | 未来 FPGA / 上位机替代方向 | 当前状态 |
|---|---|---|
| Error 生成 | `mixer_core -> lpf_core -> output_protect` | 已实现并用于 OUT1 观察 |
| Servo Core | `pi_controller` / `pi_controller_seq` | 仅作为 OUT2 candidate，仍只接示波器 |
| Ramp | `ramp_generator` | 未实现 |
| Scan/Lock 切换 | `scan_lock_fsm` | 未实现 |
| Aux Servo Output | `scan_offset + triangle + HOLD + P_LOCK / PI_LOCK` | 未实现到可接执行器阶段 |
| 参数选择 | 上位机面板 / register_bank | 未完成 |
| 自动识峰和锁定判断 | 上位机算法 / AI/CNN | 未实现 |

## 6. 安全边界

当前允许：

```text
Red Pitaya IN1 <- PD + BPF + Amp，必须在 +/-1 V 内
Red Pitaya IN2 <- REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器
Red Pitaya OUT2 -> 示波器
```

当前禁止：

```text
OUT2 接激光器
OUT2 接 D2-125 Servo Output 三通
OUT2 接激光器电源 Scan / PZT
OUT2 和 D2-125 输出并联
D2-125 DC Error 接 Red Pitaya IN1
IN1 / IN2 超过 +/-1 V
```

## 7. 当前 OUT2 结论

当前 OUT2 仍只接示波器。

OUT2 可以作为 `control_o / sequential PI candidate` 的观察信号，但不能作为真实执行器控制信号，不能接激光器，不能接 D2-125 Servo Output，不能接 Scan/PZT，不能声称已经实现 FPGA 独立真实激光闭环。
>>>>>>> host-app-v2-integration
