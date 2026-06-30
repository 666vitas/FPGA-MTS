# CLAUDE_REVIEW_DEEP_LEARNING_FEASIBILITY_V2

**审查日期**: 2026-06-26
**审查范围**: `E:\new\fpga_lock\v94`（只读，未修改任何文件）
**审查人角色**: Red Pitaya STEMlab 125-14 / Python 上位机 / 实验自动化软件审查工程师
**核心问题**: 当前项目是否应该开始写 CNN？"全自动深度学习激光自动锁定系统"的下一步路线是否合理？

---

## 1. 总体结论

### PASS WITH NOTES — 可以继续 v2B3 路线，但严禁现在开始 CNN

**工程项目链路方向正确，文档与代码一致，安全边界清晰。但 v2B3 sequential PI 的 Vivado timing 尚未通过（WNS=-1.931 ns），且没有任何 FPGA register/debug buffer 支持。在这两个问题解决之前，所有关于 scan/lock FSM、CNN 识峰、自动重锁的讨论都是空中楼阁。**

---

## 2. 当前真实链路总结

### 2.1 FPGA RTL 实际链路（代码验证）

`red_pitaya_top.sv` 当前参数：

```systemverilog
localparam logic USE_LASER_LOCK_CORE       = 1'b1;  // 启用自定义 FPGA 路径
localparam int   LASER_LOCK_OUTPUT_MODE    = 3;      // mixer + LPF → error_o
localparam int   LASER_LOCK_CONTROL_PATH_MODE = 1;   // 选通 sequential PI
```

实际信号链：

```
IN1 (adc_dat[0]) ──┐
                    ├──→ mixer_core → lpf_core → output_protect
IN2 (adc_dat[1]) ──┘                                    │
                                              protected_error
                                                    │
                    ┌───────────────────────────────┤
                    │                               │
                    ▼                               ▼
              error_o (14-bit)              CONTROL_PATH_MODE=1
                    │                               │
                    ▼                               ▼
              DAC A / OUT1                   pi_controller_seq
             (= laser_error)                 (7-state sequential PI)
                                                    │
                                                    ▼
                                              control_o (14-bit)
                                                    │
                                                    ▼
                                              DAC B / OUT2
                                             (= laser_control)
```

DAC 路由（`red_pitaya_top.sv` 第 470-484 行）：

```systemverilog
assign dac_a_sum_official = asg_dat[0] + pid_dat[0];
assign dac_a_sum_laser    = {laser_error[13], laser_error};
assign dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser : dac_a_sum_official;
// 同理 dac_b_sum
```

当 `USE_LASER_LOCK_CORE=1` 时，官方 ASG+PID 的 DAC 路径被旁路。**这一点代码与文档完全一致。**

### 2.2 已验证事项

| 事项 | 状态 | 证据 |
|------|------|------|
| IN1+IN2 → mixer+LPF → OUT1 error | ✅ 上板验证 | STATUS.md: mixer.csv 中 OUT1 Vpp=0.03439 V |
| OUT2 P-only shadow control | ✅ 上板验证 | STATUS.md: mixer.csv 中 OUT2/OUT1=0.515 |
| Sequential PI RTL 完成 | ✅ | pi_controller_seq.sv 七状态 FSM |
| Sequential PI XSim 全部通过 | ✅ | xsim.log: tests=27 pass=27 fail=0 |
| Sequential PI Vivado synthesis 成功 | ✅ | exp/v2/synth_1/runme.log: 0 errors |
| Sequential PI Vivado implementation 完成 | ✅ | exp/v2/impl_1/runme.log: route_design 完成 |
| Sequential PI bitstream 生成成功 | ✅ | exp/v2/impl_1/runme.log: Bitgen Completed |
| v2B1 P-only 上板示波器安全输出验证通过 | ✅ | WNS=+0.361 ns, TNS=0.000 ns |

### 2.3 核心问题：v2B3 sequential PI TIMING 未通过

**这是本次审查发现的最严重的工程阻塞。**

`exp/v2/impl_1/runme.log` 关键数据：

```
Estimated Timing Summary | WNS=-1.931 | TNS=-100.165 |

CRITICAL WARNING: [Timing 38-282] The design failed to meet the timing requirements.
```

最差路径全在 `pi_controller_seq` 内部：

```
integrator_next_q_reg[4]/D    (tight setup+hold)
integrator_next_q_reg[5]/D
integrator_next_q_reg[2]/D
integrator_next_q_reg[1]/D
integrator_next_q_reg[47]/D
```

Post-route 最终值：**WNS=-1.931 ns, TNS=-100.165 ns**。bitstream 虽然生成了（"Bitgen Completed Successfully"），但带有关键 timing violation。

对比 v2B1 P-only 版本：WNS=+0.361 ns, TNS=0.000 ns（timing clean）。

**结论：尽管 `pi_controller_seq.sv` 已经将 PI 计算拆成七拍（IDLE→CAPTURE→P_CALC→I_CALC→I_UPDATE→SUM→LIMIT），但当前综合/实现结果仍然在 125 MHz 下差约 2 ns。主要瓶颈是 48-bit 积分器的 anti-windup freeze 逻辑（`freeze_integrator_w` 扇出太重）和 S_SUM 阶段的三项加法器（p_scaled_q + integrator_next_q + offset_ext_q → control_pre_q）。**

**pi_controller_seq 的设计思想是对的（拆分长组合路径），但实际综合器没有把关键路径拆干净。需要进一步优化：将 S_I_UPDATE 阶段的 anti-windup freeze 组合逻辑也寄存一拍，以及将 S_SUM 阶段的 48-bit 三输入加法拆成两拍两个两输入加法。**

---

## 3. 当前禁止事项（逐条核实）

### 3.1 OUT2 接线限制

**所有源代码和文档完全一致地声明 OUT2 仅限示波器。**

| 来源 | 原文 |
|------|------|
| laser_lock_core.sv:107 | "OUT2 remains oscilloscope-only" |
| red_pitaya_top.sv:148 | "OUT2 remains oscilloscope-only" |
| STATUS.md:94 | "OUT2 仍然只能接示波器" |
| HARDWARE_TEST_SOP.md:130 | "OUT2 remains oscilloscope-only. Do not connect it to laser scan/PZT, D2-125, or Scan/PZT" |
| FPGA_MODE_BOUNDARY.md:37-42 | "Do not connect OUT2 to laser scan/PZT, D2-125, any real actuator path" |

**没有任何代码或文档暗示 OUT2 可以接激光器、D2-125 Servo Output、Scan/PZT。安全边界记录完整、一致。**

### 3.2 D2-125 DC Error 禁止接 IN1

STATUS.md 第 163-168 行和 V2_SYSTEM_ARCHITECTURE 中均将该路线标记为"已废弃 / 禁止执行"。当前有效 IN1 信号是 PD/MTS 信号（经模拟带通滤波+放大后，幅度在 ±1V 内）。

### 3.3 禁止事项合规性

所有 STATUS.md 中列出的禁止事项（不修改 RTL 除非授权、不运行 Vivado、不生成 bitstream、不把 OUT2 接激光、不开始 CNN、不开始相位自动匹配）在代码层面均可验证——代码中没有对应的功能实现。

---

## 4. LASER_LOCK_CONTROL_PATH_MODE=1 验证状态

### 4.1 XSim ✅

`xsim.log`：
```
PASS: sequential PI path is selected
PASS: sequential PI keeps OUT1 error observation
PASS: sequential PI Ki=0 matches P-only half scale
PASS: sequential PI output_limit protects OUT2
PASS: sequential PI polarity reverses OUT2
PASS: sequential PI Ki positive accumulates control
PASS: sequential PI Ki positive remains limited
SUMMARY tests=27 pass=27 fail=0
V2B1_V2B3_CONTROL_PATH_SIM PASS
```

### 4.2 Vivado Timing ❌

见第 2.3 节。WNS=-1.931 ns, TNS=-100.165 ns, CRITICAL WARNING。

### 4.3 OUT2 示波器验证 ❌ 未完成

STATUS.md 明确声明："该候选尚未完成新的 Vivado timing 或示波器验证，因此 OUT2 仍只能接示波器。"

**下一步必须先完成 timing closure，再上板示波器验证，然后才能讨论低增益闭环。**

---

## 5. 上位机 V2 模式边界检查

### 5.1 Official SCPI Mode vs Custom FPGA Mode ✅

两个模式的边界在 `FPGA_MODE_BOUNDARY.md` 和 `HOST_APP_V2_DESIGN.md` 中定义清晰：

**Official SCPI Mode**:
- 启动/连接 `redpitaya_scpi` 服务
- 通过 SCPI 控制 ASG OUT1/OUT2
- 通过 SCPI ACQ 采集 IN1/IN2
- **可能覆盖当前加载的自定义 FPGA bitstream**（已文档化风险）

**Custom FPGA Mode**:
- **不启动 SCPI overlay**（明确避免覆盖自定义 bitstream）
- 认为当前自定义 bitstream 已加载
- OUT1 = laser_error, OUT2 = laser_control
- **不声称能控制自定义 FPGA 参数**
- 只记录手动示波器读数，不读取 FPGA 内部信号

### 5.2 是否错误地在 Custom FPGA Mode 下使用 redpitaya_scpi ✅ 没有

`FPGA_MODE_BOUNDARY.md` 第 57-61 行：
> Custom FPGA Mode means the current custom bitstream is treated as loaded and should not be disturbed by starting official SCPI overlay services.

`HOST_APP_V2_DESIGN.md` 第 80-81 行：
> Custom FPGA Mode: Does not start the SCPI overlay.

**上位机正确遵守了不干扰自定义 FPGA bitstream 的原则。**

### 5.3 Custom FPGA Backend Stub ✅

`HOST_APP_V2_DESIGN.md` 第 37 行：
> `custom_fpga_backend.py`: future Custom FPGA interface stub; every hardware access raises `NotImplementedError`.

这正确实现了"预留接口但不假装能工作"的设计原则。

---

## 6. FPGA Register / Debug Buffer 支持

### 6.1 当前状态 ❌ 完全没有

- FPGA RTL 中不存在 `register_bank`、`debug_buffer`、AXI slave 寄存器、system bus 接口
- `laser_lock_core.sv` 的所有 PI 参数（Kp, Ki, offset, limit, polarity 等）都是编译时 `parameter`，没有运行时读写通道
- 上位机 `custom_fpga_backend.py` 是一个抛出 `NotImplementedError` 的 stub

### 6.2 为什么 CNN 前必须先补 register_bank/debug_buffer

这是整个审查的核心逻辑结论：

1. **CNN 需要训练数据** → 需要从 FPGA 读出 `error_internal`（mixer 后、LPF 后、PI 各阶段信号）的真实时间序列
2. **CNN 需要控制扫描** → 需要上位机设定 OUT2 扫描参数（频率、幅度、偏置）→ 目前 OUT2 由 FPGA 内部控制、参数是编译时常量
3. **CNN 识峰后需要设定锁点** → 需要上位机向 FPGA 写入 PI setpoint → 没有寄存器接口就做不到
4. **自动重锁需要 scan/lock FSM** → 需要上位机读写 FPGA 状态机（scan 中 / locked / relock 中）→ 没有状态寄存器就做不到

**因此，在没有 register_bank 和 debug_buffer 的情况下训练 CNN 等于在真空中做图像识别——你能看到的"数据"要么是 mock 模拟的，要么是示波器上手动读的，都不是 FPGA 内部的真实信号。**

### 6.3 register_bank 的最小需求

在 v3（scan/lock FSM）之前必须提供：

- 可读可写的 PI 参数：Kp, Ki, offset, limit, polarity, enable, hold, reset_integrator
- 可读的状态：current_output_mode, control_path_mode, sat, pid_ce_count
- debug_buffer：捕获一段 error_i / p_term / i_term / control_o 时间序列（例如 1024 或 4096 点，可触发）

上位机通过 AXI system bus 或自定义 memory-mapped 接口访问。

---

## 7. 阶段路线评估

### 7.1 论文架构映射（当前项目正确）

`V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md` 第 198-206 行的映射是合理的：

| 论文模块 | 当前项目对应 | 正确性 |
|----------|-------------|--------|
| Mixer + LPF | v1 数字解调 | ✅ 已完成 |
| Slow/Fast PID | v2 sequential PI | ✅ 进行中 |
| Scan/Lock control | v3 FSM | ✅ 未开始，逻辑正确 |
| 相位自动匹配 | v4 IQ/相位优化 | ✅ 未开始，逻辑正确 |
| CNN peak recognition | v5 上位机 CNN 识峰 | ✅ 未开始，位置正确 |
| 双 DAC/PZT+Current | v6+ 后续版本 | ✅ 未开始 |

**这个阶段排序是工程上合理的。CNN 不应该在 PI 未闭环、scan/lock FSM 不存在、相位匹配未处理的情况下介入。**

### 7.2 当前项目应该分成的实际阶段

根据本次审查发现的实际 RTL/文档/timing 状态，建议修正为：

```
v2B3: sequential PI timing closure + OUT2 示波器验证
      ↓ (WNS ≥ 0 ns 且示波器行为可解释)
v2D/E: 真实 MTS error 下 OUT2 开环观察
      ↓ (OUT2 方向、幅度、噪声、限幅都通过)
v2F: 低增益闭环替代 D2-125（最基本的 PI lock）
      ↓ (能锁住 > 1 分钟，OUT2 不失控)
v2G: FPGA PI vs D2-125 性能对比
      ↓
v3: register_bank + debug_buffer + scan/lock FSM
      ↓ (上位机能读写 FPGA 参数、状态、波形)
v4: 相位/IQ 优化（如果需要）
      ↓
v5: 上位机 Python 1D-CNN 识峰
      ↓ (此时才用真实 FPGA debug_buffer 数据训练 CNN)
v6: 自动重锁 + 数据记录
      ↓
v7: CNN FPGA 部署（HLS 或 hand-coded RTL，在 ARM/PL 上部署）
```

**v3 中的 register_bank 和 debug_buffer 是 v5 CNN 的前置硬依赖。没有它们，CNN 得不到真实的 FPGA 内部信号数据。**

---

## 8. 是否应该现在开始写 CNN

### 明确回答：不应该。

**原因按优先级排列：**

1. **硬件数据不存在**：当前 FPGA 没有任何 debug_buffer 或 register 接口。CNN 若现在就开始写，训练数据只能是 mock 模拟的——这和用 MNIST 练手没区别，不能迁移到真实 MTS 信号。

2. **PI 还没闭环**：CNN 的目的是在 PI 锁定后"识别吸收峰"和"判断是否失锁、需要重锁"。但在 PI 自己都没闭环的情况下，你根本没有"锁定后"的 error 信号可以喂给 CNN。

3. **scan/lock FSM 不存在**：CNN 识峰后要告诉 FSM"锁这里"。目前没有 FSM，CNN 的输出没有执行者。

4. **timing 未通过**：sequential PI 在 Vivado 中 WNS=-1.931 ns。这不是"可以上板试试"的状态——时序违规意味着 PI 计算在某些周期会出错误结果，导致 OUT2 输出不可预期。训练 CNN 需要可靠的硬件行为作为 baseline。

### 应该先完成的工程前置条件

1. **v2B3 sequential PI timing closure**（WNS ≥ 0 ns, TNS = 0 ns）
2. **v2B3 OUT2 示波器验证**（行为与 XSim 一致）
3. **v2F 低增益闭环**（至少能锁 1 分钟以上）
4. **v3 register_bank**（上位机能读写 PI 参数）
5. **v3 debug_buffer**（上位机能抓取 FPGA 内部 error/p_term/i_term/control 的时间序列）

**只有以上 5 项全部完成后，v5 CNN 才有真实数据可训练、可验证。**

---

## 9. 下一步优先级

### Priority 1（阻塞，必须立即处理）

**修复 v2B3 sequential PI 的 Vivado timing**：

当前 WNS=-1.931 ns 的问题在于 `pi_controller_seq.sv` 的 S_I_UPDATE 和 S_SUM 阶段仍然包含过长的组合路径。建议的修复方向：

- 在 S_I_UPDATE 中，将 `freeze_integrator_w` 的组合逻辑（`current_control_pre_w` vs `limit_pos_w/limit_neg_w` 比较 + `i_delta_w` 符号判断）拆成两拍：先用一拍算 `freeze_integrator_w`，下一拍再决定 `integrator_candidate_w`
- 在 S_SUM 中，将 48-bit 三输入加法 `p_scaled_q + integrator_next_q + offset_ext_q` 拆成两拍两个两输入加法
- 这会使 sequential PI 从 7 个状态变成 9 个状态，但不影响功能和接口
- **目标：WNS ≥ 0 ns, TNS = 0 ns**

### Priority 2（顺序依赖 Priority 1）

**v2B3 OUT2 示波器验证**：
- 确认 sequential PI 的 OUT2 行为与 XSim 一致
- 确认小 Ki 没有导致积分爬升或失控
- 记录 OUT1/OUT2 波形，与新 v2B1 baseline 对比

### Priority 3（顺序依赖 Priority 2）

**v2F 低增益闭环准备**：
- 确认激光控制端物理接口（电压范围、极性、带宽）
- 设计极低增益 PI 参数，确保 OUT2 +OUT1 同时接示波器的最安全闭环测试

---

## 10. 上位机需要补的接口

| 接口 | 当前状态 | 需要补充 |
|------|---------|---------|
| SCPI acquisition (IN1/IN2) | ✅ V2 已有 `acquisition_worker.py` | 无 |
| OUT2 SCPI 控制（Official Mode） | ✅ | 无 |
| Custom FPGA IN1/IN2 读取 | ❌ 需要 SCPI ACQ 读取 | 在 Custom FPGA Mode 下也允许 SCPI ACQ（只读 IN1/IN2，不控制 ASG OUT1/OUT2，不启动 redpitaya_scpi overlay） |
| Custom FPGA 参数读写 | ❌ | 依赖 FPGA register_bank |
| FPGA debug_buffer 读取 | ❌ | 依赖 FPGA debug_buffer |
| scan/lock FSM GUI | ❌ | 依赖 v3 FSM |

**关键设计决策：在 Custom FPGA Mode 下，SCPI ACQ 读取 IN1/IN2 是安全的——它只读取 ADC scope buffer，不会干扰 ASG 输出。上位机应该在 Custom FPGA Mode 下也允许 SCPI ACQ，但不启动 redpitaya_scpi overlay（通过 SSH 确认 overlay 未加载或直接连已有 SCPI 端口 5000 只发 `ACQ:*` 命令）。**

---

## 11. FPGA 需要补的接口

| 接口 | 优先级 | 最小需求 |
|------|--------|---------|
| register_bank | v3（CNN 前） | system bus slave (sys[6] or sys[7])；至少 16 个 32-bit 寄存器；可读写 Kp/Ki/offset/limit/polarity/enable/hold/reset/setpoint/mode；可读状态 sat/pid_ce_count/fsm_state |
| debug_buffer | v3（CNN 前） | BRAM 环形缓冲区；至少 4096 深度 × 32-bit；存储 protected_error/p_term/i_term/control 的时间序列；trigger 寄存器触发一次抓取；上位机通过 system bus 读出 |
| scan/lock FSM | v3（CNN 前） | 状态：IDLE / SCAN / LOCK / RELOCK；上位机可读写当前状态；自动从 SCAN 切 LOCK 的条件可配 |

---

## 12. CNN 应该何时介入

**CNN 的正确介入时机是 v5，即 register_bank + debug_buffer + scan/lock FSM + 低增益闭环全部完成之后。**

在 v5 开始前，可以并行做 CNN 的**离线准备工作**（不影响 FPGA 主工程进度）：

- 研究论文中 1D-CNN 的架构：输入层大小、卷积核数、池化策略、全连接层
- 在 Python 中搭建一个原型 CNN，用模拟的 MTS error 信号测试
- 准备吸收峰标注工具（人工标注真实 error 波形上的锁点位置）
- 确定 CNN 的输出格式（吸收峰编号、锁点评分、置信度）

**但不要"正式开始写 v5 的 CNN 代码"，因为训练数据——真实的 FPGA debug_buffer 录制的 error 波形——还不存在。**

---

## 13. 下一条 Codex 实施任务建议

```
请修复 pi_controller_seq.sv 的 125 MHz timing violation。

当前状态：
- v2B3 sequential PI 的 XSim 全部通过（tests=27 pass=27 fail=0）
- Vivado synthesis/implementation/bitstream 已完成
- 但 post-route timing 为 WNS=-1.931 ns, TNS=-100.165 ns
- 最差路径在 integrator_next_q_reg 和 control_pre_q 的组合逻辑中

修复目标：
1. 将 S_I_UPDATE 阶段拆分：
   - 现有逻辑：一个周期内算 freeze_integrator_w + integrator_candidate_w +
     integrator_accepted_w + integrator_next_q 更新
   - 建议拆分：先用一拍算 freeze_integrator_w 和 integrator_candidate_w 的组合；
     下一拍才更新 integrator_next_q

2. 将 S_SUM 阶段拆分：
   - 现有逻辑：p_scaled_q + integrator_next_q + offset_ext_q 三输入加法在一拍
   - 建议拆分：一拍做 p_scaled_q + integrator_next_q，下一拍加 offset_ext_q

3. 相应增加 1-2 个 FSM 状态（例如 S_I_PRECALC + S_I_UPDATE 替代原 S_I_UPDATE；
   S_SUM_PRE + S_SUM_FINAL 替代原 S_SUM）

验收标准：
- XSim 回归通过（所有原有 test case 仍然 PASS）
- Vivado post-route timing：WNS ≥ 0 ns, TNS = 0 ns
- 更新 xsim.log 和 xvlog.log

禁止：
- 不修改 pi_controller.sv（保留旧参考）
- 不修改 laser_lock_core.sv 的接口
- 不改变 public outputs 的语义（control_o/p_term_o/i_term_o/sat_o 的行为不变）
- 不修改 red_pitaya_top.sv
- 不修改 Vivado 工程文件
- 不生成 bitstream
- 不上板
```

---

*审查完成。报告保存于 `E:\new\fpga_lock\v94\version\v2\CLAUDE_REVIEW_DEEP_LEARNING_FEASIBILITY_V2.md`*
