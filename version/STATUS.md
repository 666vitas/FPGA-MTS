# STATUS

## 2026-06-30 v2B3 mode=1 sequential PI 时序通过记录

这里记录的是用户手动运行 Vivado Implementation 后给出的结果，只作为项目状态记录。
Codex 本次没有运行 Vivado，没有综合、实现、生成 bitstream，也没有烧录 Red Pitaya。

```text
2026-06-xx 用户手动 Vivado Implementation:
WNS = +0.107 ns
TNS = 0.000 ns
Failing Endpoints = 0
WHS = 0.054 ns
THS = 0
结论：mode=1 sequential PI 候选版本 timing clean。
```

边界说明：

```text
timing clean != 已经锁定激光
timing clean != 已经完成 D2-125 替代
timing clean != 允许把 OUT2 接到激光器
```

下一步仍然只能做示波器验证：

```text
OUT1 -> 示波器：确认 FPGA laser_error / error observation 正常
OUT2 -> 示波器：确认 FPGA laser_control / sequential PI 候选输出正常
当前阶段 OUT2 禁止连接激光器、D2-125 Servo Output、D2-125 Aux/Scan，
也禁止连接任何真实执行器通道。
```

## 2026-06-23 v2B3 mode=1 上板候选已准备，等待用户手动 timing 验证

当前实际实验接线记录：

```text
PD -> v1 既有带通/放大链路 -> Red Pitaya IN1
同路解调 REF -> Red Pitaya IN2
OUT1 -> 板内 mixer + LPF 后的 FPGA demodulated error -> 示波器 CH2
OUT2 -> 当前代码产生的 shadow/sequential control -> 示波器 CH4
```

v2B1 timing-safe P-only Shadow Control 上板验证已完成：`mixer.csv` 的 OUT2/OUT1 Vpp 为 `0.515`，`no-mixer.csv` 为 `0.555`；OUT2 没有打到 `+/-1 V`，证明 OUT2 安全输出通道已打通，但这不是激光锁定实验，也不能声称替代 D2-125。

本轮顶层已新增 `LASER_LOCK_CONTROL_PATH_MODE=1` 并显式传给 `laser_lock_core`。这使下一次用户手动生成的候选工程选择 v2B3 sequential PI；OUT1/OUT2 顶层 DAC 路由保持不变。该候选尚未完成新的 Vivado timing 或示波器验证，因此 OUT2 仍只能接示波器。

## 2026-06-22 v2B2/v2B3 sequential PI RTL/SIM 完成，等待 Vivado timing

v2B1 已关闭：OUT2 timing-safe P-only 安全输出已完成上板示波器验证，记录的 implementation 为 `WNS=+0.361 ns`、`TNS=0.000 ns`、`Failing Endpoints=0`，且 OUT2/OUT1 实测约为 `0.515` 与 `0.555`。

本轮新增 `pi_controller_seq.sv`，使用七状态顺序更新：`IDLE -> CAPTURE -> P_CALC -> I_CALC -> I_UPDATE -> SUM -> LIMIT`。完整 PI 算法保持 P、I、offset、对称限幅和 anti-windup 语义，但乘法、积分更新、求和、限幅分拍寄存，避免旧完整 PI 的单条长组合路径。

`laser_lock_core.sv` 现在使用：

```text
CONTROL_PATH_MODE=0：timing-safe P-only Shadow Control，当前默认回退路径。
CONTROL_PATH_MODE=1：新的 pi_controller_seq sequential PI，v2B3 目标路径。
CONTROL_PATH_MODE=2：旧 pi_controller，仅参考/仿真，不作默认板级路径。
```

本轮 XSim：

```text
tb_pi_controller_seq: tests=35 pass=35 fail=0
tb_laser_lock_core_v2b1_shadow_pi_dc_error: tests=27 pass=27 fail=0
```

当前仍不能声称 sequential PI 已 timing-clean 上板，也不能将 OUT2 接激光器、D2-125 Servo Output 或 Scan。下一步由用户手动把 `pi_controller_seq.sv` 加入 Vivado Design Sources 后检查 timing；只有 XSim、Vivado timing、OUT2 示波器都通过，才讨论低增益闭环。

## 2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器测试完成

本次由用户完成 Vivado 重新综合、实现、bitstream 生成和 Red Pitaya 烧录；记录的 timing 结果为：

```text
WNS = +0.361 ns
TNS = 0.000 ns
Failing Endpoints = 0
```

本轮接线仅为 `OUT1 -> 示波器`、`OUT2 -> 示波器`。OUT2 没有接激光器、D2-125、Scan 或 Servo Output。

### 上板数据

| 数据文件 | OUT2 shadow control | Board OUT1 error | OUT2 / OUT1 | 其他同步观察 |
|---|---:|---:|---:|---|
| `mixer.csv` | Vpp `0.01771 V`，RMS `0.007694 V` | Vpp `0.03439 V`，RMS `0.003643 V` | `0.515` | Saturated absorption peak：Vpp `0.1893 V`，RMS `0.8157 V`；D2-125 error：Vpp `1.829 V`，RMS `0.3469 V` |
| `no-mixer.csv` | Vpp `0.02644 V`，RMS `0.006752 V` | Vpp `0.04768 V`，RMS `0.004388 V` | `0.555` | Saturated absorption peak：Vpp `0.1793 V`，RMS `0.8147 V`；D2-125 error：Vpp `0.0402 V`，RMS `0.2935 V` |

比例计算：

```text
mixer.csv:    0.01771 / 0.03439 = 0.515
no-mixer.csv: 0.02644 / 0.04768 = 0.555
```

### 实验结论

```text
2026-06-22 v2B1 timing-safe P-only Shadow Control 上板示波器测试完成。

1. OUT1 能输出 FPGA mixer+LPF 后的 error signal，幅度为几十 mVpp。
2. OUT2 能输出由 OUT1 派生的 P-only shadow control。
3. OUT2 / OUT1 比例约为 0.5。
4. OUT2 没有打到 +/-1 V。
5. OUT2 没有出现明显失控、饱和或积分爬升。
6. 该现象与 RTL 中 protected_error >>> 1 的 timing-safe P-only 设计一致。

阶段结论：v2B1 的 OUT2 控制输出通道已经打通。
当前版本可作为“OUT2 安全输出验证通过”的实验记录。
```

### 小白解释：为什么 OUT1 / OUT2 只有几十 mV

这是安全测试版本的正常现象，不是失败。OUT2 当前不是完整 PI/PID 的大范围控制量，而是将 `protected_error` 做 `>>> 1` 后的半幅 P-only 输出；同时没有数字增益放大、没有积分累积，因此 OUT1 和 OUT2 都保持在较小幅度，便于先验证 OUT2 输出通道是否安全、方向是否合理。

### 仍然有效的限制

```text
当前版本不是完整 PI。
当前版本不是 PID。
当前版本不能锁定激光。
当前版本不能声称替代 D2-125。
OUT2 仍然只能接示波器。
OUT2 禁止接激光器。
OUT2 禁止接 D2-125 Servo Output。
OUT2 禁止接 Scan。
D2-125 DC Error 禁止接 Red Pitaya IN1。
```

## 2026-06-16 当前主线：v2B1 timing-safe P-only Shadow Control（当前有效）

手动 Vivado Implementation 已暴露一个关键 timing 问题：完整 `pi_controller.sv` 直接放进 v2B1 主工程路径时，125 MHz 下未通过时序，记录现象约为 `WNS=-10.995 ns`、`TNS=-5029 ns`。最差路径位于：

```text
i_laser_lock_core/u_output_protect/data_o_reg
-> i_laser_lock_core/i_pi_controller
-> control_o_reg
```

该路径穿过 DSP48E1、CARRY4、48-bit integrator、anti-windup freeze、integrator_accepted、P+I+offset limiter 和 `control_o` 更新逻辑。结论是：完整 PI 算法仍然保留为 v2A 已验证核心，但不能再作为 v2B1 默认上板路径。

当前有效 RTL 策略：

```text
v0.94/rtl/pi_controller.sv：不修改，保留完整 PI + anti-windup，供后续 v2B2/v2B3 流水线化使用。
v0.94/rtl/laser_lock_core.sv：默认 USE_FULL_PI_CONTROLLER=0，使用 timing-safe P-only Shadow Control。
OUT1：继续观察 FPGA mixer+LPF error。
OUT2：只输出很小的 P-only shadow control，只接示波器。
```

当前默认板级链路：

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o / OUT1

同一个 protected_error
-> timing-safe P-only Shadow Control
-> control_o / OUT2
```

OUT2 预期：约为 OUT1 error 的 1/2，并受 `PID_OUTPUT_LIMIT_DEFAULT=1500` 限制，约 `+/-0.18 V`。当前仍不能接激光器，不能接 D2-125 Servo Output，不能接 Scan，不能声称已经闭环替代 D2-125。

本轮独立 XSim 回归：

```text
xvlog：0 error，0 warning
xelab：0 error，0 warning
xsim：tests=18 pass=18 fail=0
日志：v0.94/xvlog.log，v0.94/xelab.log，v0.94/xsim.log
```

## 2026-06-14 当前主线：v2B1 FPGA MTS Error Shadow PI（当前有效）

当前安全主线已经从旧的“D2-125 DC Error -> Red Pitaya IN1”旁路方案，修正为使用 Red Pitaya 自身 IN1/IN2 生成 FPGA 内部 error，并把该 error 同时送到 OUT1 观察和 OUT2 Shadow PI 控制输出。

### 当前硬件接线边界

```text
Red Pitaya IN1 -> 混频前 PD/MTS 信号，必须在 +/-1 V 内
Red Pitaya IN2 -> 外部 REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器 CH2：FPGA mixer+LPF error，当前约 0.12~0.15 V
Red Pitaya OUT2 -> 示波器 CH4：FPGA P-only control
```

禁止：

```text
D2-125 DC Error -> Red Pitaya IN1
D2-125 Servo Output -> Red Pitaya IN1
Red Pitaya OUT2 -> 激光器
Red Pitaya OUT2 -> D2-125 Servo Output 三通
Red Pitaya OUT2 -> 激光器电源 Scan
任何超过 +/-1 V 的信号进入 IN1/IN2
```

### 当前代码状态

```text
v0.94/rtl/laser_lock_core.sv：
control_o 不再固定为 0，已接入 pi_controller。

v0.94/rtl/red_pitaya_top.sv：
OUT1 / DAC A 仍为 laser_error；
OUT2 / DAC B 已改为 laser_control。

v0.94/rtl/pi_controller.sv：
本次未修改，继续使用 v2A 已完成的 PI 控制器核心。

v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv：
新增 v2B1 Shadow PI 行为仿真。
```

### 初始参数

```text
PID_ENABLE_DEFAULT = 1
PID_HOLD_DEFAULT = 0
PID_RESET_INTEGRATOR_DEFAULT = 0
PID_POLARITY_DEFAULT = 0
PID_KP_DEFAULT = 16'sd2048
PID_KI_DEFAULT = 16'sd0
PID_OFFSET_DEFAULT = 14'sd0
PID_OUTPUT_LIMIT_DEFAULT = 14'd1500
PID_UPDATE_HZ = 10_000
```

含义：

```text
Kp=2048：OUT2 约为 OUT1 error 的 1/2
Ki=0：避免 OUT2 积分慢慢爬升
output_limit=1500：约 +/-0.18 V，防止 OUT2 接近 +/-1 V
```

### 独立仿真状态

```text
xvlog：0 error
xelab：0 error
xsim：SUMMARY tests=13 pass=13 fail=0
```

### 本轮不执行

```text
Codex 不运行 Vivado
Codex 不运行 synthesis
Codex 不运行 implementation
Codex 不生成 bitstream
Codex 不生成 bin
Codex 不烧录 Red Pitaya
Codex 不修改 redpitaya.xpr
```

Vivado、bitstream、bin 和烧录由用户手动完成。

## 2026-06-14 旧方案记录：v2B1 Shadow PI DC Error（已废弃 / 禁止执行）

> 注意：本节保留为历史记录，不再作为当前执行路线。禁止把 D2-125 DC Error 或 D2-125 Servo Output 接入 Red Pitaya IN1。当前有效主线见本文档最前面的“v2B1 FPGA MTS Error Shadow PI”。

当前下一步不是 `ramp_generator`，不是完整 `scan/lock`，也不是 FPGA 直接替代 D2-125。当前下一步定义为：

```text
v2B1 Shadow PI DC Error 旁路测试

D2-125 DC Error
-> Red Pitaya IN1
-> pi_controller
-> OUT2 示波器
```

当前真实接线：

```text
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 三通 -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3，后续接 Red Pitaya IN1
Red Pitaya OUT2 -> 后续示波器 CH4
```

v2A 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代：

```text
D2-125 Error Input -> Servo PI/PID -> Servo Output
对应
error_i -> pi_controller.sv -> control_o
```

v2A2 独立仿真报告结论：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

这只证明 `pi_controller.sv` 独立 testbench 通过，不证明它已进入主工程、已接 OUT2、已生成 bitstream、已上板或已控制激光。

下一步代码边界：

```text
允许修改：
v0.94/rtl/laser_lock_core.sv
v0.94/rtl/red_pitaya_top.sv

允许新建：
v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv

禁止修改：
v0.94/rtl/pi_controller.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
```

本轮文档任务不修改任何 `.sv`，不运行 XSim，不运行 Vivado，不生成 bitstream，不上板。

## 2026-06-15 注释与路线清理状态

本轮允许对 RTL/SIM 增加解释性注释，但不允许改变功能逻辑。当前已经把 v2B1 的有效路线固定为：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> output_protect -> error_o -> OUT1
error_o -> pi_controller -> control_o -> OUT2
```

所有后续文档和代码注释都必须把 `D2-125 DC Error -> Red Pitaya IN1` 视为历史废弃路线，不得作为当前接线方案。OUT1 在 v2B1-v2F 继续作为 error observation；OUT2 第一阶段只接示波器。

## 当前阶段

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

## 当前协作原则

每个子阶段最多一次 Claude Code 集中审查和一次 Codex 修正。通过回归仿真后关闭子阶段，不再循环审查。

## v1 状态

v1 已完成 FPGA 数字解调基础链路：

```text
PD -> ADC -> mixer -> LPF -> error-like signal -> OUT1 -> D2-125 -> Laser
```

含义：FPGA 已经能产生可用于 D2-125 的 error-like signal。当前真正闭环控制激光的仍然是 D2-125。

## v2 总目标

```text
用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo 功能。
```

v2 目标链路：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2 -> Laser actuator
```

OUT1 在 v2B-v2F 始终保留为 error observation。OUT2 第一阶段只接示波器。

## v2 阶段图

```text
v2A：独立数字 PI 核心
  v2a-1：P-only
  v2a-2：I + anti-windup

v2B：系统接口和主工程集成
v2C：Vivado 综合、实现、时序、DRC 和 bitstream
v2D：OUT2 示波器空载上板测试
v2E：真实 MTS error 输入、OUT2 开环观察
v2F：低增益闭环替代 D2-125
v2G：FPGA PI 与 D2-125 性能对比
```

## v2A 当前记录

- v2a-1：P-only 已关闭；不再重复 GPT 或 Claude Code 审查。
- v2a-2：I 通道、integrator 和 anti-windup 已完成初次实现和独立 XSim 回归；等待一次 Claude Code 集中审查。

## v2B 开始前必须回答

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

## 当前禁止事项

- 不修改 RTL，除非用户另行明确授权。
- 不运行 XSim，除非用户另行明确授权。
- 不运行 Vivado。
- 不生成 bitstream。
- 不上板。
- 不把 OUT2 接激光。
- 不开始 CNN。
- 不开始相位自动匹配。
- 不开始双 PID。

## 关键文档

- `E:\new\fpga_lock\v94\version\v2\V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_GOAL_AND_CHAIN.md`
- `E:\new\fpga_lock\v94\version\v2\V2_DEVELOPMENT_ROADMAP.md`
- `E:\new\fpga_lock\v94\version\v2\V2_NEXT_STEPS.md`
- `E:\new\fpga_lock\v94\version\v2\GPT_REVIEW_V2_SUMMARY.md`
