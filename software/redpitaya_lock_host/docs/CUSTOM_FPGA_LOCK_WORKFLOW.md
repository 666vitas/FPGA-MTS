# Custom FPGA 锁定工作流

Custom FPGA Observe Mode 面向当前真实接线：

```text
IN1 <- PD/MTS after analog BPF + amplifier, must be < +/-1 V
IN2 <- 4.6 MHz REF, must be < +/-1 V
OUT1 -> FPGA laser_error -> oscilloscope
OUT2 -> FPGA selected_out2 -> oscilloscope
```

当前阶段 OUT2 只允许接示波器。不要把 OUT2 接到 laser scan/PZT、D2-125、Scan input 或任何真实执行器。

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

v3REG-0 `SAFE/SCAN` 已有用户上板验证证据。`HOLD/P_LOCK/PI_LOCK` 还没有完成 timing、bitstream 和上板验证，所以仍然只是 scope-only 候选。

当前阶段不要把 OUT2 接到 PZT、Scan input、laser current modulation、D2-125 Servo Output 或 D2-125 Aux Output。
