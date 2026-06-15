# CLAUDE 独立项目审查报告 — v2/v2a 可行性审查

**审查日期**: 2026-06-15
**审查人**: Claude (只读审查，未修改任何 RTL/Testbench/Vivado 工程文件)
**审查范围**: `E:\new\fpga_lock\v94\v0.94\rtl\`, `v0.94\sim\`, `version/v2/v0.94/`, 官方参考设计
**任务**: 独立判断当前 FPGA-MTS 项目是否可行，审查 v2a 现有 PI/PID 代码完成度，判断可否进入 v2 阶段

---

## 一、一句话结论

**有条件可行** — 在补齐三项关键缺口（文档同步、非零 Ki 闭环测试、D2-125 安全接口验证）之前，不建议正式宣称"已进入 v2"。当前 v2B1 代码已经具备 P-only Shadow PI 的完整仿真验证和片上集成，但无法替代 D2-125 的任何真实伺服功能。

---

## 二、当前项目真实状态

### 2.1 代码实际状态（以 read 工具审查的所有 RTL 文件为准）

v2B1 `laser_lock_core.sv`（225 行）**已经完整集成**以下所有模块：

| 模块 | 状态 | 仿真验证 | 板上验证 |
|------|------|----------|----------|
| mixer_core | ✅ 已集成 | ✅ tb_mixer_core 通过 | ✅ v1ab 通过 |
| lpf_core | ✅ 已集成 | ✅ tb_lpf_core 通过 | ❌ 未单独上板 |
| output_protect | ✅ 已集成 | ✅ 集成测试通过 | ✅ v1ab 通过 |
| pi_controller | ✅ 已集成 | ✅ tb_pi_controller (666行/全覆盖) | 仅示波器观察 |
| pid_ce divider | ✅ 已集成 | ✅ 仿真周期正确 | ❌ 未上板验证 |
| DAC 路由 (OUT1/OUT2) | ✅ 已集成 | N/A | ✅ v1ab 验证 |

当前激光稳频链路的完整数据流（在 `red_pitaya_top.sv` 中已实装）：

```
IN1(PD) → ADC → mixer_core → lpf_core → output_protect → error_o → OUT1(示波器观察)
                                                          ↓
                                                    pi_controller (P-only, Ki=0)
                                                          ↓
                                                     control_o → OUT2(示波器观察)
```

这一链路使用 `USE_LASER_LOCK_CORE=1'b1` 和 `LASER_LOCK_OUTPUT_MODE=3` 编译，DAC A 输出 error_o，DAC B 输出 control_o。

### 2.2 文档与实际代码的矛盾

以下矛盾必须在 v2 启动前解决：

| 文档 | 文档内容 | 实际代码 | 实际代码内容 |
|------|----------|----------|------------|
| `00_CONTEXT_FROM_GPT.md` | "PID: 当前不做" | `laser_lock_core.sv` (v2B1) | pi_controller 已完整集成 |
| `01_PROJECT_MASTER_PLAN.md` | PID 是 stage v7 | `laser_lock_core.sv` (v2B1) | PID 在 stage v1d/v2B1 已进入 |
| `01_CURRENT_STATUS_SUMMARY.md` | "PID 还没有实现" | `laser_lock_core.sv` (v2B1) | pi_controller 是完整的数字 PID 核心 |
| `03_VERSION_EXECUTION_CHECKLISTS.md` | v2 执行清单引用 `pid_lock_core.sv` | 实际 RTL | 不存在 `pid_lock_core.sv`，实际使用 `pi_controller.sv` |
| `GPT_README.md` | "v2a PI/PID code has already been written" | `pi_controller.sv` + `laser_lock_core.sv` v2B1 | **正确，与代码一致** |

**结论**: GPT_README.md 的描述是正确的，旧版项目文档（00_CONTEXT、01_MASTER_PLAN、01_STATUS）落后于实际代码。这导致一个危险局面——如果 Codex 读的是旧文档，它可能认为 PID 尚未开始，从而重复造轮子或做出错误架构决策。

### 2.3 v2B1 Shadow PI 的真实含义

v2B1 的 pi_controller 实例化参数：

| 参数 | 值 | 含义 |
|------|-----|------|
| PID_KP_DEFAULT | 2048 (Q2.14) | 使 control_o ≈ error_o / 2 |
| PID_KI_DEFAULT | 0 | **纯 P 控制，无积分** |
| PID_ENABLE_DEFAULT | 1'b1 | 启用了！ |
| PID_HOLD_DEFAULT | 1'b0 | 未冻结 |
| PID_RESET_INTEGRATOR_DEFAULT | 1'b0 | 积分未强制复位 |
| PID_POLARITY_DEFAULT | 1'b0 | 不反相 |
| PID_OUTPUT_LIMIT_DEFAULT | 1500 | 限制 ~±0.18V |
| PID_UPDATE_HZ | 10000 | PI 更新率 10kHz |

Shadow PI 是"示波器观察级"的 PI——它确实在算，但：
- **Ki=0** 意味着它是纯比例控制，没有积分积累
- **OUT2 仅接示波器**，不接激光器，不接 D2-125 Aux Servo
- **Kp 固定**为 2048，不可调
- 参数全部是**编译时参数**，无法通过软件在线修改

因此，**v2B1 不是"PID 未实现"，而是"PID 核心已实装但处于最弱的安全演示模式"**。

---

## 三、v2a PI/PID 代码完成度审查表

### 3.1 pi_controller.sv 核心功能审查

| 功能 | 代码实现 | Testbench 覆盖 | 完成度 | 备注 |
|------|----------|---------------|--------|------|
| P 项计算 | error × kp → KP_SHIFT 缩放 | ✅ 正/负 error，正/负 kp | ✅ 100% | |
| I 项计算 | error × ki → KI_SHIFT 缩放 → 积分累加 | ✅ 积分累积、清零、保持 | ✅ 100% | |
| 抗积分饱和 (anti-windup) | 输出饱和时条件冻结积分器 | ✅ 正负饱和各方向 | ✅ 100% | 设计正确 |
| 积分钳位 | 积分器不超出 ±limit | ✅ 极限值检查 | ✅ 100% | |
| 极性反转 | polarity_i 翻转 error 符号 | ✅ 正负 error 均测 | ✅ 100% | |
| Hold 功能 | hold_i 冻结全部输出 | ✅ 值保持检查 | ✅ 100% | |
| Integrator Reset | 复位积分但保持 P 输出 | ✅ 独立触发测试 | ✅ 100% | |
| Enable/Disable | disable 清零全部输出 | ✅ 切换和优先级 | ✅ 100% | |
| Output Limiter | 独立 output_limit_i | ✅ 动态改变 limit | ✅ 100% | |
| 长时稳定性 | 1000 次迭代无漂移 | ✅ 1000 次检查 | ✅ 100% | |
| 优先级链 | rstn > !enable > reset > hold > pid_ce | ✅ 每种组合 | ✅ 100% | |
| 诊断输出 | p_term_o, i_term_o, sat_o | ✅ 仅在 testbench 检查 | ⚠️ 90% | 可用于调试但无寄存器暴露 |
| D 项（微分） | **无** | N/A | ❌ 0% | pi_controller 不含 D |

**pi_controller.sv 总评**: 代码质量极高，179 行实现了一个完整的带抗积分饱和的 PI 控制器。Testbench (666 行) 在所有维度上都进行了覆盖。这是一个可以直接用于闭环控制的成熟模块。唯一的缺失是 D 项，但对于激光稳频的常规应用（慢速热漂移补偿），PI 通常已经足够，D 项不是硬性要求。

### 3.2 laser_lock_core.sv v2B1 集成审查

| 集成项 | 状态 | 备注 |
|--------|------|------|
| pi_controller 实例化 | ✅ 正确 | ERROR_WIDTH=14, GAIN_WIDTH=16, OUT_WIDTH=14, ACC_WIDTH=48, KP_SHIFT=12, KI_SHIFT=12 |
| Mixer+LPF+PI 链 | ✅ 正确 | protected_error 同时驱动 error_o 和 pi_controller.error_i |
| pid_ce 分频 | ✅ 正确 | CLK_HZ/PID_UPDATE_HZ=12500，单周期脉冲 |
| OUT1 路由 | ✅ 正确 | error_o → dac_a_sum_laser → OUT1 |
| OUT2 路由 | ✅ 正确 | control_o → dac_b_sum_laser → OUT2 |
| 软件可配置性 | ❌ 缺失 | 所有 PI 参数是编译时常量，无系统总线寄存器接口 |
| D2-125 Aux Servo 路由 | ❌ 缺失 | 无第二个控制输出通道 |
| 扫频 ramp 生成 | ❌ 缺失 | 需要信号发生器配合 |
| 锁定检测 | ❌ 缺失 | 无 error 幅度判断逻辑 |

---

## 四、D2-125 功能拆解与替代边界表

D2-125 是 Vescent 的模拟锁相伺服控制器。以下逐项对用它能否被当前 FPGA 代码替代：

| D2-125 功能块 | FPGA 替代状态 | 代码证据 | 差距 | 优先级 |
|---------------|--------------|----------|------|--------|
| **Error Input**（差分输入，±10V） | ✅ 可替代 | 已用 ADC IN1/IN2 替代，范围 ±1V | 需验证 ±1V 足够容纳实际实验的 error 信号 | P1 |
| **Servo PI/PID**（P/I/D 三项） | ⚠️ 部分替代 | pi_controller.sv 有 P+I，无 D | 需要时加 D 项（约 20 行代码） | P2 |
| **Servo Output**（±10V 模拟输出） | ✅ 可替代 | DAC B/OUT2，±1V 范围 | 需加外部放大器或确认 ±1V 已足够 | P1 |
| **Ramp/Sweep**（三角波扫描 ±10V） | ❌ 未实现 | 无 ramp 模块，无 sweep 状态机 | 需要一个 DDS/计数器生成慢速三角波（约 100 行代码） | P0 |
| **Scan/Lock Switching** | ❌ 未实现 | 无状态机 | 需要 scan→lock 状态机（约 150 行代码） | P0 |
| **Lock Acquisition**（锁定捕获） | ❌ 未实现 | 无逻辑 | 需要在 error 过零点自动从 scan 切到 lock（约 80 行） | P0 |
| **Relock**（失锁重锁） | ❌ 未实现 | 无失锁检测 | 需要 error 幅度监测 + 自动回到 scan（约 100 行） | P1 |
| **Lock Quality Judgment**（锁定质量判断） | ❌ 未实现 | 无逻辑 | 可以离线 / PS 端做，PL 端只需输出 error 幅度（约 50 行 PL + 软件） | P2 |
| **Aux Servo Output**（第二路控制输出） | ❌ 未实现 | 只有一个 control_o → OUT2 | Red Pitaya 硬件只有 2 路 DAC，D2-125 有 2 路 Servo Output。如需 Aux 需用 PWM 或放弃 OUT1 | P2 |
| **Modulation Amplitude Control** | ❌ 未实现 | ASG 可调幅度但未接到本链路 | ASG 已有幅度寄存器，只需软件配置 | P2 |
| **10 MHz LPF / 1.8 MHz HPF**（模拟前处理） | ❌ 未实现 | lpf_core 是 5kHz 后处理 LPF | 当前无数字 BPF。但 mixer 前的 BPF 对 SNR 有贡献，不是硬性要求 | P2 |
| **External Modulation Input** | ❌ 未实现 | 无 | 不是核心需求 | P3 |

### 替代边界定义

**可以替代的部分**（约 40% 的 D2-125 功能）:
- 核心伺服 PI 计算（pi_controller.sv 可替代 D2-125 的 Error→PID→Servo Output 路径）
- Error 信号观测（OUT1 输出 mixer+LPF 后的 error）

**暂时无法替代的部分**（约 60% 的 D2-125 功能）:
- 扫频/锁定/重锁的完整自动化流程
- 第二路 Aux Servo Output
- 模拟前处理（BPF/增益）

**替代策略**: 渐进替代，而非一次性替换。先用 FPGA OUT1 输出 error → D2-125 的 Error Input（保留 D2-125 的扫频/PID/锁定），再逐步用 FPGA 自己的 PI 替代 D2-125 的 PID，最后替代扫频和锁定。

---

## 五、Red Pitaya 工程可行性审查

### 5.1 硬件能力

| 参数 | Red Pitaya STEMlab 125-14 | D2-125 | 评估 |
|------|--------------------------|--------|------|
| ADC 采样率 | 125 MSPS | N/A (模拟) | 远超需求（激光稳频带宽 ~kHz） |
| ADC 分辨率 | 14-bit | N/A | 足够（~0.12 mV/LSB） |
| 输入范围 | ±1V (高阻) / ±20V (低阻) | ±10V | 需外部分压/衰减匹配 ±10V PD 输出 |
| DAC 输出范围 | ±1V | ±10V | 需外部放大器 |
| DAC 通道数 | 2 (OUT1, OUT2) | 2 (Servo, Aux) | 刚好够用 |
| FPGA 逻辑资源 | Zynq-7010, 28K LCs | N/A | 当前设计利用率极低（<5%） |
| DSP Slices | 80 | N/A | 当前用不到 5 个 |
| PS 端 ARM | Dual Cortex-A9 | N/A | 可运行软件控制/监控/日志 |

### 5.2 时钟与延迟

- **延迟**: 当前链路从 ADC 到 DAC 的总流水延迟约为 7-8 个 125MHz 时钟周期（~60ns），加上 LPF 群延迟约 20μs（5kHz 截止）。总延迟 <50μs，对于 kHz 级别激光稳频来说完全可忽略。
- **Jitter**: ADC 时钟由板上 PLL 锁定，相位噪声在官方 PID 应用中已验证可用。

### 5.3 DSP 资源估算

| 模块 | DSP48 需求 | 当前使用 |
|------|-----------|----------|
| mixer_core | 1 个乘法器 | 1 |
| pi_controller | 2 个乘法器 (P×kp, I×ki) | 2 |
| lpf_core | 无 DSP（移位+加减） | 0 |
| 合计 | 3 | 3/80 (3.75%) |

资源极其充裕，完全不需要担心时序收敛或资源耗尽。

### 5.4 已知的限制与解决方案

- **±1V 输入范围**: PD 输出可能到 ±5V 甚至更高。需要外部分压电阻网络（简单、低成本），或者在信号进入 IN1 前使用 BNC 衰减器。
- **±1V 输出范围**: 激光器 PZT 可能需要 ±10V 甚至 0-150V。±1V 不足以直接驱动。需要外部高压放大器（D2-125 方案本身也需要这一步，因此不是新增需求）。
- **单端输入**: ADC 输入是单端的（非差分），而 D2-125 Error Input 是差分的。对于实验室桌面应用，单端噪声通常可接受，但需要注意接地回路。

### 5.5 Vivado 编译状态

根据 `01_CURRENT_STATUS_SUMMARY.md`，v1ab 的 bitstream 已经成功生成并加载：
- Synthesis ✅ 通过
- Implementation ✅ 通过
- Bitstream ✅ 生成
- `fpgautil -b` ✅ 加载成功
- v1ab-1 (IN1→OUT1) 和 v1ab-2 (IN2→OUT1) ✅ 板上测试通过

v2B1 (laser_lock_core with pi_controller) 尚未在 Vivado 中走完完整编译链（sim 通过，synthesis/implementation 未跑）。

---

## 六、工程风险排序

### P0 — 阻断级风险（必须在 v2 启动前解决）

**P0-1: 文档与代码脱节**
- 现象: 旧文档说"PID: 当前不做"，但代码已有完整的 pi_controller 集成
- 影响: Codex 或其他协作者可能基于错误前提做出重复工作或错误决策
- 修复: 更新 `00_CONTEXT_FROM_GPT.md` 和 `01_CURRENT_STATUS_SUMMARY.md` 以反映 v2B1 真实状态（预计 30 分钟）

**P0-2: 无扫频（ramp/sweep）模块**
- 现象: 没有任何 ramp 生成逻辑
- 影响: 无法自动扫描激光频率来寻找锁定点。D2-125 替代方案的核心功能缺失
- 风险: 即使 PI 完美，无法找到初始锁定点意味着整个系统无法闭环

**P0-3: 无 scan/lock 状态机**
- 现象: 没有任何 FSM 来管理 scan→lock 转换
- 影响: 需要人工时刻监控示波器并手动切换，无法实现自动锁定

### P1 — 高优先级风险（v2 阶段必须解决）

**P1-1: Pi 参数全为编译时常量**
- 当前所有 PID 参数通过 parameter/locaparam 设置，每次调参需要重新 synthesis + implementation + bitstream（约 30-60 分钟）
- 修复: 将 Kp, Ki, Kd, offset, limit, polarity 等映射到系统总线寄存器，通过 Linux `/dev/mem` 在线修改

**P1-2: DAC 输出范围验证**
- OUT2 control_o 范围 ±1V，能否驱动激光器 PZT/电流控制需要在真实实验环境中验证
- 如果不够，需要外部放大器——这本身不是 FPGA 问题，但必须在闭环前确认

**P1-3: 输出安全保护不足**
- v2B1 的安全策略是"OUT2 只接示波器"，但一旦进入 v2（真正的 PI 闭环），OUT2 会接真实负载
- 缺少: 输出 slew rate 限制、上电 soft-start、PS 端看门狗

### P2 — 中优先级风险（v2 后期解决）

**P2-1: Ki 尚未启用**
- v2B1 的 Ki=0（纯 P 控制），v2 实际闭环需要非零 Ki 来消除稳态误差
- Ki 的非零测试已在 tb_pi_controller.sv 中覆盖，但需要确认实验中的 Ki 取值不会导致积分 windup

**P2-2: 无系统总线接口暴露 PI 诊断信号**
- p_term_o, i_term_o, sat_o 在 verilog 中悬空
- 如果暴露到寄存器，可以在 Linux 端实时监测 PI 内部状态

**P2-3: 无错误记录/日志**
- 没有寄存器记录历史 sat 事件或 error 超范围事件
- 建议至少加一个 sticky status register

### P3 — 低优先级/后续迭代

**P3-1: 缺少 D 项**（pi_controller 只有 PI，不是 PID）
**P3-2: 缺少 Aux Servo Output**（Red Pitaya 只有 2 路 DAC）
**P3-3: 缺少 BPF 前处理**（目前采用 mixer 后 LPF，无 mixer 前 BPF）

---

## 七、创新性判断

### 7.1 技术层面

该项目在技术上**不是创新**，而是**工程实现**。具体来说：

- 数字锁相放大器 (DLA) 和数字 PID 是**成熟技术**，已有几十年历史
- Red Pitaya 的官方 PID 应用（`pid.sv`, `pid_block.sv`）本身就是数字 PID 的 FPGA 实现
- 该项目的工作是将 mixer + LPF + PI 三个标准 DSP 模块串联，并在 Red Pitaya 上跑通，属于**系统集成**

### 7.2 与学术/工业前沿的对比

- Zurich Instruments 的锁相放大器（如 MFLI, UHFLI）已经实现了更高性能的数字锁相 + PID
- 多个课题组已经用 Red Pitaya 实现过类似的激光稳频方案（文献中有报道）
- 该项目的特殊价值在于：**从零构建、教学导向、可完全理解每一行代码**，这对初学者（如项目负责人）有巨大的学习价值

### 7.3 判断

创新性评分: ★☆☆☆☆ (1/5)

但这**不是问题**。激光稳频工具链不需要创新，需要的是可靠、可理解、可维护。该项目的价值在于"拥有自己的工具"而非"发明新原理"。

---

## 八、是否跑偏判断

### 8.1 项目方向检查

对比 GPT_README.md 中的核心目标（用 FPGA 替代 D2-125 的伺服核心）和当前代码实际状态：

| 方向检查项 | 状态 | 判断 |
|-----------|------|------|
| Mixer 解调链 | ✅ 已实现 (mixer+LPF) | 正确方向 |
| PI 控制器 | ✅ 已实现 (pi_controller) | 正确方向 |
| DAC 输出路由 | ✅ 已实现 (OUT1+OUT2) | 正确方向 |
| Red Pitaya 集成 | ✅ 已集成 (red_pitaya_top) | 正确方向 |
| 扫频/锁定 | ❌ 未开始 | 缺失但已规划 |
| 文档维护 | ⚠️ 不同步 | 需要修正 |
| 版本管理 | ✅ 有 version/v1/v2 目录 | 良好 |

### 8.2 判断

**项目没有跑偏**。整体方向正确，核心模块按计划构建。唯一的"偏"在于文档没跟上代码——这不是方向问题，是维护问题。

特别需要指出：**之前的第一份审查报告**（`review_d2_125_pid_replacement.md`）认为"pi_controller 已写好但未集成"——这个判断**不完全准确**。实际代码中 pi_controller 已经在 v2B1 laser_lock_core.sv 中完成了集成，只是处于 P-only Shadow PI 安全模式。这暴露出文档滞后可能导致审查者误判项目进度。

---

## 九、下一步最小可执行路线

### v2-0: 文档同步（建议 1 天内完成，0 行 RTL 变更）

这是**零风险、零代码变更**的准备工作，必须在任何 RTL 改动之前做：

1. 更新 `00_CONTEXT_FROM_GPT.md`: 将"PID: 当前不做"改为"PID: v2B1 已有 P-only Shadow PI 集成，尚未闭环但可在 OUT2 示波器上观察"
2. 更新 `01_CURRENT_STATUS_SUMMARY.md`: 将"PID 还没有实现"改为反映 v2B1 实际状态
3. 更新 `03_VERSION_EXECUTION_CHECKLISTS.md`: 修正 v2 执行清单，将 `pid_lock_core.sv` 改为 `pi_controller.sv`
4. 更新 `02_VERSION_ROADMAP_V1_TO_AI.md`: 将 v2 阶段标记为"v2B1 已部分进入"

### v2-1: 最小闭环演示（建议 1 周内完成，~50 行 RTL 变更）

这是从 Shadow PI（示波器观察）到真正 PI 闭环的**最小步长**：

1. **启用 Ki** (改 1 行): 将 `PID_KI_DEFAULT` 从 `16'sd0` 改为一个小值（如 `16'sd32`，对应 Ki ≈ 0.008）
2. **增加 output_limit 安全值**: 保持 limit 较小（如 14'd500 ≈ ±0.06V）作为安全网
3. **Vivado 编译 + bitstream**: 确认新参数下 synthesis/implementation 通过
4. **电子学回环测试**: 用信号发生器模拟 error，示波器观察 OUT2 的 P+I 响应
5. **安全红线**: OUT2 仍然不接激光器——仅确认 PI 在示波器上表现正确

### v2-2: 完整伺服替代（建议 2-4 周，~300 行 RTL 变更）

1. **ramp/sweep 模块** (约 100 行): 一个简单的三角波生成器，频率可调（默认 50Hz），幅度可配置
2. **scan/lock FSM** (约 150 行): 3 个状态（SCAN→尝试锁→LOCKED），基于 error 过零检测
3. **系统总线接口** (约 50 行): 将 Kp/Ki/limit/sweep_amp 等映射到 sys_bus 寄存器
4. **安全保护**: 输出 slew rate 限制、PS 端看门狗、上电软启动
5. **安全测试**: OUT2 → 外部高压放大器 → 示波器观察 → 记录行为 → **人工审核通过后** → 接激光器

### v2-3 及以后（不在本次审查范围）

- v2-3: 重锁逻辑、锁定质量检测
- v2-4: D 项扩展
- v3: AI 辅助（建议在 PS 端，非 PL）

---

## 十、给 Codex 的后续开发建议

基于本次审查，我对 Codex（项目中的另一个 AI 协作工具）提出以下具体建议：

### 10.1 认知对齐

1. **每次开始工作前，先读 `GPT_README.md`**——它是最权威的状态说明，比旧文档更准确
2. **不要完全信任 `00_CONTEXT_FROM_GPT.md`**——它在 PID 状态这一点上是过时的。代码（`laser_lock_core.sv`）才是事实来源
3. **注意版本命名**: v2B1 = 激光锁定核心 + PI Shadow 模式，v2a = pi_controller.sv 独立模块。两者是不同的东西但密切相关

### 10.2 开发原则

1. **最小步长原则**: 每次只改一个参数或加一个功能，然后走完 仿真→Vivado→上板 完整链
2. **不删旧模式**: 保持 OUTPUT_MODE=0-3 可用，新增模式而非替换
3. **安全第一**: 任何新功能加一个 disable/bypass 开关，默认关闭
4. **优先暴露寄存器**: 把关键参数（Kp, Ki, limit, sweep_amp）映射到系统总线，避免每次调参都要重新跑 Vivado
5. **testbench 先于 RTL**: 新增功能先写 testbench 定义预期行为，再写 RTL

### 10.3 不要做的事

1. **不要创建 `pid_lock_core.sv`**——这个文件在 `03_VERSION_EXECUTION_CHECKLISTS.md` 中被提及但实际不存在，请使用 `pi_controller.sv`
2. **不要尝试完整替代 D2-125**——先用 FPGA 替代 PI 伺服部分，保留 D2-125 的扫频/锁定，再逐步替代
3. **不要把 AI 模型放进 PL**——Zynq-7010 的 PL 资源有限，AI 推理放在 PS 端，FPGA 只负责实时信号链
4. **不要忽视文档更新**——每次 RTL 变更后，更新对应的状态文档

---

## 十一、最终判断

### 11.1 判据回顾

| 判据 | 结论 |
|------|------|
| 核心 PI 计算能力 | ✅ 完备，仿真充分 |
| 信号解调链 (mixer+LPF) | ✅ 完备，v1ab 上板通过 |
| Vivado 编译链 | ✅ v1ab 已验证，v2B1 待验证 |
| 扫频/锁定自动化 | ❌ 完全缺失 |
| 软件在线配置 | ❌ 完全缺失 |
| 输出安全保护 | ⚠️ 仅有 limit，缺 slew rate/看门狗 |
| 文档与代码一致 | ❌ 严重脱节 |

### 11.2 最终结论

**有条件可行**。

当前 v2B1 代码证明 FPGA 能够在 Red Pitaya 上实现 mixer→LPF→PI 的完整数字信号链。pi_controller.sv 的代码质量（179 行 RTL + 666 行 testbench，15 个功能维度全覆盖）远超一个"阶段性原型"的通常标准。

但是，在三个条件满足之前，不能正式宣布"已进入 v2 阶段"：

1. **文档必须同步到 v2B1 代码现状**（v2-0）
2. **Ki 必须启用并通过电子学回环验证**（v2-1）
3. **至少完成 ramp 模块的仿真验证**（v2-2 前置步骤）

如果不满足这些条件，当前状态最好称为"v1.9 — PI 核心就绪，等扫频/锁定后进入 v2"。

### 11.3 时间估算

| 阶段 | 工作量 | 产出 |
|------|--------|------|
| v2-0 (文档同步) | 0.5 天 | 更新 4 个 .md 文件 |
| v2-1 (最小闭环演示) | 3-5 天 | Ki 启用 + Vivado 编译 + 电子学回环测试 |
| v2-2 (完整伺服) | 2-4 周 | ramp + FSM + sys_bus + 安全保护 |
| Total to v2 completion | 约 4-6 周 | 可演示的数字激光稳频闭环 |

---

**审查结束。本报告未修改任何 RTL、testbench 或 Vivado 工程文件。**

*只读审查工具: Read × 29 次, Glob × 2 次。审查范围覆盖 v0.94/rtl/ (全部 .sv), v0.94/sim/ (核心 testbench), version/v2/v0.94/ (全部 .md), guanfang-v0.94 (pid.sv, pwm.sv)。*

---

# 十二、v2B1 上板前二次审查补充

**二次审查日期**: 2026-06-15  
**审查触发条件**: Codex 已完成 v2-0 文档同步（见 `CODEX_v2_0_doc_sync_2026-06-15.md`），需在烧录前做最终检查  
**二次审查范围**: `laser_lock_core.sv` (225行), `pi_controller.sv` (179行), `red_pitaya_top.sv` (706行), `tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` (209行), `tb_pi_controller.sv` (665行), Codex 执行记录

## 12.1 当前是否可以烧录

**可以烧录上板观察。**

判断依据：

- `tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` 全部 15 个 check 通过（V2B1_SHADOW_PI_SIM PASS），仿真覆盖了 reset 清零、Kp 缩放、pid_ce 保持、Ki=0 无积分爬升、output_limit 钳位、极性反转、mode3 mixer+LPF+PI 全链路
- `tb_pi_controller.sv` 全部 60+ 个 check 通过，覆盖 pi_controller 所有功能维度——包括 P/I 计算、anti-windup、积分钳位、极性、hold、reset、enable、disable、饱和恢复、动态限幅、长时稳定性 1000 次迭代、优先级链
- `red_pitaya_top.sv` 中 `USE_LASER_LOCK_CORE=1'b1`，`LASER_LOCK_OUTPUT_MODE=3`，OUT1/OUT2 路由正确
- v1ab 已证明 ADC→DAC 基本通路可用（IN1→OUT1 和 IN2→OUT1 均通过板上验证）
- Codex 的 v2-0 文档同步已将四个过期文档更新到与代码一致，减少了后续误判风险

但这不是无条件的"可以烧录"。烧录后的实验边界必须严格限定在 12.5 节所列的五类实验之内，并遵守 12.6 节的六项禁令。

## 12.2 当前实验边界

逐项明确：

**1. 是否允许烧录后 OUT1/OUT2 接示波器观察？**

允许。这是 v2B1 Shadow PI 的唯一设计目标。OUT1 接示波器 CH2 观察 FPGA mixer+LPF error 信号，OUT2 接示波器 CH4 观察 P-only control 信号。这部分是安全的——output_limit=1500 把 OUT2 限制在约 ±0.18V，远低于 Red Pitaya 的 ±1V 满幅。两个输出都不接任何执行器。

**2. 是否允许 OUT2 接激光器 / PZT / 电流控制端？**

**不允许。** 这是 v2B1 的最核心安全红线。理由：

- 当前是 P-only（Ki=0），无积分消除稳态误差，OUT2 无法在 DC 误差下维持稳定控制
- PID 参数全部是编译时常量，无法在线调整——如果观察到的 control 行为不符合预期，需要改参数后重新跑 Vivado→bitstream→fpgautil，不能在线修正
- 缺少输出 slew rate 限制和上电 soft-start——FPGA 上电到 PLL 锁定之间有不确定状态
- 没有任何 PS 端看门狗——如果 FPGA 逻辑挂死或 AXI 总线异常，OUT2 会保持最后的值或跳变到不确定状态
- 代码注释里反复写明了"OUT2 is oscilloscope-only""OUT2 must not be used as proof that FPGA has locked the laser""Before OUT2 is connected to any real actuator, the enable strategy must be reviewed and made safe again"——这些不是修辞，是安全断言

**3. 是否允许称为真实闭环锁定实验？**

**不允许。** v2B1 连开环都不完整（无 sweep，无 lock detection，无 FSM），根本谈不上"闭环"。任何声称"v2B1 实现了激光锁定"的说法都是不诚实的。当前可以称为"v2B1 Shadow PI 示波器观察实验"或"v2B1 数字 PI 核心板级行为验证"。

## 12.3 当前代码状态复核

以下为 2026-06-15 二次审查的实际代码逐行核查结果：

| 检查项 | 当前值 | 所在文件:行号 |
|--------|--------|-------------|
| 当前是否为 v2B1 Shadow PI | **是** | laser_lock_core.sv:11-12 注释明确写 "v2B1 adds a Shadow PI path" |
| Ki 是否仍为 0 | **是，`PID_KI_DEFAULT = 16'sd0`** | laser_lock_core.sv:56 |
| 当前是否仍为 P-only | **是** | laser_lock_core.sv:54 注释 "Ki=0 makes this ... a P-only board observation" |
| OUT1 输出什么 | **Mixer+LPF 后的 protected error** | laser_lock_core.sv:170 `assign error_o = protected_error`；red_pitaya_top.sv:467 `dac_a_sum_laser = {laser_error[13], laser_error}` |
| OUT2 输出什么 | **P-only PI control_o，限幅 ±1500 counts (~±0.18V)** | laser_lock_core.sv:218 `control_o`；red_pitaya_top.sv:468 `dac_b_sum_laser = {laser_control[13], laser_control}` |
| USE_LASER_LOCK_CORE 是否为 1 | **是，`1'b1`** | red_pitaya_top.sv:146 |
| LASER_LOCK_OUTPUT_MODE 是否为 3 | **是，`3`** | red_pitaya_top.sv:147 |
| 是否已有 ramp/sweep | **没有** | 全文搜索无 ramp/sweep 模块 |
| 是否已有 scan/lock FSM | **没有** | 全文搜索无 FSM 模块 |
| 是否已有在线调参寄存器 | **没有** | 所有 PI 参数为 laser_lock_core 的 parameter，无 sys_bus 映射 |

补充确认：

- `pi_controller.sv` 的 testbench 以 KP_SHIFT=4、KI_SHIFT=4 运行（tb_pi_controller.sv:9-10），而 laser_lock_core 实例化时使用 KP_SHIFT=12、KI_SHIFT=12（laser_lock_core.sv:203-204）。这是**有意为之**：testbench 用较小的 shift 值让数值更大、更容易观察；真实硬件用 KP_SHIFT=12 配合 Kp=2048 使 OUT2 ≈ error_o/2。两者的定点格式逻辑一致，只是缩放不同，不构成风险。
- Codex v2-0 正确地将 `03_VERSION_EXECUTION_CHECKLISTS.md` 中的 `pid_lock_core.sv` 引用修正为 `pi_controller.sv`（CODEX_v2_0_doc_sync_2026-06-15.md:49），消除了 "创建不存在的文件" 的风险。

## 12.4 烧录前检查清单

以下每一项在烧录前必须逐一确认（打勾项）：

**Vivado 工程检查：**

- [ ] Vivado synthesis 通过（无 error，warning 需逐条审查）
- [ ] Implementation 通过（无 error，需关注 timing 报告）
- [ ] Bitstream 成功生成（.bit 文件存在且大小合理）
- [ ] 确认 top 文件是 `red_pitaya_top.sv`，不含旧版覆盖
- [ ] 确认 `USE_LASER_LOCK_CORE = 1'b1`（当前代码已是，若 Vivado 中改过需检查）
- [ ] 确认 `LASER_LOCK_OUTPUT_MODE = 3`（当前代码已是，同上）
- [ ] 确认 `laser_lock_core.sv`、`mixer_core.sv`、`lpf_core.sv`、`output_protect.sv`、`pi_controller.sv` 全部在 Vivado Design Sources 中，无遗漏无重复
- [ ] .bit 已转换为 .bit.bin，已 scp 到 Red Pitaya

**接线安全检查：**

- [ ] IN1 输入信号幅度小于 ±1V（经过衰减器或分压，确认在安全范围）
- [ ] IN2 输入信号幅度小于 ±1V（同上）
- [ ] OUT1 仅接示波器 CH2（高阻探头，不接任何负载）
- [ ] OUT2 仅接示波器 CH4（高阻探头，不接任何负载）
- [ ] 激光器 PZT 控制端 **不接** OUT2
- [ ] 激光器电流控制端 **不接** OUT2
- [ ] D2-125 Servo Output 或 Error Input **不接** OUT2
- [ ] 所有 BNC 线缆标签清晰：示波器探头 vs 激光器反馈，物理上不会接错

**实验环境检查：**

- [ ] 实验台上 OUT2 BNC 线缆目标只有示波器，没有 T 型接头分到别处
- [ ] 如果 OUT2 经过任何放大器、buffer、转接板，确认这些中间设备没有接到激光器
- [ ] 实验记录本上标注"v2B1 Shadow PI 上板观察，非闭环实验"

## 12.5 允许进行的上板实验

以下五类实验可以安全进行，不会对设备或实验造成风险：

**1. 空输入安全测试**

- IN1 和 IN2 悬空或接地
- 上电加载 bitstream
- 观察 OUT1 是否接近 0V（噪声基底）
- 观察 OUT2 是否接近 0V
- 目的：确认 reset 后所有输出安全归零，无异常跳变

**2. IN1 小信号输入测试**

- IN1 接信号发生器，输出 1kHz sine, 100mVpp, 0V offset
- IN2 悬空
- 示波器 CH2 接 OUT1，预期看到同频波形（幅度可能不同）
- 示波器 CH4 接 OUT2，预期看到约一半幅度的 P-only response
- 目的：确认 ADC→mixer→LPF→OUT1 路径正确，PI 有响应

**3. IN1/IN2 混频观察测试**

- IN1 接信号发生器 CH1，输出 1MHz sine, 200mVpp
- IN2 接信号发生器 CH2，输出 1.001MHz sine, 200mVpp
- 示波器 CH2 接 OUT1
- 预期：OUT1 出现约 1kHz 的低频差拍包络（混频+LPF 的基带输出）
- 目的：确认 mixer+LPF 链路的真实差频解调能力

**4. OUT1 error_o 示波器观察**

- 实验条件同上面的测试 2 或 3
- 重点观察 OUT1 的：幅度（不应超过 ±1V）、噪声水平、是否有削顶或饱和
- 记录 OUT1 波形截图，与 Codex 的仿真预期对比（OUTPUT_MODE=3 时预期 error 约 0.12-0.15V，以实际观察为准）
- 目的：给未来的 ramp/sweep 设计提供真实的 error 幅度数据

**5. OUT2 P-only control_o 示波器观察**

- 实验条件同上
- 重点观察 OUT2 的：幅度（预期 ≤ OUT1/2，因 Kp=2048 和 KP_SHIFT=12）、是否被 output_limit=1500 钳位、是否出现 unexpected DC drift（如果有说明 Ki 路径被意外激活或硬件异常）
- 记录 OUT2 对 IN1 幅度变化的响应：改变 IN1 幅度，OUT2 应同步比例变化
- 目的：确认 P-only PI 在真实硬件上的行为与仿真一致，为后续启用 Ki 提供基线数据

## 12.6 禁止进行的实验

以下六项在当前 v2B1 阶段**严格禁止**。这不是建议，是安全红线：

**1. 禁止 OUT2 接激光器 PZT**

OUT2 只有 P-only 控制（Ki=0），无积分意味着它像一个固定增益的比例放大器，无法消除稳态误差。如果强行接 PZT 并期望它"稳频"，结果要么是始终有残差（最好的情况），要么是 OUT2 漂移后激光器跳模（更可能的情况）。且没有软件看门狗，无法紧急关断。

**2. 禁止 OUT2 接激光电流控制端**

同上，且激光电流控制的响应带宽和电压范围与 PZT 完全不同。v2B1 的 PI 参数（Kp=2048, output_limit=1500, update rate=10kHz）从未针对电流控制端标定过。错误的参数组合可能让激光器进入不可预测的工作点。

**3. 禁止 OUT2 接 D2-125 Servo Output**

这本质上是把两个不同设计的控制器串在一起——FPGA 的 P-only OUT2 进入 D2-125 的模拟 PID——构成一个不理解的复合控制回路。两台设备的输出范围、地参考、带宽都不匹配。轻则没有效果，重则 D2-125 输入过载。

**4. 禁止声称已经完成闭环锁定**

v2B1 没有 sweep，没有 lock detection，没有 FSM，Ki=0。这些缺失使得"闭环锁定"在技术上不可能。即使碰巧 IN1/IN2 混频后的 error 看起来像锁定误差信号，也不代表系统处于闭环状态。在学术记录中声称"已完成锁定"是不诚实的。

**5. 禁止声称已经完整替代 D2-125**

GPT_README.md 中明确写了"v2a is the first digital replacement of the D2-125 servo core, but it does not yet replace the full D2-125 workflow"。v2B1 替代的是 D2-125 中约 40% 的功能（Error Input → PI 计算），60% 的功能（sweep、scan/lock FSM、relock、lock quality、Aux Servo）完全缺失。这是一个"伺服核心的数字原型"，不是一个"D2-125 的替代品"。

**6. 禁止现在做 CNN/AI/自动锁定**

项目文档中确实规划了 AI 辅助（01_PROJECT_MASTER_PLAN.md 的 stage v9，04_EXPERIMENT_DRIVEN_IMPLEMENTATION_PLAN.md 的 Phase E），但这些是最后的阶段。在一个连 sweep 和 basic PI 闭环都没跑通的系统上做 AI/CNN，属于典型的"过早优化"和"空中楼阁"。正确的顺序是：先把 PI 闭环跑通（v2-1→v2-2），积累至少几十小时的真实锁定数据，再考虑用这些数据训练或辅助判断。

## 12.7 最终结论

直接回答四个问题：

**1. 现在能不能烧录？**

能。前提是你逐项走完 12.4 的检查清单，特别是接线安全部分。仿真全部通过（tb_pi_controller 60+ check, tb_laser_lock_core_v2b1 15 check），v1ab 已验证了硬件通路，没有理由不烧。但烧完之后你只能做 12.5 的五类实验。

**2. 烧录后能不能接激光器？**

不能。OUT1 和 OUT2 都只能接示波器。OUT2 在 v2B1 的安全模型中是"oscilloscope-only"，代码注释里写了至少五遍。等 v2-1（启用小 Ki + 电子学回环验证）和 v2-2（加安全保护 + 外部放大器确认）全部完成后，再讨论接激光器。

**3. 烧录后能不能称为锁定实验？**

不能。这不是锁定实验，是"Shadow PI 板级行为观察实验"。你可以在笔记里写"v2B1 上板观察，OUT2 P-only control 行为与仿真一致"，但不能写"实现了 FPGA 激光锁定"。两者的区别不是措辞问题——前者是如实记录观察结果，后者是虚假声称完成了一个技术上不可能在当前代码下完成的功能。

**4. 下一步是上板观察，还是继续改代码？**

**上板观察。** 当前代码状态已经达到了"可以烧录、值得观察"的门槛。你需要先看到真实的 OUT1 和 OUT2 在示波器上的波形，记录以下基线数据——这些数据会直接影响 v2-1 的 Ki 取值和 v2-2 的 sweep 幅度设计：

- OUT1 error 在实际 IN1/IN2 信号下的 DC offset 和波动幅度
- OUT2 control 对 IN1 幅度变化的 P-only 响应
- PI update rate 10kHz 在示波器上是否可见（OUT2 的台阶状变化）
- 噪声基底是否在可接受范围内

拿到这些数据后，再进入 v2-1（改一行 Ki 参数，重新编译，再烧）。

---

**二次审查结束。本审查未新增任何文件，未修改任何 RTL、testbench 或 Vivado 工程文件，仅在已有审查报告末尾追加本章节。**
