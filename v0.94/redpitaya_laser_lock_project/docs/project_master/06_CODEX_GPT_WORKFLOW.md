# Codex / GPT 协作流程

## 0. 本文件作用

本文件指导以后如何让 Codex 和 GPT 协作。它的目标是防止项目跳阶段、乱改文件、文档散乱，尤其适合 FPGA / Verilog / Vivado 新手。

基本分工：

- Codex：读本地工程、改文件、生成 RTL/testbench/报告、做只读检查。
- GPT：审查设计思路、报错、实验现象和下一步策略。
- 用户：决定是否进入下一阶段、是否允许修改敏感文件、是否上板连接外部设备。

## 每次 Codex 必须做

每次进入新任务前，Codex 必须：

- 读 `docs\project_master`；
- 只做当前版本；
- 不跨阶段；
- 生成 RTL；
- 生成 testbench；
- 生成 REPORT；
- 生成 BOARD_TEST；
- 需要接 top 时先生成 integration plan 或 patch guide；
- 不直接修改敏感文件，除非用户明确允许；
- 不修改官方干净原版 `E:\new\fpga_lock\v94\guanfang-v0.94\v0.94`；
- 不运行 Vivado，除非用户明确要求；
- 不删除旧文档。

当前阶段特别规则：

```text
v1ab 没完成上板验证前，不开始 v1c mixer。
```

## 每次发给 GPT 什么

遇到需要 GPT 审查时，建议发这些内容：

- 修改文件；
- REPORT；
- Vivado 报错；
- 示波器截图；
- 当前版本；
- 失败现象；
- 当前 `USE_LASER_LOCK_CORE`；
- 当前 `LASER_LOCK_OUTPUT_MODE`；
- 当前接线；
- 当前信号源频率、幅度、offset。

不要只发一句“Vivado 报错了”。最好按这个模板：

```text
当前版本：
当前目标：
我改了哪些文件：
Vivado 运行到哪一步：
完整报错：
当前接线：
示波器现象：
我希望 GPT 判断什么：
```

## 出错时怎么让 Codex 修正

出错时不要直接要求 Codex 乱改代码。必须先让 Codex 生成：

```text
CORRECTION_xxx.md
```

`CORRECTION_xxx.md` 至少包含：

- 错误现象；
- 涉及文件；
- 可能原因；
- 建议修改；
- 回退方法；
- 是否需要修改 RTL；
- 是否需要修改 Vivado 工程；
- 是否需要重新生成 bitstream。

然后再决定是否执行修正。

## 推荐每个版本的交付物

每个版本至少应该有：

```text
rtl\<module>.sv
sim\tb_<module>_<version>.sv
docs\reports\REPORT_<version>.md
docs\board_tests\BOARD_TEST_<version>.md
docs\integration\INTEGRATION_PLAN_<version>.md
```

如果只是文档整理或 workspace 整理，也必须生成对应 REPORT。

## 敏感文件规则

以下文件或目录不能随便改：

```text
E:\new\fpga_lock\v94\guanfang-v0.94\v0.94
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
Vivado .xpr 工程文件
XDC/SDC 约束
PLL/ODDR/PS/AXI/DDR 相关文件
```

如果确实需要改 `red_pitaya_top.sv`，必须满足：

1. 用户明确允许；
2. 已有备份；
3. 已有 integration plan；
4. 已有回退方法；
5. 修改后生成 REPORT。

## 当前项目主线阅读顺序

以后优先阅读：

```text
docs\project_master\00_PROJECT_FINAL_GOAL.md
docs\project_master\01_CURRENT_STATUS_SUMMARY.md
docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
docs\project_master\04_VIVADO_OPERATION_GUIDE.md
docs\project_master\05_EXPERIMENT_TEST_GUIDE.md
```

旧文档不删除，但默认作为历史记录和证据库，不再作为第一阅读入口。
