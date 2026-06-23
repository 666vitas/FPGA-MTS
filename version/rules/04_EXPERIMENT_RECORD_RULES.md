# 04_EXPERIMENT_RECORD_RULES

## 0.0A RTL/SIM 修改后的实验说明硬要求（2026-06-23）

每次 Codex 修改 RTL 或 SIM 后，相关状态文档、SOP 或任务结果必须同步写清楚：

```text
1. 本次代码完成的功能。
2. 当前能否锁定激光。
3. 当前属于仿真、上板示波器还是闭环锁定测试。
4. IN1/IN2/OUT1/OUT2 的接线。
5. 示波器可能看到的正常现象。
6. 什么现象算通过。
7. 什么现象必须停止。
8. 是否允许烧录。
9. 是否允许接激光器。
10. 用户下一步实验动作。
11. 若不是完整 PI/PID，必须明确缺少什么或仍待验证什么。
```

缺少上述内容的输出不完整，不能作为进入 Vivado 或上板实验的依据。

## 0. 本文件作用

本文件规定每次上板实验必须如何记录。当前状态参见 [[STATUS]]。

FPGA 实验中，”我好像看到波形了”不够。必须记录版本、bit/bin、加载命令、接线、参数、示波器现象和是否通过。

## 1. 每次实验必须记录的 14 项

每次实验都必须记录：

1. 日期；
2. 版本；
3. bit/bin 文件；
4. `fpgautil` 加载命令；
5. 是否断电重载；
6. 代码参数；
7. 接线；
8. 信号发生器参数；
9. 示波器参数；
10. 观察结果；
11. 是否通过；
12. 失败排查；
13. 截图文件名；
14. 下一步。

## 2. 统一记录位置

v1 实验记录统一写入：

```text
E:\new\fpga_lock\v94\version\v1\V1_EXPERIMENT_REPORT.md
```

后续版本分别写入：

```text
E:\new\fpga_lock\v94\version\v2
E:\new\fpga_lock\v94\version\v3
E:\new\fpga_lock\v94\version\v4
E:\new\fpga_lock\v94\version\v5
```

## 3. 推荐实验记录模板

```text
## YYYY-MM-DD 实验记录：<版本 / 目标>

### 1. 实验目标

### 2. bit/bin 文件

### 3. fpgautil 加载命令

### 4. 是否断电或重新加载

### 5. 代码参数

### 6. 接线

### 7. 信号发生器参数

### 8. 示波器参数

### 9. 观察结果

### 10. 是否通过

### 11. 失败排查

### 12. 截图文件名

### 13. 下一步
```

## 4. v1 当前实验记录状态

当前已经记录：

- `v1ab-1: IN1 -> OUT1` 已真实上板通过；
- `v1ab-2: IN2 -> OUT1` 已真实上板通过。
- `v1c_mixer_only` 已真实上板通过。

这说明：

- 两路 ADC 输入链路可用；
- `laser_lock_core` 能接收 `pd_i/ref_i`；
- DAC A / OUT1 输出链路可用；
- bit.bin 加载后真实生效。
- `mixer_core(pd_i, ref_i)` 已经能在真实 FPGA 上产生依赖两路输入的混频输出。

当前准备：

```text
v1d_mixer_lpf
```

但当前还不能说明：

- 已经有 BPF/gain；
- 已经有真正 MTS error；
- 可以接 D2-125；
- 可以实现稳频。

## 4.1 v1d 上板记录必须包含

`v1d_mixer_lpf` 上板记录必须包含：

- `OUTPUT_MODE=2` raw mixer 对照；
- `OUTPUT_MODE=3` mixer + LPF；
- `IN1 = 100 kHz`；
- `IN2 = 101 kHz`；
- `OUT1` 是否出现约 `1 kHz`；
- 改 `IN2 = 102 kHz` 后，`OUT1` 是否变成约 `2 kHz`；
- 改 `LPF_SHIFT` 后平滑程度是否变化；
- 是否保存示波器截图；
- 是否保存 CSV；
- 是否明确写出“不接真实 PD，不接 D2-125”。

## 4.2 真实 PD 实验从 v1e 开始记录

真实 PD 实验从 `v1e_real_pd_ref` 开始。`v1e` 必须记录：

- CH1 scan；
- CH2 raw PD；
- CH3 analog error reference，如果可接；
- CH4 FPGA OUT1；
- `OUT1` 是否与 PD 峰位置相关；
- 拔掉 REF 后 `OUT1` 是否变化；
- 改 REF 幅度后 `OUT1` 是否变化；
- `OUT1` 是否削顶或饱和；
- 是否允许进入 `v1f`。

## 4.3 v2 PI/PID 实验记录要求

v2 PI/PID 相关仿真、OUT2 示波器测试、低增益接入前置测试必须记录：

- 日期；
- v2 子阶段；
- bit/bin 文件；
- 是否只接 OUT2 示波器；
- OUT2 是否接激光，默认必须写“否”；
- `pid_ce`；
- `kp_i`；
- `ki_i`；
- `output_limit_i`；
- `offset_i`；
- enable 默认值；
- polarity；
- reset_integrator 操作；
- OUT2 Vpp；
- OUT2 offset；
- 是否随机跳变；
- 是否饱和；
- 是否削顶；
- 是否出现振荡；
- 是否与 D2-125 对比；
- 是否允许进入下一步。

## 5. 实验安全记录要求

每次接入新信号前必须记录：

- 进 Red Pitaya 前的实际 `Vpp`；
- offset；
- 是否经过衰减；
- 是否可能超过输入安全范围；
- OUT1 是否只接示波器；
- 是否确认没有接 D2-125；
- 是否确认没有接激光器反馈。
