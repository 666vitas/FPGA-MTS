Status: ACTIVE
Effective-Gate: ALL
Authority: AGENTS
Last-Updated: 2026-07-24
Supersedes: AGENTS_PROPOSED.md
Superseded-By: NONE

# FPGA-MTS Codex 总入口

本文件是 `E:\new\fpga_lock\v94` 中 Codex 工程任务的唯一根入口，只保存长期规则，不保存每日 Vivado 结果或 Gate 进度。默认使用中文；路径、命令、寄存器、模块、信号和模式名保留英文。

## 1. 项目身份与信号语义

- Repository：`666vitas/FPGA-MTS`
- 当前本地根目录：`E:\new\fpga_lock\v94`
- RTL / Vivado：`E:\new\fpga_lock\v94\v0.94`
- Host：`E:\new\fpga_lock\v94\software\redpitaya_lock_host`
- Hardware：Red Pitaya STEMlab 125-14

固定信号语义：

```text
IN1  = PD
IN2  = REF
OUT1 = laser_error
OUT2 = selected_out2 -> laser dedicated PZT/Scan input
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK candidate
MAGIC=0x4D545330
```

`VERSION` 必须从当前 RTL、host 和实际 bitstream 记录核对，不在长期规则中写死。

## 1.1 当前 FIRST_LOCK_MVP 实验边界

- 当前唯一实验目标是以一块 Red Pitaya 完成真实、简单、可重复的 PZT
  P-only lock；AI、自动重锁、自动相位优化和 PI/Ki 均不属于当前 Gate。
- D2-125 Main Servo 继续承担激光器快电流反馈；当前 Gate 仅逐步替代其
  AUX 对 PZT 的 scan、hold 与慢校正。FPGA `OUT2` 接 PZT 时，D2-125 AUX
  Servo Output 必须与 PZT 物理断开，严禁两个输出并联。
- 不重建既有 Processing System、Block Design、ADC/DAC、125 MHz clock、
  reset、PS/PL 或 Linux transport 架构；优先审查和最小修改 custom PL RTL、
  register bank、scan/hold/lock logic 与必要的 host protocol。

## 1.2 项目内 Vivado Skills

项目的完整 Vivado Skills 安装在 `.agents/skills/`，其知识仅作参考；当前
工程实际 Vivado 版本和 `help <command>` 输出才是 Tcl/property/strategy 是否可用的唯一依据。

- `vivado-synth`：RTL、DSP、寄存器和 pipeline 的综合结构审查。
- `vivado-constraints`：XDC、clock、CDC、I/O delay 与 timing exception 审查。
- `vivado-sim`：RTL behavioral verification。
- `vivado-impl`：place/route 与 implementation strategy（仅经当前 Gate 授权）。
- `vivado-analysis`：WNS/TNS/WHS/THS、关键路径、fanout 与 congestion 解析。
- `vivado-tcl`：兼容版本的 batch Tcl 编写与执行。
- `vivado-debug`：仅在常规仿真及 OUT1/OUT2 观测不足时考虑 ILA/VIO；加入后须重新完成 implementation/timing。

不为安装 Skill 而改用 nextpnr、ice40、ECP5、Gowin 或 GateFlow 作为本 Xilinx
Zynq 工程的综合、P&R 或 timing signoff。每项重要 RTL 变更都必须经过 RTL
simulation、synthesis、implementation 和 routed timing analysis；WNS 正值本身
不构成 Timing PASS，且不得用无证据的 timing exception 掩盖问题。

## 2. 长期产品目标

在现有 SystemVerilog MTS 信号链上完成一次真实、可重复、无明显谱峰偏移的 P-only 锁定，并保持可逐步演进为 Linien-inspired 分层系统的 Host/FPGA 边界：

```text
SAFE
-> SCAN
-> aligned capture(PD/ERROR/OUT2)
-> user selects a valid target
-> HOLD / controlled approach
-> P_LOCK Kp=0
-> user-approved minimal nonzero Kp
-> sustained basic P-only lock
-> any anomaly returns SAFE
```

真实 P-only 硬件 Gate 通过前，不把主任务扩展到 PI/Ki、自动重锁、AI、IQ 重构、双执行器或大规模 GUI 重做。deterministic ARM 源码和测试必须保留，但它是否进入某个 build 只由当前 `CURRENT_GATE` 决定。

## 3. 按任务读取当前文档

每个任务先读取本文件，再按任务需要读取当前固定入口：

- 当前能力、开发范围或硬件阶段：`docs/CURRENT_STATUS.md`。
- Host 控制或接口：`docs/HOST_FPGA_INTERFACE.md` 及相关 Host 文件。
- RTL、约束或构建：`docs/FPGA_DEVELOPMENT_RULES.md` 及相关源码/脚本。
- 产物交付：`docs/RELEASE_PROCESS.md`。
- 硬件操作说明：现有 `HARDWARE_TEST_SOP` 文档（若存在）。
- 项目背景或变更记录：按需读取 `docs/PROJECT_CONTEXT.md`、`docs/CHANGELOG.md`。

历史材料只在需要追溯时读取，不重新成为当前规则。不得仅凭文件名或修改日期选择规则。

## 4. 文档冲突优先级

发生冲突时按以下顺序裁决：

1. 用户本次明确指令
2. 本文件中的安全与范围禁令
3. `version/CURRENT_GATE.md`
4. `version/STATUS.md`
5. `version/CURRENT_REVIEW_MANIFEST.md`
6. manifest 指定的 active rules
7. active architecture spec
8. README、SOP、开发日志等 supporting docs
9. `version/history/**`、`version/v1/**` 至 `version/v5/**`、旧 review 和 superseded 文档
10. 注释、文件名日期、Windows 修改日期和 AI 推测

禁止仅依据文件修改日期判断“最新”。active 文件必须被 manifest 列出，元数据为 `Status: ACTIVE`，`Effective-Gate` 与当前 Gate 兼容，且没有有效的 `Superseded-By`。

## 5. 文档职责

- `AGENTS.md`：长期工程规则、安全边界和冲突优先级。
- `version/CURRENT_GATE.md`：当前唯一 Gate、允许范围、禁止范围和验收条件。
- `version/STATUS.md`：当前事实、blocker、证据和唯一下一动作。
- `version/CURRENT_REVIEW_MANIFEST.md`：当前强制读取集合与默认排除范围。
- `version/rules/*.md`：稳定工作流、安全、架构边界和证据规则。
- `docs/architecture/*.md`：长期架构说明；不能覆盖当前 Gate。
- `docs/process/*.md`：supporting 流程与迁移方案。
- `docs/hardware/*.md`：硬件 SOP 和真实验证记录。
- `docs/experiment_logs/*.md`：实验输入、波形、结果和失败原因。
- `version/history/**`：旧 Gate、旧 review、superseded 状态和历史方案。

## 6. 单开发者与单 Gate

- 用户是唯一真实硬件操作者，也是唯一有权批准硬件 Gate 的人。
- Codex 是唯一主要开发者，负责分析、最小实现、测试、文档和同线程自检。
- 默认不启动 subagent，不创建 Builder/Critic/Evaluator/Supervisor，不以多 Agent 结论作为完成证据。
- 每轮只处理一个当前 Gate 内的可验收任务；不得顺手进入下一 Gate或扩展无关功能。
- 保护已有 working tree 修改。来源不明或与本轮重叠时先报告，不得 reset、clean、restore 或覆盖。

任务模式：

- `ANALYZE`：只读分析、诊断、审查或计划。
- `IMPLEMENT`：只在用户授权范围内实施最小修改并验证。
- `VERIFY`：只运行验证和报告证据，不改变产品代码或硬件状态。
- `HARDWARE-GATE`：每轮只给一个实验；用户操作并批准结果。

已明确授权的本地工作可连续完成必要的检查、修改、相关验证及本轮引入问题的修复，不重复索要逐步批准。只读审查不自动授权实施，编写脚本不自动授权执行；RTL 编辑、仿真、综合/实现、候选 bit 生成和真实硬件操作分别确认范围。候选 bit 不等于允许加载或烧录，旧任务授权不继承到新任务。未知副作用的测试先检查入口和依赖；不能据此宣布所有测试都不访问硬件。

## 7. Host / FPGA 职责边界

### GUI / Client

负责参数输入、真实波形显示、用户命令、readback、状态和失败原因展示。GUI 不应拥有 CSR 地址、`/dev/mem`、SSH 拼接、实时 servo、隐藏安全决策或与 FPGA readback 分离的硬件状态副本。

### LockService / RegisterMapper / AcquisitionService

- LockService：唯一拥有 host 侧 lock state、合法状态迁移、目标有效性、Kp 阶梯、失败原因和异常 SAFE。
- RegisterMapper：唯一知道 CSR 地址、`MAGIC/VERSION`、signed14、单位换算、写入顺序、W1P 和 readback 校验。
- AcquisitionService：唯一负责 aligned capture、frame、monitor sampling、统计、`capture_id` 和 `scan_generation`。

### FPGA

唯一负责实时 mixer/LPF、triangle scan、aligned capture、P-only servo、mode/output selection、saturation 和 limit。Windows、SSH、Linux 轮询不得参与每个 servo sample。

现阶段允许通过 adapter 逐步迁移现有 GUI/backend，不要求一次性重写上位机。板端常驻服务只在基础 P-only 通过后按新 Gate 开展。

## 8. 证据措辞

软件、仿真、timing、GUI 和真实硬件证据必须分开。允许的证据标签：

- `[CODE INSPECTED]`：只读代码或路由核对。
- `[IMPLEMENTED]`：实现存在，不能表示测试或硬件通过。
- `[UNIT TESTED]`：明确列出的软件单元测试通过。
- `[RTL SIMULATED]`：明确列出的 RTL 仿真通过。
- `[TIMING PASSED]`：用户提供的当前 build timing 报告满足 Gate。
- `[AUTOMATED VERIFIED]`：历史或组合自动验证记录；必须同时写清实际测试。
- `[USER GUI VERIFIED]`：用户在真实 GUI 中确认，不代表物理量通过。
- `[USER HARDWARE VERIFIED]`：用户真实接线/测量通过。
- `[FAILED]`：已有明确失败证据。
- `[NOT VERIFIED]`：尚未执行或证据不足。

不得把代码存在写成测试通过、仿真写成 timing/hardware 通过、bitstream 生成写成烧录成功、GUI 命令写成硬件已 SAFE、数字零跳变写成 PZT/激光无瞬态，或短时闭环写成长期稳频。

## 9. 永久安全边界

- OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
- 禁止 OUT2 连接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output` 或任何其他有源输出；禁止输出并联。
- IN1/IN2 必须处于 Red Pitaya 允许输入范围；接线、scope load/coupling/probe ratio 必须明确。
- `MAGIC/VERSION`、通信、SAFE、readback、范围、saturation、削顶、跳变、目标来源或反馈方向任一异常时立即停止并请求 SAFE。
- Codex 不自动提高 Kp/Ki、切换 polarity、扩大 safe range、重新 LOCK 或批准下一硬件 Gate。
- 未经当前任务明确授权，不修改 RTL、Vivado 工程、XDC/Tcl、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream。
- 默认不运行 Vivado synthesis/implementation，不生成或烧录 bitstream，不连接板卡网络。
- 禁止主动 `git fetch/pull/ls-remote` 或访问 GitHub online；默认不执行 add、commit、push、branch、merge、rebase、amend、reset 或 clean。

## 10. 变更前后回复

开始前说明：

1. 当前 Gate 和 blocker。
2. 本轮唯一目标。
3. 将读取和预计修改的文件。
4. 明确不修改的范围。
5. working tree 中需要保护的已有修改。

结束时说明：

1. 实际修改文件及原因。
2. 实际验证结果与未运行事项。
3. 未修改的产品/硬件边界。
4. 风险、未验证内容和用户唯一下一步。
5. 是否更新 `STATUS`、`CURRENT_GATE`、manifest。

默认不 commit、不 push。

---

## 11. AI 开发规则与规范文档入口（2026-09-04 补充）

本节自 2026-09-04 起更新第 3 节的必读顺序，并补充第 4、5 节的文档职责；原有安全边界、Gate 限制、证据标签和 Git 保护规则保持不变。

### 11.1 当前文档入口

第 3 节的按任务读取规则是本工程唯一当前入口。随后读取相关 RTL/Host 文件、测试和证据；历史追溯只读取 `../archive/obsolete/` 下的归档内容。

### 11.2 文档权威关系

- `docs/CURRENT_STATUS.md`：唯一项目当前状态和当前 Gate 入口；必须反映已完成、未完成、未验证、允许范围、退出条件和阻塞项。
- `docs/HOST_FPGA_INTERFACE.md`：寄存器、数据通道、控制语义和版本对应关系的权威入口。
- `docs/CHANGELOG.md`：工程变更原因、影响模块和验证摘要的固定入口。
- `docs/RELEASE_PROCESS.md`：bit 发布、命名、manifest 和追溯规则的固定入口。

若状态文件冲突，先停止实现并按第 4 节优先级核对；项目事实状态和当前 Gate 以 `docs/CURRENT_STATUS.md` 为准，接口事实以 `docs/HOST_FPGA_INTERFACE.md` 为准，归档中的旧 version 文件只能用于追溯。

### 11.3 修改代码后的强制记录

1. 更新 `docs/CURRENT_STATUS.md`，如实记录完成、未完成、未验证和阻塞。
2. 更新 `docs/CHANGELOG.md`，记录修改文件、修改原因、影响模块和验证方式。
3. 接口相关修改同步更新 FPGA、Host 和 `docs/HOST_FPGA_INTERFACE.md`，禁止单边改变接口。
4. RTL 修改按 `docs/FPGA_DEVELOPMENT_RULES.md` 完成仿真、Vivado、timing、release 和 bit 映射；未经授权或未运行的步骤必须写 NOT RUN / NOT VERIFIED。
5. 形成 bit 时按 `docs/RELEASE_PROCESS.md` 建立不可歧义的 release manifest。

### 11.4 禁止无意义重复文档

禁止为普通开发过程创建无意义或重复的 `xxx_report.md`、`xxx_status.md`、`xxx_summary.md`。优先更新上述固定入口。只有用户明确要求、工具必须输出或需要冻结不可变评审证据时，才建立独立报告，并从 `CURRENT_STATUS`、`CHANGELOG` 或 release manifest 链接。

### 11.5 重构后的路径边界

- `v94/docs/` 的固定入口包括 `PROJECT_CONTEXT.md`、`CURRENT_STATUS.md`、`CHANGELOG.md`、`FPGA_DEVELOPMENT_RULES.md`、`HOST_FPGA_INTERFACE.md`、`RELEASE_PROCESS.md`；其他有实际用途的现有文档可以保留。
- `v94/reference/` 只保存不参与自研 build 的 open source 与 guanfang-v0.94 参考工程。
- `archive/obsolete/v94_version/` 保存 version 下的全部历史版本、旧规则、review、Gate/状态快照和产品化草稿；当前 Gate 与项目状态只由 `docs/CURRENT_STATUS.md` 管理。
- 原有章节中对 `version/CURRENT_GATE.md`、`version/STATUS.md` 和 `version/CURRENT_REVIEW_MANIFEST.md` 的引用属于历史路径；进入项目时以第 3 节规定的当前入口为准。
- 原第 5 节中的 `version/rules/*.md`、`docs/architecture/`、`docs/process/`、`docs/hardware/` 和 `docs/experiment_logs/` 已归档；当前规则、上下文、接口和发布要求分别以 `docs/FPGA_DEVELOPMENT_RULES.md`、`docs/PROJECT_CONTEXT.md`、`docs/HOST_FPGA_INTERFACE.md` 和 `docs/RELEASE_PROCESS.md` 为准。
- 根目录的历史审查输出、旧计划、旧 README 和旧 docs 已归档；不得把归档文件重新当作当前状态入口。
- 生成缓存和日志进入 `archive/delete_candidates/`，删除前仍需人工确认，不因移动到该目录而自动删除。

# Development Freeze Rule

当前目录结构已经冻结。

以后开发：

只允许：

1. 修改FPGA源码
2. 修改Host源码
3. 修改必要测试
4. 更新固定入口文档

禁止：

重新规划目录。

创建重复文档。

根据archive历史文件开发。
