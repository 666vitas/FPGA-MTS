# V2_DEVELOPMENT_ROADMAP

本文档给出 v2 的主阶段路线。v2a-1 和 v2a-2 只是 v2A 的内部子阶段，不再作为整个 v2 的主体叙述。

## 1. 总原则

v2 按“先算法零件、再系统集成、再 Vivado、再示波器、再真实闭环”的顺序推进。

```text
v2A 独立 PI 核心
-> v2B 系统接口和主工程集成
-> v2C Vivado 综合、实现、时序、DRC 和 bitstream
-> v2D OUT2 示波器空载上板测试
-> v2E 真实 MTS error 输入、OUT2 开环观察
-> v2F 低增益闭环替代 D2-125
-> v2G FPGA PI 与 D2-125 性能对比
```

## 2. v2A：独立数字 PI 核心

目标：先在独立 testbench 里证明 PI 算法零件安全、可算、可审查。

内部子阶段：

- v2a-1：P-only。
- v2a-2：I + anti-windup。

输入：人工构造的 error、kp、ki、offset、limit、enable、hold、polarity。

输出：仿真中的 `control_o`、`p_term_o`、`i_term_o`、`sat_o`。

工具：独立 XSim。v2A 不运行 Vivado 主工程，不生成 bitstream，不上板。

当前状态：

```text
v2A 的 PI 核心初次实现完成；
v2a-2 等待一次 Claude Code 集中审查；
下一主阶段为 v2B 系统集成。
```

## 3. v2B：系统接口和主工程集成

目标：把 v2A 的 PI core 接到 v1 已验证的 `mixer + LPF` 后面，形成：

```text
PD -> ADC -> mixer -> LPF -> pi_controller -> OUT2
```

必须保留：

- OUT1 始终保留为 error observation。
- OUT2 第一阶段只接示波器。
- enable 默认关闭。
- output limit 默认保守。
- v1 的 OUT1 路径不能被破坏。

v2B 开始前必须回答五个物理问题：

1. OUT2 接激光的哪个控制端。
2. 该端允许的电压范围。
3. 控制极性。
4. 执行器响应带宽。
5. 初始 `pid_ce` 频率。

## 4. v2C：Vivado 编译和 bitstream

目标：确认完整主工程能综合、实现、通过关键 DRC/timing，并生成来源明确的 bitstream。

工具：Vivado Synthesis、Implementation、DRC、Timing、Generate Bitstream。

通过标准：0 fatal error；关键 warning 可解释；bitstream 对应的源码和文档版本可追踪。

不能声称：v2C 通过不等于 OUT2 硬件安全，也不等于可以接激光。

## 5. v2D：OUT2 示波器空载上板测试

目标：OUT2 只接示波器，验证硬件输出安全。

示波器要看：

- reset 后 OUT2 是否为安全值。
- enable=0 时 OUT2 是否安全。
- enable=1 后 OUT2 是否按预期变化。
- hold 是否冻结输出。
- output limit 是否真的限幅。
- OUT1 是否仍然是 error observation。

通过标准：OUT2 无异常跳变、无不可解释 offset、无超限；OUT1 路径不受影响。

不能声称：v2D 通过不等于已闭环，不等于已替代 D2-125。

## 6. v2E：真实 MTS error 输入、OUT2 开环观察

目标：让 PI 看到真实 MTS error-like signal，但 OUT2 仍只接示波器。

示波器要看：

- OUT1 上的真实 error-like signal。
- OUT2 是否随 error 方向合理变化。
- OUT2 是否噪声过大、是否频繁饱和。
- 改变 polarity 后方向是否符合预期。

通过标准：OUT2 对真实 error 的幅度、方向、限幅和噪声都可解释。

不能声称：v2E 通过仍不代表激光已经由 FPGA 锁住。

## 7. v2F：低增益闭环替代 D2-125

目标：在低 Kp、低 Ki、小 output limit、明确执行器安全范围的条件下，让 OUT2 接入一个真实激光控制端，短时间替代 D2-125 的基础 servo 功能。

通过标准：

- error 没有发散。
- OUT2 没有长期打满。
- 激光没有被拉飞。
- 能快速回退到 D2-125。
- 锁定现象可重复。

不能声称：v2F 初通不等于性能优于 D2-125，也不等于完成双执行器控制。

## 8. v2G：FPGA PI 与 D2-125 性能对比

目标：用统一指标比较 D2-125 和 FPGA PI。

比较内容：

- error RMS。
- 锁定保持时间。
- 饱和次数。
- 恢复能力。
- 噪声。
- 参数敏感性。

通过标准：有重复实验、有同一条件下的对比数据，而不是只凭一次示波器截图。

## 9. 后续版本边界

- v3：scan/lock control、自动寻峰、自动重锁 FSM。
- v4：IQ 解调、相位优化、相位自动匹配。
- v5：上位机 AI 识峰、CNN peak recognition、参数建议。
- 后续版本：双 DAC、PZT + current 双执行器控制。

这些内容不进入当前 v2A 文档闭环，也不作为 v2a-2 的阻塞项。
