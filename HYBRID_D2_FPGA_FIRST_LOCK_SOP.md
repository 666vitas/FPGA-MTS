# HYBRID_D2_FPGA_FIRST_LOCK_SOP — 保留 D2-125 电流快环 + FPGA PZT 慢环，实现第一次锁定

> 生成日期：2026-08-30
> 适用版本：`E:\new\fpga_lock\v94`，`VERSION=0x00030200`（LOCK-MVP-L1 / SIMPLE）
> 目标读者：FPGA 稳频学习者（初级经验，RedPitaya STEMlab 125-14 / Zynq-7010）

---

## 0. 本轮唯一目标（强制约束）

**不再以「Red Pitaya 完整替代 D2-125」为目标。**

当前唯一目标：

1. 保留 D2-125 的激光电流快反馈环（**不碰**）；
2. Red Pitaya FPGA 只接管四件事：
   - PZT 扫描（SCAN）
   - 过零采集（zero-crossing acquisition）
   - 锁定偏置（lock bias）
   - P-only 慢速 PZT 反馈
3. 实现**第一次 FPGA-assisted laser lock**，即使只能稳定 5–10 秒也成立。

明确**不做**：长期稳定、PI、自动 relock、AI、双执行器 FPGA、电流快环替换、先重构 GUI。

分析必须贯穿完整链路：**代码 → Red Pitaya → 模拟电气 → 接线 → PZT → Laser → MTS Error**。

---

## 1. 当前真实 D2-125 接线（Section 1）

当前实验接线为：

```
PD → BPF → amplifier → analog mixer RF
Signal Generator CH2（约 4.6 MHz）→ analog mixer LO
analog mixer output（MTS 误差 e_A）→ D2-125 Error Input
D2-125 Main Servo Output → Laser Current feedback
D2-125 AUX Servo Output → Laser PZT / Scan input
```

其中 Main Servo 只驱动激光电流快反馈；AUX 只驱动 PZT / Scan input。不存在
Main Servo Output 通过 BNC T 同时驱动 Current 和 PZT 的连接。

---

## 2. 新接线方案（Section 2）＋ 接线图

改造后分工：**D2-125 只保留电流快环；PZT 全部交给 Red Pitaya FPGA。**

```
                    ┌───────────────────────────────────────────────────┐
   PD ──→ BPF ──→ amplifier ──┬──→ analog mixer RF
                              └──→ Red Pitaya IN1（FPGA 数字解调 e_D）
   Signal Generator CH2（约 4.6 MHz）
                         ├──→ analog mixer LO
                         └──→ Red Pitaya IN2（FPGA 混频参考）
   analog mixer output ───────→ D2-125 Error Input（电流快环误差 e_A）

   D2-125 Main Servo Output ──→ Laser Current feedback（仅此一路，保持不变）
   D2-125 Aux Servo Output → 【断开】（见 §3）

   Red Pitaya OUT2 ──→ 原 D2 AUX 所接的同一个 Laser PZT / Scan input
   Red Pitaya OUT1 ──→ 示波器 CH（观察数字误差 e_D，可选）

   示波器：
     CH1 = 模拟 Mixer 输出 e_A（对比用）
     CH2 = Red Pitaya OUT1 = e_D（数字误差）
     CH3 = Red Pitaya OUT2 = PZT 命令
     CH4 = D2-125 监控 / 电流调制监视（可选）
```

关键接线确认（两条都必须满足）：

| # | 操作 | 原因 |
|---|------|------|
| 1 | 确认 D2 Main Servo Output 只接 Laser Current feedback，并保持该快环不变 | 防止误把 Main Servo 当作 PZT 驱动 |
| 2 | D2 AUX Servo Output 从 Laser PZT / Scan input 物理断开后，才把 Red Pitaya OUT2 接到该同一输入 | 严禁 D2 AUX 与 FPGA OUT2 同时驱动 PZT |

---

## 3. D2 Aux Servo Output 的处理（Section 3，A/B/C/D 选择）

首轮实验**必须断开** Aux Servo Output→Scan。断开后该 BNC 口的四种去向：

- **A. 50Ω 端接**：最干净，D2 内部不会空载，但看不到信号。适合只做 FPGA 锁定。
- **B. 接到示波器监视**（推荐）：观察 D2 是否仍在输出扫描（确认确实断开/关闭了 Aux 扫描输出）。
- **C. 接外部调制输入**：本轮不需要。
- **D. 悬空**：不推荐，可能引入噪声/反射。

**推荐 B（示波器监视），确认 D2 扫描输出确实不再影响 PZT。** 若 D2 有软件开关可关闭 Aux 输出，优先软件关闭再物理断开。

---

## 4. 误差信号共享：e_A（模拟） vs e_D（数字）（Section 4）

当前系统里其实存在**两条物理上相同、实现上不同**的 MTS 误差：

| | 信号 | 路径 | 谁在用 |
|---|------|------|--------|
| e_A | 模拟误差 | 外部 Mixer（PD×REF + LPF）→ D2 Error Input | D2-125 电流快环 |
| e_D | 数字误差 | Red Pitaya IN1(PD) × IN2(REF) → FPGA mixer → LPF IIR | FPGA PZT 慢环 |

关键结论（基于 RTL 实读）：

- Red Pitaya 当前位流**只产生 e_D**（`laser_lock_core` 的 `error_o = mixer(IN1×IN2) + LPF`），OUT1 输出 `laser_error`，OUT2 输出 PZT 命令 `selected_out2`。
- **没有运行时寄存器能把 FPGA 切到「外部模拟误差」。** 想让 FPGA 用 e_A（Plan A 的 IN1 直通），必须改编译期 `LASER_LOCK_OUTPUT_MODE 3→0`（IN1 直通）→ 重新综合 → 生成新位流。
- 因此：**首轮实验天然是「两条解调链并存」**——e_A 喂 D2 电流环，e_D 喂 FPGA PZT 环。这不需要改任何固件。

---

## 5. Plan A（共享模拟误差） vs Plan B（两条解调链）（Section 5）

**结论：首轮选 Plan B。**

| | Plan A：共享模拟误差 | Plan B：两条解调链 |
|---|----------------------|--------------------|
| 做法 | 把 e_A 分路给 D2 与 Red Pitaya IN1，FPGA 走 IN1 直通 | e_A 给 D2；e_D 由 FPGA 自己混频解调 |
| 需要的固件改动 | **改 `LASER_LOCK_OUTPUT_MODE=0` → 重新综合 → 新位流** | **无**（当前代码原生支持） |
| 额外模拟硬件 | 需要把模拟 Mixer 输出做阻抗匹配分路 | 无（PD、REF 各并一根到 Red Pitaya） |
| 误差一致性 | e_A 与 D2 完全同源，零偏置 | e_D 与 e_A 是同一物理信号的两次解调，**解调相位/增益不同会引入 DC 偏置** |
| 风险 | 浪费 FPGA 已建好的解调链；引入额外模拟分路噪声 | 两个误差零点的频率位置可能略有偏差 |

Plan B 的唯一风险（e_D 与 e_A 解调相位差 → 零点偏移）用 §13 Stage 1 在示波器上直接比对 CH1(e_A) 与 CH2(e_D) 的过零点即可消除/确认。

---

## 6. 电气分路分析（Section 6）

因为选 Plan B，**不需要对误差信号做任何分路**。需要关注的电气点只有三处：

1. **PD / REF 分路**：PD、REF 各并一路到 Red Pitaya IN1/IN2。Red Pitaya 模拟输入阻抗约 1MΩ（Hi-Z），并联基本不加载原来的 50Ω 解调链路。`[NEED_FIELD_CONFIRMATION]`：确认 PD/REF 信号幅度落在 Red Pitaya 输入范围（±1V 标称，满量程 ±20V 档可调）内。
2. **OUT2 → PZT 驱动器**：Red Pitaya 快模拟输出标称 ±1V。`[NEED_FIELD_CONFIRMATION]`：PZT 高压驱动器的**输入阻抗**（50Ω 还是 Hi-Z）与**满量程输入电压**（±1V in = 满 PZT 行程？还是 ±10V？）。OUT2 输出阻抗约 50Ω，直接驱动 Hi-Z PZT 驱动器没问题。
3. **D2 Main Servo Output → Laser Current feedback**：保持当前独立快电流反馈连接不变；本轮不改线、不替代。

---

## 7. 最小 FPGA 架构审查（Section 7）

已通读 `red_pitaya_top.sv`、`laser_lock_core.sv`、`mixer_core.sv`、`lpf_core.sv`、`ramp_generator.sv`、`simple_lock_acquisition.sv`、`out2_lock_controller`（在 `custom_register_bank.sv` 内）、`error_setpoint_corrector`、`realtime_error_crossing_detector`、`l1_kp_ramp`、`l1_lock_supervisor`。最小锁定路径完整存在：

```
IN1(PD) ─┐
          ├→ mixer(pd×ref>>>13, sat14) → LPF IIR(>>12, fc≈4.86kHz) → laser_error
IN2(REF)─┘                                        │
                                                  ├→ error_setpoint_corrector: lock_error = laser_error − error_setpoint
                                                  │
OUT2 命令源：out2_lock_controller（按 MODE 选择）│
   MODE_SCAN   → control_o = scan（三角波）
   MODE_P_LOCK → control_o = LOCK_BIAS + Kp/256 × lock_error（带 correction/absolute/slew 三级限幅）
   MODE_SAFE   → control_o = 0
```

**P-only 数学（out2_lock_controller，已核实）**：

```
s1: signed_error = polarity ? −error : error
s2: p_product    = signed_error × kp            // 29-bit
s3: p_term       = p_product >>> 8               // 增益 = Kp/256
s4: correction   = clamp(p_term, ±correction_limit)   // 默认 128
s5: raw          = LOCK_BIAS + correction
s6: target       = clamp(raw, ±lock_limit)             // 默认 8191
out: control_o   = slew_limited(control_o → target, out2_slew_limit=1)
```

**Kp=0 ⇒ s2=0 ⇒ correction=0 ⇒ OUT2 = LOCK_BIAS**（纯偏置保持）。这从电路上保证了 Kp=0 实验成立。

**LOCK_BIAS 来源**：过零触发时，FPGA 原子地捕获**触发时刻真实的 OUT2 命令**（`trigger_out2_sample`），不是鼠标坐标。这消除了 scan→lock 的偏置跳变（bumpless）。

---

## 8. OUT1 用途（Section 8）

OUT1 当前固定输出 `laser_error = e_D`（数字误差监视）。

首轮实验用途：**接到示波器，作为 e_D 的直接监视**，与模拟 Mixer 输出 e_A 对比过零点。这正是你需要的「观察 error」。

（历史遗留：`laser_lock_core` 有编译期 `OUTPUT_MODE` 参数，0=IN1 直通/1=IN2/2=raw mixer/3=mixer+LPF，当前顶层固定 =3。OUT1 始终是解调链输出，不是可运行时切换的模拟监视。）

---

## 9. SCAN → LOCK 审查（Section 9）

已核实：OUT2 **原生同时支持 SCAN 与 LOCK**（同一个 `out2_lock_controller` 按 MODE 二选一）。

SCAN→LOCK 过渡是无缝的：

1. SCAN 时 OUT2 = 三角波；
2. 过零检测到目标（方向/窗口/过零方向三条件，迟滞 H=4，连续 N=3 个采样）；
3. 触发瞬间把**当前 OUT2 值**锁存为 `LOCK_BIAS`；
4. 原子切 `MODE=P_LOCK`，Kp 从 0 起 ramp 到 `kp_acquire_target`（默认 4）；
5. 因为 LOCK_BIAS 就是触发时刻的 OUT2，**Kp=0 时 OUT2 不跳变**。

结论：**Q4 = 是**，OUT2 一路即可完成 SCAN 与 PZT LOCK，无需额外硬件。

---

## 10. Kp=0 实验设计（Section 10）

目的：在不引入任何 PZT 反馈的前提下，验证「电流快环 + 冻结的 PZT 偏置」能否把激光维持在线型上。

操作序列（GUI 全程）：

1. SCAN → Capture Waveform → 在 CH3(error) 上点击并 Confirm 目标过零点；
2. **ARM BASIC LOCK，Kp=0**（GUI 只允许 0 或 4，选 0）；
3. FPGA 检测到过零 → 锁存 LOCK_BIAS → 进入 MODE=P_LOCK，**OUT2 恒定 = LOCK_BIAS，无反馈**；
4. 观察示波器：若激光被电流环钉在锁定点，且 OUT2 恒定不变 → Kp=0 保持成功。

**Kp=0 成功的物理含义**：电流快环独立维持锁定，PZT 只是被冻结在正确电压。这已经是「第一次 FPGA-assisted lock」的第一块里程碑。

---

## 11. D2 快环 与 FPGA PZT 慢环的相互作用（Section 11）

这是快/慢双执行器的经典分频（coarse/fine，slow/fast）：

- 电流环带宽 ~MHz，负责压掉激光频率的**快速抖动**（包括 MTS 解调带宽内的噪声）；
- PZT 环带宽 ~sub-kHz，负责把激光频率的**慢漂移/DC 偏置**拉回，让电流环始终工作在它输出范围的中间附近，不饱和。

**为什么两者不会打架**：

1. **PZT 是 P-only，没有积分器** → 它不会像电流环的积分器那样把 DC 误差「抢」到零。PZT 只提供一个比例「弹簧」，留一个有限 DC 误差给电流环积分器去消除——这正是正确的分工。
2. **带宽分离** → PZT 环的伺服更新 `servo_update_div=125`（约 1 MHz 伺服节拍）+ 小 Kp + slew 限幅 1 count/节拍，天然慢。它跟不上电流环正在压制的快扰动，不会形成对抗。
3. 若两个环同时有大积分器，才会在低频互相争夺、windup、慢振荡——本轮 FPGA 明确没有积分器，故无此风险。

---

## 12. P-only vs 慢积分器（slow-I）（Section 12）

**首轮：P-only。**

理由（三条）：

1. 电流环已经承担了「把误差积到零」的职责；PZT 再加积分器就是两个积分器抢同一个 DC 误差，会 windup/慢振荡。
2. PZT P-only 给的是「DC 偏置 + 比例归位」，它允许存在一个有限稳态误差，这个误差正好由电流环消化。
3. 当前 RTL 只实现了 P-only（`out2_lock_controller` 无 I 项），P-only 是零改动路径。

slow-I 只在「电流环明显饱和、需要把 DC 完全卸给 PZT」时才需要——本轮明确不做。

---

## 13. 分阶段实验（Stage 0–6）（Section 13）

### Stage 0 — SAFE 自检（不接 PZT）
- 目标：确认位流加载正确、寄存器可读写、OUT2=0。
- 操作：GUI `Probe Registers` 确认 `MAGIC=0x4D545330`、`VERSION=0x00030200`；`SAFE` 确认回读 `SAFE CONFIRMED`；示波器确认 OUT2≈0V。
- 通过判据：MAGIC/VERSION 正确，OUT2=0，PZT 无动作（此时 PZT 可不接）。

### Stage 1 — SCAN + 误差观察（不接 PZT 驱动，或 PZT 打小范围）
- 目标：确认 e_D（OUT1）能看到清晰的 MTS 过零点，且与 e_A（模拟 Mixer）过零点对齐。
- 操作：接 PD/REF；`SCAN`（小幅度，PZT safe range 内）；`Capture Waveform`；示波器对比 CH1(e_A) 与 CH2(e_D=OUT1)。
- 通过判据：e_D 有明确异号夹住的过零点；e_D 与 e_A 过零点位置基本重合（若有固定偏置，记录之）。
- `[NEED_FIELD_CONFIRMATION]`：若 e_D 与 e_A 过零点明显不重合，需检查 REF 到 IN2 的相位/幅度、数字 LPF 相位。

### Stage 2 — ARM VALIDATE（只记录，不锁定）
- 目标：验证过零检测/锁存逻辑在真实误差上工作。
- 操作：点击 Confirm 目标过零点；`ARM VALIDATE`；FPGA 留在 SCAN、只记录触发事件。
- 通过判据：GUI 显示 VALIDATE 接受、记录到一次 crossing 事件与 `out2_counts`。

### Stage 3 — ARM BASIC LOCK Kp=0（首次 bias 保持）
- 目标：**第一次 FPGA-assisted 保持**。OUT2 冻结在 LOCK_BIAS，激光由电流环维持。
- 操作：`ARM BASIC LOCK` Kp=0；观察示波器 CH3(OUT2) 应恒定、CH1(e_A)/CH2(e_D) 应保持在线型附近。
- 通过判据：OUT2 不跳变（bumpless）；误差保持在线型 ≥5 秒。

### Stage 4 — APPLY P 小 Kp（P-only 慢反馈）
- 目标：加入 P-only 慢 PZT 反馈，验证慢漂移被拉回。
- 操作：`APPLY P`，Kp=4 → 8（每档观察）；确认 polarity 正确（`_confirm_pending_lock_point` 已给 initial polarity suggestion）。
- 通过判据：误差在锁定点附近，PZT 缓慢补偿漂移，不振荡；锁定持续 ≥5 秒。

### Stage 5 — 有扰动的短稳测试
- 目标：人为轻微扰动（轻推桌面/微调电流偏置），确认两环协作不散。
- 通过判据：扰动后自动回到锁定点；OUT2 缓慢变化吸收漂移。

### Stage 6 — 记录与复现
- 目标：复现 3–5 次，确认可重复；记录 Kp、polarity、LOCK_BIAS、error_setpoint。
- 通过判据：同一组参数可重复进入锁定。

---

## 14. 首次成功的定义（Section 14）

**里程碑 M1（Kp=0 bias 保持）**：Stage 3 达成——OUT2 冻结在 LOCK_BIAS、激光被电流环钉在线型、保持 ≥5 秒。

**里程碑 M2（P-only 慢反馈锁定）**：Stage 4 达成——Kp=4/8 的 P-only 慢 PZT 反馈下，激光保持锁定 ≥5–10 秒，且 PZT 在缓慢补偿漂移而非振荡。

**本轮「成功」= M2**。M1 是必经的中间检查点。

---

## 15. GUI 能力审查（Section 15）

**结论：当前 GUI 已完整支持首轮实验所需的全部 12 项能力，不需要改。**

| 你需要的能力 | GUI 现成控件 | 状态 |
|-------------|-------------|------|
| SAFE | `SAFE` 按钮 / `ABORT / SAFE` / `UNLOCK / SAFE` | ✅ 已有，回读确认 SAFE CONFIRMED |
| SCAN | `SCAN` 按钮（safe range 校验） | ✅ 已有 |
| Capture | `Capture Waveform` / `Capture Once` / `Start Live` / `Stop Live` | ✅ 已有 |
| 选择 zero crossing | `Select Target Transition` 勾选 + 点击 CH3/error + `Confirm Lock Point` | ✅ 已有（低幅量化过零选择，2026-07 完成） |
| ARM VALIDATE | `ARM VALIDATE` 按钮 | ✅ 已有 |
| Kp=0 ACTIVE | `ARM BASIC LOCK`（Kp 只允许 0/4）| ✅ 已有 |
| 查看 LOCK_BIAS | `captured lock_bias: -- counts / -- V calibrated` 标签 | ✅ 已有 |
| 设置 polarity | `custom_polarity`（normal / invert） | ✅ 已有 |
| 设置很小 Kp | `Kp manual step`（0/4/8/16/32） | ✅ 已有 |
| 观察 error | Capture CH3 = laser_error | ✅ 已有 |
| 观察 OUT2 | Capture CH4 = selected_out2 | ✅ 已有 |
| ABORT / SAFE | `ABORT / SAFE` 按钮（先禁止输出再清状态） | ✅ 已有 |

**不阻塞首轮实验的 GUI 改动：无。** 真正阻塞的是固件/硬件（§16）。

---

## 16. 真正阻塞第一次实验的最小修改清单（Section 16）

按优先级排序：

| # | 阻塞项 | 类型 | 是否改代码 |
|---|--------|------|-----------|
| 1 | **生成 `VERSION=0x00030200` 候选位流，并由用户在 H0 加载** | 固件部署 | 否（Codex 只离线生成，不连接或写入板卡） |
| 2 | **确认 D2 Main Servo Output 只接 Laser Current feedback** | 接线确认 | 否 |
| 3 | **断开 D2 AUX Servo Output → Laser PZT / Scan input** | 接线 | 否 |
| 4 | PD/REF 并线到 Red Pitaya IN1/IN2 | 接线 | 否 |
| 5 | OUT2 → PZT 驱动器 | 接线 | 否 |
| 6 | 确认 PD/REF 幅度在 IN1/IN2 量程内 | 现场确认 | 否 |

**GUI 不需要任何修改。RTL 不需要任何修改**（Plan B 是当前代码原生路径）。

关于阻塞项 #1 的诚实说明：`STATUS.md`（2026-07-28）记录 2026-07-26 的 clean 综合/布线已通过（`WNS=0.142ns`、`All user specified timing constraints are met`），但 bitstream 标为 `[NOT VERIFIED]`；`check_timing` 仍有 19 个未约束内部端点、17 个 no-input-delay、42 个 no-output-delay（I/O 时序项）。**I/O 时序未约束不阻塞功能自检**，但正式生成位流前建议先确认这些项的真实接口语义。`[NEED_FIELD_CONFIRMATION]`：当前是否已存在新位流、板卡是否已连接。

---

## 17. 8 个必答问题（Section 17）

**Q1 — 保留 D2 电流环 + FPGA 只做 PZT，控制上可行吗？**
可行（有条件）。这是标准的快/慢执行器分频。条件：两环带宽充分分离（电流 MHz、PZT sub-kHz），且 FPGA PZT 是 P-only（无积分器，不与电流环积分器争夺 DC）。当前 RTL 满足这两个条件。

**Q2 — D2 Main Servo Output 本轮如何处理？**
保持只接 Laser Current feedback，不改线、不替代。当前真实架构不存在 Main Servo Output 到 PZT 的分支；PZT 冲突检查针对 D2 AUX Servo Output 与 Red Pitaya OUT2。

**Q3 — 首轮必须断开 D2 Aux Servo Output → Scan 吗？**
必须。否则 D2 扫描与 FPGA OUT2 扫描同时驱动 PZT Scan 输入。断开后建议接示波器监视（§3 方案 B）。

**Q4 — FPGA OUT2 能同时做 SCAN 与 PZT LOCK 吗？**
能。`out2_lock_controller` 按 MODE 二选一，SCAN→P_LOCK 通过锁存触发时刻的 LOCK_BIAS 实现无缝切换（§9）。已核实，无需额外硬件。

**Q5 — D2 与 FPGA 该共享同一 MTS 误差吗？**
首轮不要强求共享。当前固件只能产生数字误差 e_D（OUT1=laser_error），没有运行时切到模拟误差的寄存器；要共享 e_A 必须改编译期 `OUTPUT_MODE` 并重新综合。**首轮采用 Plan B：e_A 喂 D2、e_D 喂 FPGA，两条解调链并存，零固件改动**（§5）。

**Q6 — 首轮保留外部模拟 Mixer 吗？**
保留。它是 D2 电流环的误差源（e_A），必须保留。FPGA 的数字解调是并行的第二条链（e_D），两者共存、各喂各的环。不要拆 Mixer。

**Q7 — D2 快环开着时，FPGA PZT 用 P-only 合理还是慢积分器？**
P-only。原因：电流环已有积分器把误差积到零，PZT 再加积分器会 windup/低频对抗；PZT P-only 只做 DC 归位与比例修正，留有限稳态误差给电流环。当前 RTL 只有 P-only，零改动。（§12）

**Q8 — 从现状到第一次 5–10s 锁定的最短路径？**
按顺序：① 生成候选位流并由用户加载 → ② 保持 Main Servo→Current，断开 AUX→PZT 后再接 OUT2→同一 PZT/Scan input，并接入 PD/REF → ③ Stage 0 自检 → ④ Stage 1 SCAN 看误差过零 → ⑤ Stage 2 ARM VALIDATE → ⑥ Stage 3 ARM BASIC LOCK Kp=0（首次保持）→ ⑦ Stage 4 APPLY P 小 Kp（P-only 慢反馈）。GUI 与 RTL 均不改。（§13、§16）

---

## 18. 工作原则与未知项清单（Section 18）

工作原则（遵从上轮约束）：不替代 D2、不碰 current loop、不加 AI、不加复杂 PID、不先重构 GUI、不猜硬件规格。

### 未知项（需现场确认，绝不假设）

1. `[NEED_FIELD_CONFIRMATION]` PZT 高压驱动器：输入阻抗（50Ω/Hi-Z）、满量程输入电压（OUT2 标称 ±1V 对应 PZT 多大行程）。
2. `[NEED_FIELD_CONFIRMATION]` PD / REF 信号幅度是否落在 Red Pitaya IN1/IN2 量程（±1V 标称）内；REF 到 IN2 的相位/幅度是否需要匹配数字解调。
3. `[NEED_FIELD_CONFIRMATION]` e_D（OUT1）与 e_A（模拟 Mixer）的过零点是否重合；若不重合，量化其偏置。
4. `[NEED_FIELD_CONFIRMATION]` D2-125 是否可软件关闭 Aux Servo Output 扫描（优先软件关再物理断）。
5. `[NEED_FIELD_CONFIRMATION]` 当前候选 `VERSION=0x00030200` 位流是否已生成，以及用户是否已在 H0 加载；生成记录不能替代板上身份 readback（§16 阻塞项 #1）。
6. `[BLOCKED_BY_HARDWARE_SPEC]` 若 D2 电流环带宽或 PZT 驱动器带宽未知，Stage 3/4 的带宽分离只能按「先小 Kp、逐档试」的保守方式推进。

### 一句话结论

**保留 D2 电流快环 + FPGA PZT 慢环的混合锁定，在现有代码与 GUI 上无需任何改动即可开始**；唯一真正的拦路虎是「候选位流是否生成并由用户加载」以及「确认 Main Servo 只接 Current、AUX 与 OUT2 不并联、OUT2/PD/REF 接线正确」。按 Stage 0–6 推进，第一次 5–10 秒锁定（Kp=0 bias 保持 → P-only 小 Kp）即可达成。
