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
-> ARM VALIDATE, inspect matching VALIDATED event/generation
-> user authorizes ARM BASIC LOCK (ACTIVE), select Kp=0 before ARM
-> verify captured bias with Kp=0; any nonzero P-only gain needs separate approval
-> UNLOCK / SAFE
```

`Probe Registers` 和 `Status` 只读。SAFE/SCAN/HOLD/P_LOCK/PI_LOCK 写寄存器前必须确认 `MAGIC=0x4D545330`。VALIDATE 成功只表示本次事件被识别；它会回到 SCAN，不会接入反馈。只有用户随后发出 ACTIVE，FPGA 才在新的匹配事件上接管。

ACTIVE 接管时 FPGA 会同拍捕获实际 `OUT2`、`ERROR_SETPOINT` 和 `LOCK_BIAS`。`Apply Kp` 只调 Kp、polarity 和 limit，不重捕获锁点；命令成功不等于 P_LOCKED，必须等待状态读回。错误 polarity、输出接近 limit、持续 saturation 或通信失败时立即 `UNLOCK / SAFE`。

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

文中 Official SCPI 数值仅用于独立示波器测试，不是激光器电源的安全值。真实 SCAN 输入电压范围、反馈极性和允许增益仍待操作者确认；保留用户已验证的扫描设置，不从论文或软件默认值推定。

当前阶段 FPGA OUT2 接管原 AUX 所接的前面 SCAN，允许在安全幅度下接激光器专用 PZT/Scan 输入。D2 Main 双分支反馈保持不变；D2 AUX 不得与 FPGA OUT2 并联。人工电流/PZT 预调由操作者完成，本轮不实现 D2 自动慢积分。
