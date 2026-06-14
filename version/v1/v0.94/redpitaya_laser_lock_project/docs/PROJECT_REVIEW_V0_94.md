# PROJECT_REVIEW_V0_94

## 0. 本报告作用

本报告是对当前项目资料库的工程总审查。

审查对象：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

递归阅读范围：

```text
docs
experiment_logs
patches
rtl
scripts
sim
```

本次只阅读、总结并生成本报告。没有修改 RTL，没有移动文件，没有删除文件，没有复制文件，没有运行 Vivado，没有生成 bitstream。

当前判断的核心问题是：

```text
当前 v0.94 工程是否可以作为候选 v1？
```

当前实验真实目标是先验证最小可测试链路：

```text
IN1 接 PD 候选信号
IN2 接外部 REF，4.6 MHz，进入 Red Pitaya 前必须在安全范围内
OUT1 / OUT2 先接示波器
先验证 ADC 输入、DAC 输出、直通、限幅、信号幅度、是否削顶
```

当前不做：

- 不替代 EOM 驱动；
- 不做 PID；
- 不接 D2-125；
- 不做自动锁定；
- 不做 AI。

## 1. 工程目录总览

### 1.1 `docs`

`docs` 是当前项目的主要知识库和工程记录中心。里面包含：

- `project_master`：当前最应该优先阅读的主线文档；
- `version_lessons`：教学型版本课程文档；
- `board_tests`：上板测试 SOP；
- `integration`：集成方案和 patch 指南；
- `learning`：早期学习官方 top、ADC、DAC、clock/reset 的文档；
- `beginner_roadmap`：面向 FPGA 新手的操作路线；
- `reports`：每次操作、整理、修正、排查的报告；
- `old`：旧思路和历史文档；
- `current`：较早期的当前规划文档；
- `README_DOCS_INDEX.md`：docs 总索引。

结论：`docs` 很丰富，但内容存在阶段性重复。后续开发应优先看 `docs\project_master`，旧文档只作为背景和历史证据。

### 1.2 `experiment_logs`

当前只发现：

```text
experiment_logs\log_001_top_learning.md
```

该文件当前内容为空或没有可读正文。说明项目还没有形成实际上板实验日志体系。

结论：明天做 `v1ab IN1 -> OUT1` 和 `IN2 -> OUT1` 时，应开始记录真实实验日志。

### 1.3 `patches`

当前只发现：

```text
patches\PATCH_v1ab_passthrough_debug.diff
```

该 patch 目标是把 `laser_lock_core` 接入官方 `red_pitaya_top.sv`：

- 新增 `USE_LASER_LOCK_CORE`；
- 新增 `LASER_LOCK_OUTPUT_MODE`；
- 新增 `laser_error` / `laser_control`；
- 实例化 `i_laser_lock_core`；
- 将 `laser_error` 接入 `dac_a_sum`；
- 当 `USE_LASER_LOCK_CORE=1` 时，旧 patch 中曾把 `dac_b_sum` 强制为 `15'sd0`。

注意：后续报告显示当前实际开发区 `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv` 已经对 DAC mux 做过更保守修正：DAC B 保持官方路径。也就是说，`patches` 里的 patch 可能不是当前最终实际 top 的完整状态，只能作为历史 patch 参考。

### 1.4 `rtl`

`rtl` 是项目资料库中的 RTL 保存区，不一定等于 Vivado 当前实际综合目录。

当前文件：

```text
adc_frontend.sv          0 bytes
laser_lock_core.sv       有实际逻辑
lpf_core.sv              0 bytes
mixer_core.sv            0 bytes
mts_demod_core.sv        0 bytes
output_protect.sv        有实际逻辑
pid_lock_core.sv         0 bytes
red_pitaya_top_laser.sv  有实际 top 副本/变体
```

结论：

- 当前真正可用的自定义 RTL 主要是 `laser_lock_core.sv` 和 `output_protect.sv`；
- `adc_frontend.sv`、`mixer_core.sv`、`lpf_core.sv`、`mts_demod_core.sv`、`pid_lock_core.sv` 是空壳；
- `red_pitaya_top_laser.sv` 是带 v1ab 集成的 top 副本/变体，但是否为 Vivado 当前 top 需要人工确认；
- 按已有主线文档，Vivado 当前实际开发 top 应优先看：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

### 1.5 `scripts`

当前只发现：

```text
scripts\notes_build_steps.md
```

该文件当前未提供可执行脚本内容。没有发现 `.ps1`、`.sh`、`.bat`、`.py` 等自动构建、上传、测试脚本。

结论：当前 scripts 目录还不能承担可复现构建/上传流程，只能说“脚本体系尚未形成”。

### 1.6 `sim`

当前文件：

```text
tb_laser_lock_core.sv
tb_laser_lock_core_v1ab.sv
tb_mixer_core.sv       0 bytes
tb_pid_lock_core.sv    0 bytes
```

结论：

- `tb_laser_lock_core_v1ab.sv` 是当前最重要 testbench；
- 它能验证 `laser_lock_core` 的 `OUTPUT_MODE=0` 和 `OUTPUT_MODE=1` 行为；
- 没有发现完整 top 级 ADC/DAC 仿真入口；
- 没有发现能直接验证真实 `IN1 -> OUT1` 或 `IN2 -> OUT1` 板级链路的仿真。

## 2. 文档总览

### 2.1 当前最重要的主线文档

这些文档和当前 v1/v1ab 测试最相关，应优先阅读：

```text
docs\project_master\00_PROJECT_FINAL_GOAL.md
docs\project_master\01_CURRENT_STATUS_SUMMARY.md
docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
docs\project_master\04_VIVADO_OPERATION_GUIDE.md
docs\project_master\05_EXPERIMENT_TEST_GUIDE.md
docs\project_master\06_CODEX_GPT_WORKFLOW.md
docs\project_master\07_DOCUMENT_CLEANUP_SUMMARY.md
docs\project_master\08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES.md
docs\project_master\version_lessons\LESSON_v1ab_passthrough_debug.md
```

作用概述：

- `00_PROJECT_FINAL_GOAL.md`：说明最终 MTS 数字链路和当前阶段边界。
- `01_CURRENT_STATUS_SUMMARY.md`：记录当前 v1ab 已完成 RTL、testbench、bitstream、bit.bin、fpgautil 加载，但尚未完成示波器物理测试。
- `02_VERSION_ROADMAP_V1_TO_AI.md`：定义从 `v1ab` 到 `v5` 的版本路线。
- `03_VERSION_EXECUTION_CHECKLISTS.md`：提供每个版本的执行清单，当前重点是 v1ab。
- `04_VIVADO_OPERATION_GUIDE.md`：说明 Vivado `.xpr`、Add Sources、Synthesis、Implementation、Generate Bitstream。
- `05_EXPERIMENT_TEST_GUIDE.md`：说明上板接线、安全幅度和示波器观察。
- `06_CODEX_GPT_WORKFLOW.md`：说明 Codex/GPT 协作方式。
- `07_DOCUMENT_CLEANUP_SUMMARY.md`：说明旧文档如何被合并。
- `08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES.md`：规定后续必须用教学型方式推进。
- `LESSON_v1ab_passthrough_debug.md`：v1ab 教学型课程文档，解释 v1ab 为什么不是 MTS error。

### 2.2 和当前 v1 测试直接有关的文档

最直接相关：

```text
docs\board_tests\BOARD_TEST_v1ab_passthrough_debug.md
docs\integration\INTEGRATION_PLAN_v1ab_passthrough_debug.md
docs\integration\PATCH_GUIDE_v1ab_passthrough_debug.md
docs\reports\REPORT_v1ab_passthrough_debug.md
docs\reports\REPORT_apply_patch_v1ab_passthrough_debug.md
docs\reports\REPORT_fix_dac_mux_use1_apply.md
docs\reports\REPORT_lesson_v1ab_passthrough_debug.md
docs\reports\REPORT_workspace_merge_to_v094.md
docs\reports\REPORT_workspace_rtl_migration_done.md
docs\reports\FIX_PLAN_dac_mux_use1_bitstream.md
```

作用概述：

- `BOARD_TEST_v1ab_passthrough_debug.md`：v1ab 上板测试 SOP。
- `INTEGRATION_PLAN_v1ab_passthrough_debug.md`：说明如何把 `laser_lock_core` 接入 top。
- `PATCH_GUIDE_v1ab_passthrough_debug.md`：解释 patch 修改位置。
- `REPORT_v1ab_passthrough_debug.md`：记录 v1ab RTL/testbench 生成和仿真。
- `REPORT_apply_patch_v1ab_passthrough_debug.md`：记录 patch 应用情况。
- `FIX_PLAN_dac_mux_use1_bitstream.md`：分析 USE=1 时 DAC mux 修正方案。
- `REPORT_fix_dac_mux_use1_apply.md`：记录 DAC mux 最小修正已应用。
- `REPORT_workspace_merge_to_v094.md` / `REPORT_workspace_rtl_migration_done.md`：记录 RTL 从项目资料库汇总到当前 `v0.94\rtl` 的过程。

### 2.3 学习类文档

这些文档适合 FPGA 初学者理解官方工程，不一定是当前操作入口：

```text
docs\learning\L01_top_overview.md
docs\learning\L02_adc_path.md
docs\learning\L03_dac_path.md
docs\learning\L04_clock_reset.md
docs\beginner_roadmap\00_README_beginner_roadmap.md
docs\beginner_roadmap\01_overall_workflow_for_beginner.md
docs\beginner_roadmap\02_codex_gpt_workflow.md
docs\beginner_roadmap\03_vivado_basic_operation_sop.md
docs\beginner_roadmap\04_simulation_sop.md
docs\beginner_roadmap\05_integration_to_redpitaya_top_sop.md
docs\beginner_roadmap\06_board_test_sop_v1ab.md
docs\beginner_roadmap\07_experiment_signal_checklist.md
docs\beginner_roadmap\08_error_debug_checklist.md
docs\beginner_roadmap\09_version_stage_plan.md
docs\beginner_roadmap\10_beginner_glossary.md
docs\beginner_roadmap\11_redpitaya_hardware_quickref.md
docs\beginner_roadmap\12_key_signals_cheatsheet.md
```

作用概述：

- `L01-L04`：分别解释 top、ADC 路径、DAC 路径、clock/reset。
- `beginner_roadmap`：面向新手的 Vivado、仿真、集成、上板、排查流程。

### 2.4 旧思路 / 历史文档

这些文件保留为历史记录，不建议作为当前唯一依据：

```text
docs\old\00_project_goal.md
docs\old\01_official_top_learning.md
docs\old\02_adc_signal_path.md
docs\old\03_dac_signal_path.md
docs\old\04_scope_asg_pid_reuse_analysis.md
docs\old\05_mts_demod_architecture.md
docs\old\06_integration_plan.md
docs\old\07_board_test_sop.md
docs\current\00_CONTEXT_FROM_GPT.md
docs\current\01_PROJECT_MASTER_PLAN.md
docs\current\02_TOP_LEARNING_OUTLINE.md
docs\current\03_CODEX_RULES.md
docs\current\04_EXPERIMENT_DRIVEN_IMPLEMENTATION_PLAN.md
```

结论：这些文档中有些思想仍有参考价值，但当前主线已由 `docs\project_master` 统一。后续不要再从 old/current 文档直接推导操作，除非用于查历史原因。

### 2.5 后续 v2/v3/v4/v5 才需要的文档或内容

这些内容当前不要进入开发：

- `v2_fpga_pid`：只有 v1g 以后才考虑；
- `v3_fpga_sweep`：当前不做 sweep；
- `v4_lock_relock_fsm`：当前不做自动锁定；
- `v5_ai_assisted_locking`：当前不做 AI；
- `pid_lock_core.sv` 和 `tb_pid_lock_core.sv` 目前都是空壳，不是当前可用成果；
- `mixer_core.sv` / `lpf_core.sv` / `adc_frontend.sv` 目前也是空壳，不代表已经实现 v1c/v1d/v1f。

### 2.6 报告类文档

`docs\reports` 中大量文件是操作记录和排查记录。重要报告包括：

- `REPORT_bitstream_failed_PDRC158.md`：记录曾经 bitstream 失败，DRC PDRC-158，当前判断不优先怀疑 `laser_lock_core` 逻辑。
- `REPORT_use0_bitstream_success_timing_warning.md`：记录官方 baseline 和 `USE_LASER_LOCK_CORE=0` 可 bitstream 成功，但 USE=0 不是 v1ab 测试 bit。
- `REPORT_compare_top_official_vs_dev.md`：比较官方 top 和开发 top，指出 v1ab 预期修改和曾经出现的非预期修改。
- `FIX_PLAN_dac_mux_use1_bitstream.md` / `REPORT_fix_dac_mux_use1_apply.md`：说明 DAC mux 修正方向，当前开发 top 中 DAC B 保持官方路径。
- `REPORT_project_master_consolidation.md` / `REPORT_project_master_revision_after_gpt_review.md`：记录主线文档整理。

## 3. RTL 总览

### 3.1 `laser_lock_core.sv`

状态：有实际逻辑。

作用：

```text
OUTPUT_MODE = 0: pd_i  -> output_protect -> error_o
OUTPUT_MODE = 1: ref_i -> output_protect -> error_o
default: 0
control_o = 14'sd0
```

和当前 v1 测试关系：

- 这是当前 v1ab 的核心模块；
- 用于验证 `IN1 -> OUT1` 和 `IN2 -> OUT1`；
- 不实现 mixer、LPF、BPF、PID、sweep、AI。

### 3.2 `output_protect.sv`

状态：有实际逻辑。

作用：

- `rstn_i=0` 时输出 0；
- `enable_i=0` 时输出 0；
- `enable_i=1` 时寄存输出 `data_i`。

和当前 v1 测试关系：

- v1ab 使用它保护 `error_o`；
- 现在只做基本 reset/enable 保护，不做宽位宽 saturation。

### 3.3 `red_pitaya_top_laser.sv`

状态：有实际 top 副本/变体。

作用：

- 基于 Red Pitaya 官方 top；
- 模块名是 `red_pitaya_top_laser`；
- 包含 v1ab 接入逻辑；
- 将 `adc_dat[0]` 接到 `pd_i`；
- 将 `adc_dat[1]` 接到 `ref_i`；
- 将 `laser_error` 接入 DAC A 路径。

注意：

- 该文件位于项目资料库 `redpitaya_laser_lock_project\rtl`；
- 当前 Vivado 实际 top 根据主线文档应是：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

- `red_pitaya_top_laser.sv` 是否曾被 Vivado 使用，需要人工确认；
- 当前开发 top 中已有更保守的 DAC mux 修正，而 `red_pitaya_top_laser.sv` 仍保留旧式 `dac_b_sum = 15'sd0` 写法，因此不能把它直接视为当前最终 top。

### 3.4 空壳 RTL 文件

以下文件存在，但长度为 0，当前没有实际逻辑：

```text
adc_frontend.sv
lpf_core.sv
mixer_core.sv
mts_demod_core.sv
pid_lock_core.sv
```

含义：

- `mixer_core.sv` 空壳：说明 `v1c_mixer_only` 尚未实现；
- `lpf_core.sv` 空壳：说明 `v1d_mixer_lpf` 尚未实现；
- `adc_frontend.sv` 空壳：说明 DC remove / BPF / gain 尚未实现；
- `mts_demod_core.sv` 空壳：说明完整 MTS 解调封装尚未实现；
- `pid_lock_core.sv` 空壳：说明 FPGA PID 尚未实现。

### 3.5 当前 top 文件是哪一个

按项目主线文档，当前实际 Vivado 开发 top 应该是：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

本次检查该文件的关键信号，看到：

```text
module red_pitaya_top
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 0
i_laser_lock_core
pd_i  = adc_dat[0]
ref_i = adc_dat[1]
error_o = laser_error
control_o = laser_control
dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser : dac_a_sum_official
dac_b_sum = dac_b_sum_official
```

需要人工确认：

- Vivado `.xpr` 当前 top 是否确实是 `red_pitaya_top`；
- Vivado Sources 中是否使用 `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv`；
- 是否没有误用 `redpitaya_laser_lock_project\rtl\red_pitaya_top_laser.sv`。

### 3.6 ADC 输入路径

从当前 top 和学习文档可整理为：

```text
adc_dat_i[0] / adc_dat_i[1]
  -> adc_dat_raw[0] / adc_dat_raw[1]
  -> signed/negative-slope conversion
  -> adc_dat[0] / adc_dat[1]
```

关键代码关系：

```text
adc_dat_raw[0] = adc_dat_i[0][15:2]
adc_dat_raw[1] = adc_dat_i[1][15:2]

adc_dat[0] <= digital_loop ? dac_a : converted adc_dat_raw[0]
adc_dat[1] <= digital_loop ? dac_b : converted adc_dat_raw[1]
```

当前项目候选对应关系：

```text
adc_dat[0] -> IN1 候选 -> pd_i
adc_dat[1] -> IN2 候选 -> ref_i
```

注意：IN1/IN2 和 `adc_dat[0]/adc_dat[1]` 的物理对应关系需要通过上板示波器测试最终确认。

### 3.7 DAC 输出路径

当前 top 中 DAC 路径可整理为：

```text
laser_error
  -> sign extend to 15-bit dac_a_sum_laser
  -> dac_a_sum
  -> official saturation
  -> dac_a
  -> signed-to-unsigned / negative-slope conversion
  -> dac_dat_a
  -> ODDR
  -> dac_dat_o
  -> OUT1 候选
```

当前开发 top 中 DAC B：

```text
dac_b_sum = dac_b_sum_official
```

也就是说，当前更保守方案保持 DAC B 官方路径，不用 v1ab 强制清零 DAC B。

需要人工确认：

- `dac_a` 物理上是否对应 OUT1；
- `dac_b` 物理上是否对应 OUT2；
- 示波器上 OUT1/OUT2 是否和代码预期一致。

### 3.8 IN1 / IN2 / OUT1 / OUT2 如何对应

当前候选映射：

```text
IN1  -> adc_dat[0] -> pd_i
IN2  -> adc_dat[1] -> ref_i
OUT1 <- DAC A path <- dac_a <- dac_a_sum <- laser_error
OUT2 <- DAC B path <- dac_b <- dac_b_sum
```

重要限制：

- 这是根据代码和文档得出的候选映射；
- 必须通过真实上板测试确认；
- 当前不能把该映射当作已经被物理实验完全验证。

## 4. scripts 总览

### 4.1 构建脚本

未发现可执行构建脚本。

当前只有：

```text
scripts\notes_build_steps.md
```

但该文件没有提供可执行 build 命令。

结论：当前 Vivado 构建流程主要依赖手动 Vivado 操作和文档 SOP，而不是脚本自动化。

### 4.2 上传脚本

未发现 `scp` 上传脚本。

`.bit.bin` 上传到 Red Pitaya 的过程在文档和报告中出现，但 scripts 目录没有可复用脚本。

### 4.3 测试脚本

未发现自动运行 testbench 的脚本。

仿真入口需要人工确认使用哪种工具，例如 Vivado simulator、iverilog 或其他 SystemVerilog 仿真器。当前仅有 testbench 源文件。

### 4.4 当前可能不可用的脚本

由于没有可执行脚本，不能说存在“可用脚本”。`notes_build_steps.md` 更像占位或笔记，需要人工补充。

## 5. sim 总览

### 5.1 当前有没有 testbench

有。

当前有效 testbench：

```text
sim\tb_laser_lock_core_v1ab.sv
sim\tb_laser_lock_core.sv
```

空壳 testbench：

```text
sim\tb_mixer_core.sv
sim\tb_pid_lock_core.sv
```

### 5.2 有没有仿真入口

有 testbench 文件，但没有发现统一仿真脚本或 Makefile。

需要人工确认：

- 用 Vivado simulator 运行；
- 还是用其他支持 SystemVerilog 的仿真器运行；
- `laser_lock_core.sv` 和 `output_protect.sv` 的编译顺序如何指定。

### 5.3 是否能验证 `IN1 -> OUT1` 或 `IN2 -> OUT2`

不能完整验证物理 `IN1 -> OUT1`。

当前 `tb_laser_lock_core_v1ab.sv` 能验证：

```text
OUTPUT_MODE=0: pd_i  -> error_o
OUTPUT_MODE=1: ref_i -> error_o
control_o = 0
reset 后输出为 0
```

它不能验证：

- ADC 物理输入；
- `adc_dat_i -> adc_dat_raw -> adc_dat` 完整 top 路径；
- DAC A/B saturation 后真实输出；
- ODDR；
- `dac_dat_o`；
- BNC OUT1/OUT2；
- 真实 1 kHz 或 4.6 MHz 信号链路。

关于用户问题中的 `IN2 -> OUT2`：

- 当前 v1ab 设计目标不是 `IN2 -> OUT2`；
- 当前 v1ab 目标是 `IN2 -> OUT1`；
- `control_o` 固定为 0，当前不应期待 OUT2 输出 REF 直通。

## 6. 当前工程能否作为候选 v1

明确判断：

```text
部分可以
```

理由：

### 可以作为候选 v1 的部分

- v1ab 核心 RTL 已有实际逻辑；
- v1ab testbench 已能验证 `pd_i/ref_i -> error_o`；
- 当前开发 top 中已经有 `i_laser_lock_core` 接入；
- 当前开发 top 中 `USE_LASER_LOCK_CORE=1'b1`、`LASER_LOCK_OUTPUT_MODE=0`；
- 当前开发 top 中 DAC A 使用更保守 mux，DAC B 保持官方路径；
- 文档已经清楚说明当前不做 PID、EOM、D2-125、AI；
- 已有主线文档、执行清单、实验测试指南。

### 还不能作为正式 v1 的原因

- 没有真实完成 `IN1 -> OUT1` 示波器上板验证；
- 没有真实完成 `IN2 -> OUT1` 示波器上板验证；
- `mixer_core.sv` 为空，`v1c` 未实现；
- `lpf_core.sv` 为空，`v1d` 未实现；
- `adc_frontend.sv` 为空，`v1f` 未实现；
- 没有可复现自动 build/upload/test 脚本；
- `red_pitaya_top_laser.sv` 与当前实际开发 top 状态可能不完全一致；
- `experiment_logs` 基本为空，没有实验复现记录。

所以当前更准确的定位是：

```text
候选 v1ab 工程骨架已经形成；
正式 v1 还没有形成；
v0.94 只能作为候选 v1 的基础，不应移动到 version\v1。
```

## 7. 如果要把 v0.94 整理成正式 v1，需要做哪些最小修改

注意：以下是建议，不是本次执行内容。

### 7.1 最小代码/工程确认

1. 人工确认 Vivado `.xpr` 当前 top 是 `red_pitaya_top.sv`。
2. 人工确认 Vivado Sources 中包含：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

3. 人工确认 Vivado 使用的是当前开发区 top，而不是项目资料库中的 `red_pitaya_top_laser.sv`。
4. 保持 `USE_LASER_LOCK_CORE=1'b1`。
5. 先保持 `LASER_LOCK_OUTPUT_MODE=0` 完成 `IN1 -> OUT1`。
6. `IN1 -> OUT1` 通过后，再改 `LASER_LOCK_OUTPUT_MODE=1`，重新 bitstream/bit.bin/upload/load，完成 `IN2 -> OUT1`。

### 7.2 最小实验确认

1. `IN1 -> OUT1`：

```text
1 kHz sine
100 mVpp
0 V offset
OUT1 -> 示波器
```

2. `IN2 -> OUT1`：

```text
4.6 MHz sine
100 mVpp 到 500 mVpp 起步
0 V offset
严禁 6.32 Vpp 直接进 IN2
OUT1 -> 示波器
```

3. 记录示波器结果：

- 是否同频；
- 幅度；
- 是否反相；
- 是否削顶；
- 是否顶死；
- OUT2 是否异常。

### 7.3 最小文档/复现整理

1. 在 `experiment_logs` 中新增真实实验记录。
2. 记录实际 bitstream 文件名、生成时间、`.bit.bin` 路径。
3. 记录 `scp` 上传目标路径。
4. 记录 `fpgautil` 命令和输出。
5. 记录 Red Pitaya 连接方式，例如 `rp-f0cb13.local` 是否可用。
6. 记录示波器接线和测试截图/文字结果。

### 7.4 暂时不需要做的事

- 不需要实现 `mixer_core.sv`；
- 不需要实现 `lpf_core.sv`；
- 不需要实现 `adc_frontend.sv`；
- 不需要实现 PID；
- 不需要接 D2-125；
- 不需要做 AI；
- 不需要移动到 `version\v1`。

## 8. 明天实验前最应该确认的 10 件事

1. Red Pitaya 是否能通过 SSH 连接，例如 `rp-f0cb13.local` 或实际 IP。
2. 当前板上是否仍然加载着目标 `.bit.bin`；如果重启/断电，需要重新 `fpgautil`。
3. 不要打开可能覆盖 FPGA bitstream 的 Red Pitaya 官方网页应用。
4. 当前 `.bit.bin` 是否对应 `USE_LASER_LOCK_CORE=1'b1`、`LASER_LOCK_OUTPUT_MODE=0`。
5. 信号发生器输出先在示波器上确认：`1 kHz sine, 100 mVpp, 0 V offset`。
6. `IN1 -> OUT1` 接线是否正确：信号发生器 OUT 到 IN1，OUT1 到示波器 CH1，输入参考到 CH2。
7. 示波器触发源、时间档、电压档是否适合 1 kHz / 100 mVpp。
8. OUT1/OUT2 是否接反，BNC 线是否正常。
9. 不接 D2-125，不接真实 PD，不接 EOM，不接激光器反馈。
10. 测完 `IN1 -> OUT1` 后，不要直接进入 mixer；先记录结果，再准备 `OUTPUT_MODE=1` 的新 bitstream 测 `IN2 -> OUT1`。

## 9. 风险清单

### 9.1 信号幅度风险

风险：

- 输入信号过大可能导致 ADC 饱和或硬件风险；
- 输出信号过大可能导致后级设备风险。

当前控制：

- `IN1 -> OUT1` 第一次使用 `1 kHz sine, 100 mVpp, 0 V offset`；
- `IN2 -> OUT1` 第一次建议 `100 mVpp` 到 `500 mVpp`。

需要人工确认：

- Red Pitaya 当前输入量程/跳线/设置；
- 信号发生器是否为高阻/50 ohm 标定差异导致实际幅度变化。

### 9.2 REF 输入风险

风险：

- 原模拟 mixer REF 约 `6.32 Vpp`，不能直接进 `IN2`；
- 4.6 MHz 接线和示波器探头带宽/衰减设置可能导致读数误解。

当前控制：

- 文档明确禁止 `6.32 Vpp` 直接进 `IN2`；
- 建议第一次 `100 mVpp` 到 `500 mVpp`。

需要人工确认：

- 衰减器实际衰减倍数；
- 进板前 REF 的真实幅度。

### 9.3 ADC 饱和风险

风险：

- `adc_dat[0]` 或 `adc_dat[1]` 可能已经饱和，但示波器只看 OUT1 时不一定第一时间发现。

当前控制：

- 先用低幅度信号；
- 观察 OUT1 是否削顶/顶死。

需要人工确认：

- 是否可通过 Red Pitaya scope 或其他方式查看 ADC 原始输入。

### 9.4 DAC 输出风险

风险：

- DAC 路径包含 saturation、signed-to-unsigned、negative-slope conversion 和 ODDR；
- OUT1 可能反相、幅度不同或有 offset；
- 不能把 `error_o` 数字值直接理解为物理电压。

当前控制：

- OUT1 只接示波器；
- 不接 D2-125；
- 不接激光反馈。

需要人工确认：

- DAC A 是否对应 OUT1；
- DAC B 是否对应 OUT2。

### 9.5 top 文件风险

风险：

- 项目资料库中存在 `rtl\red_pitaya_top_laser.sv`；
- 当前实际 Vivado top 应是 `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv`；
- 两者不完全相同，可能混淆。

当前控制：

- 文档主线推荐使用当前开发工程 `v0.94\rtl\red_pitaya_top.sv`。

需要人工确认：

- Vivado `.xpr` 的 top 设置；
- Vivado Sources 中实际使用的 top 文件路径。

### 9.6 bit/bin 路径风险

风险：

- `.bit` 和 `.bit.bin` 不是同一个文件；
- 可能误加载旧版本；
- `USE_LASER_LOCK_CORE=0` 的 bit 不是 v1ab 测试 bit；
- `LASER_LOCK_OUTPUT_MODE=0` 和 `1` 需要分别生成不同 bitstream。

当前控制：

- 文档记录了当前 `OUTPUT_MODE=0` 已加载成功；
- `IN2 -> OUT1` 前必须重新生成 `OUTPUT_MODE=1`。

需要人工确认：

- 当前 `.bit.bin` 文件名、时间戳、来源；
- 上传到 Red Pitaya 的路径是否正确。

### 9.7 `fpgautil` 加载风险

风险：

- `fpgautil` 成功只说明 FPGA 临时加载成功，不代表实验通路通过；
- 断电/重启会丢失配置；
- 官方网页应用可能覆盖 FPGA 配置。

当前控制：

- 已记录成功输出：

```text
BIN FILE loaded through FPGA manager successfully
```

需要人工确认：

- 板子是否重启过；
- 是否打开过官方应用；
- 当前 FPGA 是否仍是目标 bitstream。

### 9.8 `rp-f0cb13.local` 连接风险

风险：

- mDNS 名称可能解析失败；
- IP 可能变化；
- SSH 连接可能中断；
- 网络和供电问题可能导致板子重启。

需要人工确认：

- `rp-f0cb13.local` 当前是否能 ping/ssh；
- 若不能，实际 IP 是多少；
- SSH 用户、路径、权限是否正确。

## 10. 最终审查结论

当前工程结论：

```text
当前 v0.94 工程“部分可以”作为候选 v1 基础。
但它还不是正式 v1。
不要移动到 version\v1。
```

原因：

- v1ab 代码骨架、testbench、top 接入和 bitstream 流程已经有成果；
- 但最关键的物理实验验证还没有完成；
- v1c/v1d/v1f/v2 等后续模块目前为空壳或未实现；
- scripts/experiment_logs 尚未形成可复现工程闭环。

当前下一步只应该做：

```text
v1ab IN1 -> OUT1 示波器实验
```

然后再做：

```text
v1ab IN2 -> OUT1 示波器实验
```

只有这两步都通过，才允许讨论 `v1c_mixer_only`。
