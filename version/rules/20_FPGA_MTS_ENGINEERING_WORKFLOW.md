# FPGA-MTS 工程开发工作流

本文件是 FPGA-MTS 当前唯一有效的详细工程工作流。目标是尽快、安全、可验证地实现 Red Pitaya STEM125-14 上真实 MTS 激光 PZT 稳频。`version/rules/` 中其他阶段性规则可作为技术背景；若其固定角色、旧版本、旧 Gate 或旧接线与本文件、当前代码或 `version/STATUS.md` 冲突，不作为当前执行依据。

## 1. 工程职责与目标

- 用户是唯一真实实验操作者和最终决策者。
- Codex 是主要工程开发助手，负责代码、架构、测试、根因定位、开发判断、实验步骤和记录；不能代替用户确认 GUI、硬件或闭环结果。
- 当前工程目标是一个真实、可重复、可观测、不会立即失锁的最小 P-only MTS 闭环。
- 长期方向是自动识峰、自动锁定、自动重锁、参数自动优化和深度学习优化，但必须在稳定 P-only 之后逐 Gate 推进。

```text
稳定观测 -> 信号确认 -> 扫频控制 -> 人工锁点
-> Kp=0 无扰切换 -> 最小非零 Kp -> 稳定 P-only
-> PI -> 自动识峰 -> 自动锁定 -> 自动重锁
-> 参数自动优化 -> AI/深度学习优化
```

## 2. 工作模式与数据源

### Development Mode（默认）

只以当前本地 workspace 为数据源，用于开发、测试、文档和实验支持。禁止主动 fetch/pull、访问 GitHub online、比较 `origin/main` 或等待网络。只修改用户授权范围；默认不 commit、不 push。

### Review Mode

只有用户明确输入 `@GitHub 审计` 或 `审查最新main` 才启用。数据源是 GitHub `main`，只读审查，禁止修改项目文件。Development Mode 内的一次独立工程复核不等于 Review Mode。

## 3. 当前工程状态模型

按以下优先级判断事实：

1. 当前实际代码、寄存器定义和最终信号路由。
2. `version/STATUS.md` 顶部最新状态。
3. 当前 Gate 的最新 SOP、实验记录和 `version/HARDWARE_VALIDATION.md` 有效证据。
4. 本轮实际运行的自动化测试和仿真。
5. README、普通说明、历史日志和旧注释。

若证据冲突，追踪当前实际路径并判断是否影响接线、输出、限幅或实验安全。优先修复会导致错误工程决策的入口和记录；普通旧注释不应阻塞整个项目。历史目录默认不用于当前结论：

```text
v-weifang/**
version-weifang/**
version/v1/**
version/v2/**
**/old/**
**/*.before_*
**/*before*
```

长期规则不得写死当前日期、Gate、`VERSION`、锁点或临时实验参数。`VERSION` 必须从当前 RTL、host 和实际 bitstream 记录核对。

## 4. 每轮只选择一个主任务

开始时检查 branch、working tree、`version/STATUS.md` 顶部及任务直接相关的代码、测试、SOP 和实验记录。保护已有修改，不覆盖、撤销或清理来源不明或重叠改动。

建立工程模型后必须回答：

1. 当前 Stage/Gate 是什么。
2. 代码、自动化、GUI 和硬件分别证明了什么。
3. 哪些只实现但未验证。
4. 距离最小 P-only 最近的唯一阻塞是什么。
5. 阻塞属于软件、RTL、bitstream、寄存器、信号链、校准、接线、锁点、极性、Kp 还是实验证据。
6. 当前应修改代码还是执行一次硬件实验。

只推进当前 Gate。若现有代码已提供该 Gate 所需控制、观测、日志和 SAFE 能力，不为“可能有用”继续加功能。

## 5. 根因与最小修改

先建立可重复的 pass/fail 反馈环，再修改。按需检查：

- 最终信号数据路径和未连接候选逻辑。
- host/RTL 地址、模式、signed14、单位、读写顺序和 readback。
- signed/unsigned、位宽、乘法、移位、截位、舍入和饱和。
- counts、command-side voltage estimate、真实 OUT2 和 loaded PZT 的区别。
- 模式切换、capture 对齐、stale 数据和测试假设。

优先修复根因并保持已验证的 SAFE/SCAN 基线、寄存器兼容和测试。禁止为代码美观进行无关重构。

## 6. 任务分级

### A 类：普通开发

适用于 GUI 显示、日志、CSV、数据格式、非安全关键解析、小型 Python Bug 和普通文档同步。

```text
读取相关文件 -> 判断根因 -> 修改
-> targeted tests -> 完整相关测试 -> diff 检查 -> 简短交接
```

普通任务不启动独立审查线程，不重复全仓审查，不读取无关历史，也不运行不相称的高成本验证。

### B 类：FPGA/MTS 关键任务

包括 RTL、SystemVerilog、Vivado、testbench、时钟/复位/CDC、signed/位宽/定点/饱和、寄存器、`MAGIC/VERSION`、SAFE/SCAN/HOLD/P_LOCK/PI_LOCK、LOCK HERE、CAPTURE_LOCK_POINT、OUT2/PZT、Kp/Ki/polarity、bias/setpoint/limit、counts/电压校准、模式切换及硬件/闭环完成声明。

```text
主线程分析与最小实现
-> 运行相关验证
-> 一次未参与实现的独立工程复核
-> 只修复 Blocker/High
-> 针对修复点复验
```

独立复核不直接改代码，只检查：

1. 需求和最终功能路径。
2. RTL signed、位宽、流水线、reset、模式、限幅和负值/极值。
3. host/RTL 地址、模式、单位、readback、capture 和身份一致性。
4. SAFE、输出跳变、极性、Kp/Ki、PZT range、stale capture 和异常停止。
5. 测试是否真实运行，是否混用软件、GUI、硬件和闭环证据。

输出仅包含严重级别、文件与位置、实际风险、证据和最小修复建议。只有 `Blocker` 和 `High` 阻止继续；禁止格式或风格问题阻塞工程。默认一次复核；仅修复 Blocker/High 后做一次针对性复验。

## 7. P-only Gate 路线

### Gate 1：MTS error 可用

确认 IN1 PD、IN2 REF、OUT1 色散型 error、目标零交叉、无饱和且对应目标谱线。

### Gate 2：OUT2 扫频可信

确认 SCAN 中心、幅度、频率、示波器真实电压、CH4 command 与 OUT2 的关系及 PZT safe range。

### Gate 3：人工锁点可信

确认点击坐标、CH1/CH3/CH4 同一 capture、过零插值、`ERROR_SETPOINT`、`LOCK_BIAS`、readback，且不使用旧 capture 或历史 CSV 锁点。

### Gate 4：Kp=0 无扰切换

```text
SCAN -> 选点 -> CONFIRM -> HOLD 或 LOCK HERE Kp=0
```

确认谱线仍在目标附近、OUT2 无危险跳变、`LOCK_BIAS` 与实际输出一致、无 saturation，随后 SAFE。

### Gate 5：最小非零 Kp

从人工批准的最小 Kp 开始；Ki=0；polarity 人工确认；correction/absolute limit 生效；观察 error 和 OUT2，失败立即 SAFE。

### Gate 6：P-only 稳定

确认不立即失锁、error RMS 降低、OUT2 不长期饱和、仍有余量、多次可重复进入同一锁点并保存前后数据。Gate 6 通过前禁止进入 PI。

## 8. 唯一硬件实验格式

Codex 无法操作真实设备。需要用户实验时，一轮只给一个 Gate 内动作，并明确：

1. 目的。
2. 接线及 PZT 是否连接。
3. 示波器负载、耦合和探头倍率。
4. 软件参数、MODE、Kp、Ki、polarity 和 safe min/max。
5. 操作顺序。
6. PASS 与 FAIL 判据。
7. 立即 SAFE 条件。
8. 用户需返回的截图、CSV、readback 和测量数值。

禁止在同一轮同时做输出校准、LOCK HERE、翻 polarity、提高 Kp 和 PI。

## 9. 固定架构与安全边界

```text
IN1 = PD
IN2 = REF
OUT1 = laser_error
OUT2 = selected_out2
MODE=0 SAFE
MODE=1 SCAN
MODE=2 HOLD
MODE=3 P_LOCK
MODE=4 PI_LOCK candidate
MAGIC = 0x4D545330
```

永久规则：

1. OUT2 只能连接当前 Gate 明确授权的激光器专用 PZT/Scan 输入和测量设备。
2. 禁止 OUT2 连接激光器电流调制输入、D2-125 `Servo Output`、D2-125 `Aux Output` 或任何其他有源输出端；禁止两个输出端并联。
3. `MAGIC/VERSION` 不匹配、通信失败、SAFE 不可确认、OUT2 越界、saturation、削顶、异常跳变、反馈方向或 polarity 无法解释、readback 不一致、锁点非当前 capture、接线/示波器条件不明时，立即请求 SAFE 并停止。
4. Codex 不自动增加 Kp、翻转 polarity、增加 Ki、放宽 limit、扩大 PZT safe range、再次 LOCK、自动重锁或进入下一 Gate。
5. 未经用户对当前单项明确授权，不修改 RTL、Vivado 工程、寄存器地址/语义、`MAGIC`、`VERSION` 或 bitstream。
6. Codex 不运行 synthesis/implementation，不生成或烧录 bitstream。
7. 没有用户真实实验结果，不得声称激光已锁定、自动重锁、AI 优化或长期稳频完成。

## 10. 证据等级

只使用：

```text
[IMPLEMENTED]
[AUTOMATED VERIFIED]
[USER GUI VERIFIED]
[USER HARDWARE VERIFIED]
[FAILED]
[NOT VERIFIED]
```

不得把代码存在当测试通过、测试通过当 GUI/硬件通过、bitstream 生成当烧录成功、身份匹配当电压正确、CH4 `selected_out2` 当真实 OUT2/loaded PZT、电压正确当锁定、HOLD 当 P-only、短时闭环当长期稳频。

记录必须按需区分 FPGA raw counts、host 计算值、GUI ideal equivalent、calibrated estimate、pre-DAC `selected_out2`、DAC 真实 OUT2、loaded PZT 节点、光谱位置、MTS error zero crossing、P-only 闭环和长期稳定度。

## 11. 验证与记录

- Python 修改至少运行相关 `tabnanny`、修改文件 `py_compile`、`pytest --collect-only`、targeted tests 和完整 software tests。
- RTL 修改优先运行现有 testbench、lint/编译和工程 source/file-set 检查。未实际运行 synthesis/implementation/timing 时不得声称通过。
- 规则或文档修改至少运行 `git diff --check`、精确 conflict-marker 检查、`git diff --stat` 和相关 diff。
- 不得删除、skip、xfail 或弱化安全测试。任何失败如实报告。
- 只有实现、验证或实验状态变化时，更新 `version/STATUS.md`、当前 `DEVELOPMENT_LOG.md` 和必要的 `version/HARDWARE_VALIDATION.md`；计划不能写成完成。

## 12. 交接

只报告当前 Stage/Gate/Blocker、实际修改、真实验证、独立复核 Blocker/High、证据等级、唯一下一步和 Git 边界。涉及硬件时必须写清接线、参数、PASS/FAIL、返回数据和 SAFE 条件。

不自动执行 `git add`、commit、push、pull、reset、clean、rebase 或 amend。
