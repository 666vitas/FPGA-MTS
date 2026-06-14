# 03_FPGA_CODE_REVIEW_RULES

## 0. 本文件作用

本文件是 FPGA 工程师审查清单。每次修改 RTL 前后都必须按本文件检查。当前状态参见 [[STATUS]]。

## 1. RTL 修改前后通用审查清单

每次修改 RTL 前后必须检查：

| 序号 | 检查项 | 教学解释 |
|---|---|---|
| 1 | `signed / unsigned` 是否正确 | ADC 数据是 signed 14-bit，混频和滤波必须按有符号数理解 |
| 2 | 位宽是否足够 | 乘法、加法、滤波会增长位宽，不能随便截断 |
| 3 | 是否有溢出 | 溢出会让波形翻转、顶死或变成看似随机的错误 |
| 4 | 是否需要 saturation | 输出到 14-bit DAC 前通常需要限幅保护 |
| 5 | reset 是否安全 | reset 时输出必须回到安全值，不能给 OUT1/OUT2 突然大输出 |
| 6 | 是否所有逻辑在 `adc_clk` 域 | 当前 v1 主链路默认在 ADC 时钟域工作 |
| 7 | 是否引入 CDC | 如果跨时钟域，必须有同步或 FIFO，不能直接连 |
| 8 | 是否推断 latch | `always_comb` 必须覆盖所有分支 |
| 9 | 是否影响 DAC A / OUT1 路径 | OUT1 是当前实验观察口，任何改动都要可解释 |
| 10 | 是否误改 ODDR | ODDR 是官方高速 DAC 输出结构，默认禁止修改 |
| 11 | 是否误改 PLL | PLL 影响全局时钟，默认禁止修改 |
| 12 | 是否误改 ADC IO | ADC 输入格式和时序是官方底层，默认禁止修改 |
| 13 | 是否误改 PS/AXI/DDR | 当前 v1 不碰处理器系统和 DDR |
| 14 | 是否误改 XDC/SDC | 约束文件改动可能影响全工程实现，默认禁止 |
| 15 | 是否有 testbench | 没有仿真，不允许直接上 Vivado/上板 |
| 16 | 是否能上板验证 | 每个版本必须能用示波器看到一个明确现象 |
| 17 | 是否能用示波器判断结果 | 如果示波器无法判断，版本目标太大或太模糊 |

## 1.1 v2 PI/PID 审查清单

每次审查 v2 `pi_controller.sv` / `tb_pi_controller.sv` 必须检查：

- `error_i` 必须是 signed 14-bit；
- `kp_i` / `ki_i` 必须按 signed 处理；
- P/I 乘法必须扩位，不能直接截回 14-bit；
- integrator 建议 40-48 bit，若不是该范围必须明确说明理由；
- 必须使用 `pid_ce` 降采样更新，不能默认每个 125 MHz 时钟都积分；
- `enable=0` 时 `control_o=0`；
- reset 后 `control_o=0`，integrator 清零；
- `hold_i` 行为必须明确，不能半冻结半更新；
- `reset_integrator_i` 必须能清积分；
- `polarity_i` 必须可切换，用于避免正反馈；
- `output_limit_i` 必须永远有效；
- 必须有 anti-windup；
- `control_o` 到 DAC 前必须 saturation；
- 不允许 wrap-around；
- 不允许默认满量程输出；
- 不允许破坏 v1 OUT1 error 输出路径；
- testbench 必须覆盖 P-only、I-only、PI、正负误差、饱和、reset、enable、hold、polarity、output_limit。

## 2. 特别针对 v1c mixer 的审查

`v1c_mixer_only` 必须遵守：

- `14-bit signed × 14-bit signed = 28-bit signed`；
- 必须缩放回 14-bit；
- 必须考虑 saturation；
- 输出不是最终 error；
- mixer 后还有 `2f` 分量；
- `v1d` 才加 LPF。

教学解释：

两个同频正弦相乘：

```text
sin(wt) * sin(wt) = 0.5 - 0.5*cos(2wt)
```

所以没有 LPF 时，输出里会有 DC 分量和二倍频分量。`v1c` 的目标不是让波形像最终误差信号，而是证明数字乘法链路能工作。

## 3. v1c 不允许修改的范围

`v1c` 默认不允许修改：

- `red_pitaya_top.sv` 中的 ODDR；
- `dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o`；
- PLL / BUFG；
- ADC IO；
- PS/AXI/DDR；
- XADC/AMS；
- XDC/SDC；
- D2-125 接线；
- EOM 驱动；
- 激光器反馈。

## 4. v1c 推荐检查问题

实现前必须能回答：

1. `pd_i` 和 `ref_i` 的位宽是多少？
2. 它们是否是 signed？
3. 乘法结果位宽是多少？
4. 缩放选择哪几位或右移多少位？
5. 最大输入时是否会溢出？
6. reset 后输出是什么？
7. `control_o` 是否继续为 0？
8. `output_protect` 放在 mixer 前还是后？
9. testbench 如何计算期望输出？
10. 上板时示波器应该看到什么？

## 5. v1d_mixer_lpf 审查清单

`v1d_mixer_lpf` 必须检查：

- `lpf_core` 是否使用 signed 数据；
- accumulator / state 是否足够宽；
- `LPF_SHIFT` 是否可参数化；
- `enable=0` 是否安全输出 0 或保持明确定义状态；
- reset 是否输出 0；
- 输出是否 saturation 到 signed 14-bit；
- 是否不做无保护截断；
- `OUTPUT_MODE=0/1/2` 是否被保留；
- `OUTPUT_MODE=3` 是否只新增 `mixer + LPF`；
- 是否没有误改 `red_pitaya_top.sv` 的官方 ADC / DAC / PLL / ODDR / PS / AXI / XDC；
- 是否有 `tb_lpf_core`；
- 是否有 `tb_laser_lock_core_v1d`；
- testbench 是否测试 reset、enable、阶跃、高频平滑、signed 正负输入、saturation；
- 是否禁止在 v1d 中加入 `10 MHz LPF`、`1.8 MHz HPF`、gain、I/Q、PID、AI。

教学解释：

`v1d` 的 LPF 是 mixer 后低通，不是 mixer 前的 `10 MHz LPF + 1.8 MHz HPF`。它的任务是压低 mixer 后的 `2f` 高频项，让低频 / 差频 / 基带分量能从 `OUT1` 上更清楚地看到。
