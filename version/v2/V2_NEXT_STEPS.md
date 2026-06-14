# V2_NEXT_STEPS

## 1. 当前状态

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

v2a-1 已经关闭：P-only RTL、首次仿真、Claude Code 集中审查、最终修正和 XSim 回归仿真全部完成。v2a-1 不再重复 GPT 或 Claude Code 审查。

v2a-2 已经完成 I 通道、integrator 和 anti-windup 的初次实现，并完成独立 XSim 回归。当前下一步不是继续扩大测试范围，也不是直接接主工程，而是等待 Claude Code 对 v2a-2 进行一次集中静态审查。

## 2. 最近一步

最近一步只做：

```text
Claude Code 对 v2a-2 做一次集中审查
```

审查结论只允许是：

- PASS
- PASS WITH NOTES
- FAIL

如果 PASS 或 PASS WITH NOTES，则 v2A 关闭，进入 v2B 系统集成准备。如果 FAIL，则 Codex 只做一次集中修正和回归仿真；通过后关闭 v2A，不再循环审查同一版本。

## 3. v2B 开始前必须回答的五个问题

进入 v2B 前，GPT 和用户必须明确：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

这些是物理接口问题，不是 RTL 算法问题。没有这些答案，就不能安全决定 OUT2 的限幅、offset、polarity 和 PI 更新速率。

## 4. v2B 的最小任务

v2B 的最小任务是系统接口和主工程集成：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2
```

同时必须保持：

```text
OUT1 -> error observation
```

OUT1 在 v2B-v2F 始终保留为 error observation。OUT2 第一阶段只接示波器，不接激光，不接 D2-125，不接任何真实反馈端。

## 5. 当前禁止事项

当前仍然禁止：

- 不修改 `laser_lock_core.sv`，除非另开 v2B 授权任务。
- 不修改 `red_pitaya_top.sv`。
- 不修改 `redpitaya.xpr`。
- 不运行 Vivado。
- 不生成 bitstream。
- 不上板。
- 不把 OUT2 接激光。
- 不开始 CNN。
- 不开始相位自动匹配。
- 不开始双 PID。

## 6. 下一主阶段

```text
下一主阶段：v2B 系统接口和主工程集成。
```

但 v2B 只能在 v2a-2 一次 Claude Code 集中审查完成，并且五个物理问题有答案之后开始。
