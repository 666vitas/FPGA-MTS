# REPORT: L04_clock_reset

## 0. 本文件作用

本文件记录 L04_clock_reset 的执行结果。

本次任务只阅读官方文件：

```text
rtl\red_pitaya_top.sv
```

并生成 clock/reset 路径学习文档。

## 1. 本次任务是什么

任务目标：

- 说明 `adc_clk_i` 是什么；
- 说明 `adc_clk_i` 如何经过 `IBUFDS` 变成 `adc_clk_in`；
- 说明 `red_pitaya_pll` 如何生成 `pll_adc_clk`、`pll_dac_clk_1x`、`pll_dac_clk_2x`、`pll_dac_clk_2p`；
- 说明 `pll_adc_clk` 如何经过 `BUFG` 变成 `adc_clk`；
- 说明 `dac_clk_1x`、`dac_clk_2x`、`dac_clk_2p` 大概用于什么；
- 说明 `adc_rstn` 如何由 `frstn[0]` 和 `pll_locked` 生成；
- 说明 `dac_rst` 如何生成；
- 说明 `pll_locked` 的作用；
- 说明 `frstn` 来自哪里；
- 说明为什么 future `laser_lock_core` 第一版应该优先使用 `adc_clk` 和 `adc_rstn`；
- 说明为什么新手阶段不要跨时钟域；
- 说明为什么不能乱改 PLL、BUFG、reset 生成逻辑；
- 说明 clock/reset 和 L02 ADC、L03 DAC 的关系。

## 2. 阅读对象

本次只读：

```text
rtl\red_pitaya_top.sv
```

没有修改官方文件。

## 3. 生成了哪些文件

本次新增：

```text
docs\learning\L04_clock_reset.md
docs\reports\REPORT_L04_clock_reset.md
```

## 4. 学习结果摘要

clock 主路径可以概括为：

```text
adc_clk_i
  -> IBUFDS i_clk
  -> adc_clk_in
  -> red_pitaya_pll
  -> pll_adc_clk / pll_dac_clk_1x / pll_dac_clk_2x / pll_dac_clk_2p
  -> BUFG
  -> adc_clk / dac_clk_1x / dac_clk_2x / dac_clk_2p
```

reset 主路径可以概括为：

```text
frstn[0] + pll_locked
  -> adc_rstn  // active low, adc_clk 域
  -> dac_rst   // active high, dac_clk_1x 域
```

关键结论：

| 结论 | 说明 |
|---|---|
| `adc_clk_i` | 外部 ADC 差分 clock 输入 |
| `IBUFDS` | 把差分 clock 转成内部 `adc_clk_in` |
| `red_pitaya_pll` | 用 `adc_clk_in` 生成 ADC/DAC 等时钟 |
| `BUFG` | 把 PLL 输出送上 FPGA 全局时钟网络 |
| `pll_locked` | 表示 PLL 是否稳定 |
| `frstn` | 来自 PS 的 fabric reset 组 |
| `adc_rstn` | `frstn[0] & pll_locked`，active low |
| `dac_rst` | `~frstn[0] | ~pll_locked`，active high |
| future `laser_lock_core` | 第一版应优先使用 `adc_clk` / `adc_rstn` |

## 5. 证据摘要

| 证据 | 位置 |
|---|---|
| `adc_clk_i` 端口 | `rtl\red_pitaya_top.sv` 第 96 行 |
| `fclk` / `frstn` 声明 | 第 131-132 行 |
| PLL 信号声明 | 第 155-163 行 |
| `adc_clk` / `adc_rstn` 声明 | 第 170-172 行 |
| `dac_clk_1x/2x/2p` / `dac_rst` 声明 | 第 188-192 行 |
| system bus 使用 `adc_clk` / `adc_rstn` | 第 208-209 行 |
| `IBUFDS i_clk` | 第 218-219 行 |
| `red_pitaya_pll pll` | 第 221-234 行 |
| `BUFG` 分发 clock | 第 236-241 行 |
| `pll_locked` 相关计数 | 第 243-249 行 |
| `adc_rstn` 生成 | 第 256-258 行 |
| `dac_rst` 生成 | 第 260-262 行 |
| `frstn` 来自 PS | 第 275-300 行 |
| ADC 数据在 `adc_clk` 域更新 | 第 400-403 行 |
| DAC 数据在 `dac_clk_1x` 域寄存 | 第 418-423 行 |
| DAC ODDR 使用 DAC clocks | 第 425-430 行 |
| scope 使用 `adc_clk` / `adc_rstn` | 第 517-522 行 |
| ASG 使用 `adc_clk` / `adc_rstn` | 第 554-559 行 |
| PID 使用 `adc_clk` / `adc_rstn` | 第 577-584 行 |

## 6. 没有做什么

本次没有修改官方工程。

未修改：

```text
rtl
project
sim
ip
sdc
red_pitaya_top.sv
red_pitaya_pll
```

本次没有生成 RTL。

本次没有实现：

```text
laser_lock_core
```

本次没有修改：

```text
PLL
BUFG
adc_clk
dac_clk_1x
dac_clk_2x
dac_clk_2p
adc_rstn
dac_rst
```

本次没有开始：

```text
L05_scope_asg_pid
```

## 7. 已确认

- `adc_clk_i` 是 top 的 ADC clock 差分输入。
- `IBUFDS i_clk` 把 `adc_clk_i[1]` / `adc_clk_i[0]` 转成 `adc_clk_in`。
- `red_pitaya_pll` 的输入 clock 是 `adc_clk_in`。
- `red_pitaya_pll` 的 reset 输入是 `frstn[0]`。
- `red_pitaya_pll` 输出 `pll_adc_clk`、`pll_dac_clk_1x`、`pll_dac_clk_2x`、`pll_dac_clk_2p`。
- `pll_adc_clk` 经 `BUFG` 变成 `adc_clk`。
- `pll_dac_clk_1x/2x/2p` 分别经 `BUFG` 变成 `dac_clk_1x/2x/2p`。
- `pll_locked` 用于判断 PLL 是否稳定。
- `frstn` 来自 `red_pitaya_ps` 的 `.fclk_rstn_o(frstn)`。
- `adc_rstn` 在 `adc_clk` 域由 `frstn[0] & pll_locked` 生成。
- `dac_rst` 在 `dac_clk_1x` 域由 `~frstn[0] | ~pll_locked` 生成。
- `adc_dat` 在 `adc_clk` 域更新。
- 官方 scope、ASG、PID 使用 `adc_clk` / `adc_rstn`。
- future `laser_lock_core` 第一版使用 `adc_clk` / `adc_rstn` 是最合理的候选方案。

## 8. 不确定，需要人工确认

| 不确定项 | 说明 |
|---|---|
| `adc_clk_i` 实际频率 | 需要官方硬件资料确认 |
| `pll_dac_clk_2p` 的 -45DGR 相位原因 | 需要 DAC 芯片时序或官方设计说明确认 |
| `frstn[0]` 的 PS 内部释放细节 | 需要后续 L06 或 PS/block design 学习 |
| future `laser_lock_core` 输出接入 DAC 是否需要额外 CDC | 需要后续 L07/integration plan 审查 |
| 参数控制是否全部在 `adc_clk` 域 | 需要后续 system bus 学习 |

## 9. 下一步建议

下一步建议是 L05：

```text
learning\L05_scope_asg_pid.md
reports\REPORT_L05_scope_asg_pid.md
```

但本次任务到 L04 为止。

不要自动继续 L05，不要写 Verilog，不要修改官方工程。

## 10. 给 GPT 审查的问题

1. L04 是否已经足够说明 `adc_clk_i -> IBUFDS -> PLL -> BUFG -> adc_clk`？
2. 是否同意 future `laser_lock_core` 第一版使用 `adc_clk` / `adc_rstn`？
3. 是否同意新手阶段避免跨时钟域？
4. 是否需要在后续集成方案里强制写明不修改 PLL/BUFG/reset？
5. 是否需要在 L05 前先补一份 clock/reset 术语表？
