# Hardware Calibration SOP

## 当前范围

```text
Current Stage: v3LOCK-P0 / Stage 3 Hardware Verification
Current Gate: corrected OUT2 voltage mapping hardware re-validation
Allowed point: Scan center=0.800 V, amplitude=0.100 V, frequency=50 Hz
Hardware result: NOT VERIFIED
```

本 SOP 只验证修复后的单组 OUT2 SCAN 电压映射，不授权 LOCK HERE、APPLY P、P-only 或其他点位。软件测试通过不代表真实模拟输出已经通过。

校准后 `hold-v=0.0000 V` 会发送约 `-65 counts` 以抵消实测零偏，不再等于 raw count=0。旧的 HOLD exact-count=0 流程已暂停；没有独立 exact-count 安全入口时不得继续该旧流程。

## 接线

1. 断开 PZT；OUT2 本次只允许连接示波器。
2. 禁止 OUT2 与 D2-125 Servo Output、D2-125 Aux Output 或任何其他有源输出并联。
3. 使用与修复前测量相同的 scope load、DC coupling、probe ratio 和线缆；若原条件无法确认，记录实际条件并把结果标为不可直接比较。
4. 若不是 DC coupling，停止实验。

## 开始前检查

1. 点击 `Probe Registers`，只在 `MAGIC=0x4D545330`、`VERSION=0x00030001`、Identity=`Matched` 时继续。
2. 点击 `SAFE` 后再点 `Status`；必须看到 `MODE=0`、`ENABLE=0`、无 saturation。
3. 确认 PZT 已断开、OUT2 只接示波器、示波器量程足以覆盖 `0.7 V` 至 `0.9 V`。

## HV-1B 单组步骤

1. 设置 `PZT safe min=0.700 V`、`PZT safe max=0.900 V`。
2. 设置 `Scan center=0.800 V`、`Scan amplitude=0.100 V`、`Scan frequency=50 Hz`。
3. 点击 `START SCAN`。软件预期写入 center `5734 counts`、amplitude `694 counts`；`OUT2_MONITOR` 应在约 `5040..6428 counts` 内变化且无 saturation。
4. 示波器记录三角波 center、Vpp、frequency，以及 scope load、coupling、probe ratio。
5. 测量完成后立即点击 `STOP / SAFE`，再点 `Status` 确认 `MODE=0`、`ENABLE=0` 且无 saturation。
6. 将结果写入 `version/HARDWARE_VALIDATION.md`；未提供复测结果前保持 `[NOT VERIFIED]`。

## PASS / FAIL

PASS 必须同时满足：

- 三角波形正常，frequency 接近 `50 Hz`。
- center 在 `0.800 V` 的 +/-5% 内。
- Vpp 在 `0.200 V` 的 +/-5% 内。
- 无 saturation、削顶、异常跳变或通信错误。
- 实验后已确认 SAFE。

以下任一情况立即 SAFE 并停止：身份不匹配、通信失败、OUT2 越界、saturation、削顶、异常跳变、接线/负载不清楚、PZT 未断开、OUT2 与其他输出并联，或无法确认最终 SAFE。失败后先记录证据，不修改 RTL，不提高 Kp，不切换 polarity，不执行 LOCK HERE。

## 下一步唯一动作

保持 PZT 断开且 OUT2 只接示波器，执行上述 HV-1B 单组复测，记录 center、Vpp、frequency 和测量条件，然后立即 SAFE。
