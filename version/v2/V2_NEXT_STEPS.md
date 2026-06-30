# V2_NEXT_STEPS

## 2026-06-30 Next Step After v2B3 Timing Clean

Recorded user manual Vivado Implementation result:

```text
WNS = +0.107 ns
TNS = 0.000 ns
Failing Endpoints = 0
WHS = 0.054 ns
THS = 0
Conclusion: mode=1 sequential PI candidate is timing clean.
```

This closes the timing-risk question for the current mode=1 sequential PI
candidate, but it does not close the laser-lock question.

Immediate next step:

```text
OUT1 -> oscilloscope: verify laser_error remains visible and sane.
OUT2 -> oscilloscope: verify laser_control is bounded and sane.
OUT2 must still not connect to laser, D2-125 Servo Output, D2-125 Aux/Scan,
or any real actuator path.
```

New stage split:

```text
v2B3-close
v2PZT-DOC
v2PZT-RTL-SAFE-SCAN-HOLD
v2PZT-RTL-PLOCK
v2PZT-RTL-PILOCK
v2HOST-REG
```

Planning reference:

```text
version/v2/V2_CUSTOM_REGISTER_INTERFACE_AND_OUT2_PLAN.md
```

## 2026-06-23 当前下一步：v2B3 sequential PI mode=1 上板候选

v2B1 P-only 验证已经完成，不再重复证明 OUT2 是否存在。`red_pitaya_top.sv` 已显式设置 `LASER_LOCK_CONTROL_PATH_MODE=1`，使 `laser_lock_core` 选择 `CONTROL_PATH_MODE=1` 的 sequential PI；OUT1/OUT2 的 DAC A/DAC B 路由未改变。

下一步是用户手动验证 mode=1，而不是重复 P-only 上板测试：

```text
1. 确认 pi_controller_seq.sv 在 Design Sources，tb_*.sv 不在 Design Sources。
2. 确认 red_pitaya_top 是 Design Top，LASER_LOCK_CONTROL_PATH_MODE=1。
3. Run Synthesis、Run Implementation，检查 WNS >= 0、TNS = 0。
4. timing 通过后才 Generate Bitstream；失败则不得生成可上板 bit。
5. 烧录后 OUT1 -> CH2，OUT2 -> CH4；OUT2 仍不得接激光器。
```

顺序 PI 的短时 OUT2 可能很像 P-only；当同号 error 长时间存在时，小 Ki 可能带来缓慢基线移动。正常情况下 OUT2 仍受 limit 约束，不应接近 `+/-1 V`、随机跳变、快速爬升或快速饱和。

## 2026-06-22 当前下一步：用户手动验证 v2B2/v2B3 sequential PI timing

v2B1 P-only OUT2 安全输出验证已经关闭。v2B2 的 `pi_controller_seq.sv` 与 v2B3 的 `CONTROL_PATH_MODE=1` 集成 XSim 已通过，但默认仍是 `CONTROL_PATH_MODE=0` 的 timing-safe P-only 回退路径。

用户手动下一步：

```text
1. 打开 v0.94/project/redpitaya.xpr。
2. 将 v0.94/rtl/pi_controller_seq.sv 加入 Design Sources。
3. 确认 laser_lock_core.sv 来自 v0.94/rtl，red_pitaya_top 仍是 Design Top。
4. 确认所有 tb_*.sv 不在 Design Sources。
5. 手动 Run Synthesis 和 Run Implementation。
6. 检查 WNS >= 0、TNS = 0，并检查最差路径不在 pi_controller_seq 内部。
7. timing 通过后才 Generate Bitstream。
8. 烧录后只接示波器：OUT1 -> CH2，OUT2 -> CH4。
```

在 sequential PI 完成 XSim、Vivado timing 和 OUT2 示波器验证前，`CONTROL_PATH_MODE` 默认不得从 `0` 改为 `1`。OUT2 仍禁止接激光器、D2-125 Servo Output 或 Scan。

## 2026-06-22 当前下一步：进入 v2B2 / v2B3，不再重复证明 OUT2 是否存在

v2B1 已完成 timing 通过后的上板示波器验证：`WNS=+0.361 ns`、`TNS=0.000 ns`、`Failing Endpoints=0`；OUT2/OUT1 实测比例为 `0.515`（mixer.csv）和 `0.555`（no-mixer.csv），符合当前 `protected_error >>> 1` 的半幅 P-only 预期。

下一步不是继续证明 OUT2 是否存在，因为 OUT2 已经通过示波器验证。下一步进入：

```text
v2B2：设计 timing-clean pipelined PI controller。
v2B3：将流水线 PI 重新接入 OUT2。
v2D/v2E：继续进行 OUT2 示波器开环观察。
v2F：在安全条件满足后，才进行低增益闭环替代 D2-125。
```

进入 v2B2 前必须保存本次 `mixer.csv`、`no-mixer.csv` 和示波器截图，作为 v2B1 baseline。当前 P-only 版本不再扩大功能范围，不重复修改来证明已经完成的 OUT2 输出通道。

仍然禁止：OUT2 接激光器、D2-125 Servo Output 或 Scan；D2-125 DC Error 接 Red Pitaya IN1；宣称当前版本已锁定激光或已替代 D2-125。

## 2026-06-16 当前下一步：用户手动 Vivado timing 复查，不直接上板

v2B1 已改为默认 `USE_FULL_PI_CONTROLLER=0` 的 timing-safe P-only Shadow Control。完整 `pi_controller.sv` 没有删除、没有改坏，但当前不作为默认 OUT2 板级路径；后续需要 v2B2/v2B3 做流水线 PI 后再重新接回。

用户手动下一步只允许：

```text
1. 打开 v0.94/project/redpitaya.xpr
2. 确认仿真 tb 文件没有被当作 Design Source 使用
3. 确认 top module 仍为 red_pitaya_top
4. 确认 laser_lock_core.sv 来自 v0.94/rtl
5. 手动 Run Synthesis
6. 手动 Run Implementation
7. 检查 timing summary：WNS/TNS 必须不再是阻塞性负值
8. 只有 timing 通过后，才允许 Generate Bitstream
9. 烧录后第一轮只接示波器：OUT1->CH2，OUT2->CH4
```

仍然禁止：

```text
不要把 timing fail 的设计拿去烧录
不要用 multicycle path 或 false path 掩盖未经验证的控制路径
不要把 OUT2 接激光器
不要把 OUT2 接 D2-125 Servo Output / Scan / Aux / Current / PZT
不要声称已经闭环替代 D2-125
```

示波器预期：

```text
OUT1：原 FPGA mixer+LPF error，预计约 0.12~0.15 V
OUT2：小 P-only shadow control，约 OUT1 的一半，且受 +/-0.18 V 左右限制
```

## 2026-06-14 v2B1 Shadow PI 当前下一步（当前有效）

v2B1 已把 v2A 的 `pi_controller.sv` 接入主链路的 Shadow PI 位置。当前目标不是闭环替代 D2-125，而是先让 FPGA 在 OUT2 上输出一个安全、很小、可观察的 P-only control。

### 当前 RTL 链路

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o
-> OUT1

同时：

error_o
-> pi_controller
-> control_o
-> OUT2
```

### 已完成

```text
laser_lock_core.sv：control_o 不再固定为 0，已实例化 pi_controller
red_pitaya_top.sv：OUT1 / DAC A 仍接 laser_error，OUT2 / DAC B 改接 laser_control
tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv：新增 v2B1 Shadow PI 行为仿真
XSim：tests=13 pass=13 fail=0
```

### Codex 本次不做

```text
Codex 不运行 Vivado
Codex 不运行 synthesis
Codex 不运行 implementation
Codex 不生成 bitstream
Codex 不生成 bin
Codex 不烧录 Red Pitaya
Codex 不修改 redpitaya.xpr
```

### 用户手动下一步

```text
1. 打开 v0.94/project/redpitaya.xpr
2. 在 Sources 中确认 v0.94/rtl/pi_controller.sv 已存在
3. 如果不存在，手动 Add Sources：v0.94/rtl/pi_controller.sv
4. 确认 laser_lock_core.sv 和 red_pitaya_top.sv 来自 v0.94/rtl
5. 手动 Run Synthesis
6. 手动 Run Implementation
7. 手动 Generate Bitstream
8. 烧录后先只接示波器，不接激光，不接 D2-125 Servo Output
```

### 烧录后应该看到

```text
OUT1 / CH2：仍是 FPGA mixer+LPF error，当前约 0.12~0.15 V
OUT2 / CH4：跟随 OUT1 error 的小 P-only control
Kp=2048：OUT2 约为 OUT1 的 1/2
Ki=0：OUT2 不应慢慢爬升
output_limit=1500：OUT2 不应超过约 +/-0.18 V
polarity=0：OUT2 与 OUT1 同向
```

### 必须停止的现象

```text
OUT2 接近 +/-1 V
OUT2 随机跳变
OUT2 慢慢爬升
OUT1 原有 error 现象消失
任意 IN1/IN2 输入超过 +/-1 V
有人准备把 OUT2 接激光器或 D2-125 Servo Output
```

## 2026-06-14 旧方案记录：v2B1 Shadow PI DC Error（已废弃 / 禁止执行）

> 注意：本节保留为历史记录，不再作为当前下一步。禁止执行“D2-125 DC Error -> Red Pitaya IN1”。当前有效下一步见本文档最前面的“v2B1 Shadow PI 当前下一步”。

当前下一步不是 `ramp_generator`，不是完整 `scan/lock`，而是：

```text
v2B1 Shadow PI DC Error

D2-125 DC Error
-> Red Pitaya IN1
-> pi_controller
-> OUT2 示波器
```

v2A 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代。它对应：

```text
D2-125 Error Input -> Servo PI/PID -> Servo Output
error_i -> pi_controller.sv -> control_o
```

v2A2 独立 XSim 结果：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

这只说明 `pi_controller.sv` 独立 testbench 通过，不说明它已经接入 `red_pitaya_top`、OUT2、bitstream 或真实激光。

当前真实接线必须作为 v2B1 前提：

```text
D2-125 Ramp -> 示波器 CH1
D2-125 DC Error -> 示波器 CH3
模拟 mixer 后 error -> D2-125 Error Input
D2-125 Servo Output -> 激光器电源 / 激光器锁定控制端
D2-125 Aux Servo Output -> 激光器电源 Scan
Red Pitaya OUT2 -> 后续示波器 CH4
```

下一条代码任务标题草案：

```text
v2B1 Shadow PI DC Error to OUT2 RTL Integration
```

本次不执行该代码任务。

## 1. 当前状态

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

v2a-1 已经关闭：P-only RTL、首次仿真、Claude Code 集中审查、最终修正和 XSim 回归仿真全部完成。v2a-1 不再重复 GPT 或 Claude Code 审查。

v2a-2 已经完成 I 通道、integrator 和 anti-windup 的初次实现，并完成独立 XSim 回归。当前下一步不是继续扩大测试范围，也不是直接接主工程，而是等待 Claude Code 对 v2a-2 进行一次集中静态审查。

## 2. 最近一步

最近一步只做：

```text
Claude Code 对 v2a-2 做一次集中审查
```

审查结论只允许是：

- PASS
- PASS WITH NOTES
- FAIL

如果 PASS 或 PASS WITH NOTES，则 v2A 关闭，进入 v2B 系统集成准备。如果 FAIL，则 Codex 只做一次集中修正和回归仿真；通过后关闭 v2A，不再循环审查同一版本。

## 3. v2B 开始前必须回答的五个问题

进入 v2B 前，GPT 和用户必须明确：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

这些是物理接口问题，不是 RTL 算法问题。没有这些答案，就不能安全决定 OUT2 的限幅、offset、polarity 和 PI 更新速率。

## 4. v2B 的最小任务

v2B 的最小任务是系统接口和主工程集成：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2
```

同时必须保持：

```text
OUT1 -> error observation
```

OUT1 在 v2B-v2F 始终保留为 error observation。OUT2 第一阶段只接示波器，不接激光，不接 D2-125，不接任何真实反馈端。

## 5. 当前禁止事项

当前仍然禁止：

- 不修改 `laser_lock_core.sv`，除非另开 v2B 授权任务。
- 不修改 `red_pitaya_top.sv`。
- 不修改 `redpitaya.xpr`。
- 不运行 Vivado。
- 不生成 bitstream。
- 不上板。
- 不把 OUT2 接激光。
- 不开始 CNN。
- 不开始相位自动匹配。
- 不开始双 PID。

## 6. 下一主阶段

```text
下一主阶段：v2B 系统接口和主工程集成。
```

但 v2B 只能在 v2a-2 一次 Claude Code 集中审查完成，并且五个物理问题有答案之后开始。
