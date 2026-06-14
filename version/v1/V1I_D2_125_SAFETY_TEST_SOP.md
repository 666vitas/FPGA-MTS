# V1I D2-125 安全接入实验 SOP

## 0. 本文件作用

本文件是 `v1i_D2-125` 安全接入前置验证的实验 SOP。当前目标不是闭环锁定，而是确认：

```text
FPGA OUT1 error-like signal
  -> D2-125 error input
  -> D2-125 后级输出 / monitor
```

这条链路是否安全、可重复、不过载、不过度削顶，并且和真实 PD / scan 结构有物理对应关系。

当前用户只需要做接线、示波器观察、截图和 CSV 保存；不要写代码，不要运行 Vivado，不要修改 bitstream。

## 1. 当前已知前提

当前 FPGA 程序参数：

```text
USE_LASER_LOCK_CORE = 1'b1
LASER_LOCK_OUTPUT_MODE = 3
```

当前 FPGA 数据流：

```text
IN1 = 模拟前级处理后的 PD 调制信号
IN2 = 同源 4.6 MHz REF

FPGA:
  IN1 x IN2
  -> mixer_core
  -> lpf_core
  -> output_protect
  -> OUT1
```

已经观察到：

- FPGA 直接输出 error-like signal 约 `160 mVpp`；
- 三通 / 并联 REF 条件下，FPGA OUT1 可能下降到约 `30-120 mVpp`；
- FPGA OUT1 输入 `D2-125` 后，D2-125 后级输出 CH3 约 `3.42 Vpp`；
- 这说明 D2-125 对 FPGA error-like signal 有明显响应；
- 但当前还没有完成闭环锁定，也没有替代 D2-125 PID / servo。

## 2. 本次实验目标

本次只验证三件事：

1. `FPGA OUT1 -> D2-125 error input` 是否安全；
2. D2-125 后级输出是否有清晰、可重复、不过载的误差信号结构；
3. 该输出是否依赖真实 PD 输入和 4.6 MHz REF。

本次不做：

- 不闭环；
- 不让 D2-125 输出接激光器反馈；
- 不调 FPGA PID；
- 不做 AI；
- 不把一次看到 CH3 大输出当作“已经锁住”。

## 3. 推荐接线

### 3.1 FPGA 输入

```text
PD
  -> 10 MHz LPF
  -> 1.8 MHz HPF
  -> ZFL-500LN+ amplifier
  -> Red Pitaya IN1

4.6 MHz REF
  -> Red Pitaya IN2
```

注意：

- `IN1` 不是原始 PD 直接进板，而是模拟前级处理后的 PD 调制信号；
- `IN2` 必须是和 EOM 同源的 `4.6 MHz REF`；
- 进入 Red Pitaya 前必须用示波器确认幅度和 offset 安全。

### 3.2 FPGA 输出到 D2-125

```text
Red Pitaya OUT1
  -> D2-125 error input
```

第一轮只观察 D2-125 后级响应。D2-125 输出不要接激光器反馈。

### 3.3 示波器通道建议

```text
CH1: scan / ramp
CH2: PD / 饱和吸收相关信号
CH3: D2-125 后级输出 / monitor
CH4: FPGA OUT1，如果通道足够；如果 CH4 不够，可分两轮测
```

如果示波器通道不够，优先同时观察：

```text
CH1 scan
CH2 PD
CH3 D2-125 后级输出
```

另开一轮单独确认 `FPGA OUT1`。

## 4. 实验步骤

### Step 1：只看 FPGA OUT1

先不要接 D2-125。

1. `OUT1 -> 示波器`；
2. 确认 FPGA OUT1 仍有 error-like signal；
3. 记录 Vpp、offset、是否削顶、是否随 scan 重复；
4. 如果 OUT1 消失或明显异常，停止，不进入下一步。

### Step 2：接入 D2-125，但不开闭环

1. 断开 D2-125 到激光器反馈的闭环输出；
2. `FPGA OUT1 -> D2-125 error input`；
3. 观察 D2-125 后级输出 CH3；
4. 记录 CH3 Vpp、offset、削顶、噪声、过零点；
5. 确认 CH3 没有异常跳变、顶死或持续饱和。

### Step 3：IN1 依赖性测试

1. 保持 REF 接入；
2. 断开 `Red Pitaya IN1` 或断开模拟前级到 IN1；
3. 观察 CH3 是否明显变化、消失或变成无相关噪声；
4. 恢复 IN1 后，观察 CH3 是否恢复。

判断：

- 如果断开 IN1 后 CH3 不变，说明当前 CH3 可能不是由 PD 信号造成，需要停下来排查；
- 如果断开 IN1 后 CH3 消失或明显变化，说明链路依赖 PD 输入，这是好现象。

### Step 4：IN2 / REF 依赖性测试

1. 保持 IN1 接入；
2. 断开 `Red Pitaya IN2` 的 4.6 MHz REF；
3. 观察 CH3 是否明显变化；
4. 恢复 REF 后，观察 CH3 是否恢复。

判断：

- 如果断开 REF 后 CH3 不变，说明当前输出可能不是同步解调结果；
- 如果断开 REF 后 CH3 明显变化，说明 mixer+LPF 结果确实依赖同步 REF。

### Step 5：OUT1 依赖性测试

1. 保持 IN1/IN2 接入；
2. 断开 `FPGA OUT1 -> D2-125 error input`；
3. 观察 D2-125 后级输出是否明显变化；
4. 恢复 OUT1 后，观察是否恢复。

这一步用于确认 CH3 真的是 D2-125 对 FPGA error input 的响应。

### Step 6：极性和 offset 记录

记录：

- CH3 相对于 CH2 / CH1 的过零位置；
- CH3 极性是否和模拟 error 一致；
- 如果反相，先记录，不要急着改；
- 反相可以后续通过 REF 相位、FPGA 取反或 D2-125 polarity 处理。

### Step 7：多周期重复性

至少观察多个 scan 周期，记录：

- CH3 是否每个周期都有相似结构；
- 过零点是否漂移；
- Vpp 是否大幅变化；
- 是否存在呼吸、跳变或饱和。

## 5. 好现象

下面现象说明可以继续向低风险闭环准备推进：

1. D2-125 后级输出 CH3 有清晰误差信号结构；
2. CH3 与 CH1 scan / CH2 PD 峰位置对应；
3. CH3 有清晰过零点；
4. CH3 噪声可接受；
5. CH3 没有明显削顶；
6. CH3 多个 scan 周期重复；
7. 断开 IN1、IN2 或 OUT1 时，CH3 明显变化或消失；
8. 恢复接线后 CH3 恢复；
9. D2-125 后级没有异常跳变；
10. FPGA OUT1 和 D2-125 后级输出都在安全范围内。

## 6. 立即停止条件

只要出现下面任一现象，立即停止实验并断开 D2-125 输入：

1. D2-125 后级输出顶死或长时间饱和；
2. 输出出现异常尖峰或大跳变；
3. D2-125 或 Red Pitaya 输出幅度超过已知安全范围；
4. CH3 与 IN1/IN2/OUT1 依赖关系不成立；
5. D2-125 输出不受控制地漂移；
6. 接线或信号源状态不确定；
7. 无法确认 D2-125 输出是否连接到激光器反馈。

停止后只记录现象，不要现场盲改 FPGA。

## 7. 何时允许低增益短时间闭环

只有同时满足以下条件，才允许准备低增益短时间闭环：

1. FPGA OUT1 输入 D2-125 安全；
2. D2-125 后级输出不过载、不削顶；
3. CH3 过零点清晰；
4. CH3 与 PD / scan 结构对应；
5. IN1/IN2/OUT1 依赖性测试通过；
6. 极性已确认，或已经有安全的反相方案；
7. offset 合适；
8. D2-125 输出到激光器反馈路径已确认；
9. servo gain 从很低开始；
10. 有随时断开反馈的方案。

如果这些条件不满足，不允许闭环。

## 8. 记录模板

```text
日期：
阶段：v1i_D2-125 安全接入前置验证
FPGA 参数：USE_LASER_LOCK_CORE=1'b1, LASER_LOCK_OUTPUT_MODE=3
bit/bin 文件：
fpgautil 加载命令：

接线：
IN1：
IN2：
OUT1：
D2-125 输出是否接激光器反馈：

示波器：
CH1：
CH2：
CH3：
CH4：

观察：
FPGA OUT1 Vpp：
D2-125 后级 CH3 Vpp：
CH3 offset：
CH3 是否削顶：
CH3 过零点：
CH3 噪声：
多周期重复性：

依赖性测试：
断开 IN1：
断开 IN2：
断开 OUT1：

结论：
是否允许准备低增益短时间闭环：
下一步：
```

## 9. 小白必须理解

`v1i` 不是“FPGA 已经替代 D2-125”。它只是检查：

```text
FPGA 算出来的 error-like signal
能不能安全地送进 D2-125，
并让 D2-125 后级产生合理响应。
```

真正替代 D2-125 的 PID / servo，是 `v2` 以后才做。当前最重要的是安全、因果关系和可重复性。
