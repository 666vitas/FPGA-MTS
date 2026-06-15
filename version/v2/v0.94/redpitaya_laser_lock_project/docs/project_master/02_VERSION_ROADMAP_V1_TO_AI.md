# 版本路线：从 v1 到 AI

本文件把项目从当前 `v1ab_passthrough_debug` 到最终 AI-assisted locking 的路线拆成小版本。每个版本只增加一个主要能力。

## v2-0 状态同步补充（2026-06-15）

根据 Claude 独立审查报告和当前真实工程，PI core 已经提前进入 v2B1，不应再把 PI/PID 写成很后面的全新模块任务。当前真实状态：

```text
v2B1 已经集成 mixer_core + lpf_core + output_protect + pi_controller。
pi_controller.sv 是 PI 控制器，不是完整 PID。
当前 Ki=0，因此运行模式是 P-only Shadow PI。
OUT1 = error_o 示波器观察。
OUT2 = control_o 示波器观察。
OUT2 还没有接激光器闭环。
当前还没有 ramp/sweep。
当前还没有 scan/lock FSM。
当前还没有在线寄存器调参接口。
```

后续 v2 的重点不是创建 `pid_lock_core.sv`，而是：

```text
启用很小 Ki
保持 output_limit 很小
完成 Vivado 编译
完成电子学回环测试
OUT2 仍然只接示波器
之后再进入 ramp/sweep 与 scan/lock
```

当前统一主线：

```text
v1ab IN1->OUT1 和 IN2->OUT1 已经真实上板通过，
现在允许进入 v1c mixer_only，
最终 v1 完成 PD/REF 数字 MTS error signal。
```

当前 `v1ab_passthrough_debug` 已完成两项真实上板测试：

```text
v1ab-1: IN1 -> OUT1，通过
v1ab-2: IN2 -> OUT1，通过
```

v1ab 仍然不是 MTS error，它只证明 `IN1/IN2 -> ADC -> FPGA core -> DAC A -> OUT1` 的硬件通路可用。下一步允许进入 `v1c_mixer_only`，但 v1c 只验证数字 mixer，不允许接 `D2-125`，也不能声称已经完成 MTS 解调或锁频。

## 当前真实模拟链路与 FPGA 等效目标

当前实验台真实模拟链路是：

```text
PD signal
  -> 10 MHz Low Pass Filter
  -> 1.8 MHz High Pass Filter
  -> Mini-Circuits ZFL-500LN+ RF Amplifier
  -> Mini-Circuits ZFM-3+ Mixer
       REF input = 4.6 MHz sine from signal generator
  -> IF / mixed output
  -> servo / D2-125 error input
```

FPGA v1 后续要逐步等效替代：

| 真实器件/功能 | FPGA 模块目标 | 初始设计参数 |
|---|---|---|
| `10 MHz Low Pass Filter` | `bpf_core.sv` 的上边界 / digital LPF | cutoff ≈ `10 MHz` |
| `1.8 MHz High Pass Filter` | `bpf_core.sv` 的下边界 / digital HPF | cutoff ≈ `1.8 MHz` |
| 两个滤波器形成的带通链路 | `digital BPF` | passband roughly `1.8-10 MHz`，保留 `4.6 MHz` 调制相关成分 |
| `ZFL-500LN+ RF Amplifier` | `digital_gain.sv` | 名义等效约 `×15.85`，初始可选 `×1, ×2, ×4, ×8, ×16`，必须防溢出 |
| `ZFM-3+ Mixer` | `mixer_core.sv` | signed `14-bit × 14-bit -> 28-bit`，缩放回 signed `14-bit` |
| mixer 后低通 | `lpf_core.sv` | `v1d` 以后加入，cutoff 按 error signal 带宽和实验需求确定 |
| OUT1 安全输出 | `output_protect.sv` / 后续限幅 | `OUT1` 先接示波器，`v1g` 才允许接 `D2-125` |

## v1ab_passthrough_debug

目标：

- `OUTPUT_MODE=0`：`IN1 -> OUT1`；
- `OUTPUT_MODE=1`：`IN2 -> OUT1`。

输入：

- `pd_i = adc_dat[0]`，来自 Red Pitaya `IN1`；
- `ref_i = adc_dat[1]`，来自 Red Pitaya `IN2`。

输出：

- `error_o -> OUT1`；
- 历史 v1ab 阶段为 `control_o = 0`，`OUT2` 不应有异常控制输出；当前 v2B1 已改为 `control_o -> OUT2` 的 P-only Shadow PI 观察输出。

要新增的 RTL：

- 已有 `laser_lock_core.sv`；
- 已有 `output_protect.sv`。

testbench：

- 已有 `tb_laser_lock_core_v1ab.sv`；
- 检查 `OUTPUT_MODE=0` 时 `error_o` 跟随 `pd_i`；
- 检查 `OUTPUT_MODE=1` 时 `error_o` 跟随 `ref_i`；
- 检查 reset 后输出归零；
- 检查 `control_o` 恒为 0。

Vivado 操作：

- 打开 `.xpr`；
- Add Sources 加入 `laser_lock_core.sv` 和 `output_protect.sv`；
- 确认 top 是 `red_pitaya_top.sv`；
- 确认 `USE_LASER_LOCK_CORE = 1'b1`；
- 根据测试目的设置 `LASER_LOCK_OUTPUT_MODE`；
- `Run Synthesis`、`Run Implementation`、`Generate Bitstream`。

上板测试：

- `OUTPUT_MODE=0` 测 `IN1 -> OUT1`；
- `OUTPUT_MODE=1` 测 `IN2 -> OUT1`；
- `OUT1` 只接示波器。

成功标准：

- `OUT1` 能看到同频波形；
- 不削顶；
- 不长时间顶死；
- `OUT2` 无异常输出。

失败回退：

- 回到 `USE_LASER_LOCK_CORE = 0` 检查官方路径；
- 检查 Vivado Sources 是否添加文件；
- 检查 `OUTPUT_MODE`；
- 检查输入信号是否真的进板；
- 回退到 `IN1 -> OUT1` 最简单测试。

是否允许接 `D2-125`：

- 不允许。

是否允许接激光器反馈：

- 不允许。

意义：

验证 `IN1/IN2` 输入和 `OUT1` 输出通路。

当前进度：

- `v1ab` RTL 已生成；
- testbench 已通过；
- Vivado `synthesis / implementation / bitstream` 已成功；
- `.bit` 已转换为 `.bit.bin`；
- `.bit.bin` 已上传到 Red Pitaya；
- 已通过 `fpgautil -b /root/red_pitaya_top.bit.bin` 加载成功；
- 终端显示 `BIN FILE loaded through FPGA manager successfully`；
- `v1ab-1: IN1 -> OUT1` 已真实上板通过；
- `v1ab-2: IN2 -> OUT1` 已真实上板通过。

进入下一版本门槛：

```text
v1ab IN1 -> OUT1 真实上板通过
v1ab IN2 -> OUT1 真实上板通过
```

两项都通过后，才允许进入 `v1c_mixer_only`。

当前结论：

```text
允许进入 v1c_mixer_only。
```

## v1c_mixer_only

目标：

```text
pd_i * ref_i -> scaled error_o
```

对应真实器件：

```text
Mini-Circuits ZFM-3+ Mixer
```

`v1c` 只做数字乘法，不加 LPF/BPF/gain。它的意义是验证模拟 mixer 的 FPGA 等效实现。

输入：

- `pd_i`；
- `ref_i`。

输出：

- 经过缩放后的乘法结果到 `error_o -> OUT1`。

要新增的 RTL：

- `mixer_core.sv`；
- 在 `laser_lock_core.sv` 中接入 mixer；
- 必要时增加缩放和限幅逻辑。

testbench：

- 用已知正负数检查 signed 乘法；
- 检查 14-bit 到 28-bit 再缩放回 14-bit 的方向；
- 检查不会因为溢出导致长期顶死。

Vivado 操作：

- Add Sources 加入 `mixer_core.sv`；
- 更新后的 `laser_lock_core.sv` 必须在 Sources 中；
- 重新 `Run Synthesis`、`Run Implementation`、`Generate Bitstream`。

上板测试：

- 先用信号发生器给 `IN1/IN2` 两路安全小信号；
- 第一次上板测试可以先用较低频同频信号，例如 `100 kHz / 100 kHz`，确认 mixer 链路后再切到 `4.6 MHz`；
- `OUT1` 看 mixer 结果；
- 不接真实 PD；
- 不急着接真实 PD 和真实 4.6 MHz REF；
- 不接 D2-125。

成功标准：

- `OUT1` 随两路输入变化；
- 不恒为 0；
- 不长期满幅；
- 极性和缩放与仿真解释一致。

失败回退：

- 回退到 `v1ab`；
- 只测 `IN1 -> OUT1` 和 `IN2 -> OUT1`；
- 仿真中先看乘法内部宽位结果。

是否允许接 `D2-125`：

- 不允许。

是否允许接激光器反馈：

- 不允许。

意义：

验证数字 mixer。

## v1d_mixer_lpf

目标：

```text
pd_i * ref_i -> LPF -> error_o
```

输入：

- `pd_i`；
- `ref_i`。

输出：

- 低通后的基础数字 lock-in 解调输出。

要新增的 RTL：

- `lpf_core.sv`；
- mixer 后的缩放和滤波连接；
- 输出保护继续保留。

testbench：

- 输入带有乘法高频分量的模拟数据；
- 检查 LPF 输出比 mixer 原始输出更平滑；
- 检查滤波器 reset 后状态归零。

Vivado 操作：

- Add Sources 加入 `lpf_core.sv`；
- 确认 `laser_lock_core.sv` 引用了正确模块；
- 重新完整综合实现和生成 bitstream。

上板测试：

- 先用模拟输入；
- 改变 `IN1/IN2` 相位或幅度，观察 `OUT1` 低频变化；
- 仍然只接示波器。

成功标准：

- `OUT1` 不再主要表现为高频乘法分量；
- 对输入幅度/相位变化有合理响应；
- 不严重削顶。

失败回退：

- 旁路 LPF 回到 `v1c`；
- 降低输入幅度；
- 检查 LPF 系数和位宽增长。

是否允许接 `D2-125`：

- 不允许。

是否允许接激光器反馈：

- 不允许。

意义：

得到基础数字 lock-in 解调输出。

## v1e_real_pd_ref

目标：

```text
真实 PD + 外部 REF -> mixer + LPF -> error-like signal
```

输入：

- 真实 `PD -> IN1`；
- 外部安全衰减后的 `4.6 MHz REF -> IN2`。

输出：

- `OUT1` 上的真实实验 `error-like signal`。

要新增的 RTL：

- 通常不新增核心模块，主要调整 gain、缩放、保护；
- 必要时增加 DC remove bypass 或输入监测。

testbench：

- 使用 PD-like 信号和 REF 信号；
- 检查输出对相位、幅度、offset 有合理响应。

Vivado 操作：

- 使用 `v1d` 通过后的工程；
- 每次改 gain/scale 都重新生成 bitstream；
- 保留清晰版本号。

上板测试：

- `PD -> IN1`；
- 安全衰减后 `REF -> IN2`；
- `OUT1 -> 示波器`；
- 同时记录模拟链路 error 作为对比。

成功标准：

- 第一次看到真实实验链路的 FPGA `error-like signal`；
- 幅度和 offset 在安全范围；
- 信号随实验调谐变化。

失败回退：

- 回到信号发生器模拟输入；
- 回到 `v1d`；
- 回到 `v1ab` 检查输入输出通路。

是否允许接 `D2-125`：

- 不允许。

是否允许接激光器反馈：

- 不允许。

意义：

第一次看到真实实验链路的 FPGA `error-like signal`。

## v1f_bpf_gain_enable

目标：

```text
PD -> DC remove / BPF around 4.6 MHz / gain -> mixer -> LPF -> error_o
```

输入：

- `PD -> IN1`；
- `4.6 MHz REF -> IN2`。

输出：

- 经 BPF、mixer、LPF 后的 `error_o -> OUT1`。

要新增的 RTL：

- `adc_frontend.sv` 或 `bpf_core.sv`；
- gain / scaling 相关逻辑；
- DC remove 可作为可选前级；
- BPF bypass 开关，方便回退。

BPF 系数要求：

- 必须根据 ADC 采样率、`4.6 MHz` 中心频率、目标带宽和定点位宽计算；
- 不能直接照搬模拟滤波器的 `1.8 MHz high-pass + 10 MHz low-pass` 参数；
- 模拟滤波器参数只能说明实验想保留的大致频段，不能直接变成 FPGA 定点滤波器系数。

testbench：

- 输入包含低频、4.6 MHz 附近和高频成分的混合信号；
- 检查 BPF 对 4.6 MHz 附近成分更敏感；
- 检查 bypass 和 enable 两种模式。

Vivado 操作：

- Add Sources 加入 BPF/前端模块；
- 注意滤波器资源和 timing；
- 完整跑 synthesis、implementation、bitstream。

上板测试：

- 对比 BPF bypass 和 BPF enable；
- 对比 FPGA `OUT1` 与原模拟 mixer/LPF 输出；
- 仍先接示波器。

成功标准：

- 替代模拟 `1.8 MHz high-pass + 10 MHz low-pass` 的前处理效果初步可见；
- 启用 BPF 后目标调制成分更突出；
- 不明显损坏 error-like 形状。

失败回退：

- 关闭 BPF bypass 回到 `v1e`；
- 降低滤波阶数；
- 重新计算系数。

是否允许接 `D2-125`：

- 不允许，除非已经进入并确认 `v1g`。

是否允许接激光器反馈：

- 不允许。

意义：

替代模拟 `10 MHz LPF + 1.8 MHz HPF + RF amplifier` 的前处理和放大作用。

## v1g_error_to_D2_125

目标：

```text
OUT1 -> D2-125 error input
```

输入：

- 真实 PD；
- 安全 REF；
- 完整 FPGA error 链路。

输出：

- `OUT1` 接 `D2-125 error input`。

要新增的 RTL：

- 重点不是新增算法，而是完善 gain、offset、limit、保护；
- 可能需要输出幅度限制和 enable 开关。

testbench：

- 检查最大最小输出；
- 检查 reset 时输出安全；
- 检查异常输入时不会长时间满幅。

Vivado 操作：

- 使用通过 `v1f` 的工程；
- 确认 `OUT1` 幅度/offset 设计值；
- 生成明确命名的 bitstream。

上板测试：

- 先 `OUT1 -> 示波器`；
- 确认幅度、offset、极性、是否削顶和是否顶死都安全；
- 再接 `D2-125 error input`；
- 仍不让 FPGA 直接控制激光器反馈。

成功标准：

- 用 FPGA error 替代模拟 mixer 输出；
- D2-125 接收到安全、可用的 error；
- 接入后没有明显异常饱和。

失败回退：

- 立即断开 `D2-125`；
- 回到示波器；
- 回到 `v1f` 或 `v1e`。

是否允许接 `D2-125`：

- 允许，但必须先用示波器确认安全。

是否允许接激光器反馈：

- 仍不允许 FPGA 直接接激光器反馈。D2-125 自身闭环需另行确认。

意义：

用 FPGA error 替代模拟 mixer 输出。

## v2_fpga_pid

目标：

```text
error_o -> pi_controller -> control_o -> OUT2
```

状态同步：

```text
本节旧标题中的 PID 是历史叫法。
当前实际使用 pi_controller.sv，不创建 pid_lock_core.sv。
pi_controller.sv 已实现并集成到 laser_lock_core.sv。
当前 Ki=0，所以 v2B1 是 P-only Shadow PI 示波器观察版。
当前不是“PID 未实现”，而是“PI 已集成但尚未真实闭环”。
```

输入：

- FPGA error；
- PI 参数；
- enable/disable 信号。

输出：

- `control_o -> OUT2`。

要新增的 RTL：

- 不创建 `pid_lock_core.sv`；
- 当前继续使用 `pi_controller.sv`；
- v2-1 只考虑把 `PID_KI_DEFAULT` 从 0 改成很小的非零值；
- 保持 `PID_OUTPUT_LIMIT_DEFAULT` 很小；
- 后续才考虑在线寄存器调参接口。

testbench：

- 阶跃误差响应；
- 积分限幅；
- 输出饱和；
- reset 后安全输出。

Vivado 操作：

- 如果 Vivado 工程缺少 `pi_controller.sv`，由用户手动 Add Sources；
- 注意乘法器、位宽、timing；
- 先生成调试 bitstream。

上板测试：

- 先做电子学回环或假 error；
- 只用示波器看 `OUT2`；
- 不直接闭环激光器；
- 确认输出范围和符号。

成功标准：

- `OUT2` 对 error 有可解释响应；
- 不乱跳；
- reset/disable 时安全。
- 小 Ki 不导致慢慢爬升失控。

失败回退：

- PI disable；
- `control_o` 回到安全零输出；
- 回到 `v1g`。

是否允许接 `D2-125`：

- 视系统架构而定。若 FPGA PID 替代 D2-125，则不应同时让两套 PID 打架。

是否允许接激光器反馈：

- 默认不允许，必须单独审查安全和极性。

意义：

逐步替代 `D2-125` 的基础 servo core。它不能代表完整 D2-125 替代，因为 ramp/sweep、scan/lock/relock、锁定质量判断和在线调参仍未完成。

## v3_fpga_sweep

目标：

```text
FPGA 生成约 50 Hz、约 400 mVpp sweep
```

输入：

- sweep enable；
- amplitude；
- offset；
- frequency。

输出：

- sweep waveform，可叠加到控制输出或单独输出。

要新增的 RTL：

- sweep/ramp generator；
- amplitude/offset limit；
- enable/hold。

testbench：

- 频率检查；
- 幅度检查；
- reset/disable 安全检查。

Vivado 操作：

- Add Sources；
- 综合实现；
- 生成专用测试 bitstream。

上板测试：

- 先示波器看 sweep；
- 不接激光器反馈；
- 确认约 `50 Hz`、约 `400 mVpp`。

成功标准：

- sweep 频率正确；
- 幅度和 offset 安全；
- enable/disable 可控。

失败回退：

- disable sweep；
- 回到固定输出；
- 回到 v2 或 v1g。

是否允许接 `D2-125`：

- 需要按实验接线单独确认。

是否允许接激光器反馈：

- 默认不允许，必须先通过示波器和假负载。

意义：

为后续自动找峰和锁定准备扫描能力。

## v4_lock_relock_fsm

目标：

```text
扫描、找峰、进入锁定、失锁检测、自动重扫
```

输入：

- error；
- peak/lock 指标；
- sweep 状态；
- 用户 enable。

输出：

- lock state；
- sweep enable；
- PID enable；
- relock request。

要新增的 RTL：

- `lock_relock_fsm.sv`；
- 状态机；
- timer/counter；
- threshold 判断。

testbench：

- 正常锁定流程；
- 失锁流程；
- 自动重扫流程；
- 异常输入回退。

Vivado 操作：

- Add Sources；
- 检查状态机综合；
- 注意跨模块 reset 和 enable。

上板测试：

- 先离线或半自动；
- 记录每个状态；
- 不直接让系统无人值守控制激光器。

成功标准：

- 状态转换符合预期；
- 失锁能进入安全重扫；
- 不出现未知状态。

失败回退：

- FSM disable；
- 手动模式；
- 回到 v3/v2。

是否允许接 `D2-125`：

- 视当时控制架构决定。

是否允许接激光器反馈：

- 需要单独安全审查和人工监控。

意义：

让系统具备自动扫描、锁定、失锁检测、自动重扫的骨架。

## v5_ai_assisted_locking

目标：

```text
AI 峰识别、锁定状态识别、重锁策略
```

输入：

- error waveform；
- sweep waveform；
- lock state；
- 历史数据窗口。

输出：

- peak candidate；
- lock quality；
- relock decision；
- 建议参数。

要新增的 RTL：

- 第一阶段不建议把 AI 放进 PL；
- 可新增数据窗口导出、特征统计、状态标志；
- AI 初期放在 PC/PS 端。

testbench：

- 用历史波形数据验证特征输出；
- 用离线脚本验证 AI 判断；
- FPGA 只验证数据通路。

Vivado 操作：

- 只综合必要的数据导出和特征模块；
- 不急于把 CNN/AI 推理塞进 FPGA。

上板测试：

- 采集数据；
- 离线标注；
- 验证 AI 判断和人工判断是否一致。

成功标准：

- AI 能识别峰或锁定状态；
- 自动重锁建议比盲扫更可靠；
- FPGA 主链路仍稳定。

失败回退：

- AI disable；
- 回到 FSM 规则模式；
- 回到人工判断。

是否允许接 `D2-125`：

- 取决于 v1g/v2-v4 的稳定程度。

是否允许接激光器反馈：

- 必须非常谨慎，AI 不能在未经审查时直接控制激光器反馈。

意义：

实现 AI 峰识别、锁定状态识别和自动重锁策略。
