# CODEX v2B2/v2B3 sequential / pipelined PI 实现指令

**发出日期**: 2026-06-22
**阶段**: v2B2 + v2B3
**目标**: 实现 timing-clean sequential PI controller，并准备接回 OUT2
**Claude 审查预检**: 已通过（本指令已经 Claude 审查并修正）

---

## 0. 背景

v2B1 timing-safe P-only Shadow Control 上板示波器验证已完成：

```text
WNS = +0.361 ns
TNS = 0.000 ns
Failing Endpoints = 0
mixer.csv: OUT2 / OUT1 ≈ 0.515
no-mixer.csv: OUT2 / OUT1 ≈ 0.555
```

v2B1 证明了 OUT1 能输出 FPGA mixer+LPF error，OUT2 能输出安全的小 P-only shadow control。但 v2B1 不能锁定激光——它不是完整 PI，没有积分 I，OUT2 只接示波器。

下一步直接进入：
- v2B2：实现 timing-clean sequential PI controller
- v2B3：把新的 PI controller 接回 laser_lock_core 的 OUT2 路径

---

## 1. 最高权限边界

Codex 本次禁止操作 Vivado。

```
不打开 Vivado
不运行 synthesis
不运行 implementation
不生成 bitstream
不生成 bin
不烧录
不修改 redpitaya.xpr
不修改 XDC/SDC
不读取、分析或修改 v-weifang/
不读取、分析或修改 version-weifang/
不读取、分析或修改 guanfang-v0.94/
```

Vivado 全部由用户手动完成。

---

## 2. 必须先读取的文件

```
GPT_README.md
version/STATUS.md
version/v2/V2_DEVELOPMENT_ROADMAP.md
version/v2/V2_EXPERIMENT_SOP.md
version/v2/V2_NEXT_STEPS.md
version/v2/V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md
version/v2/V2_PI_PID_DESIGN_SPEC.md

version/rules/00_PROJECT_DEVELOPMENT_RULES.md
version/rules/03_FPGA_CODE_REVIEW_RULES.md
version/rules/04_EXPERIMENT_RECORD_RULES.md
version/rules/06_V2_PID_DEVELOPMENT_RULES.md
version/rules/RULE_CODEX_ENGINEER_TEACHER.md

v0.94/rtl/laser_lock_core.sv
v0.94/rtl/pi_controller.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/red_pitaya_top.sv

v0.94/sim/tb_pi_controller.sv
v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv
```

最终输出必须列出实际读取文件。

---

## 3. 原 pi_controller.sv 处理

```
保留 v0.94/rtl/pi_controller.sv。
不删除，不改坏。
它是 v2A 已验证的完整 PI 参考实现（tb_pi_controller: 165/165 PASS）。
它不能直接作为 125 MHz 主工程默认路径（之前 timing failed: WNS≈-10.995 ns）。
新模块基于它的算法意图设计 timing-clean 版本，不删改原文件。
```

---

## 4. 允许修改 / 新增 / 禁止修改

### 4.1 允许新增

```
v0.94/rtl/pi_controller_seq.sv
v0.94/sim/tb_pi_controller_seq.sv
v0.94/sim/tb_laser_lock_core_v2b3_seq_pi.sv
```

### 4.2 允许修改

```
v0.94/rtl/laser_lock_core.sv
version/STATUS.md
version/v2/V2_NEXT_STEPS.md
version/v2/V2_DEVELOPMENT_ROADMAP.md
version/v2/V2_EXPERIMENT_SOP.md
```

### 4.3 禁止修改

```
v0.94/rtl/pi_controller.sv
v0.94/rtl/mixer_core.sv
v0.94/rtl/lpf_core.sv
v0.94/rtl/output_protect.sv
v0.94/rtl/red_pitaya_top.sv
v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv
v0.94/sdc/
v0.94/project/redpitaya.xpr
```

`tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` 是 v2B1 阶段的关闭记录，不修改它。v2B3 集成测试用新增的 testbench。

---

## 5. v2B2：pi_controller_seq.sv 详细 spec

### 5.1 模块接口

```systemverilog
module pi_controller_seq #(
    parameter int ERROR_WIDTH = 14,
    parameter int GAIN_WIDTH  = 16,
    parameter int OUT_WIDTH   = 14,
    parameter int ACC_WIDTH   = 48,
    parameter int KP_SHIFT    = 12,
    parameter int KI_SHIFT    = 12
)(
    input  logic                              clk_i,
    input  logic                              rstn_i,
    input  logic                              pid_ce_i,
    input  logic                              enable_i,
    input  logic                              hold_i,
    input  logic                              reset_integrator_i,
    input  logic                              polarity_i,

    input  logic signed [ERROR_WIDTH-1:0]     error_i,
    input  logic signed [GAIN_WIDTH-1:0]      kp_i,
    input  logic signed [GAIN_WIDTH-1:0]      ki_i,
    input  logic signed [OUT_WIDTH-1:0]       offset_i,
    input  logic        [OUT_WIDTH-1:0]       output_limit_i,

    output logic signed [OUT_WIDTH-1:0]       control_o,
    output logic signed [31:0]                p_term_o,
    output logic signed [31:0]                i_term_o,
    output logic                              sat_o
);
```

### 5.2 定点格式（与旧 pi_controller 完全一致）

```text
ERROR_EXT_WIDTH = ERROR_WIDTH + 1 = 15
PRODUCT_WIDTH   = ERROR_EXT_WIDTH + GAIN_WIDTH = 15 + 16 = 31

P product = error(sign-extended to 15-bit) × kp(16-bit) → 31-bit signed
I product = 同上 × ki(16-bit) → 31-bit signed

P_scaled = P_product >>> KP_SHIFT (KP_SHIFT=12)
I_scaled = I_product >>> KI_SHIFT (KI_SHIFT=12)

I_delta  = I_scaled, sign-extended to ACC_WIDTH (48-bit)
P_scaled_ext = P_scaled, sign-extended to ACC_WIDTH

integrator width = ACC_WIDTH = 48-bit

Kp=2048 配合 KP_SHIFT=12 → OUT2 ≈ error_o / 2（与 v2B1 P-only 行为一致）
Ki 初始非常小（如 16'sd16），配合 KI_SHIFT=12 → 积分非常缓慢
```

### 5.3 状态机结构（7 状态）

所有逻辑在 clk_i 域。pid_ce_i 只是启动脉冲，不是新 clock。

```text
IDLE (3'd0):
  等待 pid_ce_i 上升沿。
  收到 pid_ce_i=1 时 → CAPTURE。
  否则停留在 IDLE。
  在 IDLE 期间，所有输出寄存器保持当前值。

CAPTURE (3'd1):
  锁存 error_i, kp_i, ki_i, offset_i, output_limit_i,
       enable_i, hold_i, polarity_i, reset_integrator_i。
  error 做 sign-extension: error_ext = {error_i[13], error_i}。
  → POLARITY。

POLARITY (3'd2):
  if (polarity_i)
      error_pol = -error_ext;   // 15-bit signed negation
  else
      error_pol = error_ext;
  error_pol 寄存。
  → P_CALC。

P_CALC (3'd3):
  p_product = $signed(error_pol) * $signed(kp_i_latched);   // 15×16→31
  p_scaled  = p_product >>> KP_SHIFT;                       // 算术右移
  p_scaled 寄存。
  → I_CALC。

I_CALC (3'd4):
  i_product = $signed(error_pol) * $signed(ki_i_latched);
  i_scaled  = i_product >>> KI_SHIFT;
  i_delta   = {{(ACC_WIDTH-31){i_scaled[30]}}, i_scaled};   // 符号扩展到 48-bit
  i_delta 寄存。
  → I_UPDATE。

I_UPDATE (3'd5):
  注意：此状态处理 anti-windup、integrator 更新、reset_integrator。
  优先级顺序与旧 pi_controller 一致：
    1. reset_integrator_i_latched → integrator = 0
    2. 否则，anti-windup 检查
    3. 否则，integrator = integrator + i_delta
    4. integrator 对称钳位到 ±limit_pos (48-bit)

  anti-windup 精确算法（与 pi_controller.sv 第 97-99 行一致）：
    current_control_pre = p_scaled_ext + integrator + offset_ext(48-bit)
    freeze = (current_control_pre >= limit_pos) && (i_delta > 0)
          || (current_control_pre <= limit_neg) && (i_delta < 0)
    if (freeze)
        integrator_candidate = integrator (保持)
    else
        integrator_candidate = integrator + i_delta

    integrator_accepted = clamp(integrator_candidate, limit_neg, limit_pos)

  integrator_accepted 寄存。
  → SUM。

SUM (3'd6):
  control_pre = p_scaled_ext + integrator_accepted + offset_ext
  control_pre 寄存（48-bit）。
  → LIMIT。

LIMIT (3'd7):
  if (control_pre > limit_pos)
      control_o_next = limit_pos[OUT_WIDTH-1:0];
      sat = 1;
  else if (control_pre < limit_neg)
      control_o_next = limit_neg[OUT_WIDTH-1:0];
      sat = 1;
  else
      control_o_next = control_pre[OUT_WIDTH-1:0];
      sat = 0;
  → DONE。

DONE (3'd0 → IDLE):
  更新 control_o, p_term_o, i_term_o, sat_o（全部寄存器输出）。
  回到 IDLE。
```

### 5.4 control_o 输出逻辑（clk_i 同步寄存器）

```systemverilog
always_ff @(posedge clk_i) begin
    if (!rstn_i) begin
        control_o    <= '0;
        p_term_o     <= '0;
        i_term_o     <= '0;
        sat_o        <= 1'b0;
        state        <= IDLE;
    end else if (!enable_i) begin
        control_o    <= '0;
        p_term_o     <= '0;
        i_term_o     <= '0;
        sat_o        <= 1'b0;
        state        <= IDLE;
    end else if (hold_i) begin
        // 所有输出保持，状态机停在 IDLE
        control_o    <= control_o;
        p_term_o     <= p_term_o;
        i_term_o     <= i_term_o;
        sat_o        <= sat_o;
        state        <= IDLE;
    end else begin
        case (state)
            IDLE: begin
                if (pid_ce_i) state <= CAPTURE;
                // outputs hold
            end
            ...
            DONE: begin
                control_o    <= control_o_next;
                p_term_o     <= p_scaled_ext[31:0];
                i_term_o     <= integrator_accepted[31:0];
                sat_o        <= sat_next;
                state        <= IDLE;
            end
            default: state <= IDLE;
        endcase
    end
end
```

### 5.5 关键约束

```text
- control_o 必须是寄存器输出（不是组合逻辑输出）。
- p_term_o, i_term_o, sat_o 必须是寄存器输出。
- 每个状态内部的所有算术运算在单周期内完成。
  状态间通过寄存器传递数据，确保相邻寄存器间组合逻辑深度 ≤ 约 6-8 levels。
- 不依赖 multicycle path。
- 不依赖 false_path 约束。
- reset_integrator 只在 pid_ce 触发的序列内处理（不在 IDLE 时异步清零积分器），
  但保持与旧 pi_controller 相同的语义：
  reset_integrator=1 时，control_o 仍输出 P + offset（积分项清零），
  而非输出 0。
- 初始参数保守：
  KP_SHIFT = 12, KI_SHIFT = 12
  Kp = 2048 → OUT2 ≈ error_o / 2
  Ki = 16（非常小）→ 积分缓慢累积
  output_limit = 1500 → 约 ±0.18V
  OUT2 仍只接示波器。
```

---

## 6. v2B3：laser_lock_core.sv 修改

### 6.1 用 CONTROL_PATH_MODE 替换 USE_FULL_PI_CONTROLLER

```systemverilog
// CONTROL_PATH_MODE selects which OUT2 control path is elaborated:
// 0: timing-safe P-only Shadow Control (v2B1 default, current fallback).
// 1: sequential / pipelined PI controller (v2B3 target path).
// 2: legacy full pi_controller (sim/reference only; do NOT use as default
//    board path — direct 125 MHz integration caused WNS≈-10.995 ns timing
//    failure).
// 0 is the safe default. Switch to 1 only after pi_controller_seq
// standalone sim PASS, integrated sim PASS, Vivado timing MET,
// and OUT2 oscilloscope test PASS.
parameter int CONTROL_PATH_MODE = 0;
```

**删除**旧的 `parameter bit USE_FULL_PI_CONTROLLER = 1'b0`。

### 6.2 generate 块改为三个分支

```systemverilog
generate
    if (CONTROL_PATH_MODE == 0) begin : g_timing_safe_p_only
        // 保持当前 v2B1 P-only Shadow Control，完全不变。
        // （把现在第 247-307 行的 P-only 代码移到这里）
    end else if (CONTROL_PATH_MODE == 1) begin : g_seq_pi
        // 新增：实例化 pi_controller_seq
        pi_controller_seq #(
            .ERROR_WIDTH(14),
            .GAIN_WIDTH (16),
            .OUT_WIDTH  (14),
            .ACC_WIDTH  (48),
            .KP_SHIFT   (12),
            .KI_SHIFT   (12)
        ) i_pi_controller_seq (
            .clk_i             (clk_i),
            .rstn_i            (rstn_i),
            .pid_ce_i          (pid_ce_q),
            .enable_i          (PID_ENABLE_DEFAULT),
            .hold_i            (PID_HOLD_DEFAULT),
            .reset_integrator_i(PID_RESET_INTEGRATOR_DEFAULT),
            .polarity_i        (PID_POLARITY_DEFAULT),
            .error_i           (protected_error),
            .kp_i              (PID_KP_DEFAULT),
            .ki_i              (PID_KI_DEFAULT),
            .offset_i          (PID_OFFSET_DEFAULT),
            .output_limit_i    (PID_OUTPUT_LIMIT_DEFAULT),
            .control_o         (control_o),
            .p_term_o          (p_term_unused),
            .i_term_o          (i_term_unused),
            .sat_o             (sat_unused)
        );
    end else if (CONTROL_PATH_MODE == 2) begin : g_full_pi_controller
        // 旧 pi_controller 实例化（当前第 207-246 行代码，完全不变）
        // 仅仿真/参考，不作为默认上板路径
        pi_controller #(...) i_pi_controller (...);
    end
endgenerate
```

### 6.3 保持 P-only 回退路径可用

```text
- CONTROL_PATH_MODE = 0 始终可用且 timing-safe。
- 即使 pi_controller_seq.sv 已写好，默认仍保持 CONTROL_PATH_MODE = 0。
- 只有全部验证通过后，才手动改为 CONTROL_PATH_MODE = 1。
- 改参数后再 Vivado 编译。
```

### 6.4 参数默认值

```systemverilog
parameter bit PID_ENABLE_DEFAULT = 1'b1;     // OUT2 只接示波器时安全
parameter bit PID_HOLD_DEFAULT = 1'b0;
parameter bit PID_RESET_INTEGRATOR_DEFAULT = 1'b0;
parameter bit PID_POLARITY_DEFAULT = 1'b0;
parameter logic signed [15:0] PID_KP_DEFAULT = 16'sd2048;   // OUT2 ≈ error_o/2
parameter logic signed [15:0] PID_KI_DEFAULT = 16'sd16;     // 非常小的 Ki，缓慢积分
parameter logic signed [13:0] PID_OFFSET_DEFAULT = 14'sd0;
parameter logic [13:0] PID_OUTPUT_LIMIT_DEFAULT = 14'd1500; // ±0.18V
```

---

## 7. testbench 要求

### 7.1 新增 tb_pi_controller_seq.sv

必须覆盖以下测试项（参照 tb_pi_controller.sv 的覆盖范围）：

```text
 1. reset → control_o = 0, integrator = 0
 2. enable = 0 → control_o = 0
 3. hold = 1 → control_o 保持, state stuck in IDLE
 4. pid_ce 脉冲触发状态机 → 固定延迟后 control_o 更新
 5. pid_ce 到 control_o 的延迟是确定值（N 个 clk）
 6. 状态机忙碌期间，新的 pid_ce 脉冲不误触发
 7. positive error → P-only (Ki=0) → control_o = error × Kp >>> KP_SHIFT
 8. negative error → control_o 为负
 9. polarity=1 → control_o 反号
10. small Ki > 0 → 恒定 error 下积分缓慢累积
11. Ki 积分累积速率与预期一致（每个 pid_ce 增加 error × Ki >>> KI_SHIFT）
12. output_limit 钳位 positive control_o
13. output_limit 钳位 negative control_o
14. anti-windup: 当 P+I+offset 达到 limit 时，积分器冻结不继续累积
15. anti-windup: 当 error 反向后，积分器能正常退出 windup
16. reset_integrator = 1 → integrator = 0, control_o = P + offset
17. offset 正确叠加到 control_o
18. sat_o 在输出钳位时 = 1, 未钳位时 = 0
19. p_term_o 输出 P 分量, i_term_o 输出 I 分量
20. pid_ce 背靠背脉冲的正确处理
21. 长时稳定性：100 次 pid_ce 无漂移

SUMMARY tests=N pass=N fail=0
V2B2_PI_CONTROLLER_SEQ_SIM PASS
```

### 7.2 新增 tb_laser_lock_core_v2b3_seq_pi.sv

基于 `tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` 的结构，但测试 `CONTROL_PATH_MODE=1`：

```text
 1. OUT1 仍是 error observation (OUTPUT_MODE=3)
 2. OUT2 来自 sequential PI (CONTROL_PATH_MODE=1)
 3. Ki=0 时行为接近 P-only（与 v2B1 基线对比）
 4. Ki>0 时有可解释的积分累积
 5. output_limit 生效
 6. polarity 生效
 7. mode3 mixer+LPF error 能进入 sequential PI
 8. reset → control_o = 0, error_o = 0
 9. enable=0 → control_o = 0
10. P-only 回退路径（CONTROL_PATH_MODE=0）仍可用
11. 确认 CONTROL_PATH_MODE 参数控制正确

SUMMARY tests=N pass=N fail=0
V2B3_LASER_LOCK_CORE_SEQ_PI_SIM PASS
```

---

## 8. 文档更新要求

更新以下文件，写清楚：

```text
v2B1 已关闭：OUT2 安全输出验证通过 (WNS=+0.361 ns, OUT2/OUT1≈0.515)。
v2B2 开始：新增 pi_controller_seq.sv，7 状态 sequential PI。
v2B3 目标：用 CONTROL_PATH_MODE=1 将 sequential PI 接回 OUT2。
CONTROL_PATH_MODE=0 始终作为 timing-safe 回退路径。
旧 pi_controller.sv 保留不修改，在 CONTROL_PATH_MODE=2 分支中仅仿真/参考。
当前仍不允许 OUT2 接激光。
只有 sequential PI 的 XSim PASS + Vivado timing PASS + OUT2 示波器 PASS 全部通过后，才讨论低增益闭环。
```

具体文件修改范围：

```text
version/STATUS.md：追加 v2B1 关闭 + v2B2/v2B3 启动记录
version/v2/V2_NEXT_STEPS.md：更新下一步为 v2B2 开发 + 用户手动 Vivado
version/v2/V2_DEVELOPMENT_ROADMAP.md：标记 v2B1 完成，v2B2 in progress
version/v2/V2_EXPERIMENT_SOP.md：追加 pi_controller_seq 上板验证 SOP
```

---

## 9. 本次禁止操作

```
不要修改 pi_controller.sv
不要修改 mixer_core.sv
不要修改 lpf_core.sv
不要修改 output_protect.sv
不要修改 red_pitaya_top.sv
不要修改 tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv
不要修改 XDC/SDC
不要修改 redpitaya.xpr
不要运行 Vivado
不要生成 bitstream
不要烧录
不要做 AI / CNN
不要做 scan/lock FSM
不要做 ramp generator
不要做双执行器
不要做自动重锁
不要读取 v-weifang/ guanfang-v0.94/ version-weifang/
```

本次目标只有一个：**让 FPGA 拥有一个能过 timing 的 PI 控制器，并准备重新接回 OUT2。**

---

## 10. 最终输出格式要求

Codex 完成后，必须输出以下结构的总结：

### A. 实际读取文件
列出所有实际读取的文件路径。

### B. v2B1 关闭结论
说明 OUT2 输出通道已验证通过（引用上板数据）。

### C. 新增 / 修改文件
列出新增的 RTL、SIM、MD，以及修改的 RTL、SIM、MD。

### D. pi_controller_seq.sv 架构说明
说明每个状态做什么、每个寄存器何时更新、每个输出何时有效。
说明 7 状态对应 7 clk 延迟，在 125 MHz 下 = 56 ns，对 10 kHz PI 更新可忽略。

### E. 与旧 pi_controller.sv 的关系
```text
pi_controller.sv：保留，不删除，不修改。v2A 已验证参考实现。
pi_controller_seq.sv：新模块。相同算法、相同定点格式、相同 anti-windup 策略，
  但用 7 状态 SM 替代长组合路径，确保 timing-clean。
control_o 行为应与 pi_controller.sv 在仿真中输出一致（等延迟后）。
```

### F. XSim 结果
```text
tb_pi_controller_seq: tests=/pass=/fail=
tb_laser_lock_core_v2b3_seq_pi: tests=/pass=/fail=
```

### G. Vivado 状态
```text
未运行 Vivado
未运行 synthesis
未运行 implementation
未生成 bitstream
未生成 bin
未烧录
```

### H. 用户下一步（交给用户手动执行）
```text
1. 打开 v0.94/project/redpitaya.xpr
2. 确认 pi_controller_seq.sv 在 Design Sources
3. 确认 laser_lock_core.sv 引用正确的 v0.94/rtl/ 路径
4. 确认 red_pitaya_top 为 Design Top
5. 确认所有 tb_*.sv 不在 Design Sources
6. Run Synthesis
7. Run Implementation
8. 检查 timing summary：WNS ≥ 0, TNS = 0
9. 确认 worst path 不在 pi_controller_seq 内部
10. timing 通过后 Generate Bitstream
11. 转换 .bit → .bit.bin, scp 到 Red Pitaya
12. fpgautil -b 加载
13. 烧录后 OUT1 接 CH2, OUT2 接 CH4
14. 仍不接激光器
```
