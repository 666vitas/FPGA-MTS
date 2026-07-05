# Claude Code 审查报告：上位机无法调节板子 OUT2 三角波问题

审查日期：2026-07-05
审查人：Claude Code，角色：Red Pitaya FPGA 工程师 / 上位机软件审查工程师 / 稳频激光器系统工程负责人 / 项目路线审查负责人
审查范围：`E:\new\fpga_lock\v94`，只读审查，不修改任何代码
后续修复主体：Codex

---

## 0. 一句话结论

1. **上位机"调不了三角波"的最可能原因**：用户在 Hardware Bring-up 页面的 Output Control 中用 SCPI 命令（`SOUR2:FUNC TRIANGLE`）尝试控制 OUT2，但当前 v3REG-0 custom FPGA bitstream 中 OUT2 的物理输出已由 `selected_out2`（ramp_generator SAFE/SCAN）驱动，官方 ASG 不再控制 OUT2。SCPI OUT2 命令被发送到了已经不驱动物理 OUT2 的 ASG 模块。

2. **用户是在 Official SCPI Mode 下调 OUT2，还是 Custom FPGA Mode？** 根据 GUI 布局分析，最可能的操作路径是：Hardware Bring-up 页 → Output Control → OUT2 设为 triangle/50Hz/0.05V → Apply。这个 Apply 按钮调用 `apply_output()`，发送 SCPI 命令到官方 ASG。GUI 虽然有一个 Custom FPGA SCAN 路径，但藏在 Custom FPGA Observe 页面中，且该页面的 wiring 标签和 mode_explain_label 文案都是**过时的**（仍写 "OUT2 = laser_control" 而非当前实际的 "OUT2 = selected_out2 SAFE/SCAN"）。

3. **SCPI OUT2 命令是否应该能控制 OUT2？** 在 current v3REG-0 bitstream 中，**不应该**。`USE_LASER_LOCK_CORE=1` 使 DAC B 路由到 `selected_out2`，`asg_dat[1]`（官方 ASG OUT2 输出）不再驱动物理 DAC B。SCPI 命令会成功发送和确认，但信号不会到达物理 OUT2 SMA 端口。

4. **Custom FPGA SCAN 路径是否具备硬件基础？** RTL 层面**代码已具备**。custom_register_bank.sv、ramp_generator.sv、顶层路由全部正确。但 **Vivado synthesis 从未运行**——`exp/v2/synth_1/` 和 `exp/v2/impl_1/` 目录为空，没有 bitstream。当前板子上烧录的只能是旧的 v2B3 版本（不含 custom_register_bank/ramp_generator）。RTL testbench 通过（tb_ramp_generator: 249/249 pass, tb_custom_register_bank_basic: pass）但顶层集成从未综合。

5. **最可能的原因排序**：
   - **P0-1**：SCPI/FPGA 路径混淆 —— 用户用 SCPI ASG 命令调一个已经不接物理 OUT2 的模块（概率最高）
   - **P0-2**：当前板子上**没有 v3REG-0 bitstream** —— exp/v2 目录空，Vivado synthesis 从未运行
   - **P0-3**：即使有 bitstream，MAGIC 预校验在远程 helper 中**尚未实现**（被文档记录为"已修复"但实际代码未更新）
   - **P1-1**：GUI 显示文案过期 —— OUT2 标签写 "laser_control" 而非 "selected_out2 SAFE/SCAN"

6. **当前是否可以接激光器？** **否。** OUT2 当前在任何 bitstream 下都只能接示波器。

---

## 1. 审查范围

### 1.1 已读取并审查的文件

**项目文档（全部）：**
- `GPT_README.md` — 项目主线确认：v3REG-0
- `README.md` — 项目概览
- `version/CURRENT_REVIEW_MANIFEST.md` — 审查清单基准
- `version/STATUS.md` — 项目状态（最新 2026-07-02，v3REG-0 未更新）
- `version/v3/V3REG0_HOST_CONTROLLED_SCAN_PLAN.md` — v3REG-0 技术方案
- `version/v3/V3REG0_SCOPE_TEST_CHECKLIST.md` — 上板验证 checklist
- `version/v3/V3REG0_P0_MAGIC_PRECHECK_FIX_2026-07-05.md` — MAGIC 预校验修复记录
- `version/v3/claude审查/CLAUDE_REVIEW_2026-07-05_V3REG0_PROJECT_FEASIBILITY_AND_AUTO_LOCK_ROADMAP_REVIEW.md` — 上次审查
- `docs/HOST_APP_INTEGRATION.md` — 上位机集成文档
- `software/redpitaya_lock_host/docs/FPGA_MODE_BOUNDARY.md` — **发现文案与当前 RTL 脱节**

**FPGA RTL（全部）：**
- `v0.94/rtl/red_pitaya_top.sv` — 顶层，重点审查 line 391-530（sys[6]/custom_register_bank/ramp_generator/DAC mux）
- `v0.94/rtl/custom_register_bank.sv` — 139 行，11 寄存器
- `v0.94/rtl/ramp_generator.sv` — 129 行，三角波生成器
- `v0.94/rtl/laser_lock_core.sv` — 346 行，pi_controller_seq 仍在实例化但不驱动 OUT2
- `v0.94/rtl/pi_controller_seq.sv` — 292 行，15 状态 PI FSM
- `v0.94/rtl/mixer_core.sv` — 63 行
- `v0.94/rtl/lpf_core.sv` — 86 行
- `v0.94/rtl/output_protect.sv` — 49 行

**FPGA 仿真（全部）：**
- `v0.94/sim/tb_ramp_generator.sv` — 101 行
- `v0.94/sim/tb_custom_register_bank_basic.sv` — 171 行
- `v0.94/sim/tb_register_bank_basic.sv` — 145 行
- `v0.94/xvlog.log` — 0 errors
- `v0.94/xelab.log` — 编译通过
- `v0.94/xsim.log` — tb_ramp_generator: 249/249 PASS

**上位机软件（全部关键文件）：**
- `software/redpitaya_lock_host/redpitaya_lock_host/main.py`
- `software/redpitaya_lock_host/redpitaya_lock_host/main_window.py` — **1508 行，核心审查对象**
- `software/redpitaya_lock_host/redpitaya_lock_host/rp_scpi_client.py` — SCPI 客户端
- `software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_backend.py` — Custom FPGA 后端
- `software/redpitaya_lock_host/redpitaya_lock_host/connection_workers.py` — 后台线程
- `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py` — CLI 脚本 + REMOTE_HELPER
- `software/redpitaya_lock_host/redpitaya_lock_host/ssh_client.py` — SSH 客户端
- `software/redpitaya_lock_host/redpitaya_lock_host/safety.py` — 安全检查

### 1.2 尝试读取但未找到的文件

| 文件 | 状态 |
|---|---|
| `v0.94/sim/tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` | **未找到**（可能已被移除或未创建） |
| `v0.94/exp/v2/synth_1/runme.log` | **不存在**（synth 从未运行） |
| `v0.94/exp/v2/impl_1/runme.log` | **不存在**（impl 从未运行） |
| `v0.94/exp/v2/impl_1/*timing*` | **不存在**（无 timing 报告） |
| `v0.94/exp/v2/impl_1/*utilization*` | **不存在**（无 utilization 报告） |
| `v0.94/exp/v2/impl_1/*bit*` | **不存在**（无 bitstream 生成） |
| `v0.94/redpitaya.xpr` | **不存在**（只有一个 xpr，在 project/ 下） |
| `software/redpitaya_lock_host/config.yaml` | **未找到**（使用 DEFAULT_CONFIG） |
| `software/redpitaya_lock_host/redpitaya_lock_host/rp_client.py` | **未找到**（已重构为 rp_scpi_client.py） |
| `software/redpitaya_lock_host/redpitaya_lock_host/scpi_client.py` | **未找到**（可能已合并/重构） |
| `software/redpitaya_lock_host/redpitaya_lock_host/mock_client.py` | **未找到** |
| `software/redpitaya_lock_host/redpitaya_lock_host/data_logger.py` | **未找到** |
| 所有 `.xdc` / `.sdc` / `.tcl` 约束文件 | **未找到**（使用 Vivado BD 生成） |

---

## 2. 当前项目真实开发阶段

通过 RTL 代码和文档交叉验证，当前项目实际状态如下：

1. **已从 v2B3 sequential PI 转向 v3REG-0 register-controlled OUT2 SAFE/SCAN。** 证据：`red_pitaya_top.sv` 中 DAC B 已改为 `selected_out2`（来自 custom_register_bank/ramp_generator），`laser_control` 不再驱动物理 OUT2。GPT_README.md 和 README.md 都确认了 v3REG-0 主线。

2. **OUT1 = `laser_error` = mixer + LPF error observation。** 不变。

3. **OUT2 = `selected_out2`。** 具体行为：
   - `custom_mode != 1`（复位/SAFE 或任何非 SCAN 值）→ selected_out2 = 0
   - `custom_mode == 1 && custom_enable == 1` → selected_out2 = scan_out2（ramp_generator 三角波）
   - `custom_mode == 1 && custom_enable == 0` → selected_out2 = 0

4. **laser_control / pi_controller_seq 不再直接驱动 OUT2。** `laser_control` 仍然在 `laser_lock_core` 中运行，但其输出未连接到物理 DAC B。

5. **OUT2 由 selected_out2 驱动，selected_out2 由 custom_mode/custom_enable 决定。** 已确认。

6. **custom_mode=1 且 enable=1 时输出 scan_out2（triangle）。** 已确认。

7. **custom_mode 默认值为 0（复位后），mode_explain_label 将输出 0。** 已确认。

8. **当前仍只能示波器观察。** OUT2 不接任何执行器。

9. **当前不能锁激光。** 项目尚未进入闭环阶段。

---

## 3. Official SCPI Mode 路径审查

### 3.1 GUI 架构分析

GUI 有两个控制 OUT2 的路径：

**路径 A（Hardware Bring-up → Output Control → OUT2 Apply）：**
- 调用链路：`main_window.py` out2.apply_button → `apply_output(2, self.out2)` (line 692) → `validate_output_settings()` → `client.apply_output(channel=2, waveform="triangle", freq=50.0, amp=0.05, offset=0.0, enable=True)` (line 975)
- 实际 SCPI 命令序列（rp_scpi_client.py line 79-86）：
  ```
  SOUR2:FUNC TRIANGLE
  SOUR2:FREQ:FIX 50
  SOUR2:VOLT 0.05
  SOUR2:VOLT:OFFS 0
  OUTPUT2:STATE ON
  SOUR2:TRig:INT
  ```
- 这些命令控制**官方 ASG 模块**，通过 `asg_dat[1]` 输出。

**路径 B（Custom FPGA Observe → Custom FPGA Control → SCAN）：**
- 调用链路：`main_window.py` custom_scan_button → `_start_custom_fpga_operation("scan")` (line 687) → `CustomFpgaRegisterWorker` → `CustomFpgaBackend.set_mode_scan()` → SSH + /dev/mem → custom_register_bank → ramp_generator → selected_out2 → DAC B
- 不走 SCPI。

### 3.2 SCPI 路径在 custom bitstream 下的实际效果

**关键证据**：`red_pitaya_top.sv` line 529-530：
```systemverilog
assign dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser : dac_a_sum_official;
assign dac_b_sum = USE_LASER_LOCK_CORE ? dac_b_sum_laser : dac_b_sum_official;
```

当 `USE_LASER_LOCK_CORE = 1` 时：
- DAC A 来自 `dac_a_sum_laser` = laser_error
- DAC B 来自 `dac_b_sum_laser` = selected_out2
- `dac_a_sum_official` (= asg_dat[0] + pid_dat[0]) 被忽略
- `dac_b_sum_official` (= asg_dat[1] + pid_dat[1]) 被忽略

**因此 SCPI `SOUR2:FUNC TRIANGLE` 命令虽然会成功执行（ASG 模块本身工作正常），但 ASG 的输出信号永远不会到达物理 DAC B / OUT2 SMA 端口。**

### 3.3 GUI 提示分析

`apply_output()` 方法 (line 947-952)：
```python
def apply_output(self, channel: int, control: OutputControl) -> None:
    if not self._official_mode() and not isinstance(self.client, MockRedPitayaClient):
        self.statusBar().showMessage(
            "Custom FPGA Mode: OUT1/OUT2 are laser_error/laser_control, not SCPI ASG"
        )
        return
```

这里有一个**重要设计细节**：此检查只在 `_official_mode()` 返回 False **且** 不是 Mock 模式时阻止 Apply。**如果用户在 Official SCPI Mode 下点击 Apply，这个检查不生效。**

但还有一个更深层的问题：**如果用户当前加载的是 custom bitstream（USE_LASER_LOCK_CORE=1），即使连接上 SCPI，SCPI OUT2 命令仍然无效**，因为物理 OUT2 不由 ASG 驱动。GUI 的 `mode_explain_label` 文案（line 1392-1405）在 Official SCPI Mode 下只说 "control official ASG OUT1/OUT2"，在 Custom FPGA Mode 下只说 "OUT1=laser_error and OUT2=laser_control. SCPI ASG output control is disabled." **但两个模式的标签都没有提到 v3REG-0 当前的真实 OUT2 路由**（selected_out2 / SAFE/SCAN / ramp_generator）。

### 3.4 结论：SCPI 路径

- SCPI 路径本身**没有 bug**。命令发送正确，格式正确，ASG 模块响应正确。
- SCPI 路径**不适用于当前 custom FPGA OUT2**，因为 DAC B 不再由 asg_dat[1] 驱动。
- **无法判断用户是否在用 SCPI 路径**（缺少 GUI 操作日志），但根据 GUI 设计分析，这是**最可能的操作路径**。
- GUI 在 Official SCPI Mode 下没有警告用户"如果你加载的是 custom bitstream，SCPI OUT2 命令不会控制物理 OUT2"。

---

## 4. Custom FPGA Mode 路径审查

### 4.1 路径分析

**GUI Custom FPGA SCAN 按钮调用链：**
```
custom_scan_button.clicked (line 687)
  → _start_custom_fpga_operation("scan") (line 805)
    → 读取 custom_offset_v/amp_v/freq_hz/step_counts/limit_counts/widgets
    → CustomFpgaRegisterWorker(operation="scan", ..., params) (line 830)
      → CustomFpgaBackend.set_mode_scan() (line 179)
        → build_scan_config(offset_v, amp_v, freq_hz, step_counts, limit_counts)
        → _run("scan", config)
          → _remote_python_command(base_addr, "scan", config)
            → REMOTE_HELPER (base64 → SSH → python3 -c)
              → RegisterWindow(base_addr) → mmap /dev/mem
                → safe 先写 ENABLE=0 → 写参数 → 写 MODE=1 → 写 ENABLE=1
                → print json status
```

### 4.2 MAGIC 预校验状态

**P0 发现：MAGIC 预校验在远程 helper 中尚未实现。**

`custom_fpga_scan_control.py` 的 `REMOTE_HELPER`（line 39-155）中：
- `safe` 操作直接写 ENABLE=0, MODE=0，无 MAGIC 预校验
- `scan` 操作直接写参数，无 MAGIC 预校验
- `status` 操作只读不写

`V3REG0_P0_MAGIC_PRECHECK_FIX_2026-07-05.md` 文档声称修复已完成（描述了 `require_magic(regs)` 函数和执行顺序），但**实际代码文件中不存在 `read_magic` 或 `require_magic` 函数**。

`custom_fpga_backend.py` 中有 `status_payload_has_expected_magic()` 和 `missing_magic_guidance()` 函数，但它们只在 `_render_custom_fpga_payload()` 中用于**显示** MAGIC 不匹配的诊断信息——**不阻止写入**。`set_mode_safe()` 和 `set_mode_scan()` 直接调用 `_run()` 执行写入，不做任何检查。

`main_window.py` 的 `_on_custom_fpga_failed()` 方法（line 857-871）能处理 MAGIC=0x00000000 的错误信息，但这只在操作**失败后**显示指引。

### 4.3 Custom FPGA 路径的 GUI 设计问题

1. **Custom FPGA Control 组在 "Custom FPGA Observe" 页面中**（line 326），用户必须手动切到这个 tab 才能看到。Hardware Bring-up 是默认的第一个 tab，也是最显眼的。

2. **Custom FPGA Observe 页面的 wiring 标签文案过期**（line 333-339）：
   ```python
   "OUT1 = FPGA laser_error -> oscilloscope\n"
   "OUT2 = FPGA laser_control -> oscilloscope only\n"
   ```
   实际当前 OUT2 = selected_out2（SAFE/SCAN），不是 laser_control。

3. **mode_explain_label 文案过期**（line 1402-1405）：Custom FPGA Mode 下显示 "OUT2=laser_control. SCPI ASG output control is disabled." 这个描述对于 v3REG-0 的 current RTL 是**错误的**。

4. **Custom FPGA Mode 下，OUT1/OUT2 Apply 被禁用**（line 1368-1370），是正确的安全设计。但用户如果切到 Official SCPI Mode，Apply 重新可用——而 SCPI OUT2 命令在 custom bitstream 下无效。

5. **Custom FPGA SCAN 前没有强制 MAGIC 检查**。用户可以跳过 Probe/Status，直接点击 SCAN。如果 MAGIC 不匹配，操作会在 remote 端失败（写错误地址），但 GUI 只能在失败后显示错误——没有前置门控。

### 4.4 结论：Custom FPGA 路径

- Custom FPGA 路径**设计合理**，后端逻辑正确。
- Custom FPGA 路径有**阻断 bug**：MAGIC 预校验未实现（P0-1），没有前置门控（P1）。
- **无法判断**用户是否使用过 Custom FPGA SCAN 路径（需要用户提供 GUI 操作记录）。
- 即使用户使用了 SCAN 路径，如果板子上烧录的是旧 bitstream（不含 custom_register_bank），SCAN 操作也会在 remote 端失败。

---

## 5. custom_register_bank.sv 审查

代码已在上一轮审查（CLAUDE_REVIEW_2026-07-05_V3REG0）中逐行审查通过。本节省略重复细节，只列出与本次问题直接相关的结论：

| # | 检查项 | 结果 |
|---|---|---|
| 1 | MAGIC = 0x4D545330 | PASS |
| 2 | VERSION = 0x00030000 | PASS |
| 3 | 11 寄存器全部存在并可通过 sys_bus_if 读写 | PASS |
| 4 | 写 MODE=1 进入 SCAN（只接受 wdata==1） | PASS |
| 5 | 写 ENABLE=1 使能 | PASS |
| 6 | 默认 offset/amp/step/update_div/limit 与 V3REG0 计划一致 | PASS |
| 7 | bus.addr[2+:6] 与 Python offset 0x00/0x04/0x08... 匹配 | PASS |
| 8 | Python 寄存器 offset 与 RTL reg_addr 对应 | PASS |
| 9 | sys_bus_if ack/rdata 逻辑合理（与 RedPitaya 官方模块一致） | PASS |
| 10 | OUT2_MONITOR 读 selected_out2（红pitaya_top 连接确认） | PASS |

**当前问题的 RTL 层面结论**：custom_register_bank.sv **没有 bug**。寄存器读写逻辑正确，默认值安全。问题不在 RTL。

---

## 6. red_pitaya_top.sv OUT2 路由审查

| # | 检查项 | 代码位置 | 结果 |
|---|---|---|---|
| 1 | USE_LASER_LOCK_CORE = 1 | line 149 | PASS |
| 2 | DAC A = laser_error | line 517, 529 | PASS |
| 3 | DAC B = selected_out2 | line 518, 530 | PASS |
| 4 | custom_register_bank 已实例化并接 sys[6] | line 471-484 | PASS |
| 5 | ramp_generator 已实例化 | line 486-497 | PASS |
| 6 | ramp_generator enable = custom_enable && custom_mode==1 | line 489 | PASS |
| 7 | scan_out2 → selected_out2 mux | line 499-504 | PASS |
| 8 | selected_out2 → dac_b_sum_laser | line 518 | PASS |
| 9 | dac_b 经过官方 saturation | line 533-534 | PASS |
| 10 | dac_dat_b 经过 signed-to-unsigned + ODDR | line 537-539+ | PASS |
| 11 | 无其他逻辑覆盖 OUT2 | 全文件审查 | PASS |
| 12 | asg_dat[1] 在 USE=1 时不驱动 OUT2 | line 530 | PASS |

**当前问题的 RTL 层面结论**：red_pitaya_top.sv OUT2 路由**正确**。DAC B 确实接 selected_out2，且 SAFE 默认值为 0。RTL 没有路由级 bug。

---

## 7. ramp_generator.sv 审查

已在上一轮审查。本节省略重复。

| # | 检查项 | 结果 |
|---|---|---|
| 1 | enable_i=0 → scan_o = 0 | PASS |
| 2 | reset → scan_o = 0 | PASS |
| 3 | SCAN 模式 = offset + triangle (offset=6962, amp=410) | PASS |
| 4 | 双重饱和保护（limit + DAC 硬件上限） | PASS |
| 5 | 频率计算：410×4×1524/125M = 20ms → 50Hz | PASS |

**额外检查**：tb_ramp_generator xsim 结果
- `v0.94/xsim.log`：**SUMMARY tb_ramp_generator tests=249 pass=249 fail=0**
- 所有 11 个断言点通过

**结论**：ramp_generator.sv 没有 bug，独立仿真完全通过。

---

## 8. Vivado / bitstream 一致性审查

### 8.1 关键发现：没有 v3REG-0 bitstream

```
v0.94/exp/v2/synth_1/ → 空目录（仅有空目录结构，无 runme.log）
v0.94/exp/v2/impl_1/  → 空目录（仅含 .hbs/）
```

| # | 检查项 | 结果 |
|---|---|---|
| 1 | custom_register_bank.sv 已加入 Design Sources | PASS（xpr 确认） |
| 2 | ramp_generator.sv 已加入 Design Sources | PASS（xpr 确认） |
| 3 | tb 文件在 Simulation Sources 中 | PASS（xpr 确认） |
| 4 | red_pitaya_top.sv 是当前 v3REG-0 版本 | PASS（git status 确认已修改） |
| 5 | synthesis 是否通过 | **未知** —— runme.log 不存在 |
| 6 | implementation 是否通过 | **未知** —— runme.log 不存在 |
| 7 | timing 是否通过 | **未知** —— 无 timing 报告 |
| 8 | bitstream 是否生成 | **否** —— 无 .bit 文件 |
| 9 | 当前板子上的 bitstream 是什么版本 | **无法判断** —— 需用户确认 |
| 10 | 旧 timing 报告（2026-06-30 v2B3, WNS=+0.107ns）是否适用于 v3REG-0 | **不适用** —— v3REG-0 新增了两个模块 |

### 8.2 关键推论

**即使上位机 Custom FPGA SCAN 路径完美工作，如果板子上没有 v3REG-0 bitstream（包含 custom_register_bank + ramp_generator），那么：**
- /dev/mem 读取 0x40600000 会读到 0x00000000（未映射区域或 stub）
- MAGIC 不会是 0x4D545330
- custom_register_bank 不存在，寄存器不可读写
- ramp_generator 不存在，OUT2 不会输出三角波

**这就是为什么 V3REG0_SCOPE_TEST_CHECKLIST.md 把 "MAGIC 是否读到" 列为第一判断依据。**

---

## 9. 上位机实际操作流程审查

### 流程 A：测试 Official SCPI OUT2 三角波（仅用于官方 ASG）

**注意：此流程不适用于验证 v3REG-0 custom OUT2。**

1. 确认 Red Pitaya 加载的是**官方 v0.94 overlay**（非 custom bitstream）
2. 启动 GUI → 确保在 Official SCPI Mode
3. Probe → 确认 SSH/SCPI 端口状态
4. 如果有 SCPI port 5000 → Connect SCPI
5. 如果没有 → Start SCPI Server（**这会加载官方 overlay，覆盖 custom bitstream**）
6. Hardware Bring-up → Output Control → OUT2 tab
7. 设置 triangle / 50Hz / 0.05V / 0 offset → enable → Apply
8. 示波器 CH4 接 OUT2 → 应看到 50Hz 三角波
9. **这个结果不能证明 custom_register_bank/ramp_generator 工作**
10. **不能证明 v3REG-0 的 OUT2 SAFE/SCAN 链路通**

### 流程 B：测试 Custom FPGA OUT2 三角波（v3REG-0 正确流程）

**前提：必须已烧录包含 custom_register_bank 和 ramp_generator 的 v3REG-0 timing-clean bitstream。**

1. 手动 Vivado: synthesis → implementation → timing check → Generate Bitstream → Program Device
2. **不启动 redpitaya_scpi**（避免覆盖 custom bitstream）
3. GUI 切到 Custom FPGA Mode → Custom FPGA Observe tab
4. OUT2 接示波器（DC coupling, 1V/div 或 200mV/div）
5. 点 **Probe Registers** → 确认 MAGIC=0x4D545330
6. 如果 MAGIC≠0x4D545330 → 停止，检查 bitstream loading 和 base_addr
7. 点 **Status** → 确认 mode=0, enable=0（复位后默认 SAFE）
8. 点 **SAFE** → 示波器确认 OUT2 ≈ 0V
9. 设置 offset=0V, amp=0.05V, freq=10Hz（建议先用低频率测试）
10. 点 **SCAN** → 示波器确认 OUT2 三角波
11. 调整 offset=0.85V, amp=0.05V, freq=50Hz → 确认 0.80~0.90V 三角波
12. 点 **SAFE** → 确认 OUT2 回到 0V
13. **保存所有 evidence：MAGIC/VERSION/MODE/ENABLE/STATUS/示波器截图**

### 流程 C：CLI 命令验证（与 GUI 等价的命令行路径）

```powershell
cd software\redpitaya_lock_host

# 先读状态（只读，安全）
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local status

# 确认 MAGIC=0x4D545330 后：
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local safe
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local scan --offset-v 0 --amp-v 0.05 --freq-hz 10
python .\scripts\custom_fpga_scan_control.py --host rp-f0cb13.local safe
```

---

## 10. 高概率故障原因排序

### P0-1：用户在 Custom FPGA bitstream 下使用 Official SCPI OUT2，路径不匹配

- **现象**：用户点击 Hardware Bring-up → Output Control → OUT2 Apply（或 CLI SCPI 命令），GUI 显示命令成功，但示波器 OUT2 没有三角波（或显示 pi_controller_seq 的残留信号）
- **证据文件**：`red_pitaya_top.sv` line 530（`dac_b_sum = USE_LASER_LOCK_CORE ? dac_b_sum_laser : dac_b_sum_official`），`rp_scpi_client.py` line 79-86（SCPI 命令控制官方 ASG），`main_window.py` line 947-951（Apply 只在官方模式下可用）
- **如何验证**：询问用户操作模式（Official SCPI Mode 还是 Custom FPGA Mode）、点击的是 OUT2 Apply 还是 Custom FPGA SCAN
- **给 Codex 的修复建议**：见 11 节任务 1/2/4
- **给用户的实验动作**：如果加载的是 custom bitstream，用 Custom FPGA Mode → SCAN（不走 SCPI）；如果需要 SCPI 三角波，先加载官方 overlay

### P0-2：当前板子未烧录包含 custom_register_bank/ramp_generator 的 bitstream

- **现象**：即使 Custom FPGA SCAN 路径正确，/dev/mem 读到的是全 0，MAGIC=0x00000000
- **证据文件**：`v0.94/exp/v2/synth_1/` 空目录，`v0.94/exp/v2/impl_1/` 空目录 —— Vivado synthesis 从未运行
- **如何验证**：检查是否存在 bitstream 文件，检查 bitstream 生成时间戳，运行 status 看 MAGIC
- **给 Codex 的修复建议**：Codex 不能运行 Vivado。任务：生成清晰的一步一步 Vivado 操作指引（见 11 节任务 5）
- **给用户的实验动作**：打开 Vivado → synthesis → implementation → timing check → Generate Bitstream → Program Device

### P0-3：Custom FPGA SCAN 路径的 MAGIC 预校验未实现

- **现象**：如果 base_addr 错误或 bitstream 不匹配，SCAN 操作会默默写错地址
- **证据文件**：`custom_fpga_scan_control.py` REMOTE_HELPER 中 safe/scan 无 magic 预校验；`V3REG0_P0_MAGIC_PRECHECK_FIX_2026-07-05.md` 描述已修复但代码未更新
- **如何验证**：读 custom_fpga_scan_control.py 的 REMOTE_HELPER 内容
- **给 Codex 的修复建议**：见 11 节任务 3
- **给用户的实验动作**：修复前先手动用 status 确认 MAGIC 再执行 SCAN

### P1-1：GUI 文案过期，误导用户

- **现象**：Custom FPGA Mode 下显示 "OUT2 = laser_control"，但实际 OUT2 = selected_out2 SAFE/SCAN。Custom FPGA Observe 页面 wiring 标签也写着 "OUT2 = FPGA laser_control"
- **证据文件**：`main_window.py` line 337（wiring 标签）、line 1405（mode_explain_label）
- **如何验证**：打开 GUI 切到 Custom FPGA Mode 看显示文案
- **给 Codex 的修复建议**：见 11 节任务 1/4
- **给用户的实验动作**：更新 GUI 文案

### P1-2：OUT2 实际为 0，因为 custom_mode 和 enable 未生效

- **现象**：即使 bitstream 正确，如果 custom_mode=0 或 enable=0，selected_out2=0
- **证据文件**：`red_pitaya_top.sv` line 499-504（mux 逻辑）
- **如何验证**：Status 读取 mode 和 enable 值
- **给 Codex 的修复建议**：SCAN 操作后自动读取并显示 mode/enable 状态（已有，但需确认）
- **给用户的实验动作**：点 SCAN 后点 Status 确认 mode=1 和 enable=1

### P2-1：ramp_generator 输出有 DC offset，示波器设置导致误判

- **现象**：默认 offset=0.85V，幅度=±0.05V，如果示波器 AC coupling 可能看不出；如果量程太大（5V/div）也可能看不出
- **证据文件**：ramp_generator 默认 offset=6962(~0.85V)
- **如何验证**：确认示波器 DC coupling, 200mV/div 量程
- **给用户的实验动作**：先用 CLI 命令 `scan --offset-v 0 --amp-v 0.05 --freq-hz 10` 测试无偏置三角波

### P2-2：SCPI server 启动后覆盖了 custom bitstream

- **现象**：SCPI OUT2 命令无效且 custom register 也失效
- **证据文件**：`HOST_APP_INTEGRATION.md` 和 `FPGA_MODE_BOUNDARY.md` 都警告了此风险
- **如何验证**：确认是否点击过 Start SCPI Server
- **给用户的实验动作**：如果曾有 SCPI 操作，先重新 Program Device 加载 custom bitstream

---

## 11. 给 Codex 的修复任务

### Codex 任务 1：更新 GUI 模式标签和 wiring 描述（P1）

**目标**：修正 GUI 中所有与当前 v3REG-0 RTL 不符的 OUT2 描述文案。

**涉及文件**：
- 允许修改：`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`
- 禁止修改：所有 `.sv` 文件、Vivado 工程文件

**需修改的代码位置**：
1. `main_window.py` line 333-339：Custom FPGA Observe 页面的 wiring 标签
   - 当前：`"OUT2 = FPGA laser_control -> oscilloscope only\n"`
   - 改为：`"OUT2 = selected_out2 (SAFE/SCAN from custom_register_bank + ramp_generator) -> oscilloscope only\n"`
2. `main_window.py` line 1402-1405：Custom FPGA Mode 的 mode_explain_label
   - 当前：`"OUT1=laser_error and OUT2=laser_control. SCPI ASG output control is disabled."`
   - 改为：`"OUT1=laser_error (mixer+LPF). OUT2=selected_out2 (register_bank SAFE/SCAN). Use Custom FPGA Observe → SCAN to control OUT2. SCPI ASG output is disabled and does not drive physical OUT2 in the current bitstream."`
3. `main_window.py` line 1271-1272：CH4 的 warning 标签
   - 当前：`"Custom FPGA Mode: OUT2 is laser_control, scope-only"`
   - 改为：`"Custom FPGA Mode: OUT2 is SAFE/SCAN register-controlled triangle, scope-only"`
4. `main_window.py` line 1393-1398：Official SCPI Mode 的 mode_explain_label
   - 增加警告："SCPI OUT2 controls the official ASG. If a custom FPGA bitstream is loaded (USE_LASER_LOCK_CORE=1), OUT2 is driven by custom_register_bank/ramp_generator instead — SCPI OUT2 commands will not produce the expected physical output."

**成功判据**：GUI 在所有模式下显示的 OUT2 描述与实际 RTL 路由一致。

---

### Codex 任务 2：增加 Custom FPGA 诊断面板（P1）

**目标**：Custom FPGA Control 组中显示关键诊断信息，让用户不需要翻 log 也能看到寄存器状态。

**涉及文件**：
- 允许修改：`software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`
- 禁止修改：所有 `.sv` 文件、Vivado 工程文件

**实现要求**：
在 `_render_custom_fpga_payload()` 被调用时（probe/status/safe/scan 完成后），除了更新 `custom_register_summary` 和 `custom_warning_text`，额外增加一个只读文本框显示：
```
MAGIC: 0x4D545330 (match / MISMATCH)
VERSION: 0x00030000
found_base_addr: 0x40600000 (或 probe 结果)
MODE: 0 (SAFE) / 1 (SCAN)
ENABLE: 0 / 1
STATUS: 0xXXXXXXXX (bit0=enable, bit1=saturated)
OUT2_MONITOR: XXXX counts / X.XXXX V
last remote command (first 200 chars)
stderr (if any)
```

**成功判据**：Probe/Status/SAFE/SCAN 任一操作完成后，诊断面板都显示完整的寄存器状态。

---

### Codex 任务 3：实现 MAGIC 预校验（P0，优先）

**目标**：SCAN/SAFE 操作前强制验证 MAGIC=0x4D545330。如果 MAGIC 不匹配，禁止写入任何寄存器。

**涉及文件**：
- 允许修改：
  - `software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py`（REMOTE_HELPER 增加 require_magic 函数）
  - `software/redpitaya_lock_host/redpitaya_lock_host/custom_fpga_backend.py`（增加前置 MAGIC 检查）
- 禁止修改：所有 `.sv` 文件、Vivado 工程文件

**实现要求**：

A. `custom_fpga_scan_control.py` 的 `REMOTE_HELPER` 中增加：
```python
EXPECTED_MAGIC = 0x4D545330

def read_magic(regs):
    return regs.read(REGISTERS["MAGIC"])

def require_magic(regs):
    actual = read_magic(regs)
    if actual != EXPECTED_MAGIC:
        print(json.dumps({
            "error": "MAGIC_MISMATCH",
            "actual_magic": f"0x{actual:08X}",
            "expected_magic": f"0x{EXPECTED_MAGIC:08X}",
            "guidance": "Check bitstream version, base address, and Program Device."
        }))
        sys.exit(1)
```

B. 在 `safe` 操作的 `main()` 中，`regs = RegisterWindow(...)` 之后立即调用 `require_magic(regs)`，然后再写寄存器。

C. 在 `scan` 操作的 `main()` 中，同样在参数写入前调用 `require_magic(regs)`。

D. `custom_fpga_backend.py` 的 `_run()` 方法中增加：如果 response.payload 包含 "MAGIC_MISMATCH" 错误，抛出明确的 `CustomFpgaBackendError`。

**成功判据**：
- `safe` 和 `scan` 在写寄存器之前必须先验证 MAGIC
- MAGIC 不匹配时非零退出且不写任何寄存器
- status 操作不受影响（仍然只读）

---

### Codex 任务 4：增加"两条路径互斥"的 GUI 提示和文档（P1）

**目标**：用户在任何模式下都能清楚知道当前 OUT2 的实际控制路径。

**涉及文件**：
- 允许修改：
  - `software/redpitaya_lock_host/redpitaya_lock_host/main_window.py`
  - `software/redpitaya_lock_host/README.md`（如果存在）
  - `software/redpitaya_lock_host/docs/FPGA_MODE_BOUNDARY.md`
- 禁止修改：所有 `.sv` 文件、Vivado 工程文件

**实现要求**：
1. Hardware Bring-up 页面的 Output Control 组上方增加一行提示文字：
   ```
   "SCPI OUT1/OUT2 control works with official v0.94 overlay/ASG.
    If a custom FPGA bitstream is loaded, OUT1/OUT2 are driven by
    the custom RTL (SAFE/SCAN for OUT2), and SCPI output commands
    will NOT produce the expected physical output."
   ```
2. 当用户 mode_combo 从 Official SCPI Mode 切到 Custom FPGA Mode（或反过来）时，弹出一次性对话框或 status bar message 解释两条路径的区别。
3. `FPGA_MODE_BOUNDARY.md` 更新 line 103：`OUT2 is the FPGA laser_control` → `OUT2 is selected_out2 (custom_register_bank SAFE/SCAN)`

**成功判据**：新用户第一次使用 GUI 时能理解 SCPI OUT2 和 Custom FPGA OUT2 是两条不同的物理路径。

---

### Codex 任务 5：生成 v3REG-0 上板验证 SOP（P0，辅助用户）

**目标**：给用户一个逐步的 Vivado + 上位机操作手册。

**涉及文件**：
- 允许新建：`version/v3/V3REG0_VIVADO_AND_HOST_VERIFICATION_SOP.md`
- 允许修改：`version/v3/V3REG0_SCOPE_TEST_CHECKLIST.md`（补充步骤）
- 禁止修改：所有 `.sv` 文件、Vivado 工程文件

**内容要求**：
1. Vivado 操作步骤（打开 xpr → 确认 sources → synthesis → implementation → 确认 timing → Generate Bitstream → Program Device）
2. 提示：旧 timing 报告（v2B3 WNS=+0.107ns）**不适用于** v3REG-0，需要重新运行
3. 上位机 CLI 验证步骤（status → safe → scan → safe，与 V3REG0_SCOPE_TEST_CHECKLIST.md 一致）
4. GUI 验证步骤（Probe → Status → SAFE → SCAN）
5. 故障排查表（MAGIC=0 → 检查 bitstream/base_addr/Program Device；OUT2 flatline → 检查 mode/enable/coupling/量程）
6. 强调禁止连接执行器

---

### Codex 任务 6：备份任务 —— 如果 synthesis 后发现 RTL bug

**目标**：仅在 Vivado synthesis 报错或 timing 不通过时执行。在此之前不要修改任何 RTL。

**当前审查结论**：独立 testbench 全部通过，RTL 逻辑审查无 bug。如果 synthesis/timing 有问题，最可能是：
- PLL/ADC 时钟域的新模块增加导致 timing 变差
- sys[6] 总线地址解码增加组合逻辑延迟
- ramp_generator 中 `effective_limit_w` 的 always_comb 路径

**允许修改**：`v0.94/rtl/ramp_generator.sv`、`v0.94/rtl/custom_register_bank.sv`（仅在 synthesis 报错时）
**禁止修改**：Vivado 工程、约束文件、其他 RTL

---

## 12. 用户下一步需要提供的信息

如本审查仍无法确定问题根因，需要用户提供以下信息（按优先级排列）：

1. **操作模式**：GUI 当前在 "Official SCPI Mode" 还是 "Custom FPGA Mode"？
2. **点击的按钮**：点击的是 Output Control → OUT2 Apply，还是 Custom FPGA Control → SCAN？
3. **如果是 CLI**：运行的命令是什么？`status` / `safe` / `scan` 的输出是什么？
4. **MAGIC 值**：`python .\scripts\custom_fpga_scan_control.py --host <IP> status` 的输出
5. **Probe Registers 输出**：GUI Custom FPGA Observe → Probe Registers 的显示
6. **MODE / ENABLE / OUT2_MONITOR**：Status 操作后的完整输出
7. **当前 bitstream**：文件名、生成时间、是不是 v3REG-0 版本
8. **Vivado timing summary**：synthesis 和 implementation 是否已运行
9. **示波器截图**：OUT2 的波形（标注 DC/AC coupling, V/div, time/div）
10. **是否启动过 redpitaya_scpi**：点击过 Start SCPI Server 吗？
11. **GUI connection log**：connection_status 文本框的完整内容

---

## 13. 当前禁止事项

- 不要把 OUT2 接激光器 PZT
- 不要把 OUT2 接激光电流控制
- 不要把 OUT2 接 D2-125 Servo Output
- 不要把 OUT2 接 Scan input
- 不要声称已经完成闭环锁定
- 不要声称已经替代 D2-125
- 不要把 Official SCPI OUT2 测试结果当作 custom_register_bank 测试结果
- 不要在 MAGIC 不匹配时点击 SCAN
- 不要在不确认 bitstream 的情况下调试上位机
- 不要启动 redpitaya_scpi 后还假设 custom bitstream 没被覆盖
- 不要在 v3REG-0 Vivado synthesis 未通过时烧录 / 上板

---

## 14. 最终结论

1. **当前问题最可能的原因**：SCPI/Custom FPGA 路径混淆。用户很可能在 Hardware Bring-up 页面用 SCPI OUT2 Apply 尝试控制 OUT2，但当前 custom FPGA bitstream 中 OUT2 由 selected_out2（ramp_generator SAFE/SCAN）驱动，ASG 的 `asg_dat[1]` 不再连接物理 DAC B。SCPI 命令成功发送但永远到不了物理 OUT2。

2. **问题性质**：这是一个**三重叠加问题**——软件 UI 设计让用户容易用错路径（P1）+ MAGIC 预校验未实现导致无安全门控（P0）+ Vivado synthesis 从未运行为 v3REG-0（P0）。RTL 层面没有 bug。

3. **是否应该先修上位机？** 是。但修复不是让 SCPI 路径工作——而是让 GUI 清楚告诉用户当前 OUT2 的实际控制路径，并在 Custom FPGA 模式下正确地引导用户走 SCAN 路径。

4. **是否应该先查 MAGIC / Status？** 是。这是区分"上位机路径问题"和"bitstream 未加载问题"的关键检测点。MAGIC=0x00000000 → bitstream 不存在或地址错；MAGIC=0x4D545330 → 硬件链路通但上位机路径可能有问题。

5. **是否应该先确认 bitstream？** 是。当前 `exp/v2/` 目录为空，Vivado synthesis 从未运行。没有 v3REG-0 bitstream = 一切上位机 SCAN 操作都是写入空地址。

6. **下一步最重要的一件事**：**用户手动运行 Vivado synthesis + implementation + timing check + Generate Bitstream + Program Device**。没有这一步，任何上位机调试都是无意义的。

---

审查完成。此报告仅供只读审查使用。所有修复任务指向 Codex 执行，所有 Vivado 操作指向用户执行。Claude Code 不修改任何文件。
