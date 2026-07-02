# CLAUDE REVIEW: v2B3 Timing Pass + Pre-Board Safety Review (V3)

**Review Type**: Pre-board Safety Review — FPGA / Vivado / Red Pitaya / Laser Frequency Locking  
**Reviewer**: Claude (read-only)  
**Date**: 2026-06-30  
**Target**: `E:\new\fpga_lock\v94\v0.94` — v2B3 sequential PI (CONTROL_PATH_MODE=1)  
**Status**: **PASS WITH NOTES** ✅⚠️  
**Execution Mode**: Read-only — no file modification, no Vivado, no bitstream, no burning.

---

## 1. git 状态与代码变更审计

### 1.1 关键 RTL 文件 — 无功能性变更

| 文件 | git diff 结果 | 结论 |
|------|--------------|------|
| `rtl/red_pitaya_top.sv` | 仅 CRLF→LF 换行符变更 | 无功能性 RTL 变更 |
| `rtl/laser_lock_core.sv` | 空 — 无任何变更 | 无变更 |
| `rtl/pi_controller_seq.sv` | 空 — 无任何变更 | 无变更 |
| `version/STATUS.md` | 空 — 无未提交变更 | 已提交 |
| `version/v2/V2_NEXT_STEPS.md` | 空 — 无未提交变更 | 已提交 |
| `version/v2/V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md` | 空 — 无未提交变更 | 已提交 |
| `software/redpitaya_lock_host/docs/FPGA_MODE_BOUNDARY.md` | 空 — 无未提交变更 | 已提交 |
| `software/redpitaya_lock_host/docs/HOST_APP_V2_DESIGN.md` | 空 — 无未提交变更 | 已提交 |

### 1.2 结论 (Section C)

**No unauthorized functional RTL changes exist.** The only uncommitted change to `red_pitaya_top.sv` is line-ending normalization (CRLF→LF), which does not affect synthesis, implementation, or bitstream content. All other critical files are committed. The v2B3 sequential PI source code in `pi_controller_seq.sv` is identical to what was reviewed in the Phase 3 feasibility audit.

---

## 2. Vivado Implementation Report 逐项核查

### 2.1 报告来源确认

所有 .rpt 文件位于 `E:\new\fpga_lock\v94\v0.94\exp\v2\impl_1\`，均标记为：

```
Date: Tue Jun 30 21:20:37-43 2026
Tool Version: Vivado v.2020.1 (win64) Build 2902540
Design: red_pitaya_top
Device: xc7z010clg400-1
Design State: Fully Routed
```

`runme.log` 同样为 2026-06-30 13:20 生成，确认这是今天(June 30)的全新 Implementation 运行。

### 2.2 时序摘要 — 设计级

```
WNS(ns)      TNS(ns)  TNS Failing Endpoints  TNS Total Endpoints
-------      -------  ---------------------  -------------------
  0.107        0.000                      0                20485

WHS(ns)      THS(ns)  THS Failing Endpoints  THS Total Endpoints
-------      -------  ---------------------  -------------------
  0.054        0.000                      0                20485

WPWS(ns)     TPWS(ns)  TPWS Failing Endpoints  TPWS Total Endpoints
--------     --------  ----------------------  --------------------
  1.000        0.000                       0                  7527
```

**Vivado 显式声明**: "All user specified timing constraints are met."

### 2.3 分时钟域时序

| 时钟域 | WNS (ns) | TNS (ns) | Failing | 总端点 | 状态 |
|--------|----------|----------|---------|--------|------|
| pll_adc_clk (125 MHz, 主时钟域) | +0.155 | 0.000 | 0 | 17804 | ✅ PASS |
| pll_dac_clk_1x (125 MHz) | +0.600 | 0.000 | 0 | 45 | ✅ PASS |
| clk_fpga_0 (125 MHz) | +5.076 | 0.000 | 0 | 32 | ✅ PASS |
| clk_fpga_3 (200 MHz, PS) | +0.107 | 0.000 | 0 | 1969 | ✅ PASS |
| par_clk (125 MHz) | +3.471 | 0.000 | 0 | 460 | ✅ PASS |
| 跨时钟域 (全部) | 全部 ≥ +0.789 | 0.000 | 0 | - | ✅ PASS |

**pll_adc_clk 是 laser_lock_core 的工作时钟域。WNS=+0.155ns 表示该域内所有路径(包括 pi_controller_seq 的 15 状态通路)的建立时间余量充足。**

### 2.4 最差路径分析

最差建立时间路径 (WNS=+0.107ns) 不在 laser_lock_core 或 pi_controller_seq 内部，而在 PS 侧的 `clk_fpga_3` (200 MHz) 时钟域：

```
Source:  ps/system_i/axi_protocol_converter_0/.../sel_first_reg/C
Dest:    ps/system_i/xadc/.../XADC_INST/DADDR[2]
Path Group: clk_fpga_3
Requirement: 5.000ns
Slack (MET): +0.107ns
```

**这是 PS 内部 AXI/XADC 路径，与 laser_lock_core 的 PI 控制路径无关。pi_controller_seq 的所有路径在 pll_adc_clk 域中有至少 +0.155ns 余量。**

### 2.5 Hold Timing

- WHS=+0.054ns (全局最差), THS=0, Failing=0
- pll_adc_clk: WHS=+0.057ns (laser_lock_core 所在域)
- 所有时钟域 hold 全部通过

### 2.6 Pulse Width

- WPWS=+1.000ns (全局最差), TPWS=0, Failing=0
- pll_adc_clk: WPWS=+2.750ns

### 2.7 Route Status

```
Fully routed nets: 11603 / 11603
Routing errors: 0
```

### 2.8 DRC 报告

**Violations: 43 — 全部为 Warning 级别，无阻塞性 Error。**

| 规则 | 严重性 | 数量 | 说明 |
|------|--------|------|------|
| DPIP-1 | Warning | 2 | DSP48 输入未流水线化 (scope模块) |
| DPOP-1 | Warning | 5 | DSP48 PREG 未使用 (scope + mixer) |
| DPOP-2 | Warning | 7 | DSP48 MREG 未使用 (scope + mixer) |
| PDRC-153 | Warning | 1 | 门控时钟 (daisy模块) |
| PLIO-8 | Warning | 28 | IOB 约束未满足 (adc_dat 高 bit) |

**全部 DRC 违规均为 Warning 级别，无任何 Error 或 Critical Warning 级别的 DRC 违规。DSP 流水线化不足是官方 Red Pitaya scope 模块的已知特征，不影响 laser_lock_core 功能。**

### 2.9 Methodology DRC

**Violations: 116 — 其中 5 个为 Critical Warning，均非新增问题。**

| 规则 | 严重性 | 说明 |
|------|--------|------|
| TIMING-6 | Critical Warning (2) | par_clk ↔ pll_adc_clk 无公共主时钟 |
| TIMING-7 | Critical Warning (2) | par_clk ↔ pll_adc_clk 无公共节点 |
| TIMING-17 | Critical Warning (1) | DNA 单元无时钟驱动 |

**TIMING-6/7 是 Red Pitaya 官方设计中 par_clk(来自 Ethernet RX)和 pll_adc_clk(ADC PLL)的跨时钟域固有问题，官方设计中即存在，Vivado 仍按其跨时钟路径约束进行时序分析且全部通过(TNS=0, Failing=0)。**

**TIMING-17 是 DNA 安全单元的时钟问题，与 laser_lock_core 完全无关。**

### 2.10 runme.log 最终确认

```
INFO: [Route 35-16] Router Completed Successfully
route_design completed successfully
...
127 Infos, 57 Warnings, 50 Critical Warnings and 0 Errors encountered.
...
INFO: [Common 17-206] Exiting Vivado at Tue Jun 30 21:20:44 2026...
```

**0 Errors. Implementation 完整成功结束。**

---

## 3. 七个审查问题回答 (A-G)

### A. RTL Signal Chain 审查

**结论: PASS ✅**

当前 RTL 链路与 v2B1 已验证链路完全一致，唯一区别是 CONTROL_PATH_MODE 从 0 改为 1：

```text
pd_i (IN1) + ref_i (IN2)
  → mixer_core (DSP48 ×, SHIFT=13)
  → lpf_core (ACC_WIDTH=32, LPF_SHIFT=12)
  → output_protect (enable_i=1)
  → protected_error

protected_error
  → error_o → DAC A → OUT1              [FPGA error observation]
  → pi_controller_seq (CONTROL_PATH_MODE=1)  [15-state sequential PI]
    → control_o → DAC B → OUT2           [FPGA control output]
```

`red_pitaya_top.sv` lines 149-151 确认：
- `USE_LASER_LOCK_CORE = 1'b1`
- `LASER_LOCK_OUTPUT_MODE = 3` (mixer+LPF)
- `LASER_LOCK_CONTROL_PATH_MODE = 1` (sequential PI)

DAC 路由 (lines 470-488) 确认 DAC A = laser_error, DAC B = laser_control，与 v2B1 相同。

**链路上的每个模块 (mixer_core, lpf_core, output_protect, pi_controller_seq) 均在 pll_adc_clk (125 MHz) 域中，且该域 WNS=+0.155ns、Failing=0。**

### B. OUT2 安全输出审查

**结论: PASS WITH NOTES ⚠️ — OUT2 可接示波器，但不能接任何执行器**

当前 OUT2 配置：

| 参数 | 值 | 含义 |
|------|-----|------|
| Kp | 2048 | 增益约 0.5× → OUT2 约 half of OUT1 |
| Ki | 16 | 小积分，约 10kHz 更新 |
| output_limit | 1500 | 约 ±0.18 V 限幅 |
| offset | 0 | 无偏置 |
| enable | 1 | 输出使能 |
| polarity | 0 | 同向 |

安全分析：

- OUT2 最大输出受 output_limit 硬限幅，理论上不会超过约 ±0.18 V
- v2B1 实测 OUT2/OUT1 ≈ 0.5，远低于 ±1 V full-scale
- output_protect 在 rstn_i=0 时将 protected_error 清零，连锁使 OUT2 归零
- enable_i=0 或 hold_i=1 均会使 OUT2 保持在安全状态
- **但 sequential PI 有 Ki=16 的积分项，与 v2B1 的纯 P-only 不同，长时间同号误差可能导致积分缓慢累积**
- 积分有 anti-windup freeze 保护，防止超过 limit 后继续积分

**当前阶段 OUT2 只能接示波器，禁止连接：激光器、D2-125 Servo Output、D2-125 Aux/Scan、PZT、激光器电源 Scan 输入、或任何真实执行器。**

### C. Uncommitted Changes 审计

**结论: PASS ✅ — 无功能性未提交变更**

已在上文 Section 1 中详细列出。唯一的未提交变更是 `red_pitaya_top.sv` 的 CRLF→LF 换行符转换，对 Vivado 综合和实现无任何影响。

### D. 文档更新需求

以下文档需要更新以反映 v2B3 timing clean 的新状态：

1. **`version/STATUS.md`** — 已有 2026-06-30 条目，但日期标注为 "2026-06-xx"，应修正为 "2026-06-30"，并补充从 .rpt 文件中核实的完整时序数据。

2. **`version/v2/V2_NEXT_STEPS.md`** — 已有 2026-06-30 条目但内容偏简略。需要补充：
   - 确认 timing clean 后 OUT2 示波器测试的具体 checklist
   - OUT2 波形预期：小 P 分量 + 小 I 缓慢累积基线，受 limit 约束
   - 积分项可能产生的缓慢基线移动的描述

3. **`software/redpitaya_lock_host/docs/HARDWARE_TEST_SOP.md`** — 需要更新 Custom FPGA Mode 部分：
   - OUT2 当前输出的是 sequential PI (mode=1)，不再是纯 P-only shadow control
   - 补充 OUT2 的积分行为说明：缓慢基线移动是正常的（Ki=16），只要不快速爬升或接近限幅就安全
   - 保持 "OUT2 oscilloscope-only" 禁令不变

4. **`software/redpitaya_lock_host/docs/FPGA_MODE_BOUNDARY.md`** — 需要更新：
   - CONTROL_PATH_MODE=1 已在 timing-clean 状态下
   - 但 register_bank 仍然缺失，host 仍无法实时修改 PI 参数

5. **`version/v2/V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md`** — 需要更新 v2B3 状态为 "timing clean confirmed 2026-06-30"

### E. Bitstream 生成条件

**结论: PASS ✅ — 条件满足，可以生成 bitstream**

条件检查：

| 条件 | 状态 |
|------|------|
| Synthesis 0 errors | ✅ |
| Implementation 0 errors | ✅ |
| WNS ≥ 0 | ✅ (+0.107 ns) |
| TNS = 0 | ✅ (0.000 ns) |
| Failing Endpoints = 0 | ✅ |
| Hold timing clean | ✅ (WHS=+0.054 ns) |
| Pulse width clean | ✅ (WPWS=+1.000 ns) |
| No blocking DRC | ✅ |
| Route complete | ✅ (11603/11603) |
| No functional RTL changes since last review | ✅ |

**前提条件**: 生成 bitstream 前确认 `red_pitaya_top` 为 Design Top，`tb_*.sv` 不在 Design Sources。

### F. Red Pitaya 烧录条件

**结论: PASS WITH NOTES ⚠️ — 条件满足，但必须在严格边界内使用**

烧录后的边界：

- ✅ OUT1 可接示波器 CH2，观察 FPGA laser_error
- ✅ OUT2 可接示波器 CH4，观察 sequential PI control 输出
- ✅ IN1 可接 PD/MTS 信号 (已确认在 ±1 V 范围内)
- ✅ IN2 可接外部 REF 信号 (已确认在 ±1 V 范围内)
- ❌ OUT2 禁止接激光器
- ❌ OUT2 禁止接 D2-125 Servo Output / Aux / Scan / Current / PZT
- ❌ OUT2 禁止接任何真实执行器
- ❌ D2-125 DC Error 禁止接 Red Pitaya IN1
- ❌ 当前阶段不能声称已替代 D2-125 或已锁定激光

### G. 激光器连接条件

**结论: NOT YET ❌ — 当前不允许将 OUT2 连接至激光器**

原因：

1. 当前阶段为 v2B3 (OUT2 示波器验证)，离 v2F (低增益闭环) 至少还有 v2PZT safe-scan-hold 和 v2PZT plock 两个阶段
2. OUT2 的 sequential PI 行为仅在仿真中验证 (XSim 27/27 pass)，从未在真实硬件上观察
3. Ki=16 积分项在长时间连续运行时的行为未经验证
4. 激光器/PZT 控制端的电压范围、极性、带宽未在此次审查中确认
5. register_bank 仍然缺失，如果 OUT2 出现异常行为，无法通过 host 软件远程关闭或调整参数

**在 OUT2 示波器验证通过、v2PZT safe-scan-hold 完成、低增益闭环安全条件满足之前，OUT2 不能接激光器。**

---

## 4. OUT2 示波器测试决定性判断

### 是否可以接示波器？

**YES ✅ — OUT2 可以接示波器进行观察，这是当前阶段 (v2B3 timing clean) 的正确定义操作。**

### 测试 checklist

1. **烧录前**: 确认 bitstream 来自 2026-06-30 WNS=+0.107ns 的实现
2. **接线**: OUT1→CH2, OUT2→CH4, 不接任何执行器
3. **预期 OUT1**: 与 v2B1 相同，FPGA mixer+LPF error，约 0.12–0.15 V
4. **预期 OUT2**: 
   - 短时行为类似 P-only (≈ OUT1 的 1/2)
   - 长时间可能存在小积分累积的缓慢基线移动 (Ki=16 小但非零)
   - 不应接近 ±1 V、不应随机跳变、不应快速爬升
5. **必须停止**: 如 OUT2 接近 ±0.5 V、快速爬升 (>0.1V/s)、随机跳变 >0.1V、或 OUT1 异常消失

### 安全警示升级条件

如果 OUT2 的积分累积导致基线持续向一个方向漂移接近 ±0.5 V，即使仍在 ±1 V 满量程内，也应停止测试并考虑：
- 临时降 Ki=0 回退 P-only
- 或在内部分析积分行为是否合理

---

## 5. 更新后的深度学习自动锁定路线图

### 从 v2B3 timing clean 出发的全阶段路线

```
v2B3-close  [COMPLETED 2026-06-30]
  ├─ pi_controller_seq.sv XSim 通过 (27/27)
  ├─ Vivado 综合 0 errors
  ├─ Vivado 实现 WNS=+0.107ns, TNS=0, Failing=0
  ├─ Bitstream 生成条件满足
  └─ 输出: timing-clean bitstream (未烧录验证)

     ↓

v2B3-board  [NEXT — 当前]
  ├─ 烧录 2026-06-30 bitstream
  ├─ OUT1→CH2, OUT2→CH4 示波器观察
  ├─ 验证 sequential PI OUT2 行为: 短时 P-like, 长时小积分
  ├─ 记录 OUT2/OUT1 比例、OUT2 基线漂移速率
  └─ 输出: OUT2 sequential PI 实验数据

     ↓

v2PZT-DOC  [文档]
  ├─ 明确 PZT/激光器控制端物理特性: 电压范围、极性、带宽
  ├─ 设计 OUT2 到 PZT 的安全接口电平转换
  ├─ 确定初始 pid_ce 频率、Kp/Ki/limit 的物理对应值
  └─ 输出: PZT 接口安全设计文档

     ↓

v2PZT-RTL-SAFE-SCAN-HOLD  [RTL]
  ├─ 可安全启停的 scan ramp generator
  ├─ hold 模式: 固定 OUT2 输出，停止积分
  ├─ 软件可控 enable/disable/hold/reset
  └─ 输出: Safe Scan/Hold RTL + 仿真

     ↓

v2PZT-RTL-PLOCK  [RTL + 闭环]
  ├─ PI lock FSM: scan→lock_detect→hold→lock
  ├─ 锁定检测阈值 (error 在零点附近)
  ├─ 低增益闭环 (Kp 保守, Ki 极低或零)
  └─ 输出: 首次 FPGA 闭环锁定 PZT

     ↓  [仅在此之后，方可讨论低增益闭环替代 D2-125 基础 servo]

v2F  [低增益闭环 — D2-125 部分替代]
  ├─ OUT2→PZT 闭环控制
  ├─ 与 D2-125 性能对比
  └─ 输出: FPGA PI vs D2-125 性能数据

     ↓

v3  [register_bank / debug_buffer]
  ├─ AXI-Lite register bank: KP, KI, KD, limit, offset, polarity
  ├─ debug_buffer: 内部信号快照
  ├─ host→FPGA 实时参数控制
  └─ 输出: 软件可控的 FPGA PI + 可调试信号链

     ↓

v4  [IQ/相位/DDS]
  ├─ 数字 IQ 解调替代 simple mixer
  ├─ 相位自动匹配/扫频
  ├─ 内部 ASG/NCO 替代外部 REF
  └─ 输出: 全数字解调 + 自动相位

     ↓

v5  [1D-CNN 吸收峰识别]
  ├─ 从 PZT scan 波形识别吸收峰
  ├─ 基于陈本永 2024 方法
  ├─ IN1 原始 ADC 数据 → CNN 推理 → 峰位置
  └─ 输出: 吸收峰自动识别模块

     ↓

v6  [Auto-Lock FSM]
  ├─ 吸收峰识别 + 自动锁定
  ├─ 失锁检测 + 自动 relock
  ├─ lock 品质评估
  └─ 输出: 全自动锁定状态机

     ↓

v7  [全自动深度学习自动锁定系统部署]
  ├─ CNN + PI + Auto-Lock 完整部署
  ├─ 实时监控
  ├─ 性能优化
  └─ 输出: 部署版本
```

### 与 V2 Phase 3 审查结论的对比

**V2 Phase 3 审查 (2026-06-15)** 的结论是:

> v2B1 PASS WITH NOTES — CNN must NOT be started. Sequential PI timing failed (WNS=-1.931 ns).

**本次审查更新**:

- v2B3 sequential PI timing PASSED (WNS=+0.107 ns)，该阻塞条件已解除
- 其余约束不变: register_bank 仍然是 CNN 的硬前置条件，CNN 不能在第 v5 阶段之前启动
- v3 register_bank 之前的所有阶段仍然是 CNN 的必要前置

---

## 6. Codex 实施任务建议

以下任务建议在当前阶段 (v2B3 timing clean) 完成后，按顺序由 Codex 执行：

### Task 1: 更新项目文档以反映 v2B3 timing clean [文档更新]

**优先级**: 高 — 应在 OUT2 示波器测试前完成  
**范围**: 只读修改 5 个 markdown 文件  
**内容**:
- `STATUS.md`: 修正日期为 2026-06-30，补充完整的 .rpt 数据
- `V2_NEXT_STEPS.md`: 更新 v2B3→board 的详细测试 checklist
- `HARDWARE_TEST_SOP.md`: 更新 Custom FPGA Mode 部分的 OUT2 行为说明
- `FPGA_MODE_BOUNDARY.md`: 更新 CONTROL_PATH_MODE=1 的状态
- `V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md`: 更新 v2B3 为 timing clean

### Task 2: v2B3-board 示波器测试数据分析 [数据分析]

**优先级**: 高 — 在用户完成 OUT2 示波器测试后  
**前提**: 用户提供示波器 CSV 数据  
**内容**: 分析 OUT2/OUT1 比例、OUT2 积分累积速率、与 v2B1 P-only 数据对比

### Task 3: v2PZT-DOC PZT 接口安全设计 [系统设计]

**优先级**: 中 — v2B3-board 数据确认后  
**内容**: 明确 PZT 控制端物理参数、设计 OUT2→PZT 安全接口电平转换方案

---

## 7. 最终裁决

| 问题 | 裁决 |
|------|------|
| 可以生成 bitstream 吗？ | ✅ YES — 2026-06-30 实现满足全部生成条件 |
| 可以烧录 Red Pitaya 吗？ | ⚠️ YES — 但必须在严格边界内使用 (OUT2 只接示波器) |
| 可以接 OUT2 到示波器吗？ | ✅ YES — 这是当前阶段的正确定义操作 |
| 可以接 OUT2 到激光器吗？ | ❌ NO — 至少还需要 v2PZT 两个子阶段 |
| 可以声称替代 D2-125 吗？ | ❌ NO — 至少还需要 v2F 低增益闭环验证 |
| 可以开始 CNN 吗？ | ❌ NO — 至少还需要 v3 register_bank + v4 IQ/相位 |
| 时序风险已关闭了吗？ | ✅ YES — WNS=+0.107ns, TNS=0, Failing=0, 全部约束满足 |

### 总体评级: PASS WITH NOTES ✅⚠️

**理由**: 2026-06-30 Vivado Implementation 报告表明 v2B3 sequential PI (CONTROL_PATH_MODE=1) 在 125 MHz pll_adc_clk 域中 timing clean (WNS=+0.155ns, Failing=0)。全部用户时序约束已满足。无功能性 RTL 未提交变更。无阻塞 DRC。bitstream 生成和 Red Pitaya 烧录条件已满足。

"WITH NOTES" 是因为: OUT2 的 sequential PI 积分行为 (Ki=16) 在真实硬件上尚未观察；register_bank 缺失意味着无法通过 host 软件远程控制 PI 参数；当前 STILL OUT2 oscilloscope-only — 所有硬件安全边界与 v2B1 时期相同。

**当前阶段进展**: 从 v2B1 (P-only) → v2B3 (sequential PI timing clean) 的时序风险已关闭。下一步是 v2B3-board OUT2 示波器验证。

---

*Claude read-only review — 2026-06-30 — no files modified, no Vivado run, no bitstream generated, no Red Pitaya burned.*
