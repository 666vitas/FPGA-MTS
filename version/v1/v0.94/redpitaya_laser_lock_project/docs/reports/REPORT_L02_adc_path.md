# REPORT: L02_adc_path

## 0. 本文件作用

本文件记录 L02_adc_path 的执行结果。

本次任务只阅读官方：

```text
rtl\red_pitaya_top.sv
```

并生成 L02 ADC 输入路径学习文档。

## 1. 本次任务是什么

任务目标：

- 追踪 `adc_dat_i` 是什么；
- 说明 `adc_dat_i[0]`、`adc_dat_i[1]` 的位宽；
- 说明 `adc_dat_raw` 如何由 `adc_dat_i` 得到；
- 说明 `adc_dat` 如何由 `adc_dat_raw` 得到；
- 说明 `adc_dat[0]`、`adc_dat[1]` 当前送到哪些模块；
- 判断 `adc_dat[0]` 是否可以作为 future `laser_lock_core.pd_i` 候选；
- 判断 `adc_dat[1]` 是否可以作为 future `laser_lock_core.ref_i` 候选；
- 说明 `adc_dat` 属于哪个时钟域；
- 说明 `adc_rstn` 如何生成；
- 列出需要板级资料或实验确认的事项。

## 2. 阅读对象

本次只读：

```text
rtl\red_pitaya_top.sv
```

没有修改官方文件。

## 3. 生成了哪些文件

本次新增：

```text
docs\learning\L02_adc_path.md
docs\reports\REPORT_L02_adc_path.md
```

## 4. 学习结果摘要

ADC 数据路径可以概括为：

```text
adc_dat_i
  -> adc_dat_raw
  -> adc_dat
  -> scope / PID / future laser_lock_core candidate
```

关键结论：

| 结论 | 说明 |
|---|---|
| `adc_dat_i` | top 的 ADC 数据输入端口 |
| `adc_dat_i[0]`、`adc_dat_i[1]` | 默认 `MNA=2` 时，两路 16 bit ADC 原始输入 |
| `adc_dat_raw` | 每路取 `adc_dat_i[x][15:2]` 得到 14 bit |
| `adc_dat` | signed 14 bit 内部 ADC 数据 |
| `adc_dat[0]` | 送 scope CH1 和 PID in1，可作为 future `pd_i` 候选 |
| `adc_dat[1]` | 送 scope CH2 和 PID in2，可作为 future `ref_i` 候选 |
| `adc_dat` 时钟域 | `adc_clk` |
| `adc_rstn` | active low，由 `frstn[0] & pll_locked` 在 `adc_clk` 下生成 |

## 5. 证据摘要

| 证据 | 位置 |
|---|---|
| `parameter MNA = 2` | `rtl\red_pitaya_top.sv` 第 56 行附近 |
| `adc_dat_i` 声明 | 第 95 行附近 |
| `SBA_T` signed 14 bit | 第 183 行附近 |
| `adc_dat` 声明 | 第 186 行附近 |
| `adc_clk`、`adc_rstn` 声明 | 第 170-172 行附近 |
| `adc_clk_i -> IBUFDS -> adc_clk_in` | 第 219 行附近 |
| PLL 输出 `pll_adc_clk` | 第 221-234 行附近 |
| `pll_adc_clk -> BUFG -> adc_clk` | 第 236 行附近 |
| `adc_rstn <= frstn[0] & pll_locked` | 第 256-258 行附近 |
| `adc_dat_raw` 声明 | 第 392 行附近 |
| `adc_dat_raw[0] = adc_dat_i[0][15:2]` | 第 397 行附近 |
| `adc_dat_raw[1] = adc_dat_i[1][15:2]` | 第 398 行附近 |
| `adc_dat` 在 `posedge adc_clk` 更新 | 第 401 行附近 |
| `adc_dat[0]` 转换 | 第 402 行附近 |
| `adc_dat[1]` 转换 | 第 403 行附近 |
| `digital_loop` 来自 HK | 第 445-452 行附近 |
| `adc_dat[0]`、`adc_dat[1]` 送 scope | 第 517-522 行附近 |
| `adc_dat[0]`、`adc_dat[1]` 送 PID | 第 577-582 行附近 |

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

本次没有开始：

```text
L03_dac_path
```

本次没有分析 DAC 输出路径。

## 7. 已确认

- `adc_dat_i` 是 ADC 输入端口。
- 默认有两路 acquisition 数据。
- `adc_dat_i[0]` 和 `adc_dat_i[1]` 每路是 16 bit。
- `adc_dat_raw[0]` 和 `adc_dat_raw[1]` 每路是 14 bit。
- `adc_dat[0]` 和 `adc_dat[1]` 每路是 signed 14 bit。
- `adc_dat` 在 `adc_clk` 时钟域。
- `adc_dat[0]` 当前送到 scope CH1 和 PID in1。
- `adc_dat[1]` 当前送到 scope CH2 和 PID in2。
- `adc_dat[0]` 是 future `pd_i` 合理候选。
- `adc_dat[1]` 是 future `ref_i` 合理候选。

## 8. 不确定，需要人工确认

| 不确定项 | 说明 |
|---|---|
| `adc_dat[0]` 是否物理对应 IN1 | 需要板级资料、约束或上板实验确认 |
| `adc_dat[1]` 是否物理对应 IN2 | 需要板级资料、约束或上板实验确认 |
| `digital_loop` 默认是否关闭 | 需要 HK/软件配置或实验确认 |
| ADC 电压范围与码值比例 | 需要 Red Pitaya 硬件资料确认 |
| 输入波形是否反相 | top 有 negative slope 转换，实际极性需实验确认 |

## 9. 下一步建议

下一步建议是 L03：

```text
learning\L03_dac_path.md
reports\REPORT_L03_dac_path.md
```

但本次任务到 L02 为止。

不要自动继续 L03，不要写 Verilog，不要修改官方工程。

## 10. 给 GPT 审查的问题

1. L02 是否已经足够说明 `adc_dat_i -> adc_dat_raw -> adc_dat`？
2. 是否同意把 `adc_dat[0]` 暂定为 future `pd_i` 候选？
3. 是否同意把 `adc_dat[1]` 暂定为 future `ref_i` 候选？
4. L03 是否应只分析 DAC 输出路径，不再重复 ADC 细节？
