# 项目上下文说明

## v2-0 状态同步补充（2026-06-15）

本文件早期内容写于 v1ab / v1 前期阶段，部分“当前不做 PID / 官方工程只读 / 不接 top”的说法已经落后于真实工程。以 `E:\new\fpga_lock\v94\v0.94` 当前实际代码为准，真实状态如下：

```text
当前不是“PID 未实现”。
当前 v2B1 已经集成 mixer_core + lpf_core + output_protect + pi_controller。
pi_controller.sv 是 PI 控制器，不是完整 PID；它没有 D 项。
当前 PID_KI_DEFAULT = 0，所以实际运行模式是 P-only Shadow PI。
OUT1 当前用于 error_o 示波器观察。
OUT2 当前用于 control_o 示波器观察。
OUT2 只是示波器观察级，不接激光器，不接 D2-125 Servo Output，不接 Scan。
当前还没有真正接入激光器闭环。
当前还没有 ramp/sweep 模块。
当前还没有 scan/lock/relock FSM。
当前还没有在线寄存器调参接口，Kp/Ki/limit 等仍是编译时参数。
```

当前有效 v2B1 数据链路是：

```text
IN1(PD/MTS) + IN2(REF)
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

因此，下面旧章节中的“PID 当前不做”“当前只做学习、文档和规划”“不直接接入官方 top”等内容，只能按历史阶段理解，不能作为 2026-06-15 之后的当前状态。

## 0. 本文件作用

本文件记录当前项目的背景、目标和边界。

它是后续 Codex 工作前必须阅读的基础文件之一。

## 1. 阅读对象 / 管理对象

阅读对象：

- 用户本人；
- GPT；
- Codex；
- 后续参与本项目的协作工具。

管理对象：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

官方 Red Pitaya 工程根目录：

```text
E:\new\fpga_lock\v94\v0.94
```

## 2. 实验定义

本项目服务于 MTS 激光稳频实验。

当前真实模拟链路大致为：

```text
signal generator branch 1 -> EOM
signal generator branch 2 -> mixer reference

PD signal
  -> band-pass filter
  -> amplifier
  -> mixer
  -> low-pass/output
  -> MTS error signal
  -> D2-125 Servo
  -> laser feedback input
```

本项目希望逐步用 Red Pitaya FPGA/PL 替代其中一部分模拟信号处理链路。

## 3. 当前目标

当前目标不是完整闭环锁定，而是先完成开环 error signal 生成链路：

```text
PD signal
REF signal
  -> FPGA
  -> error signal
```

未来候选板级连接为：

```text
PD signal  -> Red Pitaya IN1
REF signal -> Red Pitaya IN2
error      -> Red Pitaya OUT1
```

当前阶段只做学习、文档和规划，不直接接入官方 top。

## 4. 当前不做的内容

| 内容 | 当前状态 |
|---|---|
| sweep / scan | 当前不做 |
| PID / PI | v2B1 已经集成 P-only Shadow PI，Ki=0，OUT2 可观察 `control_o`，但尚未真实闭环 |
| AI | 当前不做 |
| scan / lock / relock FSM | 当前不做 |
| 直接控制激光器 | 当前不做 |
| 修改官方 `red_pitaya_top.sv` | v2B1 已在真实工程中接入 `laser_lock_core` 输出路由；本轮 v2-0 不再修改 RTL |
| 修改官方 Vivado 工程 | 当前不做 |

## 5. 当前原则

| 原则 | 说明 |
|---|---|
| 官方工程只读 | 当前只允许阅读官方工程，不允许修改 |
| 自定义内容独立保存 | 所有自定义资料放在 `redpitaya_laser_lock_project` |
| 先学习再写代码 | 先理解 `red_pitaya_top.sv`，再设计接口 |
| 先仿真再集成 | 自定义 core 先独立仿真，不直接接官方 top |
| 先生成方案再修改 | 官方 top 集成必须先写 integration plan |
| 文档默认中文 | 方便 FPGA/Verilog 新手阅读 |

## 6. 官方工程边界

以下官方目录当前只读：

```text
E:\new\fpga_lock\v94\v0.94\rtl
E:\new\fpga_lock\v94\v0.94\project
E:\new\fpga_lock\v94\v0.94\sim
E:\new\fpga_lock\v94\v0.94\ip
E:\new\fpga_lock\v94\v0.94\sdc
```

当前不允许直接修改：

```text
red_pitaya_top.sv
red_pitaya_ps.sv
PS/AXI/DDR/PLL/ODDR/XDC
```

## 7. 自定义项目边界

所有自定义内容必须放在：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

建议子目录：

```text
redpitaya_laser_lock_project\docs
redpitaya_laser_lock_project\rtl
redpitaya_laser_lock_project\sim
redpitaya_laser_lock_project\experiment_logs
```

## 8. 用户开发方式

用户是 FPGA/Verilog 新手，主要依靠 GPT + Codex 协作开发。

因此每一步都需要：

- 写清楚为什么做；
- 写清楚读了哪些文件；
- 写清楚改了哪些文件；
- 写清楚没有改哪些文件；
- 写清楚下一步怎么验证；
- 写清楚如何回退。

## 9. 已确认

- 实验背景是 MTS 激光稳频。
- 当前真实工程已经从 `PD/REF -> FPGA -> error signal` 推进到 v2B1：`error_o -> pi_controller -> control_o` 的 P-only Shadow PI 示波器观察。
- 当前不做 sweep。
- 当前不创建新的 PID 模块；实际使用 `pi_controller.sv`，不创建 `pid_lock_core.sv`。
- 当前不做 AI。
- 本轮 v2-0 文档同步不修改 RTL/testbench/Vivado；历史“官方工程只读”不再代表真实代码从未集成。
- 自定义内容放在 `redpitaya_laser_lock_project`。

## 10. 不确定，需要人工确认

| 问题 | 说明 |
|---|---|
| IN1/IN2 与 `adc_dat[0]`/`adc_dat[1]` 的物理对应 | 后续需要结合官方文档、约束或示波器实验确认 |
| OUT1/OUT2 与 DAC A/B 的物理对应 | 后续需要结合官方文档或上板实验确认 |
| 何时允许修改官方 top | 需要用户明确批准 |

## 11. 下一步建议

不要立即写新的 Verilog，也不要创建 `pid_lock_core.sv`。

下一步只建议进入 v2-1 的最小安全演示准备：

```text
启用很小 Ki
保持 output_limit 很小
由用户手动完成 Vivado 编译
先做电子学回环测试
OUT2 仍然只接示波器，不接激光器
```

## 12. 给 GPT 审查的问题

1. 当前是否应继续保持官方工程只读？
2. v2-1 启用很小 Ki 前，电子学回环的输入幅度、输出限幅和安全停止条件是什么？
3. sweep、scan/lock/relock、AI/CNN 是否继续后置到 v2 后续或 v3/v5？
