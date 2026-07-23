# Custom FPGA 锁定工作流

> **SUPPORTING / NOT A RULE ENTRY**：本文件同时区分当前 legacy 接口与 D1 目标接口。当前 Gate 是 `Gate D1-A / Freeze the deterministic lock-acquisition interface`；当前约束以 `version/STATUS.md` 顶部和主工程规则为准。

Custom FPGA Observe Mode 面向当前真实接线：

```text
IN1 <- PD/MTS after analog BPF + amplifier, must be < +/-1 V
IN2 <- 4.6 MHz REF, must be < +/-1 V
OUT1 -> FPGA laser_error -> oscilloscope
OUT2 -> FPGA selected_out2 -> laser dedicated PZT / Scan input
```

当前阶段 OUT2 的目标执行器是激光器专用 PZT / Scan 输入。不要把 OUT2 接到激光器电流调制输入、D2-125 Servo Output、D2-125 Aux Output，也不要与任何其他设备输出端并联。

## 手动读数

需要记录以下示波器读数：

- OUT1 error Vpp/min/max
- OUT2 control Vpp/min/max
- PD / saturated absorption Vpp
- REF amplitude
- 实验备注

GUI 会计算 OUT2/OUT1 Vpp 比值，并标记危险情况：

- OUT2 abs(max/min) >= 0.8 V：危险。
- OUT2 Vpp 过大：危险。
- OUT1 接近 0：警告。
- OUT2 快速爬升或随机跳变：停止实验。

## 当前 legacy FPGA 接口

`custom_fpga_backend.py` 已实现 SSH + `/dev/mem` 寄存器路径，可用于 `SAFE`、`SCAN`、`HOLD`、`P_LOCK`、`PI_LOCK` 候选模式。

当前真实路径为：

```text
capture -> user select -> confirm
-> host/Linux 轮询 OUT2_MONITOR 进入 target window
-> Linux 写 CAPTURE_LOCK_POINT
-> FPGA 捕获命令到达拍的 ERROR_SETPOINT / LOCK_BIAS
-> MODE=3 P_LOCK, Kp=0
```

`CAPTURE_LOCK_POINT` 到达 FPGA 后是同 `clk_i` 域捕获，但触发时刻仍由 Linux 轮询和寄存器写入延迟决定；GUI 保存的 `ramp_direction` 不是 FPGA 条件，也没有独立 ERROR crossing direction。

## D1 目标流程

```text
capture -> user select -> confirm
-> preload target shadow registers -> ARM
-> FPGA 自主等待：
   scan direction matches
   AND scan inside target window
   AND ERROR crosses setpoint in required direction
-> FPGA 原子捕获实际 bias 并进入 P_LOCK_KP0
-> host 只读 state/event/fault
-> 用户后续批准最小非零 Kp
```

Windows/Linux 不得负责精确 scan-to-lock 时刻。详细 target fields、FSM、寄存器建议和验收矩阵见 `FPGA_DETERMINISTIC_LOCK_ACQUISITION.md`。

当前本轮只更新设计文档；现有 `LOCK HERE`、target wait 和 Apply Kp 代码未删除。新软件/RTL仿真通过前不执行硬件实验，也不得把设计写成硬件锁定通过。禁止接 laser current modulation、D2-125 Servo Output 或 D2-125 Aux Output。
