# 项目总流程：FPGA 小白版

## 0. 本文件作用

本文件告诉你整个 Red Pitaya MTS 激光稳频 FPGA 项目应该按什么顺序推进。

大白话：不要一上来就改 Vivado、烧板子、接激光器。正确顺序是先写清目标，再写小模块，再仿真，再写集成方案，再上板示波器验证。

## 1. 我需要理解什么

你需要先理解三件事：

| 概念 | 小白解释 |
|---|---|
| RTL | 描述 FPGA 里要生成什么数字电路 |
| testbench | 不上板的虚拟实验台，用来检查 RTL |
| integration plan | 真正接入官方 top 前的接线说明 |

当前项目的目标链路是：

```text
PD -> IN1 -> adc_dat[0] -> FPGA -> error_o -> OUT1
REF -> IN2 -> adc_dat[1] --------^
```

第一阶段不是 PID，不是 sweep，不是 AI，也不是激光器反馈闭环。

## 2. 我需要操作什么

总流程如下：

| 阶段 | 你要做什么 |
|---|---|
| 1 | 让 Codex 生成当前版本 RTL 和 testbench |
| 2 | 运行 testbench，确认仿真通过 |
| 3 | 让 Codex 生成 REPORT |
| 4 | 让 Codex 生成 integration plan |
| 5 | 把 integration plan 发给 GPT 审查 |
| 6 | 审查通过后，才允许考虑 Vivado 集成 |
| 7 | 生成 bitstream |
| 8 | 上板时先接示波器 |
| 9 | 示波器确认安全后，再考虑接 `D2-125 error input` |

## 3. 我需要发给 GPT 什么

每个阶段建议发给 GPT：

```text
1. 当前版本名
2. 目标功能
3. RTL 文件
4. testbench 文件
5. REPORT 文件
6. 仿真输出结果
7. integration plan
8. 上板测试计划
```

让 GPT 审查的问题：

- 位宽是否安全？
- signed/unsigned 是否正确？
- reset 是否合理？
- 是否误改官方工程？
- 是否可以进入下一阶段？

## 4. Codex 应该生成什么

每个代码阶段，Codex 至少生成：

| 文件 | 作用 |
|---|---|
| `rtl\*.sv` | 自定义 RTL |
| `sim\tb_*.sv` | 自检 testbench |
| `docs\reports\REPORT_*.md` | 任务报告 |
| `docs\board_tests\BOARD_TEST_*.md` | 上板测试说明 |

如果要接官方 top，还必须先生成：

```text
docs\integration\INTEGRATION_PLAN_*.md
```

## 5. 成功标准是什么

进入下一阶段前必须满足：

- testbench 通过；
- REPORT 写清楚做了什么；
- 没有修改官方工程；
- 上板前有 BOARD_TEST；
- 集成前有 integration plan；
- GPT 审查没有发现硬伤。

## 6. 失败怎么排查

| 失败现象 | 先查什么 |
|---|---|
| 仿真编译失败 | 文件路径、模块名、端口名 |
| 仿真逻辑失败 | reset、时钟、signed 位宽 |
| Vivado 找不到模块 | 文件是否加入工程 |
| OUT1 没波形 | bitstream 是否正确、`OUTPUT_MODE` 是否正确、DAC 接线 |
| OUT1 削顶 | 输入幅度、输出限幅、DAC 路径 |

## 7. 现在只需要记住什么

你现在只需要记住一句话：

```text
先让每个小版本在仿真里通过，再考虑 Vivado 和上板。
```
