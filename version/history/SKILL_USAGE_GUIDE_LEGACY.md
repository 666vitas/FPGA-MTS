# Codex Skills 使用指南：Red Pitaya FPGA 激光稳频项目

## 0. 本文件作用

本文件说明 `.agents/skills` 中各个 Codex skill 在本项目中的正确用法。

本项目不是普通软件项目，而是：

```text
Red Pitaya STEMlab 125-14
  + FPGA / SystemVerilog / Vivado
  + MTS 调制转移光谱
  + PD signal / 4.6 MHz REF
  + BPF / mixer / LPF / PID
  + OUT1 / OUT2 / D2-125 servo / 示波器验证
```

所以使用 skill 时，不能只按“写代码快一点”的思路来用。每一个 skill 都必须服务于工程节奏：

```text
先读文档 -> 明确最小目标 -> 生成方案 -> 用户确认
  -> 仿真 -> 综合 -> 实现 -> bitstream -> bit.bin -> 上板 -> 示波器验证 -> 记录报告
```

当前项目实际资料库在：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

当前实际 Vivado 开发工程在：

```text
E:\new\fpga_lock\v94\v0.94
```

官方干净原版只读：

```text
E:\new\fpga_lock\v94\guanfang-v0.94\v0.94
```

## 1. 总原则

这些 skills 不是“让 AI 自动乱写代码”的工具，而是让 Codex 按工程流程工作。

对本项目来说，skill 的作用是让 Codex：

- 先理解项目结构；
- 先读已有文档；
- 先确认当前版本目标；
- 只做一个最小可测试目标；
- 写出 testbench 和报告；
- 遇到 Vivado 或上板问题时分层排查；
- 让用户在 FPGA / Vivado / 激光稳频上真正学会，而不是只拿到一堆看不懂的代码。

必须强调：

- 每次先读 `AGENTS.md`。如果当前目录没有 `AGENTS.md`，要明确报告“未找到”，再读取 `docs\agents`、`docs\project_master` 或项目已有规则文档；
- 每次只做一个最小可测试目标；
- 不允许一次性实现完整 MTS 锁频；
- 不允许不读文件就改代码；
- 不允许编造端口、路径、寄存器地址；
- 不允许把“使用某个 skill”理解成“允许自动大改 RTL”；
- 涉及 RTL、Vivado 工程、XDC/SDC、官方 top 敏感路径时，必须先给方案和风险说明，等用户明确确认后再改；
- 必须考虑 Red Pitaya ADC 输入范围和 DAC 输出范围，不能凭记忆或猜测接入信号；
- 必须先仿真、再综合、再实现、再生成 bitstream、再转换/加载 bit.bin、再上板、最后用示波器验证；
- 当前阶段不要直接用 Red Pitaya 驱动 EOM；
- 当前阶段不要直接把 OUT1 接入 D2-125，除非版本明确进入 `v1g_error_to_D2_125`，并且已经用示波器确认安全；
- 当前阶段不要把 FPGA 输出直接接激光器反馈；
- 不要把 `USE_LASER_LOCK_CORE=0` 的官方回退路径误认为 v1ab 测试 bit；
- 不要跳过 `IN1 -> OUT1` 和 `IN2 -> OUT1` 基础验证就进入 mixer。

### 1.1 硬件安全和电压边界

Red Pitaya 是真实硬件，不是仿真器。任何 skill 只要涉及上板、信号发生器、示波器、PD、REF、EOM、D2-125，都必须先检查电压和接线。

必须遵守：

- 不要让 AI 凭记忆给出“绝对安全电压”。真正接线前要查 Red Pitaya STEMlab 125-14 当前输入量程、跳线/配置、探头衰减和信号发生器输出设置；
- 第一次 v1ab 测试建议使用保守小信号，例如 `1 kHz sine, 100 mVpp, 0 V offset`；
- 原模拟 mixer REF 约 `6.32 Vpp`，禁止直接接入 Red Pitaya `IN2`；
- EOM 驱动约 `8.93 Vpp`，它不是 Red Pitaya 第一阶段输入信号，当前阶段不要让 Red Pitaya 驱动 EOM；
- `OUT1` 第一次只接示波器，不接 `D2-125`；
- `OUT2` 在 PID 阶段前不应该作为激光控制输出使用；
- 接入 `D2-125` 前，必须先用示波器确认 `OUT1` 幅度、offset、极性和是否削顶；
- 接真实 PD 和 4.6 MHz REF 前，必须先用示波器确认信号幅度安全；
- 任何“看起来没信号”的现象，都不能通过盲目增大输入幅度来解决。

FPGA 初学者要记住：Verilog 里的数字 `14'sd1000` 不是直接等于某个物理电压。它要经过 DAC 数据路径、板级模拟输出范围和外部接线，才会变成示波器上看到的电压。

### 1.2 初学者使用方法

如果你是 FPGA 新手，每次使用 skill 时都要让 Codex 同时回答三个问题：

1. 这个 skill 这次要帮我解决哪个最小问题？
2. 它会不会修改 RTL、Vivado 工程或实验接线？
3. 我应该如何用仿真、Vivado 和示波器确认它真的成功？

如果这三个问题答不清楚，就先不要进入写代码或上板步骤。

使用任何 skill 前，建议先读：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\00_PROJECT_FINAL_GOAL.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\01_CURRENT_STATUS_SUMMARY.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES.md
```

## 2. 每个 skill 的用途说明

### setup-matt-pocock-skills

#### 作用

为仓库配置 agent skills 所需的项目规则、issue tracker、triage 标签和 domain docs 位置。

#### 什么时候用

当第一次在这个项目里使用 `.agents/skills`，或者发现 Codex 不知道本项目的文档位置、问题管理方式、术语规则时使用。

例如：

```text
请使用 setup-matt-pocock-skills，帮我检查本项目是否已经配置 docs/agents、issue tracker、triage labels 和 domain docs。只生成配置文档，不修改 RTL。
```

#### 什么时候不要用

- 不要用它来写 FPGA 模块；
- 不要用它来诊断 Vivado 报错；
- 不要用它来生成 MTS mixer；
- 如果只是想了解项目结构，应优先用 `zoom-out`。

#### 推荐提示词

```text
请使用 setup-matt-pocock-skills 检查当前 Red Pitaya FPGA 项目的 agent skills 配置。
先读取 AGENTS.md、docs/agents、docs/project_master。
如果缺少配置，只生成文档草案，不修改 RTL、不运行 Vivado。
```

#### 本项目注意事项

本项目可能没有 GitHub issue tracker，而是用本地 Markdown 文档和报告管理任务。配置时要明确：

- 开发工程：`E:\new\fpga_lock\v94\v0.94`
- 项目资料库：`E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project`
- 主线文档：`docs\project_master`
- 报告：`docs\reports`
- 不要把官方干净原版当作可修改工作区。

### zoom-out

#### 作用

让 Codex 从更高层次解释项目结构、模块关系和当前代码区域的位置。

#### 什么时候用

刚打开项目、看不懂 `red_pitaya_top.sv`、不知道 ADC/DAC/laser_lock_core/Vivado 工程之间怎么连接时使用。

例如：

```text
请使用 zoom-out 读取当前项目结构，解释 Red Pitaya 官方 top、rtl、project、docs、redpitaya_laser_lock_project 分别是什么。不要修改任何文件。
```

#### 什么时候不要用

- 不要用它直接修 bug；
- 不要用它直接写 Verilog；
- 不要用它替代 Vivado 报错诊断；
- 如果已经明确要开发一个小模块，应转用 `tdd`。

#### 推荐提示词

```text
请使用 zoom-out。
我不熟悉这个 Red Pitaya FPGA 项目，请先读项目结构和 docs/project_master，给我一张从 IN1/IN2 到 laser_lock_core 再到 OUT1/OUT2 的模块地图。
只解释，不修改代码。
```

#### 本项目注意事项

必须把以下边界讲清楚：

- `guanfang-v0.94\v0.94` 是官方干净原版，只读；
- `v0.94` 是实际 Vivado 开发工程；
- `redpitaya_laser_lock_project` 是文档、报告、测试 SOP 和历史资料库；
- `v0.94\rtl` 里的 RTL 才是 Vivado 后续综合优先使用的位置。

### grill-with-docs

#### 作用

在已有文档基础上追问需求，澄清术语、目标、边界和版本范围。

#### 什么时候用

准备进入新版本，但需求还不够清楚时使用。

例如准备 `v1c_mixer_only` 前，先让 Codex 根据 `project_master` 追问：

- mixer 输入是 `pd_i/ref_i` 还是滤波后的信号；
- 第一次上板用 100 kHz/100 kHz 还是 4.6 MHz；
- 输出是否仍然只接 OUT1 示波器；
- 是否禁止接 D2-125。

#### 什么时候不要用

- 不要在 Vivado 正在报错时用它代替 `diagnose`；
- 不要在需求已经明确时反复追问；
- 不要让它边问边大改文档，除非用户明确允许。

#### 推荐提示词

```text
请使用 grill-with-docs。
目标是准备 v1c_mixer_only，但不要写 RTL。
请先读取 docs/project_master 和已有 v1ab 报告，然后一次只问我一个关键问题。
每个问题都给出你的推荐答案，并说明为什么。
```

#### 本项目注意事项

追问时必须围绕 MTS 真实链路：

```text
PD -> BPF/gain -> mixer with 4.6 MHz REF -> LPF -> error -> OUT1/D2-125
```

还必须持续确认安全边界：

- REF 不能以 6.32 Vpp 直接进 IN2；
- OUT1 先接示波器；
- 不直接驱动 EOM；
- 不直接接激光器反馈。

### grill-me

#### 作用

让 Codex 像答辩老师一样追问用户的计划，直到方案逻辑清楚。

#### 什么时候用

当你已经有一个计划，但担心自己没想全时使用。

例如：

```text
我准备做 v1d_mixer_lpf，请使用 grill-me 追问我设计方案。重点问我 LPF 系数、位宽、reset、testbench 和上板验证。
```

#### 什么时候不要用

- 不要在你只是想让 Codex 读代码时使用；
- 不要在需要基于已有 docs 自动校对时优先使用，应使用 `grill-with-docs`；
- 不要在只想快速生成报告时使用。

#### 推荐提示词

```text
请使用 grill-me。
我准备实现 FPGA 数字混频后的 LPF。
请一次只问一个问题，并给出推荐答案。
重点检查 MTS 实验意义、FPGA 位宽、Vivado 风险和示波器验证方法。
```

#### 本项目注意事项

问题要问到硬件层：

- 这个模块对应哪段模拟电路；
- 输入输出是否 signed；
- ADC/DAC 位宽如何处理；
- reset 后输出为什么必须安全；
- 是否会影响 DAC 高速路径；
- 是否允许接 D2-125。

### diagnose

#### 作用

用“复现 -> 缩小 -> 假设 -> 观测 -> 修复 -> 回归”的流程诊断 bug、Vivado 错误或上板无输出问题。

#### 什么时候用

出现下面情况时使用：

- Vivado Synthesis 报错；
- Implementation 报 timing 或 DRC；
- Generate Bitstream 失败；
- `fpgautil` 加载失败；
- bit.bin 加载成功但 OUT1 没信号；
- IN1 通过但 IN2 不通过；
- 4.6 MHz REF 接入后波形异常。

#### 什么时候不要用

- 不要在需求还不清楚时用它写方案；
- 不要没有错误日志就开始猜；
- 不要直接修改 RTL，除非已经复现、定位，并得到用户允许。

#### 推荐提示词

```text
请使用 diagnose。
当前现象是：bit.bin 已经 fpgautil 加载成功，但 OUT1 没有 1 kHz 波形。
请不要修改 RTL，不要运行 Vivado。
请先按 bitstream 加载、Vivado bit 文件、代码参数、Red Pitaya 连接、信号发生器/示波器接线、实验物理信号六类问题建立排查清单。
```

#### 本项目注意事项

诊断必须保留分层思路：

1. 代码逻辑问题；
2. Vivado 编译/综合/实现问题；
3. bitstream / bit.bin 加载问题；
4. Red Pitaya 板子/IP/SSH 问题；
5. 信号发生器/示波器接线问题；
6. 激光/MTS 实验物理信号问题。

不能看到 OUT1 没信号就立刻改 `laser_lock_core.sv`。

### tdd

#### 作用

用测试驱动开发方式开发 FPGA 小模块：先写一个可验证行为，再写最小 RTL，通过后再扩展。

#### 什么时候用

写这些小模块时使用：

- ADC 到 DAC 直通；
- 数字 gain；
- DC remove；
- 数字 BPF；
- 数字 mixer；
- LPF；
- PID；
- sweep generator；
- lock/relock FSM。

#### 什么时候不要用

- 不要用它一次性写完整 MTS 锁频系统；
- 不要先写一大堆 testbench 再写所有 RTL；
- 不要用实现细节测试替代行为测试；
- 不要在未确认端口和位宽前开始写代码。

#### 推荐提示词

```text
请使用 tdd 开发 v1c_mixer_only。
先不要直接写完整 RTL。
请先列出一个最小行为测试：pd_i 和 ref_i 为 signed 14-bit 输入，输出为缩放后的 signed 14-bit mixer 结果。
如果我没有明确允许修改 RTL，请只生成 TDD 计划、testbench 设计和 RTL 修改方案，不要应用代码。
等我确认后，每次只做一个 red-green 小步骤，并生成 testbench、RTL、REPORT 和代码教学说明。
```

#### 本项目注意事项

FPGA TDD 要特别关注：

- signed / unsigned；
- 14-bit ADC/DAC 数据；
- 乘法后位宽会变大；
- 定点缩放不能靠感觉；
- reset 后输出必须安全；
- testbench 通过不等于上板通过；
- 上板前仍需 Vivado 综合/实现/bitstream；
- 上板后仍需示波器验证；
- 任何新模块第一次上板都要用安全小信号，不直接接 D2-125、EOM 或激光反馈。

### handoff

#### 作用

在一天实验或一轮开发结束时，把当前状态整理成下一次 Codex 能继续接手的交接文档。

#### 什么时候用

当天做完下面事情后使用：

- Vivado synthesis / implementation / bitstream；
- Red Pitaya 上板测试；
- 示波器观察；
- 发现一个复杂失败现象；
- 决定明天继续排查；
- GPT 已审查并给出下一步。

#### 什么时候不要用

- 不要用它替代正式 REPORT；
- 不要把所有旧文档复制一遍；
- 不要在还没做任何实质进展时生成冗长 handoff。

#### 推荐提示词

```text
请使用 handoff。
今天完成了 v1ab bit.bin 加载，但还没做示波器测试。
请生成下一次会话可继续的交接文档，引用已有 REPORT 和 LESSON，不重复复制全文。
```

#### 本项目注意事项

handoff 必须记录：

- 当前版本；
- 当前 bitstream 是否加载；
- `USE_LASER_LOCK_CORE` 和 `LASER_LOCK_OUTPUT_MODE`；
- 是否接过板子；
- 示波器看到什么；
- 是否接 D2-125；
- 下一步最小动作。

### triage

#### 作用

当问题很多时，按优先级和状态把任务分类，决定先处理哪一个。

#### 什么时候用

例如同时存在：

- OUT1 没信号；
- Vivado 有 timing warning；
- IN2 REF 幅度不确定；
- v1c mixer 需求还没定；
- 文档也需要整理。

这时使用 triage，先判断什么是 blocker。

#### 什么时候不要用

- 不要用它直接写代码；
- 不要用它替代实验安全判断；
- 不要在只有一个明确任务时使用。

#### 推荐提示词

```text
请使用 triage。
当前有多个任务：v1ab IN1->OUT1 上板测试、IN2 REF 安全衰减确认、v1c mixer 方案、Vivado timing warning 记录。
请按 blocker、风险、安全性和版本顺序排序，不要修改代码。
```

#### 本项目注意事项

排序原则应是：

```text
安全 > 当前版本阻塞 > 可复现实验现象 > 文档记录 > 下一版本功能
```

例如还没验证 v1ab OUT1，就不应该把 v1c mixer 排在前面。

### to-issues

#### 作用

把大计划拆成一组可以独立完成、可验证的小任务。

#### 什么时候用

把 `v1c_mixer_only`、`v1d_mixer_lpf`、`v1f_bpf_enable` 这种阶段拆成任务时使用。

例如：

- 写 mixer testbench；
- 写 mixer_core；
- 接入 laser_lock_core；
- Vivado synthesis；
- 低频同频上板；
- 4.6 MHz 上板；
- 写 BOARD_TEST 和 REPORT。

#### 什么时候不要用

- 不要把一个任务拆得只有文件级别、没有实验意义；
- 不要在项目没有 issue tracker 约定时直接发布 issue；
- 不要把高风险任务标成“可无人值守”，例如接 D2-125 或接激光反馈。

#### 推荐提示词

```text
请使用 to-issues。
把 v1c_mixer_only 拆成最小可验证任务。
每个任务必须有输入、输出、testbench、Vivado 操作、上板测试、成功标准和安全限制。
不要创建远程 issue，只生成本地 Markdown 任务清单。
```

#### 本项目注意事项

每个 issue 都要有硬件验证标准，不只是“代码写完”。

好的任务应该像：

```text
验证 100 kHz / 100 kHz 两路安全输入经过 mixer 后 OUT1 有可解释输出
```

而不是：

```text
写 mixer
```

### to-prd

#### 作用

把当前讨论和项目目标整理成 PRD，也就是需求文档。

#### 什么时候用

当要规划一个较大阶段时使用：

- `v1c_mixer_only` 需求；
- `v1f_bpf_enable` 数字滤波需求；
- `v2_fpga_pid` 闭环控制需求；
- `v4_lock_relock_fsm` 自动重锁需求；
- `v5_ai_assisted_locking` AI 辅助锁定需求。

#### 什么时候不要用

- 不要用它处理单个 Vivado 报错；
- 不要用它写临时 debug 记录；
- 不要把 PRD 当作已经验证的设计。

#### 推荐提示词

```text
请使用 to-prd。
基于 docs/project_master，把 v1f_bpf_enable 写成需求文档。
重点说明 MTS 实验问题、Red Pitaya ADC 采样率、4.6 MHz 中心频率、BPF 带宽、定点位宽、testbench、Vivado 和上板安全边界。
不要写 RTL。
```

#### 本项目注意事项

PRD 必须明确 out of scope：

- 不驱动 EOM；
- 不接激光器反馈；
- 未到 v1g 前不接 D2-125；
- BPF 系数不能照搬模拟 1.8 MHz HPF + 10 MHz LPF 参数。

### improve-codebase-architecture

#### 作用

在项目稳定后，分析模块边界、接口、测试结构，提出架构改进建议。

#### 什么时候用

只有当基础版本已经稳定后再用，例如：

- v1ab/v1c/v1d 已经能仿真和上板；
- `laser_lock_core` 里开始堆很多功能；
- BPF/mixer/LPF/PID 接口混乱；
- testbench 很难写；
- 文档和版本边界开始混在一起。

#### 什么时候不要用

- 不要在 v1ab 还没上板通过时做大重构；
- 不要为了“架构漂亮”改官方 top；
- 不要动 ODDR、PLL、ADC IO、PS/AXI/DDR；
- 不要优化还没验证过的功能。

#### 推荐提示词

```text
请使用 improve-codebase-architecture。
当前 v1ab/v1c/v1d 已经通过仿真和上板。
请只分析 laser_lock_core、mixer_core、lpf_core、bpf_core 的模块边界和 testbench 可测性，提出建议，不直接修改 RTL。
```

#### 本项目注意事项

本项目架构优化必须服从硬件事实：

- top 是官方工程的关键接线板，不应随意重构；
- DAC 高速路径尽量保持官方结构；
- 每个模块都要能映射到 MTS 链路；
- 每个模块都要能写 testbench；
- 每次重构后都要重新综合、实现、bitstream 和上板验证。

### prototype

#### 作用

做可丢弃原型，用来验证一个想法是否合理。

#### 什么时候用

适合在写正式 RTL 前验证概念，例如：

- 用 Python/Matlab 风格脚本试算 BPF 系数；
- 用小脚本模拟 mixer 位宽和缩放；
- 用离线数据测试 LPF 响应；
- 用状态机表格模拟 lock/relock FSM。

#### 什么时候不要用

- 不要把 prototype 当成可综合 RTL；
- 不要把临时脚本直接放进 Vivado；
- 不要用 prototype 跳过 testbench；
- 不要用 prototype 直接控制板子或激光器。

#### 推荐提示词

```text
请使用 prototype。
我想在写 RTL 前验证 v1c mixer 的定点缩放。
请生成一个可丢弃的离线计算原型，只用于比较 signed 14-bit 输入、乘法后位宽和缩放策略。
不要修改 RTL，不要运行 Vivado。
```

#### 本项目注意事项

原型只回答一个问题，例如“这个缩放会不会溢出”。回答完要把结论写入 REPORT 或 PRD，不要让临时代码变成正式工程的一部分。

### write-a-skill

#### 作用

为本项目创建新的专用 skill。

#### 什么时候用

当反复出现同类任务时使用，例如：

- Red Pitaya Vivado bitstream 排查 skill；
- MTS 实验上板安全检查 skill；
- FPGA 定点滤波器设计 skill；
- 示波器测试记录 skill。

#### 什么时候不要用

- 不要为了一个一次性任务创建 skill；
- 不要把项目文档直接复制成超长 skill；
- 不要让 skill 绕过项目主线文档。

#### 推荐提示词

```text
请使用 write-a-skill。
我想为本项目创建一个 red-pitaya-board-test skill。
它应该指导 Codex 在上板前检查 bit.bin、fpgautil、IN1/IN2 幅度、OUT1 示波器、禁止 D2-125 和 EOM。
先生成草案，不要修改 RTL。
```

#### 本项目注意事项

新 skill 应该短小、明确、可复用，并且引用：

```text
docs\project_master
docs\board_tests
docs\reports
```

不要把 Vivado 大段日志或所有教学文档塞进 `SKILL.md`。

### caveman

#### 作用

让 Codex 用极简短句输出，减少 token 和废话。

#### 什么时候用

适合快速状态同步：

- “现在只告诉我下一步做什么”；
- “只给我 Vivado 报错优先级”；
- “只列安全检查，不解释”。

#### 什么时候不要用

本项目大多数教学文档不要用它，因为用户目标是系统学习 FPGA 和激光稳频。

不要在这些场景使用：

- 新手教学；
- 版本 lesson；
- Vivado 原理解释；
- MTS 链路解释；
- D2-125 安全接入说明。

#### 推荐提示词

```text
请使用 caveman。
只用最短句告诉我 v1ab 上板前 10 项安全检查。
不要修改文件。
```

#### 本项目注意事项

如果涉及危险接线、D2-125、EOM、激光器反馈、输入过压，不能过度压缩到让安全信息变模糊。

## 3. 按开发阶段推荐使用哪个 skill

### 阶段 0：刚打开项目，看不懂结构

推荐使用：`zoom-out`

目标是建立地图：

```text
官方原版 -> 当前开发工程 -> 项目资料库 -> rtl -> docs -> sim -> Vivado project
```

不要急着改 `red_pitaya_top.sv`。

### 阶段 1：准备开发新功能，但需求不清楚

推荐使用：`grill-with-docs` 或 `grill-me`

如果已有项目文档，优先用 `grill-with-docs`。

如果是你自己的方案想被追问，用 `grill-me`。

### 阶段 2：写 FPGA 小模块

推荐使用：`tdd`

适用例子：

- ADC 到 DAC 直通；
- 数字增益；
- 数字带通滤波；
- 数字混频；
- 低通滤波；
- PID 输出。

每个模块都必须：

```text
先定义行为 -> 写 testbench -> 写最小 RTL -> 仿真 -> 集成 -> Vivado -> 上板
```

### 阶段 3：Vivado 报错、bitstream 失败、板子无输出

推荐使用：`diagnose`

必须先建立反馈环：

- 报错日志；
- failing path；
- DRC ID；
- Vivado run 状态；
- bit.bin 文件；
- fpgautil 输出；
- 示波器截图或文字记录。

### 阶段 4：问题很多，不知道先做哪个

推荐使用：`triage`

先判断：

```text
安全问题 > 当前版本 blocker > 能复现的问题 > 文档整理 > 后续功能
```

### 阶段 5：把大目标拆成小任务

推荐使用：`to-issues`

大目标例如：

```text
FPGA 产生真实 MTS error-like signal
```

应该拆成：

```text
v1ab -> v1c -> v1d -> v1e -> v1f -> v1g
```

不要一次性写完。

### 阶段 6：整理需求文档

推荐使用：`to-prd`

适合整理 `v1f_bpf_enable`、`v2_fpga_pid`、`v4_lock_relock_fsm` 这种中等以上阶段。

### 阶段 7：一天实验结束，保存上下文

推荐使用：`handoff`

记录：

- 今天做了什么；
- 哪个 bitstream；
- 是否加载成功；
- 示波器看到什么；
- 下一步是什么；
- 禁止事项是什么。

### 阶段 8：项目稳定后，才考虑架构优化

推荐使用：`improve-codebase-architecture`

只有已经有多个版本通过验证，且模块边界变复杂时才使用。

## 4. 我的项目专用工作流

启动 Codex 后，推荐流程：

1. 先用 `zoom-out` 读取项目结构。

   目的：确认当前在哪个目录、有哪些 RTL、哪些 docs、Vivado 工程在哪里、官方原版在哪里。

2. 再用 `grill-with-docs` 澄清本次目标。

   目的：确认当前只做哪个版本，哪些事情明确禁止，实验安全边界是什么。

3. 如果是写模块，用 `tdd`。

   目的：每次只写一个最小可测试行为，不一次性写完整 MTS 链路。没有用户明确确认时，只输出计划、testbench 设计和 patch 方案，不直接改 RTL。

4. 如果是排错，用 `diagnose`。

   目的：先复现和缩小问题，再决定是否改代码。

5. 如果任务太多，用 `triage`。

   目的：先处理安全和 blocker，不被后续功能诱惑。

6. 每天结束用 `handoff`。

   目的：让下一次会话知道今天做到哪里，不重新猜。

推荐完整 prompt：

```text
请按本项目 Codex Skills 工作流执行。
先用 zoom-out 读取项目结构和 docs/project_master。
再用 grill-with-docs 澄清本次最小目标。
如果本次是写 RTL 小模块，进入 tdd；如果是排错，进入 diagnose；如果任务太多，先 triage。
今天结束时生成 handoff。
全程不要跳阶段，不要编造端口，不要忽略 Red Pitaya ADC/DAC 安全范围。
涉及 RTL 或 Vivado 工程修改时，先给方案，等我确认后再应用。
```

## 5. 常用 prompt 模板

### 项目结构审查模板

```text
请使用 zoom-out。
先读取 AGENTS.md；如果没有，请说明未找到。
再读取 docs/agents、docs/project_master 和当前目录结构。
请解释这个 Red Pitaya FPGA 项目的目录角色：
官方干净原版、当前 Vivado 开发工程、项目资料库、rtl、sim、docs、reports。
只解释，不修改任何文件。
```

### Vivado 报错诊断模板

```text
请使用 diagnose。
当前 Vivado 报错如下：
[粘贴完整错误]

请不要直接修改 RTL。
请先判断属于 Synthesis、Implementation、DRC、Timing 还是 Bitstream 阶段。
按以下顺序排查：
1. 是否是文件未加入 Sources；
2. 是否是 top/端口/位宽/signed 问题；
3. 是否影响 DAC/ADC/PLL/ODDR 等敏感路径；
4. 是否与当前版本 v1ab/v1c/v1d 的修改有关；
5. 是否可以用官方 baseline 或 USE_LASER_LOCK_CORE=0 对比。
最后给出最小修正方案和禁止修改范围。
```

### ADC-DAC 直通开发模板

```text
请使用 tdd。
目标是开发或检查 ADC-DAC 直通版本。
当前只验证 IN1 -> ADC -> FPGA -> DAC -> OUT1，不做 MTS error。
请先写最小行为、testbench 计划和 RTL 修改方案，等待我确认后再修改代码。
必须说明 adc_dat[0]、pd_i、error_o、dac_a_sum、OUT1 的关系。
输入先用 1 kHz sine、100 mVpp、0 V offset 这类安全小信号。
不要接 D2-125，不接真实 PD，不接激光器反馈。
```

### 数字滤波模块开发模板

```text
请使用 tdd。
目标是开发数字滤波模块：[BPF 或 LPF]。
请先解释它对应 MTS 链路哪一段。
然后确认采样率、中心频率、带宽、定点位宽、输入输出 signed 格式。
先生成 testbench 计划和 RTL 方案，等待我确认后再生成最小 RTL。
BPF 系数必须根据数字采样率计算，不能照搬模拟 1.8 MHz high-pass + 10 MHz low-pass 参数。
未通过仿真、Vivado 和示波器验证前，不允许接 D2-125 或激光反馈。
```

### 数字混频模块开发模板

```text
请使用 tdd。
目标是 v1c_mixer_only。
输入为 pd_i 和 ref_i，均为 signed 14-bit。
输出为缩放后的 signed 14-bit error_o。
第一次上板测试先考虑 100 kHz / 100 kHz 安全同频信号，确认 mixer 链路后再切到 4.6 MHz。
请先写 testbench 行为和 RTL 修改方案，等待我确认后再写 RTL，并说明乘法位宽和缩放。
不要把 6.32 Vpp REF 直接接入 IN2。
```

### PID 模块开发模板

```text
请使用 grill-with-docs + tdd。
目标是 v2_fpga_pid。
请先读取 docs/project_master，确认 v1g 是否已经允许 OUT1 -> D2-125。
然后澄清 PID 输入 error_o、输出 control_o、OUT2 电压范围、enable、reset、饱和保护、积分限幅。
在未通过示波器和安全审查前，不允许接激光器反馈。
```

### 上板测试前安全检查模板

```text
请使用 diagnose 的分层检查方式，但不要排错，只做上板前检查清单。
当前版本是：[v1ab/v1c/v1d/...]
请检查：
bit.bin 是否是正确版本；
fpgautil 是否加载成功；
Red Pitaya 是否保持通电；
是否禁止打开官方网页应用；
IN1/IN2 输入幅度是否安全；
OUT1 是否只接示波器；
是否禁止 D2-125；
是否禁止 EOM；
是否禁止激光器反馈。
```

### 示波器测试记录模板

```text
请生成示波器测试记录 REPORT。
当前版本：[版本名]
bitstream/bit.bin：[文件名或生成时间]
fpgautil 输出：[粘贴]
接线：
信号发生器 OUT -> [IN1/IN2]
OUT1 -> 示波器 CH1
输入参考 -> 示波器 CH2
信号参数：
[频率、幅度、offset、波形]
示波器现象：
[频率、幅度、是否反相、是否削顶、是否有噪声]
请按成功/异常/下一步建议整理。
不要修改 RTL。
```

### 实验日报 handoff 模板

```text
请使用 handoff。
今天项目进展：
1. 当前版本：
2. 修改过的文件：
3. Vivado 结果：
4. bit.bin 是否加载：
5. fpgautil 输出：
6. 示波器结果：
7. 是否接 D2-125：
8. 是否接真实 PD/EOM/激光反馈：
9. 当前 blocker：
10. 下一次最小动作：

请生成交接文档，引用已有 REPORT，不重复全文。
```

## 6. 速查表

| 我现在遇到的问题 | 应该用哪个 skill | 不应该用哪个 skill | 复制给 Codex 的一句话 |
|---|---|---|---|
| 刚打开项目，不知道目录含义 | `zoom-out` | `tdd` | 请使用 zoom-out 解释当前 Red Pitaya FPGA 项目结构，只读不修改。 |
| 不知道 `red_pitaya_top.sv` 怎么接 ADC/DAC | `zoom-out` | `prototype` | 请使用 zoom-out 画出 IN1/IN2 到 laser_lock_core 再到 OUT1/OUT2 的数据通路。 |
| 准备做 v1c，但需求没想清楚 | `grill-with-docs` | `tdd` | 请使用 grill-with-docs，基于 docs/project_master 逐个问题澄清 v1c_mixer_only。 |
| 我有方案，想被追问 | `grill-me` | `to-prd` | 请使用 grill-me 追问我的 v1d LPF 方案，每次只问一个问题并给推荐答案。 |
| 要写数字 mixer | `tdd` | `improve-codebase-architecture` | 请使用 tdd 写 v1c mixer，先 testbench，再最小 RTL，并解释 signed 位宽和缩放。 |
| 要写 BPF/LPF | `tdd` | `caveman` | 请使用 tdd 开发数字滤波模块，先确认采样率、频率、带宽和定点位宽。 |
| Vivado Synthesis 报错 | `diagnose` | `to-prd` | 请使用 diagnose 分析这个 Synthesis 错误，先定位文件、端口、位宽和 Sources。 |
| Generate Bitstream 失败 | `diagnose` | `prototype` | 请使用 diagnose 分析 bitstream 失败，优先判断 DRC/timing/官方 baseline 对比。 |
| bit.bin 加载成功但 OUT1 没信号 | `diagnose` | `tdd` | 请使用 diagnose 按 bitstream、Vivado、代码参数、板子、接线、实验信号六类排查。 |
| 问题太多不知道先做哪个 | `triage` | `prototype` | 请使用 triage 按安全、blocker、当前版本、后续功能排序。 |
| 要把 v1f 拆成任务 | `to-issues` | `diagnose` | 请使用 to-issues 把 v1f_bpf_enable 拆成最小可验证任务，不发布远程 issue。 |
| 要写完整需求文档 | `to-prd` | `caveman` | 请使用 to-prd 为 v2_fpga_pid 生成需求文档，明确 out of scope 和安全边界。 |
| 今天实验结束，要保存上下文 | `handoff` | `zoom-out` | 请使用 handoff 生成下一次 Codex 可继续的交接文档，引用已有 REPORT。 |
| 想优化模块架构 | `improve-codebase-architecture` | `tdd` | 请使用 improve-codebase-architecture 分析模块边界，只提建议，不修改 RTL。 |
| 想先离线试算滤波器或位宽 | `prototype` | `to-prd` | 请使用 prototype 做可丢弃的定点位宽/滤波器系数试算，不进 Vivado。 |
| 想新增项目专用 skill | `write-a-skill` | `triage` | 请使用 write-a-skill 草拟 red-pitaya-board-test skill，先给草案。 |
| 只想要极简下一步 | `caveman` | `grill-with-docs` | 请使用 caveman，只列 v1ab 上板前 10 项安全检查。 |
| 准备接入真实 4.6 MHz REF | `diagnose` 或 `grill-with-docs` | `tdd` | 请先检查 IN2 REF 幅度和衰减方案，禁止 6.32 Vpp 直接进 IN2，不要写 RTL。 |
| 准备把 OUT1 接 D2-125 | `grill-with-docs` 或 `triage` | `caveman` | 请先审查 OUT1 幅度、offset、极性和版本门槛，未确认 v1g 前禁止接 D2-125。 |
| 想让 Codex 直接写完整锁频系统 | `to-issues` | `tdd` | 请先把完整 MTS 锁频目标拆成 v1ab 到 v5 的最小可验证任务，不要一次性写 RTL。 |

## 7. 最后提醒

本项目的核心学习路线不是“让 Codex 一口气写完锁频系统”，而是：

```text
v1ab: 学会 ADC/DAC/top/core/bitstream/示波器基础
v1c: 学会数字乘法器、定点位宽和 DSP 资源
v1d: 学会 mixer 后 LPF 和 lock-in 解调意义
v1e: 学会真实 PD/REF 与仿真信号的差别
v1f: 学会数字 BPF、采样率、中心频率、带宽和系数
v1g: 学会 error signal 与 D2-125 的安全接口
v2: 学会数字 PID 和闭环稳定性
v3: 学会 sweep/scan
v4: 学会 lock/relock FSM
v5: 学会 AI assisted locking
```

任何 skill 都不能跳过这个顺序。

每次使用 Codex，都要问一句：

```text
我这次是在验证哪个最小硬件事实？
```

如果这个问题答不清楚，就先不要写 RTL，也不要上板。
