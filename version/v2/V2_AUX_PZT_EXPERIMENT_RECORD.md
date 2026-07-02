# V2 Aux/PZT 实验记录与后续 scan/lock 计划

## 2026-07-02 记录范围

本文件记录用户确认的 D2-125 Auxiliary Servo Output 在 Ramp / Unlock / Lock 状态下的实测数据，并据此更新后续 v3/v4/v5 的设计参考。

本次只整理 Markdown 文档：

```text
未修改 RTL。
未修改 Python。
未修改 testbench。
未运行 Vivado。
未运行 synthesis / implementation。
未生成 bitstream / bin。
未烧录 Red Pitaya。
未修改 XDC / SDC。
未执行 git add / git commit / git push。
```

## 当前 FPGA 真实能力

当前 FPGA 已具备的真实链路是：

```text
IN1 + IN2 -> mixer_core -> lpf_core -> OUT1 error
error -> 简单 P/PI candidate -> OUT2 control
```

当前还没有实现：

```text
1. OUT2 内部三角波扫描；
2. Capture Vlock / HOLD；
3. P_LOCK / PI_LOCK 模式切换；
4. 上位机通过寄存器调 FPGA 参数；
5. AI 自动识峰、自动选 Vlock 或自动重锁。
```

因此当前不能声称已经实现 PZT 锁定，也不能把 OUT2 直接当作完整 D2-125 Aux Output 替代。当前 v2B3 / v2B3_scope_safe 阶段仍然只允许 OUT2 接示波器。

## 最新 Aux/PZT 数据

### ramp-aux-unlock.csv

状态：

```text
D2-125 Aux Output / Scan-PZT 通道，Ramp / Unlock 状态
```

CH4 为 D2-125 Aux Output：

```text
Vpp = 0.1173 V
min = 0.7505 V
max = 0.8678 V
mean 约 0.8087 V
主频约 52.68 Hz
```

解释：

```text
Aux Output 在 Ramp 状态约为：
0.81 V DC offset + 0.117 Vpp triangle，频率约 52.7 Hz。
```

### ramp-aux-unlock1.csv

状态：

```text
D2-125 Aux Output / Scan-PZT 通道，Ramp / Unlock 状态，另一组扫描幅度
```

CH4 为 D2-125 Aux Output：

```text
Vpp = 0.0626 V
min = 0.7767 V
max = 0.8393 V
mean 约 0.8096 V
主频约 52.68 Hz
```

解释：

```text
Aux Output 在较小扫描幅度下约为：
0.81 V DC offset + 0.063 Vpp triangle，频率约 52.7 Hz。
```

### ramp-aux-locking.csv

状态：

```text
D2-125 Aux Output / Scan-PZT 通道，Locked 状态
```

CH4 为 D2-125 Aux Output：

```text
Vpp = 0.0169 V
min = 0.8031 V
max = 0.8200 V
mean 约 0.8130 V
```

解释：

```text
Aux Output 在锁定状态约为：
0.813 V hold + 0.0169 Vpp residual / slow correction。
```

注意：

```text
Lock 状态下 CH4 的扰动很小，不应强行解释成大三角波。
它更接近保持电压附近的小幅慢控制扰动。
```

## 对 D2-125 Aux/PZT 的新认识

D2-125 Aux Output 不是单纯从 0 V 开始的三角波。根据最新数据：

```text
Ramp / Unlock 状态：约 0.81 V DC offset + 0.063~0.117 Vpp triangle，频率约 52.7 Hz。
Lock 状态：约 0.813 V hold + 0.0169 Vpp residual / slow correction。
```

因此 Red Pitaya OUT2 如果要替代 D2-125 Aux Output，后续应实现：

```text
scan_offset
scan_amp
scan_freq
Vlock
slow_scan_output_limit

SCAN 模式：
OUT2 = scan_offset + triangle

HOLD 模式：
OUT2 = captured_vlock

P_LOCK 模式：
OUT2 = captured_vlock + Kp * error

PI_LOCK 模式：
OUT2 = captured_vlock + Kp * error + Ki * integral(error)
```

最新 Aux 数据说明 D2-125 Aux Output 的电压范围约为 `0.75 V` 到 `0.87 V`，处于 Red Pitaya OUT2 约 `+/-1 V` 输出范围内。因此后续优先尝试 `Red Pitaya OUT2 -> Scan/PZT` 替代 D2-125 Aux Output 是可行路线，但必须先实现 SAFE / SCAN / HOLD，并先用示波器验证。

这些数据属于后续 v3/v4/v5 的设计参考，不改变当前 v2B3_scope_safe 接线边界。

## 能力边界

当前 FPGA 只能完成：

```text
mixer + LPF + 简单 P/PI candidate
```

当前还没有：

```text
OUT2 scan/lock mode selector
register_bank
Custom FPGA Mode 下的 FPGA 内部模式切换
PZT 锁定完整流程
```

当前上位机在 Custom FPGA Mode 下还不能写 FPGA 内部参数，不能切换 `SCAN / HOLD / P_LOCK / PI_LOCK`，也不能读取 FPGA 内部 debug/status 寄存器。

## 后续如何使用这些数据

### v3 ramp_generator

参考默认参数：

```text
scan_offset ≈ 0.81 V
scan_amp ≈ 0.03 V 到 0.06 V
scan_freq ≈ 52.7 Hz
```

说明：

```text
0.063 Vpp 对应约 +/-0.0315 V。
0.117 Vpp 对应约 +/-0.0585 V。
```

### v3 scan_lock_fsm

用于定义：

```text
SCAN 模式：
OUTx = scan_offset + triangle

HOLD 模式：
OUTx = captured Vlock

LOCK 模式：
OUTx = Vlock + slow correction
```

### v3 Aux/Scan replacement

用于确认未来替代 D2-125 Aux Output / Scan-PZT 时，不能输出零均值三角波，而要输出带 `scan_offset` 的慢扫描量，并且必须先确认 D2-125 Aux Output 已断开，避免并联。

### v4 上位机 Custom FPGA Lock Panel

用于设置默认参数：

```text
scan_offset_v = 0.81 V
scan_amp_v = 0.03 V 起步
scan_freq_hz = 52.7 Hz
Vlock 初始范围约 0.80~0.82 V
slow output limit 可参考 0.0169 Vpp 的 Lock 状态扰动
```

### v5 AI / 自动重锁

用于判断：

```text
正常扫描范围
正常锁定保持范围
失锁后 Rescan 的扫描幅度
AI 推荐 Vlock 的初始范围
```

## 更新后的阶段计划

```text
v2PZT-0：
记录 Aux/PZT 数据，确认 D2-125 Aux Output 的电压范围和作用。

v2PZT-1：
只实现 SAFE / SCAN / HOLD。
目标：OUT2 能输出 0.81 V offset + 小三角波，并能 Capture Vlock 后保持。

v2PZT-2：
OUT2 -> Scan/PZT 开环扫谱。
目标：断开 D2-125 Aux Output，Red Pitaya OUT2 接 Scan/PZT，确认能扫出谱线。

v2PZT-3：
P_LOCK。
目标：OUT2 = Vlock + Kp * error，Ki=0，验证反馈极性和 PZT 响应。

v2PZT-4：
PI_LOCK。
目标：OUT2 = Vlock + Kp * error + Ki * integral(error)，实现短时间 PZT 慢通道锁定。

v3REG：
新增 custom FPGA register_bank。
目标：上位机在 Custom FPGA Mode 下调 OUT2_MODE、scan_offset、scan_amp、Kp、Ki、polarity、output_limit，不再每次烧录。

v4HOST：
上位机新增 Custom FPGA Lock Panel。
目标：点击 SAFE / SCAN / HOLD / P_LOCK / PI_LOCK / RESCAN，并记录 error/control/Vlock。

v5AI：
上位机 AI 识峰、选 Vlock、推荐 Kp/Ki、判断失锁、触发重扫。
```

## 上位机和 FPGA 分工

FPGA 负责：

```text
实时 mixer
LPF
triangle scan
HOLD
P/PI control
OUT2 limit
polarity
reset_integrator
```

上位机负责：

```text
切换模式
写参数
记录数据
显示状态
后续 AI 识峰和调参
```

上位机不做高速实时 PID。AI 也不直接参与 125 MHz 实时控制。

## Official SCPI Mode 与 Custom FPGA Mode 边界

Official SCPI Mode：

```text
可以单独测试 OUT2 三角波、采集 IN1/IN2、做软件解调。
但它可能加载官方 overlay，不能和 custom FPGA lock 同时使用。
```

Custom FPGA Mode：

```text
OUT1 = FPGA error
OUT2 = FPGA control
后续必须通过 register_bank 切换 SCAN / HOLD / P_LOCK / PI_LOCK。
不能用 Official SCPI 的 SOUR2:FUNC TRIANGLE 来控制 custom FPGA OUT2。
```

## 安全边界

```text
Red Pitaya OUT2 不能和 D2-125 Aux Output 同时并联到 Scan/PZT。
Red Pitaya OUT2 不能和 D2-125 Servo Output 并联。
OUT2 初始必须先接示波器。
OUT2 输出必须限制在 +/-1 V 内。
当前 v2B3 / v2B3_scope_safe 阶段 OUT2 仍只能接示波器，不能因为记录了 Aux 数据就直接接 Scan/PZT。
```

第一次 SCAN 建议：

```text
scan_offset 约 0.81 V
scan_amp 约 0.03 V
scan_freq 约 52.7 Hz
```

第一次 P_LOCK 建议：

```text
Ki = 0
Kp 很小
output_limit = +/-0.01 V 到 +/-0.03 V
先 P-only，再 PI
```
