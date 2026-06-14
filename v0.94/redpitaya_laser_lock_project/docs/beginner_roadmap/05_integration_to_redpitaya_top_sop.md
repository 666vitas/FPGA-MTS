# 接入 Red Pitaya top SOP

## 0. 本文件作用

本文件说明后续如何把自定义 `laser_lock_core` 接入 Red Pitaya 官方 top。

注意：当前不要修改官方 `red_pitaya_top.sv`，本文件只是 SOP。

## 1. 我需要理解什么

官方 `red_pitaya_top.sv` 像总接线板。

我们的自定义算法应该在：

```text
redpitaya_laser_lock_project\rtl
```

不是直接散写进官方 top。

未来接线大概是：

```text
adc_clk      -> clk_i
adc_rstn     -> rstn_i
adc_dat[0]   -> pd_i
adc_dat[1]   -> ref_i
error_o      -> DAC A / OUT1 候选路径
control_o    -> DAC B 候选路径
```

## 2. 我需要操作什么

真正集成前必须按顺序：

1. 生成 `INTEGRATION_PLAN_<version>.md`。
2. GPT 审查 integration plan。
3. 用户明确批准。
4. 再生成 patch 或修改说明。
5. 再进入 Vivado。

## 3. 我需要发给 GPT 什么

发给 GPT：

```text
1. 当前版本 RTL
2. testbench 仿真结果
3. integration plan
4. 计划接入的官方信号
5. 计划驱动的官方信号
6. 回退方案
```

## 4. Codex 应该生成什么

Codex 应生成：

```text
docs\integration\INTEGRATION_PLAN_v1ab_passthrough_debug.md
```

内容必须包括：

- 读取哪些官方信号；
- 驱动哪些官方信号；
- mux 放在哪里；
- 如何保留官方路径；
- 如何回退；
- 如何上板验证。

## 5. 成功标准是什么

integration plan 通过的标准：

- 不直接改 PLL；
- 不直接改 ODDR；
- 不直接改 PS/AXI/DDR；
- 不直接改 XDC/SDC；
- 保留官方 saturation；
- 保留官方 signed-to-unsigned / DAC 格式转换；
- 有 `USE_LASER_LOCK_CORE` 类回退开关；
- GPT 审查通过。

## 6. 失败怎么排查

| 问题 | 处理 |
|---|---|
| 不知道接哪里 | 回看 `L02_adc_path.md` 和 `L03_dac_path.md` |
| 可能破坏官方路径 | 增加 mux 和回退开关 |
| 不确定 `IN1/IN2` 对应关系 | 用 v1a/v1b 上板实测 |
| 不确定 OUT1/OUT2 | 用示波器双通道确认 |

## 7. 不要碰/不要改

未经用户明确批准，不改：

```text
rtl\red_pitaya_top.sv
Vivado 工程
PLL
ODDR
PS/AXI/DDR
XDC/SDC
```

## 8. 我现在只需要记住什么

集成不是写 RTL。

```text
集成前必须先写接线说明。
```
