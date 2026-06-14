# 实验驱动实施方案

## 0. 本文件作用

本文件不是继续学习 `red_pitaya_top.sv`，也不是继续泛读官方工程。

本文件的作用是：把 `L01_top_overview`、`L02_adc_path`、`L03_dac_path`、`L04_clock_reset` 已经学到的结论，转换成后续可以一步一步实现、仿真、集成、上板验证的实验路线。

大白话说：前面几篇文档是在认识 Red Pitaya FPGA 里面的“道路”和“插座”，本文件开始把这些知识变成“怎么接线、先做哪一步、哪些地方不能碰”的施工方案。

## 1. 我的真实实验链路

当前 MTS 激光稳频实验的模拟信号链路可以简化为：

```text
PD signal
  -> BPF
  -> Amp
  -> Mixer
  -> LPF
  -> error signal
  -> D2-125
```

其中 `REF signal` 来自信号发生器的同源参考信号。

也就是说：

- `PD signal` 是光电探测器输出的信号；
- `BPF` 用来选出需要的调制频率附近信号；
- `Amp` 用来放大信号；
- `Mixer` 用 `REF signal` 做相敏解调；
- `LPF` 滤掉高频乘积，留下慢变化的误差信号；
- `error signal` 送给 `D2-125`；
- `D2-125` 再完成后面的模拟伺服和激光反馈。

## 2. FPGA 第一阶段要替代什么

FPGA 第一阶段只准备替代模拟链路中的这一段：

```text
BPF + Amp + Mixer + LPF + error signal 输出
```

对应未来的 Red Pitaya 实验链路是：

```text
PD signal -> Red Pitaya IN1 -> FPGA -> Red Pitaya OUT1 -> error signal
REF signal -> Red Pitaya IN2 -> FPGA
```

第一阶段不替代：

| 不替代对象 | 原因 |
|---|---|
| EOM 驱动 | EOM 仍由外部信号发生器驱动 |
| sweep/ramp | 当前先验证解调和输出，不做扫描 |
| D2-125 PID | 当前仍保留 `D2-125` 做伺服 |
| AI | AI 后置，先不进入 FPGA PL |
| 激光器反馈执行器 | 当前只看 `OUT1` 的 error signal，不直接控制激光器 |

新手必须明白：现在不是一次性把整套激光锁定系统搬进 FPGA，而是先让 FPGA 做出一个可以在示波器上看到的 `error signal`。

## 3. L01-L04 已经得到的实现接口结论

| 项目 | 结论 | 来源章节 |
|---|---|---|
| PD 输入候选 | `adc_dat[0] -> pd_i` | L02 |
| REF 输入候选 | `adc_dat[1] -> ref_i` | L02 |
| 主时钟 | `adc_clk -> clk_i` | L04 |
| 复位 | `adc_rstn -> rstn_i` | L04 |
| error 输出候选 | `error_o -> DAC A saturation 前` | L03 |
| control 输出候选 | `control_o -> DAC B saturation 前` | L03 |

补充结论：

| 来源章节 | 结论 | 对实现的意义 |
|---|---|---|
| L01 | `red_pitaya_top.sv` 像 Red Pitaya FPGA 的总接线板 | 算法不要散写在 top 里，后续应放入独立 `laser_lock_core` |
| L02 | `adc_dat` 属于 `adc_clk` 时钟域 | 自定义 core 第一版也应放在 `adc_clk` 域 |
| L03 | DAC 后级已有 saturation、格式转换、ODDR | 后续接入时应复用官方 DAC 后级，不直接改 `dac_dat_o` |
| L04 | `adc_rstn` 由 `frstn[0]` 和 `pll_locked` 共同决定 | 自定义 core 第一版应使用 `adc_rstn`，避免自己造 reset |

## 4. 第一版 laser_lock_core 最小接口

未来第一版 `laser_lock_core` 建议只定义最小接口：

```text
clk_i
rstn_i
pd_i
ref_i
error_o
control_o
```

注意：本节只是接口合同，不是在写 Verilog。

| 端口 | 位宽 | signed/unsigned | 来自哪里 | 去哪里 | 和实验链路的关系 |
|---|---:|---|---|---|---|
| `clk_i` | 1 bit | 不适用 | `adc_clk` | `laser_lock_core` 内部所有时序逻辑 | 让 core 跟 ADC 数据使用同一个节拍 |
| `rstn_i` | 1 bit | 不适用，低有效 reset | `adc_rstn` | `laser_lock_core` 内部 reset | PLL 锁定并释放 reset 后，core 才开始工作 |
| `pd_i` | 14 bit | signed | `adc_dat[0]` | 未来 BPF/mixer 输入 | 代表 Red Pitaya IN1 采到的 `PD signal` |
| `ref_i` | 14 bit | signed | `adc_dat[1]` | 未来 mixer reference 输入 | 代表 Red Pitaya IN2 采到的同源 `REF signal` |
| `error_o` | 14 bit | signed | `laser_lock_core` 处理结果 | 未来接到 DAC A saturation 前 | 对应实验中的 `error signal`，从 OUT1 输出 |
| `control_o` | 14 bit | signed | 早期可固定为 `14'sd0`，后期可来自 PID | 未来接到 DAC B saturation 前 | 预留给后续 `OUT2` 控制输出 |

大白话解释：

- `clk_i` 是 core 的节拍器；
- `rstn_i` 是让 core 回到初始状态的开关；
- `pd_i` 是实验里的 PD 输入；
- `ref_i` 是 mixer 要用的参考输入；
- `error_o` 是当前最重要的输出，未来接 OUT1；
- `control_o` 先不用，但接口先留着，避免后面大改结构。

新手现在只需要记住：第一版 core 不需要复杂，先把输入、时钟、复位、输出关系定清楚。

## 5. 实现阶段重新规划

### 阶段 A：项目目录内实现 core，不接官方 top

所有文件放在：

```text
redpitaya_laser_lock_project
```

不放进官方 `rtl`。

| 子阶段 | 名称 | 目标 | 成功标准 |
|---|---|---|---|
| A1 | `v1_pd_passthrough` | `pd_i -> error_o` | 仿真中 `error_o` 跟随 `pd_i` |
| A2 | `v2_mixer_only` | `pd_i * ref_i -> error_o` | 仿真中能看到乘法混频结果 |
| A3 | `v3_mixer_lpf` | mixer 后加入 LPF | 仿真中输出变成低频解调结果 |
| A4 | `v4_bpf_mixer_lpf` | PD 先过 BPF，再 mixer，再 LPF | 形成第一版完整数字解调链 |
| A5 | `v5_gain_offset_limit` | 加 gain、offset、limiter | 输出幅度和偏置可控，不容易顶死 |

这一阶段只验证自定义 core 本身，不修改 `red_pitaya_top.sv`。

### 阶段 B：生成官方 top 集成方案，不直接修改

| 子阶段 | 名称 | 目标 |
|---|---|---|
| B1 | `INTEGRATION_PLAN_v1` | 写清楚 future `laser_lock_core` 如何接入官方 top |
| B2 | mux 接入方案 | 设计 `USE_LASER_LOCK_CORE` 之类的切换方案 |
| B3 | 保留官方后级 | 保留官方 saturation、格式转换、ODDR |
| B4 | GPT 审查 | 先让 GPT 审查集成方案，再动官方工程 |

大白话说：阶段 B 只写“怎么接”的说明书，不真正动线。

### 阶段 C：经用户批准后才接入 Vivado 官方工程

| 子阶段 | 名称 | 目标 |
|---|---|---|
| C1 | 修改 top 或生成 patch | 在用户明确批准后，才改 `red_pitaya_top.sv` 或生成 patch |
| C2 | Vivado synthesis | 运行 `Run Synthesis` |
| C3 | implementation | 运行 `Run Implementation` |
| C4 | bitstream/bin | 运行 `Generate Bitstream`，需要时生成 `.bit.bin` |
| C5 | 信号发生器 + 示波器验证 | 用简单输入信号验证 IN1 到 OUT1 的通路 |

这一阶段才开始真正靠近上板。

### 阶段 D：接真实 PD/REF

| 子阶段 | 接法 | 目标 |
|---|---|---|
| D1 | `PD -> IN1` | 把真实 PD 信号接入 Red Pitaya |
| D2 | `REF -> IN2` | 把同源参考接入 Red Pitaya |
| D3 | `OUT1 看 error` | 用示波器观察 FPGA 输出的 error signal |
| D4 | 对比模拟 mixer output | 比较 FPGA 输出和原模拟 mixer/LPF 输出是否一致 |

注意：这一阶段仍然不直接控制激光器反馈。

### 阶段 E：再考虑 D2-125、PID、sweep、AI

后续再逐步考虑：

- `OUT1 -> D2-125 error input`；
- FPGA 内部 PID；
- sweep/ramp；
- lock/relock FSM；
- AI peak recognition。

这些都不是当前第一步。

## 6. 当前不应该做什么

当前明确不应该做：

| 不做的事 | 原因 |
|---|---|
| 不直接修改官方 `red_pitaya_top.sv` | 还没有完成接口合同和集成方案 |
| 不在官方 `rtl` 里写 `laser_lock_core` | 自定义项目必须放在 `redpitaya_laser_lock_project` |
| 不碰 PS/AXI/DDR/PLL/ODDR/XDC | 这些是官方底层和板级接口，新手阶段风险很高 |
| 不直接接激光器反馈 | 第一阶段只看示波器，不闭环控制激光器 |
| 不一口气实现完整 MTS | 先从最小可验证版本开始 |
| 不继续无目的阅读官方工程 | L01-L04 已足够支持下一步接口合同和 v1 仿真设计 |

## 7. 下一步必须做什么

推荐顺序如下：

1. 先生成：

```text
docs\integration\INTERFACE_CONTRACT_laser_lock_core.md
```

这个文件只定义 `laser_lock_core` 的接口、位宽、signed 规则、reset 规则、仿真输入输出预期，以及未来 top 接线边界。

2. 再生成：

```text
redpitaya_laser_lock_project\rtl\laser_lock_core.sv
```

对应 `v1_pd_passthrough` 的仿真版。

3. 同时生成：

```text
redpitaya_laser_lock_project\sim\tb_laser_lock_core.sv
```

用于在不接官方 top 的情况下先验证 `pd_i -> error_o`。

推荐先写 `INTERFACE_CONTRACT_laser_lock_core.md`，再写 RTL。

原因是：用户是 FPGA/Verilog 新手，先把“接口合同”写清楚，可以减少后续写错位宽、reset、signed 方向、接线位置的风险。

## 8. 给 GPT 审查的问题

1. 是否可以停止泛读 top，转入实现导向？
2. L05 是否只做最小 scope/ASG/PID 干扰检查？
3. 是否应先写 `INTERFACE_CONTRACT_laser_lock_core.md` 再写 RTL？
4. v1 是否只做 `pd_i -> error_o`？
