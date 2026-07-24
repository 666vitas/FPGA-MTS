# FPGA 替代 D2-125 PID 功能 — 全面代码审查

**审查日期**: 2026-06-15  
**审查范围**: `E:\new\fpga_lock\v94\` 下所有 RTL 源码  
**目标**: 用 RedPitaya (Zynq-7010) 板载 FPGA 替代 Vescent D2-125 的锁相放大 + PID 功能

---

## 一、文件结构概览

项目有 4 个主要目录，对应 4 套工程：

| 目录 | 用途 | 关键差异 |
|------|------|----------|
| `guanfang-v0.94/v0.94/` | RedPitaya 官方 v0.94 参考设计 | 新风格 `pid.sv`（SystemVerilog interface），4ADC 版本 |
| `v0.94/rtl/` | 你的自定义开发版本 | 含 `laser_lock_core.sv`、`pi_controller.sv`、`mixer_core.sv`、`lpf_core.sv` |
| `v-weifang/rtl/` | 潍坊新实验平台版本 | 与 v0.94 功能相同，但 top 适配了 Z10 板 |
| `version/v1/`, `version/v2/` | 备份 | 与 v0.94 相同 |

**潍坊版本独有特性**：PD 直连 IN1，ASG 内部生成解调 sin，不需要外部信号发生器。

---

## 二、D2-125 功能到 FPGA 模块映射

D2-125 核心功能及 FPGA 对应状态：

| D2-125 功能 | FPGA 模块 | 状态 | 备注 |
|-------------|----------|------|------|
| 锁相放大器（混频器） | `mixer_core.sv` | ✅ 已上板验证 | 14-bit signed 乘法器，SHIFT=13 |
| 低通滤波器（LPF） | `lpf_core.sv` | ✅ 仿真通过 | 一阶 IIR，LPF_SHIFT=12 |
| PID 控制器 | 官方 `pid.sv` / `pid_block.sv` | ✅ 可用 | 4 路 MIMO，寄存器基址 0x40300000 |
| PI 控制器（带抗积分饱和） | `pi_controller.sv` | ⚠️ 已写好但未集成 | 有 anti-windup、polarity、hold 功能 |
| 解调信号生成 | 官方 `asg.sv` | ✅ 可用 | 支持相位偏移（cfg_off），需软件配置 |
| 输出保护 | `output_protect.sv` | ✅ 已上板验证 | 简单的 enable/reset 门控 |
| 扫频功能 | **无** | ❌ 需开发 | D2-125 有 ramp/sweep 模式 |
| 锁定检测 | **无** | ❌ 需开发 | D2-125 有 lock indicator |
| 调制幅度控制 | **无** | ❌ 需开发 | 可变 modulation amplitude |
| 激光器驱动输出 | `pwm.sv` | ⚠️ 部分可用 | 当前仅用于慢速 PDM DAC |

---

## 三、关键模块详细审查

### 3.1 mixer_core.sv — 数字混频器 ✅

**路径**: `v-weifang/rtl/mixer_core.sv`

```
pd_i (14-bit signed) × ref_i (14-bit signed) → 28-bit product → 算术右移 13 位 → 14-bit 饱和输出
```

**审查结论**: 设计正确，已上板验证通过。关键参数 SHIFT=13 意味着混频增益为 1/8192（~-78 dB），这是因为 14-bit 正弦波满幅值是 ±8191，两个满幅值相乘后需要除以 8192 才能归一化回 14-bit 范围。

**一个需要注意的点**: 当前 mixer 将 `ref_i` 接到 `adc_dat[1]`（IN2），但潍坊版本的目标是用内部 ASG 生成解调信号。需要在 `red_pitaya_top.sv` 中将 ASG 的输出路由到 mixer 的 ref 输入端，而不是从 ADC 采样。

### 3.2 lpf_core.sv — 后置低通滤波器 ✅

**路径**: `v-weifang/rtl/lpf_core.sv`

实现了一个一阶 IIR 低通滤波器（等效于 RC 滤波器）。算法：

```
x_scaled = x_i << LPF_SHIFT     // 扩展到 ACC_WIDTH
delta = x_scaled - acc_q        // 误差
step = delta >> LPF_SHIFT       // 每次只更新误差的 1/2^LPF_SHIFT
acc_next = acc_q + step         // 累加器更新
y_o = acc_next >> LPF_SHIFT     // 降位宽输出
```

**审查结论**: 结构正确。截止频率估算：f_c ≈ f_clk / (2π × 2^LPF_SHIFT) ≈ 125MHz / (2π × 4096) ≈ 4.9 kHz。对于激光稳频（误差信号通常在 kHz 级别）来说，这个截止频率是合理的。

**一个潜在问题**: LPF_SHIFT=12 在 125MHz 采样率下产生的截止频率约 5kHz。如果未来需要更快的锁定响应，可以减小 LPF_SHIFT。建议把 LPF_SHIFT 做成可配置参数（通过寄存器），而不是编译时常量。

### 3.3 官方 pid.sv / pid_block.sv — MIMO PID ✅

**路径**: `guanfang-v0.94/v0.94/.../rtl/pid.sv`, `pid_block.sv`

4 路 MIMO PID（2 输入 × 2 输出 = 4 个 PID 块）。每个 PID 块包含完整的 P、I、D 三条路径：

- **P 通道**: error × Kp → 右移 PSR=12 位 → 输出
- **I 通道**: error × Ki → 累加（带饱和）→ 右移 ISR=18 位 → 输出
- **D 通道**: error × Kd → 右移 DSR=10 位 → 差分（kd_reg - kd_reg_r）

**重要分析 — PID 定点格式**:

| 信号 | 位宽 | 格式 |
|------|------|------|
| 输入/输出 (dat_i/dat_o) | 14-bit | Q1.13 (signed) |
| 误差 (error) | 15-bit | Q2.13 |
| 系数 (Kp, Ki, Kd) | 14-bit | Q2.12 |
| P 乘积 (kp_mult) | 29-bit (15×14) | Q4.25 |
| I 累加器 (int_reg) | 32-bit | Q? |
| I 输出 (int_shr) | 14-bit (32-18) | Q1.13 |

**审查结论**: 官方 PID 设计成熟，可直接用于激光稳频。但需要注意：
1. 当前 top 中 PID 输入接的是 adc_dat[0] 和 adc_dat[1]（原始 ADC），不是经过 mixer+LPF 的误差信号
2. 对于 D2-125 替代场景，应该把 LPF 输出的误差信号接到 PID 输入，而不是原始 ADC

### 3.4 pi_controller.sv — 自定义 PI 控制器 ⚠️

**路径**: `v0.94/rtl/pi_controller.sv`（仅在 v0.94 中存在，v-weifang 中没有！）

这是一个设计更现代、功能更全的 PI 控制器：

**亮点功能**:
- **Anti-windup（抗积分饱和）**: 当控制量达到限幅值时冻结积分器
- **Polarity 控制**: 可翻转误差极性，适配不同的锁频边带
- **Hold 功能**: 可冻结 PI 状态，用于扫频时保持当前输出
- **可配置增益位宽**: GAIN_WIDTH=16（比官方 PID 的 14 位精度更高）
- **独立输出限幅**: output_limit_i 参数
- **诊断输出**: p_term_o、i_term_o、sat_o

**审查结论**: `pi_controller.sv` 是一个很好的设计，但有两个问题：
1. **没有 D 项**: 如果需要微分控制（常用于相位超前补偿），需要补充
2. **没有在 v-weifang 中**: v-weifang 版本没有这个文件，需要复制过去

### 3.5 laser_lock_core.sv — 集成核心 ⚠️

**路径**: `v-weifang/rtl/laser_lock_core.sv`

当前有 4 种 OUTPUT_MODE（0~3，编译时参数），缺少 PID 模式。

| MODE | 输出 | 用途 |
|------|------|------|
| 0 | pd_i（IN1 直通） | ADC→DAC 通路验证 |
| 1 | ref_i（IN2 直通） | ADC→DAC 通路验证 |
| 2 | raw mixer | 观察混频输出 |
| 3 | mixer + LPF | 观察基带误差信号 |

**缺失的关键模式**: MODE 4 — LPF 输出 → PID → OUT1（闭环锁定模式）

**另一个问题**: `control_o` 硬编码为 0（第 110 行），即使未来加入 PID，control_o 也没有被使用。

### 3.6 red_pitaya_top.sv — 顶层集成 ⚠️

**路径**: `v-weifang/rtl/red_pitaya_top.sv`

**关键发现**:

```systemverilog
// 第 138 行
localparam logic USE_LASER_LOCK_CORE = 1'b1;
localparam int   LASER_LOCK_OUTPUT_MODE = 3;

// 第 443-447 行 — DAC 路由
assign dac_a_sum_laser = {laser_error[13], laser_error};  // 符号扩展
assign dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser : dac_a_sum_official;
assign dac_b_sum = dac_b_sum_official;
```

**问题 1**: `laser_control`（PID 控制输出）没有被路由到任何 DAC。当前只有 `laser_error` 接到 DAC A。

**问题 2**: 官方 PID 模块（`red_pitaya_pid`）仍然在 top 中实例化（第 613-629 行），即使 USE_LASER_LOCK_CORE=1 时它的输出不被使用。这会消耗 FPGA 资源。

**问题 3**: ASG 输出 `asg_dat[0]` 和 PID 输出 `pid_dat[0]` 仅在 `USE_LASER_LOCK_CORE=0` 时被使用。官方架构是 ASG + PID 求和后再输出，但自定义链路绕过了这个求和。

---

## 四、D2-125 替代方案 — 推荐的数据流架构

基于现有代码，推荐的信号链：

```
IN1 (PD) ──→ ADC ──→ mixer_core ──→ lpf_core ──→ pi_controller ──→ OUT1 (激光器反馈)
                        ↑                                          │
              ASG sin (内部生成)                                   │
              ~4.565 MHz                                           │
                                                                   │
              ASG cos ──→ 第二路 mixer ──→ LPF2 ──→ 锁定检测       │
                                                                   │
                                            OUT2 (可选: 监控/调制) ←┘
```

### 需要做的修改（按优先级排序）

**P0 — 最小可行闭环**:
1. 在 `laser_lock_core.sv` 中新增 OUTPUT_MODE=4：mixer → LPF → PID → OUT1
2. 将 `pi_controller.sv` 复制到 v-weifang/rtl/
3. 在 `laser_lock_core.sv` 中实例化 `pi_controller`
4. 配置 PID 系数（通过 Linux 用户空间程序写寄存器）

**P1 — ASG 内部解调信号**:
1. 修改 `red_pitaya_top.sv`，将 ASG CH A 输出路由到 `laser_lock_core` 的 `ref_i` 端口
2. 在 ASG 中预载 4.565 MHz 正弦波查找表
3. 暴露 ASG 相位寄存器（cfg_off），允许软件调节解调相位

**P2 — 锁定检测与扫频**:
1. 在 FPGA 中实现幅度检测（将 LPF 输出取绝对值的滑动平均）
2. 实现扫频状态机：ASG 频率从低到高扫描，同时监测误差信号幅度
3. 当误差信号幅度超过阈值时触发锁定

**P3 — 完整 D2-125 替代**:
1. 实现完整的 PI+D 控制（扩展 `pi_controller.sv` 为 `pid_controller.sv`）
2. 添加调制幅度控制
3. 实现自动重锁逻辑
4. 添加 DDS 频率/相位/幅度寄存器映射到系统总线

---

## 五、发现的问题与风险

### 5.1 紧急问题

**1. v-weifang 缺少 pi_controller.sv**
- 自定义 PI 控制器只存在于 `v0.94/rtl/`，不在 `v-weifang/rtl/`
- 影响：潍坊版本无法使用 anti-windup PI 控制
- 修复：复制文件到 v-weifang/rtl/

**2. laser_lock_core control_o 未使用**
- 即使加了 PID，控制输出也没有通路
- 需要在 top 中把 `laser_control` 路由到 DAC（例如 DAC B）

### 5.2 设计问题

**3. 官方 PID 和被绕过的实例化**
- 官方 PID 模块仍在 top 中实例化但输出被丢弃
- 建议：加一个 `ifdef` 来排除未使用的模块，节省 FPGA 资源

**4. ASG ref 路由缺失**
- mixer 的 ref 输入仍然是 adc_dat[1]（IN2 ADC 数据）
- 潍坊版本的目标是用内部 ASG 生成解调信号

**5. LPF 参数硬编码**
- LPF_SHIFT=12、ACC_WIDTH=32 是编译时常量
- 建议：改成可通过系统总线配置的寄存器

### 5.3 潜在风险

**6. 定点数溢出风险**
- 混频后的信号经过 LPF 再进 PID，中间没有位宽保护
- 建议：在 mixer→LPF→PID 链的每级之间加入饱和逻辑

**7. 时序收敛**
- 当前设计在 125MHz 时钟域运行，mixer（1 个 DSP）+ LPF（几级逻辑）+ PID（乘法器 + 累加器）的级联路径可能成为关键路径
- 建议：在 PID 前面加一级流水寄存器

**8. 软件接口**
- 目前没有任何 Linux 用户空间程序来配置 PID 参数、ASG 频率相位等
- 需要开发 C/Python 程序通过 `/dev/mem` 或 UIO 来读写系统总线寄存器

---

## 六、寄存器地址映射（供软件参考）

来自官方 v0.94 设计（系统总线地址基址 + 偏移）：

| 模块 | 系统总线槽位 | 基地址偏移 | 说明 |
|------|------------|-----------|------|
| House Keeping | sys[0] | 0x00000 | SPI, GPIO, LED |
| Scope 0-1 | sys[1] | 0x10000 | 示波器 CH1/CH2 |
| Scope 2-3 | sys[2] | 0x20000 | 示波器 CH3/CH4 |
| **PID** | **sys[3]** | **0x30000** | **4路 MIMO PID 寄存器** |
| AMS | sys[4] | 0x40000 | 模拟混合信号 |
| Daisy | sys[5] | 0x50000 | 菊花链 |
| ASG | sys[2] (scope与ASG共用) | 0x20000 | 任意信号发生器 |

**PID 寄存器详细**（基址 0x40300000）:

| 偏移 | 寄存器 | 位宽 | 说明 |
|------|--------|------|------|
| 0x00 | IRST | 4-bit | 积分器复位 [PID22, PID21, PID12, PID11] |
| 0x10 | PID11_SP | 14-bit | CHA→CHA 设定点 |
| 0x14 | PID11_KP | 14-bit | CHA→CHA 比例增益 |
| 0x18 | PID11_KI | 14-bit | CHA→CHA 积分增益 |
| 0x1C | PID11_KD | 14-bit | CHA→CHA 微分增益 |
| ... | ... | ... | PID12(0x20), PID21(0x30), PID22(0x40) |

---

## 七、总结与建议

### 当前状态
你已经有了 D2-125 替代方案的 **约 60%** 的基础模块：mixer（✅）、LPF（✅）、PID 核心（✅）、输出保护（✅）。缺失的主要是 **模块集成**、**扫频/锁定检测** 和 **软件控制**。

### 立即行动建议

1. **把 pi_controller.sv 复制到 v-weifang/rtl/** — 5 分钟
2. **在 laser_lock_core.sv 中新增 MODE=4 (PID 闭环模式)** — 30 分钟
3. **在 red_pitaya_top.sv 中把 laser_control 接到 DAC B** — 5 分钟
4. **写一个简单的 Python 脚本用 /dev/mem 配置 PID 寄存器** — 1 小时
5. **用电子学回环测试验证整个闭环** — 2 小时

这 5 步做完，你应该就能在桌面上跑通一个基本的数字锁相闭环。之后再逐步加入 ASG 内部解调、扫频、锁定检测等功能。

### 架构整洁建议
建议把所有自定义模块统一放在 `v-weifang/rtl/` 下，并以 `wf_` 前缀命名（如 `wf_mixer_core.sv`、`wf_pi_controller.sv`），方便和官方模块区分，也方便未来回归官方 firmware。
