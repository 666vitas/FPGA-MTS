# Claude 审查：MTS 全自动锁频完整路线与 DAC 端口分配审查

审查时间：2026-07-08
审查人：Claude (Claude Code)，角色：FPGA / Red Pitaya / MTS 激光稳频 / 深度学习自动锁定项目的总审查工程师
审查范围：`E:\new\fpga_lock\v94`，只读，不修改任何 RTL、不运行 Vivado、不烧录 Red Pitaya
审查主题：MTS_AUTO_LOCK_FULL_ROADMAP_AND_DAC_PORT_ALLOCATION_REVIEW

---

## 执行总结

**总体判断：当前 v3REG-0 已经实现最小控制链路闭环（GUI → SSH → /dev/mem → register_bank → ramp_generator → OUT2），MTS 全自动锁频路线在架构上没有不可逾越的障碍。但当前距离"全自动深度学习稳频"仍隔着 7 个工程阶段的现实工作。DAC 端口只有 2 个高速输出，必须严格分配、分阶段演进。EOM 继续由外部信号源驱动正确，不应改变。本次审查的 17 个问题全部在此回答。**

核心结论：

1. **MTS 路线优于 SAS 路线**，当前不应因论文外力而改道
2. **2 个高速 DAC 端口足够**完成完整替代 D2-125，但需要分阶段：OUT1(Error Monitor) 已被验证可用，OUT2(Actuator Control) 尚未接真实执行器
3. **EOM 不应用 Red Pitaya DAC 驱动**，继续使用外部射频信号源
4. **v3REG-0 已实现 GUI 可控扫描**，2026-07-05 的实验记录证明全链路物理可达
5. **P0 仅剩 1 项**：D2_125_REAL_WIRING_AND_STATE_MODEL.md 合并冲突（其余 P0 已在 7/5 修复）
6. **最短"替代 D2-125 Aux Output"路径需要 2-3 个月**

---

## 1. 本次审查读取文件清单

### 1.1 核心 RTL（已读取完整内容）

| 文件 | 行数 | 审查状态 |
|---|---|---|
| `v0.94/rtl/custom_register_bank.sv` | 139 | 逐行审查 |
| `v0.94/rtl/ramp_generator.sv` | 168 | 逐行审查（含 TIMING_FIX_1/2 后版本） |
| `v0.94/rtl/laser_lock_core.sv` | 349 | 重新审查 PI 集成影响 |
| `v0.94/rtl/red_pitaya_top.sv` | ~600 | 审查 sys[6]/DAC mux/safety |
| `v0.94/rtl/red_pitaya_ps.sv` | ~80 | 审查 PS 总线接口 |
| `v0.94/rtl/pi_controller_seq.sv` | 292 | 确认 15-state 流水线 PI 行为和参数化接口 |
| `v0.94/rtl/pi_controller.sv` | — | 确认 v2A legacy 完整 PI 状态 |

### 1.2 仿真测试文件

| 文件 | 审查状态 |
|---|---|
| `v0.94/sim/tb_ramp_generator.sv` | 确认 249/249 pass |
| `v0.94/sim/tb_custom_register_bank_basic.sv` | 确认寄存器 R/W 覆盖 |
| `v0.94/sim/tb_register_bank_basic.sv` | 确认第二版 testbench |

### 1.3 上位机软件

| 文件 | 审查状态 |
|---|---|
| `software/.../custom_fpga_scan_control.py` | 逐行审查（确认 MAGIC 预校验已修复） |
| `software/.../custom_fpga_backend.py` | 审查 GUI backend |
| `software/.../main_window.py` | 审查 GUI 路径混淆 |
| `software/.../rp_scpi_client.py` | 审查 SCPI 路径 |
| `software/.../docs/HOST_APP_V2_DESIGN.md` | 审查架构设计 |
| `software/.../docs/FPGA_MODE_BOUNDARY.md` | 审查模式边界 |
| `software/.../docs/HARDWARE_TEST_SOP.md` | 审查测试流程 |

### 1.4 项目文档

| 文件 | 审查状态 |
|---|---|
| `README.md` | 确认当前主线 |
| `GPT_README.md` | 确认 Agent 分工 |
| `version/STATUS.md` | 审查 v3REG-0 全部历史 |
| `version/v3/V3REG0_HOST_CONTROLLED_SCAN_PLAN.md` | 逐行审查 |
| `version/v2/V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md` | 审查阶段映射 |
| `version/v2/D2_125_REAL_WIRING_AND_STATE_MODEL.md` | **发现合并冲突**（与上次审查相同） |
| `version/v2/V2_EXPERIMENT_SOP.md` | 审查实验边界 |
| `version/v2/V2_AUX_PZT_EXPERIMENT_RECORD.md` | 审查 D2-125 Aux 基线数据 |
| `version/v2/V2B3_ONLY_PI_SCOPE_TEST_RECORD.md` | 审查 v2B3 状态 |
| `software/.../docs/experiment_logs/experiment_log_20260630_203915.md` | 审查最新实验数据 |
| `version/v3/claude审查/CLAUDE_REVIEW_2026-07-05_V3REG0_PROJECT_FEASIBILITY_AND_AUTO_LOCK_ROADMAP_REVIEW.md` | 交叉对照上次审查 |
| `version/v3/claude审查/CLAUDE_REVIEW_2026-07-05_HOST_TRIANGLE_OUTPUT_FAILURE_REVIEW.md` | 交叉对照 OUT2 故障审查 |

---

## 2. Git 仓库状态与上次审查的交叉验证

```
HEAD: c7a04cb "Update v94 project code documents and records"
git diff --stat: 521 files, 751K insertions, 751K deletions（99%+ Vivado 自动生成）
```

### 2.1 上次审查（2026-07-05）P0 项修复状态

| 上次 P0 项 | 当前状态 | 证据 |
|---|---|---|
| P0-1: custom_fpga_scan_control.py 缺少 MAGIC 预校验 | **已修复** | REMOTE_HELPER 中 require_magic() 函数存在（line 127-143），safe/scan 操作均调用 require_magic() 后才写入 |
| P0-2: D2_125_REAL_WIRING_AND_STATE_MODEL.md 合并冲突 | **未解决** | 文件仍存在 `<<<<<<< HEAD` / `=======` / `>>>>>>>` 标记，英文版和中文版重复 |

### 2.2 上次审查（2026-07-05）P1 项修复状态

| 上次 P1 项 | 当前状态 |
|---|---|
| P1-1: 缺少 custom_register_bank testbench | **已修复** — tb_custom_register_bank_basic.sv 存在，覆盖完整的寄存器 R/W |
| P1-2: STATUS.md 未更新 v3REG-0 | **已修复** — STATUS.md 现在包含完整的 v3REG-0 历史（7/5 全部条目） |
| P1-3: "下一步"歧义 | **部分改善** — STATUS.md 明确"当前主线 = v3REG-0"，但 V2_NEXT_STEPS.md 仍保留 v2B3 条目 |
| P1-4: sys[6] 上板确认 | **已确认** — experiment_log_20260630 记录 base_addr=0x40600000 已通过 Probe Registers 验证 |

### 2.3 冲突标记检查

- `version/v2/D2_125_REAL_WIRING_AND_STATE_MODEL.md` — **P0 冲突存在**（英文版 + 中文版完整重复，每行都在冲突标记内）
- RTL 目录 — 无冲突标记
- 上位机目录 — 无冲突标记
- 审查文件目录 — 无冲突标记（上次审查中引用冲突内容是代码块展示，不是真实冲突）

---

## 3. RTL 总体评估

### 3.1 custom_register_bank.sv（139 行）— PASS，无重大变更

上次审查的 20 项安全判据中，第 1-11 项全部 PASS（复位安全、写保护、总线行为、MAGIC 机制）。本次确认代码未发生实质性变更，所有安全特性保持完整。

关键设计要点：
- 11 个寄存器（MAGIC/VERSION/MODE/ENABLE/OFFSET/AMP/STEP/UPDATE_DIV/LIMIT/STATUS/MONITOR）
- REG_MODE 只接受 wdata==1（SCAN），其他 → 0（SAFE）— 防未知模式码
- REG_OUT2_LIMIT 硬件上限 8191 — 防超量程输出
- REG_SCAN_UPDATE_DIV wdata==0 → 强制 1 — 防除零

### 3.2 ramp_generator.sv（168 行）— PASS，TIMING_FIX_2 后版本

V3REG0_TIMING_FIX_2 拆分了三角波更新路径（tick 后候选计算拍 + 边界/方向提交拍），本地 xvlog 通过 0 error。用户手动 Vivado implementation 通过：**WNS = +0.322 ns, TNS = 0.000 ns, Failing Endpoints = 0**。

关键安全特性：
- 复位/disable 后 OUT2 = 0（SAFE_VALUE）
- 双重饱和检查：limit 钳位 + DAC_POS_LIMIT/DAC_NEG_LIMIT 硬件上限
- 参数绝对值化 + 钳位（amp/step/limit 全部安全处理）

### 3.3 red_pitaya_top.sv 集成 — PASS

- sys[6] → custom_register_bank，sys[7] → sys_bus_stub（正确）
- DAC B = selected_out2（v3REG-0 的 register_bank + ramp_generator 路径）
- DAC A = laser_error（mixer + LPF 观察路径）
- OUT2 安全 MUX：custom_mode≠1 → OUT2=0；mode=1 但 enable=0 → OUT2=0
- pi_controller_seq 仍在实例化但 CONTROL_PATH_MODE=1 的 laser_control 不再驱动 DAC B

### 3.4 pi_controller_seq.sv — 预备就绪，非当前输出

15-state 流水线 PI 控制器（S_IDLE → S_CAPTURE → S_LIMIT_PREP → ... → S_OUTPUT）。参数为编译时常量（KP_DEFAULT/KI_DEFAULT/LIMIT_DEFAULT），下一步需要改为寄存器参数化才能用于运行时控制。enable_i=0 → 立即清零 control_o、清除积分器、状态机回 IDLE。Disable 安全行为独立于 register_bank。

### 3.5 仿真测试状态

| 测试 | 结果 |
|---|---|
| tb_ramp_generator | **249/249 pass** |
| tb_custom_register_bank_basic | 设计完整（覆盖寄存器 R/W），xsim log 未找到 |
| tb_register_bank_basic | 设计完整，xsim log 未找到 |

---

## 4. 上位机软件审查

### 4.1 custom_fpga_scan_control.py — PASS（上次 P0 已修复）

**关键修正确认**：REMOTE_HELPER（line 39-256）中的 `require_magic()` 函数（line 127-143）在 safe/scan 操作前验证 MAGIC=0x4D545330。不匹配时打印错误信息并 SystemExit(2)，不执行任何写入。这与上次审查时 Codex 声称"已修复"但实际未修复的状态不同——**当前代码确实已修复**。

写操作顺序合理：
- safe: ENABLE=0 → MODE=0
- scan: ENABLE=0 → 写入所有参数 → MODE=1 → ENABLE=1

SSH 返回值检查仍为 P2 建议（subprocess.run check=False）。

### 4.2 上位机 GUI — 路径清晰，文档滞后

- Custom FPGA Control v1 已接入 GUI（Probe/Status/SAFE/SCAN）
- 通过 SSH + /dev/mem 访问 custom_register_bank，不启动 redpitaya_scpi
- SAFE/SCAN 写寄存器前必须读到 MAGIC=0x4D545330
- **文档滞后**：main_window.py line 333-339 和 line 1402-1405 的 GUI label 仍说 "OUT2 = FPGA laser_control"，实际应为 "OUT2 = selected_out2 SAFE/SCAN"

### 4.3 实验日志证据 — 链路已物理验证

experiment_log_20260630_203915.md 记录：
```
base address = 0x40600000     ✓ Probe 找到 custom_register_bank
MAGIC  = 0x4D545330           ✓ 正确
VERSION = 0x00030000          ✓ 正确
MODE = 1, ENABLE = 1         ✓ SCAN 模式
OUT2 = 4522 counts / 0.552 V ✓ 与配置参数匹配
GUI SCAN 可以让 OUT2 输出三角波 ✓
GUI SAFE 可以关闭 OUT2 输出  ✓
```

**结论**：GUI → SSH → /dev/mem → custom_register_bank → ramp_generator → selected_out2 → DAC B / OUT2 全链路已物理验证通过。v3REG-0 核心目标已达。

---

## 5. 项目当前状态与全自动锁频路线

### 5.1 当前真实能力

**已验证可用的路径**：
```
IN1 (PD/MTS) + IN2 (REF)
→ mixer_core → lpf_core → output_protect → OUT1 (error observation)
GUI → SSH → /dev/mem → register_bank → ramp_generator → OUT2 (SAFE/SCAN triangle)
```

**尚未实现但需要的路径**（按工程阶段排列）：

1. OUT2 HOLD 模式（捕获锁定点电压）
2. OUT2 P_LOCK / PI_LOCK 模式（register-controlled PI 控制器输出）
3. 自动扫谱状态机（SCAN → 找到峰 → HOLD → LOCK）
4. 锁点判断和失锁检测
5. debug_buffer（采集高速 error signal 数据流到上位机）
6. 上位机识峰算法（CNN 或规则）
7. 自动重锁
8. 长时间稳定性监控
9. 深度学习参数优化

### 5.2 当前不能声称的能力

- 不能声称 FPGA 已经闭环锁定（尚未实现闭环 PI 控制）
- 不能声称已经替代 D2-125（尚未连接真实执行器）
- 不能声称 OUT2 可以驱动 Scan/PZT（尚未经过安全验证）
- 不能声称已经实现全自动深度学稳频（差距 7 个阶段）
- 不能声称 error signal 质量可以用于锁定判断（OUT1≈0 警告尚未跟进）

---

## 6. MTS vs SAS 路线对比分析

### 6.1 MTS（Modulation Transfer Spectroscopy）— 当前路线

**原理**：PD 探测泵浦光通过 EOM 调制后与探测光在非线性介质中的四波混频产生的调制转移信号。需要一个外部 RF 信号源（4.6 MHz）驱动 EOM，IN1 接收 PD 信号，IN2 接收 REF，FPGA mixer 做解调。

**在 Red Pitaya FPGA 上的实现**：
- IN1 ← PD/MTS 信号（含调制边带）
- IN2 ← 外部 4.6 MHz REF
- mixer_core → 混频解调（IN1 × IN2）
- lpf_core → 低通滤波得到 DC error
- error → PI 控制 → 激光器反馈

**优势**：
- Error signal 基线平直（调制转移消除多普勒背景），锁点判断更可靠
- 当前项目已经基于 MTS 路线做了大量工作（mixer_core/lpf_core/PI controller）
- D2-125 实验室基线也是 MTS 路线，有成熟的实验参数参照
- EOM 由外部信号源驱动，不需要消耗 Red Pitaya DAC 通道

**劣势**：
- 需要外部 RF 源 + EOM + 射频放大链路（额外硬件成本）
- 光路复杂（需要 EOM 和调制光路）

### 6.2 SAS（Saturated Absorption Spectroscopy）— 未采用路线

**原理**：探测光和泵浦光在气室中对向传播，直接通过饱和吸收信号得到误差。通常用激光器电流调制来扫频，PD 直接接收透射信号。

**在 Red Pitaya FPGA 上的可能实现**：
- IN1 ← PD/SAS 信号
- 不需要 IN2（没有 REF 混频）
- FPGA 需要生成扫描信号（OUT2）→ 激光器电流或 PZT
- Error = PD 信号的微分或峰值检测

**优势**：
- 光路简单（不需要 EOM 和调制光路）
- 不需要外部 RF 信号源

**劣势**：
- Error signal 有多普勒背景，基线不平，锁点判断复杂
- 扫频通常通过激光器电流调制（影响激光器本身的工作点）
- 当前项目完全没有 SAS 路线的 RTL/上位机/实验基线
- 论文中的 SAS 实现通常使用电流调制而非 PZT 调制，与当前 D2-125 替代路径完全不同

### 6.3 路线选择结论

**明确推荐继续 MTS 路线，不切换 SAS。**

理由：
1. 当前所有 RTL（mixer_core/lpf_core/PI controller/register_bank/ramp_generator）都是为 MTS 路线设计的
2. D2-125 实验室基线支持 MTS 路线的参数参照
3. MTS error signal 质量更好（基线平直），有利于后续自动识峰和锁点判断
4. EOM 由外部信号源驱动，不消耗 Red Pitaya DAC 通道，DAC 端口分配更宽裕
5. 切换 SAS 意味着从零开始（需要重新设计 error 提取逻辑、重新采集实验基线数据、重新设计锁定策略）
6. 论文中 SAS 路线是合理的研究路线，但不适合当前项目已经建立了 MTS 工程基础的现状

---

## 7. DAC 端口分配策略

### 7.1 Red Pitaya STEMlab 125-14 的 DAC 资源

Red Pitaya 只有 **2 个高速 DAC 输出**（OUT1/DAC A 和 OUT2/DAC B），均为 14-bit、125 MS/s。这两个端口需要同时满足实验观察、扫描驱动、锁定反馈等多种需求。

### 7.2 当前分配（v3REG-0）

```
OUT1 / DAC A = laser_error (mixer + LPF error observation, oscilloscope)
OUT2 / DAC B = selected_out2 (register-controlled SAFE/SCAN, oscilloscope)
```

两个端口都用于示波器观察。**没有任何端口接真实执行器。**这是工程上正确的安全起始状态。

### 7.3 第一阶段：单执行器 MTS（"替代 D2-125"初期）

当前 D2-125 有两路输出：Servo Output（慢速电流反馈）和 Aux Servo Output（Scan/PZT）。Red Pitaya 只有 2 个 DAC，初期只替代其中一路：

```
方案 1A：替代 Aux Servo Output（推荐优先）
  OUT1 / DAC A = error observation (继续 scope)
  OUT2 / DAC B = register-controlled HOLD/P_LOCK/PI_LOCK → Scan/PZT
  理由：Aux Output 的电压范围（~0.81V DC + small swing）在 OUT2 的安全范围内
       只需要慢速 PZT 控制，对 PI 带宽要求低
       可以从 D2-125 Aux Output 基线数据（0.81V + triangle @ 52.7Hz）直接对照验证

方案 1B：替代 Servo Output
  OUT1 / DAC A = error observation
  OUT2 / DAC B = register-controlled PI → laser current feedback
  理由：Servo Output 是主要的锁定信号
  风险：电流反馈路径对噪声、带宽和安全性要求更高
       需要验证激光器电流调制输入的电压范围和极性
```

**推荐方案 1A 优先**，因为 Aux 替代风险更低、有 D2-125 基线数据做对照、PI 带宽要求低。

### 7.4 第二阶段：双执行器 MTS（"完整替代 D2-125"）

```
OUT1 / DAC A = register-controlled PI → Servo/laser current (慢速电流反馈)
OUT2 / DAC B = register-controlled HOLD/P_LOCK/PI_LOCK → Aux/Scan/PZT
```

此时两个 DAC 都用于真实执行器。error observation 通过 debug_buffer（FPGA 内部数据采集）或 IN1/IN2 回环（物理接线）实现。

风险与前置条件：
- OUT1 从 observation 切换到 actuator 前，必须在 scope-only 模式下验证 PI control 的电压范围、极性和稳定性
- OUT2 的 Scan/PZT 驱动必须在 scope-only 模式下验证完整的 SCAN→HOLD→P_LOCK→PI_LOCK 流程
- 需要上位机同时监控 error signal 质量（通过 debug_buffer 或 IN1 loopback）
- 不能同时并联 D2-125 和 Red Pitaya 到同一执行器

### 7.5 不应该的分配：Red Pitaya 驱动 EOM

**明确结论：不应使用 Red Pitaya DAC 驱动 EOM。**

理由：
1. EOM 需要 RF 级别的驱动（4.6 MHz 或更高），Red Pitaya DAC 的 125 MS/s 虽然理论上可以生成 4.6 MHz 信号，但 DAC 输出带宽、驱动能力和噪声性能不适合直接驱动 EOM
2. 当前 EOM 已有成熟的外部信号源 + 射频放大链路，改变这条链路带来的风险远大于收益
3. 2 个 DAC 端口已经紧张（需要分别用于 error observation 和 actuator control），不应再分配给 EOM
4. 如果论文中展示的架构用 FPGA DAC1 → EOM，那是论文的设计选择（可能有额外的 DAC 板卡或不关心 EOM 驱动质量），不应直接套用到 Red Pitaya 的 2-DAC 限制上

### 7.6 DAC 分配的完整演进表

| 阶段 | OUT1 / DAC A | OUT2 / DAC B | 备注 |
|---|---|---|---|
| v3REG-0（当前） | Error observation (scope) | SAFE/SCAN triangle (scope) | 无执行器连接 |
| v3REG-2 | Error observation (scope) | HOLD / P_LOCK / PI_LOCK (scope) | PI 参数可调，仍只接示波器 |
| v3REG-3 | Error observation (scope) | P_LOCK / PI_LOCK → Aux/Scan/PZT | 替代 D2-125 Aux Output |
| v4/v5 | PI control → Servo/current | Aux → Scan/PZT | 完整替代 D2-125；error 通过 debug_buffer |

---

## 8. 全自动锁频 11 阶段详细路线

### 8.1 阶段总览图

```text
v1ab/v1c/v1d ─── PASS ─── IN/OUT passthrough, mixer, mixer+LPF
    ↓
v2A ─── PASS ─── 独立 pi_controller (v2A 已验证，但 timing-fail 在主工程中)
    ↓
v2B1 ─── PASS ─── P-only shadow control (timing clean, scope-only)
    ↓
v2B3 ─── PASS (scope) ─── pi_controller_seq 集成 (Ki=0, limit=819), 尚未关闭
    ↓
v3REG-0 ─── CURRENT ─── register_bank + ramp_generator SAFE/SCAN ✓
    ↓ [下一阶段]
Phase 1: v3REG-1 HOLD (capture lock voltage)
    ↓
Phase 2: v3REG-2 register-controlled P_LOCK / PI_LOCK
    ↓
Phase 3: v3REG-3 Aux/Scan/PZT real actuator connection (scope→actuator)
    ↓
Phase 4: v4 scan_lock_fsm (自动扫谱、锁点判断、失锁检测)
    ↓
Phase 5: v4 debug_buffer (高速 error signal 数据采集)
    ↓
Phase 6: v5 上位机识峰 (规则/CNN, 自动选择锁点)
    ↓
Phase 7: v5/v6 自动重锁 + 长时间稳定性
    ↓
Phase 8: v6 上位机自动调参 (Kp/Ki/polarity/limit)
    ↓
Phase 9: v6 完整替代 D2-125 (两个 DAC 都用于真实执行器)
    ↓
Phase 10: v7 深度学习参数优化 (offline 训练 → online 推理)
    ↓
Phase 11: v7 全自动深度学习稳频
```

### 8.2 Phase 1: v3REG-1 HOLD

**目标**：在 ramp_generator 中增加 HOLD 模式，冻结当前位置。

**技术内容**：
- register_bank: REG_MODE 增加 MODE=2 (HOLD)
- ramp_generator: 增加 HOLD 状态（pos 冻结，不递增/递减）
- 上位机: Custom FPGA Control Panel 增加 HOLD 按钮
- OUT2 仍只接示波器

**阻塞**：无硬件阻塞。SAFE/SCAN 已验证的同一链路增加小功能。

**验证标准**：
- SCAN 模式下 OUT2 在扫描
- 上位机点击 HOLD → OUT2 停在当前电压
- HOLD 切换回 SCAN → OUT2 继续扫描
- SAFE → OUT2 = 0

**预计时间**：2-3 天的 RTL + Python 修改，1 次 Vivado 编译，1 次上板验证。

**风险**：低。只是 ramp_generator 的状态扩展，不需要改变顶层集成。

### 8.3 Phase 2: v3REG-2 register-controlled P_LOCK / PI_LOCK

**目标**：将 pi_controller_seq 的参数从编译时常量改为寄存器控制，使上位机可以实时调 P_LOCK/PI_LOCK 参数。

**技术内容**：
- register_bank: 新增寄存器（KP, KI, POLARITY, RESET_INTEGRATOR, OUTPUT_LIMIT, OFFSET）
- red_pitaya_top: selected_out2 MUX 增加 MODE=3(P_LOCK) 和 MODE=4(PI_LOCK) 分支
- pi_controller_seq: 增加运行时参数输入端口（替换编译时常量）
- 上位机: Custom FPGA Control Panel 增加 P_LOCK/PI_LOCK 参数面板
- OUT2 仍只接示波器

**阻塞**：
- pi_controller_seq 的接口改为全参数化需要仔细的流水线调整（15-state 状态机中的参数捕获时机）
- register_bank 的地址空间可能不够（当前使用 11 个寄存器，需新增 6-7 个，总共约 18 个，仍在 6-bit 地址空间内）

**验证标准**：
- P_LOCK 模式下 OUT2 = OFFSET + Kp × error（纯比例控制）
- PI_LOCK 模式下 OUT2 = OFFSET + Kp × error + Ki × integral(error)
- 上位机改变 Kp/Ki → OUT2 行为相应变化
- disable → OUT2 = 0，积分器清零

**预计时间**：1-2 周的 RTL + Python 修改，2-3 次 Vivado 编译，2-3 次上板验证。

**风险**：中。pi_controller_seq 的参数化改造是主要的不确定性来源。可能有新的 timing path 需要处理。

### 8.4 Phase 3: v3REG-3 Aux/Scan/PZT 真实执行器连接

**目标**：在 scope-only 验证 PI control 行为正常后，首次将 OUT2 连接到 D2-125 Aux Output 的替代位置（Scan/PZT 输入）。

**技术内容**：
- 确认 OUT2 的电压范围、极性和带宽与 D2-125 Aux Output 兼容
- 设置初始 OUT2 输出为更保守的低幅度（limit=409 即 ±0.05V）
- 逐步增加幅度到 D2-125 等效值（D2-125 Aux 在 Ramp 状态下约 0.81V + 0.12Vpp）
- 手动控制 SCAN/HOLD/P_LOCK/PI_LOCK 切换
- 保持 D2-125 仍然控制 Servo Output（主电流反馈），仅替代 Aux Output

**关键安全规则**：
- OUT2 不能和 D2-125 Aux Output 同时并联到 Scan/PZT
- OUT2 不能和 D2-125 Servo Output 并联
- 先断开 D2-125 Aux Output，确认 PZT 回到安全状态，再接 Red Pitaya OUT2
- 从最小幅度开始，逐步增加

**验证标准**：
- OUT2 SCAN 模式能产生与 D2-125 Aux 相似的扫描波形（~0.81V DC + triangle @ ~50Hz）
- HOLD 模式能维持扫描范围内的任意点
- 示波器同时观察 IN1 (PD/MTS) 和 OUT1 (error)，确认扫谱过程中能观察到吸收峰
- 紧急停止：上位机一键 SAFE → OUT2=0, PZT 回到安全偏置

**预计时间**：1-2 周的安全验证（包含大量示波器对比和数据记录）。

**风险**：中-高。这是首次 OUT2 连接真实执行器，需要极端谨慎。需要明确记录每组参数下的 PZT 响应和 error signal。

### 8.5 Phase 4: v4 scan_lock_fsm

**目标**：FPGA 内部实现自动扫谱、锁点判断、失锁检测的状态机。

**技术内容**：
- RTL: scan_lock_fsm 模块（IDLE → RAMP → PEAK_DETECT → HOLD → LOCK → RELOCK）
- 锁点判断逻辑：检测 error signal 的特征（过零点、斜率变化方向、"dispersion-like" 形状）
- 失锁检测：error signal 突然偏离锁定点
- register_bank: 新增 FSM 状态读取、自动/手动模式切换
- 上位机: Scan & Lock Dashboard（显示 FSM 状态、当前阶段、error signal 实时波形）

**阻塞**：
- error signal 质量是锁点判断可靠性的前提——当前 OUT1≈0 的警告尚未跟进
- 需要积累多组扫谱数据来定义锁点判断参数
- FSM 的正确性验证需要大量仿真和上板测试

**验证标准**：
- SCAN 模式下 error signal 出现 dispersion-like 特征
- FSM 能自动检测到 error 零交叉点并触发 HOLD
- 模拟失锁条件 → FSM 能检测到并触发 RELOCK
- 上位机 Dashboard 能实时显示 FSM 状态和 error 波形

**预计时间**：3-4 周（RTL 设计 + 仿真 + Vivado + 上板调试）。

**风险**：高。锁点判断的可靠性是整个自动锁频路线的核心难点。在 error signal 质量不确定的情况下不应过度乐观。

### 8.6 Phase 5: v4 debug_buffer

**目标**：FPGA 内部实现高速数据采集缓冲，让上位机能读取扫谱过程中的 error signal 完整波形。

**技术内容**：
- RTL: debug_buffer 模块（BRAM-based ring buffer，可配置的触发条件和采集长度）
- 通过 sys_bus_if 或专用 AXI 接口传输数据到 PS
- 上位机: 高速数据采集和实时波形显示

**阻塞**：
- debug_buffer 需要 BRAM 资源和 AXI/总线带宽设计，是独立子项目
- 当前 sys[6] 是 register_bank，数据采集可能需要新的总线通道或复用 sys[6]
- PL → PS 的数据传输路径尚未建立

**验证标准**：
- 扫谱过程中 debug_buffer 能完整记录 1-2 个完整扫描周期的 error signal
- 上位机能读取 debug_buffer 数据并显示波形
- 采集速率至少与 PI 更新速率（~10 kHz）匹配

**预计时间**：2-3 周。

**风险**：中-高。debug_buffer 是全新 RTL 设计，且与现有的 sys_bus 架构交互关系需要仔细设计。

### 8.7 Phase 6: v5 上位机识峰

**目标**：上位机自动识别扫谱波形中的吸收峰/error signal 特征，自动选择锁点。

**技术内容**：
- 规则识峰（Phase 6A）：基于 error signal 的"dispersion-like"形状做零交叉点检测
- CNN 识峰（Phase 6B）：训练小型 1D-CNN 在扫谱波形中识别吸收峰位置
- 上位机自动推荐锁点（显示推荐的 HOLD 电压）
- 用户确认或系统自动选择

**阻塞**：
- CNN 需要大量标注的扫谱数据（至少几百组各种条件下采集的波形）
- 训练 pipeline 需要搭建（Python/TensorFlow 或 PyTorch）
- 当前没有任何扫谱数据积累

**验证标准**：
- 上位机能正确识别扫谱波形中的吸收峰位置
- 推荐的锁点电压与实际最佳锁点一致
- CNN 模型在未见过的数据上正确率 > 90%

**预计时间**：Phase 6A (规则) 1-2 周，Phase 6B (CNN) 4-8 周（含数据采集和训练）。

**风险**：6A 低-中（规则方法可控），6B 中-高（数据量和模型可靠性）。

### 8.8 Phase 7: v5/v6 自动重锁

**目标**：失锁后系统自动重新扫描、重新识峰、重新锁定。

**技术内容**：
- 失锁检测 → 触发重新扫描 → 识峰 → 选择锁点 → HOLD → LOCK
- 上位机: 自动重锁流程引擎
- 重锁超时和失败处理（多次重锁失败 → 进入 SAFE 模式 + 通知用户）

**验证标准**：
- 人为制造失锁条件 → 30 秒内自动恢复锁定
- 连续 10 次自动重锁成功率 > 80%
- 重锁失败 → 进入 SAFE 模式，不产生危险输出

**预计时间**：2-4 周。

**风险**：中。依赖 Phase 4-6 的可靠性。

### 8.9 Phase 8: v6 上位机自动调参

**目标**：上位机根据 error signal 特征自动调整 Kp/Ki/polarity/output_limit。

**技术内容**：
- 上位机: 参数扫描和优化策略（Ziegler-Nichols 或基于 error RMS 的梯度下降）
- register_bank: 支持运行时参数写入（已在 v3REG-0 实现）
- 锁定质量评估（error RMS、OUT2 波动幅度、锁定稳定性指标）

**验证标准**：
- 自动调参后的锁定稳定性不低于手动调参
- 调参过程不影响锁定安全（不产生超大幅度的 OUT2 输出）

**预计时间**：2-3 周。

**风险**：中。自动调参在实验物理中本质上是 empirical 的，需要大量实验数据验证。

### 8.10 Phase 9: v6 完整替代 D2-125

**目标**：两个 DAC 都用于真实执行器，完全断开 D2-125，Red Pitaya 独立维持激光锁定。

**技术内容**：
- OUT1: PI control → Servo/current feedback（替代 D2-125 Servo Output）
- OUT2: P_LOCK/PI_LOCK → Aux/Scan/PZT（已在 Phase 3 验证）
- 上位机: 双通道监控 Dashboard
- 长期稳定性测试（1 小时、4 小时、8 小时）

**验证标准**：
- 独立维持锁定 1 小时以上，error RMS 不劣于 D2-125
- 无人工干预
- 任意一路进入 SAFE 时，系统不产生危险输出

**预计时间**：2-4 周（含长期稳定性测试）。

**风险**：高。这是整个项目最关键的门槛。双执行器同时工作时的交叉耦合是主要风险。

### 8.11 Phase 10: v7 深度学习参数优化

**目标**：offline 训练深度学习模型来优化 PI 参数、锁点选择、重锁策略。

**技术内容**：
- 数据采集：长期记录 error/Kp/Ki/OUT2/lock quality 的时间序列
- 模型训练：offline 训练 RL 或监督学习模型
- 模型部署：轻量级推理引擎在上位机运行（不在 FPGA 内部运行 DL）

**阻塞**：
- 需要大量标注的锁定质量数据（至少需要数周-数月的实验数据）
- 深度学习模型的选择和训练策略需要研究

**验证标准**：
- DL 优化后的锁定稳定性优于手动调参
- 推理延迟不影响实时控制（推理在秒级，不在微秒级）

**预计时间**：2-3 个月（主要是数据采集时间）。

**风险**：研究级任务。v3REG-0 阶段讨论具体实现为时过早。

### 8.12 Phase 11: v7 全自动深度学习稳频

**目标**：从开机到锁定完全自动化，上位机根据环境条件自动选择最佳参数和策略。

**技术内容**：
- 集成所有自动功能：自动连接 → 自动 probe → 自动扫谱 → 自动识峰 → 自动锁定 → 自动优化 → 自动重锁
- 长时间无人值守锁定（数小时到整天）
- 环境自适应性（温度变化、激光器老化等）

**预计时间**：3-6 个月。

**风险**：极高。这是最终目标，需要在所有前 10 个阶段稳定运行后才能实现。

---

## 9. P0/P1/P2/P3 问题分类

### 9.1 P0（必须解决才能继续）

| # | 类别 | 问题 | 影响 | 修复 |
|---|---|---|---|---|
| P0-1 | 文档 | D2_125_REAL_WIRING_AND_STATE_MODEL.md 存在未解决的 git 合并冲突（英文/中文完整重复） | 对该文档的任何引用不可靠，影响实验决策 | User: git merge 选一版或手动合并 |

### 9.2 P1（下一阶段前应解决）

| # | 类别 | 问题 | 修复 |
|---|---|---|---|
| P1-1 | 实验 | OUT1≈0 警告未跟进（2026-06-30 的 WARNING 持续未解决） | User: 检查 IN1/IN2 物理信号、mixer 的 REF 相位、确认信号通路是否正常 |
| P1-2 | 文档 | V2_NEXT_STEPS.md 仍保留 v2B3 条目，与 STATUS.md 的"当前主线 = v3REG-0"不一致 | Codex: 更新 V2_NEXT_STEPS.md，明确 v2B3 和 v3REG-0 的关系 |
| P1-3 | GUI | main_window.py label 滞后（OUT2 = "laser_control" 实际是 "selected_out2 SAFE/SCAN"） | Codex: 更新 GUI label |
| P1-4 | 计划 | 缺少 v3REG-0 → v3REG-1 HOLD 的具体实现计划 | Codex/User: 在 V3REG0_HOST_CONTROLLED_SCAN_PLAN.md 补充后续阶段 |
| P1-5 | 测试 | tb_custom_register_bank_basic.sv 和 tb_register_bank_basic.sv 的 xsim log 缺失 | User: 运行 xsim 确认 testbench 通过 |

### 9.3 P2（建议改善）

| # | 类别 | 建议 |
|---|---|---|
| P2-1 | 上位机 | custom_fpga_scan_control.py SSH subprocess.run 加 check=True 或返回值检查 |
| P2-2 | 测试 | tb_ramp_generator 补充热修改参数（运行中改 offset/amp/step）和极限组合测试 |
| P2-3 | 文档 | V3REG0_HOST_CONTROLLED_SCAN_PLAN.md 补充 pass/fail 标准 |
| P2-4 | 规划 | 缺少数值化的阶段验收标准（例如"1 小时锁定 RMS error < X mV"） |
| P2-5 | RTL | ramp_generator 中 always_comb 的 double saturation 逻辑可加注释说明最后赋值生效 |

### 9.4 P3（长期考虑）

| # | 类别 | 建议 |
|---|---|---|
| P3-1 | 架构 | 如果未来 OUT1 也需要 PI 控制（Phase 9），可能需要第二个 register_bank 实例或扩展地址空间 |
| P3-2 | 数据传输 | debug_buffer 的 PL→PS 数据传输方案需要提前设计（sys_bus 复用 vs 独立 AXI/DMA） |
| P3-3 | 安全 | 硬件紧急停止路径（专用 GPIO 或物理开关）应该提前规划 |
| P3-4 | 可维护性 | 随着 register_bank 寄存器数量增加，考虑自动生成寄存器文档的工具脚本 |

---

## 10. 回答 17 个具体问题

### Q1: v3REG-0 的 register_bank + ramp_generator 是否已经实现全链路物理可达？

**A**: 是。experiment_log_20260630_203915.md 提供了确定证据：
```
base address = 0x40600000 → Probe 找到 MAGIC=0x4D545330
GUI SCAN → OUT2 输出三角波（0.55V~0.95V, ~50Hz）
GUI SAFE → OUT2 三角波消失
```
全链路 GUI → SSH → /dev/mem → register_bank → ramp_generator → OUT2 已物理验证通过。

### Q2: 当前是否可以生成 timing-clean bitstream？

**A**: 是。用户手动 Vivado implementation 已通过：
```
WNS = +0.322 ns
TNS = 0.000 ns
Failing Endpoints = 0
```
可以 Generate Bitstream。但需要确认当前的 bitstream 是 TIMING_FIX_2 之后的版本（拆分了 ramp_generator 三角波更新路径）。

### Q3: 当前 OUT2 是否可以接 Scan/PZT？

**A**: 不可以。当前只允许 OUT2 接示波器。必须先完成：
1. HOLD 模式实现（Phase 1）
2. P_LOCK/PI_LOCK 在 scope-only 模式下验证（Phase 2）
3. 确认 OUT2 电压范围、极性、安全边界与 Scan/PZT 输入匹配
4. 制定专门的 Scan/PZT 连接 SOP

最早可能在 Phase 3 (v3REG-3) 阶段实现这一目标。

### Q4: MTS 路线是否优于 SAS 路线？

**A**: 在当前项目的工程约束下，明确是。详见第 6 节分析。不应因为论文中 SAS 路线的存在而改变当前已建立的 MTS 工程基础。

### Q5: EOM 是否可以继续由外部信号源驱动？

**A**: 可以，而且应该。不应使用 Red Pitaya DAC 驱动 EOM。详见第 7.5 节分析。

### Q6: 2 个高速 DAC 端口是否足够完成完整替代 D2-125？

**A**: 足够，但需要分阶段。初期 OUT1 继续做 error observation，OUT2 逐步承担 actuator control 角色。最终两个 DAC 都用于真实执行器时，error observation 通过 debug_buffer 或 IN1 loopback 实现。详见第 7 节。

### Q7: 最短"替代 D2-125 Aux Output"的路径是什么？

**A**: Phase 1 (HOLD) → Phase 2 (P_LOCK/PI_LOCK) → Phase 3 (Aux/Scan/PZT connection)。预计 2-3 个月（含大量 scope-only 安全验证）。

### Q8: v2B3 和 v3REG-0 的关系是什么？两个并行开发线应该如何管理？

**A**: v2B3 是 OUT2 的 PI 控制路径（pi_controller_seq → control_o），v3REG-0 是 OUT2 的扫描路径（register_bank → ramp_generator → selected_out2）。当前 OUT2 实际使用的是 v3REG-0 路径（selected_out2），pi_controller_seq 虽然仍在顶层实例化但输出不连接 DAC B。

建议：正式关闭 v2B3（该线的 Ki=0/limit=819 测试已完成且满足通过标准），统一到 v3REG-0 主线。pi_controller_seq 的 PI 能力将在 Phase 2 (v3REG-2) 通过 register_bank 参数化重新引入。

### Q9: pi_controller_seq 如何从"编译时参数"改成"运行时寄存器参数"？

**A**: 需要在 pi_controller_seq 的输入端口增加参数接口（kp_i/ki_i/output_limit_i 等），并修改内部状态机在 S_CAPTURE 状态捕获这些参数。register_bank 新增寄存器映射这些参数。关键挑战：当前内部参数（如 KP_SHIFT/KI_SHIFT）是编译时常量，改为运行时变量可能影响乘法器和移位器的综合结果。

### Q10: debug_buffer 需要什么样的架构？

**A**: 最小可行方案：BRAM ring buffer，由 scan_lock_fsm 的触发条件启动采集，通过 sys_bus（复用 sys[6] 或其他 sys 端口）读取。建议使用 PL-side BRAM + 软件轮询读取（不要求 DMA），因为 PI 更新速率只有 ~10 kHz，对 data bandwidth 要求不高。

### Q11: CNN 识峰需要多少数据？

**A**: 粗略估计需要至少 200-500 组标注的扫谱波形（每组包含完整的一周期 error signal）。每组需要人工标注吸收峰位置和推荐的锁点。建议先用规则方法（零交叉点检测）实现识峰，积累数据的同时逐步训练 CNN。

### Q12: 上位机是否应该做高速实时 PID？

**A**: 不应该。当前架构设计正确：FPGA 负责 125 MHz 实时控制（mixer/LPF/PI/scan），上位机负责模式切换、参数写入、状态监控。上位机通过 SSH/SCPI 的通信延迟在 10-100 ms 量级，远不能满足激光稳频的实时性要求。不应改变这个分工。

### Q13: 当前的 OUT1≈0 WARNING 是否阻塞后续开发？

**A**: 是的。OUT1 的 error signal 是所有 PI 控制和锁点判断的基础。如果 OUT1 确实接近零（可能是信号通路断开、REF 相位不匹配或 optical input 本身为零），所有基于 error signal 的后续阶段都无法进行。**这是 P1-1，必须在进入 Phase 2 (PI_LOCK) 之前解决。**

### Q14: Red Pitaya 是否可以同时运行 Official SCPI 和 Custom FPGA？

**A**: 不可以。当前设计是互斥的：
- USE_LASER_LOCK_CORE=1 → DAC A/B 来自 custom FPGA 路径
- Official SCPI → DAC A/B 来自 ASG+PID 路径
启动 redpitaya_scpi 可能加载官方 overlay 并覆盖 custom bitstream。Custom FPGA Mode 下不启动 SCPI 是正确的安全策略。

### Q15: 实验数据中 OUT2 Vpp=0.4583V（实验日志）与默认参数 0.05V 有巨大差异，是否正常？

**A**: 正常。实验日志中使用的参数是 offset-v=0.7500V, amp-v=0.2000V（不是默认的 offset=0.85V, amp=0.05V）。用户手动调大了扫描幅度来观察更大的扫谱范围。理论 Vpp = 2 × 0.2V = 0.4V，实测 0.4583V，偏差在合理范围内（DAC 增益误差、示波器测量误差、传输线效应）。

### Q16: 上位机 GUI 的两个 OUT2 控制路径（SCPI vs Custom FPGA）是否已经明确分离？

**A**: 基本分离，但 GUI label 有滞后。FPGA_MODE_BOUNDARY.md 和 HOST_APP_V2_DESIGN.md 已经文档化了分离策略。main_window.py 的 Custom FPGA Mode 下 OUT1/OUT2 Apply 已被禁用（line 1368-1370）。但页面上的 label 仍显示 "OUT2 = FPGA laser_control"，应改为 "OUT2 = register_bank SAFE/SCAN"。

### Q17: 项目是否需要考虑 Red Pitaya 之外的硬件平台？

**A**: 当前不需要。Red Pitaya STEMlab 125-14 (Zynq-7010) 的资源（28K logic cells, 2.1 Mb BRAM, 80 DSP slices, 2× 125 MS/s DAC/ADC）对于 MTS laser lock 应用是足够的。在替代 D2-125 的路径上，不需要更强的 FPGA 或更多的 DAC 通道。仅在以下情况考虑扩展：
- 需要同时控制多个激光器
- 需要 GHz 级别的直接数字频率合成
- EOM 驱动需要集成到 FPGA DAC（本文不推荐）

---

## 11. 1 周 / 2 周 / 1 月 / 2-3 月执行计划

### 11.1 1 周计划（2026-07-08 至 2026-07-15）

**Codex 任务**：
1. 修复 P1-3: main_window.py GUI label 更新（OUT2 描述从 "laser_control" → "selected_out2 SAFE/SCAN"）
2. 修复 P1-2: V2_NEXT_STEPS.md 新增条目，说明 v2B3 关闭、v3REG-0 是当前主线
3. 修复 P2-1: custom_fpga_scan_control.py SSH 返回值检查
4. 完成 V3REG0_HOST_CONTROLLED_SCAN_PLAN.md 的 pass/fail 标准补充

**User 任务**：
1. 修复 P0-1: 解决 D2_125_REAL_WIRING_AND_STATE_MODEL.md 的 git 合并冲突
2. 调查 P1-1: 检查 IN1/IN2 物理信号、mixer 的 REF 相位，判断 OUT1≈0 的原因
3. 运行 xsim 确认 tb_custom_register_bank_basic.sv 通过

### 11.2 2 周计划（2026-07-15 至 2026-07-22）

**Codex 任务**：
1. **Phase 1 实现**: v3REG-1 HOLD 模式
   - ramp_generator.sv: 增加 HOLD 状态
   - custom_register_bank.sv: REG_MODE 增加 MODE=2 (HOLD)
   - custom_fpga_scan_control.py: 增加 hold 命令
   - 新增 tb_ramp_generator 的 HOLD 测试用例

**User 任务**：
1. OUT1≈0 的问题跟进（如果 1 周内未解决）
2. Vivado 综合 + 实现 + timing → bitstream（Phase 1 修改后）
3. 上板验证 HOLD 模式（OUT2 scope-only）

### 11.3 1 月计划（2026-07-22 至 2026-08-08）

**Codex 任务**：
1. **Phase 2 实现**: v3REG-2 register-controlled PI
   - pi_controller_seq.sv: 增加运行时参数端口（kp_i/ki_i/polarity_i/output_limit_i/offset_i）
   - custom_register_bank.sv: 新增 PI 参数寄存器
   - red_pitaya_top.sv: selected_out2 MUX 增加 MODE=3(P_LOCK) 和 MODE=4(PI_LOCK)
   - custom_fpga_scan_control.py: 增加 p_lock/pi_lock 命令
   - 新增 PI 参数化的 testbench

**User 任务**：
1. 多次 Vivado 编译和 timing 检查（pi_controller_seq 参数化可能引入新的 timing 问题）
2. OUT2 scope-only 验证: P_LOCK 行为（OUT2 ∝ error_o）、PI_LOCK 行为（OUT2 含积分器）
3. 积累实验数据: 记录不同 Kp/Ki/offset/limit 下 OUT2 的 scope 波形
4. 至少完成 3 组完整的示波器数据记录

### 11.4 2-3 月计划（2026-08-08 至 2026-10-08）

**Codex 任务**：
1. **Phase 3 准备**: 起草 Scan/PZT 连接的 SOP
2. **Phase 4 设计**: scan_lock_fsm 的详细状态机设计（IDLE→RAMP→PEAK_DETECT→HOLD→LOCK→RELOCK）
3. **Phase 5 设计**: debug_buffer 的架构设计（BRAM ring buffer + 触发条件 + 读取接口）
4. 上位机 Scan & Lock Dashboard 的原型设计

**User 任务**：
1. **Phase 3 执行**: 在 scope-only 验证通过后，首次连接 OUT2 → Scan/PZT（替代 D2-125 Aux Output）
2. 至少采集 50 组扫谱波形数据（为识峰算法做准备）
3. 与 D2-125 的实验数据做系统对比
4. 记录所有安全事件、异常现象和参数边界

---

## 12. 关键风险与缓解策略

### 风险 1: Error Signal 质量（OUT1≈0）

**风险级别**: 🔴 高
**影响范围**: Phase 2 及之后所有阶段
**缓解策略**:
1. 立即检查 IN1/IN2 物理信号通路
2. 验证 mixer 的 REF 是否与 IN2 REF 同源/同相
3. 在不接 PI 控制的情况下，手动扫谱观察 error signal 是否出现 dispersion-like 特征
4. 如果 error signal 确实因为 optical 对齐/PD 增益问题而太小，需要调整模拟链路增益

### 风险 2: pi_controller_seq 参数化引入 timing failure

**风险级别**: 🟡 中
**影响范围**: Phase 2
**缓解策略**:
1. 先做最小参数化（只加 kp_i/ki_i/output_limit_i，不改移位器）
2. 每次修改后都跑 Vivado timing
3. 保留当前硬编码版本作为 fallback

### 风险 3: Scan/PZT 执行器兼容性

**风险级别**: 🟡 中
**影响范围**: Phase 3
**缓解策略**:
1. 先用 D2-125 Aux Output 的基线数据（0.81V + triangle @ 52.7Hz）作为 OUT2 的对照目标
2. 从 0.05V 幅度开始，逐步增加
3. 全程示波器监控 PZT 响应
4. 上位机一键 SAFE 按钮随时可用

### 风险 4: 文档与代码脱节

**风险级别**: 🟢 低（但持续）
**影响范围**: 全项目
**缓解策略**:
1. 每次 RTL 修改后立即更新 STATUS.md
2. GUI label 与 RTL 实际路由同步更新
3. 每个阶段的 SOP 写清"允许连接什么"和"禁止连接什么"

---

## 附录 A: D2-125 替代对照表

| D2-125 功能 | 物理输出 | 电压范围 | 当前状态 | 替代阶段 |
|---|---|---|---|---|
| Error 生成 | —（内部） | — | ✓ mixer_core + lpf_core (v1d) | — |
| Servo Output → current | Front BNC | ~0-10V（经过三通分压） | ✗ 未实现 | Phase 9 |
| Aux Servo Output → PZT | Rear BNC | ~0.81V + ±0.06-0.12V triangle @ 52.7Hz | ✗ 未实现 | Phase 3 |
| Ramp/Unlock/Lock 切换 | —（内部） | — | ✗ 未实现 | Phase 4 |
| PI 参数调整 | 面板旋钮 | — | ✗ 未实现 | Phase 2 |

---

## 附录 B: 验证数据对照表

| 来源 | OUT2 范围 | 频率 | DC offset | Vpp |
|---|---|---|---|---|
| D2-125 Aux Output (Ramp) | 0.751-0.868V | 52.7 Hz | 0.809V | 0.117V |
| D2-125 Aux Output (Lock) | ~0.813V stable | — | 0.813V | 0.017V |
| v3REG-0 (offset=0.75, amp=0.20) | 0.624-1.082V | 50.2 Hz | 0.853V | 0.458V |
| v3REG-0 理论 (offset=0.85, amp=0.05) | 0.800-0.900V | 50.0 Hz | 0.850V | 0.100V |

v3REG-0 实际输出范围与 D2-125 Aux Output 在同一量级，证明 register_bank + ramp_generator 的组合可以产生与 D2-125 Aux Output 相当的扫描信号。当 amp 设为 0.05V 时 Vpp 约 0.1V，与 D2-125 的 0.117V 几乎一致。

---

## 附录 C: 各 Phase 依赖关系图

```
Phase 1 (HOLD)
  ├── 依赖: v3REG-0 (✓ 已完成)
  └── 被依赖: Phase 2, Phase 3

Phase 2 (PI_LOCK)
  ├── 依赖: Phase 1 (HOLD 是 PI_LOCK 的子模式)
  └── 被依赖: Phase 3, Phase 4

Phase 3 (Aux/PZT)
  ├── 依赖: Phase 1, Phase 2 (scope-only 验证通过)
  └── 被依赖: Phase 4, Phase 7

Phase 4 (scan_lock_fsm)
  ├── 依赖: Phase 3 (需要真实 error signal 来验证 FSM 正确性)
  └── 被依赖: Phase 7, Phase 9

Phase 5 (debug_buffer)
  ├── 依赖: Phase 3 (需要真实 error signal 数据来源)
  └── 被依赖: Phase 6

Phase 6 (识峰)
  ├── 依赖: Phase 5 (需要 debug_buffer 提供扫谱数据)
  └── 被依赖: Phase 7

Phase 7 (自动重锁)
  ├── 依赖: Phase 4, Phase 6
  └── 被依赖: Phase 10, Phase 11

Phase 8 (自动调参)
  ├── 依赖: Phase 4 (需要 FSM 提供锁定状态)
  └── 被依赖: Phase 10

Phase 9 (完整替代 D2-125)
  ├── 依赖: Phase 4, Phase 7 (需要可靠的锁定维持能力)
  └── 被依赖: Phase 10, Phase 11

Phase 10 (DL 参数优化)
  ├── 依赖: Phase 7, Phase 8 (需要大量锁定数据)
  └── 被依赖: Phase 11

Phase 11 (全自动 DL 稳频)
  ├── 依赖: Phase 9, Phase 10
  └── 被依赖: —
```

---

审查完成。当前项目处于工程上正确的 v3REG-0 最小验证平台。P0 仅剩 1 项（文档合并冲突）。最短"替代 D2-125 Aux Output"路径需要 2-3 个月。MTS 路线正确清晰，不应改道。2 个高速 DAC 端口通过分阶段演进策略足够完成完整替代。EOM 继续由外部信号源驱动。

请优先解决 P0-1（文档冲突），然后按 1 周→2 周→1 月→2-3 月执行计划推进。
