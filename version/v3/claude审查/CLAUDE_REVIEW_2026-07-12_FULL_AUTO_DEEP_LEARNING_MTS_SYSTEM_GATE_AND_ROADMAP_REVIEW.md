# FULL_AUTO_DEEP_LEARNING_MTS_SYSTEM_GATE_AND_ROADMAP_REVIEW

**审查日期**: 2026-07-12
**审查类型**: 全自动深度学习 MTS 稳频系统 Gate 与路线图只读审查
**仓库**: 666vitas/FPGA-MTS, branch=main（本地 detached HEAD @ 21056e8）
**审查范围**: 从 RTL 到上位机到 Vivado 到实验记录的完整工程审查
**审查结论**: P0 文档冲突阻塞，v3LOCK-P0 位流未生成，PZT 基础稳频条件具备，深度学习路线清晰但须先通过基础锁定 Gate

---

## A. 审查元信息

| 项目 | 值 |
|------|-----|
| 当前 HEAD SHA | `21056e8c979fad823289971604e36524531337ec` |
| HEAD 提交信息 | `Update v94 project code documents and records` |
| 分支状态 | **detached HEAD**（无分支） |
| origin/main 对比 | **无法确认** — `git fetch origin main` 因代理 403 失败 |
| 未提交修改 | **大量存在**（.agents/skills/, guanfang-v0.94/, software/ 等），但 v0.94/rtl/ 无未提交修改 |
| Conflict marker | **P0 发现**: `version/AI_STRICT_REVIEW_ENTRY.md` 第 83-97 行存在未解决的 `<<<<<<< HEAD` / `=======` / `>>>>>>>` |
| 审查是否只读 | ✅ 是 |
| 是否修改代码 | ❌ 否 |
| 是否运行 Vivado | ❌ 否 |
| 输出报告路径 | `version/v3/claude审查/CLAUDE_REVIEW_2026-07-12_FULL_AUTO_DEEP_LEARNING_MTS_SYSTEM_GATE_AND_ROADMAP_REVIEW.md` |

### 未提交修改（仅列与项目主线相关的路径）

```
software/redpitaya_lock_host/config.yaml (modified)
software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_workflow.py (modified)
software/redpitaya_lock_host/redpitaya_lock_host/main.py (modified)
software/redpitaya_lock_host/redpitaya_lock_host/rp_client.py (modified)
software/redpitaya_lock_host/redpitaya_lock_host/waveform_plot.py (modified)
software/redpitaya_lock_host/redpitaya_lock_host/waveform_preview.py (modified)
software/redpitaya_lock_host/tests/test_custom_fpga_workflow.py (modified)
software/redpitaya_lock_host/tests/test_waveform_preview.py (modified)
docs/HOST_APP_INTEGRATION.md (modified)
```

v0.94/rtl/ 目录 **无未提交修改** —— RTL 代码是干净的。


## B. 本次实际读取的文件

按强制读取顺序逐一列出：

| 序号 | 文件路径 | 状态 | 关键内容 |
|------|---------|------|---------|
| 1 | `AI_REVIEW_README.md` | ✅ 已读 | 入口，PRIMARY_BRANCH=main，安全边界已更新为 PZT 基础稳频 |
| 2 | `version/AI_STRICT_REVIEW_ENTRY.md` | ✅ 已读（**含 P0 conflict**） | 审查规则，第 83-97 行有 git merge conflict |
| 3 | `version/CURRENT_REVIEW_MANIFEST.md` | ✅ 已读 | 审查清单，stage=PZT 基础稳频最小闭环 |
| 4 | `version/STATUS.md` | ✅ 已读（845行） | 完整项目历史，最新条目 2026-07-12 |
| 5 | `version/rules/00_DOCUMENT_LANGUAGE_AND_STYLE_RULES.md` | ✅ 已读 | 文档语言规则 |
| 6 | `v0.94/project/redpitaya.xpr` | ✅ 已读 | Part=xc7z010clg400-1, Vivado v2020.1, DefaultLaunchDir=v3-aux |
| 7 | `v0.94/rtl/red_pitaya_top.sv` | ✅ 已读（851行） | USE_LASER_LOCK_CORE=1, OUTPUT_MODE=3, CONTROL_PATH_MODE=1 |
| 8 | `v0.94/rtl/custom_register_bank.sv` | ✅ 已读（567行） | VERSION=0x00030001, out2_lock_controller 6级流水线 |
| 9 | `v0.94/rtl/ramp_generator.sv` | ✅ 已读（168行） | TIMING_FIX_2, 双重饱和保护 |
| 10 | `v0.94/rtl/error_setpoint_corrector.sv` | ✅ 已读（37行） | 1级流水线, laser_error - error_setpoint, 饱和到 ±8191 |
| 11 | `v0.94/rtl/custom_debug_capture.sv` | ✅ 已读（97行） | BRAM fix, 同步读, DEPTH=4096 |
| 12 | `v0.94/rtl/laser_lock_core.sv` | ✅ 已读 | OUTPUT_MODE=3, CONTROL_PATH_MODE=1 |
| 13 | `v0.94/rtl/mixer_core.sv` | ✅ 已读（63行） | 数字混频, SHIFT=13 |
| 14 | `v0.94/rtl/lpf_core.sv` | ✅ 已读（85行） | 一阶 IIR LPF, SHIFT=12 |
| 15 | `v0.94/rtl/output_protect.sv` | ✅ 已读（48行） | reset/disable 强制输出 0 |
| 16 | `v0.94/rtl/pi_controller_seq.sv` | ✅ 已读 | 15状态顺序 PI（非当前 OUT2 驱动源） |
| 17 | `v0.94/rtl/pi_controller.sv` | ✅ 已读（179行） | 组合 PI（历史参考，时序不过） |
| 18 | `software/redpitaya_lock_host/README.md` | ✅ 已读 | 两种模式：Official SCPI / Custom FPGA |
| 19 | `software/redpitaya_lock_host/docs/CUSTOM_FPGA_LOCK_WORKFLOW.md` | ✅ 已读 | SCAN->LOCK HERE->Apply Kp->SAFE 完整流程 |
| 20 | `software/redpitaya_lock_host/docs/USAGE.md` | ✅ 已读 | Mock/Real 模式使用说明 |
| 21 | `software/redpitaya_lock_host/docs/HARDWARE_TEST_SOP.md` | ✅ 已读 | PD 接入、PZT 连接、安全边界 SOP |
| 22 | `software/redpitaya_lock_host/docs/DEVELOPMENT_LOG.md` | ✅ 已读（192行） | 最近条目 2026-06-26 |
| 23 | `software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_backend.py` | ✅ 已读（495行） | VERSION=0x00030001, lock_here(), update_p_lock(), SAFE |
| 24 | `software/redpitaya_lock_host/redpitaya_lock_host/main_window.py` | ✅ 已读（1934行） | LOCK HERE / APPLY P / SAFE 按钮, 4通道波形 |
| 25 | `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py` | ✅ 已读（863行） | 嵌入式 REMOTE_HELPER, /dev/mem 读写 |
| 26 | `software/redpitaya_lock_host/tests/test_custom_fpga_backend.py` | ✅ 已读（268行） | 21 tests passed |
| 27 | `version/v3/DEVELOPMENT_LOG.md` | ✅ 已读 | 2026-07-12 最新状态: Vivado timing PASS |
| 28 | `v0.94/sim/tb_custom_register_bank_basic.sv` | ✅ 已读（366行） | CAPTURE_LOCK_POINT 测试通过 |
| 29 | `v0.94/sim/tb_out2_lock_controller.sv` | ✅ 已读（226行） | P_LOCK 全场景测试通过 |
| 30 | `v0.94/sim/tb_error_setpoint_corrector.sv` | ✅ 已读（75行） | 5 场景测试通过 |
| 31 | `v0.94/sim/tb_custom_debug_capture.sv` | ✅ 已读（133行） | BRAM 捕获测试通过 |
| 32 | Vivado 最新报告 | ✅ 已读 | exp/v3-auto, 2026-07-12 15:11, WNS=+0.031ns PASS |
| 33 | 最新实验日志 | ✅ 已读 | experiment_log_20260630_203915.md (v3REG-0 SAFE/SCAN only) |

**总共读取文件**: 33/33 ✅（所有文件均实际读取）

**正确排除的历史路径**: v-weifang, version-weifang, version/v1, version/v2, old, before — 均未作为当前结论依据。


## C. 当前主线结论

### C1. 当前项目阶段

**当前主线是 PZT 基础稳频最小闭环（v3LOCK-P0 候选），不是全自动深度学习锁定。**

```
完成度状态：
v3REG-0 SAFE/SCAN:          ✅ 上板验证完成（VERSION=0x00030000）
v3LOCK-P0 RTL 集成:         ✅ 完整（error_setpoint_corrector + out2_lock_controller + custom_debug_capture BRAM fix）
v3LOCK-P0 VERSION=0x00030001: ✅ RTL 已编码, software 已匹配
v3LOCK-P0 Vivado timing:    ✅ PASS (exp/v3-auto, WNS=+0.031ns, 2026-07-12 15:11)
v3LOCK-P0 仿真 (4 testbench): ✅ 全部通过
v3LOCK-P0 Python 测试:      ✅ 21 tests passed
v3LOCK-P0 bitstream:        ❌ 未生成
v3LOCK-P0 烧录:              ❌ 未执行
v3LOCK-P0 MAGIC/VERSION 读回: ❌ 未执行
v3LOCK-P0 SAFE/SCAN 回归:   ❌ 未执行
v3LOCK-P0 LOCK HERE 上板验证: ❌ 未执行
v3LOCK-P0 P-only 基础稳频:  ❌ 未执行
Auto Lock (确定性):          ❌ 未实现（代码候选在上位机侧）
深度学习识峰:                 ❌ 未实现
深度学习参数优化:             ❌ 未实现
全自动深度学习稳频:           ❌ 远期目标
```

### C2. 当前架构总览

```
外部 REF 4.6 MHz ──→ IN2 ──┐
                            ├──→ mixer_core ──→ lpf_core ──→ output_protect ──→ laser_error ──→ OUT1 (error observation)
外部 PD ──→ 模拟 BPF ──→ 模拟放大器 ──→ IN1 ──┘
                                                                                   │
                                                                    error_setpoint_corrector
                                                                                   │
                                                                              lock_error
                                                                                   │
                                     custom_register_bank ──→ out2_lock_controller ──→ selected_out2 ──→ OUT2 (PZT/Scan)
                                            │                         ↑
                                     ramp_generator ──→ scan_i ──────┘
                                            │
                                     custom_debug_capture ──→ CH1=IN1, CH2=IN2, CH3=laser_error, CH4=selected_out2

外部 EOM: RF signal generator 独立驱动（不占用 Red Pitaya DAC）
```

### C3. 关键数值总结

```
VERSION (RTL):        0x00030001
MAGIC (RTL):          0x4D545330
Base address:          0x40600000
MODE 接受值:           1 (SCAN), 2 (HOLD), 3 (P_LOCK), 4 (PI_LOCK→退化为P_LOCK)
KP_SHIFT:              8 (P-term = error × kp >> 8)
LOCK_CORRECTION_LIMIT 默认: 128 counts
LOCK_LIMIT 默认:       8191 counts
OUT2_LIMIT 默认:       8191 counts
DAC 硬件限幅:          ±8191 counts (≈ ±1V)
error_setpoint_corrector 流水线: 1 级
out2_lock_controller 流水线: 6 级（s0→s5）
custom_debug_capture DEPTH: 4096, 同步读 1 周期延迟, BRAM 推断
Vivado WNS (latest):   +0.031 ns (exp/v3-auto)
KI / integral:         未实现（MODE=4 PI_LOCK 退化为 P_LOCK）
```



## D. 当前验证等级矩阵

针对 28 项功能逐一填写 A/B/C/D 四种等级：

A = RTL 已实现
B = testbench / 软件测试已通过
C = Vivado synthesis / implementation / timing 已通过
D = bitstream / 烧录 / 寄存器读回 / 上板实验已通过

| # | 功能 | A (RTL) | B (test/sim) | C (Vivado) | D (上板) | 综合评级 |
|---|------|---------|-------------|-----------|---------|---------|
| 1 | mixer_core | ✅ | ✅ XSim | ✅ 2026-07-12 | ✅ v3REG-0 | ✅ 已验证 |
| 2 | lpf_core | ✅ | ✅ XSim | ✅ 2026-07-12 | ✅ v3REG-0 | ✅ 已验证 |
| 3 | output_protect | ✅ | 未独立测试 | ✅ 2026-07-12 | ✅ v3REG-0 | ✅ 已验证 |
| 4 | OUT1 laser_error | ✅ | 通过顶层 | ✅ 2026-07-12 | ✅ v3REG-0 示波器 | ✅ 已验证 |
| 5 | custom_register_bank | ✅ | ✅ tb pass | ✅ 2026-07-12 | ✅ v3REG-0 | ✅ 已验证 (v3REG-0) |
| 6 | SAFE | ✅ | ✅ tb pass | ✅ 2026-07-12 | ✅ v3REG-0 | ✅ 已验证 |
| 7 | SCAN | ✅ | ✅ tb pass | ✅ 2026-07-12 | ✅ v3REG-0 | ✅ 已验证 |
| 8 | ramp_generator | ✅ | ✅ tb pass | ✅ 2026-07-12 | ✅ v3REG-0 | ✅ 已验证 |
| 9 | HOLD | ✅ | ✅ XSim | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 10 | ERROR_SETPOINT | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 11 | LOCK_ERROR_MONITOR | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 12 | CAPTURE_LOCK_POINT | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 13 | LOCK_BIAS | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 14 | P_LOCK | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 15 | LOCK_CORRECTION_LIMIT | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 16 | LOCK_LIMIT | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 17 | polarity | ✅ | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 18 | Apply Kp | ✅(上位机) | ✅ 21 tests | N/A (纯上位机) | ❌ | ⚠️ v3LOCK-P0 候选 |
| 19 | custom_debug_capture | ✅ BRAM fix | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ v3LOCK-P0 候选 |
| 20 | GUI Capture Waveform | ✅ | ✅ 21 tests | N/A | ❌ | ⚠️ v3LOCK-P0 候选 |
| 21 | GUI LOCK HERE | ✅ | ✅ 21 tests | N/A | ❌ | ⚠️ v3LOCK-P0 候选 |
| 22 | GUI UNLOCK / SAFE | ✅ | ✅ 21 tests | N/A | ✅ v3REG-0 | ✅ 已验证 |
| 23 | ARM AUTO LOCK candidate | ✅(上位机) | 部分测试 | N/A | ❌ | ⚠️ candidate |
| 24 | PI_LOCK | ✅(退化为P_LOCK) | ✅ tb pass | ✅ 2026-07-12 | ❌ | ⚠️ = P_LOCK |
| 25 | Ki / integral | ❌ 未实现 | ❌ | ❌ | ❌ | ❌ 按用户要求不恢复 |
| 26 | 自动识峰 | ❌ 未实现 | ❌ | ❌ | ❌ | ❌ 远期 |
| 27 | 自动重锁 | ❌ 未实现 | ❌ | ❌ | ❌ | ❌ 远期 |
| 28 | 深度学习参数优化 | ❌ 未实现 | ❌ | ❌ | ❌ | ❌ 远期 |

**验证等级统计**:
- 完全验证（A+B+C+D 全部通过）: 8 项（#1-8）
- v3LOCK-P0 候选（A+B+C 通过，D 未通过）: 13 项（#9-20, #22, #24）
- 上位机候选（A+B 通过，未上板）: 2 项（#21, #23）
- 明确不实现: 1 项（#25 KI）
- 远期未实现: 3 项（#26-28）

**关键结论**: 不存在任何"A 未实现但声称已验证"的虚报。文档中标记为"等待验证"的项目确实未上板验证。项目验证等级自洽。


## E. 当前 RTL 直接确认

### E1. OUT1 路径（laser_error）

```
IN1 (adc_dat[0]) × IN2 (adc_dat[1])
  → mixer_core (SHIFT=13, 14-bit → 28-bit product → >>13 → 14-bit saturated)
  → lpf_core (一阶 IIR, SHIFT=12, 32-bit 累加器)
  → output_protect (reset/disable 强制输出 0)
  → laser_error (14-bit signed)
  → DAC A / OUT1

OUT1 = laser_error，用于误差观测，不直接驱动执行器。
```

### E2. OUT2 路径（selected_out2）

```
out2_lock_controller 根据 MODE/ENABLE 选择:
  MODE=0 SAFE:        selected_out2 = 0
  MODE=1 SCAN:        selected_out2 = ramp_generator 三角波
  MODE=2 HOLD:        selected_out2 = HOLD_VALUE 寄存器
  MODE=3 P_LOCK:      selected_out2 = out2_lock_controller 6级流水线输出
  MODE=4 PI_LOCK:     selected_out2 = out2_lock_controller 6级流水线输出 (完全等同于 P_LOCK，无积分)

→ selected_out2 (14-bit signed)
→ DAC B / OUT2
```

### E3. MODE 寄存器行为（custom_register_bank.sv 第 110-118 行）

```systemverilog
unique case (bus.wdata)
    32'd1, 32'd2, 32'd3, 32'd4: mode_o <= bus.wdata;  // SCAN, HOLD, P_LOCK, PI_LOCK
    default: mode_o <= 32'd0;                          // SAFE (任何其他值)
endcase
```

写入 0 或任何非 1/2/3/4 的值均回到 SAFE。MAGIC 预检查必须先通过：写入 `0x4D545330` 到地址 0x00。

### E4. 寄存器映射摘要（custom_register_bank.sv, base=0x40600000）

**控制寄存器 (R/W)**:
| 偏移 | 名称 | 默认值 | 位宽 |
|------|------|--------|------|
| 0x02 | MODE | 0 | 32→1/2/3/4 |
| 0x03 | ENABLE | 0 | 32 |
| 0x04 | SCAN_OFFSET | 6962 | 32→14 |
| 0x05 | SCAN_AMP | 410 | 32→14 |
| 0x06 | SCAN_STEP | 1 | 32→14 |
| 0x07 | SCAN_UPDATE_DIV | 1524 | 32 |
| 0x08 | OUT2_LIMIT | 8191 | 32→14 |
| 0x0B | HOLD_VALUE | 0 | 32→14 |
| 0x0C | KP | 0 | 32→14 |
| 0x0D | POLARITY | 0 | 32 |
| 0x0E | LOCK_BIAS | 0 | 32→14 |
| 0x0F | LOCK_LIMIT | 8191 | 32→14 |
| 0x12 | KI | 0 | 32→14 (未使用) |
| 0x13 | INTEGRAL_RESET | 0 | 32 (未使用) |
| 0x14 | LOCK_CORRECTION_LIMIT | 128 | 32→14 |
| 0x15 | ERROR_SETPOINT | 0 | 32→14 (v3LOCK-P0 新增) |

**只读寄存器 (RO)**:
| 偏移 | 名称 | 说明 |
|------|------|------|
| 0x00 | MAGIC | 0x4D545330 |
| 0x01 | VERSION | 0x00030001 |
| 0x09 | STATUS | bit0=enabled, bit1=saturated |
| 0x0A | OUT2_MONITOR | 当前 OUT2 值 |
| 0x10 | ERROR_MONITOR | 当前 laser_error |
| 0x11 | CONTROL_MONITOR | 当前 selected_out2 |
| 0x16 | LOCK_ERROR_MONITOR | lock_error = laser_error - error_setpoint (v3LOCK-P0 新增) |

**特殊寄存器**:
| 偏移 | 名称 | 行为 |
|------|------|------|
| 0x17 | CAPTURE_LOCK_POINT | 写 1 触发: 同拍捕获 error_setpoint_o <= error_monitor_i, lock_bias_o <= out2_monitor_i, KP=0, KI=0, integral_reset=1, mode=3(P_LOCK), enable=1 |

### E5. LOCK HERE 硬件行为（CAPTURE_LOCK_POINT）

确认在同一 `clk_i` 域中同时执行以下操作（custom_register_bank.sv 第 170-179 行）：

```
当 bus.wdata[0] == 1:
  1. error_setpoint_o <= error_monitor_i   // 捕获当前 laser_error 作为目标过零点
  2. lock_bias_o     <= out2_monitor_i     // 捕获当前 OUT2 电压作为偏置
  3. kp_o            <= 0                  // 清零 Kp
  4. ki_o            <= 0                  // 清零 KI
  5. integral_reset_o <= 1'b1              // 复位积分器
  6. mode_o          <= 32'd3              // 进入 P_LOCK
  7. enable_o        <= 1'b1               // 使能输出
```

**关键安全特性**:
- 捕获与切换在同一个 clk_i 周期完成 → ERROR_SETPOINT 和 LOCK_BIAS 对应同一物理位置
- Kp=0 保证捕获后输出 = LOCK_BIAS（无扰切换）
- 读 CAPTURE_LOCK_POINT 返回 0（写只寄存器）

### E6. error_setpoint_corrector

37 行新模块，1 级流水线:

```
diff_w = {error_i[13], error_i} - {setpoint_i[13], setpoint_i}  // 15-bit signed
if (diff_w > 8191)  lock_error_o = 14'sd8191;
else if (diff_w < -8191) lock_error_o = -14'sd8191;
else lock_error_o = diff_w[13:0];
```

P_LOCK 下游使用 `lock_error`（不是 `laser_error`），因此锁定是基于"偏离 ERROR_SETPOINT 多少"，而非"原始 mixer 输出多少"。

### E7. out2_lock_controller P_LOCK 流水线

6 级流水线（s0→s5），每级在 clk_i 寄存:

```
s0: latch enable/mode/error/kp/polarity/bias/limit/correction_limit
s1: polarity 处理 (error × (-1 if polarity==1 else 1)), sign-extend to 15-bit
s2: 乘法 s1_signed_error × kp (14×14→28-bit)
s3: >> 8 (KP_SHIFT), produce p_term
s4: clamp p_term to ±correction_limit_abs, set correction_saturated
s5: lock_bias + correction, then clamp to ±lock_limit
```

最终输出选择（组合逻辑在流水线后）:
```
SAFE 或 !enable → 0
SCAN → scan_i
HOLD → hold_value_i
P_LOCK / PI_LOCK → s5 clamped output
```

**确认**:
- KI 完全不参与流水线
- PI_LOCK 和 P_LOCK 走完全相同路径（第 540-541 行）
- correction 限幅先于 bias 叠加
- 最终输出限幅后于 bias+correction 叠加

### E8. SAFE 退出路径

三条独立路径确保 SAFE 可靠:
1. MODE 寄存器写 0（或非 1/2/3/4 值）→ out2_lock_controller 输出 0
2. ENABLE 寄存器写 0 → out2_lock_controller 输出 0
3. ramp_generator enable=0 → scan_o = SAFE_VALUE = 0

enabled_status_w = enable_o && (mode_o != 0) — 任何非 SAFE 模式且 enable=1 显示为 enabled。

### E9. custom_debug_capture BRAM 修复

```
四通道并行存储:
  (* ram_style = "block" *) logic [13:0] mem_ch1 [0:DEPTH-1];
  (* ram_style = "block" *) logic [13:0] mem_ch2 [0:DEPTH-1];
  (* ram_style = "block" *) logic [13:0] mem_ch3 [0:DEPTH-1];
  (* ram_style = "block" *) logic [13:0] mem_ch4 [0:DEPTH-1];

读路径: 同步读，1 clk_i 周期延迟（删除组合读路径）
写路径: decimation 降采样 → 四通道同时写入 write_index_q
```

### E10. 未实现的功能（RTL 确认）

- KI 积分器：未实现
- 自动识峰：未实现（上位机侧由用户手动点击波形选点）
- 自动重锁：未实现
- CNN/深度学习：未实现
- 双执行器：未实现
- 数字 I/Q 解调：未实现（当前使用实混频 mixer × REF）


## F. 当前上位机直接确认

### F1. SCAN 模式

```
GUI: SCAN 按钮 → custom_fpga_backend.py set_mode_scan()
  → SSH python3 -c → /dev/mem 写入 MODE=1, ENABLE=1
  → 预先检查 MAGIC=0x4D545330
```

### F2. Capture Waveform

```
GUI: Capture Waveform 按钮 → custom_fpga_backend.capture_waveform()
  → SSH → /dev/mem 写入 CAPTURE_DECIMATION, CAPTURE_LENGTH
  → 写入 CAPTURE_CTRL start=1
  → 轮询 CAPTURE_STATUS busy/done
  → 读取 CAPTURE_DATA_CH1-4 全部点
  → 返回四通道数据到 GUI 显示
```

### F3. LOCK HERE

```
GUI: LOCK HERE 按钮 → custom_fpga_backend.lock_here()
  → 确认: MODE=1 (SCAN), ENABLE=1, 无饱和
  → 写入 KP=0, KI=0, POLARITY, LOCK_CORRECTION_LIMIT, LOCK_LIMIT
  → 写入 CAPTURE_LOCK_POINT=1
  → 确认: MODE 读回 = 3 (P_LOCK)
  → 返回: captured ERROR_SETPOINT, LOCK_BIAS
```

### F4. Apply Kp

```
GUI: APPLY P 按钮 → custom_fpga_backend.update_p_lock(kp, polarity)
  → 确认: MAGIC 匹配, MODE=3, ENABLE=1, 无饱和
  → 写入 KP, POLARITY (只这两个)
  → 验证: ERROR_SETPOINT 和 LOCK_BIAS 未被修改
  → Kp 限制: 只能 0/4/8/16/32
  → polarity: Kp≠0 时拒绝翻转
  → 任何异常 → SAFE
```

### F5. SAFE

```
GUI: SAFE / UNLOCK / ABORT 按钮 → custom_fpga_backend.set_mode_safe()
  → SSH → /dev/mem 写入 ENABLE=0, MODE=0
  → 确认 MAGIC 匹配
```

### F6. 状态显示

```
GUI 周期性读取 STATUS, OUT2_MONITOR, ERROR_MONITOR, CONTROL_MONITOR
  显示 enabled, saturated, current OUT2, error, control 值
```

### F7. 数据保存和波形显示

```
四通道波形显示: CH1=IN1/PD, CH2=IN2/REF, CH3=OUT1/laser_error, CH4=OUT2/selected_out2
可点击波形选点: 点击 → 记录目标 OUT2 值 → LOCK HERE 使用
锁定标记: 紫色虚线
CH3/CH4 为自定义 FPGA scope 数据（硬件 capture，非软件模拟）
```



## G. 文档冲突和污染

### G1. 【P0】AI_STRICT_REVIEW_ENTRY.md Git Merge Conflict 🔴

**位置**: 第 83-97 行

```
83: <<<<<<< HEAD
84: 截至 2026-07-11，当前主线为：
85: ...
88: HOLD / P_LOCK / PI_LOCK / LOCK HERE 尚未完成最新 Vivado synthesis ...
90: =======
91: 截至 2026-07-12，当前主线为：
92: ...
96: OUT2 的目标执行器是激光器专用 PZT / Scan 输入...
97: >>>>>>> 0a6928a (Update v94 project code documents and records)
```

**影响**:
- AI 审查者读取此文件时会同时看到两个阶段的主线描述
- HEAD 版本说"HOLD/P_LOCK/PI_LOCK/LOCK HERE 尚未完成 Vivado"
- 0a6928a 版本说"PZT 基础稳频最小闭环"
- 两个版本对 VERSION 和验证阶段的描述不同
- 这会导致 AI 审查者无法确定当前真实状态

**严重性**: P0 — 任何依赖此文件的审查都会产生歧义

**需要的修复**: 只保留 0a6928a 版本（2026-07-12 最新），删除 HEAD 版本和 conflict marker

### G2. CURRENT_REVIEW_MANIFEST 与 STATUS.md 的验证级别不一致

**MANIFEST 第 200-210 行仍写**:
```
HOLD/P_LOCK/PI_LOCK 等待最新 Vivado synthesis
HOLD/P_LOCK/PI_LOCK 等待最新 implementation
HOLD/P_LOCK/PI_LOCK 等待最新 timing 检查
```

**STATUS.md 2026-07-11 条目和 exp/v3-auto 已证明**:
- synthesis 已完成
- implementation 已完成
- timing PASS (WNS=+0.031ns, TNS=0.000ns, 0 Failing Endpoints)
- custom_debug_capture, custom_register_bank, error_setpoint_corrector 均已在 implemented design 中

**正确区分**: timing 已通过 ≠ bitstream/上板闭环已通过。MANIFEST 应改为:
- HOLD/P_LOCK/PI_LOCK: timing 已通过 (2026-07-12 exp/v3-auto)
- HOLD/P_LOCK/PI_LOCK: 等待 bitstream 生成 / 烧录 / 上板验证

### G3. CURRENT_REVIEW_MANIFEST RTL 列表缺失

MANIFEST 第 53-65 行列出的 RTL 文件缺少:
- `error_setpoint_corrector.sv` — 已存在且实例化
- `custom_debug_capture.sv` — 已存在且实例化（BRAM fix 版）

需要添加到清单中。

### G4. 旧注释污染

#### red_pitaya_top.sv 第 236 行
```
// OUT2 is oscilloscope-only in this stage
```
这是 v3REG-0 时代的注释。当前 MAIN 已将 OUT2 定位为 PZT/Scan 执行器，此注释过时。

#### laser_lock_core.sv v2B1 Shadow Control 注释
仍保留历史架构注释（pi_controller_seq 直接驱动 OUT2）。当前架构是 out2_lock_controller 驱动 OUT2。历史文档，不致 bug，但误导新读者。

### G5. STATUS.md 内部过期段落

STATUS.md 第 70-89 行"当前主线"段落存在过期描述:
- 第 72 行: "HOLD/P_LOCK/PI_LOCK 尚未完成最新 Vivado synthesis / implementation / timing" — 已过时，2026-07-11/12 已完成
- 第 81 行: "KI / integral 当前不要恢复" — 正确
- 第 85 行: 仍引用 VERSION=0x00030000 — 当前 VERSION=0x00030001

### G6. 检测到的其他 Conflict Marker

除 AI_STRICT_REVIEW_ENTRY.md 外还检测到:
- `version/v2/D2_125_REAL_WIRING_AND_STATE_MODEL.md` 第 1 行和 321 行 — 在禁止引用路径中，不影响当前审查
- `version/v3/claude审查/CLAUDE_REVIEW_2026-07-05_*.md` 第 318-324 行 — 旧审查报告，不影响当前审查


## H. 当前 PZT 最小闭环安全审查

### H1. 闭环流程逐项 RTL 和上位机确认

| # | 检查项 | RTL | 上位机 | 仿真 | 安全 |
|---|--------|-----|--------|------|------|
| 1 | CAPTURE_LOCK_POINT 同拍捕获 ERROR_SETPOINT 和 LOCK_BIAS | ✅ 同一个 always_ff @(posedge clk_i) | ✅ lock_here() 写 CAPTURE_LOCK_POINT=1 | ✅ tb 测试通过 | ✅ |
| 2 | 捕获时 Kp=0, Ki=0, integral reset, mode→P_LOCK, enable=1 | ✅ 同一周期全执行 | ✅ 先写 KP=0/KI=0 再写 CAPTURE_LOCK_POINT | ✅ tb 测试通过 | ✅ |
| 3 | error_setpoint_corrector 算 lock_error = laser_error - error_setpoint | ✅ 1级流水线 | N/A | ✅ 5 场景通过 | ✅ |
| 4 | P_LOCK 使用 lock_error（非 laser_error） | ✅ 顶层连接确认 | N/A | ✅ tb_out2_lock_controller | ✅ |
| 5 | Kp=0 无扰保持 LOCK_BIAS | ✅ s2: error×0=0, s5: bias+0=bias | N/A | ✅ tb 测试通过 | ✅ |
| 6 | P correction 经 LOCK_CORRECTION_LIMIT | ✅ s4 级 clamp | ✅ lock_here() 先写 correction_limit | ✅ tb 测试通过 | ✅ |
| 7 | 最终输出经 LOCK_LIMIT/DAC limit | ✅ s5 级 clamp + output_protect | ✅ lock_here() 先写 lock_limit | ✅ tb 测试通过 | ✅ |
| 8 | polarity 可能选错 → 正反馈 | ⚠️ 需用户人工判断 | ✅ polarity=0/1 可选, Kp≠0 时拒绝翻转 | ✅ tb 测试通过 | ⚠️ 人工判定 |
| 9 | SAFE 无条件退出 | ✅ 三条独立路径 | ✅ 多个 SAFE/UNLOCK/ABORT 按钮 | N/A | ✅ |
| 10 | Apply Kp 只修改 Kp/polarity/limit | ✅ RTL 无状态依赖 | ✅ update_p_lock() 只写 KP/POLARITY | ✅ 21 tests confirm | ✅ |
| 11 | Apply Kp 不重新捕获 LOCK_BIAS | ✅ 不重新写 CAPTURE_LOCK_POINT | ✅ 验证 ERROR_SETPOINT/BIAS unchanged | ✅ 21 tests confirm | ✅ |
| 12 | GUI 不会重复捕获错误锁点 | N/A | ✅ LOCK HERE 和 APPLY P 是独立操作 | ✅ 21 tests confirm | ✅ |

### H2. 流水线延迟分析

| 信号路径 | 延迟 | 影响 |
|---------|------|------|
| laser_error → error_setpoint_corrector → lock_error | 1 clk_i (8 ns) | 可忽略 |
| lock_error → out2_lock_controller s0→s5 → selected_out2 | 6 clk_i (48 ns) | 可忽略 |
| CAPTURE_LOCK_POINT 写入 → 寄存器更新 | 1 clk_i (8 ns) | 同拍捕获，无不一致 |
| LOCK HERE total latency (error→correction→OUT2) | 8 clk_i (64 ns) | 远小于 125 MS/s 采样周期 |

**结论**: 不存在 ERROR_SETPOINT 和 LOCK_BIAS 不对应同一物理位置的问题。不存在 P_LOCK 切换后输出瞬态异常。所有关键捕获和切换在同一 clk_i 域完成。

### H3. 当前闭环安全性判断

**具备的条件**:
1. ✅ SAFE 三条独立路径可靠
2. ✅ Kp=0 默认输出 = LOCK_BIAS（等于 SCAN 时用户选中位置的 OUT2 电压）
3. ✅ LOCK_CORRECTION_LIMIT 默认 128 counts（≈15.6 mV）— 即使 Kp 非零也很难产生危险输出
4. ✅ LOCK_LIMIT 默认 8191 与 DAC 硬件限幅一致
5. ✅ Apply Kp 只允许 0/4/8/16/32（不允许大 Kp）
6. ✅ 饱和检测可触发 SAFE
7. ✅ 上位机任何异常自动 SAFE
8. ✅ 仿真覆盖了关键场景

**缺失的条件**:
1. ❌ 新 bitstream 未生成（exp/v3-auto 时序通过但未 run write_bitstream）
2. ❌ 新 bitstream 未烧录
3. ❌ MAGIC/VERSION=0x00030001 未上板读回
4. ❌ SAFE/SCAN 回归未做（新 RTL 上板后必须先验证）
5. ❌ PZT 物理连接前未做小幅度安全性确认
6. ❌ 没有 PZT 扫描时的示波器双通道验证（OUT2 + IN1 同时观察）

**结论**: 当前 RTL + software 在功能层面已具备进入 PZT 基础稳频的条件，但工程流程上还缺 bitstream 生成、烧录、SAFE/SCAN 回归三个步骤。这三个步骤必须在任何 PZT 连接前完成。


## I. 最终目标可行性

### I1. 总体判断

**基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统在工程上是可行的，但实现路径必须分层渐进，不能跳跃。**

### I2. 逐个问题回答

**1. 当前 Red Pitaya FPGA + ARM/Linux + Python GUI 架构是否能够支持最终目标？**

能。FPGA 做实时信号处理（mixer + LPF + lock control），ARM/Linux 做寄存器访问和控制逻辑，Python GUI 做人机交互和数据采集。深度学习推理可放在 PC 端（训练和第一版推理）或 ARM 端（轻量推理）。FPGA 放 CNN 在现阶段不必要。架构层次合理。

**2. 当前 mixer + LPF + register_bank + PZT control 是否是合理基础？**

是。这是最精简且最核心的信号链：PD 信号进入 ADC → 数字混频解调 → LPF 提取 error → PZT 反馈。这是任何稳频系统的最小完备路径。

**3. 当前最小人工 PZT 锁定是否必须先完成？**

是，而且这是不可跳过的 Gate。理由:
- 没有人工验证过的锁定，自动锁定的所有假设（过零点位置、polarity、Kp 范围）都没有实验依据
- 人工锁定过程本身就是数据采集：你会知道锁点在哪里、error 信号长什么样
- 锁不住可能是物理原因（PD SNR 太低、EOM 调制深度不够、PZT 行程不足），不是代码能解决的

**4. 是否应该先完成确定性的 Auto Lock，再加入深度学习？**

是。确定性 Auto Lock（扫描→找过零点→Kp=0 激活→小 Kp 递增→成功/失败→SAFE）不需要深度学习。确定性版本成功后，采集的数据才有意义。直接用深度学习做第一次锁定是本末倒置。

**5. 深度学习应该负责什么？**

- 识峰：从扫描波形中分类信号峰（MTS 色散信号 vs 噪声 vs 干涉条纹），推荐最适合锁定的峰
- 参数建议：建议初始 Kp、polarity、target peak 区间
- 异常检测：从锁定后的 error/control 波形中检测即将失锁的征兆
- 长期优化：根据历史锁定记录调整 scan 参数和 lock 参数

**6. 深度学习不应该直接负责什么？**

- 不应该直接输出 DAC 电压（必须经过 limit/clamp）
- 不应该绕过 SAFE
- 不应该做实时闭环控制（确定性 FSM 负责，深度学习只做建议）
- 不应该在没有人工验证的情况下自动替换锁点
- 第一阶段不应该负责 PZT 压电非线性的实时补偿

**7. 模型训练应该运行在 PC、ARM 还是 FPGA？**

PC。理由:
- 训练需要 GPU（即使是 CNN 小模型）、大量数据迭代、超参搜索
- Red Pitaya ARM 是双核 Cortex-A9，远不够训练
- FPGA 训练 CNN 不现实

**8. 第一版在线推理应该运行在哪里？**

PC（通过 SSH/网络传数据到 GUI，PC 端跑 PyTorch/TensorFlow Lite 推理，结果传给 GUI 显示，用户确认后由确定性 FSM 执行锁定）。ARM 端推理可以在第二版做（模型量化后部署到 ARM），但不是第一版。

**9. 当前是否没有必要把 CNN 放入 FPGA？**

完全没必要。理由:
- FPGA 资源有限（Zynq-7010, LUT 35.86% 已用）
- CNN 推理在 PC 端延时远小于人工操作延时
- FPGA CNN 的开发、验证、调试成本极高
- 只有在需求是"不需要 PC 的全自动嵌入式锁定"时，FPGA CNN 才有意义

**10. 当前项目最大的技术风险是什么？**

PD SNR 不足。如果 PD 信号经过模拟 BPF 和放大器后进入 IN1 的 SNR 不足以让 mixer+LPF 提取出清晰的 MTS 色散信号，那么锁定就没有可靠的 error 来源。这个问题不解决，后面所有数字处理都没意义。必须在量化 SNR 后再推进。

**11. 最大实验风险是什么？**

PZT 电压超出激光器可接受范围。Red Pitaya OUT2 输出 ±1V，如果激光器 PZT 输入只接受 0-5V，需要外部电平转换。另外，激光器在 PZT 扫描时的跳模风险也存在。必须在了解激光器 PZT 输入规格后再连接。

**12. 最大 AI-assisted development 风险是什么？**

模型在有限数据上过拟合，在实际操作中推荐错误锁点或参数。缓解措施：模型只做建议，确定性 FSM 做执行；任何异常触发 SAFE；人工始终可以覆盖模型建议。

**13. 最终目标的论文创新点可以是什么？**

- 用数字混频 + LPF 替代模拟 lock-in amplifier 的一部分功能（不是全部替代，而是数字辅助）
- 深度学习辅助的 MTS 谱线自动识峰和锁点推荐
- 基于历史锁定数据的参数在线优化
- Red Pitaya 开源 FPGA + ARM + Python 全栈激光稳频平台
- 从人工锁定到确定性自动锁定再到深度学习辅助的渐进迁移方法论

**14. 哪些功能属于毕业/论文最小成果？**

- FPGA 数字 mixer+LPF 产生 MTS error 信号
- OUT2 PZT P-only 基础稳频
- 确定性 Auto Lock（扫描→识峰→锁定，不使用深度学习）
- 与 D2-125 的锁定性能对照
- (可选但加分) 深度学习辅助识峰

**15. 哪些功能属于远期增强，不应阻塞当前实验？**

- FPGA CNN 推理
- 数字 I/Q 解调和相位优化
- 替代模拟 BPF 和前置放大器
- 双执行器（PZT + 电流快反馈）
- 全自动深度学习闭环调参
- 替代 D2-125（这是论文结论，不是实验前提）


## J. 深度学习功能边界

### J1. 第一层：确定性自动化（不使用深度学习）

这些是纯规则/FSM逻辑，不需要任何学习:

```
自动扫描 (SCAN → 读波形 → 检测信号存在)
过零点候选检测 (lock_error 符号翻转点)
峰序号/斜率判断 (按 amplitude 排序)
写入 LOCK_BIAS (当前 OUT2 值)
写入 ERROR_SETPOINT (当前 laser_error 值)
polarity 检查 (小 Kp 试探)
Kp 小步增加 (0/4/8/16/32)
saturation 检查
error RMS 检查
失败 → SAFE → RESCAN
成功 → 持续监控
```

### J2. 第二层：深度学习识峰

**模型输入**:
- 当前扫描谱线 (CH3 laser_error vs CH4 OUT2, ~2000 点)
- 可选 PD 信号 (CH1)
- 扫描参数 (offset, amplitude, frequency)
- 历史锁定标签

**模型输出**:
- 目标峰类别 (MTS 色散过零点 / 噪声 / 干涉条纹)
- 峰置信度 (0-1)
- 目标锁点区间 (OUT2 counts 范围)
- 是否适合锁定 (binary)
- 建议 Vlock / capture window

**模型类型建议**: 
- 第一版: 1D CNN / ResNet 处理谱线 (2000×1 输入)
- 或用传统方法先做峰检测，CNN 只做分类

**训练数据需求**: 至少 50-100 条标注扫描波形，涵盖:
- 不同激光器工作点
- 不同扫描参数
- 不同 SNR
- 有信号和无信号的情况

### J3. 第三层：参数优化

**可优化参数及分类**:

| 参数 | 可由模型建议 | 须经安全边界裁剪 | 只能由 FSM 执行 | 当前不优化 |
|------|-------------|-----------------|----------------|-----------|
| scan offset | ✅ | ✅ 限幅 | ❌ | |
| scan amplitude | ✅ | ✅ 限幅 | ❌ | |
| scan frequency | ✅ | ✅ 限最大值 | ❌ | |
| target peak | ✅ 推荐 | | ❌ 人工确认 | |
| ERROR_SETPOINT | ✅ 推荐 | | ✅ FSM 捕获 | |
| polarity | ✅ 推荐 | | ✅ FSM 试探 | |
| Kp | ✅ 推荐 | ✅ 0/4/8/16/32/64 | ✅ FSM 递增 | |
| Ki | ✅ | ✅ 极小 | ✅ | ⚠️ 先不恢复 |
| LOCK_CORRECTION_LIMIT | ✅ 推荐 | ✅ 上限 | ✅ FSM 设置 | |
| LOCK_LIMIT | ✅ 推荐 | ✅ 上限 | ✅ FSM 设置 | |
| capture decimation | ✅ 推荐 | | ✅ FSM 设置 | |
| capture length | ✅ 推荐 | | ✅ FSM 设置 | |

**优化目标（不只 "锁得好"）**:

| 指标 | 定义 | 阶段 |
|------|------|------|
| lock_error RMS | 锁定期间 lock_error 的 RMS 值 | 阶段 8+ |
| lock_error mean | 锁定期间 lock_error 的均值 | 阶段 8+ |
| control RMS | OUT2 控制量的 RMS | 阶段 8+ |
| saturation duty | correction_saturated 的时间比例 | 阶段 8+ |
| correction-limit hit rate | 触及 LOCK_CORRECTION_LIMIT 的频率 | 阶段 8+ |
| lock duration | 连续锁定时间 | 阶段 8+ |
| reacquisition time | 失锁后重新锁定的时间 | 阶段 10+ |
| 失锁率 | 每小时失锁次数 | 阶段 10+ |
| 重新扫描次数 | 锁定失败后重新 SCAN 的次数 | 阶段 10+ |
| 长时间漂移 | 锁点位置随时间漂移 | 阶段 19 |
| Allan deviation | 频率稳定度 | 阶段 19 (独立测量) |

**禁止模型做的事**:
- ❌ 绕过 SAFE
- ❌ 绕过 limit / correction_limit
- ❌ 直接输出任意 DAC 电压
- ❌ 在不满足 MAGIC 预检查时写寄存器
- ❌ 在用户未确认时自动修改锁点


## K. 数据集和评价指标

### K1. CSV 应记录的元数据（深度学习数据集的字段建议）

**实验标识**:
- timestamp
- bitstream VERSION
- git commit SHA

**扫描配置**:
- MODE (1=SCAN)
- ENABLE
- SCAN_OFFSET
- SCAN_AMP
- SCAN_UPDATE_DIV (用于计算扫描频率)
- OUT2_LIMIT

**锁定配置**:
- LOCK_BIAS
- ERROR_SETPOINT
- KP
- KI
- POLARITY
- LOCK_CORRECTION_LIMIT
- LOCK_LIMIT

**运行时数据**:
- ERROR_MONITOR (采样)
- LOCK_ERROR_MONITOR (采样)
- CONTROL_MONITOR (采样)
- saturation flag
- CH1 (IN1/PD, 完整波形)
- CH2 (IN2/REF, 完整波形)
- CH3 (laser_error/OUT1, 完整波形)
- CH4 (selected_out2/OUT2, 完整波形)

**标注信息**:
- 用户选择的目标峰标签 (peak_id)
- 是否锁定成功 (binary)
- 锁定持续时间 (seconds)
- 失败原因 (saturation / drift / manual_abort / communication_error / other)
- SAFE 原因

### K2. 训练数据标注要求

每一条训练样本应该是:
- 一条完整的扫描波形 (CH3 vs CH4, 或 CH1 vs time)
- 人工标注: 哪些过零点是 MTS 色散信号、哪些是噪声
- 标注峰的位置 (OUT2 counts) 和宽度 (counts 窗口)
- 标注结果: 是否适合锁定

### K3. 模型评价指标

- 识峰准确率 (precision/recall on peak detection)
- 峰分类准确率 (MTS vs noise)
- 推荐的锁点在实际锁定中的成功率
- 推荐的 Kp 在锁定后的 error RMS


## L. D2-125 与模拟链路替代路线

### L1. 判断替代顺序

当前建议顺序是正确的:

```
1. 保留现有模拟 BPF 和前置放大 ✅
2. 保留外部 EOM / 4.6 MHz RF 源 ✅
3. 先用 FPGA mixer + LPF 产生 error ✅
4. 先完成 OUT2 PZT P-only 基础锁定 ✅
5. 再比较 FPGA 与 D2-125 ← 当前不需要
6. 再恢复 PI / Ki ← 当前不应该
7. 达到稳定锁定后再讨论替代 D2-125
8. 再加入数字 I/Q、相位匹配
9. 再评估数字 BPF
10. 只有 raw PD ADC SNR 足够，才考虑去掉模拟 BPF / ZFL
11. EOM 驱动链路最后单独评估
```

### L2. 逐项明确回答

**当前是否应该替代 D2-125？**
不应该。没有任何上板锁定验证数据，没有锁定性能对照。替代 D2-125 是论文结论，不是实验前提。当前任务是用 FPGA 独立锁住激光，D2-125 作为对照和备份。

**当前是否应该替代模拟 BPF？**
不应该。模拟 BPF 滤除宽带噪声，提高进入 ADC 的 SNR。去掉 BPF 会让数字混频输入端的 SNR 大幅下降。只有量化了 raw PD ADC SNR 并确认足够后，才能讨论。

**当前是否应该去掉前置放大？**
不应该。同理，前置放大器把 PD 信号提升到 ADC 有效量程。直接进 ADC 可能只有几 mV 的信号，14-bit ADC 只有几个 LSB 的有效位。

**当前是否应该做双执行器？**
不应该。单执行器（PZT）基础稳频还没完成。双执行器增加了耦合和不稳定性，现在做是制造问题而不是解决问题。

**当前是否应该做电流反馈？**
不应该。电流反馈带宽高但 authority 小，适合补偿快速扰动。当前先把慢速大范围的 PZT 锁定做好。

**当前是否应该让 Red Pitaya 直接驱动 EOM？**
不应该。EOM 驱动需要特定的 RF 功率和频率（~4.6 MHz），Red Pitaya DAC 带宽和输出功率都不够。保留外部 RF signal generator。


## M. P0 / P1 / P2 / P3

### P0: 不修不能继续

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| P0-1 | AI_STRICT_REVIEW_ENTRY.md git merge conflict | 第 83-97 行 | AI 审查同时看到两个阶段描述 |
| P0-2 | git fetch 失败，无法确认 HEAD == origin/main | 整个仓库 | 不能确认审查的是 GitHub main 最新 |
| P0-3 | v3LOCK-P0 bitstream 未生成 | exp/v3-auto | 没有可烧录的位流 |
| P0-4 | v3LOCK-P0 未烧录/未验证 MAGIC/VERSION | 上板 | 无法确认 RTL 已正确加载到 FPGA |

### P1: 上板基础锁定前必须修

| # | 问题 | 位置 |
|---|------|------|
| P1-1 | CURRENT_REVIEW_MANIFEST 仍写"等待 Vivado timing" | MANIFEST 第 200-205 行 |
| P1-2 | CURRENT_REVIEW_MANIFEST RTL 清单缺少 error_setpoint_corrector.sv 和 custom_debug_capture.sv | MANIFEST 第 55-65 行 |
| P1-3 | STATUS.md "当前主线"段落过期（仍引用 0x00030000 和 "未完成 Vivado"） | STATUS.md 第 70-89 行 |
| P1-4 | red_pitaya_top.sv 第 236 行 "OUT2 is oscilloscope-only in this stage" 过时注释 | RTL |
| P1-5 | SAFE/SCAN 回归未在新 bitstream 上执行 | 上板 |

### P2: 基础锁定后修

| # | 问题 |
|---|------|
| P2-1 | 自动识峰规则未实现 |
| P2-2 | 确定性 Auto Lock FSM 未在上位机实现 |
| P2-3 | 失锁检测和自动 RESCAN 未实现 |
| P2-4 | 长时间锁定数据采集和 CSV 标注流程 |
| P2-5 | GUI 参数优化页面 |
| P2-6 | 训练数据自动标注工具 |

### P3: 远期

| # | 问题 |
|---|------|
| P3-1 | FPGA CNN 推理 |
| P3-2 | 双执行器（PZT + 电流反馈） |
| P3-3 | 替代模拟 BPF / 前置放大器 |
| P3-4 | 替代 D2-125 |
| P3-5 | 数字 I/Q 解调 |
| P3-6 | EOM 数字驱动 |
| P3-7 | Allan deviation 完整测量 |


## N. 后续阶段路线

### 阶段 0: 清理当前主线文档冲突 ← 当前唯一下一步

- **目标**: 修复 P0-1 文档 git merge conflict
- **已有基础**: 两个版本的内容都清晰，只需保留最新版本
- **缺失内容**: 无
- **输入**: AI_STRICT_REVIEW_ENTRY.md
- **操作**: 删除 conflict marker，保留 0a6928a 版本
- **输出**: 干净的 AI_STRICT_REVIEW_ENTRY.md
- **通过标准**: grep 不再检测到 <<<<<<< / ======= / >>>>>>>
- **失败回退**: git checkout 原文件
- **需要修改 RTL**: ❌
- **需要 Vivado**: ❌
- **需要新 bitstream**: ❌
- **需要实验室**: ❌
- **用户负责**: 确认修改
- **Codex 负责**: 执行文档修复
- **Claude 负责**: 审查修复结果
- **ChatGPT 负责**: 无

### 阶段 1: 生成并确认 v3LOCK-P0 bitstream

- **目标**: exp/v3-auto 运行 write_bitstream 生成 .bit 和 .bit.bin
- **已有基础**: synthesis ✅, implementation ✅, timing PASS ✅ (WNS=+0.031ns)
- **缺失内容**: 用户手动在 Vivado 运行 Generate Bitstream
- **通过标准**: red_pitaya_top.bit 和 .bit.bin 生成
- **失败回退**: 如 bitgen 失败，检查 DRC 和约束
- **需要修改 RTL**: ❌
- **需要 Vivado**: ✅ (仅 Generate Bitstream)
- **需要新 bitstream**: ✅
- **用户负责**: 在 Vivado 中运行 Generate Bitstream
- **Codex 负责**: 提供生成指令

### 阶段 2: 烧录并读取 MAGIC / VERSION=0x00030001

- **目标**: 烧录 v3LOCK-P0 bitstream，读回 MAGIC 和 VERSION
- **通过标准**: MAGIC=0x4D545330, VERSION=0x00030001
- **失败回退**: 如 VERSION=0x00030000，确认 bitstream 版本
- **需要 Vivado**: ❌ (烧录用 Vivado/Vivado Lab 或 Red Pitaya 工具)
- **用户负责**: 烧录 bitstream, SSH 连接, 运行 probe
- **Codex 负责**: 验证脚本

### 阶段 3: SAFE/SCAN 回归

- **目标**: 确认新 bitstream 上 SAFE 和 SCAN 行为与 v3REG-0 一致
- **通过标准**: MODE=0 OUT2=0V, MODE=1 OUT2=三角波, GUI 可控制 offset/amp/limit
- **需要实验室**: ✅ (Red Pitaya + 示波器)
- **用户负责**: 连接示波器、验证波形

### 阶段 4: custom_debug_capture 上板验证

- **目标**: 确认 BRAM 修复后 capture 功能正常
- **通过标准**: GUI 显示四通道真实波形（CH1-4 非全零）
- **需要实验室**: ✅

### 阶段 5: LOCK HERE, Kp=0 无扰切换

- **目标**: SCAN → 点击波形 → LOCK HERE → OUT2 输出 = 点击时的 OUT2 值
- **通过标准**: 示波器观察到 OUT2 在 LOCK HERE 后电压与点击位置一致
- **需要实验室**: ✅

### 阶段 6: P-only 小 Kp 基础稳频

- **目标**: Kp=0 → 4 → 8 → 16 → 32，观察 lock_error 减小
- **通过标准**: lock_error RMS 随 Kp 增加而减小
- **需要实验室**: ✅ (激光器 + PZT + PD + EOM + 4.6 MHz REF)

### 阶段 7: polarity、limit、correction limit 标定

- **目标**: 确定正确 polarity，标定合理的 correction_limit
- **通过标准**: polarity 不对时 error 增大，对时 error 减小；correction_limit 不常触发 saturation
- **需要实验室**: ✅

### 阶段 8: 基础锁定与 D2-125 对照

- **目标**: 长时间 (>10分钟) 保持 P-only 锁定，与 D2-125 对照
- **通过标准**: lock_error RMS 可比于或优于 D2-125
- **需要实验室**: ✅

### 阶段 9: 确定性 Auto Lock（不使用 CNN）

- **目标**: 上位机实现自动扫描 → 找过零点 → 选最佳候选 → Kp=0 → 递增 Kp → 成功/失败
- **缺失内容**: 上位机侧锁定 FSM、过零点检测算法、峰选择逻辑
- **需要修改 RTL**: ❌ (RTL 已支持所有必要寄存器操作)
- **需要 Vivado**: ❌

### 阶段 10-19: [见完整报告后面的阶段表]

各阶段摘要:

| 阶段 | 名称 | RTL | Vivado | Bitstream | 实验室 | 阻塞项 |
|------|------|-----|--------|-----------|--------|--------|
| 0 | 文档冲突修复 | ❌ | ❌ | ❌ | ❌ | P0-1 |
| 1 | 生成 bitstream | ❌ | ✅ | ✅ | ❌ | P0-3 |
| 2 | 烧录+读 MAGIC/VERSION | ❌ | ❌ | ❌ | ✅ | P0-4 |
| 3 | SAFE/SCAN 回归 | ❌ | ❌ | ❌ | ✅ | P1-5 |
| 4 | custom_debug_capture | ❌ | ❌ | ❌ | ✅ | |
| 5 | LOCK HERE Kp=0 | ❌ | ❌ | ❌ | ✅ | |
| 6 | P-only 小 Kp | ❌ | ❌ | ❌ | ✅ | |
| 7 | polarity/limit 标定 | ❌ | ❌ | ❌ | ✅ | |
| 8 | D2-125 对照 | ❌ | ❌ | ❌ | ✅ | |
| 9 | 确定性 Auto Lock | ❌ | ❌ | ❌ | ✅ | |
| 10 | 失锁检测+RESCAN | ❌ | ❌ | ❌ | ✅ | |
| 11 | 训练数据采集标注 | ❌ | ❌ | ❌ | ✅ | |
| 12 | PC CNN 离线识峰 | ❌ | ❌ | ❌ | ❌ | |
| 13 | 在线 CNN 识峰+FSM锁定 | ❌ | ❌ | ❌ | ✅ | |
| 14 | 深度学习参数建议 | ❌ | ❌ | ❌ | ✅ | |
| 15 | 恢复 PI/Ki | 可能 | 可能 | ✅ | ✅ | |
| 16 | 评估替代 D2-125 | ❌ | ❌ | ❌ | ✅ | |
| 17 | 数字 I/Q 相位优化 | ✅ | ✅ | ✅ | ✅ | |
| 18 | 评估替代模拟链路 | ❌ | ❌ | ❌ | ✅ | |
| 19 | Allan deviation 论文 | ❌ | ❌ | ❌ | ✅ | |

**可合并的阶段**: 2+3（烧录+验证），5+6（LOCK HERE + 小Kp可同一次实验）

**绝对不能跳过的阶段**: 0（文档修复）、1（bitstream）、2（MAGIC/VERSION）、3（SAFE/SCAN 回归）、5（Kp=0 无扰切换）、6（P-only 锁定）。这些是安全 Gate。

**现在不应该做的阶段**: 9-19 全部。先通过阶段 0-6。

**最快得到第一版可靠锁定的路线**: 0→1→2→3→4→5→6（约 3-5 天实验室时间，假设每次 Vivado 2-3 小时）。

**最快得到论文阶段性成果的路线**: 0→1→2→3→4→5→6→7→8（~2 周）。阶段 8 完成后即可撰写 "FPGA-based P-only MTS laser frequency stabilization using Red Pitaya" 论文。


## O. 当前唯一下一步

根据判断规则（section 14），AI_STRICT_REVIEW_ENTRY.md 仍有 conflict marker：

**当前唯一下一步: 修复 AI_STRICT_REVIEW_ENTRY.md 第 83-97 行的 git merge conflict。**

- 不修改 RTL
- 不修改 Python
- 不修改 Vivado project
- 不运行任何硬件操作
- 只动这一个文件的这几行

完整 Codex 指令见下一节。


## P. 给 Codex 的下一条完整指令

```
你是只修改文档的 Codex。请在仓库 E:\new\fpga_lock\v94 中执行以下纯文档修复任务:

文件: version/AI_STRICT_REVIEW_ENTRY.md
位置: 第 83-97 行

当前内容包含未解决的 git merge conflict:

<<<<<<< HEAD
截至 2026-07-11，当前主线为：

```text
v3REG-0 register-controlled OUT2 SAFE/SCAN 已由用户上板验证；
GitHub main 已进入 v3LOCK-P0 人工 LOCK HERE 候选；
HOLD / P_LOCK / PI_LOCK / LOCK HERE 尚未完成最新 Vivado synthesis / implementation / timing / bitstream / 烧录 / 上板示波器验证。
=======
截至 2026-07-12，当前主线为：

```text
项目最终目标固定为：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。
当前只做 PZT 基础稳频最小闭环：SCAN -> 观察 MTS error -> 人工选择色散过零点 -> LOCK HERE -> 同拍捕获 ERROR_SETPOINT 和 LOCK_BIAS -> P-only 小增益反馈 -> SAFE。
OUT2 的目标执行器是激光器专用 PZT / Scan 输入，SCAN 和 P_LOCK 使用同一个 PZT 接口。
>>>>>>> 0a6928a (Update v94 project code documents and records)

请:
1. 删除第 83 行的 "<<<<<<< HEAD"
2. 删除第 84-89 行的 HEAD 版本内容（截至 2026-07-11 的描述）
3. 删除第 90 行的 "======="
4. 保留第 91-96 行的 0a6928a 版本内容（截至 2026-07-12 的描述）
5. 删除第 97 行的 ">>>>>>> 0a6928a (Update v94 project code documents and records)"
6. 保留第 98 行及以后的所有内容不变

修复后的第 83-96 行应该完全等于（不含反引号标记）:

截至 2026-07-12，当前主线为：

```text
项目最终目标固定为：基于 Red Pitaya 的全自动深度学习参数优化 MTS 激光稳频系统。
当前只做 PZT 基础稳频最小闭环：SCAN -> 观察 MTS error -> 人工选择色散过零点 -> LOCK HERE -> 同拍捕获 ERROR_SETPOINT 和 LOCK_BIAS -> P-only 小增益反馈 -> SAFE。
OUT2 的目标执行器是激光器专用 PZT / Scan 输入，SCAN 和 P_LOCK 使用同一个 PZT 接口。
```

不修改文件中的任何其他内容。修复完成后用 git diff 确认只删除了冲突标记和 HEAD 版本的 7 行，增加了 0 行，其他内容不变。
```


## Q. 下一次 Claude Code 审查主题

完成当前唯一任务（修复 AI_STRICT_REVIEW_ENTRY.md conflict）后，下一次审查:

**主题: v3LOCK-P0 Bitstream Generation Gate and Pre-Burn Readiness Review**

审查内容:
1. 确认文档矛盾已全部修复
2. 确认 MANIFEST 和 STATUS.md 的验证级别已同步
3. 检查 exp/v3-auto synthesis/implementation/DRC 的完整输出
4. 确认 VERSION=0x00030001 在 RTL 中编码正确
5. 生成 bitstream 前的最终安全检查清单
6. 输出: "可安全生成 bitstream" 或 "以下问题必须先修"

不需要实验室、不需要修改 RTL、不需要烧录。


## R. 最终建议

### 给用户（Cowork 3P）的最终建议

**1. 项目是否走在正确方向？**

是的。用 Red Pitaya 做数字 mixer+LPF 解调，再用 OUT2 驱动 PZT 做 P-only 反馈，这是最直接、最合理的 MTS 稳频架构。混合信号方案（保留模拟 BPF+放大器，FPGA 做数字解调和控制）在现阶段是最稳健的选择。不要现在就想全部数字化。

**2. 当前距离基础锁定有多远？**

非常近。RTL 完整，仿真全过，软件全过，Vivado 时序通过。只差: bitstream 生成 → 烧录 → MAGIC/VERSION 读回 → SAFE/SCAN 回归 → LOCK HERE Kp=0 → P-only 小 Kp。大约 3-5 天实验室工作。

**3. 当前距离自动锁定有多远？**

中等距离。确定性的 Auto Lock（不使用深度学习）在基础锁定完成后，纯软件实现。需要 1-2 周的 Python 开发（过零点检测、峰选择、状态机），不需要修改 RTL 或重新跑 Vivado。

**4. 当前距离深度学习参数优化有多远？**

很远。这需要: 基础锁定成功 → 收集至少 50-100 条标注数据 → 训练和验证模型 → 集成到 GUI → 实验验证。至少 2-3 个月。但在完成基础锁定之前讨论深度学习没有意义。

**5. 现在最应该做什么？**

修复 P0 文档 conflict。这是唯一阻塞项，也是最小工作量的一项（纯文本编辑，5 分钟）。修完后进入 bitstream 生成和烧录。

**6. 哪些事情现在绝对不要做？**

- 不要改 RTL（当前 RTL 已经足够支撑基础锁定）
- 不要恢复 KI/integral（P-only 先锁住再说）
- 不要加新功能（custom_debug_capture、error_setpoint_corrector、out2_lock_controller 已经完备）
- 不要训练深度学习模型（连基础锁定数据都没有）
- 不要尝试替代 D2-125（先让 FPGA 独立锁住）
- 不要去掉模拟 BPF 和前置放大器
- 不要做双执行器或电流反馈
- 不要把 OUT2 接到 D2-125 的 Servo/Aux Output
- 不要声称已经闭环锁定或替代 D2-125

---

**审查结束。**

*审查人: Claude（2026-07-12 session）*
*审查规则集: AI_STRICT_REVIEW_ENTRY.md（含 P0 conflict, 需修复）*
*下一位审查者建议: 等 P0-1 修复完成后发起 v3LOCK-P0 Bitstream Generation Gate Review*
