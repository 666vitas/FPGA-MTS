# CLAUDE_REVIEW_2026-07-10 — CURRENT_MAIN_STRICT_REVIEW_AND_P_LOCK_AUTOLOCK_GATE

**审查类型**: 严格主线只读审查（第7号审查规则集）
**仓库**: 666vitas/FPGA-MTS, branch=main
**审查日期**: 2026-07-10（实际写入 2026-07-11）
**审查范围**: v3REG-0 / v3REG-1 / v3REG-2 全部候选，含 out2_lock_controller + custom_debug_capture
**审查结论**: P_LOCK 未达 Auto Lock Gate —— 存在两条 P0 文档矛盾必须先修复，exp/v3-aux 位流已生成但未被文档承认

---

## A. 本次实际读取的文件列表（按强制顺序）

| 序号 | 文件路径 | 状态 | 说明 |
|------|---------|------|------|
| 1 | `AI_REVIEW_README.md` | ✅ 已读 | Tier 0 入口，定义 PRIMARY_BRANCH=main |
| 2 | `version/AI_STRICT_REVIEW_ENTRY.md` | ✅ 已读 | 强约束审查规则（183行） |
| 3 | `version/CURRENT_REVIEW_MANIFEST.md` | ✅ 已读 | 当前审查清单（250行） |
| 4 | `version/STATUS.md` | ✅ 已读 | 完整项目历史（806行） |
| 5 | `v0.94/project/redpitaya.xpr` | ✅ 已读 | Vivado 工程，Part=xc7z010clg400-1, Vivado v2020.1 |
| 6 | `v0.94/rtl/red_pitaya_top.sv` | ✅ 已读 | 顶层文件，~650行 |
| 7 | `v0.94/rtl/custom_register_bank.sv` | ✅ 已读 | 寄存器组 + out2_lock_controller，539行 |
| 8 | `v0.94/rtl/ramp_generator.sv` | ✅ 已读 | TIMING_FIX_2 版本，168行 |
| 9 | `v0.94/rtl/laser_lock_core.sv` | ✅ 已读（前120行关键段） | OUTPUT_MODE=3, CONTROL_PATH_MODE=1 |
| 10 | `v0.94/rtl/mixer_core.sv` | ✅ 已读 | 混频器核心 |
| 11 | `v0.94/rtl/lpf_core.sv` | ✅ 已读 | 低通滤波器 |
| 12 | `v0.94/rtl/output_protect.sv` | ✅ 已读 | 输出保护 |
| 13 | `v0.94/rtl/pi_controller_seq.sv` | ✅ 已读（前60行关键段） | 15状态顺序PI（非当前OUT2驱动） |
| 14 | `v0.94/rtl/custom_debug_capture.sv` | ✅ 已读 | NEW，93行，4通道BRAM环缓冲 |

**额外验证（非强制读取，但用于交叉验证）**:

| 路径 | 验证内容 |
|------|---------|
| `v0.94/exp/v3-aux/impl_1/red_pitaya_top.bit` | ✅ 位流存在，2,083,850 bytes，2026-07-10 16:04 |
| `v0.94/exp/v3-aux/impl_1/red_pitaya_top.bit.bin` | ✅ 位流存在，2,083,744 bytes，2026-07-10 16:18 |
| `v0.94/exp/v3-aux/impl_1/red_pitaya_top_timing_summary_routed.rpt` | ✅ 时序报告存在，1,120,928 bytes |
| `v0.94/exp/v3-aux/synth_1/` | ✅ 综合输出存在，含 DCP |
| `v0.94/exp/v3-aux/impl_1/` | ✅ 实现输出存在，含 routed DCP |

**未读取的历史路径（正确排除）**: v-weifang, version-weifang, version/v1, version/v2, old, before — 均未作为当前结论依据。

---

## B. 当前主线结论

### B1. 项目阶段判定

**当前主线处于 v3REG-1/v3REG-2 候选阶段，但文档状态与实际工程状态存在两条 P0 级矛盾。**

- v3REG-0 SAFE/SCAN：✅ 已由用户上板验证（MAGIC=0x4D545330, VERSION=0x00030000, base=0x40600000）
- v3REG-1 HOLD / v3REG-2 P_LOCK / PI_LOCK：RTL/software 候选已存在于 main 分支
- 但关键歧义：文档声称"未运行 Vivado"，而 exp/v3-aux 目录包含完整的综合、实现和时序通过位流

### B2. RTL 架构已确认

```
OUT1/DAC A = laser_error（mixer + post-mixer LPF，用于误差观测）
OUT2/DAC B = selected_out2（由 out2_lock_controller 根据 MODE/ENABLE 决定）

MODE=0 SAFE:   selected_out2 = 0
MODE=1 SCAN:   selected_out2 = ramp_generator（三角波扫描）
MODE=2 HOLD:   selected_out2 = HOLD_VALUE 寄存器
MODE=3 P_LOCK: selected_out2 = out2_lock_controller 流水线输出（P-only）
MODE=4 PI_LOCK: selected_out2 = out2_lock_controller 流水线输出（退化为 P_LOCK，KI 未实现）

laser_lock_core.control_o（pi_controller_seq 输出）= 内部候选/历史路径，
    非当前 DAC B / OUT2 最终输出。
```

### B3. out2_lock_controller 6级流水线（125 MHz）

```
s0: 捕获 enable / mode / error / kp / polarity / lock_bias / lock_limit / correction_limit
s1: 极性处理（polarity=1 时对 error 取负），符号扩展
s2: 乘法 s1_signed_error × kp（14-bit × 14-bit → 28-bit）
s3: 右移 8 位（>> 8），产生 p_term
s4: 钳位 p_term 到 ±correction_limit_abs（LOCK_CORRECTION_LIMIT），设 correction_saturated 标志
s5: 求和 lock_bias + correction，钳位到 ±lock_limit（LOCK_LIMIT）
```

### B4. custom_debug_capture

- 4 通道 BRAM 环缓冲（DEPTH=4096, 14-bit 宽度）
- CH1=IN1/PD, CH2=IN2/REF, CH3=laser_error(OUT1), CH4=selected_out2(OUT2)
- 支持 decimation、可配置长度、read_index 随机访问
- 已实例化在 red_pitaya_top.sv 第 532-549 行

### B5. Vivado 时序结果（exp/v3-aux, 2026-07-10）

```
Design Timing Summary (routed):
  Setup:  0 Failing Endpoints, Worst Slack (WNS) = +0.111 ns
  Hold:   0 Failing Endpoints, Worst Slack (WHS) = +0.050 ns
  Pulse Width: 0 Failing Endpoints

最差路径：i_out2_lock_controller/control_o_reg[2]@SLICE_X29Y33
  逻辑延迟 4.307 ns + 布线延迟 3.489 ns = 7.796 ns（需求 8.000 ns）
  Slack = +0.111 ns（PASS，余量 1.4%）

位流已生成：red_pitaya_top.bit（2,083,850 bytes）和 red_pitaya_top.bit.bin（2,083,744 bytes）
```

### B6. P_LOCK Autolock Gate 结论

**P_LOCK 未达到 Autolock Gate 通过条件。** 理由如下：

1. 两条 P0 文档矛盾未解决（见 F 节）
2. STATUS.md 未承认 exp/v3-aux 位流存在 —— 项目状态自述与工程实际脱节
3. 安全边界歧义未澄清 —— 文档同时说"只接示波器"和"已接 PZT/Scan"
4. P_LOCK 默认参数安全（KP=0 → 输出=0），但缺少 HOLD → P_LOCK 过渡验证流程

**Autolock Gate 状态: NOT PASSED（需先修复文档矛盾，再明确下一步验证计划）**

---

## C. 已由 RTL 直接确认的事实

### C1. 顶层实例化确认（red_pitaya_top.sv）

1. `USE_LASER_LOCK_CORE = 1'b1`（第 ~81 行）—— 激光锁核已启用
2. `LASER_LOCK_OUTPUT_MODE = 3`（第 ~82 行）—— OUT1 为 mixer + post-mixer LPF
3. `LASER_LOCK_CONTROL_PATH_MODE = 1`（第 ~83 行）—— 控制路径选 pi_controller_seq
4. `custom_register_bank` 实例化存在，接 `sys[6]`（第 ~498 行）—— 寄存器通过 /dev/mem 访问
5. `ramp_generator` 实例化存在，enable 条件为 `custom_enable && (custom_mode == 32'd1)` —— 仅 MODE=1 激活
6. `out2_lock_controller` 实例化存在（第 564-582 行）—— 驱动 `selected_out2`
7. `custom_debug_capture` 实例化存在（第 532-549 行）—— 4 通道数据捕获
8. DAC A/OUT1 = `laser_error`，DAC B/OUT2 = `selected_out2` —— 路由未变

### C2. 寄存器组确认（custom_register_bank.sv）

**地址空间**: `sys[6]`，base = `0x40600000`，每个寄存器 4 bytes

**关键寄存器及其复位默认值**:

| 寄存器 | 地址偏移 | 位宽 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| MAGIC | 0x00 | 32 | 0x4D545330 | 预检查魔数 |
| VERSION | 0x04 | 32 | 0x00030000 | 版本号 |
| MODE | 0x08 | 32 | 0 (SAFE) | 接受值 1/2/3/4 |
| ENABLE | 0x0C | 32 | 0 | 禁用 |
| SCAN_OFFSET | 0x10 | 32 | 6962 | 扫描中心值 |
| SCAN_AMP | 0x14 | 32 | 410 | 扫描幅度 |
| SCAN_STEP | 0x18 | 32 | 1 | 扫描步长 |
| SCAN_UPDATE_DIV | 0x1C | 32 | 1524 | 更新分频 |
| OUT2_LIMIT | 0x20 | 32 | 8191 | 输出硬限制 |
| STATUS | 0x24 | 32 | RO | 状态只读 |
| OUT2_MONITOR | 0x28 | 32 | RO | OUT2 当前值 |
| HOLD_VALUE | 0x2C | 32 | 0 | HOLD 模式固定值 |
| KP | 0x30 | 32 | 0 | P 项系数（KP_SHIFT=8） |
| POLARITY | 0x34 | 32 | 0 | 误差极性（0=正，1=反） |
| LOCK_BIAS | 0x38 | 32 | 0 | 锁定偏置 |
| LOCK_LIMIT | 0x3C | 32 | 8191 | 锁定输出限幅 |
| ERROR_MONITOR | 0x44 | 32 | RO | 误差监控（v3REG-2 新增） |
| CONTROL_MONITOR | 0x48 | 32 | RO | 控制量监控（v3REG-2 新增） |
| KI | 0x4C | 32 | 0 | I 项系数（当前未使用） |
| INTEGRAL_RESET | 0x50 | 32 | 0 | 积分复位（当前未使用） |
| LOCK_CORRECTION_LIMIT | 0x54 | 32 | 128 | P-term 修正钳位 |
| CAPTURE_CTRL | 0x58 | 32 | 0 | 捕获控制（start 触发） |
| CAPTURE_STATUS | 0x5C | 32 | RO | 捕获状态（busy/done） |
| CAPTURE_DECIMATION | 0x60 | 32 | 1024 | 降采样因子 |
| CAPTURE_LENGTH | 0x64 | 32 | 2048 | 捕获长度 |
| CAPTURE_READ_INDEX | 0x68 | 32 | 0 | 读索引 |
| CAPTURE_DATA_CH1-4 | 0x6C-0x78 | 32 | RO | 4 通道波形数据 |

**MODE 寄存器行为**（custom_register_bank.sv）:

```systemverilog
unique case (bus.wdata)
    32'd1, 32'd2, 32'd3, 32'd4: mode_o <= bus.wdata;
    default: mode_o <= 32'd0;
endcase
```

MAGIC 预检查：写入前必须先写 `0x4D545330` 到 MAGIC 地址，否则后续寄存器写入被忽略。

**enabled_status_w 行为变化**:

```systemverilog
// 从 v3REG-0 的 "enable_o && (mode_o == 32'd1)"
// 变为 v3REG-2 的 "enable_o && (mode_o != 32'd0)"
assign enabled_status_w = enable_o && (mode_o != 32'd0);
```

比以前更宽松 —— 任何非 SAFE 模式且 enable=1 都在 STATUS 中显示为 "enabled"。

### C3. out2_lock_controller RTL 事实

1. **6 级流水线**（s0→s5）已确认，125 MHz 时钟
2. **KP_SHIFT = 8** 已确认 —— P-term = (polarity_error × kp) >> 8
3. **KI 完全未实现** —— 流水线不含积分路径，MODE=4 PI_LOCK 与 MODE=3 P_LOCK 行为完全相同
4. **修正限幅先于偏置求和** —— correction 先被钳位到 ±correction_limit，再与 lock_bias 求和
5. **最终输出钳位** —— 偏置+修正和后，钳位到 ±lock_limit
6. **流水线饱和标志** —— s4 级设 correction_saturated，最终输出复用此标志
7. **默认安全值** —— KP=0, lock_bias=0, correction_limit=128, lock_limit=8191 → 输出 = clamp(0 + 0, 8191) = 0
8. **最终输出多路选择**（组合逻辑，流水线后）:
   - MODE_SAFE (0) 或 !enable → control_o = 0
   - MODE_SCAN (1) → control_o = scan_i
   - MODE_HOLD (2) → control_o = hold_value_i
   - MODE_P_LOCK (3) 或 MODE_PI_LOCK (4) → control_o = s5 流水线输出

### C4. ramp_generator RTL 事实

1. **TIMING_FIX_2 版本** —— 候选计算与边界/方向提交分离到不同周期
2. **双重饱和保护** —— limit_clamp + DAC_POS_LIMIT/DAC_NEG_LIMIT 硬件钳位
3. **禁用行为** —— enable=0 → scan_o = SAFE_VALUE (0), pos_q = -amp_abs_w（预定位到负峰值）
4. **三角波参数** —— offset_q, amp_q, step_q, update_div_q 为局部寄存器，切断时序路径

### C5. custom_debug_capture RTL 事实

1. **DEPTH = 4096** —— 每个通道 4096 个 14-bit 样本
2. **降采样** —— decim_cnt 计数到 decimation-1 后采样并推进写指针
3. **捕获流程** —— start_i 触发 → busy=1 → 配置锁定 → 写指针复位 → 计数采样 → 写满 length-1 后 done=1
4. **读侧** —— mem[read_index_w] 的组合读出，4 通道同时
5. **通道分配** —— CH1=adc_dat[0](IN1/PD), CH2=adc_dat[1](IN2/REF), CH3=laser_error(OUT1), CH4=selected_out2(OUT2)

### C6. pi_controller_seq RTL 事实

1. **15 状态顺序 PI** —— S_IDLE → S_CAPTURE → S_LIMIT_PREP → S_P_MUL → S_P_SCALE_I_MUL → S_I_SCALE → S_FREEZE_PREP → S_FREEZE_DECIDE → S_I_CANDIDATE → S_I_CLAMP → S_I_COMMIT → S_SUM_PRE → S_SUM_FINAL → S_LIMIT_COMPARE → S_OUTPUT
2. **编译期参数** —— KP_DEFAULT/KI_DEFAULT 等为 parameter，非运行时来自 custom_register_bank
3. **不作为当前 OUT2 驱动** —— laser_lock_core.control_o 未连接到 DAC B
4. **保留作为候选路径** —— 代码存在但未接入 OUT2，属于历史实现而非当前主线功能

---

## D. 已由文档记录确认但尚未实验验证的事实

### D1. 上板验证状态

| 功能 | 文档状态 | RTL 存在 | Vivado | Bitstream | 烧录 | 示波器 | 完整验证 |
|------|---------|---------|--------|-----------|------|--------|---------|
| SAFE/SCAN (v3REG-0) | ✅ 已验证 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HOLD (v3REG-1) | ⚠️ 候选 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| P_LOCK (v3REG-2) | ⚠️ 候选 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| PI_LOCK (v3REG-2) | ⚠️ 候选 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| custom_debug_capture | ⚠️ 候选 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Auto Lock | ⚠️ candidate | N/A | ✅ | ✅ | ❌ | ❌ | ❌ |

### D2. exp/v3-aux Vivado 结果

文档（STATUS.md）声称：

> "本轮未运行 Vivado synthesis / implementation，未生成 bitstream，未烧录，未上板验证"

但实际 exp/v3-aux/impl_1/ 目录包含：
- 完整综合输出（synth_1/red_pitaya_top.dcp，2026-07-09）
- 完整实现输出（impl_1/ routed DCP，2026-07-10）
- 位流文件（red_pitaya_top.bit，2026-07-10 16:04）
- 时序通过（WNS=+0.111ns, TNS=0.000ns, 0 Failing）

**这是一条事实性矛盾，STATUS.md 的描述与实际工程产物不符。**

### D3. 源文件注册状态（redpitaya.xpr）

以下新增模块已在 Vivado 工程中注册：
- custom_register_bank.sv ✅（含 out2_lock_controller）
- ramp_generator.sv ✅
- mixer_core.sv ✅
- lpf_core.sv ✅
- output_protect.sv ✅
- pi_controller_seq.sv ✅
- custom_debug_capture.sv ✅
- tb_custom_debug_capture.sv ✅
- tb_out2_lock_controller.sv ✅
- tb_ramp_generator.sv ✅
- tb_custom_register_bank_basic.sv ✅

---

## E. 不能确认 / 仍有风险的事实

### E1. 【P0 风险】OUT2 安全边界矛盾 🔴

四个权威文档对 OUT2 连接方式存在直接矛盾：

| 文档 | 行号 | 内容 | 立场 |
|------|------|------|------|
| `AI_REVIEW_README.md` | ~第 9 行 | "只允许 OUT2 接示波器；禁止接 Scan/PZT" | **示波器 only** |
| `AI_STRICT_REVIEW_ENTRY.md` | 第 112 行 | "OUT2 当前已接 PZT / Scan，因此 P_LOCK 必须默认小 Kp" | **已接 PZT/Scan** |
| `AI_STRICT_REVIEW_ENTRY.md` | 第 125-128 行 | "本阶段只允许 OUT2 接示波器。禁止 OUT2 接 Scan/PZT。" | **示波器 only** |
| `CURRENT_REVIEW_MANIFEST.md` | 第 35 行 | "当前 OUT2 已接 PZT / Scan 做谱线扫描" | **已接 PZT/Scan** |
| `STATUS.md` | 第 15 行 | "OUT2 仍只允许接示波器；禁止接 PZT / Scan input" | **示波器 only** |

**这份矛盾带来的风险**：
- 如果 OUT2 确实已接 PZT，那么 MODE=3 P_LOCK 即使 KP=0 也可以通过 LOCK_BIAS 写入非零值而驱动 PZT，存在物理风险
- 如果 OUT2 确实只接示波器，那么"已接 PZT/Scan"的声明就是错误文档，会误导后续审查者
- 两种立场无法同时成立，**必须在任何 P_LOCK 测试之前解决**

### E2. 【P0 风险】STATUS.md 与实际工程产物矛盾 🔴

STATUS.md 2026-07-10 条目声称未运行 Vivado，但 exp/v3-aux 存在完整工程产物。这种脱节意味着：

1. 项目状态自述不可靠 —— 不知道哪些文件是"真实状态"、哪些是过时声明
2. 不知道 exp/v3-aux 位流是用户手动生成的还是自动流程生成的
3. 不知道这个位流是否已经烧录过（文档说未烧录，但位流文件存在）
4. 如果位流已被烧录，则上板行为可能与文档描述不符

### E3. 【中等风险】exp/v3-aux 与 redpitaya.xpr 的关系

redpitaya.xpr 的 DefaultLaunch Dir 已改为 "E:/new/fpga_lock/v94/v0.94/exp/v3-aux"，且所有新增源文件已注册。这意味着 exp/v3-aux 很可能是从当前 redpitaya.xpr 打开的 Vivado 项目中生成的，但文档未明确记录这一事实。

### E4. 【中等风险】仿真验证缺失

testbench 文件已注册在 Vivado 工程中（tb_custom_debug_capture.sv, tb_out2_lock_controller.sv, tb_ramp_generator.sv, tb_custom_register_bank_basic.sv），但文档中没有任何仿真通过记录。没有仿真通过的时序 PASS 位流只能证明"综合+布局布线无时序违例"，不能证明"功能正确"。

### E5. 【低风险】KP 参数格式不明确

KP 的数值格式在 RTL 中没有统一文档说明。从 KP_SHIFT = 8（>> 8）推断，KP 可能使用 Q8.6 或 Q0.14 格式，但缺少明确注释。上位机软件需要知道这个格式才能正确计算 P-term。

### E6. 【低风险】上位机软件未在审查范围内

本次审查未读取上位机软件代码（GUI/monitor/Auto Lock 逻辑）。文档描述 Auto Lock 是 "candidate"，但无 RTL 侧支持（Auto Lock 逻辑在上位机侧，不在 FPGA 内）。

---

## F. 发现的旧注释或旧文档污染

### F1. red_pitaya_top.sv 第 236 行——v3REG-0 时代注释

```systemverilog
// OUT2 is oscilloscope-only in this stage
```

这行注释来自 v3REG-0 阶段。当前主线已集成了 out2_lock_controller（支持 HOLD/P_LOCK/PI_LOCK），此注释不再准确反映当前设计意图。P_LOCK 模式下的 OUT2 设计目标应是驱动误差修正（最终接 PZT），而非仅示波器观察。建议标注版本阶段，或直接删除。

### F2. laser_lock_core.sv——v2B1 Shadow Control 注释

laser_lock_core.sv 中仍保留 v2B1 时代的 Shadow Control 注释。这些注释描述的是历史架构（pi_controller_seq 直接驱动 OUT2），与当前架构（out2_lock_controller 驱动 OUT2）不同。属于历史文档，不是 bug，但会误导不熟悉当前架构的读者。

### F3. PI_LOCK 模式的名称与实际行为不符

MODE=4 名为 PI_LOCK，但在 out2_lock_controller 中 KI 完全未使用 —— PI_LOCK 退化为 P_LOCK。名称与行为不一致。如果不打算恢复 KI，建议重命名为 MODE_EXTRA 或注明 "reserved, currently degenerated to P_LOCK"。

### F4. AI_STRICT_REVIEW_ENTRY.md 内部自相矛盾

同一文件（AI_STRICT_REVIEW_ENTRY.md）在 24 行内自相矛盾：
- 第 112 行："OUT2 当前已接 PZT / Scan"
- 第 125-128 行："本阶段只允许 OUT2 接示波器。禁止 OUT2 接 Scan/PZT。"

**这是最危险的一类文档错误** —— 它会让 AI 审查者同时看到两种相反的指令，无法确定应遵循哪一条。

---

## G. 禁止推进的动作

以下动作在当前状态下明确禁止：

### G1. 物理连接禁止

```text
❌ 禁止 OUT2 接 PZT / Scan（安全边界未澄清）
❌ 禁止 OUT2 接激光器电流调制
❌ 禁止 OUT2 接 D2-125 Servo Output
❌ 禁止 OUT2 接 D2-125 Aux Output
❌ 禁止 OUT2 与任何 D2-125 输出并联
```

### G2. 声明禁止

```text
❌ 禁止声称 FPGA 已经闭环锁定
❌ 禁止声称 FPGA 已经替代 D2-125
❌ 禁止声称 P_LOCK / PI_LOCK 已经上板验证
❌ 禁止声称 custom_debug_capture 已经工作
❌ 禁止声称 Auto Lock 已经实现
❌ 禁止声称 OUT2 可以接 PZT（文档矛盾未解决）
```

### G3. 工程操作禁止

```text
❌ 禁止修改 RTL（本次为只读审查）
❌ 禁止运行 Vivado synthesis / implementation（未获授权）
❌ 禁止生成新 bitstream（未获授权）
❌ 禁止烧录 bitstream（安全边界未澄清）
❌ 禁止恢复 KI / integral（用户明确指示）
❌ 禁止实现 CNN（用户明确指示）
❌ 禁止运行任何会修改仓库的操作
```

---

## H. 下一步最小安全动作

### H1: 立即动作 —— 修复 P0 文档矛盾（最高优先级）

用户必须在以下两个立场中选择一个，并统一所有文档：

**选项 A: OUT2 只接示波器**
- 修改 AI_STRICT_REVIEW_ENTRY.md 第 112 行，删除"OUT2 当前已接 PZT / Scan"
- 修改 CURRENT_REVIEW_MANIFEST.md 第 35 行，删除"当前 OUT2 已接 PZT / Scan 做谱线扫描"
- 保留第 125-128 行的示波器-only 安全边界
- P_LOCK 测试时 OUT2 只接示波器

**选项 B: OUT2 已接 PZT/Scan（需要安全评审）**
- 修改 AI_STRICT_REVIEW_ENTRY.md 第 125-128 行，更新安全边界
- 修改 AI_REVIEW_README.md 安全边界声明
- 修改 STATUS.md 安全边界声明
- 在 P_LOCK 测试前增加安全评审环节：确认 KP=0, lock_bias=0 默认值确实输出 0V

### H2: 修复 STATUS.md 与实际工程产物矛盾

更新 STATUS.md 2026-07-10 条目，承认 exp/v3-aux 存在以下内容：
- 综合已完成（2026-07-09）
- 实现已完成（2026-07-10）
- 时序通过（WNS=+0.111ns, TNS=0.000ns, 0 Failing Endpoints）
- 位流已生成（red_pitaya_top.bit, 2,083,850 bytes）
- 记录位流是否已烧录、烧录日期和上板结果

### H3: 确认 P_LOCK 默认参数安全性（阻塞下一步验证）

在烧录任何位流之前：
1. 在文档中记录 P_LOCK 默认安全值：KP=0 → P-term=0 → 输出=0（即使 enable=1, MODE=3）
2. 确认 LOCK_BIAS 也默认为 0
3. 确认 LOCK_CORRECTION_LIMIT=128 是合理的起始值
4. 制定 P_LOCK KP 逐步增加的测试方案（例如：KP=1 → KP=5 → KP=10，每步示波器验证后递增）

### H4: 运行仿真（强烈建议）

在烧录前运行已有的 testbench：
1. tb_out2_lock_controller.sv —— 验证 6 级流水线、极性处理、钳位行为
2. tb_custom_debug_capture.sv —— 验证捕获触发、降采样、环缓冲行为
3. tb_custom_register_bank_basic.sv —— 验证寄存器读写、MAGIC 预检查

仿真通过后再讨论烧录 —— 这是最低安全标准。

### H5: 烧录后验证序列（需用户授权后执行）

```text
1. 烧录 exp/v3-aux 位流
2. 读 MAGIC（0x40600000）= 应为 0x4D545330
3. 读 VERSION（0x40600004）= 应为 0x00030000
4. 读 MODE = 0 (SAFE)，读 ENABLE = 0，确认 OUT2 = 0V（示波器）
5. 设置 MODE=1 (SCAN), ENABLE=1，确认 OUT2 输出三角波（示波器）
6. 设置 MODE=2 (HOLD), HOLD_VALUE=1000，确认 OUT2 稳定在预期值（示波器）
7. 设置 MODE=3 (P_LOCK), KP=0, LOCK_BIAS=0，确认 OUT2 = 0V（安全默认值）
8. 以最小 KP 开始 P_LOCK 测试，每次递增后用示波器观察 OUT2 行为
```

---

## I. 下一 Codex 任务建议

建议给 Codex 的任务（不经过 Claude 审查，直接给 Codex 执行）：

### I1：文档一致性修复（纯文档任务，无风险）

```
任务: 修复四份文档中的 OUT2 连接状态矛盾
输入: AI_REVIEW_README.md, AI_STRICT_REVIEW_ENTRY.md, CURRENT_REVIEW_MANIFEST.md, STATUS.md
要求: 将 OUT2 连接状态统一为单一立场（示波器-only 或 PZT/Scan）
注意: 同时更新安全边界声明，确保没有内部自相矛盾
```

### I2：STATUS.md 更新（纯文档任务，无风险）

```
任务: 更新 STATUS.md 2026-07-10 条目
要求: 记录 exp/v3-aux Vivado 结果（综合/实现/时序/位流）
注意: 不添加任何 RTL 修改或其他新内容，只补记录已有工程产物
```

### I3：仿真运行（无硬件风险）

```
任务: 在 Vivado 中运行全部 4 个 testbench
要求: 收集仿真波形截图和通过/失败报告
注意: 不修改 RTL，只运行现有仿真
```

### I4：默认参数安全审计文档

```
任务: 编写 P_LOCK 默认参数安全审计
范围: KP=0, KI=0, LOCK_BIAS=0, LOCK_CORRECTION_LIMIT=128, LOCK_LIMIT=8191
要求: 逐项证明每个默认值在最坏情况下不会使 OUT2 输出非零值
```

---

## J. 最终建议

### 核心判断

**v3REG-2 P_LOCK/Auto Lock Gate 当前状态：BLOCKED（阻塞）**

阻塞原因不是 RTL 或 Vivado 问题（这两者的实际状态比文档描述的好），而是**项目文档自洽性崩塌**。当前 main 分支存在两条 P0 级别的文档矛盾，使得任何 AI 审查或新参与者都无法确定当前真实安全边界。

### 实际工程状态（比文档描述的要好）

RTL 集成完整，Vivado 综合/实现/时序已通过（WNS=+0.111ns），位流已生成。默认参数安全（KP=0 → 输出=0）。KI 未被恢复（符合用户要求）。

### 必须阻塞的 Gates

1. **Document Gate**: P0 文档矛盾未修复 → BLOCKED
2. **Simulation Gate**: 无仿真通过记录 → BLOCKED
3. **Safety Boundary Gate**: OUT2 连接状态未澄清 → BLOCKED
4. **Status Gate**: STATUS.md 与实际工程产物脱节 → BLOCKED

### 一旦上述 Gates 通过后的路径

```
修复文档矛盾 → 运行仿真 → 烧录验证 SAFE/SCAN/HOLD（示波器）→ 
KP=0 P_LOCK 空载验证 → 最小 KP 递增测试 → 
安全评审 → 讨论 PZT 接入
```

总预估：文档修复 1 天 + 仿真 1-2 天 + 烧录验证 1 天 = 3-4 天后可进入安全评审。

### 对下一任审查者的话

欢迎来到这个项目。如果你也是 AI 审查者，请注意：

1. **不要相信任何一份单独文档的"I/O 连接状态"声明** —— 目前四份文档有相反的描述
2. **exp/v3-aux/impl_1/ 中的位流是真实的** —— 不管 STATUS.md 怎么写的，它确实存在且时序通过
3. **RTL 代码是干净的** —— out2_lock_controller 和 custom_debug_capture 的设计合理，参数安全
4. **KI 确实没有恢复** —— 不用担心历史 Session 把积分项加回来
5. **当前唯一的安全操作是示波器观察** —— 无论文档怎么写的，OUT2 默认假设只接示波器

---

**审查结束。**

*审查人: Claude（2026-07-10 session, completed 2026-07-11）*
*审查规则集: AI_STRICT_REVIEW_ENTRY.md（version/AI_STRICT_REVIEW_ENTRY.md）*
*下一位审查者建议: 用户先修复 P0 文档矛盾后，再发起新一轮审查*
