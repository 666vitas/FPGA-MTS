# REPORT: L03_dac_path

## 0. 本文件作用

本文件记录 L03_dac_path 的执行结果。

本次任务只阅读官方文件：

```text
rtl\red_pitaya_top.sv
```

并生成 DAC 输出路径学习文档。

## 1. 本次任务是什么

任务目标：

- 追踪 `asg_dat` 是什么；
- 追踪 `pid_dat` 是什么；
- 说明 `dac_a_sum`、`dac_b_sum` 如何得到；
- 说明 `dac_a`、`dac_b` 如何由 `dac_a_sum`、`dac_b_sum` 得到；
- 说明 saturation 如何工作；
- 说明 `dac_dat_a`、`dac_dat_b` 如何由 `dac_a`、`dac_b` 得到；
- 说明 signed-to-unsigned / negative-slope conversion 的含义；
- 说明 `ODDR oddr_dac_*` 在 DAC 输出中的作用；
- 说明为什么 `dac_dat_o`、`dac_wrt_o`、`dac_sel_o`、`dac_clk_o`、`dac_rst_o` 不能乱改；
- 说明 future `laser_lock_core.error_o` 未来可能接入 DAC A / OUT1 路径的位置；
- 说明 future `laser_lock_core.control_o` 未来可能接入 DAC B / OUT2 路径的位置；
- 列出还需要板级资料或实验确认的事项。

## 2. 阅读对象

本次只读：

```text
rtl\red_pitaya_top.sv
```

没有修改官方文件。

## 3. 生成了哪些文件

本次新增：

```text
docs\learning\L03_dac_path.md
docs\reports\REPORT_L03_dac_path.md
```

## 4. 学习结果摘要

官方 DAC 输出路径可以概括为：

```text
red_pitaya_asg
  -> asg_dat[0] / asg_dat[1]

red_pitaya_pid
  -> pid_dat[0] / pid_dat[1]

asg_dat + pid_dat
  -> dac_a_sum / dac_b_sum
  -> saturation
  -> dac_a / dac_b
  -> signed-to-unsigned / negative-slope conversion
  -> dac_dat_a / dac_dat_b
  -> ODDR oddr_dac_*
  -> dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
```

关键结论：

| 结论 | 说明 |
|---|---|
| `asg_dat` | 官方 ASG 输出，signed 14 bit，两路 |
| `pid_dat` | 官方 PID 输出，signed 14 bit，两路 |
| `dac_a_sum` | `asg_dat[0] + pid_dat[0]`，signed 15 bit |
| `dac_b_sum` | `asg_dat[1] + pid_dat[1]`，signed 15 bit |
| `dac_a` / `dac_b` | saturation 后的 14 bit DAC 内部数据 |
| `dac_dat_a` / `dac_dat_b` | 经过 DAC 格式转换后的输出数据 |
| `ODDR oddr_dac_*` | 最终驱动外部 DAC 物理引脚的 DDR 输出单元 |
| future `error_o` | 候选接入 DAC A saturation 前路径 |
| future `control_o` | 候选接入 DAC B saturation 前路径 |

## 5. 证据摘要

| 证据 | 位置 |
|---|---|
| DAC 顶层输出端口 | `rtl\red_pitaya_top.sv` 第 99-104 行 |
| `SBA_T` / `SBG_T` 为 signed 14 bit | 第 183-184 行 |
| DAC 内部信号声明 | 第 188-196 行 |
| `asg_dat` 声明 | 第 198-199 行 |
| `pid_dat` 声明 | 第 201-202 行 |
| DAC 相关 PLL/BUFG clock | 第 226-239 行 |
| DAC IO 区域 | 第 406-430 行 |
| `dac_a_sum` / `dac_b_sum` 求和 | 第 410-412 行 |
| saturation | 第 414-416 行 |
| signed-to-unsigned / negative-slope conversion | 第 418-423 行 |
| `ODDR oddr_dac_*` 输出 | 第 425-430 行 |
| ASG 输出到 `asg_dat` | 第 554-559 行 |
| PID 输出到 `pid_dat` | 第 577-584 行 |

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
```

本次没有生成 RTL。

本次没有实现：

```text
laser_lock_core
```

本次没有修改：

```text
dac_dat_o
dac_wrt_o
dac_sel_o
dac_clk_o
dac_rst_o
ODDR oddr_dac_*
```

本次没有开始：

```text
L04_clock_reset
```

## 7. 已确认

- `asg_dat[0]` 和 `asg_dat[1]` 来自官方 `red_pitaya_asg`。
- `pid_dat[0]` 和 `pid_dat[1]` 来自官方 `red_pitaya_pid`。
- `asg_dat` 和 `pid_dat` 都是 signed 14 bit。
- 官方 DAC A 当前由 `asg_dat[0] + pid_dat[0]` 得到。
- 官方 DAC B 当前由 `asg_dat[1] + pid_dat[1]` 得到。
- `dac_a_sum` 和 `dac_b_sum` 是 signed 15 bit。
- 官方 saturation 会把 15 bit 求和结果限制为 14 bit。
- `dac_dat_a` 和 `dac_dat_b` 由 `dac_a` 和 `dac_b` 经过格式转换得到。
- `ODDR oddr_dac_*` 是最终输出到外部 DAC 芯片的时序接口。
- future `laser_lock_core.error_o` 不应直接驱动 `dac_dat_o`。
- future `laser_lock_core.control_o` 不应直接驱动 `dac_dat_o`。

## 8. 不确定，需要人工确认

| 不确定项 | 说明 |
|---|---|
| DAC A 是否物理对应 OUT1 | 需要板级资料或实验确认 |
| DAC B 是否物理对应 OUT2 | 需要板级资料或实验确认 |
| 输出极性是否在示波器上表现为反相 | top 有 negative-slope conversion，实际极性需实验确认 |
| DAC 电压范围和码值比例 | 需要 Red Pitaya STEMlab 125-14 硬件资料确认 |
| future mux 的精确接线方式 | 需要后续 `INTEGRATION_PLAN_*.md` 单独审查 |

## 9. 下一步建议

下一步建议是 L04：

```text
learning\L04_clock_reset.md
reports\REPORT_L04_clock_reset.md
```

但本次任务到 L03 为止。

不要自动继续 L04，不要写 Verilog，不要修改官方工程。

## 10. 给 GPT 审查的问题

1. L03 是否已经足够说明官方 DAC 输出路径？
2. 是否同意 future `error_o` 应该接在 DAC A saturation 前路径，而不是直接驱动 `dac_dat_o`？
3. 是否同意 future `control_o` 应该接在 DAC B saturation 前路径，而不是直接驱动 `dac_dat_o`？
4. 后续 integration plan 是否必须保留官方 saturation、格式转换和 ODDR？
5. 是否需要在进入 integration plan 前，先查官方硬件资料确认 DAC A/B 与 OUT1/OUT2？
