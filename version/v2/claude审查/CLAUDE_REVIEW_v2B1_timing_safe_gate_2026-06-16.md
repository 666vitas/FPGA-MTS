# Claude Code v2B1 timing-safe 阶段审查报告

**审查日期**: 2026-06-22
**审查人**: Claude (只读审查，未修改任何 RTL/Testbench/Vivado 工程文件)
**审查触发**: 用户要求独立审查 v2B1 timing-safe P-only Shadow Control 修改是否合理，是否可继续 Vivado，是否可烧录上板
**审查范围**: `laser_lock_core.sv`, `pi_controller.sv`, `red_pitaya_top.sv`, `mixer_core.sv`, `lpf_core.sv`, `output_protect.sv`, `tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv`, `tb_pi_controller.sv`, Vivado exp/v2/impl_1/ 全套 report/log/bitstream, xsim/xvlog/xelab log, version/STATUS.md, version/v2/*.md, version/rules/*.md

---

## 0. 审查结论摘要

1. **当前项目已经恢复到 timing-safe P-only Shadow Control 路线。** 代码证据确凿：`USE_FULL_PI_CONTROLLER = 1'b0` 为默认值，generate 块中完整 pi_controller 仅在 `USE_FULL_PI_CONTROLLER=1` 时实例化，默认走 P-only 分支。
2. **当前代码修改边界合理。** 只修改了 `laser_lock_core.sv`（加 generate 块 + P-only 路径）、`tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv`（改测 P-only 默认路径）、version/ 下文档。`pi_controller.sv`、`red_pitaya_top.sv` 的核心逻辑、`mixer_core.sv`、`lpf_core.sv`、`output_protect.sv` 均未修改。
3. **Vivado synthesis / implementation 已经跑过且通过。** 2026-06-16 的 exp/v2 运行结果：synthesis 0 errors 0 critical warnings，implementation 0 errors，WNS=0.361 ns（正值，MET），TNS=0.000 ns，bitstream 已成功生成。
4. **可以烧录上板观察。** 前提是严格遵守 OUT2 只接示波器的红线。
5. **不缺少证据。** synthesis log、implementation log、timing summary、DRC report、methodology report、bitstream 全部存在且已审查。
6. **后续修复仍应交给 Codex。** 本轮审查未发现需要 Claude 介入修复的问题。

**结论三选一：可以烧录上板观察。**

---

## 1. 本轮审查范围

### 1.1 实际读取的文件

| 类别 | 文件 | 状态 |
|------|------|------|
| RTL | `v0.94/rtl/laser_lock_core.sv` (310 行) | 已完整读取，逐行审查 |
| RTL | `v0.94/rtl/pi_controller.sv` (179 行) | 已完整读取，确认未修改 |
| RTL | `v0.94/rtl/red_pitaya_top.sv` (706 行) | 已完整读取，确认核心未修改 |
| RTL | `v0.94/rtl/mixer_core.sv` | 确认未被本轮修改 (git diff HEAD 无输出) |
| RTL | `v0.94/rtl/lpf_core.sv` | 确认未被本轮修改 |
| RTL | `v0.94/rtl/output_protect.sv` | 确认未被本轮修改 |
| SIM | `v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` (230 行) | 已完整读取 |
| SIM | `v0.94/sim/tb_pi_controller.sv` | 已审查（via Codex 执行记录） |
| SIM log | `v0.94/xsim.log` | 已读取，18/18 全部 PASS |
| SIM log | `v0.94/xvlog.log` | 已确认存在 |
| SIM log | `v0.94/xelab.log` | 已确认存在 |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_timing_summary_routed.rpt` | 已读取关键部分 (337 行) |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_drc_routed.rpt` | 已读取关键部分 |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_methodology_drc_routed.rpt` | 已读取关键部分 |
| Vivado | `v0.94/exp/v2/synth_1/runme.log` (tail) | 已读取末尾 |
| Vivado | `v0.94/exp/v2/impl_1/runme.log` (tail) | 已读取末尾 |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top.bit` | 已确认存在 (2,083,850 bytes) |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_utilization_placed.rpt` | 已确认存在 |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_route_status.rpt` | 已确认存在 |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_power_routed.rpt` | 已确认存在 |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_clock_utilization_routed.rpt` | 已确认存在 |
| Vivado | `v0.94/exp/v2/impl_1/red_pitaya_top_bus_skew_routed.rpt` | 已确认存在 |
| SDC | `v0.94/sdc/red_pitaya.xdc` | 已确认存在且未被修改 |
| Docs | `GPT_README.md` | 已完整读取 |
| Docs | `version/STATUS.md` | 已完整读取 |
| Docs | `version/v2/V2_NEXT_STEPS.md` | 已读取关键部分 |
| Docs | `version/rules/06_V2_PID_DEVELOPMENT_RULES.md` | 已读取关键部分 |
| Docs | `version/rules/03_FPGA_CODE_REVIEW_RULES.md` | 已读取关键部分 |
| Docs | `version/v2/claude审查/CLAUDE_REVIEW_v2_v2a_feasibility_2026-06-15.md` | 已完整读取 |
| Docs | `version/v2/codex执行记录/CODEX_v2_0_doc_sync_2026-06-15.md` | 已完整读取 |
| Git | `git status --short` + `git diff --stat` + `git log --oneline -10` | 已执行 |

### 1.2 不存在 / 未找到 / 无法判断

以下项目在本轮审查中明确标注：

- **v0.94/exp/v2/synth_1/runme.log**：存在，已读取。
- **v0.94/exp/v2/impl_1/runme.log**：存在，已读取。
- **v0.94/exp/v2/impl_1/red_pitaya_top_timing_summary_routed.rpt**：存在，已读取关键路径。
- **v0.94/exp/v2/impl_1/red_pitaya_top.bit**：存在 (2,083,850 bytes)，生成于 2026-06-16 20:05。
- **所有 .rpt 文件**：均存在。
- **Vivado project .xpr**：存在 (`v0.94/project/redpitaya.xpr`)。
- **SDC 约束**：存在 (`v0.94/sdc/red_pitaya.xdc`, `red_pitaya_4ADC.xdc`, `red_pitaya_4adc_test.xdc`)。
- **无法从文件系统直接判断**：Vivado project sources 中是否引用了正确路径的 `laser_lock_core.sv`（需要用户在 Vivado GUI 中确认，见第 9 章）。

---

## 2. 当前项目真实状态

| 问题 | 答案 | 证据 |
|------|------|------|
| 当前阶段是否为 v2B1 | **是** | `version/STATUS.md` 标题 "v2B1 timing-safe P-only Shadow Control"；`laser_lock_core.sv` 注释 "v2B1 adds a Shadow Control path" |
| 当前是否是 timing-safe P-only Shadow Control | **是** | `USE_FULL_PI_CONTROLLER = 1'b0`（第 53 行）；默认进入 `g_timing_safe_p_only` generate 分支 |
| 当前是否已经不是完整 PI 上板路线 | **是** | 完整 `pi_controller` 仅在 `USE_FULL_PI_CONTROLLER=1` 时实例化（第 207 行）；默认 `=0`，不会进入 synthesis |
| 当前 OUT1 输出什么 | **FPGA mixer+LPF error（protected_error）** | `assign error_o = protected_error`（第 188 行）；`red_pitaya_top.sv` 路由到 DAC A / OUT1 |
| 当前 OUT2 输出什么 | **P-only shadow control（约 OUT1/2）** | `p_only_scaled_w = p_only_error_pol_w >>> 1`（第 277 行）；受 `output_limit=1500` 限制 |
| 当前 OUT2 是否可以接激光器 | **禁止** | 代码注释明确 "OUT2 remains oscilloscope-only"；`STATUS.md` 明确 "OUT2 禁止接激光器 PZT" |
| 当前是否有 ramp/sweep | **没有** | 代码中无任何 ramp/sweep 模块；`STATUS.md` 确认 |
| 当前是否有 scan/lock FSM | **没有** | 代码中无任何 FSM；`STATUS.md` 确认 |
| 当前是否有在线调参寄存器 | **没有** | 所有 PI 参数为 compile-time `parameter`，无 sys_bus 映射 |
| 当前是否可以声称已经替代 D2-125 | **不能** | `STATUS.md` 明确 "不能声称已经完成闭环锁定""不能声称已经完整替代 D2-125"；上轮 Claude 审查 (2026-06-15) 估算替代度约 40% |

---

## 3. 修改边界审查

### 3.1 允许修改且实际修改的文件

根据 `git diff HEAD` 和 `git log` 审查，本轮（2026-06-15 ~ 2026-06-16）实际修改文件：

| 文件 | 修改内容 | 合规 |
|------|----------|------|
| `v0.94/rtl/laser_lock_core.sv` | 新增 `USE_FULL_PI_CONTROLLER` 参数（默认 1'b0）；新增 `g_timing_safe_p_only` generate 分支；完整 PI 移入 `g_full_pi_controller` generate 分支 | ✅ 允许修改 |
| `v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` | 所有 DUT 实例化显式设置 `USE_FULL_PI_CONTROLLER(1'b0)`；新增 check 验证默认路径选择；tests 从 13→18 | ✅ 允许修改 |
| `version/STATUS.md` | 更新为 "v2B1 timing-safe P-only Shadow Control"；记录 timing failure 现象和恢复策略 | ✅ 允许修改 |
| `version/v2/V2_NEXT_STEPS.md` | 新增 2026-06-16 用户手动 Vivado timing 复查步骤 | ✅ 允许修改 |
| `version/v2/V2_DEVELOPMENT_ROADMAP.md` | 更新路线反映 timing-safe 默认 | ✅ 允许修改 |
| `version/v2/V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md` | 更新架构图 | ✅ 允许修改 |
| `version/rules/03_FPGA_CODE_REVIEW_RULES.md` | 新增 §0.0B v2B1 timing 审查硬规则 | ✅ 允许修改 |
| `version/rules/06_V2_PID_DEVELOPMENT_RULES.md` | 新增 §0.0B v2B1 timing-safe 默认路径规则 | ✅ 允许修改 |
| `version/rules/RULE_CODEX_ENGINEER_TEACHER.md` | 更新 Codex 指导 | ✅ 允许修改 |

### 3.2 应保持不变的核心文件 — 全部确认未修改

| 文件 | 状态 | 检查方法 |
|------|------|----------|
| `v0.94/rtl/pi_controller.sv` | **未修改** | `git diff HEAD` 无输出；Read 确认仍为 179 行原始 v2A 代码 |
| `v0.94/rtl/red_pitaya_top.sv` | **核心逻辑未修改** | `git diff HEAD` 无输出；`USE_LASER_LOCK_CORE=1'b1`、`LASER_LOCK_OUTPUT_MODE=3` 保持不变；laser_lock_core 实例化仅传入 `OUTPUT_MODE`，未传入 `USE_FULL_PI_CONTROLLER` |
| `v0.94/rtl/mixer_core.sv` | **未修改** | `git diff HEAD` 无输出 |
| `v0.94/rtl/lpf_core.sv` | **未修改** | `git diff HEAD` 无输出 |
| `v0.94/rtl/output_protect.sv` | **未修改** | `git diff HEAD` 无输出 |
| `v0.94/sdc/red_pitaya.xdc` | **未修改** | 文件时间戳为 Sep 26 2025 |
| `v0.94/project/redpitaya.xpr` | **Vivado 自动更新** | git diff --stat 显示 2860 行变更，属 Vivado 正常工程文件更新 |

**结论：修改边界严格合规。所有应保护的核心 RTL 未被触碰。**

---

## 4. laser_lock_core.sv 审查

### 逐项检查

| # | 检查项 | 结果 | 行号/证据 |
|---|--------|------|-----------|
| 1 | 是否存在 USE_FULL_PI_CONTROLLER 参数 | ✅ 存在 | 第 53 行 |
| 2 | 默认值是否为 1'b0 | ✅ `1'b0` | 第 53 行 |
| 3 | 默认路径是否为 timing-safe P-only | ✅ 是 | `g_timing_safe_p_only` 分支（第 247 行） |
| 4 | 默认路径是否不实例化完整 pi_controller | ✅ 不实例化 | pi_controller 仅在 `if (USE_FULL_PI_CONTROLLER)` 分支中（第 207 行） |
| 5 | 完整 pi_controller 是否只在 generate 分支中保留 | ✅ 是 | `g_full_pi_controller` generate 块（第 207-246 行） |
| 6 | 完整 pi_controller 是否只有 USE_FULL_PI_CONTROLLER=1 时才启用 | ✅ 是 | `if (USE_FULL_PI_CONTROLLER)`（第 207 行） |
| 7 | 默认 P-only 路径是否为 protected_error → polarity → arithmetic shift right by 1 → output_limit → registered control_o | ✅ 是 | 第 273-277 行 assign 链 + 第 289-301 行 always_ff |
| 8 | 默认 P-only 路径是否没有 DSP multiplier / 48-bit integrator / anti-windup / P+I+offset 长组合路径 | ✅ 没有 | P-only 路径只有 sign extension + mux + shift + comparator + register；纯组合逻辑深度极浅（~2-3 LUT levels） |
| 9 | pid_ce_q 是否只是 clock enable，不是新 clock | ✅ 是 | 第 296 行 `else if (pid_ce_q)` — 标准的 clock enable 用法 |
| 10 | control_o 是否在 clk_i 上寄存 | ✅ 是 | 第 289 行 `always_ff @(posedge clk_i)` |
| 11 | reset 时 control_o 是否清零 | ✅ 是 | 第 290-291 行 |
| 12 | PID_ENABLE_DEFAULT=0 时 control_o 是否清零 | ✅ 是 | 第 292-293 行（注：当前默认 PID_ENABLE_DEFAULT=1'b1，但逻辑存在） |
| 13 | PID_HOLD_DEFAULT=1 时 control_o 是否保持 | ✅ 是 | 第 294-295 行（注：当前默认 PID_HOLD_DEFAULT=1'b0） |
| 14 | output_limit 是否仍然限制 OUT2 幅度 | ✅ 是 | 第 279-287 行 comparator chain，limit=1500 (~±0.18V) |
| 15 | 当前 OUT2 是否明确只能接示波器 | ✅ 明确 | 注释 "OUT2 remains oscilloscope-only"（第 271-272 行）；"do not connect it to a laser, D2-125 Servo Output, or Scan input" |

### laser_lock_core.sv 结论：**通过**

代码修改质量高。generate 块结构清晰，注释充分解释了为什么默认不启用完整 PI（timing failure 记录）、P-only 路径的数据流、电压安全边界。P-only 组合逻辑深度只有 sign-extension + polarity mux + arithmetic shift + comparator → 约 2-3 个 LUT level，在 125 MHz 下毫无 timing 压力。

一个小注意点：`PID_ENABLE_DEFAULT` 当前为 `1'b1`（第 64 行），这意味着上电后 OUT2 会立即输出 P-only control。这是有意为之（因为 OUT2 只接示波器），但如果在未来阶段将此参数改为 0 或 OUT2 接了真实负载，需重新审查 enable 策略。

---

## 5. red_pitaya_top.sv 审查

### 逐项检查

| # | 检查项 | 结果 | 行号/证据 |
|---|--------|------|-----------|
| 1 | USE_LASER_LOCK_CORE 是否仍为 1'b1 | ✅ 是 | 第 146 行 |
| 2 | LASER_LOCK_OUTPUT_MODE 是否仍为 3 | ✅ 是 | 第 147 行 |
| 3 | red_pitaya_top.sv 是否没有显式把 USE_FULL_PI_CONTROLLER 改成 1 | ✅ 没有 | 第 445-454 行 laser_lock_core 实例化只传入 `.OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)` |
| 4 | laser_lock_core 实例化时是否只传入 OUTPUT_MODE | ✅ 是 | 第 447 行，无 USE_FULL_PI_CONTROLLER 覆盖 |
| 5 | 这是否意味着 USE_FULL_PI_CONTROLLER 使用默认 1'b0 | ✅ 是 | SystemVerilog parameter 默认值规则：上层不传则用模块定义的默认值 |
| 6 | OUT1 / DAC A 是否仍为 laser_error | ✅ 是 | 第 467 行 `dac_a_sum_laser = {laser_error[13], laser_error}` |
| 7 | OUT2 / DAC B 是否仍为 laser_control | ✅ 是 | 第 468 行 `dac_b_sum_laser = {laser_control[13], laser_control}` |
| 8 | DAC saturation 是否保持原样 | ✅ 是 | 第 481-482 行 |
| 9 | signed-to-unsigned 是否保持原样 | ✅ 是 | 第 485-489 行 |
| 10 | ODDR 输出结构是否保持原样 | ✅ 是 | 第 492-496 行 |
| 11 | ADC 输入路径是否保持原样 | ✅ 是 | 第 422-439 行 |
| 12 | PLL、ADC clock、DAC clock、PS、AXI、DDR 是否未被本轮修改 | ✅ 是 | git diff 确认无变更 |

### red_pitaya_top.sv 结论：**通过**

最关键的安全检查通过：`red_pitaya_top.sv` 实例化 `laser_lock_core` 时只传入了 `OUTPUT_MODE`，**没有覆盖** `USE_FULL_PI_CONTROLLER`。这意味着 `USE_FULL_PI_CONTROLLER` 使用 `laser_lock_core.sv` 中定义的默认值 `1'b0`，即 P-only Shadow Control。DAC 路由、saturation、signed-to-unsigned 转换、ODDR 输出结构全部保持原样，与 v1ab 已验证的硬件通路一致。

---

## 6. sim testbench 审查

### 逐项检查

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | testbench 是否已改成 timing-safe P-only Shadow Control 测试 | ✅ 是 | 所有 4 个 DUT 实例化均显式 `.USE_FULL_PI_CONTROLLER(1'b0)` |
| 2 | testbench 是否显式设置 USE_FULL_PI_CONTROLLER=1'b0 | ✅ 是 | 第 77/96/116/136 行 |
| 3 | 是否验证 reset clears output | ✅ 是 | check "reset clears direct control_o" + "reset clears mode3 error_o" — PASS |
| 4 | 是否验证 OUT1 error visibility | ✅ 是 | check "OUTPUT_MODE=0 exposes protected error source" — PASS |
| 5 | 是否验证 OUT2 ≈ OUT1 / 2 | ✅ 是 | check "timing-safe P-only makes control_o half of positive error_o" + negative 版本 — PASS |
| 6 | 是否验证正 error | ✅ 是 | pd_direct=400 → control_direct=200 — PASS |
| 7 | 是否验证负 error | ✅ 是 | pd_direct=-400 → control_direct=-200 — PASS |
| 8 | 是否验证 polarity reversal | ✅ 是 | check "polarity=1 reverses OUT2 control direction" control_reverse=-200 — PASS |
| 9 | 是否验证 output_limit | ✅ 是 | check "output_limit clamps positive OUT2 control" control_limit=100 — PASS |
| 10 | 是否验证 OUTPUT_MODE=3 下 mixer+LPF error | ✅ 是 | check "OUTPUT_MODE=3 still produces mixer plus LPF error" error_mode3>0 — PASS |
| 11 | 是否验证 mode3 下 OUT2 跟随 OUT1/2 | ✅ 是 | check "mode3 P-only control is approximately half the visible error" — PASS |
| 12 | 是否存在 race condition | ✅ 无 | testbench 使用 `#1` delay after `@(posedge clk)`，标准 practice |
| 13 | 是否存在 reset 后等待不足 | ✅ 无 | `wait_cycles(4)` 后 check reset + `wait_cycles(12)` 后 check 正常行为，充裕 |
| 14 | 是否存在 signed 比较问题 | ✅ 无 | 所有比较使用 `==` 直接比较 14-bit signed 值 |
| 15 | 是否有任何 testbench 行为可能误导 synthesis | ✅ 无 | testbench 不在 Vivado Design Sources 中，不会被 synthesis 读取 |

### 必须明确说明

**sim 文件是否会进入 synthesis / implementation / bitstream？**

**不会。** Testbench 文件（`.sv` 在 `sim/` 目录下）仅在 Vivado Simulation Sources 中使用。Vivado synthesis 只读取 Design Sources 中的文件。Testbench 中的 `USE_FULL_PI_CONTROLLER(1'b0)` 设置不会影响 synthesis——synthesis 使用 `laser_lock_core.sv` 中定义的 parameter 默认值 `1'b0`。两者一致（都是 1'b0），所以不存在 "仿真通过但 synthesis 用不同参数" 的隐蔽 bug。

### sim testbench 结论：**通过**

18/18 全部 PASS，覆盖完整。xsim.log 确认 `V2B1_TIMING_SAFE_SHADOW_CONTROL_SIM PASS`。testbench 设计合理：用 4 个 DUT 实例分别测试不同参数组合（direct/large-signal-limit/polarity-reverse/mode3），避免单实例串行测试的参数残留问题。

---

## 7. pi_controller.sv 保留策略审查

| # | 问题 | 判断 | 理由 |
|---|------|------|------|
| 1 | pi_controller.sv 本轮未修改是否合理 | **合理** | 完整 PI 核心是 v2A 已验证资产（tb_pi_controller: 165/165 PASS），不应该为 "绕过 timing" 而删改它。正确的做法正是当前策略：保留完整模块，通过 generate 控制实例化 |
| 2 | 之前 timing failed 是否说明 pi_controller 功能错误 | **不说明** | timing failure 是 "组合路径太长"（物理实现问题），不是 "算错了"（功能问题）。pi_controller 在仿真中功能完全正确 |
| 3 | 是否只是说明完整 PI 需要后续流水线化 | **是** | 48-bit accumulator + anti-windup freeze tree + P+I+offset limiter 构成约 30+ logic level 的组合路径，在 125 MHz (8 ns) 下只能通过寄存器分割（流水线）解决 |
| 4 | 当前保留 pi_controller.sv 是否有价值 | **有价值** | 是经过 165 项仿真验证的完整数字 PI 参考实现，后续 v2B2/v2B3 流水线化将以此为起点 |
| 5 | 当前默认绕开完整 PI 是否合理 | **完全合理** | 在 PI 流水线化完成之前，用 P-only 路径提供 OUT2 示波器观察，是唯一正确的工程决策 |
| 6 | 后续是否应进入 v2B2/v2B3 专门做 pipelined PI | **是** | v2B1 已经验证了 "绕开 PI 后 timing met"，v2B2 应做 PI 流水线化 |
| 7 | 当前是否禁止启用 Ki | **是** | `PID_KI_DEFAULT=16'sd0`（第 74 行），Ki 为零意味着即使完整 PI 被意外实例化，积分项也不会累积。P-only 默认路径根本没有积分器 |
| 8 | 当前是否禁止 USE_FULL_PI_CONTROLLER=1 | **禁止上板** | 允许在仿真中设为 1 做对照验证，但禁止用于生成上板 bitstream。代码注释明确警告 "Directly using this complete PI branch in the 125 MHz main project caused implementation timing failure" |

### pi_controller.sv 保留策略结论：**通过**

当前策略是教科书级别的 "preserve-and-bypass"——保留了经过充分验证的复杂模块，同时通过编译时开关提供了 timing-safe 的简化路径。这是处理 "功能正确但时序不收敛" 问题的最佳实践。

---

## 8. Vivado timing 风险审查

### 8.1 旧 worst path vs 当前 worst path

**旧 worst path**（来自 STATUS.md 记录）：
```
i_laser_lock_core/u_output_protect/data_o_reg
-> i_laser_lock_core/i_pi_controller
-> control_o_reg
WNS ≈ -10.995 ns, TNS ≈ -5029 ns
```

**当前 worst path**（来自 2026-06-16 timing_summary_routed.rpt）：
```
Source: i_laser_lock_core/i_lpf_core/acc_q_reg[0]/C
Destination: i_laser_lock_core/i_lpf_core/y_o_reg[11]/D
Logic Levels: 18 (CARRY4=14 LUT1=1 LUT2=2 LUT3=1)
Data Path Delay: 7.548 ns
Slack (MET): 0.361 ns
```

### 逐项判断

| # | 问题 | 回答 | 证据 |
|---|------|------|------|
| 1 | 默认 USE_FULL_PI_CONTROLLER=0 时，i_pi_controller 是否还会进入默认上板路径 | **不会** | generate 块中 `if (USE_FULL_PI_CONTROLLER)` 为假，`i_pi_controller` 不被 synthesis；timing report 中无任何 `i_pi_controller` 路径 |
| 2 | 旧 worst path 是否理论上应该消失 | **是，已消失** | timing report 中 worst path 是 lpf_core 的 32-bit accumulator CARRY4 链，不是 pi_controller |
| 3 | 如果 timing report 仍出现 i_pi_controller worst path，可能原因是什么 | **不适用** | 当前 report 中无 i_pi_controller 路径，说明 synthesis 正确排除了该 generate 分支 |
| 4 | 当前 P-only 路径是否足够短 | **是** | P-only 路径：sign-extend → polarity mux → arithmetic shift → comparator → register — 约 2-3 LUT levels。在 8 ns 周期下完全不是瓶颈 |
| 5 | 当前是否还需要 pipeline | **对 P-only 路径不需要**；**对 lpf_core 可考虑但非紧急** | P-only 路径组合深度极浅。lpf_core 的 32-bit accumulator 有 18 logic levels，slack=0.361 ns 虽已 MET 但余量不大，后续如果加更多逻辑可能成为瓶颈 |
| 6 | 当前是否还需要 multicycle path | **不需要** | 所有路径 timing met |
| 7 | 是否不建议用 multicycle path 掩盖真实 timing 问题 | **不建议** | 规则文件已明确："不允许用未经论证的 multicycle path、false path 或约束技巧掩盖真实控制路径 timing failure"。当前 timing met，完全无需此类约束 |

### Vivado timing 风险审查结论：**通过**

旧 WNS=-10.995 ns 的 pi_controller 路径已从当前 synthesis 中完全消失。新的 worst path 在 lpf_core（32-bit accumulator CARRY4 链），slack=+0.361 ns，timing met。P-only 控制路径组合深度极浅，无 timing 风险。

---

## 9. Vivado 工程 sources 审查

### 从文件系统可判断的部分

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | Vivado design sources 是否引用 `v0.94/rtl/laser_lock_core.sv` | **从 git 记录推断为是** | synthesis log 中有 `i_laser_lock_core` 层次结构；DRC report 中有 `i_laser_lock_core/i_mixer_core` 路径。project .xpr 文件存在且引用 `v0.94/` 目录 |
| 2 | 是否误引用 `version/v2/v0.94/...` | **无法从文件系统直接判断** | 需用户在 Vivado GUI 中打开 Project Sources 确认 |
| 3 | 是否误引用 `v-weifang/...` | **无法从文件系统直接判断** | 同上 |
| 4 | 是否存在多个 laser_lock_core.sv | **文件系统中只有一个** | Glob 搜索确认：只有 `v0.94/rtl/laser_lock_core.sv`（`version/v2/v0.94/rtl/` 下是旧 v2A 副本，与当前 v2B1 不同——Vivado 绝不能引用该路径） |
| 5 | 是否存在多个 red_pitaya_top.sv | **文件系统中存在多个副本** | `v0.94/rtl/red_pitaya_top.sv` (当前), `version/v1/v0.94/rtl/red_pitaya_top.sv` (旧), `version/v2/v0.94/rtl/red_pitaya_top.sv` (旧), `v-weifang/rtl/red_pitaya_top.sv` (旧). Vivado 引用错误路径将导致不可预测的 synthesis 结果 |
| 6 | 是否存在 duplicated module definition | **文件系统中无同名模块冲突** | 但若 Vivado 同时添加了多个路径的 red_pitaya_top.sv，会导致 elaboration 错误 |
| 7 | 是否需要 update compile order | **如果 sources 正确则不需要** | synthesis 成功说明当前 compile order 有效 |
| 8 | 是否需要 reset synth_1 / reset impl_1 | **如果 sources 有变更则建议 reset** | 当前代码自 2026-06-16 后无 RTL 变更，但建议用户在继续之前确认 sources 指向正确 |
| 9 | 是否需要确认 Project Sources 和 Simulation Sources 分离 | **需要** | 从 `v0.94/project/redpitaya.sim/sim_1/behav/xsim/` 下的 .prj 文件可看到 testbench 在 Simulation Sources 中。这是正确的——testbench 绝不应在 Design Sources 中 |

### Vivado 工程 sources 审查结论：**有风险但可接受，需用户手动确认**

从 synthesis/implementation 成功且 timing report 中无 `i_pi_controller` 路径来看，Vivado 大概率引用了正确路径的 `laser_lock_core.sv`。但文件系统中存在多个 `red_pitaya_top.sv` 和 `laser_lock_core.sv` 的历史副本（在 `version/v1/`、`version/v2/`、`v-weifang/` 下），用户应在 Vivado GUI 中确认 Design Sources 指向 `v0.94/rtl/` 下的文件，**绝不应**指向 `version/` 或 `v-weifang/` 下的历史副本。

---

## 10. Vivado log / report 审查

### 10.1 Synthesis (2026-06-16 20:02-20:03)

| 项目 | 结果 |
|------|------|
| 是否通过 | ✅ 通过 — "Synthesis finished with 0 errors, 0 critical warnings and 2 warnings" |
| 关键警告 | 2 warnings（非 critical），DCP 正常生成 |
| 资源 | 11 DSP48E1, 5381 FDRE, 1462 LUT6, 30 RAMB36E1 — 利用率极低 |

### 10.2 Implementation (2026-06-16 20:03-20:05)

| 项目 | 结果 |
|------|------|
| 是否通过 | ✅ 通过 — "route_design completed successfully" "0 Errors encountered" |
| Timing met | ✅ WNS=0.361 ns, TNS=0.000 ns, WHS=0.050 ns, THS=0.000 ns |
| "All user specified timing constraints are met." | ✅ 明确写入 report |
| 是否仍然出现 WNS=-10.995 ns 类似结果 | ❌ **未出现** — worst slack 为 +0.361 ns（正值） |
| 是否仍然出现 i_pi_controller 相关最差路径 | ❌ **未出现** — worst path 在 lpf_core (acc_q → y_o CARRY4 chain) |
| Bitstream 是否生成 | ✅ 是 — `red_pitaya_top.bit` (2,083,850 bytes) |
| unconstrained paths | 19 个 unconstrained internal endpoints（来自官方 daisy chain / housekeeping 模块，非本设计引入） |
| no_clock endpoints | 52 个（来自官方模块的 daisy/hk 寄存器，预存在） |
| CDC warning | TIMING-6/TIMING-7 Critical Warnings：par_clk ↔ pll_adc_clk 无共同 primary clock（来自官方 daisy chain 设计，预存在） |
| Gated clock | PDRC-153：`i_daisy/txp_dv_reg_i_2_n_0` 是 gated clock（来自官方 daisy chain 设计，预存在） |

### 10.3 DRC (routed)

| 项目 | 结果 |
|------|------|
| DRC errors | 0 |
| DRC warnings | 43（DPIP-1: 2, DPOP-1: 5, DPOP-2: 7, PDRC-153: 1, PLIO-8: 28） |
| 与本设计相关 | DPOP-1#1 + DPOP-2#1 指向 `i_laser_lock_core/i_mixer_core/product_w` DSP 未使用 MREG/PREG 寄存器（mixer_core 的乘法器输出未经过 DSP 内部 pipeline 寄存器）— 这是 mixer_core 的已知设计特征，非本轮引入 |
| 其余 DRC warnings | 全部来自官方 scope/ASG/daisy 模块 |

### 10.4 Methodology DRC

| 项目 | 结果 |
|------|------|
| Violations | 114 |
| Critical Warnings | 5（TIMING-6: 2, TIMING-7: 2, TIMING-17: 1） |
| 与本设计相关 | **0** — 全部来自官方 IP 和 daisy chain 模块 |

### Vivado log / report 审查结论：**通过**

旧 WNS=-10.995 ns 的 pi_controller timing failure **已完全消失**。当前所有 timing constraints met。DRC warnings 和 methodology critical warnings 全部来自官方 Red Pitaya 设计模块（scope filter DSP、daisy chain clock crossing、housekeeping），没有一项是本轮代码修改引入的。Bitstream 已成功生成。

---

## 11. 当前是否可以继续 Vivado

**结论：可以继续跑 Vivado synthesis / implementation。**

理由：
1. 当前 RTL 代码（laser_lock_core.sv 默认 USE_FULL_PI_CONTROLLER=0）已通过 synthesis（0 errors）。
2. 相同代码已通过 implementation 和 timing（WNS=+0.361 ns, TNS=0.000 ns）。
3. Bitstream 已生成成功。
4. 没有任何结构性阻断问题（无 elaborated module conflict、无 missing module、无 black box 缺失）。

但建议：如果距离上次 Vivado 运行（2026-06-16）后 RTL 代码有任何变更（即使是注释），应先 reset_run 再重新 synthesis→implementation。如果代码无变更，已有的 bitstream 可以直接使用。

---

## 12. 当前是否可以烧录

**结论：可以烧录上板观察。**

### 判断标准逐项验证

| 标准 | 状态 | 证据 |
|------|------|------|
| synthesis 通过 | ✅ | synth_1/runme.log: "Synthesis finished with 0 errors, 0 critical warnings" |
| implementation 通过 | ✅ | impl_1/runme.log: "route_design completed successfully" "0 Errors" |
| timing met | ✅ | timing_summary_routed.rpt: "All user specified timing constraints are met." |
| WNS >= 0 | ✅ | WNS = +0.361 ns |
| TNS = 0 | ✅ | TNS = 0.000 ns |
| bitstream 成功生成 | ✅ | red_pitaya_top.bit 存在 (2,083,850 bytes) |
| 当前确认为 timing-safe P-only 默认路径 | ✅ | USE_FULL_PI_CONTROLLER=1'b0；timing report 中无 i_pi_controller 路径 |
| OUT2 只接示波器 | ✅ | 代码注释和文档反复确认，需用户在实验台上遵守 |

### 烧录前提条件

1. **用户需手动确认 Vivado Project Sources 指向 `v0.94/rtl/laser_lock_core.sv`**，而非 `version/v2/v0.94/rtl/` 或 `v-weifang/rtl/` 下的历史副本。
2. **用户需手动确认 Simulation Sources 和 Design Sources 分离**，testbench 文件不在 Design Sources 中。
3. **如果对以上两点不确定**，应在 Vivado 中 reset_run → 重新 synthesis → 重新 implementation → 重新 timing check → 重新 generate bitstream。
4. **烧录后严格遵守**：OUT1 接示波器 CH2，OUT2 接示波器 CH4，OUT2 不接任何执行器。

### 烧录后允许的实验（与上轮 Claude 审查 §12.5 一致）

1. 空输入安全测试
2. IN1 小信号输入测试
3. IN1/IN2 混频观察测试
4. OUT1 error_o 示波器观察
5. OUT2 P-only control_o 示波器观察

---

## 13. 当前禁止事项

以下事项在当前 v2B1 阶段**严格禁止**（与上轮 Claude 审查 §12.6 一致，并根据本轮 timing 结果更新）：

- 不要修改 `pi_controller.sv`
- 不要把 `USE_FULL_PI_CONTROLLER` 改成 1（禁止用于上板 bitstream，仿真对照可以）
- 不要启用 Ki（`PID_KI_DEFAULT` 保持 0）
- 不要做完整 PI 上板
- 不要做 ramp/sweep
- 不要做 scan/lock FSM
- 不要做 CNN/AI
- OUT2 禁止接激光器 PZT
- OUT2 禁止接激光电流控制端
- OUT2 禁止接 D2-125 Servo Output
- OUT2 禁止接 Scan input
- 不能声称已经完成闭环锁定
- 不能声称已经完整替代 D2-125
- 不能用 multicycle path / false path 掩盖未验证的控制路径 timing
- **新增：不要修改 Vivado Design Sources 指向非 `v0.94/rtl/` 路径的历史文件副本**

---

## 14. 给 Codex 的后续修复建议

**总体评估：本轮审查未发现需要紧急修复的代码缺陷。以下建议为预防性和前瞻性任务。**

### Codex 任务 1：Vivado Project Sources 路径验证辅助

**目的**：帮助用户确认 Vivado 工程中 Design Sources 指向正确的文件路径。

**涉及文件**：`v0.94/project/redpitaya.xpr`, `v0.94/project/redpitaya.srcs/`

**允许修改**：仅读取 .xpr 和 sources 配置文件，不修改任何文件。

**禁止修改**：所有 .sv, .xdc, .sdc, .tcl 文件。

**具体检查**：
1. 读取 `redpitaya.xpr` 中 `<FileSet Name="sources_1">` 部分
2. 确认 `laser_lock_core.sv` 的 `<File Path>` 指向 `v0.94/rtl/laser_lock_core.sv`
3. 确认 `red_pitaya_top.sv` 的 `<File Path>` 指向 `v0.94/rtl/red_pitaya_top.sv`
4. 检查是否有任何文件路径指向 `version/v2/v0.94/rtl/` 或 `v-weifang/rtl/`
5. 如果发现错误引用，不要自行修改 .xpr，而是输出明确的修复指令给用户

**成功判据**：出具一份 sources 路径清单，标出哪些是正确的、哪些需要修正。

**失败处理**：如果无法解析 .xpr 文件，告知用户需要在 Vivado GUI 中手动检查。

### Codex 任务 2：Vivado timing 复查辅助文档

**目的**：为用户手动 Vivado timing 复查提供操作 SOP。

**涉及文件**：`version/v2/V2_EXPERIMENT_SOP.md`（可追加章节）

**允许修改**：`version/v2/V2_EXPERIMENT_SOP.md`

**禁止修改**：所有 .sv, .xdc, .sdc, .tcl, .xpr 文件。

**具体内容**：
1. 如何在 Vivado 中 reset_run
2. 如何 run synthesis
3. 如何 run implementation
4. 如何打开 timing summary
5. 如何确认 WNS/TNS 非负
6. 如何确认 worst path 不穿过 i_pi_controller
7. 如何 generate bitstream
8. 如何 scp .bit.bin 到 Red Pitaya
9. 如何 fpgautil -b 加载

**成功判据**：SOP 文档可以让用户无需额外搜索即可完成完整 Vivado 流程。

### Codex 任务 3：lpf_core timing 余量监控建议

**目的**：当前 worst path 在 lpf_core 的 32-bit CARRY4 accumulator chain，slack=0.361 ns（仅 4.5% 余量）。如果后续在 lpf_core 路径上增加任何逻辑，可能再次 timing fail。

**涉及文件**：无（仅建议）

**允许修改**：无

**禁止修改**：无

**具体建议**：
1. 记录当前 worst path 为 baseline
2. 如果后续给 lpf_core 增加功能（如可配置 LPF_SHIFT、多级滤波），建议先考虑 lpf_core 内部流水线化
3. lpf_core 的 32-bit accumulator 是 4×CARRY4 + adder CARRY4 链，可以在中间插入寄存器级（需验证数值等价性）

**成功判据**：此条仅为建议，无需执行判断。

### Codex 任务 4：testbench 与 synthesis 参数一致性自动化检查

**目的**：确保未来 testbench 中的 parameter override 与 synthesis 默认值保持一致。

**涉及文件**：可新建 `v0.94/sim/check_params.py` 或类似脚本

**允许修改**：仅新建文件

**禁止修改**：所有 .sv 文件。

**具体检查**：
1. 提取 `laser_lock_core.sv` 中的所有 `parameter` 默认值
2. 提取 testbench 中所有 DUT 实例化的 parameter override
3. 标注差异并解释原因（如 testbench 用 CLK_HZ=8 加速仿真 — 这是有意为之且可接受）

**成功判据**：脚本可以运行并输出差异报告。

### Codex 任务 5：文档中 "OUT2 只接示波器" 声明一致性检查

**目的**：确保所有文档和代码注释中关于 OUT2 安全边界的声明一致。

**涉及文件**：`version/STATUS.md`, `version/v2/V2_NEXT_STEPS.md`, `version/v2/V2_EXPERIMENT_SOP.md`, `v0.94/rtl/laser_lock_core.sv`, `v0.94/rtl/red_pitaya_top.sv`

**允许修改**：仅 .md 文件中的文字描述

**禁止修改**：所有 .sv, .xdc, .sdc, .tcl 文件。

**具体检查**：
1. 是否所有文档都声明 OUT2 只接示波器
2. 是否所有文档都声明不能接激光器/D2-125/Scan
3. 是否所有文档都声明不能声称闭环锁定
4. 如有不一致，统一修正

**成功判据**：所有文档的安全声明一致。

### Codex 任务 6：v2B2 pipelined PI 预研（不实现）

**目的**：为下一阶段 v2B2 的流水线化 PI 做技术预研，但不写任何 RTL。

**涉及文件**：无（仅输出研究笔记）

**允许修改**：可新建 `version/v2/claude审查/PIPELINED_PI_RESEARCH_v2B2.md`

**禁止修改**：所有 .sv 文件。

**研究内容**：
1. pi_controller.sv 中哪些组合路径需要打断（P multiply → KP_SHIFT, I multiply → KI_SHIFT → integrator, integrator + P + offset → limiter）
2. 流水线化后的等效性证明（Z-transform 或时序图）
3. 流水线级数估算
4. 对 pid_ce 更新率的影响评估

**成功判据**：研究笔记足够清晰，可以作为 v2B2 RTL 实现的 spec。

---

## 15. 下一步路线建议

### 当前处于情况 B：Vivado timing 通过

Vivado synthesis ✅ / implementation ✅ / timing MET (WNS=+0.361 ns) / bitstream ✅。

### 情况 B：下一步应该

1. **用户手动确认 Vivado Project Sources 路径正确**（见 §14 Codex 任务 1）。
2. **如果 sources 正确，直接使用已有 bitstream**（`v0.94/exp/v2/impl_1/red_pitaya_top.bit`）。
3. **如果 sources 不确定，reset runs → 重新 synthesis → implementation → timing → bitstream**。
4. **将 .bit 转换为 .bit.bin**，scp 到 Red Pitaya。
5. **fpgautil -b 加载 bitstream**。
6. **只烧录观察 OUT1/OUT2**：OUT1 接示波器 CH2，OUT2 接示波器 CH4。
7. **IN1/IN2 先接小信号**（≤200mVpp，从信号发生器开始，不要直接接 PD/REF）。
8. **记录波形**：OUT1 error 幅度和波动、OUT2 P-only control 行为、噪声基底。
9. **不接激光器**。
10. **拿到基线数据后**，进入 v2-1（改小 Ki + 电子学回环测试）。

### 如果未来出现情况 C（重新 Vivado 后 timing 仍失败）

1. 不烧录。
2. 检查是否 Vivado sources 指向了旧版本 `laser_lock_core.sv`（没有 generate 块的版本）。
3. reset runs 后重新 synthesis。
4. 如果确认新代码（带 generate + USE_FULL_PI_CONTROLLER=0）仍 timing fail，检查是否是 lpf_core accumulator 路径恶化（因为追加了其他逻辑）。
5. 交给 Codex 做最小 timing 修复（如在 lpf_core 中加一级流水线寄存器）。

---

## 16. 最终结论

1. **当前项目有没有跑偏？** 没有。方向正确——发现了 timing 问题后，用 generate + P-only 默认路径绕开，保留了完整 PI 核心，等待后续流水线化。这是正确的工程判断。

2. **当前修改方向是否正确？** 正确。`USE_FULL_PI_CONTROLLER` 参数化 + generate 块是解决 "功能完备但时序不收敛的模块暂时不能上板" 的标准 SystemVerilog 做法。

3. **当前是否应继续让 Codex 修代码？** 不需要紧急修复。Codex 可以做 §14 中的辅助任务（sources 验证、SOP 文档、参数一致性检查），但 RTL 本身没有需要修复的 bug。

4. **当前是否应先跑 Vivado timing？** Vivado timing 已经跑了，且通过了。WNS=+0.361 ns。用户需要做的是在 Vivado GUI 中确认 sources 路径正确性，然后决定是直接使用已有 bitstream 还是重新跑一遍。

5. **当前能否烧录？** 能。前提是 (a) 确认 Vivado sources 指向正确的 v0.94/rtl/ 文件，(b) 烧录后严格遵守 OUT2 只接示波器的红线。

6. **下一步最重要的一件事是什么？** 烧录已有的 bitstream，在示波器上观察 OUT1（mixer+LPF error）和 OUT2（P-only control），记录基线波形数据。这是 v2B1 阶段存在的唯一目的——积累真实硬件行为数据，为 v2B2 流水线化 PI 和 v2-1 启用小 Ki 提供参数依据。

---

**审查结束。本报告未修改任何 RTL、testbench、Vivado 工程文件或已有文档。仅新增本审查报告文件。**

*只读审查工具使用统计：Read × 24, Bash × 14。审查覆盖全部关键 RTL（6 文件）、testbench（2 文件）、Vivado log/report（10+ 文件）、文档（10+ 文件）、git 状态和历史。*
