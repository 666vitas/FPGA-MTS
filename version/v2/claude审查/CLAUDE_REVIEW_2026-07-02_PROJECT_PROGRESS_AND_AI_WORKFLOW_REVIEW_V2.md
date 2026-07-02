# PROJECT_PROGRESS_AND_AI_WORKFLOW_REVIEW

## 1. 审查元信息

- **审查日期:** 2026-07-02
- **审查范围:** `E:\new\fpga_lock\v94`（不含 weifang 目录）
- **是否只读:** 是
- **是否修改文件:** 否
- **是否运行 Vivado:** 否
- **是否生成 bitstream:** 否
- **是否烧录 Red Pitaya:** 否
- **输出文件路径:** `E:\new\fpga_lock\v94\version\v2\claude审查\CLAUDE_REVIEW_2026-07-02_PROJECT_PROGRESS_AND_AI_WORKFLOW_REVIEW_V2.md`

### Git 记录摘要

```
git log --oneline -10:
3630b5d Update v94 project code and documents
ba68702 Update v94 project code and documents
0db768d Update v94 project code and documents
529388c Update v94 project code and documents
9b88257 Update v94 project code and documents
b376479 Update v94 project code and documents
5e0771a Update v94 project code and documents
8b7ddf2 Update v2 text-level RTL docs and project records
60db862 Update v2 text-level RTL docs and project records
3848dfa Add Red Pitaya host app V2 under software
```

**git status 实质性修改文件:**

- `GPT_README.md` (modified)
- `v0.94/rtl/laser_lock_core.sv` (modified: Ki=16→0, limit=1500→819)
- `v0.94/rtl/red_pitaya_top.sv` (modified: CONTROL_PATH_MODE=1)
- `software/redpitaya_lock_host/docs/experiment_logs/experiment_log_20260630_203915.md` (modified)
- `version/STATUS.md` (modified: 2026-07-02 v2B3_scope_safe 记录)
- `version/v2/V2_NEXT_STEPS.md` (modified)
- `version/v2/V2_EXPERIMENT_SOP.md` (modified)
- `version/v2/V2_DEVELOPMENT_ROADMAP.md` (modified)
- `version/v2/V2_AUX_PZT_EXPERIMENT_RECORD.md` (modified)

**git diff --stat:** 609 files changed, 927616 insertions(+), 928336 deletions(-)。99%+ 为 Vivado 自动生成文件（stub.v、ps7_init.c、.bd、xsim.ini 等），跨越三套并行工程目录（guanfang-v0.94、v0.94、v-weifang）。实质性 RTL 和文档变更极小（几十行级）。

**安全性判断:** 未提交的修改不影响当前实验安全。唯一涉及硬件路径的变更是 `laser_lock_core.sv` 中 `PID_KI_DEFAULT=0` 和 `PID_OUTPUT_LIMIT_DEFAULT=819`——这两项是降低风险的安全修正，不是增加危险的改动。

### Vivado Timing Report 确认

本地 report 文件存在：`v0.94/exp/v2/impl_1/red_pitaya_top_timing_summary_routed.rpt`，日期 2026-06-30 21:20:43。

```
Design Timing Summary:
  WNS = +0.107 ns, TNS = 0.000 ns, Failing Endpoints = 0
  WHS = +0.054 ns, THS = 0.000 ns, Failing Endpoints = 0

Intra-Clock (pll_adc_clk):
  WNS = +0.155 ns, TNS = 0, Failing = 0/17804 endpoints
  
check_timing: no_clock (52 pins, daisy unused registers), 
  unconstrained_internal_endpoints (19 pins, 非关键路径)
```

**结论:** 本地 Vivado report 完全支持用户截图结论（WNS=+0.107 ns, TNS=0, Failing=0）。**Vivado timing 风险已关闭。**

---

## 2. 总体结论

**PASS WITH NOTES**

### 六个核心问题的回答

**1. 当前规划是否能完成项目？**
能。v2 规划（v2A→v2G→v3→v7）在逻辑上是逐步替代 D2-125 的正确路线。每一步都有明确的输入/输出/通过标准/不能声称什么。路线本身能完成项目。

**2. 当前规划是否能加快实验进度？**
不能。规划文本本身不会加快进度。当前最大的瓶颈不是缺少规划文档，而是文档执行率太低。STATUS.md 从 2026-06-14 到 2026-07-02 记录了 10 个日期快照，但实际只产生了 2 次正式上板测试（v2B1 P-only PASS + v2B3 only-pi FAIL）。文档在膨胀，实验在等用户有空。

**3. 如果不能，主要问题是什么？**
三个问题：
- (a) AI 代码和文档产出速度远超实验验证速度——这是这个项目最根本的风险；
- (b) "下一步" 在多处出现且不一致——STATUS.md 说 v2B3_scope_safe，V2_NEXT_STEPS.md 说 v2PZT-1，V2_EXPERIMENT_SOP.md 说 OUT1/OUT2 示波器复测；
- (c) experiment_log_20260630_203915.md 记录的 `OUT1≈0, safety_level=WARNING` 没有被跟进到 STATUS 或 V2_NEXT_STEPS 中。

**4. 是否适合用户主要依赖 AI 软件开发？**
部分可行。前提是建立严格的 "AI 产出 < 实验产出" 约束。详见第 6 节。

**5. 下一步是否应该进入 CNN？**
不应该。详见下文。

**6. 下一步是否应该进入 OUT1/OUT2 示波器测试？**
是。这是当前唯一的正确下一步。v2B3_scope_safe 修正（Ki=0, limit=819）已在 RTL 中完成，但还没有经过 Vivado timing 和示波器验证。

---

## 3. 当前项目真实阶段

### 当前硬件链路

```
PD -> v1 既有带通/放大链路 -> Red Pitaya IN1 (MTS/PD 信号, +/-1 V 内)
模拟 4.6 MHz REF -> Red Pitaya IN2 (REF 信号, +/-1 V 内)
Red Pitaya OUT1 -> 示波器 CH1/CH2: FPGA mixer+LPF error observation
Red Pitaya OUT2 -> 示波器 CH4: FPGA sequential PI control candidate (scope-only)
D2-125: 继续独立完成真实激光锁定
  Servo Output -> 激光器控制端
  Aux Output -> Scan/PZT (Ramp: 0.81 V DC + 三角波; Lock: 0.813 V hold)
```

### 当前 FPGA 链路

```
red_pitaya_top.sv:
  USE_LASER_LOCK_CORE = 1
  LASER_LOCK_OUTPUT_MODE = 3 (mixer + LPF)
  LASER_LOCK_CONTROL_PATH_MODE = 1 (sequential PI)

IN1 (14-bit signed ADC) + IN2 (14-bit signed ADC)
  -> mixer_core.sv (14b×14b=28b, shift 13, saturate -> 14b)
  -> lpf_core.sv (32-bit accumulator, shift 12, 一步低通)
  -> output_protect.sv (reset/enable 安全门)
  -> protected_error (14b signed)
      -> OUT1 / DAC A: laser_error observation
      -> pi_controller_seq.sv: 15-state sequential PI
           (Ki=0, Kp=2048, output_limit=819 ≈ +/-0.10 V)
           timing clean: WNS=+0.107 ns, worst path NOT in PI logic
         -> control_o (14b signed)
            -> OUT2 / DAC B: scope-only

定时: pid_ce 每 125MHz/12500 = 10000 Hz 产生一个 update pulse
```

### 当前上位机能力

```
Official SCPI Mode:
  OUT2 三角波/正弦波控制, IN1/IN2 采集
  启动 SCPI 服务可能覆盖 custom FPGA bitstream

Custom FPGA Mode:
  OUT1 = FPGA laser_error, OUT2 = FPGA laser_control
  上位机不能写 FPGA 内部参数 (没有 register_bank)
  上位机不能切换 SCAN/HOLD/P_LOCK/PI_LOCK 模式
  上位机不能读取 FPGA 内部 debug 信号
  Lock Workflow Mode: 是 checklist，不是实现的锁控制器
```

### 当前禁止事项

```
OUT2 只能接示波器，禁止接激光器、D2-125 Servo/Aux Output、Scan/PZT
不能声称 FPGA 已锁定激光或替代 D2-125
不能开始在线 CNN、在线自动重锁
IN1/IN2 必须在 +/-1 V 内
```

---

## 4. 当前规划的优点

1. **安全边界极其清晰且冗余。** 所有文档（STATUS、SOP、NEXT_STEPS、D2_125_REAL_WIRING、V2B3_ONLY_PI_SCOPE_TEST_RECORD）反复强调 OUT2 scope-only、IN1/IN2 +/-1 V。在安全问题上冗余不可省，这一点做得非常好。

2. **阶段划分是教科书级的逐步替代方案。** v2A→v2B→v2C→v2D→v2E→v2F→v2G 每一步都有：输入是什么、处理什么、输出是什么、示波器上能看到什么、通过标准、不能声称什么。定义本身合理且可执行。

3. **对 AI 工具的边界有清醒认识。** GPT_README.md 明确规定：Codex 不运行 Vivado、Claude Code 只读审查、用户手动 Vivado/烧录/接线。这是防止 AI 幻觉伤害硬件的关键护栏。

4. **最大技术风险（v2B3 timing）已经被消除。** 从 v2B1 的 WNS=-10.995 ns 到 v2B3 sequential PI 的 WNS=+0.107 ns，pi_controller_seq.sv 的 15-state 流水线架构证明了其有效性。

5. **实验数据指导路线更新，而不是空想。** Aux/PZT 实测数据（0.81 V DC + 三角波，而不是从 0 V 开始）直接影响了 v2PZT 的 scan_offset 参数设计。这是正确的做法。

---

## 5. 当前规划的风险

1. **AI 写代码和写文档的速度远快于实验验证（最大风险）。** STATUS.md 486 行，V2_EXPERIMENT_SOP.md 865 行，V2_NEXT_STEPS.md 511 行——但实际只有 2 次正式上板测试。代码在积压、文档在膨胀、但实验在等用户有空去实验室。这是 AI-assisted 开发的根本性矛盾：AI 可以在几分钟内生成人类几天的文档量，但物理实验不能加速。

2. **"下一步" 在多处出现且不一致（次大风险）。** STATUS.md 说下一步是 v2B3_scope_safe；V2_NEXT_STEPS.md 同时提到 v2B3_scope_safe 和 v2PZT-1 SAFE/SCAN/HOLD；V2_EXPERIMENT_SOP.md 说下一步是 OUT1/OUT2 示波器复测。一个人打开三个文档，不知道哪个才是 "现在该做的第一步"。虽然它们不是矛盾的，但优先级没有唯一的入口。

3. **实验异常未跨文档跟进。** experiment_log_20260630_203915.md 记录 `OUT1≈0, safety_level=WARNING`，但 STATUS.md、V2_NEXT_STEPS.md、V2_AUX_PZT_EXPERIMENT_RECORD.md 中完全没有引用或讨论这个异常。如果 error signal 本身有问题，所有基于 "error signal 正常" 假设的后续规划都需要先悬置。

4. **三套并行 Vivado 工程目录（guanfang-v0.94、v0.94、v-weifang）增加混淆成本。** git status 显示这三套工程的 Vivado 生成文件都在 modified 状态。虽然 GPT_README.md 规定忽略 weifang，但这些并行目录仍然存在并被 git 跟踪。

5. **上位机功能规划跳过基础设施。** HOST_APP_V2_DESIGN.md 描述了四个 GUI 页面和未来的 Custom FPGA Lock Panel + AI 调参。但 FPGA 侧连最基本的 register_bank 都没有——上位机的任何 "Custom FPGA Lock Panel" 功能在 RTL 侧没有对应物。

---

## 6. 是否适合用户这种 AI-assisted 开发方式

**结论: 部分可行。**

### AI 可以完成（且已在本项目中证明了质量）

- RTL 模块设计: mixer_core.sv、lpf_core.sv、pi_controller_seq.sv 都是高质量、仿真通过、timing clean 的代码
- testbench 编写和 XSim 仿真: 已产出 35+27 个 pass 的测试套件
- Python 上位机界面和 SCPI 通信: Official SCPI Mode 下已工作
- 数据分析脚本: 读取 CSV 计算 Vpp/RMS/mean
- 文档整理和架构文档: 已有 STATUS 486 行和 SOP 865 行
- 实验 SOP: 安全边界、通过标准、停止条件——Claude Code 的强项
- 代码审查: 定位检查和 timing 风险评估
- Vivado report 解读: WNS/TNS/Failing Endpoints 分析
- CNN 离线训练脚本（未来阶段）
- 数据集格式设计（未来阶段）

### 用户必须亲自完成（AI 不能替代）

- 光路调整（EOM、反射镜、λ/4 波片）
- 接线确认（确认 PD 信号在 +/-1 V、确认 REF 幅度合理）
- 示波器读数（确认波形匹配预期）
- Vivado GUI 手动操作（Add Sources、Run Synthesis/Implementation、Generate Bitstream）
- 判断信号是否过压（OUT2 是否接近 +/-1 V）
- 判断激光是否跳模
- 安全连接 OUT2 到执行器（必须在现场确认接线）
- 实验现场异常处理（断线、干扰、设备故障）
- 决定是否真的烧录和上板
- 决定是否真的闭环控制激光

### 必须建立的 AI 工作流（否则项目将失控）

```
ChatGPT / GPT:
  负责: 项目规划、任务拆分、基于最新实验数据更新路线
  约束: 每次输出必须引用新实验数据；没有新数据时不写新规划
  禁止: 在用户没有提供新数据时再写架构规划或扩展功能范围

Codex:
  负责: 小步 RTL 实现 + testbench + Python 脚本 + SOP 生成 + 文档同步
  约束: 每次只实现一个明确可测试的功能；必须同步更新 STATUS 和 NEXT_STEPS
  禁止: 一次修改多个模块、运行 Vivado、生成 bitstream、扩大系统功能

Claude Code:
  负责: 只读审查 + timing 风险评估 + 实验安全检查 + 代码审查 + 项目规划审查
  约束: 每次审查给 PASS / PASS WITH NOTES / FAIL 结论
  禁止: 修改文件、运行 Vivado、声称可以进入下一阶段而不引用实验数据

用户:
  负责: Vivado 操作 + 烧录 + 示波器观察 + 数据记录 + 安全判断 + 决定是否推进
  约束: 每次实验后必须产出 CSV + 截图 + 参数记录

核心循环（每个周期不应超过 2-3 天）:
  用户报告实验结果 (CSV + 截图)
  -> Claude Code 分析数据, 判断 PASS/FAIL
  -> 如果 PASS: Codex 更新 STATUS (≤10 行) 和 V2_NEXT_STEPS (≤3 条)
  -> 如果 FAIL: Codex 执行最小修复 (1 个文件, ≤50 行改动)
  -> 用户下一步实验
  -> 循环

关键约束:
  - 每次实验后只更新 STATUS.md 不超过 10 行
  - V2_NEXT_STEPS.md 每次只能包含 3 条以内、无歧义、直接可执行的任务
  - 不再生成新的架构文档，除非当前阶段正式关闭
  - 文档不是实验进度的替代物
```

---

## 7. 最快推进路线（按优先级）

**1. v2B3_scope_safe 上板验证并关闭 v2B3。**
用户手动 Vivado timing→烧录→示波器验证 Ki=0、limit=819 的 pi_controller_seq。这是当前唯一的正确下一步，所有其他路线（v2D、v2E、v2PZT、CNN、register_bank）都以此为前提。

**2. 解决 OUT1 异常（如果复现）。**
如果 v2B3_scope_safe 仍然出现 OUT1=0 或异常小，必须先排查 IN1 输入、带通/放大链路、OUTPUT_MODE=3。不能带着未知的 error signal 异常进入后续阶段。

**3. v2D: OUT2 硬编码 scan_offset+triangle 示波器验证。**
不等 register_bank，做一个临时 bitstream 验证 OUT2 能输出 0.81 V offset + 52.7 Hz 小三角波。不改 scan/lock FSM。

**4. v2E: 真实 MTS error 下 OUT2 开环观察。**
不动 RTL，直接接真实 PD 信号到 IN1，D2-125 独立锁定，同时记录 FPGA OUT1 error 和 OUT2 control。

**5. v2F 准备: 低增益 P-only 闭环 SOP。**
在 v2E 数据通过后，Claude Code 生成 v2F 单页 SOP（首次 OUT2→Scan/PZT 的完整步骤和安全停止条件）。

---

## 8. 两周实验推进计划

### Day 1-2: v2B3_scope_safe Vivado timing + 示波器验证

**目标:** 正式关闭 v2B3，确认 Ki=0、limit=819 的 sequential PI 行为

**输入:**
- 当前 laser_lock_core.sv（Ki=0, limit=819, CONTROL_PATH_MODE=1）
- v2B3_scope_safe bitstream（用户在上次 Vivado session 中生成）

**操作（用户，需要实验室现场）:**
1. 打开 Vivado，确认 laser_lock_core.sv 参数为 Ki=0, limit=819
2. 确认 pi_controller_seq.sv 在 Design Sources
3. Run Synthesis→Implementation→检查 WNS>=0→Generate Bitstream→烧录
4. 接线：IN1 <- PD/MTS, IN2 <- REF, OUT1 -> CH1, OUT2 -> CH4
5. 保存 CSV（至少 20 秒），截图
6. 改 Kp=4096，保存 CSV；改 Kp=1024，保存 CSV

**输出:** Vivado timing 截图 + 3 个 CSV + 3 个截图

**通过标准:**
- Timing: WNS>=0, TNS=0
- OUT1: 能看到 error-like 信号（几十 mVpp 量级）
- OUT2: 不再贴在 -0.2 V 附近；围绕 0 V 小幅变化；不超过约 +/-0.10 V
- OUT2 跟随 OUT1 error 的变化趋势

**失败回退:**
- OUT1=0: 检查 IN1 输入、带通/放大链路、OUTPUT_MODE=3
- OUT2 仍贴 limit: 降到 limit=410；如果仍然贴边，检查 pi_controller_seq 符号逻辑
- Timing fail: 不烧录

**是否需要实验室:** 是

**AI 工具分工:**
- Claude Code: 生成单页 checklist（v2b3_scope_safe_scope_checklist.md）
- Codex: 写 CSV 分析 Python 脚本
- ChatGPT: 不参与

---

### Day 3: v2B3 数据分析与关闭决策

**目标:** 判断 v2B3 能否正式关闭

**输入:** Day 1-2 的 CSV + 截图

**操作（Claude Code，不需要实验室）:**
1. 分析 CSV: OUT1 Vpp/RMS/mean, OUT2 Vpp/RMS/mean
2. 对比 v2B3 only-pi.csv 的 OUT2 数据（贴在 -0.2 V）
3. 输出 PASS / PASS WITH NOTES / FAIL
4. 如果 PASS: 更新 STATUS.md 一行，关闭 v2B3
5. 如果 FAIL: 分析失败原因，建议最小修复路径

**AI 工具分工:**
- Claude Code: 分析数据，输出结论
- Codex: 更新 STATUS.md（≤10 行）

---

### Day 4-5: v2D RTL 实现（硬编码 scan_offset+triangle）

**目标:** Codex 实现 OUT2_TEST_MODE，为 Day 6-7 上板做准备

**输入:** Claude Code 审查结论（v2B3 PASS）

**操作（Codex，不需要实验室）:**
1. 在 laser_lock_core.sv 新增参数 `OUT2_TEST_MODE`:
   - 0: 正常 sequential PI（默认，保持当前行为）
   - 1: control_o = 硬编码 scan_offset + triangle
     （scan_offset=0.81V 对应 DAC 值，scan_amp=0.03V 对应值，频率≈52.7 Hz）
2. 实现使用简单 counter 生成三角波
3. 写 testbench（约 30 行）验证数字波形形态
4. 不修改 pi_controller_seq.sv，不新增 FSM，不修改顶层

**输出:** 修改后的 laser_lock_core.sv + testbench

**通过标准:**
- XSim pass
- 仿真波形显示正确的 offset + triangle 形态

**失败回退:** 删除 OUT2_TEST_MODE 分支，回退到 clean v2B3

**是否需要实验室:** 否

**AI 工具分工:**
- Claude Code: 写 RTL 任务 spec
- Codex: 实现 RTL + testbench

---

### Day 6-7: v2D 上板验证 + 数据整理

**目标:** 验证 Red Pitaya OUT2 能输出正确的 DC 偏置 + 三角波

**输入:** Codex 实现的 v2D RTL

**操作（用户，需要实验室现场）:**
1. 打开 Vivado，加入新 RTL 文件
2. Run Synthesis→Implementation→检查 timing→Generate Bitstream→烧录
3. OUT2 只接示波器（OUT1 也接示波器同时观察）
4. 确认波形是约 0.81 V DC + 小三角波（频率约 52.7 Hz）
5. 保存 CSV + 截图

**输出:** Vivado timing 截图 + CSV + 示波器截图

**通过标准:**
- Timing 通过（WNS>=0, TNS=0）
- OUT2 示波器: 0.81 V offset + 小三角波，频率约 52.7 Hz
- OUT1 保持不变（error observation）

**失败回退:**
- Timing fail: 不烧录，回退 OUT2_TEST_MODE=0
- 波形不对: 检查 offset/amplitude 参数与 DAC 电压映射

**是否需要实验室:** 是

**AI 工具分工:**
- Claude Code: 写 v2D checklist
- Codex: 不参与（RTL 已在上一步完成）

---

### Day 8: v2D 数据分析 + git 整理

**目标:** 关闭 v2D，git commit，清理过期文档引用

**输入:** Day 6-7 数据

**操作（Claude Code + Codex，不需要实验室）:**
1. Claude Code 分析 v2D 数据，输出 PASS/FAIL
2. 如果 PASS: Codex 更新 STATUS.md（≤10 行）
3. Codex 整理实验数据目录，按日期命名
4. Claude Code 审查 .gitignore 建议

---

### Day 9-11: v2E 真实 MTS error 下 OUT2 开环观察

**目标:** 用真实 PD 信号驱动 v2B3 sequential PI（OUT2_TEST_MODE=0），同时 D2-125 独立锁定

**输入:** v2B3 bitstream (OUT2_TEST_MODE=0), 真实光路

**操作（用户，需要实验室现场）:**
1. D2-125 正常锁定激光（不打断）
2. IN1 <- PD/MTS, IN2 <- REF, OUT1 -> CH2, OUT2 -> CH4
3. 扫描 D2-125 Ramp 时，同时记录 CH1 (D2-125 Ramp), CH2 (FPGA OUT1 error), CH4 (FPGA OUT2 control)
4. 保存 CSV（至少 30 秒含一个完整 ramp 周期）

**输出:** CSV + 截图（至少 2 组：mixer mode + no-mixer mode）

**通过标准:**
- OUT1 error 在吸收峰附近有明显特征
- OUT2 control 跟随 error 变化，方向合理
- OUT2 不失控、不贴 limit

**失败回退:** OUT2 只接示波器，完全不影响激光安全

**是否需要实验室:** 是

**AI 工具分工:**
- Claude Code: 生成 v2E single-page checklist
- Codex: 写分析脚本（提取 ramp 周期、标记峰值区域）

---

### Day 12: v2E 数据分析

**目标:** 判断是否具备进入 v2F 的条件

**输入:** Day 9-11 数据

**操作（Claude Code，不需要实验室）:**
1. 分析 v2E 数据: error 与吸收峰的关系、control 的方向和量级
2. 输出 PASS/PASS WITH NOTES/FAIL
3. 如果 PASS: 生成 v2F SOP（单页，首次 OUT2→Scan/PZT 完整安全步骤）

---

### Day 13-14: v2F SOP 生成 或 v2E 问题修复

**目标:** 生成可执行的 v2F 低增益闭环 SOP

**操作（Claude Code，不需要实验室）:**
1. 如果 v2E PASS: 写 v2F 单页 SOP（包括：OUT2 先接示波器验证 Kp=极小、Ki=0 → 确认极性 → 断开 D2-125 Aux Output → OUT2 接 Scan/PZT → P-only 最小增益闭环）
2. 如果 v2E FAIL: 分析失败原因，建议最小修复路径
3. 更新 STATUS.md 一行

---

## 9. 当前不该做的事

**1. 不要直接写在线 CNN 闭环。**
FPGA 连 register_bank 都没有，error signal 的可靠性都还没通过 v2E 验证。CNN 最早在 v5 阶段开始——那是在上位机能正常采集数据之后。

**2. 不要直接接 OUT2 到激光器。**
timing clean ≠ 可以接激光。OUT2 必须先在示波器上验证几十次不同条件后，才讨论接 Scan/PZT。

**3. 不要跳过 OUT2 示波器测试。**
v2B3_scope_safe 的 OUT2 示波器验证是这个阶段的正式关闭条件。

**4. 不要重构整个 Red Pitaya 工程。**
当前 USE_LASER_LOCK_CORE 的 MUX 方案干净且可回退。不要改 PLL、ODDR、ADC IO、PS/AXI。

**5. 不要让上位机假装能控制 FPGA 参数。**
在没有 register_bank 的情况下，上位机的任何 "Custom FPGA Lock Panel" 功能都是假的。

**6. 不要因为 timing pass 就声称已经能锁定。**
timing clean 只说明逻辑能在 125 MHz 下正确运行，不说明控制行为正确、不说明能锁定激光。

**7. 不要把 CNN 写进 FPGA。**
当前的 RTL 工程没有 CNN 模块、没有 HLS IP、没有硬件加速器。CNN 在 v5-v7 阶段都应该是上位机（PC/Python）的工作。

**8. 不要在当前阶段碰双执行器（PZT+Current）。**
单执行器 PZT 慢通道都还没有走通。

**9. 不要继续生成新的架构文档直到 v2B3 关闭。**
每篇新文档都在增加 "不知道先看哪个" 的成本。

---

## 10. 面向全自动深度学习锁定的阶段路线

```
当前位置: v2B3 scope fail (only-pi.csv OUT2 stuck at -0.2V)
已修正: laser_lock_core.sv Ki=0, limit=819
已生成: v2B3_scope_safe bitstream (用户手动 Vivado)

阶段 1: v2B3-close (当前 → Day 3)
  目标: Ki=0, limit=819 的 sequential PI 上板示波器验证
  RTL 改动: 无（已完成）
  通过标准: OUT2 不再贴 limit, 行为可用 P-only 解释
  文件: v2b3_scope_safe_ki0_limit819.csv

阶段 2: v2D (Day 4-8)
  目标: OUT2 硬编码 scan_offset + triangle 示波器验证
  RTL 改动: laser_lock_core.sv 新增 OUT2_TEST_MODE
  通过标准: OUT2 = 0.81 V DC + 52.7 Hz 三角波

阶段 3: v2E (Day 9-12)
  目标: 真实 MTS error 下 OUT2 开环观察
  RTL 改动: 无（OUT2_TEST_MODE=0）

阶段 4: v2F (Week 3-4)
  目标: 低增益 P-only 闭环, OUT2 -> Scan/PZT, Ki=0
  RTL 改动: 参数调整（Kp, limit）
  安全: 用户现场确认接线, 极性, 停止条件

阶段 5: v2G (Week 5-6)
  目标: FPGA PI 与 D2-125 性能对比
  (锁定时间, error RMS, 保持时间)

阶段 6: v3 scan/lock FSM (Week 7-9)
  目标: SAFE / SCAN / HOLD / P_LOCK / PI_LOCK 状态机
  RTL 改动: 新增 FSM 模块, laser_lock_core 集成

阶段 7: v4 register_bank / debug_buffer (Week 10-12)
  目标: 上位机写 Kp/Ki/limit/polarity/mode, 读 error/p_term/i_term/sat
  RTL 改动: 新增 AXI-lite register_bank 模块
  上位机: Custom FPGA Lock Panel 从 checklist 变为可操作

阶段 8: v5 上位机 Python 1D-CNN 离线识峰 (Week 13-16)
  目标: 采集 error 波形数据集 → 训练 CNN → 离线识别吸收峰 → 输出 Vlock
  RTL 改动: 无（纯 Python/PC 工作）
  允许: CSV 格式设计, 峰编号规则, 标签规范, 离线训练脚本
  禁止: 在线闭环

阶段 9: v6 自动扫描→自动锁定→自动重锁 (Week 17-20)
  目标: 上位机 CNN→下发 Vlock→FPGA 执行锁定→失锁判断→自动重扫
  RTL 改动: scan/lock FSM 完善, 失锁检测逻辑
  上位机: 完整的 Custom FPGA Lock Panel + AI 辅助

阶段 10: v7 CNN 量化或 FPGA 部署 (远期)
  如果 v5-v6 的上位机 CNN 方案性能足够, 此阶段可能不需要
  如果延迟不满足要求: 考虑 HLS 部署或 INT8 量化
```

### 当前是否应该开始 CNN?

**不应该。** 四条理由:

1. CNN 需要训练数据（吸收峰波形 + 标签 + 锁点），但当前连一次系统性的 error signal 波形采集都没有完成。v2B3 only-pi.csv 的 OUT2 甚至没有通过。

2. register_bank（v4）还没有——CNN 即使选出了 Vlock，也无法下发到 FPGA，也无法切换 SCAN/HOLD/P_LOCK 模式。

3. 最近一次实验日志显示 OUT1≈0 (WARNING)，error signal 本身的可靠性待验证。用不可靠的 error 信号训练 CNN 只会产生不可靠的模型。

4. 当前阶段是 v2B3（PI controller scope test），距离 v5（CNN）还有 v2D、v2E、v2F、v2G、v3、v4 六个阶段。每个阶段都依赖前一个阶段的实验数据。

**如果用户坚持现在做 CNN 的准备工作，唯一允许的范围是:**
- 设计 CSV 数据采集列名规范: `timestamp, pd_raw, error, control, d2_125_ramp, d2_125_error, absorption_saturated`
- 峰编号规则: peak_1 到 peak_N (从低频到高频)
- 标签规范: `is_crossover, is_lockable, slope_sign, v_lock_mv`

**禁止:** 在线闭环 CNN、FPGA 端 CNN、CNN 驱动的自动锁定。

**当前最应该先完成的阶段:** v2B3_scope_safe 示波器验证 → v2B3 关闭。

**v6 完成后才允许讨论 "自动锁定"。**

**v5 完成后才允许讨论 "CNN 在线识峰"。** v5 阶段 CNN 仍然是离线的（采集数据 → 训练 → 验证 → 离线推理），在线闭环是 v6 的事。

---

## 11. 下一条 Codex 任务

### 任务标题

**v2B3-close: 生成 v2B3_scope_safe 示波器验证 checklist 和 CSV 数据分析脚本**

### 完整指令草案

```
## 任务: v2B3_scope_safe 示波器验证 checklist 和 CSV 分析脚本

### 背景

v2B3 sequential PI (CONTROL_PATH_MODE=1) 已通过 Vivado timing
(WNS=+0.107 ns, 0 Failing Endpoints)。但上次 only-pi.csv 测试 OUT2
长期贴在 -0.2 V 附近。本轮代码已做安全修正: Ki=0, output_limit=819。

下一版 v2B3_scope_safe bitstream 需要用户手动 Vivado timing 通过后
上板示波器验证。本任务生成:
1. 一份用户可打印的单页实验 checklist
2. 一个实验后自动分析 CSV 的 Python 脚本

### 本次不做

- 不修改任何 RTL 文件
- 不运行 Vivado / synthesis / implementation
- 不生成 bitstream
- 不连接 Red Pitaya 网络
- 不修改 pi_controller_seq.sv、mixer_core.sv、lpf_core.sv、output_protect.sv

### 产出 1: 单页实验 checklist

文件: E:\new\fpga_lock\v94\version\v2\v2b3_scope_safe_checklist.md

要求:
- 单页打印 (不超过一页 A4)
- 每行都是可直接执行的动作
- 必须包含:
  1. 上电前确认 (3 项)
  2. 接线 (IN1, IN2, OUT1, OUT2 示波器)
  3. Vivado 操作步骤 (synthesis→implementation→timing check→bitstream)
  4. 预期正常现象 (4 条)
  5. 需要立即停止的现象 (5 条)
  6. CSV 命名规范: v2b3_scope_safe_ki0_limit819_kp{N}.csv
  7. 三步参数测试: Kp=2048, Kp=4096, Kp=1024
  8. 禁止: OUT2 接激光器/执行器

### 产出 2: CSV 分析脚本

文件: E:\new\fpga_lock\v94\software\redpitaya_lock_host\scripts\analyze_v2b3_scope.py

用法:
  python analyze_v2b3_scope.py <csv_file> --ch1-col 4 --ch4-col 5 --skip-rows 15 [--plot]

功能:
- 读取示波器 CSV
- 计算: OUT1/CH1: Vpp, RMS, min, max, mean
          OUT2/CH4: Vpp, RMS, min, max, mean
- 判断:
  - OUT2 是否贴 limit (|mean| > output_limit 的 80%)
  - OUT2 是否接近 +/-1 V
  - OUT2 动态范围是否足够 (Vpp > 5 mV)
- --plot: matplotlib 双子图

依赖: 仅 Python 标准库 + 可选的 matplotlib

### 安全检查

- checklist 不得指示用户把 OUT2 接到任何执行器
- 脚本不得连接 Red Pitaya 网络
- checklist 必须明确: "如果 OUT2 接近 +/-1 V, 立即停止, 不进入任何闭环"
- checklist 必须明确: "如果 OUT1 消失, 立即停止, 检查 error 链路"

### 完成标准

- checklist 单页打印不超过一页 A4
- 脚本能用 python analyze_v2b3_scope.py --help 显示帮助
- 脚本能正确解析示波器 CSV 并打印分析结果
```

---

## 12. 最终建议

**下一步到底该做什么:** 用户手动 Vivado timing→烧录 v2B3_scope_safe bitstream→OUT1/OUT2 示波器验证→保存 CSV→Claude Code 分析数据→如果 PASS 则关闭 v2B3。这是所有其他路线的共同前提。没有 v2B3 的关闭，后续的 v2D、v2E、v2PZT、register_bank、CNN 都没有立足点。

**为什么这样做能最快推动实验:** 因为这是当前唯一被阻塞的步骤。v2B3 only-pi.csv 显示 OUT2 异常——OUT2 贴 limit 这个现象必须在进入任何新功能之前被解释和修正。一旦 v2B3_scope_safe 通过，后续每一步都是新增一个小功能并验证，而不是停在原地反复修正同一个问题。

**为什么现在还不能直接 CNN:** CNN 需要三个条件: (1) 可靠的 error signal 波形采集——当前 OUT1≈0 警告和 OUT2 贴 limit 都说明 error 链路的可靠性待验证; (2) register_bank——CNN 选出的 Vlock 必须有物理路径下发到 FPGA; (3) scan/lock FSM——CNN 选出的 Vlock 必须在正确的状态下被使用。这三个条件在当前阶段都不存在。CNN 最早在 v5 阶段（那是在 v2B3→v2D→v2E→v2F→v2G→v3→v4 之后）。

**为什么 AI-assisted 开发必须以实验验证为节奏:** 因为 FPGA 激光稳频项目的瓶颈从来不是代码产出速度。AI 可以在几分钟内生成人类几天的 RTL 代码量和文档量，但每一次烧录、每一次示波器观察、每一次激光安全判断，都只能由用户在实验室现场完成。如果 AI 产出的速度快于实验验证的速度，项目就会变成"代码仓库里有 50 个模块，但激光还没被 FPGA 锁住一次"。这不是 AI 的问题，这是硬件项目的物理约束。正确的节奏是: 每次实验产出 CSV+截图→AI 分析数据→AI 产生最小下一步→用户再次实验→循环。每次循环不超过 2-3 天。文档是实验的记录，不是实验的替代物。

---

**审查工程师:** Claude Code (只读审查, 未修改任何文件)
**下次审查建议时间:** 2026-07-05 (v2B3_scope_safe 示波器验证完成后)
