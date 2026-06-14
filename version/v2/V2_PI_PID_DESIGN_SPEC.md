# V2_PI_PID_DESIGN_SPEC

本文档服务于 v2 FPGA PI/PID 替代 D2-125 阶段。

## 1. 第一版控制器选择

v2 第一版建议只做 PI，不直接做完整 PID。

原因：

- P 项负责误差的即时响应；
- I 项负责消除静态误差；
- D 项容易放大 MTS error signal 噪声；
- 当前目标是安全替代 D2-125 的基本 servo 功能，不是一次性完成复杂控制器；
- PI 参数更少，便于用户、GPT、Codex、Claude Code 分工审查；
- 后续如果 PI 已稳定，再决定是否加入 D 或更复杂补偿。

## 2. 推荐模块定位

建议模块名：

```text
pi_controller.sv
```

推荐数据流：

```text
error_i
  -> polarity select
  -> P term
  -> I integrator
  -> sum + offset
  -> output saturation
  -> control_o
```

`control_o` 第一阶段接 `DAC OUT2`，只接示波器。

## 3. 建议接口

建议第一版接口包含：

```systemverilog
input  logic              clk_i;
input  logic              rst_i;
input  logic              pid_ce_i;
input  logic              enable_i;
input  logic              hold_i;
input  logic              reset_integrator_i;
input  logic              polarity_i;
input  logic signed [13:0] error_i;
input  logic signed [15:0] kp_i;
input  logic signed [15:0] ki_i;
input  logic signed [13:0] offset_i;
input  logic        [13:0] output_limit_i;
output logic signed [13:0] control_o;
output logic signed [31:0] p_term_o;
output logic signed [31:0] i_term_o;
output logic              sat_o;
```

说明：

- `pid_ce_i` 决定控制器更新频率；
- `enable_i=0` 时输出安全值，建议 `control_o=14'sd0`；
- `hold_i=1` 时冻结积分器和输出，便于实验暂停；
- `reset_integrator_i=1` 时清零积分器；
- `polarity_i` 用于切换反馈极性，避免正反馈；
- `output_limit_i` 保护 DAC 输出范围；
- debug 输出可在最终资源压力大时关闭，但第一版建议保留。

## 4. P 通道设计

P 通道：

```text
p_term = error_signed * kp_i
```

建议：

- `error_i` 为 signed 14-bit；
- `kp_i` 为 signed 16-bit；
- 乘法结果至少 signed 30-bit；
- P 输出进入求和前统一右移缩放；
- 右移位数不要写死在文档里，建议 RTL 参数化，例如 `KP_SHIFT`。

P-only 测试必须先通过：

- 正 error 输出方向正确；
- 负 error 输出方向正确；
- `polarity_i` 翻转后方向反转；
- 大 error 不 wrap-around；
- 输出受 `output_limit_i` 保护。

## 5. I 通道设计

I 通道：

```text
i_step = error_signed * ki_i
integrator_next = integrator + i_step_scaled
i_term = integrator_limited
```

建议：

- `ki_i` 为 signed 16-bit；
- `i_step` 至少 signed 30-bit；
- integrator 至少 signed 40-bit，建议 40-48 bit；
- `KI_SHIFT` 参数化；
- integrator 输出到 DAC 前再右移到控制量尺度；
- 必须有限幅，不能无限累加。

## 6. 为什么暂时不做 D 通道

D 通道需要对误差做差分：

```text
d_term = error[n] - error[n-1]
```

当前暂不做 D，因为：

- MTS error-like signal 仍有噪声；
- 差分会放大高频噪声；
- 第一版安全目标高于动态性能；
- PI 已足够验证替代 D2-125 的最小 servo 功能；
- D 通道会增加参数维度和调试风险。

## 7. PID 更新频率建议

FPGA 主时钟为 `125 MHz`。PI 不建议每个时钟都更新积分器。

建议用 `pid_ce_i` 降采样更新：

| `pid_ce` 目标更新率 | 说明 |
|---:|---|
| `1 kHz` | 最安全，适合最早期仿真和函数发生器模拟 error |
| `5 kHz` | 可用于观察更快响应，但仍较保守 |
| `10 kHz` | 可作为 v2b/v2c 候选上限 |
| `>10 kHz` | 暂不建议第一轮直接使用，需 GPT 审查和实验确认 |

更新频率必须和 MTS error 带宽、激光执行器响应、DAC 输出噪声和稳定性一起审查。

## 8. fixed-point 缩放策略

建议所有缩放显式参数化：

```text
P_OUT = (error_i * kp_i) >>> KP_SHIFT
I_STEP = (error_i * ki_i) >>> KI_SHIFT
CONTROL_PRE = P_OUT + I_OUT + offset_i
```

要求：

- 不允许无保护截断；
- 所有右移使用算术右移；
- 所有输出到 14-bit DAC 前必须 saturation；
- 仿真中必须覆盖最大正、最大负、接近 0、小信号、大信号。

## 9. anti-windup

第一版至少采用一种 anti-windup：

方案 A：积分器限幅。

```text
integrator <= clamp(integrator_next, -I_LIMIT, +I_LIMIT)
```

方案 B：输出饱和时冻结积分。

```text
if output_saturated and error pushes further into saturation:
    freeze integrator
else:
    update integrator
```

建议第一版先做方案 A，必要时叠加方案 B。

## 10. output saturation

输出限幅必须位于 DAC 输出之前：

```text
control_o = clamp(control_pre, -output_limit_i, +output_limit_i)
```

`output_limit_i` 第一轮必须设置得很小。不要默认满量程 ±8191。

## 11. DAC ±1 V 安全约束

Red Pitaya fast DAC 通常按约 ±1 V 理解，但具体 OUT2 幅度、offset 和负载下行为必须实测。

v2 第一版要求：

- 上电默认输出 0；
- `enable_i=0` 输出 0；
- reset 输出 0；
- `output_limit_i` 默认小范围；
- OUT2 先接示波器；
- 未经 GPT 和用户确认，不接激光控制输入。

## 12. 防止一烧录就打飞激光的安全机制

必须具备：

- 默认 `enable_i=0`；
- 默认 `control_o=0`；
- reset 清零 integrator；
- `output_limit_i` 不允许默认为满量程；
- `polarity_i` 可切换；
- `hold_i` 可冻结输出；
- `reset_integrator_i` 可随时清积分；
- OUT2 上板初测只接示波器；
- v1 OUT1 error 输出路径保留，便于回退 D2-125。

