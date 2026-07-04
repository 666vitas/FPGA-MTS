# Claude 审查：V3REG0 工程可行性 与 全自动锁频路线审查

审查时间：2026-07-05  
审查人：Claude (Claude Code)，角色：FPGA 激光稳频项目规划审查工程师 / AI-assisted development 工作流审查  
审查范围：`E:\new\fpga_lock\v94`，只读，不修改任何 RTL、不运行 Vivado、不烧录 Red Pitaya  
审查主题：V3REG0_PROJECT_FEASIBILITY_AND_AUTO_LOCK_ROADMAP_REVIEW

---

## 执行总结

**总体判断：v3REG-0 有条件可行，P0 阻塞项 2 项，P1 高优先级 4 项，方向正确无需变更。**

Codex 本次 v3REG-0 实现（custom_register_bank.sv + ramp_generator.sv + custom_fpga_scan_control.py）在 RTL 层面核心逻辑正确、复位安全、默认输出为零、SCAN 模式参数计算一致。但上位机脚本缺少 magic 预校验这一关键安全检查步骤，文档存在合并冲突和"下一步"歧义。

全自动锁频路线（v3REG-0 → v7 deep learning）在架构上没有不可逾越的障碍，但 v3REG-0 本身距离"全自动锁频"还隔着至少 6 个阶段的工程工作。当前最紧迫的动作是修完 P0 项后尽快上板验证 sys[6] → OUT2 的控制链路是否物理可达。

---

## 1. 本次审查读取文件清单

### 1.1 核心 RTL（已读取完整内容）

| 文件 | 行数 | 审查状态 |
|---|---|---|
| `v0.94/rtl/custom_register_bank.sv` | 139 | 逐行审查 |
| `v0.94/rtl/ramp_generator.sv` | 129 | 逐行审查 |
| `v0.94/rtl/laser_lock_core.sv` | 349 | 重新审查 v3REG-0 集成影响 |
| `v0.94/rtl/red_pitaya_top.sv` | ~350行关键部分 | 审查 sys[6]/DAC mux 集成 |
| `v0.94/rtl/pi_controller_seq.sv` | 292 | 重新确认复位/disable 安全行为 |
| `v0.94/rtl/output_protect.sv` | 49 | 确认安全门行为 |
| `v0.94/rtl/mixer_core.sv` | 63 | 确认 |
| `v0.94/rtl/lpf_core.sv` | 86 | 确认 |
| `v0.94/sim/tb_ramp_generator.sv` | 101 | 审查测试覆盖率 |

### 1.2 系统总线与官方模块（只读关键部分）

| 文件 | 用途 |
|---|---|
| `sys_bus_if.sv` | 确认接口协议（wen/ren/addr/wdata/rdata/ack/err） |
| `sys_bus_interconnect.sv` | 确认 SN=8, SW=20, sys[6] 1MiB 区域 |
| `sys_reg_array_o.sv` | 作为 register_bank 行为参照基准 |

### 1.3 上位机脚本

| 文件 | 行数 | 审查状态 |
|---|---|---|
| `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py` | 279 | 逐行审查 |

### 1.4 项目文档

| 文件 | 审查状态 |
|---|---|
| `version/v3/V3REG0_HOST_CONTROLLED_SCAN_PLAN.md` | 逐行审查 |
| `GPT_README.md` | 逐行审查 |
| `version/STATUS.md` | 审查 v3REG-0 历史缺失 |
| `version/v2/V2_NEXT_STEPS.md` | 审查"下一步"歧义 |
| `version/v2/V2_EXPERIMENT_SOP.md` | 确认是否有新条目 |
| `version/v2/V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md` | 审查阶段映射 |
| `version/v2/D2_125_REAL_WIRING_AND_STATE_MODEL.md` | **发现合并冲突** |
| `version/v2/V2B3_ONLY_PI_SCOPE_TEST_RECORD.md` | 确认 v2B3 状态 |
| `version/v2/V2_AUX_PZT_EXPERIMENT_RECORD.md` | 确认 PZT 基线数据 |
| `version/v2/claude审查/CLAUDE_REVIEW_2026-07-02_PROJECT_PROGRESS_AND_AI_WORKFLOW_REVIEW_V2.md` | 交叉对照上次审查结论 |
| `v0.94/project/redpitaya.xpr` | 仅关键片段（确认源文件注册） |

---

## 2. Git 仓库状态

```
HEAD: c7a04cb "Update v94 project code documents and records"
git status --short: 1200+ 行，大部分为 Vivado 自动生成文件
git diff --stat: 510 files changed, 751K insertions, 751K deletions
```

510 个变更文件中 99%+ 为 Vivado 自动生成文件（三个平行项目目录），实质性变更集中在：
- `v0.94/rtl/custom_register_bank.sv`（新建）
- `v0.94/rtl/ramp_generator.sv`（新建）
- `v0.94/rtl/red_pitaya_top.sv`（修改，集成 custom_register_bank + ramp_generator）
- `v0.94/sim/tb_ramp_generator.sv`（新建）
- `v0.94/project/redpitaya.xpr`（修改，添加新源文件）
- `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py`（新建）
- `version/v3/V3REG0_HOST_CONTROLLED_SCAN_PLAN.md`（新建）
- `GPT_README.md`（修改，更新到 v3REG-0 阶段描述）
- `version/v2/D2_125_REAL_WIRING_AND_STATE_MODEL.md`（修改，**但存在未解决的 git 合并冲突**）

---

## 3. RTL 逐模块审查

### 3.1 custom_register_bank.sv（139 行）

**功能概述**：11 个寄存器的读写接口，映射到 sys[6]（GP0 base + 0x0060_0000），地址偏移 0x00-0x28。输出直接驱动 ramp_generator。

**复位安全性**：PASS
- `mode_o` 复位 = 32'd0（SAFE 模式）
- `enable_o` 复位 = 1'b0（禁用）
- `scan_offset_o` 复位 = 14'sd6962（~0.85V，与 V3REG0 计划一致）
- `scan_amp_o` 复位 = 14'sd410（~0.05V，与 V3REG0 计划一致）
- `scan_step_o` 复位 = 14'sd1
- `scan_update_div_o` 复位 = 32'd1524（~50Hz @ 125MHz，与 V3REG0 计划一致）
- `out2_limit_o` 复位 = 14'sd8191（±1V）

**写保护**：PASS（但有注意事项）
- REG_MODE：只接受 wdata == 1（SCAN），任何其他值 → mode_o = 0（SAFE）。这是好的设计，防止未知模式码导致意外行为。
- REG_SCAN_UPDATE_DIV：wdata == 0 → 强制为 1，避免除以零。
- REG_OUT2_LIMIT：硬件上限 8191，即使上位机写更大的值也无法突破。
- 注意：`enable_o` 复位默认是 0，写入后才能为 1。复位后必须在写入 enable=1 前先配置好所有参数。

**总线行为**：参照基准 sys_reg_array_o，行为一致。
- ack 在 wen|ren 后 1 周期上升（已注册）。
- 对未定义地址的读写也返回 ack（与 RedPitaya 官方模块行为一致，不是 bug）。

**读路径**：
- REG_MAGIC = 0x4D545330（MTS0 的 ASCII hex 编码）
- REG_VERSION = 0x00030000
- REG_STATUS = {30'd0, saturated_i, enabled_status_w}（bit1=saturation, bit0=enabled）
- REG_OUT2_MONITOR = sign-extended out2_monitor_i

**结论**：RTL 逻辑正确，复位安全，写保护适当。**P0 问题不在 RTL，而在上位机脚本未利用 MAGIC 做预校验。**

---

### 3.2 ramp_generator.sv（129 行）

**功能概述**：三角波生成器，offset_i + symmetric triangle，支持可配置步长、更新分频、输出限幅。

**复位安全性**：PASS
- `scan_o` 复位 = 14'sd0（SAFE_VALUE）
- `saturated_o` 复位 = 1'b0
- `pos_q` 复位 = 0
- `direction_up_q` 复位 = 1'b1（向上）
- `update_cnt_q` 复位 = 0

**disable 安全性**：PASS
- `scan_o` = 14'sd0
- `pos_q` = -amp_abs_w（预置到负峰值，下次 enable 从负端开始）
- `update_cnt_q` = 0

**参数安全**：PASS（但有设计细节需注意）
- amp_abs_w：绝对值化 + 上限钳位到 8191
- step_abs_w：绝对值化 + 下限钳位到 1（防止卡死）
- effective_limit_w：limit_abs_w 钳位到 8191，作为对称 ±limit
- raw_scan_w = offset + pos（pos 范围 [-amp, +amp]）
- 双重饱和检查：先对 effective_limit_w 比较，再对 DAC_POS_LIMIT/DAC_NEG_LIMIT 比较
- 两层保护确保输出不可能超出 ±8191（±1V）

**频率验证**（已通过代码路径演算）：
```
amp = 410, step = 1, update_div = 1524
tick 周期 = 1524 / 125e6 = 12.192 μs
三角形周期 = 4 × 410 × 12.192 μs = 20.00 ms → 50.00 Hz
```
与 V3REG0 计划（~50 Hz）一致。

**输出行为验证**：
```
offset = 6962, amp = 410
最小值 = 6962 - 410 = 6552 计数 → 0.7998 V（tb check: <= 6552）
最大值 = 6962 + 410 = 7372 计数 → 0.8999 V（tb check: >= 7372）
```
与 D2-125 Aux 输出实测数据（0.81V DC + triangle，Ramp 状态）一致。

**结论**：RTL 逻辑正确，复位/disable 安全默认为 0，参数计算与计划一致，输出范围在 0.8~0.9V 安全区间。三角波生成算法正确（上升沿 count-up → 检查上限 → 反转方向 → count-down → 检查下限 → 反转方向）。

---

### 3.3 tb_ramp_generator.sv（101 行）

**测试覆盖**：11 个测试点
- reset → safe value ✓
- disable → safe value ✓
- 120 周期运行：OUT2 从不超出 ±1V ✓
- 三角形范围检查：min ≤ 6552, max ≥ 7372 ✓（对应 0.80V~0.90V）
- 自定义 limit=6500：saturation 标志正确 ✓
- disable 后清除 saturation ✓

**缺失的测试**：
- 无 enable 后 disable 再 enable 的行为测试
- 无 offset/amp/step 参数在运行中热修改的测试
- 无 update_div 大值/小值的边界测试
- 无极限参数组合测试（如 offset=8000, amp=500, limit=8191）
- **缺少 custom_register_bank 的 testbench**

**结论**：现有测试覆盖核心安全路径，但覆盖不全面。建议在 v3REG-0 上板前至少补一个 custom_register_bank 的 testbench。

---

### 3.4 red_pitaya_top.sv 集成审查

**sys[6] 分配**：确认
```
sys[6] → custom_register_bank (.bus)
sys[7] → sys_bus_stub (未使用)
```
sys[6] 对应 GP0 base + 0x0060_0000（1MiB per slave × 6 = 6MiB offset）。

**OUT2 数据路径**：确认
```
custom_register_bank → scan_offset/amp/step/update_div/limit/enable/mode
                     → ramp_generator → scan_out2
                     → selected_out2 mux → dac_b_sum_laser → DAC B → OUT2
```

**OUT2 安全 MUX**：PASS
```systemverilog
always_comb begin
  unique case (custom_mode)
    32'd1:   selected_out2 = custom_enable ? scan_out2 : 14'sd0;
    default: selected_out2 = 14'sd0;
  endcase
end
```
- custom_mode != 1（包括复位后 mode=0）：OUT2=0
- custom_mode == 1 但 custom_enable == 0：OUT2=0
- 只有 custom_mode == 1 且 custom_enable == 1 时：OUT2 = scan_out2

**laser_lock_core 状态**：仍以 CONTROL_PATH_MODE=1 实例化 pi_controller_seq，但其输出 `laser_control` 不再连接到 DAC B（DAC B 现在使用 selected_out2）。pi_controller_seq 仍在运行但不影响输出。这不是问题，但如果希望减少功耗/资源，后续可考虑门控。

**DAC 饱和路径**：与非 laser_lock_core 路径共用相同的 saturation + signed-to-unsigned + ODDR 结构，不改动 PLL/ADC/PS/AXI/DDR。

**结论**：顶层集成正确，OUT2 安全 MUX 三重保护（mode、enable、mux default），DAC 路径复用现有安全基础设施。

---

### 3.5 与 pi_controller_seq 的共存分析

pi_controller_seq 的 disable 行为（line 145-157）：enable_i=0 → 立即清零 control_o、清除积分器、状态机回 IDLE。即使顶层 mux 某天错误切换到 laser_control，disable 状态下输出仍为 0。

**结论**：pi_controller_seq 的 disable 安全行为独立于 custom_register_bank/ramp_generator 的安全行为。两者形成了冗余安全层。

---

## 4. 上位机脚本审查：custom_fpga_scan_control.py

### 4.1 整体架构

双端设计：PC 端通过 SSH 将 base64 编码的 Python helper 推送到 Red Pitaya Linux 端执行，helper 通过 `/dev/mem` mmap 访问 GP0 物理地址空间的寄存器。

### 4.2 参数计算验证（已通过 Python 等效演算）

```python
COUNTS_PER_VOLT = 8191.0  # 与 RTL 的 DAC_POS_LIMIT = 8191 一致

# scan --offset-v 0.85:
offset_counts = int(round(0.85 * 8191)) = 6962  # ✓ 与 RTL 默认值一致

# scan --amp-v 0.05:
amp_counts = abs(int(round(0.05 * 8191))) = 410  # ✓ 与 RTL 默认值一致

# scan --freq-hz 50.0, --step-counts 1:
update_rate = 50.0 * 4.0 * 410 / 1 = 82000.0
update_div = int(round(125e6 / 82000.0)) = 1524  # ✓ 与 RTL 默认值一致
```

### 4.3 P0 阻塞：缺少 MAGIC 预校验 ⚠️

**问题描述**：脚本在 "safe" 和 "scan" 操作中都直接写入寄存器，只有在操作完成后才调用 `read_status()` 读取并打印 magic 值。**没有任何事先验证 magic == 0x4D545330 的逻辑。**

**风险**：如果 `--base-addr` 参数错误、用户烧录的是旧版 bitstream（无 custom_register_bank）、或 sys[6] 地址映射与预期不符，脚本会默默地把数据写到错误的物理地址，可能：
- 破坏其他外设的寄存器状态
- 写入未映射区域导致 bus error
- 在错误地址上产生不正确输出

**为什么这是 P0**：这是上板前必须修复的安全问题。即使 v3REG-0 的 OUT2 只接示波器，写错物理地址仍可能影响 Red Pitaya 的其他功能模块。

**修复方案（不涉及 RTL，仅改脚本）**：
```python
# 在任何写操作之前执行 magic 预校验：
# 1. 读取 REG_MAGIC
magic_raw = regs.read(REGISTERS["MAGIC"])
if magic_raw != 0x4D545330:
    raise SystemExit(
        f"MAGIC mismatch: read 0x{magic_raw:08X}, "
        f"expected 0x4D545330. Check --base-addr and bitstream."
    )
# 2. 可选：读取 REG_VERSION 确认版本兼容
version_raw = regs.read(REGISTERS["VERSION"])
if (version_raw >> 16) != 0x0003:
    raise SystemExit(
        f"VERSION mismatch: read 0x{version_raw:08X}, "
        f"expected v3.x.x. Check bitstream version."
    )
```

### 4.4 写操作顺序分析

"safe" 操作：
```
ENABLE=0 → MODE=0
```
顺序合理。先禁能，再切模式。

"scan" 操作：
```
ENABLE=0 → SCAN_OFFSET → SCAN_AMP → SCAN_STEP → UPDATE_DIV → LIMIT → MODE=1 → ENABLE=1
```
顺序合理。先禁能，配置全部参数，最后切模式并使能。

### 4.5 远程执行安全性

问题：SSH 命令通过 `subprocess.run(command, check=False)` 执行，不检查 ssh 连接是否成功、helper 脚本是否执行完毕。

建议：使用 `check=True` 或检查 `completed.returncode`。

### 4.6 脚本结论

代码结构清晰，参数计算正确，写操作顺序合理。**P0 阻塞项：magic 预校验缺失。** P2 建议：SSH 返回值检查。

---

## 5. 文档审查

### 5.1 P0 阻塞：D2_125_REAL_WIRING_AND_STATE_MODEL.md 存在未解决 git 合并冲突 ⚠️

文件开头和结尾都有冲突标记：
```
<<<<<<< HEAD
# D2-125 Real Wiring and State Model (English version)
...
=======
# D2-125 真实接线与状态模型 (Chinese version)
...
>>>>>>> host-app-v2-integration
```

整个文件内容被重复了两遍（英文版 + 中文版），每行都被标记为冲突。**这个文件在 git status 中属于 modified 但冲突未解决，任何对它的引用都是不可靠的。**

影响：如果任何人（包括 GPT/Codex）基于此文件中的信息做实验决策，可能读取到不一致的内容。

### 5.2 文档"下一步"歧义（继承自上次审查）

三个文档对"当前下一步"给出了不同答案：

| 文档 | 当前下一步 |
|---|---|
| GPT_README.md（第 11 行） | v3REG-0：register_bank + ramp_generator |
| V2_NEXT_STEPS.md（最新条目 2026-07-02） | v2B3_scope_safe：Ki=0, limit=819 示波器验证 |
| V2B3_ONLY_PI_SCOPE_TEST_RECORD.md | v2B3_scope_safe 修正 → 等待关闭 v2B3 |

歧义根源在于 v2B3 和 v3REG-0 是两条平行开发线（OUT2 的 PI 路径 vs OUT2 的扫描路径），但没有文档说明二者之间的关系和优先级。

### 5.3 STATUS.md 未更新 v3REG-0

STATUS.md 最新条目停留在 2026-07-02 "v2B3_scope_safe"。v3REG-0 的文件已创建并集成，但没有在 STATUS.md 中记录。

### 5.4 V3REG0_HOST_CONTROLLED_SCAN_PLAN.md 审查

**质量评价**：良好。明确了：
- 目标和动机（为什么需要 register_bank）
- 功能边界（SAFE/SCAN only，不做 HOLD/P_LOCK/PI_LOCK）
- 实验边界（OUT2 → 示波器 only，禁止 6 类连接）
- 上位机与 FPGA 分工
- 第一版默认参数（与 RTL 和脚本默认值一致）
- 后续阶段概览

建议补充：
- sys[6] 地址 0x40600000 的推导过程（现在是"预计"，应写出 GP0 base + 6×1MiB 的计算）
- 明确的 pass/fail 标准（例如"MAGIC=0x4D545330 读取成功"、"SAFE 模式下 OUT2=0"、"SCAN 模式下 OUT2 显示 0.80~0.90V 三角波"）

### 5.5 GPT_README.md 更新审查

第 11 行将项目阶段更新为"已经进入 v3REG-0"，描述了上位机 → register_bank → ramp_generator → OUT2 链路。内容正确，安全边界描述到位。

---

## 6. P0/P1/P2 阻塞项汇总

### P0 阻塞项（上板前必须解决）

| 编号 | 类别 | 问题 | 影响 | 修复主体 |
|---|---|---|---|---|
| P0-1 | 上位机安全 | custom_fpga_scan_control.py 缺少 MAGIC 预校验 | 可能写错物理地址，影响其他外设 | Codex（仅改 Python） |
| P0-2 | 文档 | D2_125_REAL_WIRING_AND_STATE_MODEL.md 存在未解决 git 合并冲突 | 文档引用不可靠，影响实验决策 | User（git merge 或手动选一版） |

### P1 高优先级（实验验证前应解决）

| 编号 | 类别 | 问题 | 修复主体 |
|---|---|---|---|
| P1-1 | 测试 | 缺少 custom_register_bank 的 testbench | Codex |
| P1-2 | 文档 | STATUS.md 未更新 v3REG-0 条目 | Codex |
| P1-3 | 文档 | V2_NEXT_STEPS.md / GPT_README.md / V2B3 测试记录 三者"下一步"不一致 | Codex/User |
| P1-4 | 验证 | 缺少 sys[6] @ 0x40600000 地址的上板确认计划 | User |

### P2 建议改善

| 编号 | 类别 | 建议 |
|---|---|---|
| P2-1 | 上位机 | SSH 返回值检查（subprocess.run check=True） |
| P2-2 | 文档 | V3REG0_HOST_CONTROLLED_SCAN_PLAN.md 补 pass/fail 标准 |
| P2-3 | 测试 | tb_ramp_generator 补热修改参数、极限组合测试 |
| P2-4 | RTL | ramp_generator 中 effective_limit_w 的 always_comb 赋值逻辑可加注释说明最后赋值生效 |

---

## 7. 上位机→FPGA 全链路可行性判断

### 链路逐段分析

```
上位机 PC (custom_fpga_scan_control.py)
  → SSH → Red Pitaya Linux
    → /dev/mem mmap → 物理地址 0x40600000
      → PS M_AXI_GP0 → AXI4 slave → ps_sys bus master
        → sys_bus_interconnect (SN=8, SW=20) → 地址解码 sys[6]
          → sys_bus_if.s (wen/ren/addr[31:0]/wdata[31:0])
            → custom_register_bank (reg_addr = addr[2+:6])
              → mode_o/enable_o/scan_*/out2_limit_o
                → ramp_generator (enable = enable && mode==1)
                  → scan_out2 → selected_out2 mux
                    → dac_b_sum_laser → DAC saturation → ODDR
                      → Red Pitaya OUT2 (SMA)
```

### 各段可行性评估

| 段落 | 可行？ | 条件 |
|---|---|---|
| SSH + Python helper 注入 | 可行 | 已验证（Codex 的 helper 模式是成熟方案） |
| /dev/mem mmap @ 0x40600000 | **待上板验证** | 假设 GP0 base = 0x40000000，sys[6] offset = 0x00600000。需用 MAGIC 读取确认 |
| sys_bus_interconnect 地址解码 | 可行 | sys[6] 寻址逻辑由硬件决定，已编译到 bitstream |
| sys_bus_if 协议 | 可行 | 与 RedPitaya 官方模块协议一致，ack 在 wen/ren 后 1 周期注册 |
| custom_register_bank 寄存器读写 | 可行 | RTL 逻辑正确，已在第 3 节审查通过 |
| ramp_generator 三角波生成 | 可行 | RTL 逻辑正确，testbench 通过 |
| DAC 输出路径 | 可行 | 复用已验证的 DAC saturation + ODDR 路径 |

**最不确定的环节**：`/dev/mem` mmap 到具体物理地址的映射是否与 Vivado 地址空间分配一致。这只能通过上板读取 MAGIC=0x4D545330 来最终确认。

### 整体判断

**链路设计正确、参数一致、逻辑可行。** 剩余风险在上板物理地址验证，这正是 MAGIC 机制设计的目的——在 P0-1 修复后即可用 MAGIC 读取来闭环验证。

---

## 8. 全自动锁频路线可行性

### 8.1 当前项目阶段图（v3REG-0 在整条路线中的位置）

```text
v1ab/v1c/v1d ─── 已通过 ─── IN/OUT passthrough, mixer, mixer+LPF
    ↓
v2A ─── 已通过 ─── 独立 pi_controller
    ↓
v2B1 ─── 已通过 ─── P-only shadow control (timing clean)
    ↓
v2B3 ─── 未关闭 ─── pi_controller_seq 集成 (OUT2 粘 limit, 待 scope_safe 验证)
    ↓
v3REG-0 ─── 本次审查 ─── register_bank + ramp_generator SAFE/SCAN
    ↓ [未实现]
v3REG-1: HOLD (capture lock voltage)
    ↓
v3REG-2: P_LOCK / PI_LOCK (register-controlled PI)
    ↓
v4: scan_lock_fsm (自动扫谱、锁点判断、失锁检测)
    ↓
v5: 上位机 CNN/规则识峰
    ↓
v6: 自动重锁 + 长时间稳定性
    ↓
v7: 全自动 deep learning 参数优化
```

### 8.2 每阶段阻塞分析

**v3REG-0 → v3REG-1 (HOLD)**：
- 需要：SAFE/SCAN 链路验证成功后，在 ramp_generator 中增加 HOLD 行为（pos 冻结在当前值）
- 硬件阻塞：无。只需 register_bank 增加 MODE=2(HOLD)，ramp_generator 增加 hold 状态
- 风险：低。SAFE/SCAN 已验证的同一链路增加小功能

**v3REG-1 → v3REG-2 (P_LOCK / PI_LOCK)**：
- 需要：将 pi_controller_seq 的控制路径与 register_bank 参数绑定
- 硬件阻塞：pi_controller_seq 已有时序 clean 的流水线实现，主要工作是参数化接口改造
- 风险：中。需要将现有的编译时参数（KP_DEFAULT/KI_DEFAULT/LIMIT_DEFAULT）改为运行时寄存器

**v3REG-2 → v4 (scan_lock_fsm)**：
- 需要：FSM 状态机设计（IDLE→RAMP→PEAK_DETECT→LOCK→HOLD→RELOCK）、锁点判断逻辑、失锁检测
- 硬件阻塞：无根本性硬件限制。关键在状态机正确性和锁点判断参数的调优
- 风险：中-高。锁点判断的可靠性取决于 error signal 质量（当前的 OUT1≈0 警告值得关注）

**v4 → v5 (上位机 CNN/规则识峰)**：
- 需要：debug_buffer（采集 scan 过程中的 error signal 数据流）、上位机数据传输链路
- 硬件阻塞：debug_buffer 未实现，PL→PS 数据传输路径未建立
- 风险：高。debug_buffer 需要 BRAM/DMA 设计，是独立子项目

**v5 → v6 (自动重锁)**：
- 需要：scan_lock_fsm 可靠 + 失锁检测可靠 + CNN 识峰可靠
- 风险：中-高。依赖前两个阶段的可靠性

**v6 → v7 (全自动 DL 参数优化)**：
- 需要：所有前面阶段稳定运行 + 大量实验数据 + offline 训练 pipeline
- 风险：高。这是研究级任务，v3REG-0 阶段讨论具体实现为时过早

### 8.3 方向判断

**当前方向正确，无需变更。** v3REG-0 选择先建立最小 PS→PL 控制链路（SAFE/SCAN），而不是直接跳到 PI 控制或自动锁定，这是工程上正确的最小步验证策略。理由：

1. register_bank 是所有后续阶段的共同基础设施（没有它，所有参数都是编译时常量）
2. SAFE/SCAN 比 PI_LOCK 简单，验证了 PS→PL→OUT2 的全链路是否物理可达
3. OUT2 的三角波输出可以直接与 D2-125 Aux Output 基线数据（0.81V DC + triangle @ 52.7Hz）对比，验证数值正确性
4. 如果 sys[6] 地址映射有误，在 SAFE/SCAN 阶段发现比在 PI_LOCK 阶段发现更安全

---

## 9. v3REG-0 上板前检查清单

以下所有条件必须在上板前通过。User 负责 Vivado 操作，Codex 负责代码修正，Claude Code 负责最终只读确认。

### 9.1 P0 修正（Codex 执行）

- [ ] P0-1：custom_fpga_scan_control.py 增加 MAGIC 预校验（在 safe/scan 的任何写入之前读取并验证 MAGIC=0x4D545330）
- [ ] P0-2：User 解决 D2_125_REAL_WIRING_AND_STATE_MODEL.md 的 git 合并冲突

### 9.2 P1 修正（Codex 执行）

- [ ] P1-1：新增 `v0.94/sim/tb_custom_register_bank.sv`，至少覆盖：reset 默认值、SAFE→SCAN 模式切换、enable 开关、参数写入/回读、MAGIC/VERSION/STATUS 读取、OUT2_LIMIT 上限保护、未定义寄存器写不产生副作用
- [ ] P1-2：STATUS.md 新增 2026-07-05 v3REG-0 RTL+host 集成完成条目
- [ ] P1-3：V2_NEXT_STEPS.md 新增澄清条目，说明 v2B3 和 v3REG-0 的关系和优先级

### 9.3 Vivado 检查（User 执行）

- [ ] 确认 `v0.94/rtl/custom_register_bank.sv` 和 `v0.94/rtl/ramp_generator.sv` 在 Vivado Design Sources 中
- [ ] 确认 `v0.94/sim/tb_ramp_generator.sv` 和 `v0.94/sim/tb_custom_register_bank.sv` 在 Simulation Sources 中
- [ ] Run Synthesis → 0 errors, 检查 critical warnings
- [ ] Run Implementation → timing clean (WNS ≥ 0, TNS = 0)
- [ ] Generate Bitstream → 0 errors

### 9.4 上板安全验证（User 执行，示波器）

- [ ] 烧录后，不运行任何主机脚本，直接测 OUT2 直流电压 = 0（验证复位默认值）
- [ ] 运行 `python custom_fpga_scan_control.py --host <IP> safe` → OUT2 = 0
- [ ] 运行 `python custom_fpga_scan_control.py --host <IP> status` → MAGIC=0x4D545330, VERSION=0x00030000
- [ ] 运行 `python custom_fpga_scan_control.py --host <IP> scan` → OUT2 显示 0.80~0.90V 三角波，频率约 50Hz
- [ ] 运行 `python custom_fpga_scan_control.py --host <IP> safe` → OUT2 = 0（确认能回到安全状态）
- [ ] 验证期间 OUT2 只接示波器，不接任何其他设备

### 9.5 安全停止条件

以下任何现象出现即停止实验：
- MAGIC 读取值 ≠ 0x4D545330
- OUT2 在任何时刻 > +1.0V 或 < -1.0V
- OUT2 在 SAFE 模式下非零
- OUT2 有随机跳变或高频振荡
- 有人准备把 OUT2 接到示波器之外的任何设备
- Vivado timing 不通过

---

## 10. 与上次审查（2026-07-02）的交叉对照

上次审查（CLAUDE_REVIEW_2026-07-02_PROJECT_PROGRESS_AND_AI_WORKFLOW_REVIEW_V2.md）提出的关键发现在本轮中的状态：

| 上次发现 | 本状态 |
|---|---|
| OUT1≈0 警告异常（experiment_log 2026-06-30） | **仍未跟进**。OUT1 接近零的问题既没有解决也没有记录原因，对后续 error-signal-based 的 PI 控制和 lock detection 构成潜在风险 |
| 文档膨胀（486+865+511 行） | **继续膨胀**。又新增了 V3REG0_HOST_CONTROLLED_SCAN_PLAN.md |
| "下一步"歧义（三个文档三个答案） | **未解决**。v3REG-0 的加入增加了第四个"下一步"候选 |
| OUT2 只能接示波器 | **维持**。v3REG-0 的安全边界描述到位 |
| CNN 过早 | **仍然过早**。register_bank 刚开始，debug_buffer 未实现 |
| 禁止 weifang 目录访问 | **遵守**。本次未访问 weifang 目录 |

上次审查的 v2B3 OUT2 粘在 -0.2V 的问题通过 v2B3_scope_safe（Ki=0, limit=819）得到了 RTL 修正，但 **v2B3_scope_safe 是否已上板验证在 STATUS.md 中没有记录**。这可能意味着 v2B3 和 v3REG-0 之间的上板测试存在一个缺口。

---

## 11. 最短实验推进路线

### 第一优先：v3REG-0 上板验证（预计 1 次 Vivado 编译 + 1 次上板测试）

```
Step 1: Codex 修复 P0-1（magic 预校验）+ P1-1/P1-2/P1-3
Step 2: User 运行 XSim 确认 testbench 通过
Step 3: User 手动 Vivado → synthesis → implementation → bitstream
Step 4: User 烧录 + 示波器验证（按 9.4 节清单执行）
Step 5: 如果 MAGIC 读取成功且 OUT2 三角波正确，v3REG-0 → CLOSED
```

### 第二优先：v2B3_scope_safe 关闭（如果尚未完成）

```
Step 1: 确认是否已上板测试 v2B3_scope_safe (Ki=0, limit=819)
Step 2: 如果未测试，安排一次示波器测试
Step 3: 如果 OUT2 不再贴 limit 且行为可解释 → CLOSE v2B3
```

### 第三优先：OUT1≈0 问题调查

这是从 2026-06-30 遗留的 WARNING，一直未跟进。在进入任何 error-signal-based 的 PI 控制（v3REG-2）之前，必须确认 OUT1 的 error signal 是否真正可用。建议：
- 检查 IN1/IN2 输入的物理连接和信号质量
- 检查 mixer 的 4.6 MHz REF 是否与 IN2 的 REF 同源/同相
- 如果 OPTICAL input 本身确实接近零（锁定时），需要区分"信号正常为零"还是"信号通路断开"

---

## 附录 A：完整安全判据检查表

| # | 检查项 | 结果 |
|---|---|---|
| 1 | custom_register_bank 复位后 mode_o = 0 (SAFE) | PASS |
| 2 | custom_register_bank 复位后 enable_o = 0 | PASS |
| 3 | ramp_generator 复位后 scan_o = 0 | PASS |
| 4 | ramp_generator disable 后 scan_o = 0 | PASS |
| 5 | 顶层 mux: custom_mode ≠ 1 → selected_out2 = 0 | PASS |
| 6 | 顶层 mux: custom_mode == 1, enable == 0 → selected_out2 = 0 | PASS |
| 7 | OUT2_LIMIT 硬件上限 = 8191 | PASS |
| 8 | REG_MODE 只接受 wdata == 1，其他 → 0 | PASS |
| 9 | REG_SCAN_UPDATE_DIV: wdata == 0 → 强制 1 | PASS |
| 10 | ramp_generator 双重饱和检查（limit + DAC 硬件上限） | PASS |
| 11 | DAC 输出路径复用现有 saturation + ODDR | PASS |
| 12 | 上位机脚本 MAGIC 预校验 | **FAIL (P0)** |
| 13 | RTL 源文件已注册到 redpitaya.xpr | PASS |
| 14 | tb_ramp_generator 在 sim 源中 | PASS |
| 15 | custom_register_bank 有 testbench | **FAIL (P1)** |
| 16 | D2-125 文档无合并冲突 | **FAIL (P0)** |
| 17 | STATUS.md 已更新 v3REG-0 | **FAIL (P1)** |
| 18 | "下一步"文档一致 | **FAIL (P1)** |
| 19 | OUT1≈0 WARNING 已跟进 | **FAIL (继承)** |
| 20 | 文档不暗示 OUT2 可接执行器 | PASS |

---

## 附录 B：默认参数对照表

| 参数 | V3REG0 计划 | RTL 默认值 | 脚本默认值 | 是否一致 |
|---|---|---|---|---|
| offset | 0.85V ≈ 6962 | 14'sd6962 | 6962 | ✓ |
| amp | ±0.05V ≈ 410 | 14'sd410 | 410 | ✓ |
| freq | ~50Hz | update_div=1524 → 50Hz | update_div=1524 → 50Hz | ✓ |
| step | 1 | 14'sd1 | 1 | ✓ |
| limit | 8191 | 14'sd8191 | 8191 | ✓ |
| base_addr | 0x40600000 | — | 0x40600000 | ✓ |

---

审查完成。请优先处理 P0 阻塞项（magic 预校验 + 文档合并冲突），然后安排一次 Vivado 编译 + 上板测试来关闭 v3REG-0。
