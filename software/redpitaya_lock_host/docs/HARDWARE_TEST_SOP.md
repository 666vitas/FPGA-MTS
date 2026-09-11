# 硬件测试 SOP

> **LOCK-MVP-L1 当前证据（2026-09-11）**
> 已生成首次板级测试候选 bit：`releases/20260911_LOCK-MVP-L1_CANDIDATE_8fc084e/red_pitaya_top_CANDIDATE.bit`，SHA-256 `6E5077DE121E261C198FB828E4178687932A79BC9D468D3931FE796A2369CB0B`。它是 CANDIDATE，不是硬件验证通过的 release；未连接板卡、未加载、未烧录。
> 本轮离线实现 run 为 `l1_candidate_impl_final_20260911`，WNS 0.024 ns、TNS 0、WHS 0.049 ns、THS 0；DRC 无 Critical Warning/Error。板级 I/O delay 和 CDC No ASYNC_REG 仍需人工审查，不能用旧 bit 声称验证本次修复。

按本顺序执行。前面的检查没有通过之前，不要连接 PD、laser scan / PZT 或任何真实执行器。

当前上位机开发目录：

```text
E:\new\fpga_lock\v94\software\redpitaya_lock_host
```

## 本轮 Custom FPGA 首次加载（唯一允许入口）

只执行以下五步：**候选身份/哈希确认 → 用户手动加载 → identity 读回 → SAFE 读回 → 示波器验证实际输出**。

加载时先将 FPGA 输出与激光执行器隔离，不改变 D2 参考主反馈链。上述五步未完成前，不连接 PD、laser scan/PZT 或任何真实执行器；本轮不批准 ACTIVE 或非零 Kp。完成后，只有在批准的接线和参数下才可进入 `ARM VALIDATE`。

下面第 1–10 节中的 SCPI server、`*IDN?` 和 Official SCPI OUT1/OUT2 波形步骤是另一条 Official SCPI 路径，不是本轮 Custom FPGA 首次加载步骤；Custom FPGA 用户不得按它们替代上面的五步。

## 1. Official SCPI 兼容路径（不用于本轮 Custom FPGA 首次加载）

1. 不连接任何实验信号。
2. 启动上位机。
3. 输入 `rp-f0cb13.local` 或 Red Pitaya 直接 IP。
4. 点击 `Probe`。
5. 确认 resolved IP、ping、端口 22、端口 80、端口 5000 的状态。

成功现象：GUI 显示网络和端口状态，不冻结。

失败处理：如果 IP 漂移或端口不通，先修网络，不继续接线。

## 2. 通过 SSH 启动 SCPI Server

如果端口 5000 不可用，但端口 22 可用：

1. 输入 SSH 用户名，通常是 `root`。
2. 输入 SSH 密码。
3. 点击 `Start SCPI Server`。
4. 确认 GUI 报告 5000 端口可用。

如果 Probe 已经显示 `SCPI True`，跳过本节，直接点击 `Connect SCPI`。

启动 SCPI 后 `Web False` 不一定是失败，因为 `redpitaya_nginx` 可能被停止以便 `redpitaya_scpi` 监听 5000 端口。

等效手动命令：

```sh
systemctl stop redpitaya_nginx
systemctl start redpitaya_scpi
systemctl status redpitaya_scpi --no-pager
ss -lntp | grep 5000
```

## 3. PC 侧确认端口

在 PowerShell 中运行：

```powershell
Test-NetConnection rp-f0cb13.local -Port 5000
```

或使用当前选定 IP：

```powershell
Test-NetConnection 192.168.137.125 -Port 5000
```

成功现象：`TcpTestSucceeded` 为 `True`。

## 4. 连接 SCPI

1. 点击 `Connect SCPI`。
2. 确认 `*IDN?` 返回 Red Pitaya 响应。

失败处理：如果无响应，不继续输出测试，先检查 5000 端口和 `redpitaya_scpi` 状态。

## 5. OUT2 示波器测试

本节只用于 Official SCPI Mode。

1. 只把 OUT2 接到示波器。
2. 设置 OUT2 waveform 为 `triangle`。
3. 设置 frequency 为 `50 Hz`。
4. 设置 `amplitude_v = 0.05 V`。
5. 设置 `offset_v = 0 V`。
6. Enable OUT2 并点击 `Apply`。
7. 在示波器上确认波形安全。

成功现象：示波器看到安全幅度的 50 Hz 三角波。

注意：CH4 是软件生成预览，不是实测 OUT2。50 Hz 三角波周期是 20 ms，GUI preview 只用于辅助判断；真实 OUT2 以示波器为准。

## 6. OUT1 示波器测试

本节只用于 Official SCPI Mode。

1. 只把 OUT1 接到示波器。
2. 设置 OUT1 waveform 为 `sine`。
3. 设置 frequency 为 `1 kHz`。
4. 设置 `amplitude_v = 0.05 V`。
5. 设置 `offset_v = 0 V`。
6. Enable OUT1 并点击 `Apply`。
7. 在示波器上确认波形安全。

## 7. IN1 采集测试

1. 把 signal generator 接到 IN1。
2. 使用 `1 kHz sine`、`100 mVpp`。
3. 开始 acquisition。
4. 确认 CH1 显示波形，并且 Vpp / min / max / mean 合理。

## 8. IN2 采集测试

1. 把 signal generator 接到 IN2。
2. 使用 `4.6 MHz sine`、`100 mVpp`。
3. decimation 设置为 `1`、`2`、`4` 或 `8`。
4. 开始 acquisition。
5. 确认 CH2 显示波形。

## 9. PD 连接

只有前面检查全部通过后，才允许：

1. 先用示波器测 PD signal。
2. 确认绝对电压小于 `1 V`。
3. 把 PD 接到 IN1。
4. 开始 acquisition 并验证 CH1。

如果 PD 信号接近或超过 Red Pitaya 输入范围，立即停止，不接 IN1。

## 10. Laser Scan / PZT 连接

当前 Custom FPGA 路径的 OUT2 目标是激光器专用 Scan/PZT 输入。接入必须满足以下条件：

1. 确认当前是 Custom FPGA Mode，OUT2=selected_out2；确认 D2 AUX 未与 OUT2 并联。
2. 先只把 OUT2 接到示波器。
3. 使用操作者已验证的扫描幅度、偏置和限幅；真实硬件安全范围仍待记录，不能采用软件默认值代替。
4. 确认 amplitude 和 offset 对后级输入安全。
5. 不要直接从大 scan amplitude 开始。
6. 确认 D2 Main 双分支反馈接线不变，人工完成电流/PZT 预调后，才允许连接前面 SCAN/PZT。

## 11. Custom FPGA Mode 安全

加载与当前源码绑定的候选 custom bitstream 时，当前 RTL 路由为：

- OUT1 = `laser_error`
- OUT2 = `selected_out2`

Custom FPGA Mode 下，先只接示波器验证 OUT2，再按本 SOP 接入原 AUX 所接的前面 SCAN。不要把 OUT2 接到激光器电流调制输入、D2 Main 输出或 D2 AUX，也不要与任何设备输出端并联。

当前 host 可以控制 custom FPGA register path 的 SAFE/SCAN、ARM VALIDATE、用户批准后的 ARM ACTIVE 和 P-only Apply；HOLD/PI_LOCK、自动重锁和持续稳频仍不属于本轮已验证能力。本轮只允许先完成身份/SAFE/示波器五步入口，未批准 ARM ACTIVE 或非零 Kp；验证成功、Kp=0 捕获成功、P-only 实验和持续稳频必须分别记录。

使用 Custom FPGA Observe Mode 记录 OUT1/OUT2 手动示波器读数。OUT2 达到操作者确认的电压边界、快速爬升、振荡或随机跳变时立即停止；真实 SCAN 安全电压、极性和允许 Kp 尚待确认。

## 12. 本轮选点到 P-only 操作判据

操作前提：Probe/identity 匹配、MAGIC/VERSION/capability 正确、OUT2 示波器幅度安全、MODE=SCAN、ENABLE=1、无 saturation；目标点必须来自本次 capture，会话重连或重扫后旧目标作废。

真实按钮顺序：`Capture Waveform` → 选零交叉 → `Confirm Lock Point` → `ARM VALIDATE` → 刷新 `Status` → 核对 `event_type=VALIDATED`、`valid=1`、新 sequence、方向和本次 generation。下一阶段需用户明确批准，先在 Kp 下拉框选择 0，再点击 `ARM BASIC LOCK`（ACTIVE）；接管后核对偏置。非零 P-only 实验另经批准，工程诊断按钮名称为 `APPLY P`，不得把它作为正常实时获取的替代。

预期寄存器/事件：VALIDATE 先进入 `acquisition_state=2`，事件完成后回到 `SCAN=1`，MODE/ENABLE、偏置和 Kp 不变；快速完成可以首次读回就是 SCAN，但必须有新 sequence 和匹配 generation/方向。ACTIVE 匹配事件后进入 `ACQUIRING=4`，事件中的 OUT2 是实际捕获样本；Kp=0 时校正量为零。示波器测点为 OUT2 及前面 SCAN 输入、OUT1 误差信号，确认接管前后偏置连续；可接受跳变量需由操作者按仪器噪声和硬件范围预先规定。

判据分层：① 验证成功＝本次匹配事件且无反馈接入；② Kp=0 捕获成功＝停扫并保持正确偏置；③ P-only＝另经批准后观察真实误差是否减小且无振荡/限幅；④ 持续稳频＝预先规定的持续时间、扰动和误差统计下实测通过。`P_LOCKED=5` 仅表示 FPGA 监督窗口判据通过，不替代第④项。

失败条件：旧/错 generation 事件、方向不符、目标过期、读回状态不符、非零 Kp 但状态不是 ACQUIRING/P_LOCKED、saturation、FAILED/FAULT 或通信中断。立即点击 `UNLOCK / SAFE`，确认 MODE=SAFE、ENABLE=0、acquisition_state=SAFE；无法确认 SAFE 时停止后级连接并人工断开执行器。
