# Hardware Calibration SOP

## 当前范围

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current Gate: HV-1 OUT2 fixed-count physical voltage calibration
Allowed point: count=0 only
Hardware result: NOT VERIFIED
```

本 SOP 只建立 OUT2 的第一个真实测量点。禁止执行非零 count、SCAN、LOCK HERE、APPLY P 或 P-only。本文中的判据是计划判据，必须由用户真实实验结果确认；当前没有执行任何硬件校准。

## 目标

验证上位机请求 count=0 后，`OUT2_MONITOR`、CH4 和示波器 OUT2 真实 DC 电压之间的对应关系。GUI 的 `V` / `mV` 只表示 nominal/ideal 换算，示波器读数才是本 Gate 记录的真实物理电压。

## 接线

1. 断开 PZT；本次不允许 OUT2 连接激光器或任何 Scan/PZT 输入。
2. 只连接 `Red Pitaya OUT2 -> oscilloscope input`。
3. 禁止 OUT2 与 D2-125 Servo Output、D2-125 Aux Output 或任何其他有源输出并联。
4. 记录 scope input 为 `50 ohm` 或 `1 Mohm/Hi-Z`、probe ratio 和 `DC coupling`。若不是 DC coupling，停止本实验。
5. 同一份校准记录不得混用不同 load、probe ratio、coupling 或线缆配置。

## 开始前检查

1. 确认当前 GUI 连接的是目标 Red Pitaya，PZT 已物理断开，OUT2 只接示波器。
2. 在 `Advanced` 中点击 `Probe Registers`。
3. 只在读回 `MAGIC=0x4D545330` 且 `VERSION=0x00030001` 时继续；否则停止，不尝试绕过身份检查。
4. 点击 `Status`，记录初始 `MODE`、`ENABLE`、`STATUS`、`OUT2_MONITOR` 和 saturation。
5. 点击 `SAFE`，再点击 `Status`；必须看到 `MODE=0`、`ENABLE=0`、无 saturation。无法确认时停止。

## HV-1 count=0 单点步骤

1. 在 `Advanced` 的 `hold-v` 输入 `0.0000 V`。该字段是 nominal 输入，但代码会把它精确转换成 requested count=0；不得把 `0.0000 V` 标签当作示波器真实电压。
2. 再确认 PZT 已断开、OUT2 只接示波器且没有有源输出并联。
3. 点击 `HOLD`。现有上位机发送 `HOLD_VALUE=0`，选择 `MODE=2` 并设置 `ENABLE=1`。注意：HOLD 不受 SCAN `OUT2_LIMIT` 保护，因此本轮禁止输入任何非零值。
4. 操作返回后点击 `Status`，记录：requested count=`0`、`OUT2_MONITOR`、`MODE`、`ENABLE`、`STATUS` 和 saturation。
5. 只有 `MODE=2`、`ENABLE=1`、`OUT2_MONITOR=0` 且无 saturation 时，才点击一次 `Capture Waveform`，记录 CH4 raw count。CH4 是 pre-DAC digital count，不是物理电压。
6. 在示波器上读取并记录 OUT2 的 DC mean、min 和 max，同时记录 scope load、coupling、probe ratio 和 repeat index。
7. 测量完成后立即点击 `SAFE`，再点击 `Status`，确认 `MODE=0`、`ENABLE=0` 且无 saturation。
8. 将记录写入 `version/HARDWARE_VALIDATION.md` 的 count=0 行；在用户确认前保持 `[NOT VERIFIED]`。

## PASS / FAIL 判据

PASS 只能由用户真实硬件结果确认，并至少满足：

- `MAGIC` / `VERSION` 正确。
- requested count=0、`OUT2_MONITOR=0`，CH4 稳定在 0 count 或能解释的单 count 读回范围内。
- `MODE=2`、`ENABLE=1` 且无 saturation。
- 示波器波形稳定，无异常跳变、削顶或过压；DC mean/min/max 已记录。
- 实验后已确认 SAFE。

以下任一项为 FAIL：readback 不一致、通信中断、身份不匹配、saturation、异常跳变、削顶、过压、接线或负载不清楚、PZT 未断开，或无法确认最终 SAFE。FAIL 后停止当前 Gate，先审计证据，不进入非零点、SCAN、LOCK HERE 或 P-only，也不直接猜测修改 RTL。

## 负载与系数限制

本次 count=0 只能记录零点，不能得到 `counts_per_volt` 或完整线性校准。未来即使在 50 ohm 下拟合出系数，也不能自动用于 Hi-Z 或 PZT；Hi-Z/PZT 系数也不能反向用于 50 ohm。每组系数必须绑定对应的 load、probe ratio、coupling、线缆和板卡身份。

## 通信失败处理

通信失败时，不得绕过上位机直接写寄存器，也不得继续下一步。若 GUI 仍可通信，点击 SAFE 并确认；若无法确认 SAFE，则停止操作并报告“SAFE NOT CONFIRMED”，不要继续接线或测量。

## 下一步唯一动作

断开 PZT，使 OUT2 只连接示波器，按照本 SOP 只执行 count=0 的 HV-1 测量，记录 readback 和示波器真实电压，然后立即 SAFE。
