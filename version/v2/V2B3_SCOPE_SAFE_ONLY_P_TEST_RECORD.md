# v2B3_scope_safe only-p.csv 上板示波器测试记录

## 1. 测试名称

```text
v2B3_scope_safe / only-p.csv scope test
```

本次测试目标是验证 `Ki=0`、`output_limit=819` 后，`CONTROL_PATH_MODE=1` 下 `pi_controller_seq` 的 P 路径是否安全、可解释。

本次仍然是示波器-only 测试：

```text
OUT1 -> 示波器
OUT2 -> 示波器
```

这不是闭环测试，不是 Scan/PZT 测试，也不是激光锁定测试。

## 2. 测试接线

```text
Red Pitaya IN1 <- PD + BPF + Amp 后的 MTS/PD 信号，必须在 +/-1 V 内
Red Pitaya IN2 <- 外部 REF，必须在 +/-1 V 内

Board OUT1 -> 示波器 CH1
Board OUT2 -> 示波器 CH4

CH2：饱和吸收 / PD 相关信号
CH3：D2-125 / analog error 相关观测信号
```

本次安全边界：

```text
OUT2 没有接激光器。
OUT2 没有接 Scan/PZT。
OUT2 没有接 D2-125 Servo Output。
OUT2 没有接 D2-125 Aux Output。
```

## 3. Board OUT1 / CH1 数据

```text
Board OUT1 / CH1:
Vpp ≈ 0.04874 V
min ≈ -0.01209 V
max ≈ +0.03665 V
RMS ≈ 0.01007 V
mean ≈ +0.00868 V
```

判断：

```text
OUT1 仍然显示 FPGA mixer + LPF error-like signal。
OUT1 没有消失。
OUT1 没有明显削顶。
OUT1 链路正常。
```

## 4. CH2 数据

```text
CH2:
Vpp ≈ 0.1482 V
min ≈ 0.5627 V
max ≈ 0.7108 V
RMS ≈ 0.6475 V
```

判断：

```text
CH2 能看到饱和吸收 / PD 相关谱线。
说明光学扫描和谱线仍存在。
```

## 5. CH3 数据

```text
CH3:
Vpp ≈ 2.322 V
min ≈ -1.187 V
max ≈ +1.134 V
RMS ≈ 0.2356 V
```

判断：

```text
CH3 是 D2-125 / analog error 相关大信号观测。
该信号不能直接进入 Red Pitaya IN1/IN2。
IN1/IN2 仍必须保持在 +/-1 V 内。
```

## 6. Board OUT2 / CH4 数据

```text
Board OUT2 / CH4:
Vpp ≈ 0.02410 V
min ≈ -0.00177 V
max ≈ +0.02233 V
RMS ≈ 0.00888 V
mean ≈ +0.00850 V
```

判断：

```text
OUT2 不再长期贴在 -0.2 V。
OUT2 不再贴近负向 output_limit。
OUT2 没有明显积分爬升。
OUT2 没有随机跳变。
OUT2 没有快速饱和。
OUT2 没有接近 +/-1 V。
OUT2 Vpp / OUT1 Vpp ≈ 0.02410 / 0.04874 ≈ 0.494。
OUT2 行为接近 Ki=0 后的 P-only control candidate。
```

## 7. 实验结论

本次 `v2B3_scope_safe / only-p.csv` 判定为：

```text
PASS WITH NOTES
```

理由：

```text
1. OUT1 error observation 正常；
2. OUT2 不再贴在 -0.2 V；
3. OUT2 不再积分爬升；
4. OUT2 不接近 +/-1 V；
5. OUT2 与 OUT1 的比例约 0.5，符合 Kp=2048、Ki=0 后的 P-only 安全行为；
6. v2B3_scope_safe 的主要目标已经达成：确认 pi_controller_seq 的 P 路径在示波器-only 条件下安全可解释。
```

Notes：

```text
这不是闭环锁定。
这不代表 FPGA 已经替代 D2-125。
这不允许直接进入 OUT2 接 Scan/PZT。
OUT2 仍然只能接示波器，直到后续 v2D/v2E/v2F SOP 明确允许。
v2B3 可以准备关闭，但需要把数据、Vivado timing 截图和 CSV 文件名记录完整。
```

## 8. 与旧 only-pi 异常数据对比

旧 `only-pi.csv`：

```text
OUT2 mean ≈ -0.199 V
OUT2 Vpp ≈ 0.01497 V
判断：OUT2 贴近负向 output_limit，未通过，疑似 Ki 积分导致饱和。
```

新 `only-p.csv`：

```text
OUT2 mean ≈ +0.00850 V
OUT2 Vpp ≈ 0.02410 V
判断：OUT2 不再贴 limit，P-only 行为正常，v2B3_scope_safe 通过。
```

结论：

```text
Ki=0 的 scope-safe 修正有效。
```

## 9. 当前仍禁止事项

```text
OUT2 禁止接激光器。
OUT2 禁止接 D2-125 Servo Output。
OUT2 禁止接 D2-125 Aux Output。
OUT2 禁止接 Scan/PZT。
OUT2 禁止和任何 D2-125 输出并联。
不能声称 FPGA 已经锁定。
不能声称 FPGA 已经替代 D2-125。
```

## 10. 下一步路线

当前下一步不是 CNN，不是接 Scan/PZT，也不是闭环锁定。

下一步准备单独任务：

```text
v2D: OUT2 hardcoded scan_offset + triangle scope-only test mode
```

该任务目标：

```text
在 laser_lock_core.sv 中增加一个编译时测试模式，让 OUT2 输出：
OUT2 = 0.81 V offset + 52.7 Hz triangle

用途：
只用于示波器验证 Red Pitaya OUT2 是否能复现 D2-125 Aux Ramp 的电压范围。
```

该任务以后单独执行。本次只记录，不写代码。
