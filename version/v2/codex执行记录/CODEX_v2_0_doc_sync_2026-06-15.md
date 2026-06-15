# CODEX v2-0 文档同步执行记录

## 1. 阅读的文件

| 类型 | 文件 |
|---|---|
| Claude 审查报告 | `E:\new\fpga_lock\v94\version\v2\claude审查\CLAUDE_REVIEW_v2_v2a_feasibility_2026-06-15.md` |
| 项目入口 | `E:\new\fpga_lock\v94\GPT_README.md` |
| v2 总体文档 | `E:\new\fpga_lock\v94\version\v2\V2_SYSTEM_ARCHITECTURE_AND_STAGE_MAP.md` |
| v2 总体文档 | `E:\new\fpga_lock\v94\version\v2\V2_DEVELOPMENT_ROADMAP.md` |
| v2 总体文档 | `E:\new\fpga_lock\v94\version\v2\V2_NEXT_STEPS.md` |
| 旧上下文文档 | `E:\new\fpga_lock\v94\version\v2\v0.94\redpitaya_laser_lock_project\docs\current\00_CONTEXT_FROM_GPT.md` |
| 旧状态文档 | `E:\new\fpga_lock\v94\version\v2\v0.94\redpitaya_laser_lock_project\docs\project_master\01_CURRENT_STATUS_SUMMARY.md` |
| 旧路线文档 | `E:\new\fpga_lock\v94\version\v2\v0.94\redpitaya_laser_lock_project\docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md` |
| 旧执行清单 | `E:\new\fpga_lock\v94\version\v2\v0.94\redpitaya_laser_lock_project\docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md` |
| RTL 事实来源 | `E:\new\fpga_lock\v94\v0.94\rtl\mixer_core.sv` |
| RTL 事实来源 | `E:\new\fpga_lock\v94\v0.94\rtl\lpf_core.sv` |
| RTL 事实来源 | `E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv` |
| RTL 事实来源 | `E:\new\fpga_lock\v94\v0.94\rtl\pi_controller.sv` |
| RTL 事实来源 | `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv` |
| RTL 事实来源 | `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv` |
| SIM 事实来源 | `E:\new\fpga_lock\v94\v0.94\sim\tb_pi_controller.sv` |
| SIM 事实来源 | `E:\new\fpga_lock\v94\v0.94\sim\tb_mixer_core.sv` |
| SIM 事实来源 | `E:\new\fpga_lock\v94\v0.94\sim\tb_lpf_core.sv` |
| SIM 事实来源 | `E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` |

## 2. Claude 审查报告的核心结论

Claude 审查结论是：**有条件可行**。

必须同步到文档的核心判断：

- 当前 v2B1 已有 PI 集成，不是“PID 未实现”。
- 当前 v2B1 已经集成 `mixer_core + lpf_core + output_protect + pi_controller`。
- 当前是 P-only Shadow PI。
- `PID_KI_DEFAULT = 0`，因此没有积分参与真实运行。
- OUT2 只是示波器观察级 `control_o`，不能当作真实激光控制输出。
- 当前还没有真实激光闭环。
- 当前还没有 `ramp/sweep`。
- 当前还没有 `scan/lock FSM`。
- 文档与代码脱节是 P0 风险，因为会导致 Codex/GPT/Claude 基于旧状态重复造轮子或做错架构判断。

## 3. 修改了哪些文档

| 文件 | 原问题 | 修改内容 |
|---|---|---|
| `version\v2\v0.94\redpitaya_laser_lock_project\docs\current\00_CONTEXT_FROM_GPT.md` | 写着 PID 当前不做、只做规划、不接 top | 增加 v2-0 状态同步块；说明 v2B1 已集成 P-only Shadow PI，Ki=0，OUT1/OUT2 只示波器观察，不创建 `pid_lock_core.sv` |
| `version\v2\v0.94\redpitaya_laser_lock_project\docs\project_master\01_CURRENT_STATUS_SUMMARY.md` | 写着 `control_o=0`、mixer/LPF/PID 未实现 | 增加 v2-0 状态同步块；把当前状态修正为 mixer+LPF+output_protect+pi_controller 已集成，仍未真实闭环 |
| `version\v2\v0.94\redpitaya_laser_lock_project\docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md` | v2 执行清单引用 `pid_lock_core.sv`，像是还要新建 PID | 增加 v2-0 状态同步块；v2 清单改为使用 `pi_controller.sv`，不创建 `pid_lock_core.sv` |
| `version\v2\v0.94\redpitaya_laser_lock_project\docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md` | 把 v2 写成未来新建 PID 模块阶段 | 增加 v2-0 状态同步块；说明 PI core 已提前进入 v2B1，后续 v2 重点是小 Ki、电子学回环、ramp/sweep、scan/lock |

## 4. 当前代码真实状态

| 模块 | 状态 | 文件 |
|---|---|---|
| `mixer_core` | 已实现并在 v2B1 链路中集成，用于 IN1/IN2 数字混频 | `E:\new\fpga_lock\v94\v0.94\rtl\mixer_core.sv` |
| `lpf_core` | 已实现并在 mixer 后集成，用于生成 error-like signal | `E:\new\fpga_lock\v94\v0.94\rtl\lpf_core.sv` |
| `output_protect` | 已实现并集成，用于 reset/输出保护 | `E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv` |
| `pi_controller` | 已实现 PI 控制器，带 P/I、limit、anti-windup、reset/enable/hold；不是完整 PID，无 D 项 | `E:\new\fpga_lock\v94\v0.94\rtl\pi_controller.sv` |
| `laser_lock_core` | v2B1 已集成 mixer+LPF+output_protect+pi_controller；当前 Ki=0，P-only Shadow PI | `E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv` |
| `red_pitaya_top` | 已把 `laser_error` 路由到 OUT1，把 `laser_control` 路由到 OUT2；`USE_LASER_LOCK_CORE=1`，`LASER_LOCK_OUTPUT_MODE=3` | `E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv` |
| `tb_pi_controller` | 已存在，用于 PI core 独立验证 | `E:\new\fpga_lock\v94\v0.94\sim\tb_pi_controller.sv` |
| `tb_mixer_core` | 已存在，用于 mixer 独立验证 | `E:\new\fpga_lock\v94\v0.94\sim\tb_mixer_core.sv` |
| `tb_lpf_core` | 已存在，用于 LPF 独立验证 | `E:\new\fpga_lock\v94\v0.94\sim\tb_lpf_core.sv` |
| `tb_laser_lock_core_v2b1_shadow_pi_dc_error` | 已存在，用于 v2B1 Shadow PI 集成行为验证；文件名含 `dc_error` 是历史命名，不代表当前接线 | `E:\new\fpga_lock\v94\v0.94\sim\tb_laser_lock_core_v2b1_shadow_pi_dc_error.sv` |

当前真实链路：

```text
IN1 + IN2
-> mixer_core
-> lpf_core
-> output_protect
-> error_o
-> OUT1

同时：

error_o/protected_error
-> pi_controller
-> control_o
-> OUT2
```

## 5. 当前不能声称完成的内容

当前不能声称：

- 已经完整替代 D2-125。
- 已经完成自动锁定。
- 已经完成 PID 闭环锁激光。
- AI/CNN 已进入当前实现阶段。
- OUT2 可以接激光器。
- 已经完成 ramp/sweep。
- 已经完成 scan/lock/relock FSM。
- 已经完成在线寄存器调参接口。

## 6. 下一步建议

下一步只能建议进入 **v2-1**：

```text
启用很小 Ki；
保持 output_limit 很小；
由用户手动完成 Vivado 编译；
先做电子学回环测试；
OUT2 仍然只接示波器，不接激光器。
```

v2-1 之前不要创建新的 PID 模块，不要创建 `pid_lock_core.sv`，不要做 CNN/AI，不能开始完整 scan/lock/relock。
