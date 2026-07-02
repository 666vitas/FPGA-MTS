# PROJECT_PROGRESS_AND_AI_WORKFLOW_REVIEW

## 审查日期

2026-07-02

## 审查范围

只读审查，未修改任何文件，未运行 Vivado，未烧录 Red Pitaya。
审查目录：`E:\new\fpga_lock\v94`

## 审查证据

### git 状态

```text
git log --oneline -10:
529388c Update v94 project code and documents
9b88257 Update v94 project code and documents
b376479 Update v94 project code and documents
5e0771a Update v94 project code and documents
8b7ddf2 Update v2 text-level RTL docs and project records
...
```

仓库中大量 Vivado 生成文件（stub.v、cache 文件）处于 modified 状态，但 RTL 源文件（sv）大部分未被修改。
唯一实质性用户修改的文档：GPT_README.md、experiment_log_20260630_203915.md。

### Vivado Timing（v2B3 mode=1 sequential PI）

```text
来源: v0.94/exp/v2/impl_1/red_pitaya_top_timing_summary_routed.rpt
日期: 2026-06-30 21:20:43
Setup WNS: +0.155 ns, 0 Failing Endpoints
Hold WHS:  +0.057 ns, 0 Failing Endpoints
最差路径位于 i_scope（官方 scope 模块），不在 laser_lock_core 或 pi_controller_seq。
结论：v2B3 mode=1 sequential PI timing clean，验证通过。
```

---

## 1. 总体结论

**PASS WITH NOTES**

当前规划能够完成项目，但存在一个系统性问题：文档体系正在自我膨胀，而实验推进速度跟不上文档更新速度。AI 一直在写文档、更新 STATUS、生成 NEXT_STEPS，但用户实际的示波器上板验证仍然停留在 v2B1 P-only（2026-06-22）和最近的 Aux/PZT 示波器数据采集（2026-07-01）。

**能否加快实验进度？** 可以，但需要强制约束 AI 文档产出，让 AI 输出更多直接推动实验的产物（checklist、SOP、data analysis script），而不是更多架构文档。

**主要问题：** 文档数量已超过实验数据数量。STATUS.md 长达 486 行，V2_NEXT_STEPS.md 长达 378 行，V2_EXPERIMENT_SOP.md 长达 649 行，但实际可执行的 "下一步" 指令散落在 5-6 个文件中，没有一个人看了就能去实验室执行的单页清单。

---

## 2. 当前项目真实阶段

### 硬件链路

```text
PD -> v1 既有带通/放大链路 -> Red Pitaya IN1 (MTS 信号, +/-1 V 内)
模拟 REF 4.6 MHz -> Red Pitaya IN2 (REF 信号, +/-1 V 内)
Red Pitaya OUT1 -> 示波器 CH2 (FPGA mixer+LPF error observation)
Red Pitaya OUT2 -> 示波器 CH4 (FPGA sequential PI control, 不可接激光)
D2-125 继续独立完成真实激光锁定（Servo Output + Aux Output）
```

### FPGA 链路

```text
red_pitaya_top.sv:
  USE_LASER_LOCK_CORE = 1
  LASER_LOCK_OUTPUT_MODE = 3 (mixer + LPF)
  LASER_LOCK_CONTROL_PATH_MODE = 1 (sequential PI)

IN1 + IN2
-> mixer_core.sv (14-bit signed 乘法器，已通过上板验证)
-> lpf_core.sv (post-mixer 低通滤波器，已通过上板验证)
-> output_protect.sv (安全门，已通过上板验证)
-> protected_error -> OUT1 error observation

protected_error
-> pi_controller_seq.sv (15-state sequential PI, timing clean, Ki=16)
-> control_o -> OUT2 scope-only
```

### 上位机能力

```text
Official SCPI Mode: 能控制 OUT2 三角波、采集 IN1/IN2
Custom FPGA Mode: OUT1 和 OUT2 由 FPGA RTL 驱动
  上位机不能写 custom FPGA 参数（没有 register_bank）
  上位机不能切换 SCAN/HOLD/P_LOCK/PI_LOCK
  上位机不能读取 FPGA 内部 debug 信号
  Custom FPGA Observe Mode 只是手动记录示波器读数
  Lock Workflow Mode 是 checklist 不是实现的控制器
```

---

## 3. 当前规划的优点

1. **安全边界极其清晰。** 所有文档反复强调 OUT2 只能接示波器、禁止接激光、禁止并联 D2-125。这些安全语句冗余但必要。

2. **阶段划分合理。** v2B3 -> v2D -> v2E -> v2F -> v2G 的路线图是教科书级的逐步替代方案，每一步都有明确的输入/输出/通过标准/不能声称什么。

3. **对 AI 工具的边界有清醒认识。** GPT_README.md 明确规定了 Codex 不运行 Vivado、Claude Code 只读审查、用户手动操作 Vivado/烧录/接线。这是防止 AI 幻觉伤害硬件的关键约束。

4. **最新 Aux/PZT 数据已经校准了后续路线。** 用户实验确认了 D2-125 Aux Output 是 0.81 V DC 偏置 + 小三角波，使 v2PZT-1 的 scan_offset/triangle 有了物理依据。

5. **timing 风险已经关闭。** v2B3 sequential PI 的 Vivado timing 已通过（WNS=+0.155 ns），最差路径不经过 PI 逻辑。这消除了一个主要的技术风险。

---

## 4. 当前规划的风险

1. **AI 写代码和写文档的速度远快于实验验证。** STATUS.md 从 2026-06-14 到 2026-07-01 已经记录了 10 个日期快照，V2_NEXT_STEPS.md 记录了 7 个日期的"下一步"，但实际只有 2 次上板测试（v2B1 P-only 和 Aux/PZT 示波器数据采集）。文档产出量远超实验产出量。

2. **"下一步"在多处出现且不完全一致。** STATUS.md 说下一步是 v2PZT-1 SAFE/SCAN/HOLD；V2_NEXT_STEPS.md 说下一步是 v2B3-close -> v2PZT-DOC -> v2PZT-RTL-SAFE-SCAN-HOLD；V2_EXPERIMENT_SOP.md 说下一步是 OUT1/OUT2 示波器验证。同一个人盯着三个文件不知道该先去实验室做什么。

3. **平台分裂风险。** 项目中同时存在 guanfang-v0.94、v0.94、v-weifang 三套工程。git status 显示三套工程的大量 Vivado 生成文件都在 modified 状态。虽然 GPT_README.md 禁止使用 weifang 目录，但这些目录的存在增加了混淆成本。

4. **上位机功能过度设计风险。** HOST_APP_V2_DESIGN.md 描述了四个 GUI 页面、两套连接模式、未来 Custom FPGA Lock Panel，但 FPGA 侧连一个 register_bank 都还没有。上位机文档已经画了 AI 识峰和自动重锁的架构图，但基础的 "OUT2 示波器观察 sequential PI" 这一步甚至还没有按 SOP 完成。

5. **实验记录不规范。** 最近一次实验日志 experiment_log_20260630_203915.md 报告 OUT1=0 且 safety_level=WARNING，但 STATUS.md 和讨论路线中完全没有跟进这个问题。如果实验本身有异常（OUT1=0），那么基于 "error signal 正常" 假设的所有后续讨论都要悬置。

---

## 5. 是否适合用户这种 AI-assisted 开发方式

**结论：部分可行，但必须建立严格的 AI 角色分离和产出约束。**

### AI 可以做（且质量可靠）

- RTL 模块设计（mixer_core、lpf_core、pi_controller_seq 都是 Codex 生成的高质量代码）
- testbench 编写和 XSim 仿真
- Python 上位机界面和 SCPI 通信
- 数据分析脚本（读取 CSV 计算 Vpp/RMS/mean）
- 文档整理和架构文档
- 实验 SOP（安全边界、通过标准、停止条件，这些是 Claude Code 的强项）
- 代码审查（Claude Code 的定位检查和 timing 风险评估）
- Vivado report 解读（WNS/TNS/Failing Endpoints 等）

### AI 不能替用户完成

- 光路调整（反射镜、EOM、λ/4 波片等）
- 接线确认（确认 PD 信号在 +/-1 V 内、确认 REF 幅度合理）
- 示波器读数（确认波形、判断异常）
- Vivado GUI 手动操作（打开 .xpr、Add Sources、Run Synthesis/Implementation、Generate Bitstream）
- 判断信号是否过压（OUT2 是否接近 +/-1 V）
- 判断激光是否跳模
- 安全连接 OUT2 到执行器（这是用户必须在现场决定的操作）
- 实验现场异常处理（断线、干扰、设备故障）

### 必须建立的 AI 工作流

如果不建立下面的工作流，项目最终会变成"AI 写了 100 个文档，但激光还没被 FPGA 锁住"。

```text
ChatGPT:
  职责: 总体规划 + 阶段拆分 + 基于实验数据更新路线
  每次输出必须引用: 最新的实验数据（CSV、截图、用户报告）
  禁止: 在用户没有提供新实验数据时，再写新的架构规划

Codex:
  职责: 小步 RTL 实现 + testbench + Python 脚本
  每次只能实现一个明确可测试的功能
  禁止: 一次修改多个模块、运行 Vivado、生成 bitstream

Claude Code:
  职责: 只读审查 + timing 风险评估 + 实验安全检查
  每次审查必须输出: PASS / PASS WITH NOTES / FAIL
  禁止: 修改文件、运行 Vivado

用户:
  职责: Vivado 手动操作 + 烧录 + 示波器观察 + 数据记录 + 安全判断
  每次实验后必须输出: CSV 文件 + 截图 + 实验日期和参数

核心流程:
  用户报告实验结果
  -> Claude Code 审查实验数据，判断是否通过当前阶段
  -> 如果通过，ChatGPT/Codex 生成下一阶段的单个小任务
  -> 用户执行下一阶段
  -> 循环
```

---

## 6. 最快推进路线（按优先级）

1. **关闭 v2B3：完成 OUT1/OUT2 示波器验证（mode=1 sequential PI）。**
   这是 v2B3 的正式关闭条件。当前 timing 已通过，但尚未正式记录过示波器截图和数据。
   OUT1 应能看到 FPGA error（如果 OUT1=0 的问题未解决必须先解决），OUT2 应能看到 sequential PI 输出。
   这是后续所有 v2D/v2E/v2F 的前提。

2. **v2D：OUT2 示波器空载测试（scan_offset + triangle）。**
   不等 register_bank，先做一个烧录时硬编码的 scan_offset=0.81 V + 小三角波版本。
   只用示波器验证，不加 scan/lock FSM。
   这是验证 "Red Pitaya OUT2 能否输出正确 DC 偏置" 的最快方法。

3. **v2E：真实 MTS error 下 OUT2 开环观察。**
   这是已知的最短路径：IN1 接真实 PD 信号，OUT1 观察 error，OUT2 观察 sequential PI 输出。
   不需要改 RTL，只需要接线和记录。

4. **v2F：低增益 P-only 短时闭环（Ki=0，极小 Kp）。**
   只有在 v2D 和 v2E 都通过后才进入。最开始只接 Scan/PZT（替代 D2-125 Aux Output），
   不碰 Servo Output。Ki=0，Kp 从极小值开始。

5. **v3 register_bank + scan/lock FSM。**
   这是让上位机能控制 FPGA 的基础。在此之前，上位机不需要再做任何 Lock Panel 功能。

---

## 7. 两周实验推进计划

每个任务只做一件事。失败后回退到上一个已知安全状态。

### Day 1-2：关闭 v2B3 OUT1/OUT2 示波器验证

**目标：** 正式记录 mode=1 sequential PI 的 OUT1 和 OUT2 示波器数据

**输入：**
- 当前 v2B3 mode=1 bitstream（用户 2026-06-30 已生成，timing clean）
- 示波器和接线

**操作（用户）：**
1. 确认烧录的是 timing-passed v2B3 mode=1 bitstream
2. 接线：IN1 <- PD/BF 信号，IN2 <- REF，OUT1 -> CH2，OUT2 -> CH4
3. 如果 CH2 OUT1=0，先查输入信号是否存在（上次 experiment_log 报告 OUT1 接近零）
4. 保存示波器截图和 CSV
5. 小范围改变 Kp（从 2048 到 4096 到 1024），观察 OUT2 变化

**输出：** CSV 文件 + 示波器截图 + 简单记录（不是新文档）

**通过标准：**
- OUT1 可见 FPGA error（应该能观察到几十 mVpp 的 MTS error signal）
- OUT2 随 error 变化，方向合理
- OUT2 不接近 +/-1 V，不随机跳变
- 数据保存到 `v0.94/exp/v2/v2b3-out1-out2/` 目录

**失败回退：**
- 如果 OUT1=0：检查 IN1 是否有 PD 信号输入，检查 PD 带通/放大链路，检查 OUTPUT_MODE=3
- 如果 OUT2 异常：检查 CONTROL_PATH_MODE=1，检查 pi_controller_seq.sv 是否在 Design Sources
- 回到 mode=0 P-only 确认 OUT1/OUT2 通路没有硬件问题

**AI 工具分工：**
- Claude Code：生成 v2B3 示波器验证 checklist（单页，不是新文档）
- Codex：如果 OUT1=0，帮用户写一个简单的 mode=0/1/2/3 切换排查脚本
- ChatGPT：不参与，等实验数据出来再说

### Day 3：数据分析和 v2B3 关闭决策

**目标：** 判断 v2B3 是否可以正式关闭

**输入：** Day 1-2 的实验 CSV 和截图

**操作（Claude Code）：**
1. 读 CSV 计算 OUT1 Vpp/RMS/mean，OUT2 Vpp/RMS/mean，OUT2/OUT1 比例
2. 对比预期（Ki=16 时 OUT2 应有缓慢基线移动但不爬升到 +/-1 V）
3. 输出 PASS / PASS WITH NOTES / FAIL

**输出：** 一行状态更新到 STATUS.md

**通过标准：** OUT1 可见，OUT2 安全和可解释

**失败回退：** 回到 mode=0 P-only 安全模式，查明问题

**AI 工具分工：**
- Claude Code：分析 CSV，输出结论
- Codex：写 CSV 分析 Python 脚本

### Day 4-5：v2D OUT2 示波器 scan_offset + triangle 验证

**目标：** 生成一个临时 bitstream，让 OUT2 输出 scan_offset=0.81 V + 小三角波

**输入：**
- Claude Code 写的 RTL 任务文档（只描述一个简单的 scan_offset + triangle 生成器）
- 当前 v2B3 代码

**操作（Codex）：**
1. 在 laser_lock_core.sv 中新增一个参数化选项：
   `OUT2_TEST_MODE`，当 =1 时，control_o 直接输出 scan_offset + triangle
2. 不修改 pi_controller_seq.sv
3. 不新增 FSM、不新增 register_bank
4. testbench 只验证数字波形形态（SAFE=0, SCAN=offset+triangle）

**操作（用户）：**
1. 打开 Vivado，确认新 RTL 文件在 Design Sources
2. Run Synthesis -> Implementation -> 检查 timing -> Generate Bitstream
3. 烧录后 OUT2 只接示波器
4. 确认波形是约 0.81 V DC 偏置 + 约 52.7 Hz 小三角波

**输出：** 示波器截图 + timing report

**通过标准：**
- Timing 通过（WNS >= 0，TNS = 0）
- OUT2 示波器波形：0.81 V offset + 小三角波
- OUT2 不超过 +/-1 V

**失败回退：**
- Timing fail：不烧录，找 Claude Code 审查路径
- 波形不对：检查 offset 和 amplitude 参数，检查 DAC 到电压的转换
- OUT2 接近 +/-1 V：立即停止，降低 amplitude

**AI 工具分工：**
- Claude Code：写 RTL 任务 spec（单文件，<50 行任务描述）
- Codex：实现 RTL（只在 laser_lock_core.sv 新增一个 generate 分支）
- ChatGPT：不参与

### Day 6-7：休息或缓存日

**目标：** 不推新功能。整理数据、整理 git、删除不必要的文档。

**操作（用户 + Claude Code）：**
1. 整理 v2B3 实验数据目录
2. git commit（把 v2B3 和 v2D 的文件整理好）
3. Claude Code 审查 git status，建议哪些 Vivado 生成文件应该被 .gitignore
4. 把实验 CSV 文件按日期命名

**AI 工具分工：**
- Claude Code：审查文件组织，建议 .gitignore 更新
- Codex：不参与

### Day 8-10：v2E 真实 MTS error 下 OUT2 开环观察

**目标：** 用真实 PD 信号跑 v2B3 sequential PI，观察 OUT1 error 和 OUT2 control，但仍然只接示波器

**输入：**
- v2B3 mode=1 bitstream（如果 OUT1=0 问题已解决）
- 真实实验光路和 D2-125 继续独立锁定

**操作（用户）：**
1. 保持 D2-125 独立锁定激光（不打断 D2-125 的锁定链路）
2. IN1 <- PD/MTS 信号（确认在 +/-1 V 内）
3. IN2 <- REF（确认在 +/-1 V 内）
4. OUT1 -> CH2，OUT2 -> CH4
5. 在 D2-125 保持锁定的同时，观察 FPGA OUT1 error 和 OUT2 control
6. 保存 CSV 和截图

**输出：** CSV + 截图

**通过标准：**
- OUT1 能看到与吸收峰同步的 error signal
- OUT2 跟随 error 变化，在 Peak 附近能看到相应的 control 响应
- OUT2 不失控

**失败回退：** OUT2 只接示波器，随时可断开，不威胁激光

**AI 工具分工：**
- Claude Code：生成 v2E 实验 checklist
- Codex：写 CSV 分析脚本，自动提取 error zero-crossing 附近的 OUT2 值

### Day 11-12：数据分析与 v2E 结论

**目标：** 判断 v2E 是否通过

**操作（Claude Code）：**
1. 分析 v2E 数据：OUT1 error 与吸收峰的关系、OUT2 control 的方向和量级
2. 输出 PASS / PASS WITH NOTES / FAIL
3. 更新 STATUS.md 一行

### Day 13-14：准备 v2F 低增益闭环 SOP 或回退整理

**目标：** 如果 v2E 数据支撑，生成 v2F 低增益 P-only 闭环 SOP
**如果 v2E 数据不支撑：** 查明问题、修复、重跑

**操作（Claude Code）：**
1. 如果 v2E PASS：生成 v2F 单页 SOP（OUT2 首次接 Scan/PZT 的安全步骤）
2. 如果 v2E FAIL：分析失败原因，建议最小修复

**AI 工具分工：**
- Claude Code：生成 v2F SOP（必须是单页）
- Codex：如果需要修改 RTL 参数（Kp/Ki/limit），只改参数表，不赶新功能

---

## 8. 当前不该做的事

以下任务如果现在开始，会严重拖慢实验进度：

1. **不要直接写在线 CNN 闭环。** 当前连 error signal 的正确性都还没有充分验证（最近一次实验日志显示 OUT1=0），更谈不上 CNN 训练集。CNN 最早应该在 v5 阶段开始（等 register_bank 和上位机数据采集通了再说）。

2. **不要直接接 OUT2 到激光。** 即使 timing clean、仿真通过，OUT2 必须先在示波器上验证几十次不同条件（不同 error 幅度、不同 Kp、不同 Ki），才能讨论接 Scan/PZT。

3. **不要跳过 OUT2 示波器测试。** v2B3 的 OUT2 scope verification 是 v2B 阶段的正式关闭条件，不是可选的。

4. **不要重构整个 Red Pitaya 工程。** 当前 USE_LASER_LOCK_CORE 的 MUX 方案干净且可回退。不要重新设计 top-level，不要动 PLL、ODDR、ADC IO、PS/AXI/DDR。

5. **不要给上位机加功能，直到 FPGA 有 register_bank。** 上位机 Lock Workflow Mode 已经是 checklist 而非实现。在 register_bank 就绪之前，不要给上位机添加任何 "Custom FPGA Lock Panel" 或 "AI 调参" 功能。

6. **不要在当前阶段处理双执行器（PZT + Current）。** 单执行器 PZT 慢通道都没有走通，双执行器是过度优化。

---

## 9. 面向全自动深度学习锁定的阶段路线

以下是从当前到最终目标的完整阶段图。当前位置：v2B3 刚 timing-pass，OUT1/OUT2 示波器验证待完成。

```text
阶段 1: v2B3-close (当前 → ~Day 3)
  关闭 v2B3：OUT1/OUT2 示波器验证通过
  交付：CSV + 截图，STATUS.md 一行更新

阶段 2: v2D (~Day 4-5)
  OUT2 示波器空载测试：硬编码 scan_offset + triangle
  交付：示波器截图确认 0.81 V offset + 三角波

阶段 3: v2E (~Day 8-10)
  真实 MTS error 下 OUT2 开环观察
  交付：OUT1 error 和 OUT2 control 在真实信号下的 CSV

阶段 4: v2F (~Week 3-4)
  低增益 P-only 短时闭环：OUT2 -> Scan/PZT，替代 D2-125 Aux Output
  交付：OUT1 error 在闭环下变小的证据

阶段 5: v2G (~Week 5-6)
  FPGA PI 与 D2-125 性能对比
  交付：对比报告（锁定时间、error RMS、保持时间）

阶段 6: v3 scan/lock FSM (~Week 7-9)
  SAFE / SCAN / HOLD / P_LOCK / PI_LOCK 状态机
  交付：OUT2 能按 FSM 自动切换模式

阶段 7: v4 register_bank + debug_buffer (~Week 10-12)
  上位机能写 FPGA 参数（Kp/Ki/limit/polarity/mode）
  上位机能读 FPGA 内部 debug 信号（error、p_term、i_term、sat）
  交付：上位机 Custom FPGA Mode 下能调参数

阶段 8: v5 上位机 Python 1D-CNN 离线识峰 (~Week 13-16)
  离线数据采集格式设计
  峰编号规则
  标签规范
  训练集组织
  交付：能在 PC 上识别吸收峰并给出 Vlock 的 Python 脚本

阶段 9: v6 自动扫描、自动锁定、自动重锁 (~Week 17-20)
  上位机调用 CNN -> 选 Vlock -> 下发参数 -> FPGA 执行锁定
  失锁判断 -> 自动重扫重锁
  交付：从扫描到锁定的完整自动流程

阶段 10: v7 CNN 量化或 FPGA 部署（远期）
  如果 v6 的上位机 CNN 方案性能足够，此阶段可能不需要
```

**当前是否应该开始 CNN？**

**不应该。**

理由：
1. CNN 需要训练数据（吸收峰波形 + 标签），但当前连一次正式的 error signal 示波器截图数据都还没有系统采集
2. register_bank 还没有，即使 CNN 选出了 Vlock，也无法下发到 FPGA
3. 实验日志显示 OUT1 曾接近零，error signal 的可靠性本身待确认
4. 在 error signal 都还没有通过 v2E 开环观察的情况下，做 CNN 属于跳过 80% 的基础验证工作

**如果可以开始，只允许：**
- 离线数据采集格式设计（CSV 列名规范：timestamp, pd_raw, error, control, d2_125_error, d2_125_ramp, absorption_saturated）
- 峰编号规则（peak_1, peak_2, ... peak_N，从低频到高频编号）
- 标签规范（is_crossover, is_lockable, slope_sign, v_lock_mv）
- 训练集组织（每个峰至少 50 个样本，每个样本包含 +/- 50 ms 的 error 波形窗口）

禁止进入：在线闭环 CNN、FPGA 端 CNN、CNN 驱动的自动锁定。

---

## 10. 下一条 Codex 任务

### 任务标题

**v2B3-close: 生成 v2B3 OUT1/OUT2 示波器验证 checklist 和 CSV 分析脚本**

### 完整指令草案

```text
## v2B3-close: OUT1/OUT2 Oscilloscope Verification Checklist and CSV Analysis Script

### Context

v2B3 sequential PI mode=1 has passed Vivado timing (WNS=+0.155 ns, 0 Failing Endpoints,
worst path in i_scope, not in laser_lock_core). The compiled bitstream has been generated
but not yet verified on the oscilloscope with a formal checklist and data analysis.

This task does NOT modify RTL. It does NOT run Vivado. It only produces two files:

1. A single-page checklist the user can print and take to the lab.
2. A Python CSV analysis script that reads oscilloscope CSV and computes validation metrics.

### Deliverable 1: v2B3 Oscilloscope Verification Checklist

Write a single-page Markdown file:
`E:\new\fpga_lock\v94\version\v2\v2b3_scope_checklist.md`

The checklist must be a single page (no scrolling on printed A4). It must include:

1. Pre-power-on checks (3 items)
2. IN1/IN2 wiring check (2 items, with voltage limits)
3. OUT1/OUT2 oscilloscope setup (CH2/CH4 settings)
4. Normal expected observations (4 items)
5. Abnormal conditions that require immediate stop (4 items)
6. Data recording: which CSV files to save, naming convention
7. A 3-step parameter variation test: Kp=2048, Kp=4096, Kp=1024

Do NOT embed long explanations. Every line must be directly actionable.

### Deliverable 2: CSV Analysis Script

Write a Python script:
`E:\new\fpga_lock\v94\software\redpitaya_lock_host\scripts\analyze_v2b3_scope.py`

This script reads a single oscilloscope CSV file and prints:

- OUT1/CH2: Vpp, RMS, min, max, mean
- OUT2/CH4: Vpp, RMS, min, max, mean
- OUT2/OUT1 ratio (using Vpp)
- Whether OUT2 approaches +/-1 V (yes/no)
- Whether OUT2 shows slow baseline drift (yes/no, based on mean vs time-windowed mean)

Usage:
```
python analyze_v2b3_scope.py <csv_file> [--plot]
```

If --plot is given, show a simple matplotlib figure with two subplots (OUT1 upper, OUT2 lower).
Do NOT use any heavy dependencies. Use only Python standard library for computation
and matplotlib for optional plotting.

Column mapping: the oscilloscope CSV format is unknown (varies by oscilloscope model).
Make the script accept command-line arguments to specify which CSV columns correspond to
CH2 and CH4:

```
python analyze_v2b3_scope.py <csv_file> --ch2-col 4 --ch4-col 5 [--skip-rows 15] [--plot]
```

Default: --ch2-col 4, --ch4-col 5, --skip-rows 15 (common Rigol defaults).

### Safety Boundaries

- This task writes only Markdown and Python. No RTL modifications.
- No Vivado, no synthesis, no implementation, no bitstream.
- The checklist must NOT instruct the user to connect OUT2 to any actuator.
- The analysis script must NOT connect to any Red Pitaya network interface.
```

### 为什么这条任务是当前最应该做的

1. **小步：** 不修改 RTL，只生成 checklist 和分析脚本。
2. **可审查：** checklist 只有一页，Claude Code 可以在 5 分钟内审查完毕。
3. **不扩大系统：** 不新增 register_bank、不新增 FSM、不修改任何 .sv 文件。
4. **能推动实验：** 用户拿着一页 checklist 就能去实验室完成 v2B3 的正式验证。做完后有了 CSV 数据，Claude Code 可以分析并决定是否关闭 v2B3。
5. **执行后让下一次上板更清楚：** 用户不会再面对 "不知道该测什么" 的问题。

---

**审查工程师签名：** Claude Code（只读审查，未修改任何文件）

**下次审查建议时间：** 2026-07-05（v2B3 OUT1/OUT2 示波器验证完成后）
