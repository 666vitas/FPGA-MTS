# 02_CODEX_WORKFLOW_COMPLETE

## 0.0 当前项目 Vivado 操作边界（2026-06-15）

当前项目中，Codex 默认永远不操作 Vivado。即使独立 XSim 已通过，也不能自动运行：

```text
Vivado Add Sources
synthesis
implementation
Generate Bitstream
write_bitstream
生成 bit/bin
烧录 Red Pitaya
```

Vivado Add Sources、综合、实现、生成 bit/bin、烧录都由用户手动完成。Codex 只能给出手动操作清单、检查 RTL/SIM/MD、运行被明确允许的独立 XSim。

当前状态参见 [[STATUS]]。本文件合并自原 02_CODEX_GPT_WORKFLOW_RULES、05_CODEX_SKILL_PROMPT_PREFIX_RULES、06_TASK_ROUTER_RULES。

## 0. Codex 与 GPT 分工

```
Codex 负责：本地工程执行、证据整理、小步修改 RTL、生成 testbench、生成实验记录
GPT 负责：方案审查、物理解释、实验现象判断、下一步决策辅助
```

两者都不能跨阶段开发。

## 0.1 GPT / Codex / Claude Code 固定协作流程

为避免 GPT、Codex、Claude Code 对同一阶段反复审查、反复扩大范围，后续每个开发子阶段采用固定四轮流程：

```text
1. GPT 定义任务和通过标准
2. Codex 实现并完成独立仿真
3. Claude Code 集中静态审查一次
4. Codex 完成一次集中修正并回归仿真
```

四轮完成后必须关闭该子阶段。除非仍存在 `FAIL` 阻塞项，不再让 GPT 或 Claude Code 对同一版本重复逐行审查。

### 0.1.1 三者职责边界

GPT 是项目负责人，负责：

- 定义当前阶段的最小任务；
- 明确接口、范围、风险和通过标准；
- 判断是否允许进入下一阶段；
- 根据 Vivado 结果和实物实验结果分析问题。

GPT 不负责：

- 对同一份已由 Claude Code 审查的 RTL 再次完整逐行审查；
- 不断扩大当前阶段测试范围；
- 反复生成新的审查文档。

Codex 是主要执行工程师，负责：

- 修改实际工程代码；
- 编写 testbench；
- 运行独立仿真；
- 根据 Claude Code 的审查意见完成一次集中修正；
- 回归仿真；
- 后续在用户逐项批准后执行 Vivado 集成、综合、实现、bitstream；
- 更新 version 记录。

Claude Code 是独立审查员，负责：

- 对 Codex 本阶段代码进行一次集中静态审查；
- 将问题分为：必须修改、建议修改、可留到后续；
- 给出 `PASS`、`PASS WITH NOTES` 或 `FAIL`。

Claude Code 不负责：

- 无限增加测试；
- 反复创建审查文档；
- 将未来优化项作为当前阻塞项；
- 在 Codex 完成回归仿真后再次重复同一轮审查，除非仍有 `FAIL`。

### 0.1.2 审查结论定义

只允许以下三种审查结论：

- `PASS`：无阻塞问题，直接进入下一阶段。
- `PASS WITH NOTES`：存在非关键问题，记录到文档，但不能阻止进入下一阶段。
- `FAIL`：存在当前阶段必须修正的阻塞问题。

只有以下问题才能判定 `FAIL`：

- RTL 功能错误；
- signed / unsigned 或位宽可能导致错误结果；
- reset、enable、saturation、output limit 存在安全问题；
- 当前阶段核心 testbench 缺失；
- 仿真存在 `FAIL`；
- 代码无法编译或展开；
- 会破坏 v1 已验证路径。

以下内容原则上只能记录为 `NOTE`：

- 代码风格；
- 注释优化；
- 未来参数扩展；
- 当前参数范围无法触发的防御逻辑；
- 不影响当前阶段的额外测试；
- 后续模块才需要的功能。

### 0.1.3 子阶段关闭条件

一个子阶段同时满足以下条件后必须关闭：

- 本阶段 RTL 已创建；
- 本阶段 testbench 已创建；
- `xvlog` 0 error；
- `xelab` 0 error；
- `xsim` 0 FAIL；
- Claude Code 的必须修改项已完成；
- 回归测试 0 FAIL；
- 没有安全阻塞项。

关闭后不得继续让 GPT 或 Claude Code 重复审查同一版本。后续问题必须进入下一子阶段、Vivado 集成阶段、综合/实现阶段、bitstream 阶段、上板阶段或实物实验问题定位阶段。

### 0.1.4 v2a-1 当前处理规则

当前 v2a-1 已有：

- P-only RTL；
- testbench；
- 65/65 PASS；
- Claude Code 静态审查。

下一步只允许：

1. Codex 完成 Claude Code 列出的必须修改项；
2. Codex 补充必要测试；
3. 重新运行独立 XSim；
4. 若 0 FAIL，则将 v2a-1 标记为 `CLOSED`；
5. 进入 v2a-2 I + anti-windup。

不再将 v2a-1 重新提交 GPT 做逐行代码审查。

### 0.1.5 后续标准流水线

```text
GPT 定义任务
-> Codex 实现和独立仿真
-> Claude Code 集中审查一次
-> Codex 修正和回归仿真
-> 关闭子阶段
-> Vivado 主工程集成
-> 综合
-> 实现
-> bitstream
-> 上板
-> 示波器/实物测试
-> 根据真实结果定位问题
```

## 1. 每次任务启动前：Codex 必须输出路由结果

```
【任务路由结果】
任务类型：
当前阶段（引用 STATUS）：
使用 rules：
是否允许修改 RTL：
是否允许修改 md：
是否允许运行 Vivado：
是否允许生成 bitstream：
是否允许上板：
是否允许进入下一阶段：
本次最小目标：
```

如果用户已在指令中写明权限，Codex 必须复述并遵守。如果用户指令存在冲突（如同时说"不要写 RTL"和"实现 mixer_core.sv"），Codex 必须先指出冲突并询问。

## 2. 任务类型分诊表

| 用户任务关键词 | 任务类型 | 默认权限 |
|---|---|---|
| "写代码/生成模块/实现 mixer/LPF/BPF/修改 laser_lock_core" | RTL 代码开发 | 允许修改指定 RTL；不允许运行 Vivado；不允许上板；不允许进入下一阶段 |
| "审查代码/看代码有没有问题/上板前检查" | RTL 代码审查 | 只读，不修改代码，不运行 Vivado |
| "整理文档/更新实验报告/复盘/总结" | 文档整理 | 允许修改 md，不修改 RTL |
| "Vivado 报错/synthesis error/implementation failed/bitstream failed/timing/DRC" | Vivado/bitstream debug | 先分析，不修改代码，不运行 Vivado，除非用户批准 |
| "示波器没信号/板子没输出/fpgautil 失败" | 上板故障诊断 | 先分析，不改 RTL |
| "记录实验/今天测试结果" | 实验记录 | 允许修改实验 md，不修改 RTL |
| "AI/机器学习/峰识别/锁定状态判断/自动重锁" | AI 辅助设计 | 不写入 FPGA PL；先做数据和算法方案 |
| "不知道下一步/帮我排优先级" | 任务优先级整理 | 不修改文件，先给最小下一步 |

**权限判断铁律**：只有用户明确允许时，才可以修改 RTL / 运行 Vivado / 生成 bitstream / 上板。默认全部禁止。

## 2.1 工程事实与示例接口冲突时的决策顺序

当任务指令中的示例接口与实际工程不一致时，Codex 按以下优先级自行判断：

1. 当前实际工程中已验证、正在使用的接口和编码风格；
2. `STATUS.md`；
3. 当前版本 rules；
4. 当前版本设计文档；
5. 用户指令中的示例代码或建议接口。

用户指令中的示例接口默认是设计参考，不要求逐字照搬。

如果现有工程已经能够明确确认：

- reset 名称和极性；
- 主时钟名称；
- RTL 目录；
- testbench 目录；
- signed 声明风格；
- testbench 风格；

Codex 应直接采用现有工程风格继续执行，不需要再次询问用户。

只有出现以下情况才停止询问：

- 不同有效工程文件之间互相矛盾；
- 无法判断哪个文件是当前真实版本；
- 两种选择会明显改变硬件功能或安全边界；
- 用户授权范围不足以完成必要修改；
- 可能破坏已经验证的 v1 路径。

对于当前工程，已经确认：

```text
reset 接口：rstn_i
reset 极性：低有效
时钟接口：clk_i
实际主时钟：由顶层 adc_clk 驱动
RTL 目录：E:\new\fpga_lock\v94\v0.94\rtl
testbench 目录：E:\new\fpga_lock\v94\v0.94\sim
```

因此后续 `pi_controller.sv` 应使用：

```systemverilog
input logic rstn_i;
```

不再就 `rst_i/rstn_i` 向用户询问。

## 2.2 独立仿真权限分级

### Level 1：静态代码审查

允许：

- 读取 RTL；
- 检查语法；
- 检查 signed、位宽、saturation；
- 检查 testbench；
- 不执行工具。

### Level 2：独立 testbench 仿真

只有用户明确允许时可以执行。

允许：

- 仅编译指定的独立 RTL 和对应 testbench；
- 使用已有 Vivado Simulator/XSim 命令行；
- 或使用工程已有且可确认兼容的独立仿真脚本；
- 运行 `xvlog`、`xelab`、`xsim`；
- 读取编译和仿真日志；
- 根据错误只修改用户明确授权的两个文件。

不允许：

- 打开或修改完整 Vivado 工程；
- 修改 `.xpr`；
- Add Sources；
- Run Synthesis；
- Run Implementation；
- Generate Bitstream；
- 修改顶层；
- 上板。

### Level 3：Vivado 工程集成

必须由用户另行明确批准。

### Level 4：综合、实现、bitstream、上板

必须逐项单独批准。

## 2.3 独立仿真修复循环

当用户明确允许独立 testbench 仿真时：

1. 先生成指定 RTL 和 testbench；
2. 运行一次独立编译与仿真；
3. 如果失败，读取错误日志；
4. 只修改本任务授权的 RTL/testbench；
5. 再次运行；
6. 最多进行 3 轮修复；
7. 仍失败则停止，报告具体错误和未解决原因。

不得为了让仿真通过而修改：

```text
laser_lock_core.sv
red_pitaya_top.sv
mixer_core.sv
lpf_core.sv
output_protect.sv
.xpr
XDC/SDC
```

## 3. 禁止行为

- 不读文档就改 RTL
- 一次实现完整 MTS error
- v1d 同时加入 BPF/gain/PID/AI
- 未经允许修改 ODDR / PLL / ADC IO / PS / AXI / DDR / XDC / SDC
- 用 OUT1 直接接 D2-125
- 把 AI 作为当前阶段捷径
- 用未验证的 bit.bin 做实验结论

## 4. 每次任务必须读取的 rules 清单

```
E:\new\fpga_lock\v94\version\STATUS.md
E:\new\fpga_lock\v94\version\rules\00_PROJECT_DEVELOPMENT_RULES.md
E:\new\fpga_lock\v94\version\rules\01_TEACHING_ENGINEER_RULES.md
E:\new\fpga_lock\v94\version\rules\02_CODEX_WORKFLOW_COMPLETE.md
E:\new\fpga_lock\v94\version\rules\03_FPGA_CODE_REVIEW_RULES.md
E:\new\fpga_lock\v94\version\rules\04_EXPERIMENT_RECORD_RULES.md
E:\new\fpga_lock\v94\version\rules\RULE_CODEX_ENGINEER_TEACHER.md
E:\new\fpga_lock\v94\version\rules\06_V2_PID_DEVELOPMENT_RULES.md（如果存在）
```

`05_CODEX_SKILL_PROMPT_PREFIX_RULES.md` 已废弃，不作为有效规则入口；其内容已合并到本文件。

如果涉及具体版本开发，还必须按 `STATUS.md` 读取对应版本目录：

```
当前阶段为 v1：E:\new\fpga_lock\v94\version\v1
当前阶段为 v2：E:\new\fpga_lock\v94\version\v2
当前阶段为 v3/v4/v5：读取 E:\new\fpga_lock\v94\version\v3 / v4 / v5
```

## 5. Prompt 前缀模板

### 5.1 RTL 代码开发

```
【任务类型：RTL 代码开发 / <版本号>】
【当前阶段：见 STATUS.md】
【允许修改 RTL：是，仅限指定文件】
【允许修改 md：是】
【允许运行 Vivado：否，除非我明确批准】
【允许生成 bitstream：否】
【允许上板：否】
【允许进入下一阶段：否】

当前开发目标：<一句话>
禁止：不要跨阶段开发，不要修改 ODDR/PLL/ADC IO/DAC IO/PS/AXI/XDC
```

### 5.2 纯文档任务

```
【任务类型：纯文档任务】
【允许修改代码：否】
【允许生成 md：是】
【允许运行 Vivado：否】
【允许生成 bitstream：否】
【允许接板子/实验设备：否】
【允许进入下一阶段：否】
```

### 5.3 v2 PI/PID RTL 独立模块开发

```
【任务类型：v2 PI/PID RTL 独立模块开发】
【当前阶段：见 STATUS.md】
【允许修改 RTL：是，仅限 pi_controller.sv 和 tb_pi_controller.sv】
【允许修改 md：是，仅限同步实现状态和下一步】
【允许接顶层：否】
【允许运行 Vivado：否】
【允许生成 bitstream：否】
【允许上板：否】
【允许接激光：否】
【允许进入下一阶段：否】

默认边界：
- 只写独立 `pi_controller.sv` 和 `tb_pi_controller.sv`；
- 不接 `laser_lock_core.sv`；
- 不改 `red_pitaya_top.sv`；
- 不破坏 v1 OUT1 error 输出路径；
- 不直接完整 PID，不加入 D 通道；
- 不闭环，不把 OUT2 接激光。
```

### 5.4 Vivado / bitstream 诊断

```
【任务类型：Vivado / bitstream / 上板异常诊断】
请按六层排查：代码逻辑 → Vivado 编译/实现 → bitstream 加载 → Red Pitaya 板子/IP/SSH → 信号发生器/示波器/接线 → MTS 实验物理信号
先诊断，不要直接改代码。
```

### 5.5 实验记录整理

```
【任务类型：实验记录整理】
记录位置：E:\new\fpga_lock\v94\version\v1\V1_EXPERIMENT_REPORT.md
不要修改 RTL。不要把未验证现象写成已通过。
```

## 6. 任务结束时 Codex 必须回答

1. 当前阶段是什么
2. 修改/审查了哪些文件
3. 是否修改代码
4. 是否运行 Vivado
5. 是否生成 bitstream
6. 是否允许上板
7. 是否允许进入下一阶段
8. 主要风险点
9. 下一步最小动作

如果是文档任务，还要说明：是否只修改了 md、是否没有删除旧文档、是否没有移动旧文档。

## 7. 默认保守原则

当任务权限不清楚时：**先问清楚，不擅自执行。**

当任务可能跨阶段时：**先指出跨阶段风险，不直接推进。**

当任务可能影响硬件安全时：**先写方案和安全检查，不直接接设备。**

只要任务没有明确允许，就默认：不写 RTL、不修改 Verilog、不运行 Vivado、不生成 bitstream、不接 D2-125、不进入下一阶段。

## 8. 历史 v1d 协作方式

```
1. Codex 先读 STATUS + rules + v1 文档
2. Codex 只开发 lpf_core.sv + v1d testbench
3. GPT 审查 signed、位宽、saturation、LPF 逻辑和实验边界
4. Codex 再协助 Vivado 添加文件和跑仿真
5. tb_lpf_core 和 tb_laser_lock_core_v1d 都 PASS 后才允许 bitstream
6. 上板先做 100 kHz × 101 kHz 差频测试
7. 通过后才进入 v1e 真实 PD + REF
```

本节仅保留为历史 v1d 流程，不再代表当前主线。当前主线和当前版本目录以 `STATUS.md` 为准。Codex 不允许绕过 GPT 审查直接推进 bitstream 或上板。
