# BOARD_TEST_v1ab_passthrough_debug

## 0. 本文件作用

本文件说明 `v1ab_passthrough_debug` 的上板测试方法。

这个版本只用于验证输入输出通路：

- `v1a`：验证 `IN1 -> OUT1`；
- `v1b`：验证 `IN2 -> OUT1`，特别是 4.6 MHz `REF` 输入。

本文件不是闭环锁频说明，不接激光器反馈。

## 1. 测试前安全原则

必须遵守：

- `OUT1` 先接示波器，不接 `D2-125`；
- 不接激光器反馈；
- 第一阶段不做 PID；
- 第一阶段不做 sweep；
- 第一阶段不做 AI；
- 第一阶段不让 FPGA 生成 `REF`；
- 第一阶段不让 FPGA 驱动 EOM；
- `IN2` 的 `REF` 必须衰减到 Red Pitaya 输入安全范围内；
- 明确禁止把原模拟 mixer 的 `6.32 Vpp` REF 直接接入 `IN2`。

## 2. v1a：IN1 -> OUT1 测试接线

### 2.1 bitstream 配置

`laser_lock_core` 参数：

```text
OUTPUT_MODE = 0
```

含义：

```text
error_o = pd_i
```

### 2.2 接线

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器 CH2
```

### 2.3 v1a 信号发生器参数

建议从安全小信号开始：

```text
频率：1 kHz sine
幅度：100 mVpp
offset：0 V
```

如果波形正常，再逐步调整频率和幅度。

### 2.4 v1a 示波器通道

| 通道 | 信号 |
|---|---|
| CH1 | Red Pitaya `OUT1` |
| CH2 | 信号发生器输入参考 |

### 2.5 v1a 通过标准

通过标准：

- `OUT1` 能看到和 `IN1` 同频的波形；
- 幅度可以不完全一样；
- 允许反相；
- 允许有轻微延迟；
- `OUT2` 应没有有效控制输出。

不通过：

- `OUT1` 完全没波形；
- `OUT1` 长时间直流顶死；
- `OUT1` 严重削顶；
- `OUT1` 输出异常大电压。

## 3. v1b：IN2 -> OUT1 测试接线

### 3.1 bitstream 配置

`laser_lock_core` 参数：

```text
OUTPUT_MODE = 1
```

含义：

```text
error_o = ref_i
```

### 3.2 接线

```text
外部 REF 信号 -> 衰减器/安全幅度设置 -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
外部 REF 信号安全衰减后 -> 示波器 CH2
```

### 3.3 v1b 4.6 MHz REF 输入安全参数

目标频率：

```text
4.6 MHz
```

输入幅度要求：

```text
必须衰减到 Red Pitaya 输入安全范围内，例如 ±1 V 内。
```

强制禁止：

```text
不允许把原模拟 mixer 的 6.32 Vpp REF 直接接入 IN2。
```

建议第一次测试使用更保守的幅度，例如：

```text
100 mVpp ~ 500 mVpp
offset = 0 V
```

具体安全幅度以 Red Pitaya 当前输入量程和实验室接线为准。

### 3.4 v1b 示波器通道

| 通道 | 信号 |
|---|---|
| CH1 | Red Pitaya `OUT1` |
| CH2 | 衰减后的 4.6 MHz `REF` |

### 3.5 v1b 通过标准

通过标准：

- `OUT1` 能看到 4.6 MHz 同频波形；
- 幅度可以不完全一样；
- 允许反相；
- 允许轻微延迟；
- `OUT1` 不应长时间顶死或严重削顶。

## 4. OUT1 先接示波器，不接 D2-125

`v1a` 和 `v1b` 都是输入输出通路验证版本。

因此：

```text
OUT1 -> 示波器
```

不要接：

```text
OUT1 -> D2-125 error input
```

原因：当前还没有完成 mixer、LPF、gain/limit 的真实 error 输出，也还没有确认 `OUT1` 对 D2-125 是安全幅度和安全 offset。

## 5. 如果 OUT1 没波形怎么排查

| 排查项 | 怎么看 |
|---|---|
| 信号源是否真的有输出 | 用示波器直接量信号发生器输出 |
| 接线是否接到正确输入 | v1a 接 `IN1`，v1b 接 `IN2` |
| `OUTPUT_MODE` 是否正确 | v1a 用 0，v1b 用 1 |
| 示波器量程是否正确 | 调整垂直档位和触发 |
| Red Pitaya 是否加载了正确 bitstream | 重新确认加载文件 |
| reset 是否释放 | 若 reset 未释放，`output_protect` 会输出 0 |
| DAC A / OUT1 集成是否正确 | 后续 integration plan 中重点检查 |

## 6. 如果 OUT1 削顶怎么排查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 波形上下被切平 | 输入幅度太大 | 降低信号发生器幅度 |
| v1b 4.6 MHz 波形削顶 | `REF` 衰减不够 | 增加衰减，禁止 6.32 Vpp 直接进 `IN2` |
| 输出贴近最大/最小值 | DAC 路径或数据格式问题 | 回到仿真和 integration plan 检查 signed/unsigned |
| 波形有很大 DC offset | 信号源 offset 不为 0 或 DAC offset 问题 | 先把输入 offset 设为 0 V |

## 7. 如果 OUT1/OUT2 接反怎么确认

确认方法：

1. 示波器 CH1 接 `OUT1`；
2. 示波器 CH2 接 `OUT2`；
3. 加载 `OUTPUT_MODE=0` 的 v1a bitstream；
4. 给 `IN1` 输入 1 kHz 小信号；
5. 正常情况下，应主要在 `OUT1` 看到直通信号；
6. `OUT2` 不应有有效控制输出，因为 `control_o = 0`。

如果 `OUT2` 有明显波形而 `OUT1` 没有，需要检查：

- DAC A / DAC B 是否在 integration plan 中接反；
- `error_o` 是否接到了 DAC B；
- `control_o` 是否误接到了 DAC A；
- 示波器线缆是否标错。

## 8. 失败后回退原则

如果上板测试不正常：

1. 先停止接入 `D2-125`；
2. 只保留示波器；
3. 回到 `v1a` 测 `IN1 -> OUT1`；
4. 再回到 `v1b` 测 `IN2 -> OUT1`；
5. 不要继续进入 `v1c_mixer_only`，直到 v1a/v1b 都通过。
