# D2-125 真实接线与状态模型

## 1. 当前模拟链路总图

当前项目仍以 D2-125 真实实验链路作为安全基准。Red Pitaya / FPGA 目前只做观察和候选控制输出，不完整替代 D2-125。

当前可理解为：

```text
PD + BPF + Amp
-> Red Pitaya IN1
-> mixer_core + lpf_core + output_protect
-> OUT1 / error_o 观察

REF
-> Red Pitaya IN2

error_o / protected_error
-> pi_controller 或 pi_controller_seq
-> OUT2 / control_o candidate
-> 目前只接示波器
```

D2-125 真实链路仍负责实际 Ramp / Unlock / Lock 工作流，以及真实 Servo Output 和 Aux Servo Output 的实验控制。

## 2. D2-125 的 Ramp / Unlock / Lock 三种状态

### Ramp

Ramp 状态用于扫谱和寻找谱线。D2-125 通过 Aux Servo Output / Scan/PZT 相关输出给激光器扫描端提供慢速扫描量，让激光频率扫过目标谱线。

当前 Red Pitaya 还没有实现可上板使用的 `ramp_generator`，也没有实现完整 `scan_lock_fsm`。

### Unlock

Unlock 状态表示系统尚未处于稳定锁定。此时可以观察 error signal、scan 波形和候选 control 输出，但不能把当前 OUT2 当作真实锁定控制量。

当前 OUT2 是 `control_o / sequential PI candidate`，仍只允许接示波器。

### Lock

Lock 状态表示 D2-125 已经通过自己的模拟控制链路维持锁定。当前 FPGA 还没有独立完成真实激光闭环，因此不能声称 FPGA 已经替代 D2-125 完成 Lock。

## 3. Servo Output 三通两路电流反馈的真实定义

D2-125 Servo Output 是真实控制输出，经过三通后进入两路电流反馈相关链路。它属于真实执行器控制路径，不是 Red Pitaya OUT2 当前可以直接并联或替代的安全节点。

当前禁止：

```text
OUT2 接 D2-125 Servo Output 三通
OUT2 和 D2-125 输出并联
OUT2 接激光器电流反馈执行器
OUT2 接任何未确认输入范围和极性的真实执行器
```

## 4. Aux Servo Output 在 Ramp 和 Lock 状态下的真实作用

在 Ramp 状态下，Aux Servo Output / Scan/PZT 相关输出提供带 DC offset 的慢速扫描量，用于扫过谱线。

在 Lock 状态下，Aux Servo Output 不再是大幅扫描，而更接近锁定点附近的保持量和小幅慢控制扰动。

因此，未来 Red Pitaya 替代 Aux Servo Output 时，不能只输出从 0 V 开始的三角波，而应考虑：

```text
scan_offset + triangle
Capture Vlock
HOLD
P_LOCK
PI_LOCK
```

这些功能当前还没有进入可接 Scan/PZT 的阶段。

## 5. Red Pitaya 未来替代映射

未来替代路线应分阶段推进：

| D2-125 功能 | 未来 FPGA / 上位机替代方向 | 当前状态 |
|---|---|---|
| Error 生成 | `mixer_core -> lpf_core -> output_protect` | 已实现并用于 OUT1 观察 |
| Servo Core | `pi_controller` / `pi_controller_seq` | 仅作为 OUT2 candidate，仍只接示波器 |
| Ramp | `ramp_generator` | 未实现 |
| Scan/Lock 切换 | `scan_lock_fsm` | 未实现 |
| Aux Servo Output | `scan_offset + triangle + HOLD + P_LOCK / PI_LOCK` | 未实现到可接执行器阶段 |
| 参数选择 | 上位机面板 / register_bank | 未完成 |
| 自动识峰和锁定判断 | 上位机算法 / AI/CNN | 未实现 |

## 6. 安全边界

当前允许：

```text
Red Pitaya IN1 <- PD + BPF + Amp，必须在 +/-1 V 内
Red Pitaya IN2 <- REF，必须在 +/-1 V 内
Red Pitaya OUT1 -> 示波器
Red Pitaya OUT2 -> 示波器
```

当前禁止：

```text
OUT2 接激光器
OUT2 接 D2-125 Servo Output 三通
OUT2 接激光器电源 Scan / PZT
OUT2 和 D2-125 输出并联
D2-125 DC Error 接 Red Pitaya IN1
IN1 / IN2 超过 +/-1 V
```

## 7. 当前 OUT2 结论

当前 OUT2 仍只接示波器。

OUT2 可以作为 `control_o / sequential PI candidate` 的观察信号，但不能作为真实执行器控制信号，不能接激光器，不能接 D2-125 Servo Output，不能接 Scan/PZT，不能声称已经实现 FPGA 独立真实激光闭环。
