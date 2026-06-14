# V2_CODE_REVIEW_CHECKLIST

本文档服务于 v2 FPGA PI/PID 替代 D2-125 阶段。

## 1. `pi_controller.sv` 代码审查清单

每次修改 `pi_controller.sv` 必须检查：

| 项目 | 检查点 |
|---|---|
| signed / unsigned | `error_i`、`kp_i`、`ki_i`、乘法结果、integrator、sum 是否全部按 signed 处理 |
| 位宽 | P 乘法、I 乘法、integrator、输出求和是否留足保护位 |
| 缩放 | `KP_SHIFT`、`KI_SHIFT` 是否明确，右移是否为算术右移 |
| saturation | 输出到 14-bit DAC 前是否限幅，不允许 wrap-around |
| reset | reset 后 integrator 清零，control 输出安全值 |
| enable | `enable=0` 时输出安全值，积分器不继续跑飞 |
| hold | `hold=1` 时行为明确，不能半冻结半更新 |
| reset_integrator | 可以独立清零积分器，不影响全局 reset |
| polarity | 极性翻转是否只影响 error 方向，不破坏限幅逻辑 |
| anti-windup | 积分限幅或饱和冻结是否有效 |
| output_limit | 正负限幅是否对称，limit=0 时输出是否为 0 |
| debug | `p_term_o`、`i_term_o`、`sat_o` 是否真实反映内部状态 |

## 2. fixed-point 位宽检查

必须回答：

1. `error_i` 是多少位 signed？
2. `kp_i/ki_i` 是多少位 signed？
3. P 乘法结果多少位？
4. I 乘法结果多少位？
5. integrator 多少位？
6. integrator limit 多少？
7. sum before saturation 多少位？
8. 到 `control_o[13:0]` 前是否经过 saturation？
9. 是否存在无保护截断？
10. 是否存在 signed 右移被写成 logical shift 的风险？

## 3. reset / enable 行为检查

必须仿真确认：

- 上电 reset 后 `control_o=0`；
- reset 后 integrator 为 0；
- `enable=0` 时 `control_o=0`；
- `enable=0` 时 integrator 不继续累加；
- 从 `enable=0` 切回 `enable=1` 不出现随机跳变；
- `reset_integrator_i` 可在运行中清零积分器；
- `hold_i` 行为可解释。

## 4. anti-windup 检查

必须覆盖：

- 长时间正误差；
- 长时间负误差；
- 输出达到正限幅；
- 输出达到负限幅；
- 误差反向后能从饱和恢复；
- reset_integrator 后立即解除 windup；
- `output_limit_i` 改小后不会出现内部积分不可控。

## 5. output limiter 检查

必须覆盖：

- `output_limit_i = 0`；
- 很小 limit；
- 中等 limit；
- 接近满量程 limit；
- 正向大误差；
- 负向大误差；
- offset 加入后仍不越界；
- P/I 相加后仍被限幅。

## 6. testbench 覆盖清单

testbench 至少覆盖：

- 零误差；
- 正误差；
- 负误差；
- 正负误差切换；
- 小误差；
- 大误差；
- P-only；
- I-only；
- PI 同时启用；
- 饱和；
- reset；
- enable；
- hold；
- reset_integrator；
- polarity；
- output_limit；
- offset；
- 长时间运行积分稳定性。

## 7. 接入工程前检查

接入 `laser_lock_core.sv` 前必须确认：

- v1 `mixer_core + lpf_core -> OUT1` 可回退；
- 不误改 ADC IO；
- 不误改 DAC ODDR / DAC IO；
- 不误改 PLL / BUFG；
- 不误改 PS / AXI / DDR；
- 不误改 XDC / SDC；
- OUT2 路径明确；
- OUT2 默认安全；
- 顶层参数默认不启用闭环。

## 8. 禁止通过条件

出现以下任一情况，不允许进入上板：

- reset 后输出非零且不可解释；
- `enable=0` 仍有控制输出；
- integrator 可无限增长；
- 输出 wrap-around；
- `output_limit_i` 无效；
- testbench 未覆盖负误差；
- testbench 未覆盖饱和；
- 破坏 v1 OUT1 回退路径。

