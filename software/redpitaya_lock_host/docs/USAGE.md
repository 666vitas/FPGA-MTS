# 使用说明

## Mock Mode

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
.\run_mock.bat
```

Mock mode 不连接 Red Pitaya，只用于检查 GUI 是否能正常打开。

## 真实连接模式

```powershell
Set-Location E:\new\fpga_lock\v94\software\redpitaya_lock_host
.\run.bat
```

## GUI 模式

- Hardware Bring-up：Official SCPI Mode，用于 Probe、Start SCPI Server、Connect SCPI、官方 ASG OUT2 Safe Scan、IN1/IN2 acquisition。
- Custom FPGA Observe：用于记录 IN1 PD/MTS、IN2 REF、OUT1 `laser_error`、OUT2 `selected_out2`。Custom FPGA Control 通过 SSH + `/dev/mem` 控制 SAFE/SCAN/LOCK HERE/Apply Kp。OUT2 的目标执行器是激光器专用 PZT / Scan 输入。
- Lock Workflow：PZT 基础稳频 checklist，用于记录输入安全、error observation、control observation、polarity、gain/limit 和 SAFE 条件。
- Data Log：把实验日志导出到 `docs/experiment_logs/`。

## 推荐硬件测试顺序

1. 先只打开软件。
2. 点击 `Probe`。
3. 如果是 Official SCPI Mode，按需要点击 `Start SCPI Server`。
4. 点击 `Connect SCPI`。
5. 确认 OUT2 幅度、偏置、limit 和 SAFE 设置。
6. 将 OUT2 接到激光器专用 PZT / Scan 输入。
7. 点击 `SCAN`。
8. 观察 MTS error 色散曲线。
9. 再把 IN1 接到小信号源测试。
10. 再把 IN2 接到 4.6 MHz REF 小信号源测试。
11. 最后才考虑接入实验链路；接入前必须重新确认幅度、偏置和安全边界。

## Custom FPGA Control 推荐顺序

```text
Custom FPGA Mode
-> Probe Registers
-> Status
-> SAFE
-> SCAN
-> Capture Waveform
-> click selected zero crossing
-> LOCK HERE, Kp=0 first
-> Apply Kp, suggested steps 0/4/8/16/32
-> UNLOCK / SAFE
```

`Probe Registers` 和 `Status` 只读。SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 写寄存器前必须确认 `MAGIC=0x4D545330`。

`LOCK HERE` 后不要重新填写历史锁点；FPGA 会同拍捕获 `ERROR_SETPOINT` 和 `LOCK_BIAS`。`Apply Kp` 只调 Kp、polarity 和 limit，不重捕获锁点。错误 polarity、输出接近 limit、持续 saturation 或通信失败时立即 `UNLOCK / SAFE`。

## OUT1/OUT2 预览

CH3 和 CH4 是软件生成的预览，不是 ADC 实测数据。

旧预览显示曾复用 IN1/IN2 acquisition 时间轴。默认 `sample_count=2048`、`decimation=1024` 时，采集窗口约为：

```text
2048 / (125e6 / 1024) = 16.78 ms
```

`50 Hz` 三角波周期是 20 ms，所以旧预览窗口短于一个完整周期，不能显示完整三角波。

现在预览使用独立时间轴：

```yaml
preview:
  cycles: 2
  min_points: 1024
  max_points: 5000
```

对于 `50 Hz`，CH4 预览覆盖两个完整周期，约 40 ms。注意：这仍然不是实测 OUT2 波形。

真实 OUT2 必须用示波器测量。OUT2 -> IN1 的物理回环测试只允许在安全幅度下进行，并且 Red Pitaya IN1/IN2 必须保持在 +/-1 V 内。

## 安全说明

Red Pitaya IN1/IN2 绝对输入电压不得超过 +/-1 V。

连接 OUT1/OUT2 到任何激光相关输入前，必须先用示波器确认 amplitude、frequency 和 offset。

不要一开始就用大信号驱动 laser scan/PZT input。

推荐初始 OUT2 设置：`50 Hz`、`0.05 V`、`0 offset`。

当前阶段 OUT2 允许且目标就是激光器专用 PZT / Scan 输入。禁止把 OUT2 接到激光器电流调制输入、D2-125 Servo Output 或 D2-125 Aux Output，禁止两个设备输出端并联。
