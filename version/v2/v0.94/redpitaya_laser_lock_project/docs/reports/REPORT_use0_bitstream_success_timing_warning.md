# REPORT USE_LASER_LOCK_CORE=0 bitstream success with timing warning

## 0. 本报告作用

本报告记录当前 bitstream 排查进展：官方干净工程可以生成 bitstream，当前开发工程在 `USE_LASER_LOCK_CORE=0` 时也可以生成 bitstream，但存在 timing critical warning。

本报告只记录现象和下一步判断，不修改 RTL，不运行 Vivado。

## 1. 官方干净工程结果

官方干净工程可以 `Generate Bitstream` 成功：

```text
E:\new\fpga_lock\v94\guanfang-v0.94\v0.94
```

这说明官方 baseline 本身可以通过 bitstream 生成。

## 2. 当前开发工程 USE_LASER_LOCK_CORE=0 结果

当前开发工程在以下设置时也可以 `Generate Bitstream` 成功：

```text
USE_LASER_LOCK_CORE = 0
```

当前开发工程路径：

```text
E:\new\fpga_lock\v94\v0.94
```

这说明当前开发工程的官方回退路径可以完成 bitstream。

## 3. 当前 timing critical warning

当前 bitstream 虽然成功，但出现 timing critical warning：

```text
WNS = -0.005 ns
failing endpoint = 1
```

主要路径集中在：

```text
pll_dac_clk_1x / DAC ODDR 附近
```

当前判断：

- 这是非常接近 0 的 timing violation；
- 需要记录，但不是本报告中最优先的功能性阻塞点；
- 后续如果修改 DAC mux 接入方案，应继续观察该 timing warning 是否变化。

## 4. USE_LASER_LOCK_CORE=0 的含义

`USE_LASER_LOCK_CORE=0` 只是官方回退路径。

它表示 DAC A/B 仍然走官方原始路径：

```text
dac_a_sum = asg_dat[0] + pid_dat[0]
dac_b_sum = asg_dat[1] + pid_dat[1]
```

因此，这个 bitstream 不是 `v1ab IN1 -> OUT1` 测试 bit。

不能用 `USE_LASER_LOCK_CORE=0` 的 bitstream 去验证：

```text
IN1 -> laser_lock_core -> OUT1
```

它只能说明官方回退路径和当前工程基本 bitstream 流程可走通。

## 5. 对 USE_LASER_LOCK_CORE=1 失败的判断

之前 `USE_LASER_LOCK_CORE=1` 时失败，而 `USE_LASER_LOCK_CORE=0` 时可以 bitstream 成功。

因此当前优先怀疑：

```text
laser_error 接入 DAC A/B 求和路径的 mux 方案
```

也就是重点检查：

```text
dac_a_sum / dac_b_sum mux
laser_error 到 dac_a_sum 的符号扩展和组合路径
laser_control 或 dac_b_sum 的处理方式
```

当前不优先怀疑：

```text
v1c mixer
LPF
BPF
AI
```

因为这些还没有进入当前问题。

## 6. 下一步建议

下一步不是上板。

下一步应该是修正：

```text
USE_LASER_LOCK_CORE=1 的 DAC mux 接入方案
```

建议先生成修正计划，说明：

- 当前 mux 接入点；
- 为什么 `USE_LASER_LOCK_CORE=0` 可以过；
- 为什么 `USE_LASER_LOCK_CORE=1` 可能触发失败；
- 是否需要在 DAC mux 前增加寄存器；
- 是否需要保持 `dac_a_sum / dac_b_sum` 的官方时序风格；
- 如何回退。

在修正方案确认前，不要继续扩大功能。

## 7. 明确禁止

当前明确禁止：

- 不要开始 `v1c mixer`；
- 不要接板子；
- 不要接 `D2-125`。

补充说明：

- 当前 `USE_LASER_LOCK_CORE=0` 成功 bitstream 不是 v1ab 测试 bit；
- 不能用它进行 `IN1 -> OUT1` 上板测试；
- 必须先解决 `USE_LASER_LOCK_CORE=1` 的 DAC mux 接入问题。
