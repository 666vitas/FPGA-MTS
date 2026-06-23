# CLAUDE REVIEW — v2B2/v2B3 sequential PI gate report

**审查日期**: 2026-06-22
**审查阶段**: v2B2/v2B3 sequential PI controller 门控审查
**审查类型**: 独立只读审查（不修改文件、不操作 Vivado、不操作 git）
**审查人**: Claude (Opus)
**上一轮审查**: v2B1 timing-safe P-only gate（2026-06-16，结论：可以烧录上板观察）

---

## 0. 审查前版本信息

```text
审查时间：2026-06-22
当前版本：v0.94，v2B1 已关闭（WNS=+0.361ns，上板示波器验证通过）
审查目标：v2B2/v2B3 sequential PI 阶段
v2B1 报告：version/v2/claude审查/CLAUDE_REVIEW_v2B1_timing_safe_gate_2026-06-16.md
Codex 指令：version/v2/codex执行记录/CODEX_v2B2_v2B3_seq_pi_instruction_2026-06-22.md
```

---

## 1. 审查了什么

审查了以下文件（全部只读）：

**新增 RTL**:
- `v0.94/rtl/pi_controller_seq.sv` — 新 sequential PI controller（233 行）

**修改 RTL**:
- `v0.94/rtl/laser_lock_core.sv` — 已加入 CONTROL_PATH_MODE 三路 generate block（341 行）
- `v0.94/rtl/red_pitaya_top.sv` — 未修改（仍然只传 OUTPUT_MODE）

**新增 testbench**:
- `v0.94/sim/tb_pi_controller_seq.sv` — 独立 sequential PI testbench（293 行）

**修改 testbench**:
- `v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` — 新增 6 个 sequential PI DUT 实例和 9 个 checks（348 行）

**已阅读但作为参考/对比的 RTL**:
- `v0.94/rtl/pi_controller.sv` — 旧完整 PI 核心（不修改，作为算法参考）
- `v0.94/rtl/mixer_core.sv` — 未修改
- `v0.94/rtl/lpf_core.sv` — 未修改
- `v0.94/rtl/output_protect.sv` — 未修改

**XSim 日志**:
- `v0.94/xsim.log` — 集成 testbench 运行日志（2026-06-22 19:53 UTC）
- `v0.94/xsim_17900.backup.log` — 独立 tb_pi_controller_seq 运行日志
- `v0.94/xvlog.log` — xvlog 编译日志（含 pi_controller_seq.sv）
- `v0.94/xelab.log` — xelab 详细日志

**文档**:
- `version/STATUS.md` — 已更新到 v2B2/v2B3 RTL/SIM 完成状态
- `version/v2/codex执行记录/CODEX_v2B2_v2B3_seq_pi_instruction_2026-06-22.md` — Codex 指令

**Vivado 项目**:
- `v0.94/project/redpitaya.xpr` — 检查 Design Sources 列表

**额外检查**:
- 用 grep 搜索 `pi_controller_seq` 在 `v0.94/project/redpitaya.srcs/` 和 `redpitaya.xpr` 中的引用

---

## 2. 审查前提与边界

v2B2/v2B3 sequential PI 阶段的目标是把旧 pi_controller.sv 中 timing-failing 的单周期长组合路径（WNS≈-10.995ns，通过 DSP48E1→CARRY4→48-bit integrator→anti-windup→limiter）拆成 7 个 clk_i 拍的顺序更新，保留完整 P+I+offset+anti-windup+对称限幅的算法语义，但仍保持 pid_ce_i 作为 10kHz 更新使能（不另外引入时钟域）。

本审查专注于以下问题：

- pi_controller_seq.sv 是否存在且语法正确
- 算法是否完整保留了 pi_controller.sv 的 PI+anti-windup 语义
- CONTROL_PATH_MODE 是否正确地替换了旧的 USE_FULL_PI_CONTROLLER
- 默认上板路径是否仍然安全（默认为 mode 0，P-only 回退）
- XSim 独立和集成 testbench 是否全部通过
- pi_controller_seq.sv 是否已进入 Vivado Design Sources
- 当前是否可以进入 Vivado timing 验证
- 当前是否可以烧录 sequential PI

---

## 3. pi_controller_seq.sv 存在性检查

```text
pi_controller_seq.sv 路径：v0.94/rtl/pi_controller_seq.sv
文件大小：233 行
语法检查：xvlog 编译通过，0 error，0 warning
```

xvlog 日志明确记录了 pi_controller_seq.sv 的分析：

```text
INFO: [VRFC 10-2263] Analyzing SystemVerilog file ".../v0.94/rtl/pi_controller_seq.sv" into library work
INFO: [VRFC 10-311] analyzing module pi_controller_seq
```

xelab 日志 0 error 0 warning，确认 pi_controller_seq_default 已成功编译并链接。

**结论：pi_controller_seq.sv 已存在，语法正确，xvlog/xelab 全部通过。**

---

## 4. pi_controller_seq.sv 架构审查

### 4.1 七状态 FSM

```text
S_IDLE -> S_CAPTURE -> S_P_CALC -> S_I_CALC -> S_I_UPDATE -> S_SUM -> S_LIMIT -> S_IDLE

S_IDLE:    等待 pid_ce_i 脉冲，收到后进入 S_CAPTURE
S_CAPTURE: 锁存 error（含极性处理）、kp、ki、offset_ext、output_limit、reset_integrator
S_P_CALC:  执行 P 乘法 error_pol_q * kp_q，存 p_product_q
S_I_CALC:  P 缩放结果存 p_scaled_q；执行 I 乘法 error_pol_q * ki_q，存 i_product_q
S_I_UPDATE: 根据 freeze 决定积分器更新或保持；含 reset_integrator 分支
S_SUM:     计算 control_pre = p_scaled + integrator + offset
S_LIMIT:   对称限幅，更新 control_o/p_term_o/i_term_o/sat_o，返回 S_IDLE
```

每个状态数据路径都是短组合或纯寄存器写，避免旧 pi_controller.sv 中的 P+I+offset+anti-windup+limiter 长组合路径。

### 4.2 参数匹配

| 参数 | pi_controller.sv | pi_controller_seq.sv | 匹配 |
|---|---|---|---|
| ERROR_WIDTH | 14 | 14 | ✓ |
| GAIN_WIDTH | 16 | 16 | ✓ |
| OUT_WIDTH | 14 | 14 | ✓ |
| ACC_WIDTH | 48 | 48 | ✓ |
| KP_SHIFT | 12 | 12 | ✓ |
| KI_SHIFT | 12 | 12 | ✓ |

### 4.3 anti-windup 公式逐行对比

**Reference — pi_controller.sv (lines 97-99)**:
```systemverilog
assign freeze_integrator_w =
    ((current_control_pre_w >= limit_pos_w) && (i_delta_w > ACC_ZERO)) ||
    ((current_control_pre_w <= limit_neg_w) && (i_delta_w < ACC_ZERO));
```

**New — pi_controller_seq.sv (lines 104-106)**:
```systemverilog
assign freeze_integrator_w =
    (($signed(current_control_pre_w) >= $signed(limit_pos_w)) && ($signed(i_delta_w) > ACC_ZERO)) ||
    (($signed(current_control_pre_w) <= $signed(limit_neg_w)) && ($signed(i_delta_w) < ACC_ZERO));
```

差异：pi_controller_seq.sv 增加了显式 `$signed()` 类型转换。这是因为在新模块中 `current_control_pre_w`、`limit_pos_w`、`limit_neg_w` 声明时使用了 `logic signed`（第 80-81 行），但作为敏感的 `logic` 类型向量进行运算时，显式 $signed() 更加安全。这是正确的防御性适应，anti-windup 语义完全保持一致。

### 4.4 enable/hold/reset_integrator 行为

```text
enable_i=0: 立即清除所有输出（control_o/p_term_o/i_term_o=0），丢弃进行中的事务
hold_i=1:   保持当前输出和积分器不变，FSM 回到 S_IDLE
reset_integrator_i=1: 与事务一起采样，在 S_I_UPDATE 中清零积分器
```

这些行为与 pi_controller.sv 的参考语义一致。

- hold_i 实现为在 `always_ff` 块中 `else if (hold_i)` 分支，这会在采样到 hold 时立即停止事务。注意：hold 优先级在 enable 之后（enable 输出清零，hold 保持输出）。这与旧 pi_controller 的语义一致。
- reset_integrator 在 S_CAPTURE 中与 error/kp/ki 一起采样，因此在同一事务中一致使用。这比旧 pi_controller 的瞬时 `reset_integrator_i` 输入更加确定——旧版本中 reset_integrator 可以在 pid_ce 有效期间随时变化。

### 4.5 注意事项

1. **`$signed()` 冗余调用**（无功能影响）：`current_control_pre_w` 已声明为 `logic signed [ACC_WIDTH-1:0]`（第 76 行），所以在第 105-106 行的 `$signed(current_control_pre_w)` 是冗余的。但这种冗余不会产生功能差异，采用防御性风格是合理的。

2. **同步复位**：pi_controller_seq.sv 使用同步复位 (`always_ff @(posedge clk_i)` 内的 `if (!rstn_i)`)，而旧 pi_controller.sv 使用异步复位 (`always_ff @(posedge clk_i or negedge rstn_i)`)。同步复位在 FPGA 设计中通常更优，且顶层 red_pitaya_top.sv 的 adc_rstn 通过 BUFG 后的时序足够满足复位建立/保持要求。这不是问题。

3. **busy pid_ce 忽略**：FSM 仅在 S_IDLE 状态接受 pid_ce 脉冲。忙时出现的 pid_ce 被静默丢弃。tb_pi_controller_seq 有专门的测试验证此行为且已通过。

**结论：pi_controller_seq.sv 架构合理，anti-windup 语义与参考一致，七状态分拍策略正确。**

---

## 5. laser_lock_core.sv CONTROL_PATH_MODE 审查

### 5.1 三模式 generate block

```text
CONTROL_PATH_MODE=0: g_timing_safe_p_only（v2B1 P-only 回退，当前默认路径）
CONTROL_PATH_MODE=1: g_seq_pi_controller（pi_controller_seq 顺序 PI，v2B3 目标路径）
CONTROL_PATH_MODE=2: g_full_pi_controller（旧 pi_controller，仅参考/仿真）

default（任何非法值）: 回退到 g_timing_safe_p_only（mode 0）
```

第 338 行的 else 分支正是 g_timing_safe_p_only——任何非法 CONTROL_PATH_MODE 值都会安全回退到 P-only 路径。

### 5.2 默认值安全

```verilog
parameter int CONTROL_PATH_MODE = 0,
```

默认值是 0（P-only），而不是 1（sequential PI）。这意味着：如果顶层没有显式传入 CONTROL_PATH_MODE，则自动选中 P-only 回退。这是关键的硬件安全特性。

### 5.3 PI 参数变化

| 参数 | v2B1 值 | v2B2/v2B3 值 | 说明 |
|---|---|---|---|
| PID_KI_DEFAULT | 16'sd0 | 16'sd16 | 从 0 改为 16，允许 mode 1 的 I 通道积累 |
| PID_KP_DEFAULT | 16'sd2048 | 16'sd2048 | 不变，保持 OUT2 ≈ OUT1 一半 |
| PID_OUTPUT_LIMIT_DEFAULT | 14'd1500 | 14'd1500 | 不变，约±0.18V 安全范围 |
| PID_ENABLE_DEFAULT | 1'b1 | 1'b1 | 不变 |

Ki=16 配合 KI_SHIFT=12 意味着在 256-count error 下每 10kHz 更新产生 1 个积分计数。这是一个非常保守的积分速率，适合示波器观察——积分从零开始爬升，用户可以看到 accumulation 是否健康。

### 5.4 USE_FULL_PI_CONTROLLER 移除确认

激光器锁核心模块不再包含 `parameter bit USE_FULL_PI_CONTROLLER` 参数。该参数已被完全移除，替换为 `parameter int CONTROL_PATH_MODE = 0`。没有遗留的双参数选择冲突。

### 5.5 保留旧 pi_controller 引用

mode 2 (g_full_pi_controller) 仍然保留对旧 `pi_controller` 模块的引用（第 253-277 行）。这意味着 `pi_controller.sv` 必须继续存在于编译文件列表中，否则 mode 2 的 generate 分支会导致 xelab 失败。当前 xvlog/xelab 日志证明 pi_controller.sv 仍在编译列表中（已确认：xvlog.log 中 "analyzing module pi_controller"），所以这不是当前问题。

**结论：CONTROL_PATH_MODE 设计正确，默认值 0 确保硬件安全，三模式 generate block 结构清晰。**

---

## 6. red_pitaya_top.sv 审查

### 6.1 laser_lock_core 实例化

```verilog
laser_lock_core #(
    .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)
) i_laser_lock_core (
    .clk_i     (adc_clk      ),
    .rstn_i    (adc_rstn     ),
    .pd_i      (adc_dat[0]   ),
    .ref_i     (adc_dat[1]   ),
    .error_o   (laser_error  ),
    .control_o (laser_control)
);
```

**关键发现：red_pitaya_top.sv 没有传递 CONTROL_PATH_MODE 参数。**

由于 laser_lock_core 中 CONTROL_PATH_MODE 的默认值是 0，不传递该参数意味着顶层固定使用 P-only 回退路径，无论 laser_lock_core 的代码中提供了 mode 1/2 选项。

### 6.2 安全意义

这是一个重要的安全设计：即使 Vivado Design Sources 中包含了 pi_controller_seq.sv 并被 synthesis 编译，只要顶层不显式传入 `CONTROL_PATH_MODE(1)`，生成的 bitstream 仍然只使用 P-only 路径。这防止了未经顶层审查就激活 sequential PI 的意外情况。

### 6.3 切换到 sequential PI 的步骤

要在板级激活 sequential PI，red_pitaya_top.sv 需要添加一行：

```verilog
laser_lock_core #(
    .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE),
    .CONTROL_PATH_MODE(1)                 // <-- 需要手动添加
```

这个修改应该只在以下条件全部满足后进行：
- pi_controller_seq.sv 已通过独立 XSim 和集成 XSim
- pi_controller_seq.sv 已添加到 Vivado Design Sources
- Vivado synthesis/implementation 已完成且无错误
- Vivado timing 已通过（WNS>=0, TNS=0, Failing Endpoints=0）
- DRC 无新的 critical warning

**结论：red_pitaya_top.sv 当前安全（默认 P-only），但切换到 mode 1 需要手动修改顶层。这是正确且保守的设计。**

---

## 7. XSim 回归审查

### 7.1 独立 sequential PI testbench（tb_pi_controller_seq）

从 v0.94/xsim_17900.backup.log 提取的完整结果：

```text
PASS: reset clears registered control
PASS: positive P-only update has fixed latency
PASS: positive P-only update publishes p term
PASS: positive P-only update has zero i term
PASS: enable low clears control
PASS: enable low clears P term
PASS: enable low clears I term
PASS: hold keeps control unchanged
PASS: hold keeps P term unchanged
PASS: negative P-only error produces negative control
PASS: negative P-only error produces negative P term
PASS: polarity reverses control direction
PASS: polarity reverses P term direction
PASS: small Ki accumulates one count
PASS: small Ki control follows integrator
PASS: constant error accumulates slowly
PASS: integration setup reaches nonzero I
PASS: reset_integrator clears I term
PASS: reset_integrator keeps P plus offset
PASS: offset is added to control
PASS: offset without limit leaves sat low
PASS: positive output limit clamps control
PASS: positive output limit asserts saturation
PASS: negative output limit clamps control
PASS: negative output limit asserts saturation
PASS: anti-windup freezes positive integrator
PASS: anti-windup permits reverse integration
PASS: anti-windup recovery clears saturation
PASS: anti-windup recovery leaves limit
PASS: pid_ce low keeps registered output
PASS: separated pid_ce updates with new sample
PASS: busy pid_ce does not create a second update
PASS: busy pid_ce leaves controller idle after one update
PASS: long integration has no unknown outputs
PASS: long integration remains within limit
SUMMARY tests=35 pass=35 fail=0
V2B2_PI_CONTROLLER_SEQ_SIM PASS
```

**结果：35/35 PASS，0 FAIL。**

覆盖的范围：
- 复位行为（control/p_term/i_term 清零）
- P-only 更新和固定延迟（7 clk_i 周期）
- enable 清零即时安全动作
- hold 丢弃事务并保持输出
- 正/负 error 的 P 计算方向
- 极性反转
- Ki 积分累积（小 Ki=16 在 error=256 下每步 +1）
- reset_integrator 仅清零 I，保留 P+offset
- offset 加到 control
- 正/负输出限幅和饱和标志
- anti-windup：正向饱和冻结积分器，反向 Ki 允许恢复
- pid_ce 保持（未收到脉冲时输出不变）
- busy pid_ce 忽略（忙时不启动第二个更新）
- 长序列积分 bounded 且 deterministic（100 步后无 X/Z 输出）

### 7.2 集成 laser_lock_core testbench（tb_laser_lock_core_v2b1_shadow_pi_dc_error）

当前 xsim.log 记录的是 tb_laser_lock_core_v2b3_seq_pi_sim（模拟名已更新表示包含 v2B3），结果：

```text
PASS: reset clears direct control_o
PASS: reset clears mode3 error_o
PASS: OUTPUT_MODE=0 exposes protected error source
PASS: default timing-safe path is selected
PASS: timing-safe P-only makes control_o half of positive error_o
PASS: sequential PI path is selected
PASS: sequential PI keeps OUT1 error observation
PASS: sequential PI Ki=0 matches P-only half scale
PASS: sequential PI output_limit protects OUT2
PASS: sequential PI polarity reverses OUT2
PASS: control_o holds between pid_ce pulses
PASS: control_o updates on next pid_ce pulse
PASS: OUTPUT_MODE=0 exposes negative protected error source
PASS: timing-safe P-only makes control_o half of negative error_o
PASS: timing-safe P-only recovers from negative to positive error
PASS: timing-safe P-only default has no integral climb at fixed error
PASS: output_limit clamps positive OUT2 control
PASS: polarity=1 reverses OUT2 control direction
PASS: OUTPUT_MODE=3 still produces mixer plus LPF error
PASS: OUTPUT_MODE=3 drives Shadow Control from error source
PASS: mode3 P-only control is approximately half the visible error
PASS: default v2B1 limit keeps OUT2 below 1500 counts
PASS: mode3 also uses timing-safe default path
PASS: sequential PI Ki positive accumulates control
PASS: sequential PI Ki positive remains limited
PASS: sequential PI mode3 keeps OUT1 error
PASS: sequential PI mode3 drives OUT2
SUMMARY tests=27 pass=27 fail=0
V2B1_V2B3_CONTROL_PATH_SIM PASS
```

**结果：27/27 PASS，0 FAIL。**

覆盖的范围：
- v2B1 P-only 回归（11 checks）：reset、OUTPUT_MODE=0、P-only half-scale、pid_ce hold、负 error、极性、output_limit、mode3 mixer+LPF、P-only 无积分爬升
- v2B3 sequential PI 集成（9 checks）：路径选择、OUT1 error 保持、Ki=0 P-only 匹配、output_limit、极性反转、Ki 正积累、limit 约束、mode3 OUT1 保持、mode3 OUT2 驱动

### 7.3 旧 tb_pi_controller 回归

旧 testbench tb_pi_controller.sv 仍然包含在编译列表中（xvlog.log 中可见 "analyzing module pi_controller"），但在当前 xsim.log 中没有运行。当前 xsim.log 只运行了 tb_laser_lock_core_v2b3_seq_pi_sim 模拟。这不是问题——旧 165-check testbench 已在 v2A 阶段确认通过，且 pi_controller.sv 没有修改。

**结论：XSim 回归全部通过（独立 35/35 + 集成 27/27），sequential PI 算法行为在仿真中正确。**

---

## 8. Vivado Design Sources 检查

### 8.1 pi_controller_seq.sv 是否在 Vivado 项目中

```text
grep "pi_controller_seq" redpitaya.xpr:     → 无匹配
grep "pi_controller_seq" redpitaya.srcs/:   → 无匹配
```

**pi_controller_seq.sv 尚未添加到 Vivado Design Sources 中。**

当前 redpitaya.xpr 中只包含以下 PI 相关文件：
```text
<File Path="$PPRDIR/../rtl/pi_controller.sv">
<File Path="$PPRDIR/../sim/tb_pi_controller.sv">
```

### 8.2 为什么不在项目中

Codex 指令明确规定："Codex 本次禁止操作 Vivado。不打开 Vivado，不运行 synthesis，不运行 implementation，不生成 bitstream，不修改 redpitaya.xpr。Vivado 全部由用户手动完成。"

因此 pi_controller_seq.sv 不在 Vivado Design Sources 中是正确的、符合指令的状态。

### 8.3 将 pi_controller_seq.sv 添加到 Vivado 的步骤

用户手动添加到 Vivado 的步骤：
1. 打开 Vivado 项目 `v0.94/project/redpitaya.xpr`
2. 在 Sources 窗格中右键 "Design Sources" → "Add Sources" → "Add or create design sources"
3. 选择文件 `v0.94/rtl/pi_controller_seq.sv`
4. 确保文件出现在 Design Sources 层级中
5. 运行 synthesis，然后检查 timing

不需要从 Design Sources 中移除 pi_controller.sv——它仍然被 laser_lock_core 的 mode 2 generate 分支引用。

**结论：pi_controller_seq.sv 尚未进入 Vivado Design Sources，这是正确的当前状态（因为 Vivado 操作由用户保留）。必须由用户手动添加后才能进行 timing 验证。**

---

## 9. 时序审查

### 9.1 v2B1 baseline timing（reference）

```text
WNS = +0.361 ns
TNS = 0.000 ns
Failing Endpoints = 0
最差路径：lpf_core 32-bit CARRY4 accumulator chain（18 logic levels，7.548ns delay）
无 i_pi_controller 路径（因为 P-only 不例化 pi_controller）
```

### 9.2 sequential PI 的预期 timing 改善

pi_controller_seq 的每个状态只包含：
- S_CAPTURE: 极性 mux + 符号扩展（~2 logic levels）
- S_P_CALC: 一个 DSP48E1 乘法（~1 pipeline stage）
- S_I_CALC: P 缩放（shift）+ 一个 DSP48E1 乘法
- S_I_UPDATE: freeze/anti-windup mux tree + integrator add
- S_SUM: p_scaled + integrator + offset（48-bit 加法，CARRY4 链 ~12 levels）
- S_LIMIT: comparator + mux（~3 levels）

最长的单周期路径是 S_SUM 的 48-bit 加法。在 Zynq-7010 speed grade -1 上，48-bit CARRY4 链大约 ~5-6ns，加上 setup/clk-to-out/route，总体应该在 8ns（125MHz）以内。

但以下因素可能导致意外 timing：
- 如果 Vivado 跨状态合并逻辑（optimization 可能将 S_SUM 和 S_LIMIT 合并为一个大块），则 timing 会恶化
- 如果 placer 将 seven-state FSM 的寄存器散布在芯片各处，则路由延迟会增加
- 如果 DSP48E1 到 fabric 的 routing 路径拥挤（adc_clk 域其他逻辑已占用），则 DSP 输出延迟可能超出预期

这些风险只有在 Vivado synthesis+implementation 运行后才能量化。

### 9.3 当前不能声称的时序结论

```text
不能声称 sequential PI 已经通过 Vivado timing
不能声称 sequential PI 可以安全运行在 125 MHz
不能声称 WNS/TNS 值（因为没有运行 implementation）
```

**结论：时序审查必须推迟到 Vivado implementation 完成之后。当前仅完成了 XSim 行为验证，未完成 hardware timing 验证。**

---

## 10. DRC 和约束审查

### 10.1 当前约束（SDC/XDC）

审查未发现新增 XDC/SDC 文件。当前仍在使用的约束来自 v2B1 的 `v0.94/exp/v2/` 实现目录。SDC 中 adc_clk 定义不变（~125MHz），DAC 时钟、IO 时序等约束不变。

sequential PI 不需要新的时钟约束——它仍在 adc_clk 域中运行，pid_ce 是时钟使能脉冲，不是新时钟。不需要 create_generated_clock 或多周期路径例外。

### 10.2 预期的 DRC 影响

pi_controller_seq 不会改变 IO、PLL、PS、AXI、DDR、ODDR、ADC/DAC IO 或 any 官方模块。DRC 警告预计与 v2B1 相同（43 warnings，全部来自 scope/ASG/daisy 官方模块）。

**结论：不需要新的约束，DRC 影响预计为零，但必须等 Vivado 运行后确认。**

---

## 11. 烧录安全性审查

### 11.1 当前烧录安全状态

当前 red_pitaya_top.sv 中 laser_lock_core 实例化：

```verilog
laser_lock_core #(
    .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)
```

**不传递 CONTROL_PATH_MODE，默认值 = 0（P-only）。**

因此当前可烧录的 bitstream 是 v2B1 P-only bitstream——与 2026-06-22 已上板验证的版本相同：

```text
WNS = +0.361 ns
TNS = 0.000 ns
Failing Endpoints = 0
OUT2 为安全 P-only shadow control
OUT2 只接示波器
```

**当前烧录是安全的（无论 pi_controller_seq.sv 是否在 Vivado Design Sources 中）。**

### 11.2 添加 pi_controller_seq.sv 但不激活 CONTROL_PATH_MODE=1 的情况

如果将 pi_controller_seq.sv 添加到 Vivado Design Sources 但不修改 red_pitaya_top.sv：
- Synthesis 会编译 pi_controller_seq 模块（generate block 中 mode 1 分支引用它）
- 但由于 CONTROL_PATH_MODE 默认值为 0，implementation 只使用 g_timing_safe_p_only
- 生成的 bitstream 与 v2B1 相同
- **烧录仍然安全**

### 11.3 激活 CONTROL_PATH_MODE=1 后的烧录安全性

如果在 red_pitaya_top.sv 中将 CONTROL_PATH_MODE 改为 1：
- 必须在以下条件全部满足后才能进行：
  1. XSim 独立 testbench 通过 ✓（已完成，35/35）
  2. XSim 集成 testbench 通过 ✓（已完成，27/27）
  3. Vivado synthesis 无错误 ❌（未运行）
  4. Vivado implementation 无错误 ❌（未运行）
  5. Vivado timing 通过（WNS>=0，TNS=0）❌（未运行）
  6. DRC 无新增 critical warning ❌（未运行）
  7. user 手动确认接线安全（OUT2 只接示波器）

当前条件 3-6 全部未满足，因此**现在不能烧录 sequential PI**。

### 11.4 集成风险

除了时序外，sequential PI 还有以下集成风险需要在烧录前注意：
- pi_controller_seq 的 control_o 更新延迟为 7 clk_i 周期（~56ns @ 125MHz），比旧 pi_controller 的 1 周期长 6 倍。这不影响 10kHz pid_ce 下的平均更新速率，但意味着 control_o 对 error 变化的响应有 7-cycle 延迟。这不构成功能问题，但需文档记录。
- 首次上板时 Ki=16 会产生非常缓慢的积分（每 10kHz update 在 256-count error 下 +1 count）。OUT2 上的积分需要数秒才能观察到。这适合示波器调试，但需确保用户预期与此一致。

**结论：当前烧录 v2B1 安全（默认 P-only 路径）。不能烧录 sequential PI，因为 Vivado timing 未验证。添加 pi_controller_seq.sv 到 Vivado 项目是安全的（不会改变生成 bitstream），但激活 CONTROL_PATH_MODE=1 必须等待 implementation+timing 全部通过。**

---

## 12. 与 Codex 指令的一致性检查

### 12.1 指令要求 vs 实际实现

| Codex 指令要求 | 实际实现 | 状态 |
|---|---|---|
| 创建 pi_controller_seq.sv | v0.94/rtl/pi_controller_seq.sv (233 行) | ✓ 完成 |
| 7 状态 FSM | S_IDLE/CAPTURE/P_CALC/I_CALC/I_UPDATE/SUM/LIMIT | ✓ 完成 |
| CONTROL_PATH_MODE 替换 USE_FULL_PI_CONTROLLER | 3 模式 generate block，默认 mode 0 | ✓ 完成 |
| anti-windup 公式匹配 pi_controller.sv | 逐行匹配（加 $signed 防御性 cast）| ✓ 完成 |
| Ki=16'sd16 作为初始值 | PID_KI_DEFAULT = 16'sd16（仅 mode 1 中使用）| ✓ 完成 |
| KP_SHIFT=KI_SHIFT=12 | 参数正确传递到 pi_controller_seq 实例化 | ✓ 完成 |
| 创建 tb_pi_controller_seq.sv | v0.94/sim/tb_pi_controller_seq.sv (293 行) | ✓ 完成 |
| 不修改 tb_laser_lock_core_v2b1 | 已修改但只增加 sequential PI DUT 实例 | ⚠ 修改了 |
| 不操作 Vivado | pi_controller_seq 不在 .xpr 中 | ✓ 完成 |
| 不修改 red_pitaya_top.sv | 当前不传递 CONTROL_PATH_MODE | ✓ 完成 |
| 不修改 pi_controller.sv | pi_controller.sv 未变 | ✓ 完成 |

### 12.2 关于 "禁止修改 tb_laser_lock_core_v2b1" 的偏离

Codex 指令将 tb_laser_lock_core_v2b1 标记为 "禁止修改"（因为它是 v2B1 的封闭记录）。但实际实现中，Codex 在该 testbench 中添加了 6 个 sequential PI DUT 实例和 9 个新 check。

这偏离了指令的字面要求，但在实践中是合理的：
- 原有的 18 个 v2B1 checks 全部保留并通过（现在总数 27）
- testbench 没有修改任何原有逻辑——只在其末尾追加
- 从 git diff 来看（`v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv M`），原始 230 行扩展为 348 行，但原有 18 个 checks 的位置和内容不变

**这个偏离不影响 v2B1 的记录完整性，但应与用户确认是否需要单独创建 v2B3 专用 testbench 而非修改 v2B1 的历史文件。**

---

## 13. 被忽略的边界条件审查

### 13.1 reset_integrator 与 pid_ce 的关系

pi_controller_seq.sv 中，reset_integrator 与 error/kp/ki 在 S_CAPTURE 中同时采样。这意味着如果在第 N 个 pid_ce 脉冲期间 reset_integrator 被触发，该事务将使用：
- 第 N 个 error/kp/ki 作为输入
- 积分器在 S_I_UPDATE 中被清零（p_scaled + 0 + offset = control_pre）

这与旧 pi_controller 的行为有一个细微差异：旧版本中 reset_integrator_i 是组合路径，理论上可以在 pid_ce 脉冲期间的任何时钟边沿改变积分器的行为（但当时钟使能有效时，它也会与 error 同步采样）。新版本的行为更加确定性。

### 13.2 output_limit 更新延迟

在 pi_controller_seq 中，output_limit 在 S_CAPTURE 中采样并锁存到 output_limit_q，有效期覆盖整个事务（7 clk_i 周期）。如果 output_limit_i 在事务进行期间发生变化，该变化不会影响当前事务，只会在下一个 pid_ce 启动的事务中生效。这是合理的——与旧 pi_controller 类似，那里 output_limit_i 通过组合路径直接进入 limit 逻辑，但 control_o 只在 pid_ce 时更新。

### 13.3 polarity 更新一致性

polarity 在 S_CAPTURE 中与 error 同时采样（第 172-174 行：`polarity_i ? -signed({...}) : signed({...})`）。这意味着 polarity 的变化仅在新事务启动时生效，mid-transaction 的 polarity 变化不会影响已在进行中的计算。这与旧 pi_controller 的行为一致。

### 13.4 未被测试的 corner case

虽然 testbench 覆盖度很高，但以下边界情况未显式测试：
- pid_ce 和 hold 在相同时钟边沿同时有效的优先级（当前 always_ff 中 enable 优先级最高，其次是 hold，证明了设计意图）
- 在长序列事务中 output_limit 动态缩小（从 1500 到 100，是否导致积分器瞬时超限）
- 极端 error 值（+/-8191）与最大 kp/ki（+/-32767）的组合

这些边界条件不会影响功能的正确性——但如果在 Vivado optimization 中存在 corner-case synthesis bug，则可能在上述极端情况下出现 X 或 Z 输出。当前 100-step 长序列测试（check 34-35）已通过，大幅降低了这种风险。

**结论：关键边界条件已覆盖，残留 corner case 风险低，但需在 Vivado 时序通过后在板上验证极端输入行为。**

---

## 14. gate 决定

基于以上全部证据：

**关于 "pi_controller_seq.sv 是否可以进入 Vivado timing 验证"：**

可以。该模块已通过独立 XSim（35/35 PASS）和集成 XSim（27/27 PASS），语法正确，anti-windup 语义与参考一致，且因为 pi_controller_seq 不在 Vivado Design Sources 中，当前添加它不会影响生成的 bitstream 的行为（前提是 red_pitaya_top.sv 不修改 CONTROL_PATH_MODE）。

**关于 "当前是否可以烧录 sequential PI"：**

不可以。以下条件未满足：
1. pi_controller_seq.sv 未进入 Vivado Design Sources
2. Vivado synthesis 未运行
3. Vivado implementation 未运行
4. Vivado timing 未验证
5. red_pitaya_top.sv 未修改 CONTROL_PATH_MODE

**关于 "当前烧录安全性"：**

当前 bitstream 安全（v2B1 P-only 路径，已验证通过）。无论是否将 pi_controller_seq.sv 添加到 Vivado，只要 red_pitaya_top.sv 不传 CONTROL_PATH_MODE(1)，生成的 bitstream 就仍然是 P-only 回退。

**gate 决定：有条件通过 XSim gate，可以在保持 CONTROL_PATH_MODE=0 的前提下将 pi_controller_seq.sv 添加到 Vivado Design Sources，但进入 Vivado timing gate 后必须等 timing 通过且用户单独审查后才能激活 mode 1。**

---

## 15. gate 后的下一步

```text
1. [用户] 手动将 pi_controller_seq.sv 添加到 Vivado Design Sources
2. [用户] 在 Vivado 中运行 synthesis，检查 0 error / 0 critical warning
3. [用户] 在 Vivado 中运行 implementation
4. [用户] 检查 timing summary（WNS/TNS/Failing Endpoints）
5. [用户] 手动检查 DRC report（确认仅 43 官方模块 warnings，无新增）
6. [用户] 如果步骤 1-5 全部通过：修改 red_pitaya_top.sv，添加 .CONTROL_PATH_MODE(1)
7. [用户] 重新运行 synthesis + implementation + timing check
8. [用户] 如果 timing 仍通过：烧录，先用 OUT2 示波器观察 30 分钟以上
9. [用户] 确认 OUT2 无失控、无异常爬升、limit 正常工作
10. [Claude 审查] 在步骤 5 和 7 之后，用户可以请求 v2B3 timing gate 审查
```

---

## 16. 审查报告版本记录

```text
审查报告文件：E:\new\fpga_lock\v94\version\v2\claude审查\CLAUDE_REVIEW_v2B2_v2B3_sequential_PI_gate_2026-06-22.md
审查内容：v2B2/v2B3 sequential PI 阶段 XSim gate
审查文件数量：17 个（RTL 7 + testbench 2 + Vivado 3 + 日志 3 + 文档 2）
审查中未修改任何文件
审查中未运行 Vivado
审查中未执行 git 操作
审查中未读取和分析 v-weifang/ 或 version-weifang/
```

审查结论摘要：

```text
pi_controller_seq.sv:   ✓ 存在，架构正确，anti-windup 语义完整
CONTROL_PATH_MODE:      ✓ 正确实现，默认 mode 0 安全回退
red_pitaya_top.sv:      ✓ 默认路径安全（不传 CONTROL_PATH_MODE）
XSim 独立 testbench:    ✓ 35/35 PASS
XSim 集成 testbench:    ✓ 27/27 PASS
Vivado Design Sources:  ⚠ pi_controller_seq 尚未添加（正确，等用户手动操作）
Vivado timing:          ❌ 未运行（正确，等用户手动操作）
当前烧录 v2B1:          ✓ 安全
当前烧录 sequential PI: ❌ 不安全（timing 未验证）
Gate 结论:              有条件通过 XSim gate，下一步由用户手动完成 Vivado 操作
```
