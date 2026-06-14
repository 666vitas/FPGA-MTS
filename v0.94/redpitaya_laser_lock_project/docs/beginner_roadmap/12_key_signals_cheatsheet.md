# 关键信号速查表

## 0. 本文件作用

本文件把你从学习文档到写代码到上板，最常用到的大约 15 个信号列在一张表里。

读到任何文档里出现这些信号名，回来查这张表就行。

## 1. 官方 top 信号（你只读，不改）

这些信号在 `rtl\red_pitaya_top.sv` 里定义，你的代码通过 `laser_lock_core` 的端口连接它们。

| 信号 | 位宽 | signed? | 来自 | 你的用法 |
|---|---|---|---|---|
| `adc_dat[0]` | 14 bit | signed | ADC CH1（IN1）数据，经格式转换后 | **你的 pd_i**：PD 信号输入 |
| `adc_dat[1]` | 14 bit | signed | ADC CH2（IN2）数据，经格式转换后 | **你的 ref_i**：外部 REF 输入 |
| `adc_clk` | 1 bit | 不适用 | PLL → BUFG | **你的 clk_i**：模块主时钟，约 125 MHz |
| `adc_rstn` | 1 bit | 不适用 | PS frstn[0] & pll_locked | **你的 rstn_i**：active-low 复位 |
| `dac_a_sum` | 15 bit | signed | asg_dat[0] + pid_dat[0] | **error_o 候选接入点**（saturation 之前） |
| `dac_b_sum` | 15 bit | signed | asg_dat[1] + pid_dat[1] | control_o 候选接入点（saturation 之前） |
| `dac_a` | 14 bit | 语义 signed | dac_a_sum 饱和后 | 不要直接接这里，接 saturation 前面 |
| `dac_dat_a` | 14 bit | DAC 格式 | dac_a 格式转换后 | 不要接这里，已经转成 DAC 物理格式 |
| `asg_dat[0]` | 14 bit | signed | red_pitaya_asg CH1 | 官方 ASG 输出，集成时要保留回退路径 |
| `pid_dat[0]` | 14 bit | signed | red_pitaya_pid out1 | 官方 PID 输出，第一阶段不使用 |
| `digital_loop` | 1 bit | 不适用 | red_pitaya_hk | 为 1 时 ADC 数据来自 DAC 回环，实验时**必须确认它为 0** |

## 2. 你的 laser_lock_core 端口

你的自定义模块通过这些端口和官方 top 连接。

| 端口 | 位宽 | signed? | 方向 | 接什么 | v1 行为 |
|---|---|---|---|---|---|
| `clk_i` | 1 bit | 不适用 | input | `adc_clk` | 模块时钟 |
| `rstn_i` | 1 bit | 不适用 | input | `adc_rstn` | active-low，拉低时 error_o 和 control_o 归零 |
| `pd_i` | 14 bit | signed | input | `adc_dat[0]` | PD 信号，进 BPF/mixer |
| `ref_i` | 14 bit | signed | input | `adc_dat[1]` | 外部 REF，4.6 MHz，进 mixer |
| `error_o` | 14 bit | signed | output | `dac_a_sum` 前 | v1a：= pd_i；v1b：= ref_i；v1c+：mixer+LFP 结果 |
| `control_o` | 14 bit | signed | output | `dac_b_sum` 前 | v1 全程固定为 0 |

## 3. 内部子模块信号（v1c 以后使用）

这些信号在 `laser_lock_core` 内部，连接各个子模块。

| 信号 | 位宽 | signed? | 从哪个模块 | 到哪个模块 |
|---|---|---|---|---|
| 内部 pd_filtered | 14 bit | signed | bandpass_filter（或 bypass） | mixer_core |
| mixer 输出 | 28 bit | signed | mixer_core（pd_i × ref_i） | lowpass_filter |
| 内部 lpf_out | 28 bit 或更多 | signed | lowpass_filter | gain_offset_limit |
| 内部 gain_out | 14 bit | signed | gain_offset_limit | output_protect |

**特别提醒**：mixer 输出是 28-bit signed（两个 14-bit 相乘的完整结果）。写到 error_o 之前必须在 gain_offset_limit 里缩放到 14-bit 并做饱和保护。直接截位会丢精度。

## 4. 信号名字规律

| 规则 | 例子 | 说明 |
|---|---|---|
| `_i` 结尾 | `pd_i`、`clk_i` | input 端口 |
| `_o` 结尾 | `error_o`、`dac_dat_o` | output 端口 |
| `_n` 结尾 | `rstn_i`、`adc_rstn` | 通常是 active-low |
| `[数字]` | `adc_dat[0]` | 数组的第 0 个元素，例如第 0 路 ADC |

## 5. 你现在只需要记住

```
pd_i  = adc_dat[0]  ← IN1 ← PD
ref_i = adc_dat[1]  ← IN2 ← 外部 REF
clk_i = adc_clk     ← 125 MHz 主时钟
rstn_i = adc_rstn   ← active-low
error_o → OUT1      ← 你要看的结果
control_o = 0       ← 第一阶段不用
```
