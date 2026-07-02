# v2B3 only-pi 示波器测试记录与 v2B3_scope_safe 修正方案

## 1. 本次 only-pi.csv 的接线说明

本次数据来自 v2B3 / only-pi 上板示波器观察。Red Pitaya 输入和板上输出含义如下：

```text
Red Pitaya IN1 <- PD + BPF + Amp 后的 MTS/PD 信号，必须在 +/-1 V 内
Red Pitaya IN2 <- 外部 REF，必须在 +/-1 V 内

Board OUT1 -> 示波器 CH1
Board OUT2 -> 示波器 CH4
```

本次仍然只是示波器验证，不是真实反馈测试。OUT2 没有资格接入激光器、D2-125 Servo Output、D2-125 Aux Output 或 Scan/PZT。

## 2. 各通道含义

```text
CH1 / Board OUT1：
  FPGA mixer + LPF 后的 error observation。

CH2：
  饱和吸收 / PD 相关信号。

CH3：
  D2-125 / analog error 相关观测信号。

CH4 / Board OUT2：
  CONTROL_PATH_MODE=1 下 pi_controller_seq 的 control_o candidate。
```

CH3 幅度已经超过 Red Pitaya IN1/IN2 安全输入范围，因此 CH3 只能作为示波器观测，不能直接进入 Red Pitaya IN1/IN2。

## 3. OUT1 / CH1 数据

```text
Board OUT1:
Vpp ≈ 0.05385 V
min ≈ -0.02714 V
max ≈ +0.02671 V
RMS ≈ 0.009618 V
```

判断：

```text
OUT1 能看到 FPGA mixer + LPF 后的 error-like 信号。
OUT1 没有明显满量程削顶。
OUT1 链路基本正常。
```

## 4. CH2 数据

```text
CH2:
Vpp ≈ 0.151 V
min ≈ 0.593 V
max ≈ 0.744 V
RMS ≈ 0.6554 V
```

判断：

```text
CH2 能看到谱线 / PD 相关信号。
说明光学扫描和谱线信号仍存在。
```

## 5. CH3 数据

```text
CH3:
Vpp ≈ 2.443 V
min ≈ -1.102 V
max ≈ +1.341 V
RMS ≈ 0.3496 V
```

判断：

```text
CH3 外部 D2-125 / analog error 相关信号较大。
该信号不能直接进入 Red Pitaya IN1/IN2。
IN1/IN2 仍必须保持在 +/-1 V 内。
```

## 6. OUT2 / CH4 数据

```text
Board OUT2:
Vpp ≈ 0.01497 V
min ≈ -0.2036 V
max ≈ -0.1886 V
RMS ≈ 0.1991 V
mean ≈ -0.199 V
```

判断：

```text
OUT2 长期贴在约 -0.2 V 附近。
OUT2 只剩约 15 mVpp 的小动态。
这不是 v2B3 通过现象。
疑似 sequential PI 的积分项把 control_o 推到负向 output_limit 附近。
```

## 7. 本次通过 / 失败判断

本次 `only-pi.csv` 不是 v2B3 通过数据。

```text
OUT1 正常：
FPGA mixer + LPF error observation 链路仍可见。

OUT2 异常：
Board OUT2 / CH4 长期贴在约 -0.2 V 附近，并出现底部类似“削底”的现象。
这更像是 control_o 被 output_limit 限幅，而不是 Red Pitaya +/-1 V 满量程物理削顶。
```

因此本次不能进入真实反馈测试，也不能关闭 v2B3。

## 8. OUT2 负向限幅 / 积分饱和的可能原因

可能原因：

```text
OUT1 error 存在 DC 偏置或平均误差；
PID_KI_DEFAULT 当前非零；
积分器在一段时间内累积同号误差；
control_o 被推到负向 output_limit；
导致 OUT2 动态范围只剩约 15 mVpp。
```

专业说法：
`pi_controller_seq` 的积分项可能在持续同号 error 下把 `control_o` 推到负向 `output_limit`。

小白理解：
OUT2 像被一直往负方向推，最后贴在安全限幅墙上，只剩很小一点抖动。

在本项目中的对应关系：
`PID_KI_DEFAULT=16` 时，示波器 CH4 看到 OUT2 长期贴在约 `-0.2 V`，这接近原 `PID_OUTPUT_LIMIT_DEFAULT=1500` 的输出范围。

如果做错的风险：
如果直接接入真实执行器，可能把控制端长期推向错误方向，造成发散、拉飞锁点或误接风险。

## 9. 下一版 v2B3_scope_safe 修正建议

`v2B3_scope_safe` 的目标不是增强功能，而是让 OUT2 回到安全、可解释、不会贴限幅的示波器验证状态。

本轮建议并已采用的 RTL 参数修正：

```text
v0.94/rtl/laser_lock_core.sv

PID_KI_DEFAULT = 16'sd0
PID_OUTPUT_LIMIT_DEFAULT = 14'd819
```

含义：

```text
Ki=0：
  先关闭积分项，验证 CONTROL_PATH_MODE=1 下 pi_controller_seq 的 P 路径是否安全。

output_limit=819：
  约等于 +/-0.10 V，让 OUT2 远离 Red Pitaya +/-1 V 满量程。
```

如果 OUT2 仍然偏置明显或接近 limit，下一轮再降到：

```text
PID_OUTPUT_LIMIT_DEFAULT = 14'd410
```

约等于 `+/-0.05 V`。

保持不变：

```text
CONTROL_PATH_MODE=1 仍然使用 pi_controller_seq
OUTPUT_MODE=3 仍然让 OUT1 显示 mixer + LPF error
OUT1 / OUT2 顶层 DAC 路由不变
mixer_core 不改
lpf_core 不改
output_protect 不改
pi_controller_seq 主体状态机不改
red_pitaya_top.sv 不改
```

禁止新增：

```text
scan_lock_fsm
ramp_generator
register_bank
AI
上位机控制
timing exception
```

## 10. 绝对安全边界

```text
本次不能进入真实反馈测试。
OUT2 仍只能接示波器。
禁止 OUT2 接激光器。
禁止 OUT2 接 D2-125 Servo Output 三通。
禁止 OUT2 接 D2-125 Aux Output。
禁止 OUT2 接激光器电源 Scan / PZT。
禁止 OUT2 与任何 D2-125 输出并联。
IN1/IN2 必须在 +/-1 V 内。
```

只有当 `v2B3_scope_safe` 同时满足下面条件，才可以关闭 v2B3：

```text
1. timing 通过；
2. OUT1 error 正常；
3. OUT2 不再贴 limit；
4. OUT2 不随机跳变；
5. OUT2 不接近 +/-1 V；
6. OUT2 行为能用 Ki=0 的 P-only through pi_controller_seq 解释；
7. 所有数据已保存。
```

v2B3 关闭后，才讨论 v2D / v2E 或后续 v2PZT 路线。
