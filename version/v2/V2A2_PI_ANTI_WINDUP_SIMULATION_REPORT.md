# V2A2 PI + Anti-Windup 独立 XSim 仿真报告

本文档记录 v2a-2 的初次实现结果：在 v2a-1 P-only 已关闭的基础上，加入 I 通道、积分器限幅和条件 anti-windup，并完成独立 XSim 回归仿真。

## 1. 阶段目标

v2a-2 的目标是实现独立 `pi_controller.sv` 的 PI 控制骨架：

```text
error_i
-> signed 扩位
-> polarity
-> P 通道
-> I 通道
-> P + I + offset
-> output limiter
-> control_o
```

本阶段仍不接顶层、不接 OUT2、不接 D2-125、不接激光、不生成 bitstream。

## 2. 修改文件

```text
E:\new\fpga_lock\v94\v0.94\rtl\pi_controller.sv
E:\new\fpga_lock\v94\v0.94\sim\tb_pi_controller.sv
```

未修改：

```text
laser_lock_core.sv
red_pitaya_top.sv
mixer_core.sv
lpf_core.sv
output_protect.sv
redpitaya.xpr
```

## 3. I 通道架构

I 通道计算：

```text
selected_error = polarity_i ? -sign_extend(error_i) : sign_extend(error_i)
i_product      = selected_error * ki_i
i_delta        = i_product >>> KI_SHIFT
integrator     = clamp_or_freeze(integrator + i_delta)
i_term_o       = integrator
```

积分器使用：

```text
logic signed [ACC_WIDTH-1:0] integrator_q
```

当前参数：

```text
ERROR_WIDTH = 14
GAIN_WIDTH  = 16
OUT_WIDTH   = 14
ACC_WIDTH   = 48
KP_SHIFT    = 12
KI_SHIFT    = 12
```

testbench 使用：

```text
KP_SHIFT = 4
KI_SHIFT = 4
```

因此测试中：

```text
Ki_real_per_pid_ce ~= ki_i / 2^KI_SHIFT
```

注意：这是每个 `pid_ce_i` 更新周期的离散积分增量，不等同于连续时间控制理论中的物理 Ki。真实物理 Ki 还取决于 `pid_ce_i` 更新频率。

## 4. Anti-Windup 算法

本次采用方案 A+B：

```text
积分器内部限幅
+
输出饱和方向条件冻结
```

积分器内部限幅：

```text
-output_limit_i <= integrator_q <= +output_limit_i
```

并且最大有效范围仍限制在：

```text
-8191 ... +8191
```

条件冻结规则：

```text
如果 P + 当前 I + offset 已达到正限幅，并且 i_delta > 0，则冻结积分器；
如果 P + 当前 I + offset 已达到负限幅，并且 i_delta < 0，则冻结积分器；
如果 i_delta 方向有助于退出饱和，则允许积分器更新。
```

判断方向使用 `i_delta` 的符号，而不是只看 `error_i`，因为 `ki_i` 可以为负数。

`sat_o` 仍只表示最终 `control_o` 是否被 output limiter 限幅，不表示积分器是否被冻结或钳制。

## 5. 控制优先级

时序优先级为：

```text
1. !rstn_i
2. !enable_i
3. reset_integrator_i
4. hold_i
5. pid_ce_i
6. 保持状态
```

行为：

- `rstn_i=0`：积分器、输出和 debug 全部清零；
- `enable_i=0`：积分器、输出和 debug 全部清零；
- `reset_integrator_i=1`：清积分器和 `i_term_o`，但 P + offset 仍正常计算；
- `hold_i=1`：保持积分器、输出和 debug；
- `pid_ce_i=0`：不更新 P、I 或输出状态；
- 不创建新时钟，`pid_ce_i` 只是 clock enable。

## 6. 新增测试

在保留 v2a-1 原有 104 项 P-only 回归测试基础上，新增 61 项 I / PI / anti-windup 检查，覆盖：

- I-only 正向累加；
- I-only 负向累加；
- 负 Ki；
- polarity 影响 I 通道方向；
- `pid_ce_i=0` 不更新积分器；
- hold 冻结积分器和输出；
- `reset_integrator_i` 清积分但保留 P + offset；
- disable 清积分，重新 enable 不恢复旧积分；
- PI 组合手工固定点；
- 正积分限幅；
- 负积分限幅；
- 正饱和冻结；
- 负饱和冻结；
- 正饱和恢复；
- 负饱和恢复；
- `output_limit_i` 动态减小；
- `output_limit_i=0`；
- 1000 次正向长时间积分；
- 1000 次负向长时间积分；
- `reset_integrator_i` 优先于 hold。

## 7. 独立 XSim 结果

工作目录：

```text
E:\new\fpga_lock\v94\v0.94
```

只编译：

```text
rtl/pi_controller.sv
sim/tb_pi_controller.sv
```

运行命令：

```tcl
xvlog -sv rtl/pi_controller.sv sim/tb_pi_controller.sv
xelab tb_pi_controller -s tb_pi_controller_sim
xsim tb_pi_controller_sim -runall
```

日志文件：

```text
E:\new\fpga_lock\v94\v0.94\xvlog.log
E:\new\fpga_lock\v94\v0.94\xelab.log
E:\new\fpga_lock\v94\v0.94\xsim.log
```

结果：

| 阶段 | Error | Warning | 结果 |
|---|---:|---:|---|
| xvlog | 0 | 0 | PASS |
| xelab | 0 | 0 | PASS |
| xsim | 0 | 0 | PASS |

最终 testbench 汇总：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

## 8. 回归结果

```text
原有 104 项 P-only 测试：PASS
新增 I/PI/anti-windup 测试：61 PASS
总测试：165
PASS：165
FAIL：0
```

## 9. 修复轮次

本次在允许的 3 轮内完成。

第 1 轮：

- xvlog：PASS；
- xelab：PASS；
- xsim：153 PASS / 12 FAIL；
- 原因：anti-windup 中 `i_delta` 与零比较不够明确，负向冻结/恢复未触发；旧 P-only hold 回归受 testbench 残留控制信号影响。

第 2 轮：

- xvlog：PASS；
- xelab：PASS；
- xsim：162 PASS / 3 FAIL；
- 原因：旧 P-only `drive_raw` helper 未清理 `reset_integrator_i` / `ki_i`。

第 3 轮：

- xvlog：PASS；
- xelab：PASS；
- xsim：165 PASS / 0 FAIL。

## 10. 尚未完成事项

本次通过不表示：

- v2a-2 已经 CLOSED；
- Claude Code 审查已完成；
- Vivado 主工程集成已完成；
- 综合 / 实现 / bitstream 已完成；
- OUT2 可用；
- FPGA 已替代 D2-125；
- 可以上板；
- 可以接激光。

## 11. 当前结论

```text
v2a-2初次实现通过，等待Claude Code一次集中审查
```

下一步只能进入一次 Claude Code 集中审查，不重复循环审查。
