# REPORT_integration_plan_v1ab_passthrough_debug

## 0. 本报告作用

本报告记录本次任务：为 `v1ab_passthrough_debug` 生成官方 top 集成方案。

本次只生成文档，不修改官方工程，不修改 `red_pitaya_top.sv`，不复制官方 top，不生成 patch，不开始 `v1c mixer`。

## 1. 本次阅读的文件

本次先阅读了：

```text
redpitaya_laser_lock_project\docs\current\03_CODEX_RULES.md
redpitaya_laser_lock_project\docs\integration\IMPLEMENTATION_PLAN_mts_error_chain_v1.md
redpitaya_laser_lock_project\docs\reports\REPORT_v1ab_passthrough_debug.md
redpitaya_laser_lock_project\docs\board_tests\BOARD_TEST_v1ab_passthrough_debug.md
redpitaya_laser_lock_project\rtl\laser_lock_core.sv
redpitaya_laser_lock_project\rtl\output_protect.sv
redpitaya_laser_lock_project\sim\tb_laser_lock_core_v1ab.sv
```

## 2. 本次生成的文件

| 文件 | 作用 |
|---|---|
| `redpitaya_laser_lock_project\docs\integration\INTEGRATION_PLAN_v1ab_passthrough_debug.md` | 规划 `laser_lock_core` 如何接入 Red Pitaya top |
| `redpitaya_laser_lock_project\docs\reports\REPORT_integration_plan_v1ab_passthrough_debug.md` | 本报告 |

## 3. 集成方案核心内容

集成目标：

```text
clk_i  <- adc_clk
rstn_i <- adc_rstn
pd_i   <- adc_dat[0]
ref_i  <- adc_dat[1]

error_o   -> DAC A saturation 前候选路径
control_o -> 第一阶段保持 0
```

建议新增 top 内部信号：

```text
laser_error
laser_control
```

建议 DAC A 接入方式：

```text
USE_LASER_LOCK_CORE = 0:
  dac_a_sum = asg_dat[0] + pid_dat[0]
  dac_b_sum = asg_dat[1] + pid_dat[1]

USE_LASER_LOCK_CORE = 1:
  dac_a_sum = sign_extend(laser_error)
  dac_b_sum = 15'sd0
```

## 4. 仿真命令路径修正说明

为避免新手混淆路径，本次在新报告和 integration plan 中补充：

如果当前目录是：

```text
redpitaya_laser_lock_project\sim
```

推荐命令是：

```text
xvlog -sv ..\rtl\output_protect.sv ..\rtl\laser_lock_core.sv tb_laser_lock_core_v1ab.sv
xelab tb_laser_lock_core_v1ab -s tb_laser_lock_core_v1ab_sim
xsim tb_laser_lock_core_v1ab_sim -runall
```

如果当前目录是临时子目录，例如：

```text
redpitaya_laser_lock_project\sim\v1ab_xsim_run
```

才需要使用：

```text
..\..\rtl
```

## 5. 本次没有做的事

| 项目 | 状态 |
|---|---|
| 修改官方 `rtl` | 没有 |
| 修改官方 `red_pitaya_top.sv` | 没有 |
| 修改 Vivado 工程 | 没有 |
| 复制官方 top | 没有 |
| 生成 patch | 没有 |
| 写 Verilog/SystemVerilog | 没有 |
| 开始 `v1c mixer` | 没有 |
| 接 `D2-125` | 没有 |
| 接激光器反馈 | 没有 |

## 6. 必须保留的官方逻辑

集成方案明确要求保留：

- saturation；
- signed-to-unsigned / negative-slope conversion；
- DAC ODDR；
- PLL；
- BUFG；
- ADC IO；
- PS/AXI/DDR；
- XDC。

## 7. 下一步建议

下一步不是直接上板。

建议顺序：

1. GPT 审查：

```text
docs\integration\INTEGRATION_PLAN_v1ab_passthrough_debug.md
```

2. 决定使用 `vendor_shell` 还是 patch；
3. 用户明确允许后，再生成具体修改 diff；
4. 然后进入 Vivado；
5. Vivado 通过后，再按 `BOARD_TEST_v1ab_passthrough_debug.md` 做示波器验证。

## 8. 给 GPT 审查的问题

1. `laser_error` 接到 `dac_a_sum` 前的方案是否合理？
2. `dac_b_sum = 15'sd0` 是否是 v1ab 最安全的选择？
3. 当前是否应优先采用 `vendor_shell` 副本策略？
4. `OUTPUT_MODE=0/1` 分别生成 bitstream 是否适合当前小白阶段？
5. 是否需要在 integration plan 中进一步补充 Vivado GUI 操作截图或菜单步骤？
