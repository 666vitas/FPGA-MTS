# 08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES

## 0. 本文件作用

本文件规定后续所有 Codex 生成的文档、代码说明、`REPORT`、`BOARD_TEST`、`DEBUG_PLAN`，都必须以“教学型项目开发”为目标。

本项目的目标不是只完成代码，也不是让 AI 替我把 FPGA 工程黑箱式改完。真正目标是：通过 Red Pitaya + MTS 激光稳频项目，系统掌握 FPGA 开发、Verilog/SystemVerilog、Vivado 工程流、上板测试、以及激光稳频实验链路。

所以后续每一步都必须回答：

```text
这一步为什么做？
它对应实验中的哪段物理链路？
它在 FPGA 中变成了哪些硬件连接？
Vivado 为什么要这样操作？
示波器上应该看到什么？
失败时怎么一步步定位？
```

当前统一教学主线：

```text
先完成 v1ab IN1->OUT1 和 IN2->OUT1，
再进入 v1c mixer，
最终 v1 完成 PD/REF 数字 MTS error signal。
```

当前实际阶段是 `v1ab_passthrough_debug`。它不是 MTS error 课程，而是 FPGA 输入输出硬件链路课程。

当前实际进度是：RTL、testbench、Vivado synthesis / implementation / bitstream、`.bit.bin` 转换、上传和 `fpgautil` 加载已经完成；终端已显示 `BIN FILE loaded through FPGA manager successfully`。但是还没有接信号发生器和示波器完成物理波形验证。

因此，当前教学重点不是 mixer，而是让学习者真正理解并完成：

```text
Step 1: IN1 -> ADC -> FPGA core -> DAC -> OUT1
Step 2: IN2 -> ADC -> FPGA core -> DAC -> OUT1
```

## 1. 后续每个版本必须回答的 8 个问题

每个版本必须回答：

1. 这个版本解决哪个实验物理问题？
2. 它对应 MTS 实验链路的哪一段？
3. 它在 FPGA 里对应哪些输入、输出、时钟、复位？
4. 它对应哪些 Verilog 模块？
5. 每个模块在硬件上等价于什么电路？
6. Vivado 为什么要这样操作？
7. 示波器上应该看到什么？
8. 如果看不到，如何判断是代码问题、Vivado 问题、bitstream 问题、板子问题、接线问题，还是实验信号问题？

还必须额外回答：

9. 为什么现在不能跳到下一阶段？
10. 这一阶段学完后，我应该真正学会什么？

这些问题不能只用一句话糊弄。每个版本都要像老师带研究生做项目一样，把“为什么”和“怎么判断”讲清楚。

## 2. 每个版本的固定文档模板

以后每个版本，例如 `v1ab`、`v1c`、`v1d`，都必须生成一个教学文档：

```text
docs\project_master\version_lessons\LESSON_vX_xxx.md
```

模板如下：

```text
# LESSON_vX_xxx

## 0. 本版本一句话目标

例如：
v1ab 的目标不是产生 MTS error，而是验证 IN1/IN2 到 OUT1 的 FPGA 输入输出通路。

## 1. 对应的真实实验链路

用 MTS 实验语言说明：
PD、REF、BPF、mixer、LPF、D2-125 中，本版本对应哪一部分。

## 2. 对应的 FPGA 数据通路

用 FPGA 语言说明：
adc_dat[0]、adc_dat[1]、laser_lock_core、error_o、dac_a_sum、OUT1 分别是什么。

## 3. 新手必须理解的概念

列出 5 到 10 个概念。
例如：
- FPGA 不是运行 Python；
- Verilog 描述的是硬件连接；
- bitstream 是 FPGA 配置；
- ADC 输入进来后是 signed 14-bit；
- DAC 输出不是直接 assign 到 BNC；
- reset 为什么重要；
- clock 为什么重要。

## 4. 本版本代码结构

列出本版本涉及哪些文件：
red_pitaya_top.sv
laser_lock_core.sv
output_protect.sv
tb_xxx.sv

每个文件说明：
- 文件作用；
- 我必须看懂哪里；
- 我可以暂时不懂哪里；
- 千万不要乱改哪里。

## 5. 逐段解释代码

不能只贴代码。
必须解释每段代码在硬件上是什么。

例如：
assign control_o = 14'sd0;

要解释为：
这不是“给变量赋值”，而是在硬件上把 control_o 这 14 根线固定接到 0。

## 6. Vivado 操作与原理

写清楚：
- Add Sources 是什么；
- Synthesis 是什么；
- Implementation 是什么；
- Generate Bitstream 是什么；
- 为什么仿真通过不等于上板通过；
- 为什么 bit.bin 加载后断电会丢失。

## 7. 实验测试步骤

写清楚：
- 接线；
- 信号发生器参数；
- 示波器通道；
- 预期波形；
- 成功标准；
- 失败排查。

## 8. 本版本学完后我应该掌握什么

用学习目标总结：
完成本版本后，我应该能解释什么、操作什么、判断什么。

## 9. 进入下一版本前的门槛

必须列出：
哪些实验现象确认后，才允许进入下一版本。

## 10. 给 GPT 审查的问题

列出需要 GPT 判断的问题。
```

## 3. 每次生成 RTL 必须配套“代码教学说明”

以后 Codex 每次生成或修改 RTL，必须同时生成：

```text
docs\project_master\code_explanations\EXPLAIN_<module_name>.md
```

每个代码说明必须包含：

1. 这个模块在实验链路里对应什么；
2. 这个模块在 FPGA 里输入输出是什么；
3. 每个端口解释；
4. 每个 `always_ff` / `always_comb` / `assign` 的大白话解释；
5. 这个模块在硬件上等价于什么；
6. `signed` / `unsigned` / 位宽为什么这样设计；
7. reset 后为什么要输出 0；
8. testbench 如何验证；
9. 上板时如何验证；
10. 后续版本会如何扩展。

例如：

```systemverilog
assign control_o = 14'sd0;
```

教学说明不能写成“把 `control_o` 赋值为 0”就结束。必须解释：

```text
在硬件上，这表示 control_o 的 14 根输出线被固定接到数字 0。
它不是 CPU 执行的一条语句，而是一种永久存在的硬件连接。
v1ab 阶段还没有 PID，所以 OUT2 不应该输出任何控制量。
```

## 4. 每次 Vivado 操作必须解释“为什么”

不能只写：

```text
点击 Run Synthesis。
```

必须写：

```text
Run Synthesis 是把 Verilog/SystemVerilog 变成 FPGA 逻辑门、触发器、DSP、LUT 等硬件网络。
如果这里失败，说明代码语法、模块连接、端口位宽、综合可实现性等在硬件综合层面有问题。
```

不能只写：

```text
Generate Bitstream。
```

必须写：

```text
Generate Bitstream 是把实现后的 FPGA 资源布局布线结果转换成可下载到 FPGA 的配置文件。
Red Pitaya OS 2.x 通常还需要进一步转换为 .bit.bin，并用 fpgautil 加载。
加载到 FPGA 后，这些配置会变成真实硬件连接；断电或重启后，FPGA 配置会丢失，需要重新加载。
```

Vivado 四个基础动作必须这样解释：

| 操作 | 教学解释 |
|---|---|
| `Add Sources` | 把 `.sv` 文件加入 Vivado 工程。文件在磁盘目录里，不等于 Vivado 会综合它。 |
| `Run Synthesis` | 把 HDL 描述转换成 FPGA 可实现的逻辑网络。 |
| `Run Implementation` | 把逻辑网络放入具体 FPGA 资源，并完成布局布线。 |
| `Generate Bitstream` | 把布局布线结果生成 FPGA 配置文件。 |

## 5. 每次实验测试必须区分六类问题

每次失败都必须分类排查：

1. 代码逻辑问题；
2. Vivado 编译/综合问题；
3. bitstream 加载问题；
4. Red Pitaya 板子连接/IP/SSH 问题；
5. 信号发生器/示波器接线问题；
6. 激光/MTS 实验物理信号问题。

排查时不能一上来就改代码。要先问：

```text
bitstream 是不是正确版本？
Vivado Sources 有没有加对文件？
Red Pitaya 有没有真的加载这个 bitstream？
输入信号有没有真的进 IN1/IN2？
示波器通道有没有接对？
实验物理信号本身是否存在？
```

六类问题的典型判断：

| 类型 | 典型现象 | 先查什么 |
|---|---|---|
| 代码逻辑问题 | 仿真输出不符合预期，或者硬件现象和设计逻辑矛盾 | testbench、端口连接、位宽、signed |
| Vivado 编译/综合问题 | Synthesis/Implementation 报错 | 完整 Vivado error、Sources、top |
| bitstream 加载问题 | Vivado 成功但板上无变化 | bit/bin 文件、fpgautil 命令、加载日志 |
| Red Pitaya 板子连接/IP/SSH 问题 | 无法连接或无法加载 | IP、SSH、系统版本、电源、网络 |
| 信号发生器/示波器接线问题 | OUT1 没波形或看错通道 | 线缆、触发、CH1/CH2、输入幅度 |
| 激光/MTS 实验物理信号问题 | 真实 PD/REF 不稳定或没有目标信号 | PD、EOM、REF、光路、扫描、锁点 |

## 6. 每个版本必须有“学习成果检查题”

每个版本最后必须有 5 到 10 个问题，用来检查我是不是真的懂了。

例如 `v1ab` 后必须能回答：

1. 为什么 `v1ab` 不是 MTS error？
2. `adc_dat[0]` 和 `pd_i` 的关系是什么？
3. `error_o` 为什么不能直接驱动 `dac_dat_o`？
4. 为什么 `OUT1` 波形可能反相？
5. 为什么断电后要重新 `fpgautil`？
6. 为什么不能一开始就接 `D2-125`？
7. 为什么 `IN1 -> OUT1` 通过后才能做 mixer？

这些问题不是考试形式主义。它们的作用是确认：我不是只会让 AI 生成代码，而是真的理解了 FPGA、Vivado 和实验链路。

## 7. 后续主线版本的学习目标

后续版本必须用教学目标来推进：

| 版本 | 学习目标 |
|---|---|
| `v1ab` | 学习 FPGA 输入输出通路，ADC/DAC/top/core/bitstream 基础。 |
| `v1c` | 学习数字乘法器、定点位宽、乘法缩放、DSP 资源。 |
| `v1d` | 学习数字低通滤波、IIR/FIR、lock-in 解调中的低通意义。 |
| `v1e` | 学习真实 PD/REF 信号和仿真信号的差别。 |
| `v1f_bpf_gain_enable` | 学习数字 BPF、gain、采样率、中心频率、带宽、滤波器系数。 |
| `v1g` | 学习 error signal 与 `D2-125` 的接口、电压范围、offset、安全输出。 |
| `v2` | 学习数字 PID、闭环控制、稳定性、饱和保护。 |
| `v3` | 学习 sweep/scan 生成、DAC 输出标定、`50 Hz` 扫频。 |
| `v4` | 学习状态机 FSM、自动找峰、锁定/失锁判断。 |
| `v5` | 学习 AI 峰识别、锁定状态分类、自动重锁策略。 |

每个版本完成后，都要能说清楚：

```text
我学会了什么硬件概念？
我学会了什么实验判断方法？
我学会了什么 Vivado 操作？
我现在能独立排查哪类问题？
```

## 8. 后续 Codex 输出的强制要求

以后每次 Codex 输出都必须：

- 中文；
- 小白教学；
- 不跳阶段；
- 明确当前版本门槛；
- 解释为什么；
- 写出硬件等价含义；
- 写出实验链路对应关系；
- 写出示波器应该看到什么；
- 写出 GPT 审查问题；
- 写出失败排查；
- 写出本版本学会了什么。

禁止输出风格：

- 只给代码，不解释原理；
- 只说“运行 Vivado”，不解释 Vivado 在做什么；
- 只说“接示波器”，不解释应该看到什么；
- 失败时直接乱改 RTL；
- 没通过当前版本就开始下一版本；
- `IN1 -> OUT1`、`IN2 -> OUT1` 没有真实上板通过就开始 mixer；
- 把 v1ab passthrough 说成已经产生 MTS error；
- 未到 `v1g` 就建议接 `D2-125`；
- 未到 `v1e` 就建议接真实 `PD/REF`；
- 把 AI 当成替代学习的黑箱。

## 9. 本文件如何被使用

以后每次开始新任务，Codex 必须先阅读：

```text
docs\project_master\00_PROJECT_FINAL_GOAL.md
docs\project_master\01_CURRENT_STATUS_SUMMARY.md
docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
docs\project_master\08_TEACHING_STYLE_FPGA_LASER_LOCK_RULES.md
```

然后再生成任何代码或文档。

如果任务涉及上板实验，还必须阅读：

```text
docs\project_master\05_EXPERIMENT_TEST_GUIDE.md
```

如果任务涉及 Codex/GPT 协作，还必须阅读：

```text
docs\project_master\06_CODEX_GPT_WORKFLOW.md
```

本文件以后就是项目的“教学风格总规则”。只要 Codex 的输出没有解释原理、没有对应实验链路、没有失败排查、没有学习目标，就不算合格输出。
