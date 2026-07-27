# FPGA-MTS LOCK-MVP-L1 Read-Only Audit

**日期**: 2026-07-27
**审查人**: Claude (Opus 4.6)
**审查类型**: 严格只读独立审计
**审查范围**: v94 仓库，Effective-Gate LOCK-MVP-L1
**方法**: 所有分析均通过文件读取和代码审查完成；未运行 Vivado、未生成位流、未修改任何文件、未连接开发板

---

## 1. 摘要

| 项目 | 结果 |
|------|------|
| 仓库状态 | 4 个预期未提交文件；HEAD=76cf4534 |
| 活跃文档 | 3/4 存在冲突或过期 |
| Vivado 源码集 | 正确；LOCK_ACQ_IMPL=1 (SIMPLE)；正确的 RTL 文件 |
| 时序 | **已满足**: WNS=0.142ns, TNS=0, WHS=0.053ns, THS=0 |
| CDC | **问题**: TIMING-6/7 Critical Warnings, TIMING-10 Warning, XDC 中注释掉 CDC 伪路径 |
| FPGA RTL | FSM 正确；流水线对齐已验证；ARM/VALIDATE 协议正确 |
| Host 协议 | 命令编码正确；状态映射在关键路径中正确 |
| 测试覆盖率 | 23 个 RTL testbench + 5 个 Python 测试；无系统级集成测试 |
| 位流 | **不存在** — exp/v3-arm/ 中未找到 .bit 文件 |
| **结论** | **C — BLOCKED_BY_LOG_OR_HOST_DEFECT** |

---

## 2. 结论

### 判决: C — BLOCKED_BY_LOGIC_OR_HOST_DEFECT

v94 仓库包含一个正确设计的 L1 P-Only 锁定架构，该架构在结构上是健全的。FPGA FSM、主机命令编码、流水线对齐和时序收敛均为正确。然而，**阻止立即进行位流测试的一个阻塞性缺陷**使得本次审查的结论不是 A 或 B：

**主要阻塞缺陷**: XDC 约束文件包含两个被注释掉的 CDC 伪路径（`par_clk` ↔ `pll_adc_clk`），这些路径是 Red Pitaya Zynq-7010 PS-to-PL 寄存器接口的关键路径。这些被注释掉的约束在 Vivado methodology 报告中产生了 TIMING-6 和 TIMING-7 Critical Warnings（"No common primary clock between related clocks" / "No common node between related clocks"）。虽然 STA 通过跨域设置 `set_clock_groups` 或继承的 MIG 约束处理了多周期路径，从而设法实现了时序收敛，但**这种配置在 CDC 验证方面未经证明安全**。没有任何 CDC 报告，并且没有明确区分已经过同步器正确处理的 `par_clk`→`adc_clk` 跨域路径和确实需要约束覆盖的路径之间的差异。

这些被注释掉的伪路径最初在 Red Pitaya 官方参考设计中存在，这表明它们被注释掉在原始设计中是有意为之的——可能是因为官方设计依赖了已知良好且经过验证的同步器结构。然而，本项目的自定义寄存器组添加了大量的新跨域寄存器（所有 L1 影子寄存器、ACQ_COMMAND、ACQ_STATE 等），而**这些新添加的寄存器没有被明确验证与官方设计依赖的相同同步器保证兼容**。

用操作术语来说：一个含有这部分内容的位流可以被生成并且在开发板上正常工作。但在没有 CDC 验证或恢复这些伪路径的情况下，无法断言该项目符合其自身的工程标准（`20_FPGA_MTS_ENGINEERING_WORKFLOW.md` 要求"unconstrained paths=0"）。在解决此 CDC 可追溯性缺口之前，无法诚实地宣布位流"可安全烧录"。

**如果在以下情况下，此缺陷可以降级**: (a) 生成一份 CDC 报告，确认所有 `par_clk`→`adc_clk` 跨域路径都由正确标注了 ASYNC_REG 的同步器链处理，或 (b) 在仔细验证了从 PS AXI 时钟域进行的所有新添加的寄存器读取/写入不对齐导致的功能风险后，恢复被注释掉的伪路径。

**如果在以下情况下，结论会变为 A**: 生成了位流，包含了恢复的伪路径，在一份正式的 CDC 报告中确认了 0 条未同步的跨域路径，并且对完整的 L1 锁门控序列进行了集成测试。

### 关于判决的说明

- 这与 B（时序/约束阻塞）不同，因为 STA 指标（WNS, TNS, WHS, THS）表明时序可以满足——即使在当前被注释掉伪路径的情况下。
- 这与 A（准备就绪可进行位流测试）不同，因为 XDC 中存在一个已确认的 CDC 可追溯性缺口，这直接违反了项目自身的工程标准。
- 术语说明：本判决使用了 "BLOCKED_BY_LOGIC_OR_HOST_DEFECT" 模板，但根本问题严格来说是一个约束/CDC 可追溯性问题。在提供的 4 个选项中，C 是最匹配的，因为阻塞项不在 STA 结果中（那将是 B），也不在"逻辑是否正确"的抽象意义上（那将是 C，取决于对"逻辑缺陷"的广义解读）。被注释掉的伪路径是一个项目配置级缺陷 — 一个有意为之但未经验证的约束移除 — 阻碍了一个负责任的"准备就绪"声明。

---

## 3. 仓库状态

- **HEAD**: `76cf453408f9b54d50faa0ea7f34401bb5263e5d` (2026-07-20)
- **最后一次提交**: "v3LOCK-P0 Host Lock Point Selector review and fixes (read-only)"
- **分支**: `main`
- **工作树**: 根据 STATUS.md 有 4 个预期未提交文件；日期在 2026-07-26 之后

---

## 4. 活跃文档审查

| 文档 | 状态 | Effective-Gate | 问题 |
|------|------|-----------------|------|
| `AGENTS.md` | ACTIVE | ALL | 正确；定义信号语义、安全边界、文件优先级 |
| `CURRENT_GATE.md` | ACTIVE | LOCK-MVP-L1 | 声称"TIMING NOT VERIFIED" — **与 STATUS.md 冲突** |
| `STATUS.md` | ACTIVE | LOCK-MVP-L1 | 声称 WNS=0.142ns — **与 GATE 冲突**；自矛盾："task start working tree clean"但随后列出 4 个未提交文件 |
| `CURRENT_REVIEW_MANIFEST.md` | ACTIVE | LOCK-MVP-T0 | **过期**（当前门控是 LOCK-MVP-L1）；2026-07-24 后未更新 |
| `20_FPGA_MTS_ENGINEERING_WORKFLOW.md` | ACTIVE | 工程规则 | 要求开发板构建的 WNS≥0, TNS=0, unconstrained=0 |
| `FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md` | 参考 | 项目规范 | L1 状态编码已更新，SAFE→SCAN→ARM→ACQUIRING 流程已正确记录 |

**文档冲突计数**: 两对冲突（GATE/STATUS 时序声明，MANIFEST 门控级别），加上 STATUS.md 中的一个内部矛盾。

---

## 5. Vivado 源码集验证

**.xpr 分析** (redpitaya.xpr):
- 顶级模块: `red_pitaya_top`
- 器件: xc7z010clg400-1
- 活跃 RTL 文件: 12 个文件，均存在于 `rtl/` 中
- `LOCK_ACQ_IMPL` 默认值: 1 (SIMPLE)
- `USE_LASER_LOCK_CORE`: 1
- synth_1 和 impl_1 指向 `exp/v3-arm/`

**活跃 XDC 文件**:
1. `sdc/red_pitaya.xdc` (用户本地)
2. `prj/v0.94/sdc/red_pitaya.xdc` (Red Pitaya 官方)

两个文件包含的 `par_clk`↔`pll_adc_clk` 伪路径均被注释掉。

**重复检查**: 源码集中没有重复的模块定义。活跃源集中的所有 include 文件都通过 include 路径正确解析。

---

## 6. 周期级闭环审计

### 6.1 信号路由

```
adc_dat[0] (IN1/PD)
  → laser_lock_core → mixer_core (× ASG ch[0] sine)
  → lpf_core → laser_error
  → error_setpoint_corrector → lock_error
  → out2_lock_controller (在 P_LOCK 模式下)
  → selected_out2 → {selected_out2[13], selected_out2} → dac_dat_b (OUT2/PZT)
```
**判决**: PASS。信号路由从 IN1 到 OUT2 的每一步在单个 adc_clk 域中均可追踪。

### 6.2 流水线对齐

来自 simple_lock_acquisition.sv 的已声明参数: SAMPLE=1, CROSSING=2, SUPERVISOR=3, EVENT=1。OUT2_pipeline_latency = 8。

S0 样本对齐（第 494-516 行）：out2, error, setpoint, lock_error, abs_error, scan_direction, in_guard, direction_match, runtime_ok 所有信号在同一周期采样。

穿越检测器链：sample → detector_out2_q（1 个周期）→ crossing_w/crossing_event_q（2+1 个周期）。

触发器提交（custom_register_bank 第 490-497 行）：lock_bias, error_setpoint, correction_limit, absolute_limit, ki=0, integral_reset, mode=P_LOCK, enable=1 全部在同一个周期。

**判决**: PASS。流水线延迟一致且正确应用于整个闭环。

### 6.3 FSM 状态机

L1 状态编码: SAFE=0, SCAN=1, VALIDATING=2, ARMED=3, ACQUIRING=4, P_LOCKED=5, FAILED=6, FAULT=7。

转换 SA0: SAFE → SCAN（当 mode=1 且 enable=1）。
转换 S1: SCAN → VALIDATING（在 VALIDATE 命令时，如果 out2 在目标窗口内）。
转换 S2: SCAN → ARMED（在 ARM 命令时，如果 out2 在目标窗口内）。
转换 S3: ARMED → ACQUIRING（在实时穿越时，穿越数据被捕获）。
转换 S4: ACQUIRING → P_LOCKED（由监控器确认收敛）。
转换 S5: ACQUIRING → FAILED（由监控器检测到发散或超时）。
转换 S6: 任何 → SAFE（中止或故障时）。

**判决**: PASS。FSM 转换与规范匹配。VALIDATE 正确避免了断言 trigger_o 或更改 OUT2。

### 6.4 穿越检测器

基于滞回，需要 N 个连续样本在源侧，然后 N 个在目标侧。上下文验证包括 armed_i, runtime_ok_i, in_guard_i, scan_direction 匹配和 direction 匹配。pass_consumed_o 锁存器防止重触发，直到扫描退出并重新进入 guard。

**判决**: PASS。

### 6.5 Kp 斜坡和监控器

Kp 从预加载值斜坡上升到目标 Kp。伺服分频器可配置。监控器从 P_LOCK 转换后的 observe_shift 个周期开始检查发散。

**判决**: PASS。斜坡逻辑和监控器参数可配置且正确。

---

## 7. Host/FPGA 协议审计

### 7.1 MAGIC/VERSION 检查

- MAGIC: 0x4D545330 — 在主机和远程脚本中均匹配
- EXPECTED_VERSION: 0x00030100 — 为了向后兼容而接受
- SIMPLE_VERSION: 0x00030200 — 当前 FPGA 构建
- L1_CAPABILITY: 0x4C310001 — 在远程脚本中检查并标记为 "L1_ERROR_CROSSING"
- 远程脚本通过 L1_CAPABILITY 寄存器拒绝非 L1 构建

**判决**: PASS。

### 7.2 ARM/VALIDATE 命令编码

来自 `custom_fpga_scan_control.py`，`run_preload_acquisition()` 第 471-494 行：

```
ARM:       regs.write(REGISTERS["ACQ_COMMAND"], 1)    # 0x01
VALIDATE:  regs.write(REGISTERS["ACQ_COMMAND"], 8)    # 0x08
Abort:     regs.write(REGISTERS["ACQ_COMMAND"], 2)    # 0x02
ClearEvent: regs.write(REGISTERS["ACQ_COMMAND"], 4)   # 0x04
```

这些与 simple_lock_acquisition.sv 中的 W1P 命令解码匹配（CMD_ARM=0x01, CMD_ABORT=0x02, CMD_CLEAR_EVENT=0x04, CMD_VALIDATE=0x08）。

在发送 ACQ_COMMAND 之前，远程脚本会写入影子寄存器（TARGET_OUT2, TARGET_ERROR_SETPOINT, TARGET_WINDOW, TARGET_REQUIREMENTS, CORRECTION_LIMIT, ABSOLUTE_LIMIT, CONFIG_GENERATION），然后检查 CONFIG_VALIDATION 位 7。

**判决**: PASS。编码正确，影子寄存器写入顺序正确，验证检查在命令发送之前进行。

### 7.3 状态读取和解释

远程脚本对 ACQ_STATE 使用 FPGA L1 编码（SAFE=0, SCAN=1, VALIDATING=2, ARMED=3, ACQUIRING=4, P_LOCKED=5, FAILED=6, FAULT=7）。

`lock_service.py` 正确地将原始状态映射到主机 LockState 枚举（第 127-131 行）：
```python
2: LockState.VALIDATING,
3: LockState.ARMED,
4: LockState.ACQUIRING,
5: LockState.P_LOCKED,
```

主要 GUI (`main_window.py`) 直接使用来自有效载荷的原始 `acquisition_state` 值，并将 5 解释为 P_LOCKED，4 解释为 ACQUIRING。

**判决**: PASS。主机和远程脚本之间无状态编码不匹配。`custom_fpga_backend.py` 中的 `AcquisitionState` 枚举（SAFE=0, SCAN=1, ARMED=2, TRIGGER_CAPTURE=3, P_LOCK_KP0=4, P_LOCK_ACTIVE=5, FAULT=6）定义了不同的编码，但**在任何关键路径中均未使用**。该枚举是遗留的，并且不会影响运行时行为。

### 7.4 遗留路径检查

`lock_here()` 方法在第 1171 行仍然存在于 `custom_fpga_backend.py` 中。CURRENT_GATE.md 禁止将 `lock-here` 作为正常 L1 路径。然而，其存在本身并不妨碍 L1 流程——它只是一个未暴露给主采集工作流程的独立方法。

`CAPTURE_LOCK_POINT` 寄存器（0x5C）仍然定义在寄存器映射中。门控禁止将其作为正常 L1 路径。

**判决**: PASS（带有注意事项）。遗留路径存在但被禁用或未被 L1 工作流程使用。

### 7.5 命令前置条件

远程脚本在发送 ACQ_COMMAND 之前检查：
1. MAGIC 匹配（第 472 行）
2. VERSION 在 SUPPORTED_VERSIONS 中（第 474 行）
3. mode==1 且 enable==1（第 479 行）
4. 未饱和（第 481 行）
5. 采集状态 != VALIDATING（第 483 行）— **注意**: 错误消息显示"ARMED"，但代码检查的是 VALIDATING；这是误导性但逻辑正确，因为在 VALIDATING 期间不应进行重新配置。
6. 构建能力 == L1_ERROR_CROSSING（第 485 行）
7. CONFIG_VALIDATION 位 7 已设置（第 491 行）

**判决**: PASS（错误消息文本为次要问题）。

---

## 8. Vivado 构建证据

### 8.1 时序摘要（已布线）

| 指标 | 值 | 通过？ |
|------|-----|-------|
| WNS | 0.142ns | ✓ |
| TNS | 0.000ns | ✓ |
| WHS | 0.053ns | ✓ |
| THS | 0.000ns | ✓ |
| 不满足的端点 | 0 / 26835 | ✓ |
| 未布线的网络 | 0 | ✓ |

### 8.2 Methodology DRC 违规

| 规则 | 严重性 | 描述 | 计数 |
|------|--------|------|-------|
| TIMING-6 | Critical Warning | par_clk 和 pll_adc_clk 之间没有共同的主时钟 | 2 |
| TIMING-7 | Critical Warning | par_clk 和 pll_adc_clk 之间没有共同节点 | 2 |
| TIMING-17 | Critical Warning | DNA CLK 未被时钟信号到达 | 1 |
| TIMING-10 | Warning | 同步器上缺少 ASYNC_REG 属性 | 1 |
| TIMING-18 | Warning | 缺少输入或输出延迟 | 39 |
| TIMING-20 | Warning | 非时钟锁存器 | 17 |
| TIMING-28 | Warning | 由时序约束引用的自动派生时钟 | 2 |
| SYNTH-6 | Warning | RAM 块时序可能次优 | 18 |
| SYNTH-11 | Warning | DSP 输出未注册 | 7 |

### 8.3 check_timing 问题

| 类别 | 计数 | 与锁定相关 |
|--------|-------|-----------------|
| no_clock | 52 | 否（daisy tx_cfg_sel, hk daisy_mode, dna_clk） |
| unconstrained_internal_endpoints | 19 | 待分类 |
| no_input_delay | 17 | 待分类 |
| no_output_delay | 42 | 待分类 |

### 8.4 CDC 报告

**未找到**。exp/v3-arm/impl_1/ 中不存在 CDC 报告。`TIMING-10` 警告表明检测到了同步器链，但未使用 ASYNC_REG 属性进行注释，但这没有后续的 CDC 分析来验证。

### 8.5 位流

**未找到**。exp/v3-arm/ 中不存在 .bit 或 .bin 文件，在 exp/v3-arm/impl_1/ 的直接搜索中也不存在。

---

## 9. 约束审计

### 9.1 被注释掉的伪路径

在 `sdc/red_pitaya.xdc`（用户本地 XDC，第 216-226 行区域）和 `prj/v0.94/sdc/red_pitaya.xdc`（Red Pitaya 官方项目 XDC）中，以下关键 CDC 伪路径均被注释掉：

```tcl
#set_false_path -from [get_clocks par_clk]     -to [get_clocks pll_adc_clk]
#set_false_path -from [get_clocks pll_adc_clk] -to [get_clocks par_clk]
```

这些路径覆盖了 PS AXI 接口（`par_clk`，通常为 100 MHz）和 ADC PLL 输出（`pll_adc_clk`，125 MHz）之间的跨域穿越。本项目的自定义寄存器组通过此接口添加了大量新的跨域寄存器，包括：
- 所有 L1 采集影子寄存器（TARGET_OUT2, TARGET_ERROR_SETPOINT, TARGET_WINDOW 等）
- ACQ_COMMAND（W1P 编码：ARM, VALIDATE, Abort, ClearEvent）
- ACQ_STATE 寄存器
- 事件寄存器（仅 PS 读取，由 adc_clk 域更新）
- 所有监控寄存器（KP_EFFECTIVE, VALIDATE_EVENT_COUNT 等）

### 9.2 为什么这很重要

虽然静态时序分析报告 WNS=0.142ns > 0，STA 解决的是时序延迟，而不是跨时钟域的亚稳态问题。被注释掉的伪路径意味着 Vivado 将这些路径视为必须满足单周期时序，而不是将它们视为异步穿越。在硅片上：
- 如果同步器链存在且正确，该设计尽管有约束警告仍可正常工作
- 如果同步器链缺失或不充分，亚稳态可能导致偶发性的寄存器读取损坏或命令丢失

TIMING-10 警告确认了**至少检测到了一个同步器链**。挑战在于无法验证哪些 `par_clk`→`adc_clk` 穿越由同步器覆盖，哪些不是——因为没有生成任何 CDC 报告。

### 9.3 与锁定功能的相关性

PS 寄存器的写入是偶发性的（仅在 ARM, VALIDATE, Abort 或配置更新时）。一旦采集正在进行（ARMED → ACQUIRING → P_LOCKED），关键路径完全在 adc_clk 域中运行。只有中止和状态回读涉及 par_clk 域。因此：
- 在操作期间，写入命令丢失可能会阻止 ARM 或使中止失败
- 损坏的状态读取可能会向 GUI 显示错误的状态
- 在采集期间，锁定伺服本身不受影响

**底线**: 此 CDC 缺口是真实存在的，但不妨碍对核心锁定功能进行开发板测试——它只是增加了可靠性风险。然而，它确实妨碍了"准备就绪可安全烧录"的声明，因为该项目自身的工程标准要求 0 条无约束路径。

---

## 10. 测试覆盖率

### 10.1 RTL Testbench

存在 23 个 RTL testbench 文件。关键内容包括：
- `tb_simple_lock_acquisition.sv` — 测试 ARM, VALIDATE, 基本 FSM 流程
- `tb_l1_error_crossing_plant.sv` — 带模拟植物的端到端穿越检测
- `tb_l1_kp_ramp.sv` — Kp 斜坡单元测试
- `tb_l1_lock_supervisor.sv` — 监控器收敛/发散检测
- `tb_realtime_error_crossing_detector.sv` — 穿越检测器单元测试
- `tb_out2_lock_controller.sv` — OUT2 控制器 P 项
- `tb_custom_register_bank_basic.sv` — 寄存器组基本 CSR 测试

### 10.2 主机测试

5 个 Python 测试文件存在于 `software/redpitaya_lock_host/tests/` 中：
- `test_custom_fpga_backend.py` — 后端单元测试
- `test_custom_fpga_workflow.py` — 工作流程集成测试
- `test_lock_services.py` — 锁服务逻辑测试
- `test_waveform_preview.py` — 波形预览测试
- `test_operator_voltage_diagnostics.py` — 电压诊断测试

### 10.3 测试缺口

1. **没有完整的端到端系统测试**: 没有 testbench 或测试以完全集成的闭环方式将 `simple_lock_acquisition` 与 `laser_lock_core`, `mixer_core`, `lpf_core` 和 `out2_lock_controller` 连接起来。
2. **没有 CDC 验证测试**: 没有 testbench 验证来自 PS 时钟域的穿越是否正确同步。
3. **没有带噪声的植物模型**: `tb_l1_error_crossing_plant` 使用确定性穿越，而不是模拟真实光电二极管信号的噪声。
4. **没有压力测试**: 没有测试验证在快速连续的扫描穿越或并发中止/ARM 序列下的锁门控行为。
5. **没有主机- FPGA 集成测试**: 主机 Python 测试使用 mock 后端；没有测试在真实（或模拟）的 FPGA 寄存器上运行完整协议。

---

## 11. 风险登记册

| ID | 风险 | 严重性 | 可能性 | 缓解措施 |
|----|------|----------|-----------|------------|
| R1 | CDC 亚稳态导致 ARM 命令丢失 | 中等 | 低 | 恢复被注释掉的伪路径；生成并审查 CDC 报告 |
| R2 | 带噪声 PD 信号时穿越检测失败 | 中等 | 中等 | 增加穿越滞回和连续样本的硬件在环测试 |
| R3 | Kp 斜坡太快导致超调 | 中等 | 低 | 可配置的斜坡参数已经存在；根据植物响应进行调整 |
| R4 | 在嘈杂环境中出现假阳性穿越 | 低 | 中等 | 穿越连续样本要求缓解了此问题；可能需要调整 |
| R5 | 带长线缆时 OUT2 模拟输出噪声 | 低 | 未知 | 开发板测试将揭示这一点 |

---

## 12. 建议（只读）

这些操作**并未**由本审计执行，提供这些建议是为了指导后续开发。所有这些都在本审计的禁止操作清单范围内——它们是供用户以后运行的操作。

1. **恢复被注释掉的伪路径** (优先级 P0，预计 5 分钟)
   - 在 `sdc/red_pitaya.xdc` 中取消注释 `par_clk`↔`pll_adc_clk` 伪路径
   - 重新运行 `synth_1` 和 `impl_1`；验证 WNS 保持 ≥0

2. **生成 CDC 报告** (优先级 P0，预计 10 分钟)
   - 运行 `report_cdc -file red_pitaya_top_cdc_routed.rpt`
   - 验证所有 `par_clk`→`adc_clk` 穿越已被识别和同步
   - 记录结果

3. **为 CDC 同步器添加 ASYNC_REG 属性** (优先级 P1，预计 30 分钟)
   - 识别 `par_clk`→`adc_clk` 穿越的同步器 FF
   - 将 ASYNC_REG 属性添加到每个同步器链的两个阶段
   - 重新运行 synthesis 和 CDC 报告

4. **生成位流** (优先级 P0，预计 15 分钟)
   - 运行 `write_bitstream red_pitaya_top.bit`
   - 验证无关键警告

5. **分类 check_timing 项目** (优先级 P1，预计 1 小时)
   - 验证 19 个无约束内部端点中是否有任何与锁定相关的端点
   - 确认所有 17 个无输入延迟的项目用于非锁定 IO（daisy, 扩展端口）
   - 文档化哪些项目是故意的，哪些需要约束

6. **添加端到端集成测试** (优先级 P2)
   - 创建一个将 simple_lock_acquisition 与信号链连接的 testbench
   - 测试完整的 SAFE→SCAN→ARM→ACQUIRING→P_LOCKED 流程
   - 包含带有噪声的模拟 PD 信号

---

## 13. 方法说明

本审计完全通过静态文件分析进行——未进行工具运行、未生成位流、未连接开发板、未进行 git 操作、未进行 RTL 修改。用于分析的工具：Read, Glob, Grep。证据引用自实际的 RTL 源码行号和 Vivado 报告数据。

本审计没有：
- 假设时序收敛等于功能正确性
- 将 RTL 仿真通过等同于真实世界的锁定行为
- 将 WNS>0 视为设计安全的证据
- 将文档声明视为事实
- 推测缺失的证据（如 CDC 报告）
- 回溯或依赖早期审查的结论

---

## 14. 附录：已核实声明

| 声明 | 来源 | 核实状态 |
|--------|--------|------------------|
| LOCK_ACQ_IMPL = 1 (SIMPLE) | red_pitaya_top.sv | ✓ 已确认 |
| SIMPLE_VERSION = 0x00030200 | custom_register_bank.sv | ✓ 已确认 |
| L1_CAPABILITY = 0x4C310001 | 寄存器组 L1_CAPABILITY 寄存器 | ✓ 已确认 |
| ARM = 0x01 至 ACQ_COMMAND | 远程脚本行 494 | ✓ 已确认 |
| VALIDATE = 0x08 至 ACQ_COMMAND | 远程脚本行 494 | ✓ 已确认 |
| W1P 防重复保护 | custom_register_bank.sv | ✓ 已确认 |
| 时序已满足 (WNS=0.142) | Vivado 时序报告 | ✓ 已确认 |
| 位流存在 | exp/v3-arm/ 文件列表 | ✗ 已纠正：不存在 |
| CDC 报告存在 | exp/v3-arm/impl_1/ | ✗ 已纠正：不存在 |
| XDC 中的伪路径是活跃的 | sdc/red_pitaya.xdc | ✗ 已纠正：被注释掉 |
| 门控要求 0 无约束路径 | 20_FPGA_MTS_ENGINEERING_WORKFLOW.md | ✓ 已确认；当前构建有 19 个无约束内部端点 |
| 文档处于有效门控下 | CURRENT_GATE.md | ✗ 已纠正：MANIFEST 过期于 LOCK-MVP-T0 |

---

*审查结束。本报告是输出到 `docs/process/CLAUDE_REVIEW_2026-07-27_LOCK_MVP_L1_READ_ONLY_AUDIT.md` 的唯一文件。未进行任何修改。*
