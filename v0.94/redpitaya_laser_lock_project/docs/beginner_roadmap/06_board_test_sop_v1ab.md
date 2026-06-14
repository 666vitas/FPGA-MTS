# v1ab 上板测试 SOP

## 0. 本文件作用

本文件给 `v1ab_passthrough_debug` 上板测试一个小白版流程。

它对应：

- `OUTPUT_MODE = 0`：测试 `IN1 -> OUT1`；
- `OUTPUT_MODE = 1`：测试 `IN2 -> OUT1`。

## 1. 我需要理解什么

`v1ab` 不是 mixer，不是 MTS error。

它只是调试输入路径：

```text
IN1 -> adc_dat[0] -> pd_i -> error_o -> OUT1
IN2 -> adc_dat[1] -> ref_i -> error_o -> OUT1
```

## 2. 我需要操作什么

### v1a：IN1 -> OUT1

配置：

```text
OUTPUT_MODE = 0
```

接线：

```text
信号发生器 OUT -> Red Pitaya IN1
Red Pitaya OUT1 -> 示波器 CH1
信号发生器 OUT -> 示波器 CH2
```

建议输入：

```text
1 kHz sine
100 mVpp
0 V offset
```

### v1b：IN2 -> OUT1

配置：

```text
OUTPUT_MODE = 1
```

接线：

```text
安全衰减后的 4.6 MHz REF -> Red Pitaya IN2
Red Pitaya OUT1 -> 示波器 CH1
安全衰减后的 4.6 MHz REF -> 示波器 CH2
```

安全提醒：

```text
禁止 6.32 Vpp REF 直接进 IN2。
```

## 3. 我需要发给 GPT 什么

上板前发：

```text
1. 当前 bitstream 对应 OUTPUT_MODE
2. 信号发生器频率、幅度、offset
3. 示波器截图
4. OUT1 幅度和 offset
5. 是否看到削顶
```

## 4. Codex 应该生成什么

上板前 Codex 应生成：

- `BOARD_TEST_v1ab_passthrough_debug.md`；
- `INTEGRATION_PLAN_v1ab_passthrough_debug.md`；
- REPORT；
- Vivado 添加文件和回退说明。

## 5. 成功标准是什么

v1a 成功：

- `OUT1` 看到和 `IN1` 同频波形；
- 幅度可不同；
- 可反相；
- 不顶死；
- 不严重削顶。

v1b 成功：

- `OUT1` 看到 4.6 MHz 同频波形；
- `IN2` 输入安全；
- 不顶死；
- 不严重削顶。

## 6. 失败怎么排查

| 现象 | 先查什么 |
|---|---|
| OUT1 没波形 | bitstream、`OUTPUT_MODE`、信号源、示波器触发 |
| OUT1 削顶 | 输入幅度太大、DAC 路径格式问题 |
| v1b 没 4.6 MHz | REF 是否真的接到 `IN2` |
| OUT2 有波形 | DAC A/B 可能接反 |

## 7. 不允许做什么

不允许：

- `OUT1` 直接接 `D2-125`；
- 接激光器反馈；
- 让 FPGA 驱动 EOM；
- 把 6.32 Vpp REF 直接接 `IN2`。

## 8. 我现在只需要记住什么

`v1ab` 只验证通路。

```text
看到 OUT1 有正确波形，就是胜利；不要急着锁激光。
```
