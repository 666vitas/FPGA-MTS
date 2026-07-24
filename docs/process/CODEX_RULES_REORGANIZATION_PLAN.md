Status: SUPPORTING
Effective-Gate: LOCK-MVP-T0
Authority: SUPPORTING
Last-Updated: 2026-07-24
Supersedes: CODEX_RULES_REORGANIZATION_PLAN.md
Superseded-By: NONE

# FPGA-MTS Codex 规则整理与 Linien-inspired 协同架构方案

## 一、针对当前截图的直接判断

当前 implementation 的 hold 已通过，但 setup 未通过：

```text
WNS = -0.387 ns
TNS = -5.015 ns
19 个 setup failing endpoints
WHS = +0.052 ns
```

所以后续工作必须拆成两条有顺序的主线，而不能混在一轮里：

```text
主线 A：先得到 timing-clean LOCK_MVP_BUILD
主线 B：再整理上位机 → LockService → FPGA 的职责边界
```

GUI 重构不能与本轮 timing 修复一起大规模进行，否则 Codex 无法判断功能回归来自 RTL 还是上位机。

---

## 二、现有规则体系为什么容易冲突

当前项目中已经存在：

- 根目录 AGENTS/README/多个 AI review 入口；
- `version/STATUS.md`；
- `CURRENT_REVIEW_MANIFEST.md`；
- 多份 rules、SOP、roadmap、review、history；
- 新增的 Linien Basic Lock 项目说明书。

如果只要求 Codex“读取最新文件”，会出现三个问题：

1. Windows 修改日期不能表示规则权威性；
2. 新复制的旧文档会拥有最新时间；
3. Gate、架构 spec、实验记录可能互相覆盖。

正确方案不是继续增加 review，而是把文件分成五种权威等级：

```text
入口规则 > 当前 Gate > 当前事实 > active rules/spec > supporting/history
```

---

## 三、推荐目录

```text
E:\new\fpga_lock\v94
├── AGENTS.md
├── README.md
├── v0.94/
├── software/
├── docs/
│   ├── architecture/
│   │   └── FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md
│   ├── experiment_logs/
│   └── hardware/
└── version/
    ├── CURRENT_GATE.md
    ├── STATUS.md
    ├── CURRENT_REVIEW_MANIFEST.md
    ├── rules/
    │   ├── 00_SOURCE_OF_TRUTH_AND_CONFLICTS.md
    │   ├── 10_SAFETY_AND_HARDWARE_BOUNDARY.md
    │   ├── 20_FPGA_MTS_ENGINEERING_WORKFLOW.md
    │   ├── 30_HOST_FPGA_ARCHITECTURE.md
    │   └── 40_VERIFICATION_AND_EVIDENCE.md
    └── history/
```

### 新说明书的位置

用户现在放在根目录的：

```text
docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md
```

建议移动到：

```text
docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md
```

原因：它是长期架构说明，不是 Codex 总入口，也不是每日状态。根目录应保持只有 `AGENTS.md` 和 README 类入口。

---

## 四、唯一冲突算法

Codex 每次开始任务时执行：

```text
1. 读取 AGENTS.md
2. 读取 CURRENT_GATE.md
3. 读取 STATUS.md 顶部
4. 读取 CURRENT_REVIEW_MANIFEST.md
5. 只读取 manifest 标记 active 的规则和 spec
6. 检查文档头的 Status/Effective-Gate/Supersedes
7. 出现冲突时按 authority 排序，不按修改时间猜测
8. 仍不能裁决则停止并列出冲突
```

建议在 `CURRENT_REVIEW_MANIFEST.md` 中写精确路径和用途：

```markdown
# Active Review Manifest

Current Gate: LOCK-MVP-T0

## Mandatory
- AGENTS.md — global rules
- version/CURRENT_GATE.md — only active task
- version/STATUS.md — current verified facts
- version/rules/10_SAFETY_AND_HARDWARE_BOUNDARY.md
- version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md
- version/rules/30_HOST_FPGA_ARCHITECTURE.md
- version/rules/40_VERIFICATION_AND_EVIDENCE.md
- docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md

## Current code scope
- v0.94/rtl/red_pitaya_top.sv
- v0.94/rtl/custom_register_bank.sv
- v0.94/rtl/ramp_generator.sv
- v0.94/rtl/out2_lock_controller.sv
- <current failing-path source files>

## Supporting only
- software/redpitaya_lock_host/README.md
- docs/hardware/<active SOP>

## Excluded / history
- version/history/**
- version/v2/**
- version/v3/claude审查/**
- *_restored.py
```

---

## 五、上位机为什么显得杂乱

当前界面把四种不同角色放在同一页面：

1. 实验操作：连接、扫描、选点、Kp；
2. 示波器：RUN/STOP/SINGLE、通道；
3. 工程诊断：MAGIC、版本、readback、capture 状态；
4. 旧 acquisition：ARM LOCK、generation、raw diagnostics。

因此用户同时看到大量：

- 不可用按钮；
- `--`；
- Communication lost 重复提示；
- calibrated estimate 警告；
- ARM 与手动锁定混合；
- 正常实验和工程诊断混合。

这不是单纯“UI不好看”，而是职责没有分层。

---

## 六、Linien-inspired GUI 信息架构

### 页面 1：Experiment（默认）

只显示真实实验主线：

```text
顶部状态条：Connection | FPGA Version | Bitstream | Mode | Saturation | Lock State

左侧：
- Scan center
- Scan amplitude
- Scan frequency
- Safe range
- 当前唯一合法操作按钮

中央：
- PD
- ERROR
- OUT2
- target cursor

底部 Lock Bar：
- 当前 target
- HOLD/approach 状态
- Kp / polarity
- error RMS
- SAFE（始终可见）
```

按钮由状态机决定，不同时显示整排无效按钮：

```text
SAFE            → START SCAN
SCANNING        → CAPTURE / PICK TARGET / STOP
TARGET_SELECTED → HOLD TARGET / RESCAN
HOLDING         → APPROACH / RESCAN
READY_TO_LOCK   → ENTER P_LOCK Kp=0
P_LOCK_KP0      → APPLY Kp=4
P_LOCK_ACTIVE   → NEXT Kp / SAFE
```

### 页面 2：Diagnostics

显示：

- MAGIC/VERSION/readback；
- counts 与 volts；
- capture stats；
- error mean/std/RMS；
- selected→hold delta；
- correction margin；
- communication logs；
- loaded PZT calibration。

### 页面 3：Engineering

默认隐藏，包含：

- raw register read/write（只读优先）；
- capture length/decimation；
- REF debug；
- deterministic ARM；
- generation/event；
- legacy diagnostic actions。

ARM 不再出现在默认实验页。

---

## 七、上位机与 FPGA 如何共同维护实验

### 1. 参数拥有关系

| 数据 | 唯一拥有者 |
|---|---|
| 用户设定值 | ParameterStore / LockService |
| 寄存器地址和编码 | RegisterMapper |
| FPGA 当前模式和输出 | FPGA readback |
| 波形 | AcquisitionService Frame |
| GUI 显示值 | 从 Store/Frame 投影，不另存副本 |
| 锁定状态 | LockService |
| 实时 P 反馈 | FPGA |

### 2. 状态同步

每个命令必须采用：

```text
command request
→ validation
→ register transaction
→ FPGA readback
→ update state
→ publish GUI event
```

不能先把 GUI 标签改成 SCANNING，再假定 FPGA 成功。

### 3. 断线行为

- GUI 断线：LockService 记录通信失败；
- 当前 Phase A 无法保证远端 SAFE 时，界面必须显示 `SAFE NOT CONFIRMED`；
- Phase B 板端 server 完成后，由 server watchdog 决定失联策略；
- 不得把“发送了 SAFE 命令”写成“硬件已 SAFE”，除非有 readback。

### 4. Phase A 与 Phase B

#### Phase A：现在

```text
GUI → LocalClient → LockService → RegisterMapper → existing SSH backend → FPGA
```

目标是最小重构和真实锁定，不改变通信基础。

#### Phase B：H4 之后

```text
GUI → RPC client → Red Pitaya Lock Server → mmap → FPGA
```

此时 GUI 关闭后锁定仍运行，并可重连恢复状态，更接近 Linien。

---

## 八、执行顺序

### Gate 0：规则整理（只改文档）

- 更新 AGENTS；
- 创建 CURRENT_GATE；
- 缩短 STATUS，只留当前事实；
- 更新 manifest；
- 将说明书移到 docs/architecture；
- 旧 review 移入 history 或标记 excluded。

### Gate 1：Timing-clean LOCK_MVP_BUILD

- 隔离 ARM 综合；
- 保留最小实时链；
- timing closure；
- 不重构 GUI。

### Gate 2：Host/FPGA Contract

- 建 RegisterMapper；
- 统一版本/寄存器/编码；
- 先迁移 CONNECT、identity、SAFE、SCAN。

### Gate 3：Experiment GUI

- 建 LockService 状态机；
- 改默认实验页；
- 把 diagnostics/engineering 分页；
- 不改变 FPGA 锁定算法。

### Gate 4：HOLD + approach + P_LOCK

- 完成真实 H1-H4 验收。

### Gate 5：Board Server

- 迁移服务到 Red Pitaya；
- GUI 变 RPC client；
- 重连恢复。

---

## 九、给 Codex 的第一次规则整理指令

```text
你现在只执行“FPGA-MTS 规则体系整理”，不修改 RTL、Python 功能或 GUI。

项目根目录：E:\new\fpga_lock\v94

先读取：
1. AGENTS.md
2. version/STATUS.md
3. version/CURRENT_REVIEW_MANIFEST.md
4. version/rules/20_FPGA_MTS_ENGINEERING_WORKFLOW.md
5. 根目录 docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md
6. README.md

当前用户提供的 Vivado 事实：
- WNS = -0.387 ns
- TNS = -5.015 ns
- setup failing endpoints = 19
- WHS = +0.052 ns
- hold failing endpoints = 0

任务：

A. 不删除任何历史内容，先创建备份或移动到 version/history。
B. 将根 AGENTS.md 整理成唯一总入口：只含长期规则、冲突优先级、安全、证据措辞和强制读取顺序。
C. 新建 version/CURRENT_GATE.md，当前 Gate 设为 LOCK-MVP-T0：创建 timing-clean LOCK_MVP_BUILD。
D. 重写 version/CURRENT_REVIEW_MANIFEST.md，使其只列当前 active 文件、当前代码范围、supporting 和 excluded/history。
E. 将 docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md 移到 docs/architecture/，保持内容，不把它设为高于 CURRENT_GATE 的规则。
F. 给 active Gate/rules/spec 增加统一元数据头：Status、Effective-Gate、Authority、Last-Updated、Supersedes、Superseded-By。
G. 检查 README/STATUS 中旧 VERSION、旧 capture 描述和旧 Gate，只修正文档冲突，不修改实现。
H. 不创建新的 review 报告；输出一个简短变更摘要即可。

冲突优先级：
用户本次指令 > AGENTS安全与范围 > CURRENT_GATE > STATUS > manifest > active rules > active spec > supporting > history。
禁止按文件修改日期决定最新。

最终回复必须给出：
1. 修改/移动文件列表；
2. 新的 source-of-truth 层级；
3. 被标记为 history/excluded 的文件类型；
4. 仍存在的文档冲突；
5. 未修改的 RTL/GUI；
6. 用户下一步只执行什么。
```

---

## 十、规则整理完成后给 Codex 的 Timing 指令骨架

```text
当前 Gate：LOCK-MVP-T0。
只处理 LOCK_MVP_BUILD 的 setup timing closure。

先读取 AGENTS、CURRENT_GATE、STATUS、manifest 和 manifest 指定的 RTL/报告。

当前 implementation：WNS -0.387 ns，TNS -5.015 ns，19 setup endpoints，hold pass。

必须先按 startpoint/endpoint/clock/path group 对 19 条 failing endpoint 分类，再决定修改。
不得看到 timing failure 就大规模重写 custom_register_bank。

本轮目标：
- 通过 build parameter/generate 将 deterministic ARM 从 LOCK_MVP_BUILD 的综合路径移除；
- 保留 SCAN/HOLD/P_LOCK/capture/limits/SAFE；
- D1_ARM_BUILD 源码和测试不删除；
- 增加两个 build 的 RTL/test 证明；
- 给出用户运行 Vivado implementation 的精确步骤。

不修改 GUI，不增加新功能，不声称 timing passed。
```
