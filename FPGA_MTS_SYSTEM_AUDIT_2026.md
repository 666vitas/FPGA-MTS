# FPGA-MTS 真实闭环导向工程审计报告（2026）

> 审计日期：2026-08-24
> 审计模式：`ANALYZE`，只读代码/文档/Git，并运行现有 Host 测试；未修改产品代码，未运行 Vivado，未生成或加载 bitstream，未连接硬件。
> 审计基线：本地 `main@d435c51`，同时审查当前 working tree 中已有、未提交的 Host/测试/STATUS 修改。
> 唯一 KPI：缩短从“可扫描、可看谱”到“一次真实、可重复的 P-only 激光锁定”的距离。

## 1. Executive Summary

### 目前做到什么

项目已经完成了一条结构上完整、可追踪的 FPGA 数字 P-only 候选闭环：

```text
IN1(PD) × IN2(REF)
→ mixer
→ fixed IIR LPF
→ laser_error
→ error - setpoint
→ polarity × Kp/256
→ correction limit
→ captured actual OUT2 bias
→ absolute limit + slew limit
→ OUT2(PZT/Scan)
```

Host 也已具备身份检查、SAFE、SCAN、四通道 aligned capture、人工选零交叉、generation 检查、`ARM VALIDATE/ACTIVE`、readback、事件和失败诊断。当前 working tree 的 Host tests 为 `[UNIT TESTED] 181 passed in 8.40s`。RTL 记录表明 20 个 testbench 已通过，但本次审计没有重跑 RTL 仿真。

真实硬件方面，已有证据只证明：旧 bitstream 能通过 GUI/SSH/寄存器让 OUT2 扫描，能看到相应光谱/误差信号候选，并曾完成空载 OUT2 软件预补偿验证。用户还报告过带 PZT 扫描时可以选择 zero crossing，但旧 `LOCK HERE` 后谱峰与 cursor 明显偏移。

### 没做到什么

**尚未证明真实锁定。** 没有当前 `VERSION=0x00030200` L1 bitstream 的生成、加载和板上身份记录；没有带 PZT 负载的 OUT2 节点标定；没有证明 OUT1/内部 `laser_error` 是稳定、低噪、相位正确且可用于锁频的 MTS error；没有证明整体 feedback sign；没有 Kp=0 模拟无扰切换；没有非零 Kp 后 error RMS 降低；没有 60 s 保持和重复成功记录。

因此应把项目分成两个评分：

- **源码能力：Level 6/10 候选**——代码能闭合 P-only 回路，并有理想化 plant 仿真。
- **真实系统证据：Level 2/10**——已可靠到“扫描并观察 spectroscopy”；Level 3（物理上可用的 error）尚未正式通过，更不能据代码把系统评为 Level 6。

### 最主要瓶颈

瓶颈不是“缺更多功能”，而是下面五个证据断点没有被按顺序关闭：

1. 当前 L1 build 的完整 timing/约束 Gate 未闭合，且干净 timing 报告未作为可复核工件保存在当前报告目录。
2. error signal 的物理适用性没有定量验证，尤其是 REF 相位、零点噪声、斜率、DC offset 和 ADC/mixer clipping。
3. OUT2 command、实际带载节点电压、PZT 响应和静态/动态工作点之间的映射未知。
4. `error polarity × FPGA polarity × DAC/PZT response` 的总环路符号没有现场确认。
5. 当前 L1 源码从未在真实激光链路上完成 Kp=0 → 最小非零 Kp → 60 s → 重复性验收。

### 为什么开发很多但实验锁定没有明显推进

过去的工作大量提高了安全性、可观测性、测试覆盖、GUI 诊断、状态机和 timing 可实现性；其中 2026-07-26 的实时 ERROR crossing、实际 OUT2 bias capture、Kp ramp、supervisor 和 OUT2 pipeline 是直接缩短真实锁定距离的工作。但硬件实验节奏没有同步跟上软件/RTL迭代，且现有板上证据仍属于旧 bitstream。结果是“新能力主要存在于源码和仿真，实验台仍在重复旧的扫描/选点体验”。

### 下一步最应该做什么

当前 Gate 是 `LOCK-MVP-L1`。**唯一下一步不是调 Kp，也不是接线试锁，而是先固定并提供与当前源码对应的完整 Vivado timing 工件；若 `STATUS` 所述 0.142 ns route 结果没有原始报告，则重新运行并导出。随后只读审查现有 XDC/官方 I/O 的 `check_timing` 语义，解释并正确处理 19 个 unconstrained internal endpoints、17 个 no-input-delay ports、42 个 no-output-delay ports 和 daisy/DNA no-clock 项。** 在没有证据前不得用 blanket false path 清零。完整 Timing Gate 通过后，才生成带明确 SHA/日期/VERSION 的测试 bitstream，再进入一次一个硬件实验的 H0→H4 路线。

---

## 2. 审计依据、证据等级与文档一致性

### 2.1 权威依据

本报告依次采用：`AGENTS.md`、`version/CURRENT_GATE.md`、`version/STATUS.md`、`version/CURRENT_REVIEW_MANIFEST.md`、active rule、active architecture spec、当前源码/测试、supporting hardware records、Git 历史。

### 2.2 发现的治理漂移

| 文件 | 当前内容 | 审计判断 |
|---|---|---|
| `version/CURRENT_GATE.md` | Gate=L1，但 blocker 仍写“尚未重新运行 synthesis/implementation” | 与更新较晚的 STATUS 冲突；Gate 目标有效，blocker 描述过期 |
| `version/STATUS.md` | 已记录 route setup/hold 收敛，但完整 `check_timing` 未通过 | 当前最可信动态事实 |
| `version/CURRENT_REVIEW_MANIFEST.md` | 仍写 Gate=T0 | manifest 已漂移 |
| `README.md` | 仍写 Gate=T0、WNS=-0.387 ns | 已明显过期 |
| `docs/architecture/FPGA_MTS_LINIEN_BASIC_LOCK_PROJECT_SPEC.md` | 主体含旧 SIMPLE/HOLD/APPLY P 描述，末尾再用 L1 note 覆盖 | 可读但容易误操作，必须先读末尾覆盖说明 |
| `docs/process/CLAUDE_REVIEW_2026-07-27_LOCK_MVP_L1_READ_ONLY_AUDIT.md` | 把 mixer 输入描述为 ASG sine | 与当前 `red_pitaya_top.sv` 的 `adc_dat[1]`/IN2 REF 不符 |

这些漂移不会直接让环路正反馈，但会让开发者烧错 build、执行错 SOP、把旧结果当成当前事实，是显著的工程风险。

### 2.3 本报告标签

- `[CODE INSPECTED]`：本次直接追踪了当前源码。
- `[UNIT TESTED]`：本次实际运行 `python -m pytest -q tests`。
- `[RTL SIMULATED]`：仅引用 STATUS 中记录的既有仿真结果，本次未重跑。
- `[USER HARDWARE VERIFIED]`：只采用明确记录的用户实测。
- `[NOT VERIFIED]`：没有足够当前硬件证据。

---

## 3. 当前系统真实状态

| 层级 | 状态 | 证据 |
|---|---|---|
| ADC/DAC 基本工作 | 已有历史硬件证据 | 扫描输出及通道响应可见 |
| GUI→SSH→`/dev/mem`→CSR | 已有历史硬件证据 | base `0x40600000`，旧 MAGIC/VERSION 读回成功 |
| FPGA triangle SCAN | `[USER HARDWARE VERIFIED]` | 旧 bitstream 下可扫谱 |
| aligned CH1/CH2/CH3/CH4 capture | `[IMPLEMENTED]`、软件/RTL测试；真实连续对齐验收不足 | 当前 capture RAM 四通道同拍写入 |
| MTS error 生成 | `[IMPLEMENTED]` | mixer+LPF 路径明确；物理“可锁”性未证 |
| 人工 zero-crossing 选择 | `[IMPLEMENTED]`、Host tests | 真实目标可选曾被用户报告 |
| L1 realtime crossing acquisition | `[IMPLEMENTED]`、既有 `[RTL SIMULATED]` | 当前 bitstream 未上板 |
| Kp=0 原子切换 | `[IMPLEMENTED]`、既有 `[RTL SIMULATED]` | 带载模拟无扰未证 |
| 非零 Kp 负反馈 | 理想 plant 仿真通过 | 真实激光/PZT 未证 |
| 60 s/重复锁定 | `[NOT VERIFIED]` | 无日志、截图、CSV、bitstream identity 证据 |

结论：**当前不是“锁定系统已经完成、只差调参”，而是“用于第一次闭环的数字基础设施已基本就绪，但物理对象和部署证据还没有接上”。**

---

## 4. 当前实验接线图

### 4.1 当前源码定义的理想 L1 链路

```text
External RF source ───────────────┬──→ EOM drive 【需要现场确认】
                                  └──→ Red Pitaya IN2 = REF (< allowed input range)

Laser → Rb cell / MTS optics → PD + analog conditioning
                                  └──→ Red Pitaya IN1 = PD (< allowed input range)

IN1/IN2 → FPGA mixer/LPF → OUT1 = laser_error → oscilloscope observation
                         └→ P controller → OUT2 = selected_out2
                                              └→ laser dedicated PZT/Scan input
                                                   → laser frequency → optics/PD
```

### 4.2 仓库能确认与不能确认的边界

已确认：

- 代码语义固定为 IN1=PD、IN2=REF、OUT1=`laser_error`、OUT2=`selected_out2`。
- 当前 L1 目标是 OUT2 只驱动激光器专用 PZT/Scan input。
- 禁止 OUT2 接 laser current modulation，禁止接 D2-125 `Servo Output`/`Aux Output`，禁止与任何有源输出并联。

无法从当前仓库确认：

- RF source 到 EOM 与 IN2 的实际 splitter、幅度、相位和终端方式。
- PD/analog conditioning 的带宽、增益、DC offset、50 Ω/Hi-Z 条件。
- 当前实验台上 OUT1、OUT2、D2-125 和示波器每个通道的真实接线。
- PZT/Scan input 的允许范围、输入阻抗、内部增益以及 V→laser-frequency 方向。
- 示波器 probe ratio、coupling、load、地线拓扑。

以上全部标记为 **【需要现场确认】**，不能从“代码设计目标”推断为“真实接线”。

### 4.3 D2-125 当前角色

active L1 架构不需要 D2-125 参与闭环。历史/roadmap 文档既出现“D2-125 曾用 FPGA error 尝试锁定”的乐观描述，也有硬件记录明确说当前扫描不是 D2-125 替代，且缺少可复核实验日志。结论是：

> **D2-125 的当前真实角色无法从仓库确认。理想 L1 链路应旁路其有源输出；若它仍连接在系统中，必须现场画出每根线后再进行任何 OUT2 实验。**

---

## 5. FPGA 数据路径

### 5.1 输入与解调

1. `v0.94/rtl/red_pitaya_top.sv:475-487`：ADC 16-bit bus 取 `[15:2]`，再从板卡格式转换为 signed 14-bit，代码包含“negative slope”转换。
2. `red_pitaya_top.sv:493-503`：`adc_dat[0]`→PD，`adc_dat[1]`→REF。
3. `v0.94/rtl/mixer_core.sv:35-59`：signed 14×14→28-bit product，`>>>13` 后饱和到 signed14。
4. `v0.94/rtl/lpf_core.sv:34-82`：一阶 IIR，近似

   ```text
   y[n] = y[n-1] + (x[n]-y[n-1]) / 4096
   ```

   125 MHz 下近似 `fc ≈ 4.86 kHz`、时间常数约 `32.8 µs`。
5. `laser_lock_core.sv:172-196`：top 固定 `OUTPUT_MODE=3`，所以 `laser_error=LPF output`，并送 OUT1。

### 5.2 capture

`custom_debug_capture.sv:63-92` 在同一 `adc_clk` 边沿把四个通道写入独立 BRAM：

```text
CH1 = PD raw ADC count
CH2 = REF raw ADC count
CH3 = laser_error
CH4 = selected_out2 digital command
```

四通道数字采样是对齐的。注意 CH4 是 FPGA command/readback，不是示波器测得的 loaded PZT node voltage。

### 5.3 target crossing 与原子切换

`simple_lock_acquisition.sv` 将 target OUT2 只当 guard center。ARM 后仍保持 SCAN，在指定 scan direction、OUT2 guard 和 ERROR crossing direction 同时满足时：

- crossing detector 要求先连续 N 拍位于 `<=-H`，再连续 N 拍位于 `>=+H`（或反向）；
- 保存对齐的 crossing OUT2/error；
- `custom_register_bank.sv:490-500` 把实际 trigger OUT2 写成 `LOCK_BIAS`，写入 setpoint/limits，`MODE=P_LOCK`、`ENABLE=1`；
- SIMPLE 不强制 Kp=0，允许用户预选 Kp=0 或 4；
- Kp 由 FPGA ramp 到目标值。

默认 H=4 counts、N=3。N=3 在 125 MHz 下只覆盖 24 ns；它是数字连续样本条件，不等于经过独立噪声样本统计。真实噪声抑制能力仍需板上验证。

### 5.4 P-only controller

`custom_register_bank.sv:1739-2049` 实现：

```text
lock_error = saturate14(laser_error - ERROR_SETPOINT)
signed_error = polarity ? -lock_error : lock_error
p_term = (signed_error × Kp) >>> 8
correction = clamp(p_term, ±CORRECTION_LIMIT)
target = clamp(LOCK_BIAS + correction, ±LOCK_LIMIT)
OUT2 = slew_limit(previous_OUT2, target)
```

因此 Kp 的数字增益是 `Kp/256`：Kp=4→0.015625，8→0.03125，16→0.0625，32→0.125，256→1.0。

当前 L1 默认 `servo_update_div=125`，即约 1 MHz OUT2 update；默认 slew=1 count/update。P pipeline 为 8 个 adc clocks，约 64 ns，但 actuator、LPF 和 plant 延迟远大于这一数字流水线延迟。

### 5.5 SAFE 与异常

- `ENABLE=0`、`MODE=SAFE`、abort 或 acquisition fault 会让 OUT2 数字命令归零。
- saturation、ARM/ACQUIRE runtime 状态异常、timeout、supervisor divergence 会触发 SAFE。
- 但进入 `P_LOCKED` 后 supervisor 停止累计；此后只继续检查 saturation、MODE、ENABLE 等硬故障，不持续判定 error 是否漂离目标。因此 `P_LOCKED` 不是长期 lock detector。

---

## 6. 上位机 → FPGA 控制路径

### 6.1 “按 ARM BASIC LOCK 后发生什么”

```text
用户点击 ARM BASIC LOCK
→ main_window.py::_start_custom_fpga_operation("lock")
→ 停止 Live capture，检查 worker/identity/SCAN/target/generation/Kp
→ CustomFpgaRegisterWorker
→ 每次操作新建 AcquisitionService + LockService + LocalClient
→ LockService.request_lock()
→ CustomFpgaBackend.arm_lock_target()
→ SSH 上传/执行嵌入式 Python helper
→ Red Pitaya /dev/mem base 0x40600000
→ 写 target/crossing/Kp/supervisor shadow CSR
→ 校验 CONFIG_VALIDATION
→ 写 ACQ_COMMAND=1
→ 最多约 200 ms 有界轮询 FPGA state
→ FPGA SCAN 中等待实时 ERROR crossing
→ 捕获实际 selected_out2 为 LOCK_BIAS
→ MODE=P_LOCK，Kp soft-start，supervisor 判定
→ ACQUIRING / P_LOCKED，或 FAILED/FAULT→SAFE
```

### 6.2 结构上是否形成物理负反馈闭环

从当前源码结构看，**信号路径已经闭合**：OUT2 影响 PZT，PZT 影响 laser frequency，frequency 影响 spectroscopy/PD，PD/REF 形成 error，error 再改变 OUT2。Host 不在实时 servo loop 内。

但“结构闭合”不证明“物理负反馈”：真实 PZT 是否接入、V→frequency 的符号和带宽、error 的物理意义、Kp 是否足够且稳定都没有当前硬件证据。因此最终判词是：

> **软件/RTL 闭环存在，但物理闭环尚未验证。**

### 6.3 Host 架构与文档目标的差距

文档要求 `LockService` 是唯一长期状态所有者、RegisterMapper 唯一拥有 CSR。但当前实现是：

- `connection_workers.py:136-140` 每次 worker 操作重新创建 `LockService`；
- GUI 自己保存 `selected_lock_point`、capture generation、acquisition state、applied Kp、worker/live flags；
- CSR map 同时存在于 RTL、`custom_fpga_scan_control.py` 本地字典及其嵌入式 REMOTE_HELPER；
- 尚无独立 `register_mapper.py`。

FPGA readback 和 backend 的再次检查缓解了风险，但“单一状态所有者/单一 register truth”尚未真正实现。

---

## 7. 关键寄存器与协议

base address：`0x40600000`；32-bit word，地址步长 4 bytes。关键寄存器如下：

| Offset | 名称 | 语义/格式 |
|---:|---|---|
| `0x00` | MAGIC | `0x4D545330` |
| `0x04` | VERSION | SIMPLE L1=`0x00030200` |
| `0x08` | MODE | 0 SAFE, 1 SCAN, 2 HOLD, 3 P_LOCK, 4 PI candidate |
| `0x0C` | ENABLE | bit0 |
| `0x10..0x20` | SCAN params/limit | signed14 counts，divider uint32 |
| `0x24` | STATUS | enabled/saturated |
| `0x28` | OUT2_MONITOR | signed14 sign-extended |
| `0x30` | KP | signed14，实际 P gain=`Kp/256` |
| `0x34` | POLARITY | bit0，1=反转 error |
| `0x38` | LOCK_BIAS | signed14 OUT2 count |
| `0x3C` | LOCK_LIMIT | magnitude，最大8191 |
| `0x40` | ERROR_MONITOR | signed14 `laser_error` |
| `0x50` | CORRECTION_LIMIT | magnitude，最大8191 |
| `0x54` | ERROR_SETPOINT | signed14 |
| `0x58` | LOCK_ERROR_MONITOR | signed14 saturated difference |
| `0x60..0x78` | acquisition shadow config | target/guard/directions/limits/generation |
| `0x7C` | CONFIG_VALIDATION | validation bits + write mask |
| `0x80..0xA0` | aligned capture | control/status/decimation/length/index/CH1-4 |
| `0xA4` | ACQ_COMMAND | W1P: 1 ACTIVE, 2 ABORT, 4 clear event, 8 VALIDATE |
| `0xA8` | ACQ_STATE | 0 SAFE,1 SCAN,2 VALIDATING,3 ARMED,4 ACQUIRING,5 P_LOCKED,6 FAILED,7 FAULT |
| `0xAC..0xE0` | event/active config/fault | sticky diagnostic snapshots |
| `0xE4` | L1_CAPABILITY | `0x4C310001` |
| `0xE8` | CROSSING_CONFIG | hysteresis + consecutive samples |
| `0xEC` | KP_ACQUIRE_TARGET | 0 or 4 from normal Host path |
| `0xF0` | KP_RAMP_CONFIG | step + divider |
| `0xF4` | ACQUIRE_TIMEOUT | adc clock cycles；默认0.1 s |
| `0xF8` | SERVO_CONFIG | update divider + OUT2 slew counts |
| `0xFC/0x100` | supervisor config | thresholds/windows |
| `0x104..0x110` | L1 event/metrics | event lock error、validate count、effective Kp、metrics |

协议目前在 RTL 与 Host 中逐项一致，但重复定义本身是未来漂移风险。

---

## 8. SCAN 工作原理

`ramp_generator.sv` 产生 signed14 triangle：

```text
scan = clamp(offset + position, ±OUT2_LIMIT)
position ∈ [-abs(amplitude), +abs(amplitude)]
每 update_div 个 adc clocks 改变 abs(step) counts
```

Host 用近似公式：

```text
update_rate = scan_frequency × 4 × amplitude_counts / step_counts
update_div  = round(125 MHz / update_rate)
```

扫描容易成功，因为它是开环问题：只需数字 ramp、DAC、PZT 和光谱响应存在，不要求 error 具有正确相位，不要求 feedback sign，不要求闭环稳定裕量，也不要求动态扫描点等于静态工作点。

---

## 9. LOCK 工作原理

当前正常 L1 路径不是“鼠标坐标直接变成静态 bias”。鼠标只帮助 Host 在 aligned CH3/CH4 capture 中找到候选零交叉，并生成 OUT2 guard、scan direction、error crossing direction 和 setpoint。FPGA ARM 后继续扫描，等真实 crossing 到达，再捕获当时的实际 `selected_out2` 作为 bias。

这个设计正确地解决了旧路径中的大部分 Host latency/cursor→DAC 映射问题。但它还不能消除：

- 扫描动态状态→静态状态时 PZT/laser 的迟滞与松弛；
- error 的 DC offset/相位漂移；
- 真实模拟 OUT2 节点相对数字 command 的负载效应；
- 错误 polarity 或不合适的 Kp；
- laser mode hop/thermal drift。

更重要的是：**这条新路径尚未上板，不能用旧 `LOCK HERE` 失败来否定它，也不能用 RTL 仿真通过来宣布它已经解决问题。**

---

## 10. 当前真正完成到哪个阶段

| Level | 定义 | 当前证据判定 |
|---:|---|---|
| 0 | ADC/DAC 工作 | 通过（历史硬件） |
| 1 | 可以扫描 | 通过（历史硬件） |
| 2 | 可以观察 spectroscopy | 通过（用户记录） |
| 3 | 可产生物理上适合锁频的 error | **未通过**；代码有、实验定量证据不足 |
| 4 | 可可靠选择目标 zero crossing | GUI/代码候选具备；物理有效性随 Level 3 阻塞 |
| 5 | PZT 可无扰停在目标附近 | 旧路径失败；新 L1 未上板 |
| 6 | 闭合 P-only feedback | 源码/理想仿真有；硬件未证 |
| 7 | 稳定锁住数秒 | 未证 |
| 8 | 自动 relock | 不在当前范围 |
| 9 | 长期稳定 | 未证 |
| 10 | 全自动 | 不在当前范围 |

**系统总体评级：Level 2。** 不能用源码候选能力替代真实系统等级。

---

## 11. 为什么扫描成功但锁定失败

### 11.1 根本差别

扫描只验证 `OUT2 → PZT → spectrum` 的开环可见性。锁定还要求：

```text
正确 error + 正确 target + 正确静态 bias + 正确总符号
+ 合适 gain/bandwidth + 不饱和 + 足够低的延迟/噪声
```

任一条件失败都锁不住。当前只有第一行的一部分被真实硬件证明。

### 11.2 项目特有原因排序

1. **新 L1 没有部署到真实板卡。** 实验体验和当前源码不是同一个系统版本。
2. **error 质量没有形成量化 Gate。** 过去曾记录 OUT1 近零告警，之后虽看到 error 候选，但没有 Vpp/noise/slope/offset/phase 的统一记录。
3. **旧 scan→lock 工作点有实测偏移。** 新 L1 用实时 crossing/bias capture 针对性修复，但尚未硬件验证。
4. **PZT 总符号和动态对象未知。** 数字 polarity 逻辑正确不代表物理闭环为负反馈。
5. **增益/带宽没有从 plant measurement 推导。** Kp=4 很保守，但是否大于噪声和死区、是否足以纠偏未知。
6. **FPGA `P_LOCKED` 判定过短且非持续。** 它可能给 GUI 一个比物理事实更乐观的状态。

---

## 12. SCAN → LOCK 工作点偏移分析

### 12.1 软件/数字原因

- 旧路径可能使用 cursor/capture 时刻与稍后寄存器操作之间的时间差。
- rising/falling branch 混用会把同一谱线映射到不同 OUT2。
- capture generation 过期或通道错位会产生错误 target。
- 旧 bitstream 的 `CAPTURE_LOCK_POINT` 与当前 L1 realtime crossing 语义不同。
- command counts 与 GUI“V”之间使用一次空载经验预补偿，不等于带载节点电压。

当前源码已经针对前四项加入 aligned capture、direction、generation、guard 和实时 crossing；第五项仍是硬件空白。

### 12.2 物理原因

- PZT hysteresis、creep、scan-rate dependence；
- 动态扫频时与静态保持时的 laser thermal/current/PZT 平衡不同；
- mode hop 或目标 transition 改变；
- cable/load/driver input 改变 OUT2 实际节点；
- error DC offset、demodulation phase、光功率变化让 zero crossing 移动。

### 12.3 5–10 分钟区分实验（计划，不是当前 Gate 授权）

在 timing-clean L1 bitstream 完成 H0 后，固定同一 transition、同一 rising branch、Kp=0：同时记录 FPGA event OUT2 count、CH4 数字 capture、示波器 loaded OUT2 node、PD feature。连续做三次 `ARM VALIDATE`（不改变 OUT2）与三次 ACTIVE Kp=0。

- VALIDATE 中 crossing count 本身漂移：光谱/扫描/zero crossing 不稳定，优先查物理与 error。
- VALIDATE 稳定，ACTIVE 时数字 OUT2 首拍跳变：RTL/bitstream/版本或采样对齐问题。
- 数字 OUT2 无跳变，模拟节点跳变：DAC/负载/接线问题。
- 数字和模拟 OUT2 都无跳变，但谱峰移走：PZT hysteresis/creep、热效应或 error zero 与目标 transition 不一致。

这比继续调 GUI cursor 或增加自动寻峰更快地区分软件与物理原因。

---

## 13. Error Signal 审查

### 13.1 已确认

- OUT1 与 servo 内部误差源都来自同一个 `laser_error`。
- mixer 是 signed PD×REF；LPF 会抑制 2f/高频分量。
- 数字路径有饱和保护。

### 13.2 不能确认

- IN1 上是适合直接数字混频的 RF PD signal，还是已经被其他仪器处理过的低频/DC signal。
- IN2 的 4.6 MHz REF 幅度、相位、offset 和终端是否合适。
- 只有单相 mixer，没有 I/Q 或数字 phase shifter；相位只能靠外部 RF/电缆/光路调整。
- 没有 pre-mixer 10 MHz LPF、1.8 MHz HPF/DC removal；实际 alias、DC product 和宽带噪声未知。
- 固定约 4.86 kHz LPF 是否匹配当前 MTS linewidth、scan speed 和 PZT loop bandwidth。
- ADC 是否 clipping，mixer/LPF 是否量化过小或饱和。
- zero crossing 是否对应目标 transition、是否有足够 slope、是否随时间稳定。

结论：

> **当前没有足够实验依据证明 FPGA 得到的是“可用于稳定锁频的误差信号”。代码生成了 error-like signal，但物理资格 Gate 尚未通过。**

最小定量 Gate 应记录同一 branch 上：IN1/IN2 min/max、CH3 Vpp、zero 附近 RMS/MAD、局部 slope `Δerror/ΔOUT2`、DC offset、连续 10 次 crossing count 分布，以及外部 REF phase 小幅变化对线形的影响。

---

## 14. Feedback Polarity 审查

数字控制器中：

```text
POLARITY=0: correction ∝ +error
POLARITY=1: correction ∝ -error
```

若局部 `d(error)/d(OUT2)>0`，负反馈需要 invert；若 slope<0，需要 normal。GUI 的 `initial_polarity_suggestion = 1 if slope>0 else 0` 在数学上正确，而且该 slope 来自同一 aligned ERROR/OUT2 capture，已经包含 DAC/PZT 对 error 的局部符号。

但 GUI 明确“suggestion not applied”，用户可保留默认 normal。并且动态时 plant sign 可能因 branch、mode hop 或接线改变。因此真实总符号仍是：

> **【必须现场实验确认】**

一分钟实验原则（在 H0/H1/H2 通过后、一次只做一个 Gate）：先 HOLD/Kp=0，施加用户批准的 ±1 count 短小步进，观察 `lock_error` 是朝零还是离零；恢复原点并 SAFE。只有方向明确、无异常跳变，才允许选择 polarity。不要用“试两个 polarity 看哪个不爆”作为确认方法。

---

## 15. FPGA 数值范围 / Fixed-point 审查

| 信号 | 物理单位 | FPGA 格式/公式 | 数字范围 | 电压/实验范围 |
|---|---|---|---:|---|
| ADC IN1 PD | V at connector | board format→signed14 | nominal -8192..8191 | 设计假设约±1 V；实际增益/offset/clipping未标定 |
| ADC IN2 REF | V at connector | board format→signed14 | nominal -8192..8191 | 设计假设约±1 V；实际未标定 |
| mixer product | normalized product | signed28，`pd×ref` | 约±67M | 无直接物理 V 单位 |
| mixer output | normalized count | `(pd×ref)>>>13` + sat14 | -8192..8191 | 不是普通电压乘积读数 |
| LPF/error | error count | signed14 一阶 IIR | -8192..8191 | OUT1 可观察；物理 scale 未标定 |
| ERROR_SETPOINT | error count | signed14 | Host限制-8191..8191 | 通常零交叉附近，非电压配置项 |
| lock_error | error count | saturated `(error-setpoint)` | -8191..8191 | 内部 servo 量 |
| Kp | Q8 gain | signed14；gain=`Kp/256` | 正常Host 0/4 | 无量纲 |
| P correction | OUT2 count | `(lock_error×Kp)>>>8` | clamp到±correction limit | 当前物理增量标定使用经验1.18 gain，带载未证 |
| LOCK_BIAS | OUT2 count | signed14，trigger实际 command | -8191..8191 | 空载经验式 `1.13*count/8191+0.009 V`；带载未证 |
| DAC OUT2 command | count | signed14→DAC format | -8191..8191 | 设计约±1 V；当前软件用经验预补偿 |
| actual PZT node | V | 非 FPGA 数字量 | N/A | **未完整测量** |

主要风险：

1. `counts_to_volts()` 有理想 `count/8191` 表示，而 OUT2 GUI 另有经验校准；必须避免把两者混为物理真值。
2. 校准常数 `gain=1.13/1.18, offset=0.009` 没有绑定 board serial、日期、load、coupling、probe ratio 和温度。
3. signed14 的 `-8192` 在多处被主动排除/钳到 -8191，这是安全一致性选择，但文档必须统一。
4. error count 不是经过 ADC/DAC 双向物理标定的 V；把它显示成“ideal equivalent voltage”只能用于诊断，不可当 MTS error 的校准电压。

---

## 16. DAC / PZT / D2-125 实际链路

### 当前有证据的历史链路

```text
GUI → SSH → /dev/mem → CSR → ramp_generator
→ selected_out2 digital count → Red Pitaya OUT2
→（用户报告曾接 loaded PZT 并看到谱线）
```

### 理想 L1 lock 链路

```text
Red Pitaya OUT2
→ 单独连接 laser dedicated PZT/Scan input
→ laser frequency
→ Rb/MTS optics → PD
→ Red Pitaya IN1 + IN2 REF
→ FPGA error/P-only
→ Red Pitaya OUT2
```

D2-125 在理想链路中不承担闭环执行器，也不得把其输出与 OUT2 并联。若现场仍需要 D2-125 的某个输入/监视功能，必须单独画线并确认端口是输入而非有源输出。

---

## 17. 控制环路与带宽分析

| 环节 | 当前可得估计 | 审计结论 |
|---|---:|---|
| MTS modulation | 历史文本约4.6 MHz | 现场频率/phase未记录 |
| mixer sample | 125 MHz | 足够采样4.6 MHz |
| post-mixer LPF | 约4.86 kHz | 固定值；合理性待真实谱线/noise验证 |
| FPGA P pipeline | 约64 ns | 不是主要延迟 |
| servo update | 默认1 MHz | 远高于典型慢 PZT 的有效机械带宽；主要用于数字更新/slew |
| Kp ramp 0→4 | 默认约4 µs | “soft”主要靠1 count/µs OUT2 slew，不等于按PZT时间常数设计 |
| acquisition timeout | 0.1 s | 对扫描 crossing 足够与否取决于10 Hz branch/ARM时刻 |
| supervisor确认 | 约1.024 ms | 只能做短时数字判定，不能证明激光稳定 |
| GUI refresh | config 100 ms，SSH操作更慢 | 正确地不在实时servo loop内 |
| PZT bandwidth | 未知 | 必须实测，当前最重要的 plant 参数之一 |

控制稳定性不能只看 FPGA 64 ns latency。实际 loop phase 由 LPF、PZT driver、PZT/laser mechanics、spectroscopy response、线缆与采样共同决定。当前没有 Bode/step-response 数据，无法客观给出最大 Kp 或闭环带宽。

---

## 18. 最少必须观察的诊断量

第一次闭环不需要九路全部实时画在 GUI。最小 5 项是：

1. PD/目标 spectroscopy feature（确认仍是同一 transition）；
2. `laser_error` 与 `lock_error/error_setpoint`（确认零点、noise、发散）；
3. FPGA `selected_out2`/LOCK_BIAS/correction 数字值；
4. 示波器实际 loaded OUT2/PZT node voltage；
5. MODE/ENABLE/Kp/polarity/saturation/acquisition state/event。

REF 在 error bring-up 阶段必须观察，但在每次锁定画面中可作为工程页诊断。当前缺口不是“大 GUI”，而是 correction 与 loaded analog node 没有被同一实验记录关联起来。

---

## 19. Git 历史：过去时间到底花在哪里

本地历史共有 114 commits，时间集中在 2026-06-14 至 2026-07-28。最近 40 个 commits 中：30 个触及文档/流程，18 个触及 Host code，15 个触及 Host tests，10 个触及 RTL，10 个触及 RTL tests，5 个触及 timing reports，12 个触及 Vivado project/cache；另有 1 个 commit 导入大量开源仓库。由于 commit message 几乎都只是 `Update v94 project code documents and records`，只能主要按 diff 文件分类，提交历史本身不利于实验追溯。

### A. 真正缩短真实锁定距离

- `1abfc74`：OUT2 实测校准层。
- `0f273cd`：L1 realtime ERROR crossing、Host/RTL contract。
- `afe5e2c`：Kp ramp、supervisor、plant test。
- `5b8efd3`：OUT2 pipeline/timing 修复。
- `9ebb3a4`：ramp timing 路径优化。

这些工作直接对应 bias、crossing、P feedback、safety 与可实现性，价值高。

### B. 必要但间接

- `8f459e9`：LocalClient/LockService/AcquisitionService 分层。
- `d435c51`：状态轮询、错误分类、GUI diagnostics。
- 多轮 tests、STATUS、SOP、timing report 收集。

这些提高了可维护性和安全性，但必须由硬件 Gate兑现价值。

### C. 对第一次锁定贡献较低或时机过早

- `a43f004`：大规模导入/阅读开源项目。
- `46b38fe`、`3067d9a` 等：大量 agent/workflow/skill 文档。
- 多套旧/新 UI control、legacy P_LOCK/PI_LOCK/LOCK HERE/APPLY P 路径并存。
- 大量状态标签、诊断字段和审查文档超过了当前可用硬件证据。

客观结论：最近开发并非“完全没有解决闭环”；7月26日前后已经显著转向 crossing/bias/P-control/timing。但整体仍更偏向**提高系统工程完整度和构建防护**，而不是高频率地关闭真实硬件因果链。真正短缺的是每次 RTL/Host 改动后立刻完成一个可复核硬件 Gate。

---

## 20. 为什么优化很久但实验效果变化不大

1. 最近真实实验所用 bitstream 与当前源码能力存在代差。
2. 软件/RTL迭代速度远快于硬件实验、校准和数据归档速度。
3. 过去把“能扫描/能选点/能进入某状态”当作接近锁定，但没有把 error qualification、plant sign、loaded node 和 RMS improvement 设为硬 Gate。
4. 每轮加入更多状态、诊断和自动保护，却没有先获得最小 plant measurement。
5. 文档/版本漂移让不同代路径混在同一 GUI 和同一叙事中。
6. 理想化 plant test 的 actuator 每个仿真 clock 消除一半误差，远快于真实 PZT；它证明逻辑方向和故障分支，不证明真实稳定裕量。

---

## 21. 当前系统是否过度工程化

是，但需要精确区分“有价值复杂度”和“暂时应冻结的复杂度”。

有价值：aligned capture、actual OUT2 bias、limits、SAFE/readback、generation、ERROR crossing、最小 P pipeline。这些直接防止跳峰和失控。

暂时应冻结：

- 约5925行 `main_window.py` 中继续增加状态副本和诊断 UI；
- 约1388行 backend + 1476行带嵌入 helper 的脚本继续复制寄存器语义；
- 2050行 register bank 中继续扩展 D1/PI/event，而当前 L1 尚未上板；
- board server/RPC、自动 relock、AI/IQ、PSD、双执行器；
- 更多 review/agent/workflow 文档。

当前复杂度已经影响调试：同一工程里同时存在旧 manual P_LOCK、PI_LOCK candidate、legacy `CAPTURE_LOCK_POINT/LOCK HERE/APPLY P`、D1 与 L1 SIMPLE；GUI 又保留隐藏/工程入口。第一次锁定期间应只认：

```text
CONNECT → SAFE → SCAN → CAPTURE → CONFIRM
→ ARM VALIDATE → SAFE
→ ARM ACTIVE(Kp=0) → SAFE
→ ARM ACTIVE(Kp=4, user-approved polarity) → SAFE
```

---

## 22. Failure Tree：为什么现在锁不住

```text
没有真实、可重复 P-only lock
├── 当前新闭环根本未在实验台运行
│   ├── L1 bitstream 未生成/加载
│   ├── VERSION/CAPABILITY 未板上确认
│   └── timing/check_timing Gate 未闭合
├── error 不具备锁频资格
│   ├── REF phase/幅度/终端未知
│   ├── 单相 mixer 无数字相位调节
│   ├── ADC clipping、DC offset、量化、噪声未量化
│   ├── 固定4.86 kHz LPF与实际线宽/scan不匹配
│   └── zero crossing并非目标transition或随时间漂移
├── scan crossing 到静态工作点不一致
│   ├── 旧Host/cursor/bitstream路径延迟
│   ├── rising/falling branch差异
│   ├── PZT hysteresis/creep
│   ├── scan-rate→HOLD动态松弛
│   └── 数字OUT2≠loaded node voltage
├── feedback 不是负反馈
│   ├── GUI suggestion未自动应用
│   ├── PZT V→frequency方向未知
│   ├── branch/mode hop改变局部slope
│   └── 实际接线与设计语义不一致
├── feedback 是负的但增益/带宽不合适
│   ├── Kp=4小于噪声/死区
│   ├── Kp过大、PZT共振/延迟导致振荡
│   ├── LPF相位延迟
│   └── correction/absolute/slew limit过紧或撞限
└── 状态显示误导
    ├── supervisor约1 ms即判P_LOCKED
    ├── P_LOCKED后不持续检查error drift
    ├── Host service每次worker重建，GUI仍持有多份状态
    └── 文档/Gate/VERSION描述漂移
```

---

## 23. P0 / P1 / P2 问题排名

### P0 — 不解决就不能客观宣布真实锁定

| 排名 | 当前证据 | 为什么重要 | 怎么验证 | 成功判据 | 层 |
|---:|---|---|---|---|---|
| 1 | setup/hold记录为正，但仍有 unconstrained/no-delay/no-clock；干净0.142 ns报告未在当前工件中找到 | 未约束路径可能掩盖真实硬件时序风险 | 审查XDC与每类endpoint语义，重新生成完整报告 | WNS/WHS≥0、TNS/THS=0、unconstrained=0；I/O例外逐项有依据 | FPGA/XDC |
| 2 | error代码存在；物理资格未证 | 没有合格error，任何Kp都无意义 | scope+aligned capture测Vpp/noise/slope/offset/phase/clipping和10次crossing | 同一transition/branch可重复，零点稳定，局部slope显著高于noise，无clipping | hardware/FPGA |
| 3 | 空载预补偿有记录；loaded node未完整标定，旧LOCK偏移实测 | bias错/节点跳变会直接离开capture range | command/CH4/loaded-node/feature同步A/B | counts一致，Kp=0切换模拟跳变在批准阈值内，feature不跳走 | hardware/Host |
| 4 | 数学polarity suggestion正确；真实总符号未证 | sign错必然发散 | Kp=0附近±1 count小步进确认error恢复方向 | 两个方向结果可重复且唯一决定polarity | hardware/control |
| 5 | 无当前bitstream非零Kp/60s/重复记录 | 这是项目唯一KPI | Kp=4受控闭环，采集before/after与事件/示波器 | error RMS下降、无sat/撞限、60s、至少4/5重复成功 | 全系统 |

### P1 — 首次锁定后优先优化

1. 延长并持续运行 lock-quality monitor；把 `P_LOCKED` 与“60 s hardware verified”严格分开。
2. 用 measured PZT step response/频响设置 servo divider、slew、Kp ladder、supervisor windows，而不是沿用数字默认值。
3. 让一个持久 `LockService` 真正拥有 Host 状态，GUI 只显示 FPGA readback。
4. 单一来源生成 RTL/Python/helper register map。
5. 把 OUT2 calibration 绑定 board/load/date/scope configuration，并分开 command calibration 与 loaded-node calibration。
6. 精简 GUI 正常路径，legacy 操作只留明确的 Engineer/diagnostic 页面。

### P2 — 后续工程化

- board-local service/RPC；
- PI/Ki、lost-lock/relock；
- I/Q或数字phase；
- PSD、双执行器、自动寻峰/AI；
- 长期稳定度、Allan deviation、论文级数据链。

---

## 24. 最小 P-only 锁定系统

真正的最小系统只需要：

```text
ADC(PD, REF)
→ demodulation + LPF
→ error/setpoint
→ sign × Kp
→ captured bias
→ correction/absolute limit
→ DAC OUT2
→ PZT
```

必要的外围只有 SAFE、SCAN、aligned capture、readback 和人工目标确认。当前项目的 L1 data path已经包含这些必要模块；缺的不是新算法，而是 timing-clean deployed artifact 与物理参数/验收数据。

---

## 25. 第一次真实锁定实验 SOP（分阶段计划）

> 下面是 Gate 路线，不是一次性授权。按项目规则每轮只执行一个实验；任何 MAGIC/VERSION、接线、范围、saturation、削顶、跳变、目标或方向异常，立即 SAFE 并停止。

### Test 0 — Timing 与 artifact 身份

- 目的：确保即将上板的是当前 L1，而非旧 build。
- 操作：先固定或重新导出与当前源码对应的完整 timing/check_timing/utilization 工件，再完成 XDC 语义审查；通过后记录 bitstream SHA/日期/VERSION。
- PASS：完整 timing Gate；否则不生成/加载正式测试 bitstream。

### Test 1 — H0 SAFE 与 OUT2 scope-only

- 接线：OUT2只接示波器；PZT断开。记录Hi-Z/50Ω、DC coupling、probe ratio。
- GUI：CONNECT→Probe→SAFE。
- 看什么：MAGIC、VERSION=`0x00030200`、L1 capability、MODE=0、ENABLE=0、OUT2物理值。
- PASS：身份/readback一致、无异常输出。FAIL→停止，不接PZT。

### Test 2 — OUT2 command 标定

- 接线：OUT2→scope only。
- GUI：在批准的小范围内做多个 exact count/HOLD 点，点间SAFE。
- 看什么：command、OUT2_MONITOR、scope mean/min/max。
- PASS：单调、可重复、无clipping，拟合残差满足实验阈值；保存load条件。

### Test 3 — loaded PZT node 标定

- 接线：OUT2单独接laser dedicated PZT/Scan input，同时高阻测节点；确认没有任何有源输出并联。
- GUI：小幅低速SCAN。
- 看什么：loaded node voltage、PD feature、OUT2 count、rising/falling位置。
- PASS：电压范围安全、无异常跳变/削顶，记录两方向同一feature差值。

### Test 4 — error qualification / ARM VALIDATE

- 接线：IN1 PD、IN2 REF均确认范围；OUT1/loaded OUT2上scope。
- GUI：SCAN→aligned capture→同一branch选zero→ARM VALIDATE。
- 看什么：PD、REF、error、OUT2；event generation/direction/count。
- PASS：10次crossing方向和generation正确，crossing OUT2分布小、error无clipping、zero附近SNR/slope满足阈值；VALIDATE不改变OUT2。

### Test 5 — Kp=0 原子切换

- GUI：同一目标/branch，ARM ACTIVE with Kp=0。
- 看什么：最后scan command、captured bias、第一lock command、loaded node、feature位置。
- PASS：数字≤1 count跳变；模拟节点无不可接受jump；feature不明显离开目标；然后SAFE。

### Test 6 — plant sign

- 起点：Test 5通过。
- 操作：HOLD/Kp=0附近做用户批准的±1 count单步；每次恢复并SAFE。
- 看什么：error变化方向和重复性。
- PASS：唯一确定negative-feedback polarity；不自动反转、不进入非零Kp。

### Test 7 — Kp=4 首次闭环

- 起点：用户明确批准polarity和Kp=4。
- GUI：记录至少5 s Kp=0 baseline，再ARM ACTIVE Kp=4。
- 看什么：error mean/RMS、OUT2 correction、saturation、PD feature、loaded node。
- PASS：error向setpoint收敛且RMS下降，无sat/撞限/跳峰；任一发散立即SAFE。

### Test 8 — 60 s 保持

- 操作：保持完全相同参数60 s，不调Kp。
- PASS：全程同一transition，error/actuator满足第26节标准；结束SAFE并重新SCAN确认目标。

### Test 9 — 重复性

- 操作：从SAFE开始完整重复5次，参数和branch固定。
- PASS：至少4/5达到60 s标准；记录每次失败原因，不用最好一次代替统计。

---

## 26. 第一次成功锁定的客观验收标准

单次 H4 成功必须同时满足：

1. 记录 bitstream SHA/date、MAGIC、VERSION、Host commit、接线、scope load/coupling/probe、参数。
2. 选定同一 MTS transition 与同一 scan branch。
3. SCAN→P_LOCK 的数字OUT2首拍差≤1 count；loaded node无实验上不可接受的jump。
4. Kp=4后，在相同长度窗口比较，`lock_error RMS` 相对Kp=0/HOLD baseline至少下降20%，mean更接近setpoint。
5. `saturation=0`，correction峰值不超过limit的80%，不持续贴rail。
6. PD/spectroscopy feature没有离开目标；等效OUT2位置偏移不超过预先记录局部线宽的10%或实验批准阈值（取更严格者）。
7. 连续保持≥60 s，期间不靠人工调bias/Kp/polarity维持。
8. SAFE后重新SCAN，仍能在预期branch找到同一transition，无mode hop证据。

“可靠”还要求从SAFE重复5次至少4次成功。FPGA `P_LOCKED` bit、短于1 s的稳定波形或一次偶然成功都不能单独作为验收。

---

## 27. 后续真正需要修改的 FPGA / Host / Hardware

当前不应立即修改；应由实验结果触发最小变更：

- 若 timing/XDC 不完整：只修正确认有语义依据的约束或最小 timing path。
- 若 error 不合格：先修RF phase/幅度/输入conditioning；只有证据指向数字滤波时才改 mixer/LPF。
- 若数字无扰但模拟节点跳：修接线/load/output stage/calibration，不先改GUI。
- 若 sign确认但Kp=4无效：先测plant step response，再调整Kp/servo/slew。
- 若短时锁住后漂失：增加持续lock-quality monitor；PI只能在P-only H4之后进入新Gate。
- 若Host状态冲突：把worker生命周期与持久LockService统一，不重写整套GUI。

### 暂时不要做

PI/Ki、auto relock、AI/CNN、automatic peak recognition/tuning、IQ重构、PSD、双执行器、board server、大规模GUI美化、更多多Agent/报告系统。

---

## 28. 我现在必须重新掌握的知识

### 激光稳频

- spectroscopy feature、MTS产生机制、demodulation phase；
- error zero crossing、局部slope、capture range；
- P控制的负反馈符号、增益、稳定裕量；
- PZT hysteresis/creep/resonance与thermal drift；
- “找到工作点”“闭合反馈”“持续稳频”三种不同证据。

### FPGA

- Red Pitaya ADC/DAC signed14与板卡极性；
- `pd×ref>>>13`、IIR `1/4096`、`Kp/256`；
- saturation、absolute/correction/slew limit；
- adc clock、DAC forwarded clock与XDC I/O timing；
- aligned capture、CSR/W1P、pipeline latency、版本/bitstream身份。

### 实验

- 用scope记录load/coupling/probe与真实节点，而不只看GUI voltage；
- 量化error Vpp/noise/slope/offset/clipping；
- 用小步进判断plant sign；
- 区分数字command跳变、模拟node跳变和PZT物理松弛；
- 用before/after RMS、rail margin、持续时间和重复率验收。

---

## 29. 7天重新进入项目计划

| 天 | 学习 | 实际产出 |
|---:|---|---|
| 1 | 只读AGENTS/Gate/STATUS、本报告；画当前接线 | 一张现场线缆图，逐端口标输入/输出/范围/load |
| 2 | 复习ADC/DAC signed14、register map、SAFE/SCAN | 手写一页counts↔V与关键CSR速查表 |
| 3 | 复习mixer、phase、LPF、MTS error | 能用scope解释PD/REF/mixer/error每一路 |
| 4 | 复习P-only、sign、PZT hysteresis/step response | 设计±1 count sign测试和停止条件 |
| 5 | 完成当前唯一Gate：XDC/check_timing语义审查 | 可复核timing包；未通过则不进硬件 |
| 6 | 若Gate通过，仅做H0或下一单一硬件Gate | 一份带bitstream身份和scope条件的实验记录 |
| 7 | 复盘证据，不加功能 | 更新一张evidence matrix和唯一下一实验 |

如果第5天未通过 timing，后两天继续约束/报告审查，不提前烧录或试锁。

---

## 30. 给老师汇报的一页总结

### 目标

用 Red Pitaya FPGA 从PD和4.6 MHz REF生成MTS error，并由OUT2直接驱动激光器专用PZT输入，实现最小P-only稳频。

### 已完成

- 已能用GUI控制Red Pitaya OUT2扫描并观察光谱。
- FPGA已有mixer、LPF、aligned capture、SCAN/SAFE、实时zero-crossing acquisition、actual OUT2 bias capture、P-only、限幅和故障SAFE。
- Host已有选点、版本检查、状态/readback和安全流程。
- 软件测试通过；RTL已有系统仿真和理想plant仿真记录。

### 未完成

- 当前新L1 bitstream尚未形成完整timing-clean、可复核并上板的工件。
- 尚未定量证明error signal适合锁频。
- 尚未确认带载OUT2/PZT映射和总feedback sign。
- 尚未完成Kp=0无扰、Kp=4 error改善、60 s和重复性实验。

### 过去为什么做了很多但实验变化不大

大部分进展发生在代码、测试、GUI、安全和文档层；真正的硬件闭环证据没有跟随每轮代码推进。实验台最后确认的仍主要是旧版本扫描与选点能力。

### 下一步

先完成XDC/check_timing Gate；随后严格按身份→空载输出→带载节点→error qualification→Kp=0→sign→Kp=4→60 s的单实验路线推进。首次P-only完成前停止PI、AI、自动重锁和GUI扩展。

---

## 31. 最后10个问题

1. **当前系统现在究竟能做什么？** 旧硬件能安全扫描和观察谱线；当前源码还能完成aligned capture、实时ERROR crossing和FPGA P-only候选闭环。
2. **当前系统究竟不能做什么？** 不能用现有证据证明当前build已在真实激光上稳定、重复锁定。
3. **有没有证据证明FPGA真正锁过激光？** 没有可接受的当前证据。
4. **最关键缺失是什么？** 同一已识别bitstream下，从合格error、带载PZT、正确sign到Kp=4/60 s的完整实验数据链。
5. **最大瓶颈是FPGA、上位机、算法、接线还是实验方法？** 当前首要是部署/timing Gate与实验方法/物理链路证据，不是缺新算法；具体物理瓶颈要由error和plant实验区分。
6. **为什么优化很久但实验感觉一样？** 新能力没有通过新bitstream和逐Gate实验落到台面，很多时间用于工程完整度而非关闭物理因果链。
7. **上位机是不是太复杂？** 是；正常路径之外保留了过多legacy状态和操作，但这不是第一锁失败的唯一根因。
8. **FPGA是否具备最小P-only所需功能？** 从当前源码和仿真看基本具备；从可部署、真实硬件证据看尚未具备“已证明可用”的资格。
9. **如果明天只能做三个实验，做哪三个？** 当前Gate下不能直接做三个硬件实验；先完成XDC/timing审查。通过后依次做H0身份/SAFE、loaded OUT2节点标定、ARM VALIDATE error/crossing资格。
10. **距离第一次可靠P-only lock的最短路径？** 冻结新功能→timing-clean L1 bitstream→H0/H1 error与loaded-node证据→Kp=0无扰→小步进确认sign→用户批准Kp=4→60 s→5次重复。

---

## 32. 审计结论与唯一下一动作

本项目的主要不足不是“完全没有闭环代码”，而是**源码、bitstream、接线、物理对象和验收数据没有处在同一个证据闭环中**。7月末的L1实现方向总体正确：它把旧Host/cursor式锁点升级为FPGA实时ERROR crossing和actual OUT2 bias capture，正面解决了最痛的scan→lock偏移问题。但在当前时刻，它仍是未经硬件证明的候选系统。

本轮未修改RTL、Host、XDC、Vivado工程、bitstream、`STATUS`、`CURRENT_GATE` 或manifest；只新增本审计报告并运行Host tests。

**用户唯一下一步：固定并提供与当前源码对应的完整 Vivado timing/check_timing 报告；若现有 0.142 ns 摘要没有原始工件，则重新导出或重新运行。之后再授权一次只读 XDC 语义审查，逐项处理或解释 unconstrained/no-delay/no-clock 项；完整 Timing Gate 通过前不要生成或烧录正式 bitstream。**
