# REPORT_experiment_driven_implementation_plan

## 0. 本报告作用

本报告记录本次任务：把 L01-L04 的学习结论整理成“以实验链路为准、以实现为目标”的项目实施方案。

本次没有继续泛读 `red_pitaya_top.sv`，没有开始 L05，也没有写 Verilog。

## 1. 本次阅读的输入文档

本次依据以下已有文档整理：

```text
docs\README_DOCS_INDEX.md
docs\current\00_CONTEXT_FROM_GPT.md
docs\current\01_PROJECT_MASTER_PLAN.md
docs\current\02_TOP_LEARNING_OUTLINE.md
docs\current\03_CODEX_RULES.md
docs\learning\L01_top_overview.md
docs\learning\L02_adc_path.md
docs\learning\L03_dac_path.md
docs\learning\L04_clock_reset.md
docs\reports\REPORT_L01_top_overview.md
docs\reports\REPORT_L02_adc_path.md
docs\reports\REPORT_L03_dac_path.md
docs\reports\REPORT_L04_clock_reset.md
```

## 2. 本次生成的文件

| 文件 | 作用 |
|---|---|
| `docs\current\04_EXPERIMENT_DRIVEN_IMPLEMENTATION_PLAN.md` | 把 L01-L04 结论转换成实验驱动的实施路线 |
| `docs\reports\REPORT_experiment_driven_implementation_plan.md` | 记录本次整理任务 |

## 3. 本次整理出的核心结论

| 项目 | 结论 |
|---|---|
| PD 输入候选 | `adc_dat[0] -> pd_i` |
| REF 输入候选 | `adc_dat[1] -> ref_i` |
| 主时钟 | `adc_clk -> clk_i` |
| 复位 | `adc_rstn -> rstn_i` |
| error 输出候选 | `error_o -> DAC A saturation 前` |
| control 输出候选 | `control_o -> DAC B saturation 前` |
| 实现边界 | 自定义 core 放在 `redpitaya_laser_lock_project`，不直接写入官方 `rtl` |

## 4. 本次实施路线摘要

本次建议后续按以下顺序推进：

1. 阶段 A：先在 `redpitaya_laser_lock_project` 内实现和仿真自定义 core，不接官方 top。
2. 阶段 B：生成官方 top 集成方案，不直接修改官方工程。
3. 阶段 C：经用户和 GPT 审查后，再进入 Vivado 集成、synthesis、implementation、bitstream/bin。
4. 阶段 D：先用信号发生器和示波器验证，再接真实 `PD` 和 `REF`。
5. 阶段 E：后续再考虑 `D2-125`、PID、sweep、AI。

## 5. 本次没有做的事

| 项目 | 状态 |
|---|---|
| 修改官方 `rtl` | 没有修改 |
| 修改官方 `project` | 没有修改 |
| 修改官方 `sim` | 没有修改 |
| 修改官方 `ip` | 没有修改 |
| 修改官方 `sdc` | 没有修改 |
| 修改 `red_pitaya_top.sv` | 没有修改 |
| 生成 Verilog/SystemVerilog | 没有生成 |
| 实现 `laser_lock_core` | 没有实现 |
| 开始 L05 | 没有开始 |

## 6. 下一步建议

推荐下一步先生成：

```text
docs\integration\INTERFACE_CONTRACT_laser_lock_core.md
```

然后再生成 `v1_pd_passthrough` 的 RTL 和 testbench。

这样做的好处是：先把接口、位宽、signed、reset、时钟域、未来 top 接线边界讲清楚，再写代码，比较适合 FPGA/Verilog 新手。

## 7. 给 GPT 审查的问题

1. 是否可以停止泛读 top，转入实现导向？
2. L05 是否只做最小 scope/ASG/PID 干扰检查？
3. 是否应先写 `INTERFACE_CONTRACT_laser_lock_core.md` 再写 RTL？
4. v1 是否只做 `pd_i -> error_o`？
