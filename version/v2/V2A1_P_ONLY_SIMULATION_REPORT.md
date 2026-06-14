# V2A1 P-Only 独立 XSim 仿真报告

本文档是 v2a-1 P-only 独立 RTL 的完整静态复审、仿真证据整理与状态报告。

## 1. 测试目标

验证 `pi_controller.sv`（v2a-1 P-only skeleton）在独立 XSim 仿真中的功能正确性，覆盖：
- 低有效同步复位（`rstn_i`）
- `enable_i` 安全输出零
- `enable_i` 优先于 `hold_i`
- reset 优先于一切
- `pid_ce_i` 作为 clock enable
- P 通道乘法和移位（signed 14-bit × signed 16-bit → 31-bit → KP_SHIFT → 48-bit ACC）
- `polarity_i` 符号翻转且不溢出
- `offset_i` 符号扩展加法
- `output_limit_i` 正负对称限幅
- `output_limit_i` 上限钳位到 8191
- `output_limit_i=0` 输出全零
- 正/负饱和
- `hold_i` 状态保持
- I 通道占位（`i_term_o` 固定为 0）
- 连续 `pid_ce` 更新

## 2. DUT 文件路径

```
E:\new\fpga_lock\v94\v0.94\rtl\pi_controller.sv
```

## 3. Testbench 文件路径

```
E:\new\fpga_lock\v94\v0.94\sim\tb_pi_controller.sv
```

## 4. Vivado / XSim 版本

```
Vivado Simulator 2020.1 (64-bit)
SW Build 2902540 on Wed May 27 19:54:49 MDT 2020
```

## 5. 编译命令（xvlog）

```tcl
xvlog -sv rtl/pi_controller.sv sim/tb_pi_controller.sv
```

实际日志文件：`E:\new\fpga_lock\v94\v0.94\xvlog.log`

xvlog 返回结果：
```
INFO: [VRFC 10-2263] Analyzing SystemVerilog file "rtl/pi_controller.sv" into library work
INFO: [VRFC 10-311] analyzing module pi_controller
INFO: [VRFC 10-2263] Analyzing SystemVerilog file "sim/tb_pi_controller.sv" into library work
INFO: [VRFC 10-311] analyzing module tb_pi_controller
```

编译通过，无 warning，无 error。

## 6. Elaboration 命令（xelab）

```tcl
xelab tb_pi_controller -s tb_pi_controller_sim
```

实际日志文件：`E:\new\fpga_lock\v94\v0.94\xelab.log`

xelab 返回结果：
```
Starting static elaboration
Pass Through NonSizing Optimizer
Completed static elaboration
Starting simulation data flow analysis
Completed simulation data flow analysis
Time Resolution for simulation is 1ps
Compiling module work.pi_controller(KP_SHIFT=4,KI_SHIFT=4,...)
Compiling module work.tb_pi_controller
Built simulation snapshot tb_pi_controller_sim
```

Elaboration 通过，无 error，无 warning。

## 7. 仿真命令（xsim）

```tcl
xsim tb_pi_controller_sim -autoloadwcfg -runall
```

实际日志文件：`E:\new\fpga_lock\v94\v0.94\xsim.log`

xsim 返回结果：
```
tb_pi_controller summary: tests=65 pass=65 fail=0
$finish called at time: 670 ns
```

仿真通过，无 error，无 warning。

## 8. 测试项目清单及结果

| # | 测试项目 | 结果 |
|---|---------|------|
| 1 | low active reset clears control | PASS |
| 2 | low active reset clears p_term | PASS |
| 3 | low active reset clears i_term | PASS |
| 4 | low active reset clears sat | PASS |
| 5 | positive error positive kp (error=100, kp=16) | PASS |
| 6 | positive error positive kp i_term_zero | PASS |
| 7 | positive error positive kp sat | PASS |
| 8 | enable low clears control | PASS |
| 9 | enable low clears i_term | PASS |
| 10 | pid_ce low holds control | PASS |
| 11 | negative error positive kp (error=-100, kp=16) | PASS |
| 12 | negative error positive kp i_term_zero | PASS |
| 13 | negative error positive kp sat | PASS |
| 14 | polarity flips sign (error=-100, polarity=1) | PASS |
| 15 | polarity flips sign i_term_zero | PASS |
| 16 | polarity flips sign sat | PASS |
| 17 | positive offset (offset=+25) | PASS |
| 18 | positive offset i_term_zero | PASS |
| 19 | positive offset sat | PASS |
| 20 | negative offset (offset=-25) | PASS |
| 21 | negative offset i_term_zero | PASS |
| 22 | negative offset sat | PASS |
| 23 | positive saturation (error=8191, kp=128, limit=200) | PASS |
| 24 | positive saturation i_term_zero | PASS |
| 25 | positive saturation sat | PASS |
| 26 | negative saturation (error=-8192, kp=128, limit=200) | PASS |
| 27 | negative saturation i_term_zero | PASS |
| 28 | negative saturation sat | PASS |
| 29 | output limit zero (limit=0) | PASS |
| 30 | output limit zero i_term_zero | PASS |
| 31 | output limit zero sat | PASS |
| 32 | hold setup (error=200, kp=16) | PASS |
| 33 | hold setup i_term_zero | PASS |
| 34 | hold setup sat | PASS |
| 35 | hold keeps control (hold=1, error changed to -700) | PASS |
| 36 | hold keeps i_term | PASS |
| 37 | maximum positive error (error=8191) | PASS |
| 38 | maximum positive error i_term_zero | PASS |
| 39 | maximum positive error sat | PASS |
| 40 | minimum negative error (error=-8192) | PASS |
| 41 | minimum negative error i_term_zero | PASS |
| 42 | minimum negative error sat | PASS |
| 43 | minimum negative error polarity no overflow (error=-8192, polarity=1) | PASS |
| 44 | minimum negative error polarity no overflow i_term_zero | PASS |
| 45 | minimum negative error polarity no overflow sat | PASS |
| 46 | enable priority setup | PASS |
| 47 | enable priority setup i_term_zero | PASS |
| 48 | enable priority setup sat | PASS |
| 49 | enable priority over hold (enable=0, hold=1) | PASS |
| 50 | reset priority setup | PASS |
| 51 | reset priority setup i_term_zero | PASS |
| 52 | reset priority setup sat | PASS |
| 53 | reset priority highest (rstn=0, enable=0, hold=1, pid_ce=1) | PASS |
| 54 | consecutive pid_ce update 1 (error=100) | PASS |
| 55 | consecutive pid_ce update 1 i_term_zero | PASS |
| 56 | consecutive pid_ce update 1 sat | PASS |
| 57 | consecutive pid_ce update 2 (error=200) | PASS |
| 58 | consecutive pid_ce update 2 i_term_zero | PASS |
| 59 | consecutive pid_ce update 2 sat | PASS |
| 60 | consecutive pid_ce update 3 (error=-300) | PASS |
| 61 | consecutive pid_ce update 3 i_term_zero | PASS |
| 62 | consecutive pid_ce update 3 sat | PASS |
| 63 | ki change leaves i_term zero | PASS |
| 64 | reset_integrator placeholder leaves i_term zero | PASS |
| 65 | reset_integrator placeholder allows P behavior | PASS |

## 9. PASS / FAIL 汇总

| 指标 | 数值 |
|------|------|
| 测试总数 | 65 |
| PASS | 65 |
| FAIL | 0 |
| 通过率 | 100% |

## 10. Warning 汇总

| 阶段 | Warning 数 | 关键 Warning |
|------|-----------|-------------|
| xvlog | 0 | 无 |
| xelab | 0 | 无 |
| xsim | 0 | 无 |

注意：XSim 2020.1 的 warning 检查可能不如 Spyglass 或 Verilator 严格。以下风险（见第 11 节）在 XSim 中未被报告，但在更严格的 lint 工具中可能出现。

## 11. 静态审查结果

### 11.1 pi_controller.sv 审查（26 项）

| # | 检查项 | 结果 | 依据 |
|---|--------|------|------|
| 1 | `rstn_i` 低有效同步复位 | ✅ 通过 | `if (!rstn_i)` in always_ff, 低电平有效 |
| 2 | reset 优先级最高 | ✅ 通过 | if-else 链首项 |
| 3 | `enable_i=0` 输出安全零 | ✅ 通过 | `control_o <= '0` 及全部输出清零 |
| 4 | enable 优先于 hold | ✅ 通过 | `!enable_i` 在 `hold_i` 之前 |
| 5 | `hold_i=1` 完整保持状态 | ✅ 通过 | `control_o <= control_o` 等全部保持 |
| 6 | `pid_ce_i` 只作为 clock enable | ✅ 通过 | 在 always_ff 内条件更新 |
| 7 | 未生成新时钟 | ✅ 通过 | 只有 `posedge clk_i` |
| 8 | `error_i` 为 signed | ✅ 通过 | `input logic signed [13:0] error_i` |
| 9 | -8192 polarity 翻转安全 | ✅ 通过 | 15-bit signed `-(-8192)=+8192` 不溢出 |
| 10 | P 乘法位宽 31 bit | ✅ 通过 | `PRODUCT_WIDTH = 15+16 = 31` |
| 11 | `>>> KP_SHIFT` 保持 signed | ✅ 通过 | 算术右移保留符号位 |
| 12 | 扩展到 `ACC_WIDTH` 符号扩展 | ✅ 通过 | 31-bit signed → 48-bit signed 自动扩展 |
| 13 | offset 在 ACC_WIDTH 中符号扩展 | ✅ 通过 | `{{34{offset_i[13]}}, offset_i}` |
| 14 | output_limit 限制到 8191 | ⚠️ 风险 | `output_limit_i (unsigned) > OUT_POS_MAX (signed)` 混合比较，功能正确但生成 lint warning |
| 15 | 负限幅对称 | ✅ 通过 | `limit_neg_w = -limit_pos_w` |
| 16 | `output_limit_i=0` 行为正确 | ✅ 通过 | `limit_pos=0, limit_neg=-0=0`, 输出钳位为 0 |
| 17 | `control_o` 截取低 14 位安全 | ✅ 通过 | limiter 后截取, 限制值 ≤ 8191 |
| 18 | `p_term_o[31:0]` 截断 | ⚠️ 可接受 | 所有有效参数下 p_scaled_w 值在 32-bit signed 范围内；但若未来 KP_SHIFT=0 且 kp=32767, error=8192，p_scaled_w ≈ 2^28，仍安全 |
| 19 | `i_term_o` 固定为 0 | ✅ 通过 | `i_term_o <= 32'sd0` 明确赋值 |
| 20 | ki/reset_integrator/KI_SHIFT 占位处理 | ⚠️ 可接受 | XOR 到 `unused_inputs_w`, 但该 wire 本身可能被优化掉并产生额外 warning |
| 21 | `always_comb` 全部覆盖 | ✅ 通过 | if/else if/else 覆盖全部路径 |
| 22 | 不推断 latch | ✅ 通过 | always_comb 全覆盖 |
| 23 | signed/unsigned 比较 warning | ⚠️ 风险 | 第 14 行 `output_limit_i > OUT_POS_MAX` 是 unsigned vs signed 比较, 功能正确但势必产生综合/仿真 warning |
| 24 | 参数约束满足 | ⚠️ 可接受 | ACC_WIDTH≥PRODUCT_WIDTH(48≥31), ≥OUT_WIDTH(48≥14), OUT_WIDTH≤32(14≤32), KP_SHIFT≥0(12≥0) 均满足, 但缺少 `assert` 保护 |
| 25 | 综合可移植性 | ⚠️ 风险 | 无 vendor primitive; 仅使用 $signed(), >>>, 标准 always_comb/always_ff; 但 item 23 的 signed/unsigned 比较可能导致不同工具行为差异 |
| 26 | 不影响 v1 OUT1 路径 | ✅ 通过 | 独立模块, 未接 laser_lock_core.sv |

### 11.2 tb_pi_controller.sv 审查（30 项）

| # | 检查项 | 结果 | 依据 |
|---|--------|------|------|
| 1 | 低有效 reset 测试 | ✅ 通过 | `rstn_i=0` 后检查输出清零 |
| 2 | 输入在时钟边沿前稳定 | ✅ 通过 | `update_once` 在 negedge 驱动, posedge 采样 |
| 3 | `update_once` 只触发一次 | ✅ 通过 | `pid_ce_i=1` 恰好一个周期 |
| 4 | `expected_control` 位宽一致 | ✅ 通过 | 返回 `[13:0]` signed, 与 `control_o` 一致 |
| 5 | `expected_sat` 与 DUT limiter 一致 | ✅ 通过 | 使用相同限幅逻辑 |
| 6 | TB 与 DUT 共同错误 | ⚠️ 风险 | TB 的 `expected_control` 函数复制了 DUT 的计算逻辑；若 DUT 存在系统性逻辑错误（如错误的 offset 扩展），TB 无法检测 |
| 7 | 正 error 覆盖 | ✅ 通过 | error=100, kp=16 |
| 8 | 负 error 覆盖 | ✅ 通过 | error=-100, kp=16 |
| 9 | polarity 覆盖 | ✅ 通过 | polarity=1, error=-100 |
| 10 | 最大正数 8191 | ✅ 通过 | error=8191 |
| 11 | 最小负数 -8192 | ✅ 通过 | error=-8192 |
| 12 | 最小负数 polarity 翻转 | ✅ 通过 | error=-8192, polarity=1 |
| 13 | 正饱和 | ✅ 通过 | error=8191, kp=128, limit=200 |
| 14 | 负饱和 | ✅ 通过 | error=-8192, kp=128, limit=200 |
| 15 | limit=0 | ✅ 通过 | output_limit=0, control=0 |
| 16 | offset 正负 | ✅ 通过 | offset=+25, offset=-25 |
| 17 | hold 覆盖 | ✅ 通过 | hold=1 保持 control=200 |
| 18 | enable 与 hold 优先级 | ✅ 通过 | enable=0, hold=1 → control=0 |
| 19 | reset 优先级 | ✅ 通过 | rstn=0 覆盖 enable/hold/pid_ce |
| 20 | pid_ce=0 | ✅ 通过 | pid_ce=0 保持 control=0 |
| 21 | 连续 pid_ce | ✅ 通过 | 三次连续更新 |
| 22 | I 占位接口 | ✅ 通过 | ki 变化和 reset_integrator 占位测试 |
| 23 | `check_equal` 掩盖 X/Z | ✅ 通过 | 使用 `!==`（case inequality）可捕获 X/Z |
| 24 | 额外检查 `p_term_o` | ⚠️ 缺失 | `p_term_o` 仅在 reset 后被检查，未被独立验证计算正确性 |
| 25 | hold 时 `p_term_o` 和 `sat_o` | ⚠️ 缺失 | hold 时未检查 p_term_o 和 sat_o 的保持 |
| 26 | enable 后重新使能 | ⚠️ 缺失 | 未独立测试 disable→re-enable 的状态恢复行为 |
| 27 | output_limit > 8191 | ⚠️ 不可达 | 14-bit unsigned max=8191, 无法测试 >8191; DUT 内部 clamp 逻辑在 TB 的 14-bit limit 接口下无法触发 |
| 28 | 负 Kp | ⚠️ 缺失 | 所有测试 kp=16 或 128（正）, kp_i 是 signed 16-bit 但未测负值 |
| 29 | kp_i=0 | ⚠️ 缺失 | P 通道增益为 0 的情况未覆盖 |
| 30 | offset 单独饱和 | ⚠️ 缺失 | offset 单独导致饱和（error=0, offset 很大）未测试 |

### 11.3 缺失测试分类

#### 必须在 v2a-1 补充

| 测试 | 说明 |
|------|------|
| 负 Kp | `kp_i` 为 signed 16-bit，必须验证负增益下输出方向正确，且 polarity 与负 Kp 组合后行为可解释 |
| `kp_i=0` | 验证 P 通道增益为零时 `control_o=0`（无 offset）或仅反映 offset |
| `p_term_o` 独立检查 | `drive_and_check` 中调用 `check_equal` 时未独立验证 `p_term_o` 的计算正确性；当前只有 reset 后检查 |

#### 可以留到 v2a-2 补充

| 测试 | 说明 |
|------|------|
| hold 时 `p_term_o` / `sat_o` 保持 | hold 冻结后验证 debug 输出也保持 |
| enable disable→re-enable | 验证 disable 清零后重新使能的完整行为 |
| offset 单独饱和 | offset 值很大而 error=0 时是否饱和 |

#### 不需要测试

| 测试 | 说明 |
|------|------|
| `output_limit_i > 8191` | 14-bit 接口物理上无法输入 >8191，DUT 内部 clamp 是对未来 16-bit 接口的防御性代码 |

## 12. 发现的风险

### 风险 1：signed/unsigned 比较（必须修正）

```systemverilog
// pi_controller.sv line 69
assign limit_pos_w = (output_limit_i > OUT_POS_MAX)
```

`output_limit_i` 是 `logic [13:0]`（unsigned），`OUT_POS_MAX` 是 `logic signed [13:0]`（signed）。SystemVerilog 会将两者都当作 unsigned 比较，当前功能正确（因为 `OUT_POS_MAX=8191` 全为正），但 **所有 lint 工具都会报 warning**，且在不同工具间可能产生行为差异。

**建议修正**（待 v2a-2，当前阶段不可修改 RTL）：
```systemverilog
assign limit_pos_w = ($signed({1'b0, output_limit_i}) > OUT_POS_MAX)
```
或将 `output_limit_i` 改为 `logic signed [OUT_WIDTH-1:0]`。

### 风险 2：TB 与 DUT 共享计算逻辑（建议修正）

TB 的 `expected_control` 函数逐行复制了 DUT 的计算逻辑。如果存在逻辑级错误（例如 offset 符号扩展方式不正确），TB 会给出一致的错误期望值，导致 PASS 但不能证明正确。

**建议修正**（待 v2a-2）：至少对几个关键测试点用独立的手工计算验证期望值，或用 Python/MATLAB 生成参考值。

### 风险 3：`unused_inputs_w` 可能产生级联 warning（可接受）

```systemverilog
// pi_controller.sv line 116
assign unused_inputs_w = reset_integrator_i ^ ki_i[0] ^ (KI_SHIFT == 0);
```

`unused_inputs_w` 自身未被读取，综合工具可能报告 "unused wire" warning。

### 风险 4：`p_term_o[31:0]` 隐式截断（可接受）

```systemverilog
// pi_controller.sv line 105
p_term_o <= p_scaled_w[31:0];
```

`p_scaled_w` 是 48-bit signed，截取低 32-bit 赋予 32-bit 输出。当前所有有效参数下值均在 32-bit signed 范围内，但该截断未做保护。若未来参数空间扩展（如 KP_SHIFT=0 且 kp 超大），可能产生不可解释的 debug 值。

## 13. 尚未完成的内容

- I 通道积分器（v2a-2 目标）
- anti-windup（v2a-2 目标）
- 负 Kp 测试（待补）
- `kp_i=0` 测试（待补）
- `p_term_o` 独立计算验证（待补）
- Vivado 主工程集成（v2b 目标）
- 综合 / 实现 / bitstream（遥远将来）
- 上板验证（遥远将来）
- 激光闭环（遥远将来）

## 14. 是否允许进入 v2a-2

**有条件允许，需先完成指定修正。**

依据：
1. pi_controller.sv 核心 P 通道逻辑正确，65/65 测试通过；
2. 但存在 signed/unsigned 比较 warning（风险 1），应在进入 v2a-2 前修正；
3. TB 缺少负 Kp 和 `kp_i=0` 覆盖（必须补充），这些测试直接影响 v2a-2 I 通道的对齐验证；
4. TB 与 DUT 共享逻辑的风险（风险 2）在当前阶段可接受，但应在 v2a-2 至少补充手工验证；
5. I 通道占位正确（`i_term_o` 固定为 0、`ki_i` / `reset_integrator_i` 无效化），不会误导 v2a-2 开发。

修正清单（进入 v2a-2 前）：
1. **修正 pi_controller.sv line 69 的 signed/unsigned 比较**（将 `output_limit_i` 声明改为 signed 或显式转换）；
2. **补充 tb_pi_controller.sv 的负 Kp 测试**（至少一个测试点）；
3. **补充 tb_pi_controller.sv 的 `kp_i=0` 测试**（至少一个测试点）；
4. **补充 `p_term_o` 的独立计算检查**（至少一个测试点，对比手工计算值）；
5. **完成以上修正后重新运行 xvlog/xelab/xsim 并确认 0 FAIL**。

## 15. 当前绝对不能声称的结论

- ❌ "FPGA PI 已替代 D2-125"（P-only 是 v2a-1 独立仿真，未接顶层，未上板，无 I 通道）
- ❌ "FPGA PI 已经可以闭环锁定"（未接 OUT2，未接激光，无 I 通道）
- ❌ "FPGA PID 已完成"（只有 P，无 I，无 D）
- ❌ "OUT2 可以安全接入激光"（OUT2 未接任何东西，安全链未验证）
- ❌ "可以直接进入主工程综合"（仅独立仿真，未在 Vivado 工程中添加）
- ❌ "可以生成 bitstream"（未综合，未实现）
- ❌ "anti-windup 已完成"（v2a-1 不包含）

---

**报告生成时间**：2026-06-11
**审查工具**：XSim 2020.1 + 人工静态复审
**日志文件位置**：
- `E:\new\fpga_lock\v94\v0.94\xvlog.log`
- `E:\new\fpga_lock\v94\v0.94\xelab.log`
- `E:\new\fpga_lock\v94\v0.94\xsim.log`

---

## 16. 2026-06-11 最终修正与回归仿真

### 16.1 最终 RTL 修正

已修正 `pi_controller.sv` 中 `output_limit_i` 与最大正限幅值之间的 signed / unsigned 混合比较问题。

修正方式：

- 保持 `output_limit_i` 为 unsigned 非负幅度接口；
- 新增 `output_limit_ext_w`，将 `output_limit_i` 显式零扩展为 `OUT_WIDTH+1` 位 unsigned；
- 新增 `OUT_POS_MAX_EXT`，将最大正限幅值显式表示为同位宽 unsigned；
- 使用同位宽 unsigned 比较得到 `limit_clamped_w`；
- 再将 `limit_clamped_w` 零扩展到 `ACC_WIDTH`，生成 signed 正限幅；
- `limit_neg_w = -limit_pos_w`，继续保持对称输出范围 `-8191` 到 `+8191`。

本次未改变：

- `output_limit_i` 接口类型；
- P 通道计算；
- polarity 行为；
- offset 行为；
- reset / enable / hold / pid_ce 优先级；
- I 通道占位状态。

### 16.2 新增测试清单

在保留原有 65 项测试的基础上，新增 39 项检查，覆盖：

- `kp_i=0` 且 `offset_i=0`：`p_term_o=0`、`control_o=0`、`sat_o=0`；
- `kp_i=0` 且正 offset：输出仅由 offset 决定；
- `kp_i=0` 且 offset 超过 limit：输出仍受 `output_limit_i` 限制；
- 正 error 乘负 Kp：负 P 输出；
- 负 error 乘负 Kp：正 P 输出；
- polarity 与负 Kp 组合：符号和手算结果一致；
- 三个 `p_term_o` 手工固定点：
  - `error=16, kp=8, polarity=0 -> p_term_o=8`
  - `error=-16, kp=8, polarity=0 -> p_term_o=-8`
  - `error=-16, kp=8, polarity=1 -> p_term_o=8`
- hold 完整保持：`control_o`、`p_term_o`、`i_term_o`、`sat_o` 全部保持；
- disable 后重新 enable：不会恢复旧输出，按新输入重新计算；
- offset 单独造成正向 saturation；
- offset 单独造成负向 saturation。

### 16.3 最终工具结果

工作目录：

```text
E:\new\fpga_lock\v94\v0.94
```

只编译：

```text
rtl/pi_controller.sv
sim/tb_pi_controller.sv
```

命令：

```tcl
xvlog -sv rtl/pi_controller.sv sim/tb_pi_controller.sv
xelab tb_pi_controller -s tb_pi_controller_sim
xsim tb_pi_controller_sim -runall
```

日志路径：

- `E:\new\fpga_lock\v94\v0.94\xvlog.log`
- `E:\new\fpga_lock\v94\v0.94\xelab.log`
- `E:\new\fpga_lock\v94\v0.94\xsim.log`

结果：

| 阶段 | Error 数 | Warning 数 | 结果 |
|---|---:|---:|---|
| xvlog | 0 | 0 | PASS |
| xelab | 0 | 0 | PASS |
| xsim | 0 | 0 | PASS |

最终 testbench 汇总：

```text
tb_pi_controller summary: tests=104 pass=104 fail=0
```

### 16.4 最终结论

```text
v2a-1 CLOSED
```

该结论只表示：

```text
P-only 独立 RTL、首次仿真、Claude Code 集中审查、最终修正和 XSim 回归仿真已完成。
```

该结论不表示：

- FPGA PI 已完成；
- I 通道已完成；
- anti-windup 已完成；
- 主工程集成完成；
- 综合通过；
- bitstream 完成；
- FPGA 已替代 D2-125；
- 允许上板；
- 允许连接 OUT2 / D2-125 / 激光。
