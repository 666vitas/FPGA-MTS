---
name: mts-redpitaya-project
description: Develop, debug, review, validate, document, and prepare experiments for the 666vitas/FPGA-MTS Red Pitaya MTS laser-frequency-locking repository. Use for v0.94 RTL, Vivado, custom_register_bank, SAFE/SCAN/HOLD/P_LOCK, OUT1 laser_error, OUT2 selected_out2, PZT scan and locking, custom_debug_capture, Python/PySide6 host GUI, SSH /dev/mem register control, waveform capture, experiment records, and Codex/Claude handoff. Always read the current mainline status and route each task to the correct FPGA, host, protocol, test, documentation, or experiment workflow. Do not use for unrelated FPGA, generic Python, or unrelated laser questions.
---

# Red Pitaya MTS 项目工作流

## Purpose

把 FPGA-MTS 仓库任务路由到正确的 RTL、仿真、寄存器协议、上位机、Vivado 检查、文档或实验交接流程。此 Skill 不开发 Codex，不创建 AI 应用，也不是通用 Verilog 教程。

## Trigger and Scope

任务涉及 `666vitas/FPGA-MTS`、`v0.94/rtl`、`v0.94/project/redpitaya.xpr`、`software/redpitaya_lock_host`、`MAGIC/VERSION`、`SAFE/SCAN/HOLD/P_LOCK/PI_LOCK`、`OUT1/OUT2`、`PZT`、`custom_debug_capture`、PySide6、`SSH /dev/mem`、波形采集、实验记录或 Codex/Claude 交接时使用。无关 FPGA、通用 Python 或无关激光问题不使用本 Skill。

## Mandatory Startup

1. 确认工作目录和 Git 根目录都是 `E:\new\fpga_lock\v94`。
2. 读取 `AI_REVIEW_README.md`、`AGENTS.md`、`version/AI_STRICT_REVIEW_ENTRY.md`、`version/CURRENT_REVIEW_MANIFEST.md`、`version/STATUS.md`、`version/rules/00_DOCUMENT_LANGUAGE_AND_STYLE_RULES.md`。
3. 读取任务关联源码和当前版本的 `DEVELOPMENT_LOG.md`；涉及 Vivado 时读取 `v0.94/project/redpitaya.xpr`。
4. 记录 `git branch --show-current`、`git rev-parse HEAD`、`git status --short --branch`、`git diff --name-only`、`git diff --cached --name-only`。
5. 可先运行 `scripts/check-project-state.ps1`，但它只读，不替代精确读取 `STATUS.md` 和 manifest。

主线是 GitHub `main` 和本地当前 `main`。detached HEAD、其他 branch、未提交改动、冲突标记或状态冲突必须报告，不得自动切换、清理、覆盖或回退。

## Evidence Hierarchy

按 `references/project-map.md` 使用证据层级：Tier 0 当前代码和测试，Tier 1 当前状态入口，Tier 2 当前实验记录和用户证据，Tier 3 普通说明，Tier 9 历史资料。代码、STATUS 和实验记录冲突时报告冲突，以真实代码和 STATUS 顶部快照为当前依据；旧注释不能覆盖实现。

默认禁止把 `v-weifang/**`、`version-weifang/**`、`version/v1/**`、`version/v2/**`、`**/old/**`、`**/*.before_*`、`**/*before*` 作为当前 main 结论。`version/AI_STRICT_REVIEW_ENTRY.md` 的规则必须读取，但其 merge markers、过期状态不能覆盖 STATUS 或 manifest。

## Task Classification

先指定一个主类别，可列出次类别，但一次只推进一个最小、可验证目标。详细路由见 `references/task-routing.md`。

- Repository review：读取当前状态、代码和变更，分离代码事实、文档事实、实验事实、污染、风险和下一步。
- FPGA RTL：检查 signed/位宽/乘法/移位/截断/饱和、pipeline、reset、MODE、SAFE、OUT2 最终来源、DAC 限幅、仿真和 `.xpr` source set。
- Register protocol：同步核对 `custom_register_bank.sv`、`custom_fpga_scan_control.py`、backend、worker、tests、MAGIC、VERSION、地址、默认值、读回和兼容性；不得猜寄存器地址。
- Python host / GUI：核对 `main_window.py`、backend、workers、scan control、`waveform_plot.py`、tests 和日志，保持 Live 防重入、完成后调度、Stop 禁止再次采集、真实 points、异常 SAFE 和显示不写 FPGA。
- Vivado：只能检查工程、源文件、脚本、报告和日志；不自动运行 Vivado、生成 bitstream 或烧录，并严格区分 synthesis、implementation、timing、bitstream、烧录和上板证据。
- Experiment preparation：输出接线、前置条件、SAFE 起点、参数、操作、观测、PASS、FAIL、停止条件和记录项。
- Documentation：STATUS 顶部为当前快照，DEVELOPMENT_LOG 只追加历史；代码完成不等于实验通过。
- AI/automatic optimization：只有用户单项授权且基础 P_LOCK、采集、日志、指标和 fallback 已确认后才进入；先离线分析和参数建议，AI 不进入 125 MHz FPGA 快速环。

## Scope and Change Rules

先报告计划修改和明确不修改的文件，只做最小改动，不重构、不随意改名、不移动目录、不替换 GUI 框架、不重建整个 Vivado 工程、不修改自动生成文件、不覆盖用户未提交改动。遵守 `AGENTS.md` 的状态和日志规则；若用户明确把文件列为不修改项，报告冲突并保持不改。

## Safety Boundary

- Agent 不运行 Vivado，不综合、实现、生成 bitstream、不烧录。
- `IN1`、`IN2` 绝对输入必须保持在 `+/-1 V` 内。
- `OUT1` 是 `laser_error` 的 error observation，不是执行器输出。
- `OUT2` 涉及 `SCAN`、`HOLD`、`P_LOCK`、`PI_LOCK` 时，先读回 `MAGIC`、`VERSION`、`MODE`、`ENABLE`、限幅、监视值、饱和和 SAFE 条件。
- `OUT2` 只能接激光器专用 `PZT/Scan` 输入；禁止接激光电流调制、`D2-125 Servo Output`、`D2-125 Aux Output`，禁止任何输出并联；`EOM` 仍由外部信号源驱动。
- 首次 `P_LOCK` 从 `Kp=0` 开始，后续只人工按 `0/4/8/16/32` 小步测试；`polarity` 只能人工判断。
- 越界、接近 limit、saturation、振荡、异常跳变、通信错误、MAGIC/VERSION 错误或反馈方向疑似错误时立即 SAFE。禁止自动提高 Kp、自动切 polarity、自动重锁或恢复 `KI/integral`。

详细接线和实验停止条件见 `references/experiment-safety.md`。

## Validation and Handoff

按 `references/verification-matrix.md` 选择验证；证据等级不可互相推断。按 `references/handoff-template.md` 输出中文交接，至少包含实际读取文件、主类别和唯一目标、修改边界、验证结果、未运行项、PASS/FAIL、SAFE 条件和下一步唯一任务。没有用户实验反馈时只能写“等待验证”。

准备提交前检查 `git status --short`、`git diff --name-only`、`git diff --cached --name-only`、`git diff --check`。禁止 `git reset --hard`、`git clean -fd`、覆盖式 `checkout/restore`、force push、未经授权 commit/push 和混入 Vivado 临时文件。

## References

按需读取，不要把全部引用文件一次性塞入上下文：

- `references/project-map.md`：项目身份、信号链、关键文件和协议事实。
- `references/task-routing.md`：任务分类、读取清单和实施边界。
- `references/verification-matrix.md`：按修改类型选择命令和证据等级。
- `references/experiment-safety.md`：硬件接线、PZT、输入输出和 SAFE 条件。
- `references/handoff-template.md`：固定中文交接模板。
