# 项目总规划书

## 0. 本文件作用

本文件定义 Red Pitaya + MTS FPGA 激光稳频项目的阶段路线。

它用于防止项目一次跳太远，保证每一步都能学习、记录、仿真、审查和回退。

## 1. 阅读对象 / 管理对象

阅读对象：

- FPGA/Verilog 新手用户；
- GPT；
- Codex。

管理对象：

```text
redpitaya_laser_lock_project
```

官方工程只作为阅读对象，不作为当前直接修改对象。

## 2. 当前原则

| 原则 | 说明 |
|---|---|
| 一次只做一个阶段 | 不跨阶段实现功能 |
| 先文档，后代码 | 没有学习报告和接口计划，不写 RTL |
| 先独立仿真，后官方集成 | `laser_lock_core` 先在自定义目录仿真 |
| 先 integration plan，后改官方 top | 不直接修改 `red_pitaya_top.sv` |
| 每阶段有输入、输出、成功标准 | 方便新手检查是否完成 |

## 3. 阶段总表

| 阶段 | 名称 | 输入 | 输出 | 成功标准 |
|---|---|---|---|---|
| 阶段 0 | 学习官方 top | `rtl/red_pitaya_top.sv` | `learning\L01_top_overview.md` 和 `REPORT_stage0_top_learning.md` | 能说清 top 主要模块和信号分区 |
| 阶段 1 | ADC/DAC/clock/reset 接口总结 | 官方 top 只读分析 | `learning\L02_adc_path.md`、`learning\L03_dac_path.md`、clock/reset 报告 | 能说明未来 custom core 该接哪个 clock/reset 和候选 ADC/DAC 点 |
| 阶段 2 | 设计 `laser_lock_core` 接口 | 阶段 1 结果 | 接口计划文档 | 明确端口，不接官方 top，不写散乱算法 |
| 阶段 3 | 实现自定义 core 的 v1 仿真版 | 接口计划 | 自定义 RTL、testbench、仿真报告 | 仿真通过，文件只在 `redpitaya_laser_lock_project` 下 |
| 阶段 4 | 生成官方 top 集成方案 | v1 仿真结果 | `integration\INTEGRATION_PLAN_*.md` 或 patch 说明 | 能说明接线点、mux、回退方式，不直接修改官方 top |
| 阶段 5 | GPT 审查后进入 Vivado 集成 | integration plan | 审查意见、允许后再集成 | GPT/用户确认后才进入 Vivado |
| 后续 | mixer、LPF、BPF、gain/offset、D2-125、PID、AI | 前一阶段结果 | 分阶段报告和代码 | 每阶段可仿真、可回退、可上板验证 |

## 4. 阶段 0：学习官方 top

输入：

```text
rtl\red_pitaya_top.sv
```

输出：

```text
learning\L01_top_overview.md
reports\REPORT_stage0_top_learning.md
```

成功标准：

- 能说明 `red_pitaya_top.sv` 的主要端口分组；
- 能区分 ADC、DAC、clock/reset、PS/system bus、scope/ASG/PID；
- 能说明哪些区域绝对不应修改。

禁止：

- 不写 Verilog；
- 不修改官方 top；
- 不修改 Vivado 工程。

## 5. 阶段 1：ADC/DAC/clock/reset 接口总结

输入：

```text
rtl\red_pitaya_top.sv
```

输出：

```text
learning\L02_adc_path.md
learning\L03_dac_path.md
learning\L04_clock_reset.md
reports\REPORT_stage1_adc_dac_clock_reset.md
```

成功标准：

- 能说明 `adc_dat[0]`、`adc_dat[1]` 的候选含义；
- 能说明 DAC A/B 的候选输出路径；
- 能说明未来 custom core 候选使用的 clock/reset；
- 能列出不确定项和需要上板确认项。

## 6. 阶段 2：设计 `laser_lock_core` 接口，不接官方 top

输入：

```text
learning\L02_adc_path.md
learning\L03_dac_path.md
learning\L04_clock_reset.md
```

候选接口：

```text
clk_i
rstn_i
pd_i
ref_i
error_o
control_o
```

输出：

```text
integration 或 learning 中的接口计划文档
reports\REPORT_stage2_laser_lock_core_interface.md
```

成功标准：

- 端口含义清楚；
- 位宽、signed/unsigned 计划清楚；
- 不接官方 top；
- 不生成官方目录内文件。

## 7. 阶段 3：实现自定义 core 的 v1 仿真版

输入：

```text
阶段 2 接口计划
```

输出：

```text
redpitaya_laser_lock_project\rtl
redpitaya_laser_lock_project\sim
reports\REPORT_stage3_v1_simulation_core.md
```

成功标准：

- 自定义 RTL 只放在 `redpitaya_laser_lock_project\rtl`；
- testbench 只放在 `redpitaya_laser_lock_project\sim`；
- 仿真行为清楚；
- 给出完整 diff；
- 不修改官方工程。

## 8. 阶段 4：生成官方 top 集成方案，但不直接修改

输入：

```text
阶段 3 仿真结果
```

输出：

```text
integration\INTEGRATION_PLAN_v1_*.md
```

可选输出：

```text
integration\*.patch
```

成功标准：

- 说明从哪里读 `adc_dat[0]`、`adc_dat[1]`；
- 说明 mux 放在哪里；
- 说明如何保留官方 `dac_a_sum`、`dac_b_sum` 路径；
- 说明如何回退；
- 不直接修改 `red_pitaya_top.sv`。

## 9. 阶段 5：GPT 审查后再进入 Vivado 集成

输入：

```text
integration\INTEGRATION_PLAN_*.md
```

输出：

```text
reports\REPORT_stage5_gpt_review.md
```

成功标准：

- GPT/用户确认集成方案合理；
- 明确允许后，才考虑修改官方工程；
- 修改前有回退方案；
- 修改后能运行 `Run Synthesis`、`Run Implementation`、`Generate Bitstream`。

## 10. 后续阶段

| 阶段 | 内容 | 说明 |
|---|---|---|
| v2 | mixer | 只验证乘法混频 |
| v3 | LPF | 在 mixer 后加入低通 |
| v4 | BPF | 在 PD 侧加入带通 |
| v5 | gain/offset/limit | 调整 error signal 幅度、偏置和保护 |
| v6 | D2-125 | 用 OUT1 输出给 D2-125 error input |
| v7 | PID | FPGA 内部 PID，先示波器或假负载验证 |
| v8 | scan/lock/relock | 扫描、锁定、失锁检测、重扫 |
| v9 | AI | AI 放 PC/PS 侧，PL 不早期实现 AI |

## 11. 已确认

- 当前先学习和规划，不急着写 RTL。
- `laser_lock_core` 不应直接放进官方 `rtl`。
- 官方 top 集成必须先写 integration plan。
- sweep、PID、AI 都是后续阶段。

## 12. 不确定，需要人工确认

| 问题 | 说明 |
|---|---|
| 阶段 3 的 v1 功能是否确定为 passthrough | 需要用户在进入代码阶段前确认 |
| 集成 patch 放 `integration` 还是单独 `patches` | 需要用户确认 |
| 何时允许实际修改官方 Vivado 工程 | 必须由用户明确批准 |

## 13. 下一步建议

下一步不要写 RTL。

建议从：

```text
docs\current\02_TOP_LEARNING_OUTLINE.md
```

开始，生成：

```text
learning\L01_top_overview.md
```

## 14. 给 GPT 审查的问题

1. 阶段划分是否足够细，适合 FPGA/Verilog 新手？
2. 阶段 2 是否应先单独写 `INTERFACE_laser_lock_core.md`？
3. 阶段 4 是否只允许生成 Markdown，不生成 patch？
