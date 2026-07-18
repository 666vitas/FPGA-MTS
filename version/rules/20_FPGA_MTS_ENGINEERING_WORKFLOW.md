# FPGA-MTS 单开发者 Gate 工作流

本文件是 FPGA-MTS 当前唯一有效的详细工程规则。当前目标不是扩展 GUI、PI、自动锁定、AI 优化或审查流程，而是在现有 SystemVerilog MTS 信号链上实现一个 Linien-style minimal manual lock framework。

## 1. 当前唯一工程目标

```text
宽范围扫描
-> 选择目标 MTS 谱线区域
-> 确认零交叉、误差斜率和 rising/falling 扫描方向
-> 缩小并居中扫描
-> FPGA 在指定方向原子执行 scan-to-Kp=0 transition
-> 验证 OUT2 和谱峰无明显跳变
-> 加入人工批准的最小非零 Kp
-> 基础 P-only 稳频
```

基础 P-only 未经用户真实硬件验证前，不扩展 PI、自动重锁、完整自动锁定、AI 参数优化、深度学习、全谱线自动识别、大量 GUI 页面或大规模上位机重构。

## 2. 单开发者职责

### 用户

- 唯一真实硬件实验操作者。
- 唯一有权确认硬件 Gate 是否通过的人。
- 负责接线、示波器读数、PZT 行为、谱线位置和真实锁定结果。
- 不需要理解全部 RTL、寄存器或上位机实现细节；Codex 必须把实验步骤和判据写清楚。

### Codex

- 唯一主要开发者，负责根因分析、最小实现、测试、文档和提交前自检。
- 默认不启动 subagent，不创建 Builder、Critic、Evaluator、Supervisor 等多角色流程。
- 不因任务复杂自动增加审查线程，不以“多 Agent 已通过”作为完成证据。
- 不能代替用户操作硬件、确认硬件 Gate 或提升硬件证据等级。

## 3. 活跃入口与数据源

日常开发只需读取：

1. `AGENTS.md`：角色、基本工作方式和安全边界。
2. `version/STATUS.md` 顶部：Current Stage、Current Gate、Blocker、证据和唯一实验。
3. 本文件：完整 Gate 工作流和完成标准。
4. `version/CURRENT_REVIEW_MANIFEST.md`：当前有效代码、测试、文档根目录和历史排除。
5. `software/redpitaya_lock_host/docs/HARDWARE_CALIBRATION_SOP.md`：OUT2、loaded PZT 和锁点对比实验的操作与证据要求。

Development Mode 默认只使用当前本地 workspace。禁止主动 `git fetch`、`git pull`、`git ls-remote`、访问 GitHub online 或比较 `origin/main`；默认不 commit、不 push。

`version/rules/` 中除本文件外的旧阶段规则均为 `HISTORICAL / NOT ACTIVE`。`version/v1/`、`version/v2/`、`version/v3/`、`v-weifang/`、`version-weifang/`、`old/` 和 `*.before_*` 仅作历史证据，不控制当前开发。

## 4. 每次只推进一个 Gate

任务开始时检查 branch、working tree、`version/STATUS.md` 顶部和任务直接相关的代码、测试、SOP、实验记录，然后只回答：

1. 当前 Gate 是什么。
2. 当前 blocker 是什么。
3. 本次任务是否直接服务于 blocker。
4. 预计修改哪些文件。
5. 完成后需要什么测试或用户实验。

保护已有修改。来源不明或与任务重叠的改动不能被覆盖、撤销或清理。若现有代码已经提供当前 Gate 所需的控制、观测、readback、记录和 SAFE 能力，不为“以后可能有用”继续增加功能。

Gate 未通过时禁止自动进入下一 Gate、扩展额外功能、用测试数量或代码量代替实验结果，或因设计看起来合理而宣布完成。

## 5. 证据和 Gate 权限

记录按三个维度分开：

- SOFTWARE VERIFIED / SIMULATION VERIFIED：使用 `[IMPLEMENTED]` 或 `[AUTOMATED VERIFIED]`。
- HARDWARE VERIFIED：只能使用用户真实结果对应的 `[USER GUI VERIFIED]` 或 `[USER HARDWARE VERIFIED]`。
- 未通过或未测：使用 `[FAILED]` 或 `[NOT VERIFIED]`。

不得把代码存在当测试通过、测试通过当 GUI/硬件通过、bitstream 生成当烧录成功、CH4 `selected_out2` 当真实 OUT2/loaded PZT、电压正确当锁定、HOLD 当 P-only，或短时闭环当长期稳频。

只有用户提供真实硬件记录并满足当前 Gate 的验收标准，才能把该 Gate 写成 HARDWARE VERIFIED。Codex 不自动批准 Gate。

## 6. 当前开发优先级

按顺序完成：

1. 核实真实 OUT2 与 loaded PZT 节点电压。
2. 对同一谱线、零交叉和扫描方向比较 `HOLD SELECTED COUNT` 与 `LOCK HERE`。
3. 区分 scan-to-hold 动态迟滞、rising/falling 差异与 `LOCK HERE` 逻辑或触发错误。
4. 采用 Linien 的 manual lock、谱线区域选择、方向选择、扫描居中/缩小、FPGA robust trigger 和 lock check 思想。
5. 设计并实现最小 FPGA scan-to-lock 状态机。
6. 实现并验证 Kp=0 无明显跳变。
7. 实现并验证最小 P-only 稳频。

在第 7 项通过前，禁止开展 PI、自动重锁、完整自动锁定、AI 参数优化、深度学习、全谱线自动识别、大量 GUI 页面、大规模上位机重构、多 Agent 项目管理或新增重复规则。

## 7. Linien 的定位与职责划分

Linien 是当前主要参考框架，但不直接复制其完整代码，不改为 Migen：

- Windows host：显示、选择目标谱线、配置低速参数和保存结果。
- FPGA：实时扫描、方向判断、目标穿越判断、原子模式切换、P 控制、限幅和安全。
- Red Pitaya Linux：低速配置、状态读取和数据传输。
- Windows/Linux 通信不得负责精确的 scan-to-lock 切换时刻。

保留现有 SystemVerilog + Vivado 工程、MTS mixer + LPF、自定义寄存器和四通道采集框架：

```text
IN1 = PD
IN2 = REF
OUT1 = laser_error
OUT2 = selected_out2 -> laser dedicated PZT/Scan input
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK candidate（当前禁止开展）
MAGIC = 0x4D545330
```

`VERSION` 必须从当前 RTL、host 和实际 bitstream 记录核对，不在长期规则中写死。PyRPL 仅作辅助架构参考，不与 Linien 并列为当前主要框架。

## 8. Gate 路线

### Gate L0：Diagnose scan-to-lock offset

比较同一目标在 `HOLD SELECTED COUNT` 与 `LOCK HERE, Kp=0` 下的 selected count、readback、真实 loaded-node 电压、扫描方向和谱峰相对 cursor 偏移，区分物理迟滞、方向差异、触发逻辑与 MTS 零点/谱峰对应关系。

### Gate L1：Target and direction are deterministic

确认目标来自当前 capture；谱线区域、零交叉、误差斜率、rising/falling 方向、扫描中心和缩小后的范围均明确且可重复。

### Gate L2：Atomic scan-to-Kp=0 transition

FPGA 在指定方向穿越目标时原子捕获 setpoint/bias 并切换；Windows/Linux 只配置和读取。确认 Kp=0 时 OUT2 无危险跳变、谱峰不明显偏移、无 saturation，并最终 SAFE。

### Gate L3：Minimal nonzero Kp

Ki=0，从用户批准的最小 Kp 开始；polarity 必须有方向证据；correction/absolute limit 生效。确认形成负反馈，异常立即 SAFE。

### Gate L4：Basic P-only lock

确认 error RMS 降低、OUT2 不长期饱和、仍有调节余量、可重复进入同一锁点，并保存锁定前后数据。Gate L4 通过前禁止 PI。

## 9. 根因与最小修改

先建立可重复的 pass/fail 反馈环，再修改代码。按需检查最终信号路由、host/RTL 地址与模式、signed/位宽/饱和、counts 与物理电压、capture 对齐、扫描方向、模式切换和 stale 数据。

优先修复根因，保持已验证的 SAFE/SCAN、寄存器兼容和测试。禁止无关重构，也不得在 Gate L0 结果返回前预先实现 Linien 状态机。

## 10. 自检与额外审查

普通任务完成后只做一次同线程自检：

1. 修改是否服务当前 Gate。
2. 是否修改任务外文件或破坏已有改动。
3. 要求的测试是否真实通过。
4. 是否引入输出、接线、限幅或模式安全风险。
5. 是否错误提升 GUI、硬件或闭环证据。

只有改动涉及 OUT2 最终 DAC 路由、PZT safe range、SAFE/SCAN/HOLD/P_LOCK 切换、寄存器地址/位宽/signed、saturation/限幅、FPGA 原子 scan-to-lock 或可能导致激光器/板卡异常输出时，才允许增加一次额外工程审查。该审查不是强制多 Agent 流程；禁止三轮、五轮或持续监督直到通过。只修复 Blocker/High 后做一次针对性复验。

## 11. 验证与记录

- Python 修改：相关 `tabnanny`、修改文件 `py_compile`、`pytest --collect-only`、targeted tests 和完整 software tests。
- RTL 修改：现有 testbench、lint/编译和工程 source/file-set 检查；Codex 不运行 synthesis/implementation，不生成或烧录 bitstream。
- 规则/文档修改：`git diff --check`、精确 conflict-marker 检查、`git diff --stat` 和相关 diff。
- 不删除、skip、xfail 或弱化安全测试；失败必须如实报告。
- 实现、验证或实验状态变化时更新 `version/STATUS.md` 顶部和必要的当前记录；计划不能写成完成。

## 12. 硬件实验与永久安全边界

每轮只给一个 Gate 内实验，并写清目的、接线、scope load/coupling/probe、参数、MODE/Kp/Ki/polarity/safe range、顺序、PASS/FAIL、立即 SAFE 条件和返回数据。

永久规则：

1. OUT2 只能连接当前 Gate 授权的激光器专用 PZT/Scan 输入和测量设备。
2. 禁止连接激光器电流调制、D2-125 `Servo Output`、D2-125 `Aux Output` 或任何其他有源输出；禁止输出端并联。
3. `MAGIC/VERSION`、通信、SAFE、接线、scope 条件、readback、输出范围、saturation、削顶、跳变、目标来源或反馈方向任一不明确，立即 SAFE 并停止。
4. Codex 不自动提高 Kp/Ki、切换 polarity、放宽 limit、扩大 safe range、再次 LOCK 或进入下一 Gate。
5. 未经用户对当前单项明确授权，不修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream。

## 13. 交接

软件修改完成后报告修改文件、目的、软件测试、仿真结果、未完成的硬件验证和用户唯一下一步。默认不执行 `git add`、commit、push、pull、reset、clean、rebase 或 amend。
