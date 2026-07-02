# V2 开发路线图

## 当前中文总规则和安全边界

本文档面向实验用户，默认使用中文表达；文件路径、RTL 模块名、端口名、寄存器名和 Vivado timing 术语保留英文原名。

当前 D2-125 真实接线模型仍是实验安全基准：D2-125 负责真实 Ramp / Unlock / Lock 工作流，Red Pitaya / FPGA 当前只做 `mixer_core + lpf_core + output_protect` 误差观察和 `control_o / sequential PI candidate` 候选输出观察。

当前 Red Pitaya / FPGA 主线状态：

```text
v0.94 是唯一有效 FPGA 主线。
version/v2 是当前 v2 阶段文档主线。
software 是上位机软件主线。
```

当前 FPGA 已实现：

```text
mixer_core + lpf_core + output_protect
OUT1 = error_o 观察输出
OUT2 = control_o / sequential PI candidate
```

当前还没有实现：

```text
完整替代 D2-125
FPGA 独立真实激光闭环
ramp_generator
scan_lock_fsm
上位机选谱线
AI/CNN 自动锁定
```

v2B3 当前状态：`pi_controller_seq` 和 `CONTROL_PATH_MODE=1` 已完成 RTL/SIM 与用户手动 timing clean 记录，但它仍只是 OUT2 示波器候选路径，不等于可以接激光器，不等于可以替代 D2-125。

D2-125 各功能未来替代边界：

| 阶段 | 替代目标 | 当前边界 |
|---|---|---|
| v2F | 单路低增益闭环 | 只允许在明确安全 SOP 下做低增益、短时间、可回退闭环 |
| v3 | `ramp_generator`、`scan_lock_fsm`、Aux Servo Output 替代 | v3 才开始做，不属于当前 v2B3 已完成内容 |
| v4/v5 | 上位机选谱线、自动识峰、AI/CNN | 后续阶段，不作为当前上板前提 |

当前 OUT2 仍只接示波器。禁止把 OUT2 接激光器、D2-125 Servo Output 三通、Scan/PZT，或和 D2-125 输出并联。

## 2026-07-02 v2B3_scope_safe 状态：PASS WITH NOTES / 准备关闭

`v2B3_scope_safe / only-p.csv` 已完成上板示波器测试：

```text
OUT1 Vpp ≈ 0.04874 V，error observation 正常。
OUT2 Vpp ≈ 0.02410 V，mean ≈ +0.00850 V。
OUT2 不再贴 -0.2 V。
OUT2 / OUT1 Vpp ≈ 0.494。
Ki=0 修正有效。
```

阶段判断：

```text
v2B3_scope_safe = PASS WITH NOTES / 准备关闭。
```

下一阶段：

```text
v2D：
OUT2 hardcoded scan_offset + triangle 示波器验证。
```

v2D 的目标不是接 Scan/PZT，而是先证明 Red Pitaya OUT2 能安全输出类似 D2-125 Aux Ramp 的 `0.81 V offset + 小三角波`。真正接 Scan/PZT 是更后面的 v2F 或单独 PZT SOP，不是 v2D 第一轮。

## 2026-07-02 Aux/PZT 实测数据后的路线更新

最新 D2-125 Aux Output / Scan-PZT 数据表明：

```text
Ramp / Unlock:
  ramp-aux-unlock.csv:
    mean≈0.8087 V, min≈0.7505 V, max≈0.8678 V, Vpp≈0.1173 V, freq≈52.68 Hz
  ramp-aux-unlock1.csv:
    mean≈0.8096 V, min≈0.7767 V, max≈0.8393 V, Vpp≈0.0626 V, freq≈52.68 Hz

Lock:
  ramp-aux-locking.csv:
    mean≈0.8130 V, min≈0.8031 V, max≈0.8200 V, Vpp≈0.0169 V
```

这些 Aux 实测数据将作为 v3 `ramp_generator`、v3 `scan_lock_fsm`、v3 Aux/Scan replacement、v4 上位机 `Custom FPGA Lock Panel`、v5 AI / 自动重锁的设计参考。

重要边界：

```text
当前 v2B3 / v2B3_scope_safe 不使用这些数据改变接线。
当前 OUT2 仍只接示波器。
当前还没有 ramp_generator / scan_lock_fsm。
v3 之后才考虑 Aux/Scan replacement。
Red Pitaya OUT2 不能和 D2-125 Aux Output 并联到 Scan/PZT。
Red Pitaya OUT2 不能和 D2-125 Servo Output 并联。
```

后续 Red Pitaya OUT2 替代路线更新为：

| 阶段 | 目标 | 当前是否实现 |
|---|---|---|
| `v2PZT-0` | 记录 Aux/PZT 数据，确认 D2-125 Aux Output 电压范围和作用 | 本次完成文档记录 |
| `v2PZT-1` | 只实现 SAFE / SCAN / HOLD | 未实现 |
| `v2PZT-2` | OUT2 -> Scan/PZT 开环扫谱 | 未实现 |
| `v2PZT-3` | P_LOCK，`OUT2 = Vlock + Kp * error`，`Ki=0` | 未实现 |
| `v2PZT-4` | PI_LOCK，`OUT2 = Vlock + Kp * error + Ki * integral(error)` | 未实现 |
| `v3REG` | 新增 custom FPGA register_bank | 未实现 |
| `v4HOST` | 上位机新增 Custom FPGA Lock Panel | 未实现 |
| `v5AI` | AI 识峰、选 Vlock、推荐 Kp/Ki、失锁判断和重扫 | 未实现 |

当前 FPGA 已具备：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> OUT1 error
error -> 简单 P/PI candidate -> OUT2 control
```

当前还缺少：

```text
OUT2 内部三角波扫描
Capture Vlock / HOLD
P_LOCK / PI_LOCK 模式切换
register_bank
上位机 Custom FPGA Mode 下写 FPGA 参数
AI 自动识峰和自动重锁
```

安全路线必须保持：

```text
当前先回到 v2B3_scope_safe 的 OUT1/OUT2 示波器验证；
Aux 数据先作为后续设计参考；
先 SAFE / SCAN / HOLD；
先示波器；
先断开 D2-125 Aux Output；
再 Red Pitaya OUT2 -> Scan/PZT 开环扫谱；
先 P-only；
再 PI；
最后才考虑 AI。
```

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
