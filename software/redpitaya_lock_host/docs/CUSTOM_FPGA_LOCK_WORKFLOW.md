# Custom FPGA 锁定工作流

> **SUPPORTING / NOT A RULE ENTRY**：本文件只描述现有接口。当前 Gate L0 仅比较 `HOLD SELECTED COUNT` 与 `LOCK HERE, Kp=0`；不得据此自动进入 Apply Kp。当前约束以 `version/STATUS.md` 顶部和主工程规则为准。

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

## 当前 FPGA 接口

`custom_fpga_backend.py` 已实现 SSH + `/dev/mem` 寄存器路径，可用于 `SAFE`、`SCAN`、`HOLD`、`P_LOCK`、`PI_LOCK` 候选模式。

接口候选闭环路径为：`SCAN -> Capture Waveform -> 点击当前 error 过零点 -> LOCK HERE -> FPGA 捕获 ERROR_SETPOINT / LOCK_BIAS -> Apply Kp -> UNLOCK / SAFE`。当前 Gate L0 尚未批准 Apply Kp，只允许 Kp=0 的 HOLD/LOCK HERE 对比。

`LOCK HERE` 只捕获锁点并以 Kp=0 进入 `MODE=3 P_LOCK`；`Apply Kp` 只修改 Kp、polarity 和 limit，不重新捕获 `LOCK_BIAS` 或 `ERROR_SETPOINT`。禁止接 laser current modulation、D2-125 Servo Output 或 D2-125 Aux Output。
