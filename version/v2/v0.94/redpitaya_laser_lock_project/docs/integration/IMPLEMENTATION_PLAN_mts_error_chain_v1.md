# IMPLEMENTATION_PLAN_mts_error_chain_v1

## 0. 本文件作用

本文件说明第一阶段从“top 学习阶段”进入“功能实现阶段”的最新计划。

最新策略是：第一版 `REF` 不由 FPGA 生成，第一版 `REF` 从外部信号发生器输入 Red Pitaya `IN2`。

也就是说，FPGA 第一阶段不是信号源，不驱动 EOM，只做数字信号处理：

```text
PD -> IN1 -> adc_dat[0] -> FPGA 数字处理 -> error_o -> OUT1
REF -> IN2 -> adc_dat[1] -----------^
```

大白话解释：外部信号发生器继续负责给 EOM 打调制，也同时给 Red Pitaya 一个安全幅度的参考信号。FPGA 只拿 `PD` 和 `REF` 两路 ADC 数据做数字 mixer、低通、增益和限幅，最后从 `OUT1` 输出 error-like signal。

本文件只写计划，不写 Verilog，不修改官方工程。

## 1. 最新实验接线策略

### 1.1 外部信号发生器继续驱动 EOM

外部信号发生器继续驱动 EOM：

```text
4.6 MHz，约 8.93 Vpp
```

Red Pitaya 第一阶段不驱动 EOM。

新手必须明白：EOM 驱动是大信号、高频实验链路的一部分，第一阶段不要让 FPGA 接管它。我们先让 FPGA 只做“读信号、算 error、从 OUT1 输出”。

### 1.2 外部 REF 输入 Red Pitaya IN2

外部 `REF` 输入 Red Pitaya `IN2`：

```text
4.6 MHz
```

但是必须先衰减到 Red Pitaya 输入安全范围内，例如 ±1 V 内。

特别强调：

```text
不允许把原模拟 mixer 的 6.32 Vpp 参考信号直接接入 IN2。
```

原因很简单：Red Pitaya ADC 输入有安全范围。超过范围可能削顶，严重时可能损坏输入前端。第一阶段宁可信号小一点，也不能为了“看得明显”直接上大电压。

### 1.3 PD 输入 Red Pitaya IN1

`PD signal` 接 Red Pitaya `IN1`。

对应 FPGA 内部候选信号：

```text
pd_i = adc_dat[0]
```

### 1.4 FPGA 内部目标链路

对应 FPGA 内部目标：

```text
pd_i  = adc_dat[0]
ref_i = adc_dat[1]

pd_i
  -> optional BPF / bypass
  -> mixer_core with ref_i
  -> lowpass_filter
  -> gain/limit
  -> error_o
```

### 1.5 OUT1 输出策略

`OUT1` 输出 `error_o`。

验证顺序必须是：

```text
OUT1 -> 示波器
确认安全后 -> D2-125 error input
```

任何版本都不能直接接 `D2-125`，除非前一版已经用示波器确认 `OUT1` 幅度和 offset 安全。

## 2. 实验链路与 FPGA 链路对应关系

真实实验物理链路：

```text
PD signal
  -> 带通滤波器
  -> 放大器
  -> mixer
  -> 低通滤波
  -> error signal
  -> D2-125 error input
```

第一阶段 FPGA 目标链路：

```text
adc_dat[0]  // PD
  -> optional BPF / bypass
  -> mixer_core with adc_dat[1]  // external REF from IN2
  -> lowpass_filter
  -> gain/limit
  -> error_o
  -> DAC A / OUT1
```

| 实验链路部分 | FPGA 对应 | 对应文件 | 新手解释 |
|---|---|---|---|
| `PD` | `adc_dat[0]` | 未来由 `vendor_shell\red_pitaya_top_laser.sv` 接入 | Red Pitaya `IN1` 的 ADC 数据，作为 PD 信号 |
| `REF` | `adc_dat[1]` | 未来由 `vendor_shell\red_pitaya_top_laser.sv` 接入 | Red Pitaya `IN2` 的 ADC 数据，来自外部信号发生器安全幅度参考 |
| `BPF` | `bandpass_filter` 或 bypass | `bandpass_filter.sv` | 提取 4.6 MHz 附近成分，早期版本可先 bypass |
| `Amp` | `digital_gain` | `gain_offset_limit.sv` | 数字增益，调节 error 输出幅度 |
| `Mixer` | `mixer_core` | `mixer_core.sv` | `pd_i * ref_i`，数字 lock-in 的核心 |
| `LPF` | `lowpass_filter` | `lowpass_filter.sv` | 去掉乘法后的高频分量，留下低频 error 成分 |
| `Error` | `error_o` | `gain_offset_limit.sv` / `output_protect.sv` | 缩放和保护后的 14-bit signed 输出 |
| `OUT1` | DAC A 输出 | 通过 `vendor_shell` 中的 `dac_a_sum` 路径 | 后续接 DAC A，并保留官方 saturation/格式转换/ODDR |

注意：`vendor_shell\red_pitaya_top_laser.sv` 只是未来项目内的官方 top 参考副本，不代表允许修改官方 `rtl\red_pitaya_top.sv`。

## 3. 代码目录规划

计划使用以下项目内路径：

```text
redpitaya_laser_lock_project\vendor_shell\red_pitaya_top_laser.sv
redpitaya_laser_lock_project\rtl\laser_lock_core.sv
redpitaya_laser_lock_project\rtl\bandpass_filter.sv
redpitaya_laser_lock_project\rtl\mixer_core.sv
redpitaya_laser_lock_project\rtl\lowpass_filter.sv
redpitaya_laser_lock_project\rtl\gain_offset_limit.sv
redpitaya_laser_lock_project\rtl\output_protect.sv
redpitaya_laser_lock_project\sim\tb_laser_lock_core.sv
```

| 文件 | 作用 | 当前策略 |
|---|---|---|
| `vendor_shell\red_pitaya_top_laser.sv` | 官方 top 的项目内参考副本 | 后续需要时复制，官方原始 top 不改 |
| `rtl\laser_lock_core.sv` | 自定义链路顶层 wrapper | 按 v1a 到 v1g 逐版推进 |
| `rtl\bandpass_filter.sv` | 4.6 MHz 附近带通或 bypass | 早期可先 bypass，v1f 再启用 |
| `rtl\mixer_core.sv` | 数字 mixer | `pd_i * ref_i` |
| `rtl\lowpass_filter.sv` | 低通滤波 | v1d 起启用 |
| `rtl\gain_offset_limit.sv` | 增益、缩放、限幅 | 防止 `error_o` 超范围 |
| `rtl\output_protect.sv` | 输出保护 | reset、disable 或超范围时保护输出 |
| `sim\tb_laser_lock_core.sv` | 顶层 testbench | 每个版本都必须覆盖对应行为 |

说明：旧计划里的 `dc_remove.sv` 第一阶段暂时降级为可选项。当前最新链路优先验证外部 `REF`、数字 mixer、LPF 和安全输出。后续如果真实 PD 的 DC 偏置影响明显，再把 `dc_remove` 加回计划。

## 4. 第一阶段功能边界

第一阶段做：

```text
pd_i
  -> optional BPF / bypass
  -> mixer_core with ref_i
  -> lowpass_filter
  -> gain/limit
  -> error_o

control_o = 0
```

第一阶段不做：

- FPGA PID；
- sweep/ramp；
- AI；
- lock/relock FSM；
- PS/AXI 参数控制；
- FPGA 生成 `REF`；
- FPGA 驱动 EOM；
- 直接接激光器反馈。

新手必须明白：第一阶段的目标不是做完整自动锁频系统，而是先把“外部 REF + PD 输入 -> FPGA 数字 mixer/LPF -> OUT1 error signal”这条链路跑通。

## 5. laser_lock_core 端口定义（顶层 wrapper）

第一阶段 `laser_lock_core` 顶层 wrapper 建议保持以下端口：

```systemverilog
input  logic               clk_i      // <- adc_clk
input  logic               rstn_i     // <- adc_rstn（active-low）
input  logic signed [13:0] pd_i       // <- adc_dat[0]，PD 光强信号
input  logic signed [13:0] ref_i      // <- adc_dat[1]，外部 4.6 MHz REF
output logic signed [13:0] error_o    // -> DAC A 饱和前候选
output logic signed [13:0] control_o  // -> DAC B，第一阶段固定为 0
```

| 端口 | 位宽 | signed/unsigned | 来自哪里 | 去哪里 | 作用 |
|---|---:|---|---|---|---|
| `clk_i` | 1 bit | 不适用 | `adc_clk` | 自定义 MTS 链路所有寄存器 | 统一时钟 |
| `rstn_i` | 1 bit | 不适用，active-low | `adc_rstn` | 自定义 MTS 链路 reset | 低电平时回到安全输出 |
| `pd_i` | 14 bit | signed | `adc_dat[0]` | BPF/bypass 和 mixer | 来自 `IN1` 的 PD 信号 |
| `ref_i` | 14 bit | signed | `adc_dat[1]` | mixer | 来自 `IN2` 的外部 4.6 MHz REF |
| `error_o` | 14 bit | signed | gain/limit/output_protect | DAC A saturation 前候选 | 输出到 OUT1 的 error signal |
| `control_o` | 14 bit | signed | 第一阶段固定 0 | DAC B 候选 | 第一阶段不用控制输出 |

## 6. 测试驱动版本规划

第一阶段改成以下测试驱动版本。每个版本都必须小、清楚、可仿真、可上板验证。

### 6.1 `v1a_pd_passthrough`

| 项目 | 内容 |
|---|---|
| 功能 | `error_o = pd_i`，`control_o = 0` |
| 目的 | 验证 `IN1 -> OUT1` 通路 |
| testbench | reset 后输出归零；`pd_i` 正数、负数、0 都能到 `error_o`；`control_o` 恒 0 |
| 仿真成功标准 | `error_o` 正确跟随 `pd_i`，`control_o` 始终为 0 |
| 上板测试 | 信号发生器进 `IN1`，`OUT1` 接示波器观察 |
| 失败排查 | 见第 7 节通用失败排查表 |

### 6.2 `v1b_ref_passthrough`

| 项目 | 内容 |
|---|---|
| 功能 | `error_o = ref_i`，`control_o = 0` |
| 目的 | 验证 `IN2` 可以接收 4.6 MHz `REF` |
| testbench | `ref_i` 正弦/符号变化能到 `error_o`；改变 `pd_i` 不影响输出；`control_o` 恒 0 |
| 仿真成功标准 | `error_o` 正确跟随 `ref_i` |
| 上板测试 | 4.6 MHz 安全幅度 `REF` 进 `IN2`，`OUT1` 接示波器观察 |
| 特别注意 | `REF` 必须衰减到 Red Pitaya 输入安全范围内，例如 ±1 V 内 |

### 6.3 `v1c_mixer_only`

| 项目 | 内容 |
|---|---|
| 功能 | `pd_i * ref_i -> 缩放 -> error_o` |
| 目的 | 验证数字 mixer |
| testbench | 输入两路同频 4.6 MHz 等效采样正弦，检查 28-bit 乘法和缩放方向 |
| 仿真成功标准 | mixer 内部结果随两路输入正负变化；`error_o` 不溢出、不恒 0、不顶死 |
| 上板测试 | `IN1/IN2` 输入同频 4.6 MHz 正弦，`OUT1` 看乘法结果 |
| 特别注意 | 该版本还没有 LPF，`OUT1` 可能包含明显高频成分，只接示波器 |

### 6.4 `v1d_mixer_lpf`

| 项目 | 内容 |
|---|---|
| 功能 | `pd_i * ref_i -> lowpass_filter -> error_o` |
| 目的 | 得到基础数字解调输出 |
| testbench | 改变 `pd_i/ref_i` 相位或幅度，低通输出应随之变化 |
| 仿真成功标准 | lowpass 输出比 mixer 原始输出更平滑；`error_o` 对相位/幅度变化有响应 |
| 上板测试 | 改变 `IN1/IN2` 相位或幅度，`OUT1` 低频输出应变化 |
| 特别注意 | 仍然不接 `D2-125`，先确认 `OUT1` 幅度和 offset |

### 6.5 `v1e_real_pd_ref`

| 项目 | 内容 |
|---|---|
| 功能 | 真实 `PD` + 外部 `REF -> mixer + LPF -> error_o` |
| 目的 | 第一次看到真实实验 error-like signal |
| testbench | 使用仿真 PD-like 信号和 REF 信号检查链路稳定性 |
| 仿真成功标准 | `error_o` 不溢出、不顶死，对输入变化有合理响应 |
| 上板测试 | `PD` 接 `IN1`，4.6 MHz 安全幅度 `REF` 接 `IN2`，`OUT1` 接示波器 |
| 特别注意 | 真实接线前再次确认 `PD` 和 `REF` 不超过输入范围 |

### 6.6 `v1f_bpf_enable`

| 项目 | 内容 |
|---|---|
| 功能 | `PD -> BPF around 4.6 MHz -> mixer -> LPF -> error_o` |
| 目的 | 替代模拟 `1.8 MHz high-pass + 10 MHz low-pass` 链路 |
| testbench | 输入含低频、4.6 MHz、较高频成分的混合信号，检查 BPF 对 4.6 MHz 附近更敏感 |
| 仿真成功标准 | BPF/bypass 对比时，启用 BPF 后目标频率成分更突出 |
| 上板测试 | 对比 FPGA `OUT1` 和模拟 mixer 输出 |
| 特别注意 | BPF 参数必须基于真实 `f_mod` 和采样率计算，不能随便猜 |

### 6.7 `v1g_error_to_D2_125`

| 项目 | 内容 |
|---|---|
| 功能 | `OUT1 -> D2-125 error input` |
| 目的 | 用 FPGA error signal 替代模拟 mixer 输出 |
| testbench | 与 v1f 相同，但重点检查 `error_o` 幅度、offset、限幅保护 |
| 仿真成功标准 | `error_o` 在 D2-125 允许范围内，不出现长时间顶死 |
| 上板测试 | 先示波器确认 `OUT1` 幅度和 offset 安全，再接 `D2-125 error input` |
| 前提 | 示波器已经确认 `OUT1` 幅度和 offset 安全 |

特别强调：`v1g` 也不接激光器反馈，只是把 FPGA error signal 送到 `D2-125 error input`。

## 7. 每个版本必须包含的交付物

每个版本都必须包含：

| 必须项 | 说明 |
|---|---|
| testbench | 每个版本必须有对应仿真，不能只靠上板猜 |
| REPORT | 每个版本必须生成 `docs\reports\REPORT_<version>.md` |
| 仿真成功标准 | 先定义什么叫通过，再运行仿真 |
| 上板测试方法 | 写清楚信号源、Red Pitaya、示波器怎么接 |
| 失败排查表 | 失败时先查输入幅度、时钟/reset、输出是否饱和 |
| 安全说明 | 说明哪些线不能接，哪些电压不能超 |

## 8. 通用失败排查表

| 现象 | 可能原因 | 优先排查 |
|---|---|---|
| `OUT1` 完全没信号 | 未接入 DAC 路径、输出被 reset、`control_o/error_o` 未变化 | 先看仿真，再看 `rstn_i`，再看示波器量程 |
| `OUT1` 直流顶死 | 缩放太大、offset 错误、限幅触发 | 降低 gain，检查 `gain_offset_limit` |
| `OUT1` 严重削顶 | 输入幅度过大或输出超 14-bit | 降低 `IN1/IN2` 幅度，检查限幅 |
| `v1b` 看不到 4.6 MHz | `REF` 没进 `IN2`、幅度太小、示波器设置错误 | 先用示波器直接量 `IN2` 前的 REF |
| `v1c` mixer 输出异常 | signed 位宽错误、缩放错误、`ref_i` 太小或太大 | 先在 testbench 看 28-bit 乘法结果 |
| `v1d` LPF 没有效果 | LPF 系数不合适、截止频率太高或太低 | 用仿真扫不同输入频率 |
| 真实 PD/REF 后输出混乱 | PD 幅度、REF 相位、BPF/LPF 参数不合适 | 回退到 v1a/v1b/v1c 分别检查 |
| 接 D2-125 前不确定是否安全 | 没有示波器确认 | 不接 D2-125，继续示波器验证 |

## 9. 第一阶段禁止事项

第一阶段明确禁止：

- 第一阶段不做 PID；
- 第一阶段不做 sweep；
- 第一阶段不做 AI；
- 第一阶段不让 FPGA 生成 `REF`；
- 第一阶段不让 FPGA 驱动 EOM；
- 任何版本不能接激光器反馈；
- 任何版本不能直接接 `D2-125`，除非前一版已用示波器确认 `OUT1` 安全；
- 不直接修改官方 `rtl\red_pitaya_top.sv`；
- 不直接修改官方 ODDR/PLL/PS/XDC；
- 不把原模拟 mixer 的 6.32 Vpp 参考信号直接接入 `IN2`。

## 10. 风险和保护

| 风险 | 保护措施 |
|---|---|
| `REF` 输入过大 | 必须衰减到 Red Pitaya 输入安全范围内，例如 ±1 V 内 |
| EOM 驱动被误接到 Red Pitaya | 明确区分 EOM 驱动 8.93 Vpp 和 Red Pitaya `IN2` 安全 REF |
| `OUT1` 输出异常 | 所有版本先接示波器，不直接接 `D2-125` |
| `control_o` 误输出 | 第一阶段固定 `control_o = 0` |
| 误接激光器反馈 | 第一阶段禁止接激光器反馈 |
| 官方工程被污染 | 官方 `rtl\red_pitaya_top.sv` 保持不修改 |
| 底层 IO 被破坏 | 不直接修改官方 ODDR/PLL/PS/XDC |

核心原则：

```text
先仿真
再示波器
再 D2-125 error input
不接激光器反馈
```

## 11. 需要用户补充的实验参数

后续正式写滤波器和缩放逻辑前，需要确认：

| 参数 | 当前已知/待确认 | 为什么需要 |
|---|---|---|
| MTS 调制频率 `f_mod` | 已知约 `4.6 MHz` | 决定 BPF 中心频率 |
| EOM 驱动幅度 | 已知约 `8.93 Vpp` | 只作实验背景，不能直接进 Red Pitaya |
| `REF` 输入 Red Pitaya 幅度 | 待确认，必须安全衰减 | 判断 `IN2` 是否安全 |
| 原模拟 mixer 参考幅度 | 已知约 `6.32 Vpp` | 明确不能直接进 `IN2` |
| `REF` 是正弦还是方波 | 待确认 | 影响 mixer 和输入处理 |
| `PD` 输入 Red Pitaya 幅度 | 待确认 | 判断 `IN1` 是否安全 |
| 模拟链路高通/低通 | 已知目标替代 `1.8 MHz high-pass + 10 MHz low-pass` | 帮助设计 v1f BPF |
| 模拟 mixer 输出 error 典型 `Vpp` | 待确认 | 设定 `OUT1` 目标幅度 |
| `D2-125 error input` 允许电压范围 | 待确认 | 决定 v1g 是否安全 |
| LPF 截止频率 `fc` | 待确认 | 决定 v1d 解调输出速度 |

## 12. 下一步建议

下一步建议先审查本计划。

如果用户确认，就按测试驱动顺序进入：

```text
v1a_pd_passthrough
```

写代码前还需要明确：

1. 是否保留当前已有 `laser_lock_core.sv` 的时序 passthrough 风格；
2. 是否为每个版本单独保留一个 git diff 或文档 diff；
3. `v1b_ref_passthrough` 上板时 `REF` 计划衰减到多少 `Vpp`；
4. `OUT1` 示波器确认安全的判据，比如最大 `Vpp` 和 offset 限制。
