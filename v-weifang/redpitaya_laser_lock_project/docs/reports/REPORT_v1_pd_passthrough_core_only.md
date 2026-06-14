# REPORT_v1_pd_passthrough_core_only

## 0. 本报告作用

本报告记录本次任务：在 `redpitaya_laser_lock_project` 项目目录内实现 `v1_pd_passthrough` 的 core-only 版本。

core-only 的意思是：只实现自定义 `laser_lock_core` 和它的 testbench，不接入官方 `red_pitaya_top.sv`，也不修改 Vivado 工程。

## 1. 本任务做了什么

本次实现了 `laser_lock_core` 的第一版最小功能：

```text
pd_i -> error_o
control_o -> 0
```

并且规定：

- `rstn_i` 是 active-low 复位；
- 当 `rstn_i = 0` 时，`error_o` 和 `control_o` 都清零；
- 当 `rstn_i = 1` 时，`error_o` 在每个 `clk_i` 上升沿锁存 `pd_i`；
- `ref_i` 在 v1 中暂不使用；
- `control_o` 在 v1 中始终为 `14'sd0`。

本次采用的是时序直通，不是纯组合直通。

大白话解释：这个 v1 模块在硬件上等价于一个 14 bit signed 寄存器。它每个时钟上升沿把 `pd_i` 记下来，然后从 `error_o` 输出。

## 2. 新增/修改文件

| 文件 | 类型 | 作用 |
|---|---|---|
| `redpitaya_laser_lock_project\rtl\laser_lock_core.sv` | 修改已有 0 字节占位文件 | 实现 `v1_pd_passthrough` core |
| `redpitaya_laser_lock_project\sim\tb_laser_lock_core.sv` | 修改已有 0 字节占位文件 | 测试 reset、正数、负数、0、`ref_i` 不影响、`control_o` 恒 0 |
| `redpitaya_laser_lock_project\docs\reports\REPORT_v1_pd_passthrough_core_only.md` | 新增 | 记录本次任务 |

## 3. 端口说明

| 端口 | 位宽 | signed/unsigned | 方向 | 说明 |
|---|---:|---|---|---|
| `clk_i` | 1 bit | 不适用 | input | 模块时钟，未来接 `adc_clk` |
| `rstn_i` | 1 bit | 不适用 | input | active-low 复位，未来接 `adc_rstn` |
| `pd_i` | 14 bit | signed | input | 未来来自 `adc_dat[0]`，表示 PD 光强信号 |
| `ref_i` | 14 bit | signed | input | 未来来自 `adc_dat[1]`，v1 暂不使用 |
| `error_o` | 14 bit | signed | output | v1 中输出 `pd_i` 的寄存结果 |
| `control_o` | 14 bit | signed | output | v1 固定为 0 |

## 4. testbench 覆盖内容

`tb_laser_lock_core.sv` 覆盖以下检查：

| 测试项 | 预期结果 |
|---|---|
| `rstn_i` 拉低 | `error_o = 0`，`control_o = 0` |
| `pd_i` 为正数 | `error_o` 在时钟上升沿后等于 `pd_i` |
| `pd_i` 为负数 | `error_o` 正确保持 signed 负数 |
| `pd_i` 为 0 | `error_o = 0` |
| `ref_i` 改变 | 不影响 `error_o` |
| 任意正常工作状态 | `control_o` 始终为 0 |
| 运行中再次 reset | 两个输出重新清零 |

## 5. 仿真结果

已使用 Vivado Simulator 2020.1 运行仿真。

运行命令：

```text
xvlog -sv redpitaya_laser_lock_project\rtl\laser_lock_core.sv redpitaya_laser_lock_project\sim\tb_laser_lock_core.sv
xelab tb_laser_lock_core -s tb_laser_lock_core_sim
xsim tb_laser_lock_core_sim -runall
```

仿真文字结果：

```text
PASS: tb_laser_lock_core v1_pd_passthrough all checks passed.
```

说明：

- `xvlog` 通过，SystemVerilog 语法检查通过；
- `xelab` 通过，模块例化和 elaboration 通过；
- `xsim` 通过，所有 testbench 检查通过；
- 本次没有生成波形截图，只记录文字仿真结果。

## 6. 没有修改官方工程

本次明确没有修改以下官方目录：

```text
rtl
project
sim
ip
sdc
```

本次也没有修改：

```text
rtl\red_pitaya_top.sv
red_pitaya_top.sv
Vivado 工程
```

## 7. 没有生成 integration patch

本次没有生成 `integration patch`。

原因：当前任务只要求 core-only 版本，后续接入官方 top 前，必须先生成单独的 `integration plan`。

## 8. 下一步建议

下一步建议先运行 testbench，确认 v1 行为正确。

通过仿真后，再生成：

```text
docs\integration\INTERFACE_CONTRACT_laser_lock_core.md
```

或根据用户明确指令继续生成官方 top 集成方案。
