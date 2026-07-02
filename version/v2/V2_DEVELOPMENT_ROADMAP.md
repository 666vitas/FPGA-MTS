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

## 2026-06-23 v2B3 上板候选选择状态

`pi_controller_seq.sv` 已通过独立 XSim，mode=1 集成路径已通过 XSim。顶层 `red_pitaya_top.sv` 现显式使用：

```text
LASER_LOCK_CONTROL_PATH_MODE = 1
-> laser_lock_core CONTROL_PATH_MODE = 1
-> pi_controller_seq
-> OUT2 候选输出
```

这一步仅把 v2B3 设为下一次用户手动 Vivado 的候选路径；不等于 timing 已通过，不等于可锁激光。v2B1 P-only 上板证据仍作为 mode=0 回退基线保留：OUT2/OUT1 为 `0.515`（mixer.csv）与 `0.555`（no-mixer.csv）。

## 2026-06-22 v2B2/v2B3 状态：RTL/SIM 通过，板级 timing 验证待用户执行

| 子阶段 | 当前状态 | 已完成 | 尚未完成 |
|---|---|---|---|
| v2B1 | CLOSED | timing-safe P-only OUT2 上板示波器验证；WNS `+0.361 ns` | 不扩大 P-only 功能 |
| v2B2 | RTL/SIM PASS | `pi_controller_seq.sv`；35/35 PASS | Vivado synthesis/implementation/timing |
| v2B3 | RTL/SIM PASS | `CONTROL_PATH_MODE=1` 集成；27/27 PASS | mode 1 的 timing 与 OUT2 示波器验证 |

控制路径规则：

```text
mode 0：默认 timing-safe P-only 回退路径。
mode 1：sequential PI，等待用户手动 Vivado timing 和示波器验证。
mode 2：旧完整 PI，仅参考/仿真，不作为板级默认。
```

只有 sequential PI 的 XSim、Vivado timing、OUT2 示波器三项都通过，才进入 v2D/v2E 的进一步开环观察；之后才讨论 v2F 低增益闭环。当前 OUT2 仍只接示波器。

## 2026-06-22 v2B1 上板验证完成：OUT2 安全输出验证通过

v2B1 timing-safe P-only Shadow Control 已完成 timing-clean 上板示波器测试。用户记录的 implementation 结果：`WNS=+0.361 ns`、`TNS=0.000 ns`、`Failing Endpoints=0`。烧录后 OUT1 输出 FPGA mixer+LPF error，OUT2 输出 P-only shadow control。

两组板级数据均支持半幅关系：

| 数据文件 | OUT2 Vpp | OUT1 Vpp | OUT2 / OUT1 | 结论 |
|---|---:|---:|---:|---|
| `mixer.csv` | `0.01771 V` | `0.03439 V` | `0.515` | 与 `protected_error >>> 1` 一致 |
| `no-mixer.csv` | `0.02644 V` | `0.04768 V` | `0.555` | 与当前 P-only shadow control 一致 |

v2B1 已完成的范围是“OUT2 安全输出验证”，不是完整 PI/PID，也不是激光闭环。下一路线固定为：

```text
v2B2：timing-clean pipelined PI controller。
v2B3：将流水线 PI 重新集成到 OUT2。
v2D/v2E：在 OUT2 仍只接示波器的前提下继续开环观察。
v2F：满足物理接口、安全限幅和低增益条件后，才讨论闭环替代 D2-125。
```

## 2026-06-16 v2B1 timing 修复后的当前有效路线

v2B1 的默认上板目标从“完整 `pi_controller` 直接驱动 OUT2”调整为“timing-safe P-only Shadow Control”。原因是：手动 Vivado Implementation 已显示完整 PI 直接进入 125 MHz 主路径会严重 timing fail，约 `WNS=-10.995 ns`、`TNS=-5029 ns`，最差路径在 `i_laser_lock_core/i_pi_controller` 内部，穿过 DSP、CARRY、integrator、anti-windup 和 limiter。

当前保留两条路线，但默认只走安全路线：

| 路线 | 当前状态 | 用途 |
|---|---|---|
| `USE_FULL_PI_CONTROLLER=0` | v2B1 默认 | 小逻辑、寄存输出、P-only、OUT2 只接示波器，优先解决 timing |
| `USE_FULL_PI_CONTROLLER=1` | 保留但不默认 | 完整 PI + anti-windup，后续 v2B2/v2B3 做流水线化后再回到主路径 |

当前有效阶段划分：

```text
v2B1：timing-safe P-only Shadow Control，上板前必须重新跑 Vivado timing
v2B2：完整 pi_controller 流水线化设计，不改变 v2A 算法意图
v2B3：流水线 PI 重新集成到 OUT2 路径
v2C：Vivado 综合、实现、时序、DRC 和 bitstream
v2D：OUT2 示波器空载上板测试
v2F：低增益闭环替代 D2-125
```

小白理解：现在先让 OUT2 有一个很小、可预测、容易过时序的影子控制量。完整 PI 没丢，只是不能拿一个已经 timing fail 的长组合路径去冒险烧板。

## 2026-06-15 v2 当前有效路线：FPGA MTS Error Shadow PI

v2 的总目标不是“一步完整复刻 D2-125”，而是先用 FPGA 数字 PI 逐步替代 D2-125 的基础 servo core。D2-125 还包含 Ramp、Offset、Scan/Lock 切换、Servo Output、Aux Servo Output、relock、锁定质量判断等完整工作流；这些不属于当前 v2B1，后续放到 v3 以后处理。

当前有效链路是：

```text
Red Pitaya IN1 -> 混频前 PD/MTS 信号，必须在 +/-1 V 内
Red Pitaya IN2 -> REF，必须在 +/-1 V 内

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

当前禁止继续把下面旧方案当作有效路线：

```text
D2-125 DC Error Monitor -> Red Pitaya IN1 -> pi_controller -> OUT2
```

该 DC Error 旁路方案只保留为历史记录，不再执行。禁止把 D2-125 DC Error、D2-125 Servo Output、激光电源 Scan 或任何超过 +/-1 V 的信号接入 Red Pitaya IN1/IN2。OUT2 在 v2B1/v2D 第一阶段只接示波器，不接激光、不接 D2-125 Servo Output、不接 Scan。

## v2B1 到 v3/v4/v5 的阶段边界

| 阶段 | 替代对象 | 代码功能 | 板上现象 | 是否接激光 |
|---|---|---|---|---|
| v2B1 | D2-125 Servo Core 的 shadow output | `error_o -> pi_controller -> OUT2` | OUT1 = FPGA error；OUT2 = 小幅 P-only control | 否 |
| v2C | Vivado project bit generation | 用户手动综合、实现、生成 bitstream | 还没有板上波形结论 | 否 |
| v2D | OUT2 示波器空载上板测试 | bitstream 烧录后 OUT2 只接 CH4 | OUT2 跟随 OUT1，且不超过约 +/-0.18 V | 否 |
| v2E | 参数方向确认 | 调整 polarity、Kp、limit | OUT2 方向和幅度可解释 | 否 |
| v2F | 低增益替代 Servo Output | OUT2 接一个真实控制端，D2 输出断开 | error 不发散，OUT2 不饱和 | 是，低增益 |
| v2G | FPGA PI 与 D2-125 对比 | 记录 RMS、锁定时间、饱和次数 | 形成可重复对比数据 | 是 |
| v3 | 替代 scan 和 lock 工作流 | ramp、scan/lock FSM、relock | FPGA 能扫描、找峰、切锁 | 后续 |
| v4/v5 | 自动优化和 AI | 数据集、基准、AI 参数建议 | 自动调参/锁定状态识别 | 后续 |

## 当前 v2 代码文件作用

| 文件 | 当前作用 | 小白理解 |
|---|---|---|
| `v0.94/rtl/red_pitaya_top.sv` | 把 `laser_lock_core` 的 `error_o/control_o` 路由到 OUT1/OUT2 | 板子最外层接线板，决定 OUT1/OUT2 最后输出什么 |
| `v0.94/rtl/laser_lock_core.sv` | v2B1 主链路：IN1/IN2 混频、低通、保护、送 PI | FPGA 内部的“误差信号生成 + Shadow PI”小系统 |
| `v0.94/rtl/mixer_core.sv` | 数字混频 | 把 PD/MTS 信号和 REF 相乘 |
| `v0.94/rtl/lpf_core.sv` | mixer 后低通 | 把混频后的高频项压下去，留下 error-like signal |
| `v0.94/rtl/output_protect.sv` | 输出保护和 reset 安全 | 避免 reset 或异常时输出乱跑 |
| `v0.94/rtl/pi_controller.sv` | v2A 完成的 PI core | 只替代 D2-125 servo core 的基础控制计算 |
| `v0.94/sim/tb_pi_controller.sv` | 独立 PI core 回归测试 | 证明 PI 零件自己算得对 |
| `v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` | v2B1 集成行为测试 | 证明 OUT1 仍看 error，OUT2 会给小幅 Shadow PI 输出 |

## 2026-06-14 v2B1 Shadow PI 路线插入

v2A / v2a-1 / v2a-2 已完成的是 FPGA 版 D2-125 Servo Core，不是完整 D2-125 替代。

当前推荐路线改为：

```text
v2B1：DC Error Shadow PI
v2C：Vivado 综合 / bitstream
v2D：OUT2 示波器测试
v2E：真实 error 开环观察
v2F：低增益手动替代 Servo Output
v3：Ramp / Scan / Lock 状态机
```

v2B1 数据链路：

```text
D2-125 DC Error Monitor
-> Red Pitaya IN1
-> v2A 已完成的 pi_controller.sv
-> Red Pitaya OUT2
-> 示波器 CH4
```

v2B1 只做 Shadow PI：D2-125 继续负责真实扫描和真实锁定；OUT2 只接示波器；不替代 D2-125 Ramp、Servo Output 或 Aux Servo Output。

下一步允许的代码范围：

```text
允许修改：laser_lock_core.sv、red_pitaya_top.sv
允许新建：tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv
禁止修改：pi_controller.sv、mixer_core.sv、lpf_core.sv、output_protect.sv
```

本文档给出 v2 的主阶段路线。v2a-1 和 v2a-2 只是 v2A 的内部子阶段，不再作为整个 v2 的主体叙述。

## 1. 总原则

v2 按“先算法零件、再系统集成、再 Vivado、再示波器、再真实闭环”的顺序推进。

```text
v2A 独立 PI 核心
-> v2B 系统接口和主工程集成
-> v2C Vivado 综合、实现、时序、DRC 和 bitstream
-> v2D OUT2 示波器空载上板测试
-> v2E 真实 MTS error 输入、OUT2 开环观察
-> v2F 低增益闭环替代 D2-125
-> v2G FPGA PI 与 D2-125 性能对比
```

## 2. v2A：独立数字 PI 核心

目标：先在独立 testbench 里证明 PI 算法零件安全、可算、可审查。

内部子阶段：

- v2a-1：P-only。
- v2a-2：I + anti-windup。

输入：人工构造的 error、kp、ki、offset、limit、enable、hold、polarity。

输出：仿真中的 `control_o`、`p_term_o`、`i_term_o`、`sat_o`。

工具：独立 XSim。v2A 不运行 Vivado 主工程，不生成 bitstream，不上板。

当前状态：

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

## 3. v2B：系统接口和主工程集成

目标：把 v2A 的 PI core 接到 v1 已验证的 `mixer + LPF` 后面，形成：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2
```

必须保留：

- OUT1 始终保留为 error observation。
- OUT2 第一阶段只接示波器。
- enable 默认关闭。
- output limit 默认保守。
- v1 的 OUT1 路径不能被破坏。

v2B 开始前必须回答五个物理问题：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

## 4. v2C：Vivado 编译和 bitstream

目标：确认完整主工程能综合、实现、通过关键 DRC/timing，并生成来源明确的 bitstream。

工具：Vivado Synthesis、Implementation、DRC、Timing、Generate Bitstream。

通过标准：0 fatal error；关键 warning 可解释；bitstream 对应的源码和文档版本可追踪。

不能声称：v2C 通过不等于 OUT2 硬件安全，也不等于可以接激光。

## 5. v2D：OUT2 示波器空载上板测试

目标：OUT2 只接示波器，验证硬件输出安全。

示波器要看：

- reset 后 OUT2 是否为安全值。
- enable=0 时 OUT2 是否安全。
- enable=1 后 OUT2 是否按预期变化。
- hold 是否冻结输出。
- output limit 是否真的限幅。
- OUT1 是否仍然是 error observation。

通过标准：OUT2 无异常跳变、无不可解释 offset、无超限；OUT1 路径不受影响。

不能声称：v2D 通过不等于已闭环，不等于已替代 D2-125。

## 6. v2E：真实 MTS error 输入、OUT2 开环观察

目标：让 PI 看到真实 MTS error-like signal，但 OUT2 仍只接示波器。

示波器要看：

- OUT1 上的真实 error-like signal。
- OUT2 是否随 error 方向合理变化。
- OUT2 是否噪声过大、是否频繁饱和。
- 改变 polarity 后方向是否符合预期。

通过标准：OUT2 对真实 error 的幅度、方向、限幅和噪声都可解释。

不能声称：v2E 通过仍不代表激光已经由 FPGA 锁住。

## 7. v2F：低增益闭环替代 D2-125

目标：在低 Kp、低 Ki、小 output limit、明确执行器安全范围的条件下，让 OUT2 接入一个真实激光控制端，短时间替代 D2-125 的基础 servo 功能。

通过标准：

- error 没有发散。
- OUT2 没有长期打满。
- 激光没有被拉飞。
- 能快速回退到 D2-125。
- 锁定现象可重复。

不能声称：v2F 初通不等于性能优于 D2-125，也不等于完成双执行器控制。

## 8. v2G：FPGA PI 与 D2-125 性能对比

目标：用统一指标比较 D2-125 和 FPGA PI。

比较内容：

- error RMS。
- 锁定保持时间。
- 饱和次数。
- 恢复能力。
- 噪声。
- 参数敏感性。

通过标准：有重复实验、有同一条件下的对比数据，而不是只凭一次示波器截图。

## 9. 后续版本边界

- v3：scan/lock control、自动寻峰、自动重锁 FSM。
- v4：IQ 解调、相位优化、相位自动匹配。
- v5：上位机 AI 识峰、CNN peak recognition、参数建议。
- 后续版本：双 DAC、PZT + current 双执行器控制。

这些内容不进入当前 v2A 文档闭环，也不作为 v2a-2 的阻塞项。
