# V2_EXPERIMENT_SOP

本文档服务于 v2 FPGA PI/PID 替代 D2-125 阶段。

## 1. 上板前检查

上板前必须确认：

- `pi_controller.sv` testbench PASS；
- P-only 测试 PASS；
- I 项测试 PASS；
- anti-windup 测试 PASS；
- output limiter 测试 PASS；
- reset / enable / hold / reset_integrator 测试 PASS；
- v1 OUT1 error 输出路径仍可回退；
- GPT 已审查设计；
- Claude Code 已审查 RTL；
- 当前 bit/bin 对应的参数已记录。

## 2. bit/bin 烧录前检查

烧录前记录：

- 日期；
- git / 文件版本，如果可用；
- bit/bin 文件名；
- top 参数；
- `pid_ce` 更新频率；
- `kp_i`；
- `ki_i`；
- `output_limit_i`；
- `offset_i`；
- `enable_i` 默认值；
- `polarity_i` 默认值；
- OUT2 接线。

默认要求：

```text
enable_i = 0
kp_i = 0 或极小
ki_i = 0
output_limit_i = 很小
control_o = 0
```

## 3. OUT2 接示波器测试步骤

第一轮只允许：

```text
Red Pitaya OUT2 -> 示波器
```

不允许：

- OUT2 接激光器；
- OUT2 接 D2-125 输出端；
- OUT2 接任何未知输入；
- 闭环。

测试：

1. reset 后 OUT2 是否为 0；
2. `enable=0` 时 OUT2 是否为 0；
3. `enable=1, kp=0, ki=0` 时 OUT2 是否为 0；
4. 小 `kp` 时 OUT2 是否随 error 变化；
5. `polarity_i` 翻转后 OUT2 方向是否翻转；
6. `output_limit_i` 改小时 OUT2 是否被限制；
7. `hold_i` 时 OUT2 是否冻结或保持定义行为；
8. `reset_integrator_i` 后 I 项是否清零。

## 4. 不接激光时的测试步骤

使用函数发生器或仿真风格输入模拟 error：

- 低频正弦；
- 低频三角波；
- 阶跃；
- 固定正偏差；
- 固定负偏差。

观察：

- 输出方向；
- 输出限幅；
- 积分累加；
- windup；
- reset；
- enable；
- 随机跳变。

## 5. 接入实验链路前必须满足的条件

必须全部满足：

- OUT2 示波器测试通过；
- 无随机跳变；
- 无 reset 后异常输出；
- `enable=0` 安全；
- `output_limit_i` 有效；
- 初始 `kp/ki` 很小；
- `ki_i` 可先设为 0；
- `reset_integrator_i` 操作明确；
- 用户知道如何立即断开反馈；
- GPT 判断可以进入低增益测试。

## 6. 初始 Kp/Ki 要求

初始参数：

- 先 `P-only`；
- `ki_i=0`；
- `kp_i` 从极小值开始；
- P-only 输出方向确认后，再加入很小 `ki_i`；
- 每次只改一个参数；
- 每次记录示波器截图和参数。

## 7. enable 默认关闭

所有上板版本默认：

```text
enable_i = 0
```

操作顺序：

1. 烧录 bit/bin；
2. 确认 OUT2 为 0；
3. 确认示波器接线；
4. 确认 output limit；
5. reset integrator；
6. 设置极小 Kp/Ki；
7. 手动 enable；
8. 随时准备 disable。

## 8. reset_integrator 操作流程

使用场景：

- 每次 enable 前；
- 每次改变 `ki_i` 前；
- 输出饱和后；
- 误接极性导致发散后；
- 从 hold 恢复前。

流程：

```text
disable -> reset_integrator -> 检查 OUT2 -> 设置参数 -> enable
```

## 9. 异常处理

### 出现振荡

立即：

- disable；
- reset_integrator；
- 降低 `kp_i`；
- `ki_i` 设为 0；
- 检查 polarity；
- 回到 OUT2 示波器测试。

### 出现削顶

立即：

- disable；
- 降低 `output_limit_i`；
- 检查 offset；
- 检查 P/I sum；
- 检查是否 windup。

### 输出饱和

立即：

- disable；
- reset_integrator；
- 检查 anti-windup；
- 降低 `ki_i`；
- 降低 `kp_i`；
- 检查是否 error 输入 offset 过大。

### 疑似正反馈

立即：

- disable；
- 切换 `polarity_i`；
- 从 P-only 小增益重测；
- 不允许带 I 项直接重试。

## 10. 与 D2-125 对比

对比时记录：

- D2-125 是否能锁；
- FPGA PI 是否能锁；
- 锁定时间；
- 锁定持续时间；
- error RMS；
- control 输出是否饱和；
- 是否发散；
- 是否需要手动重置；
- 极性是否一致；
- 相同 error signal 下噪声是否变化。

对比原则：

- D2-125 是 v2 的基准；
- FPGA PI 第一版只要求安全可控，不要求立刻优于 D2-125；
- 若 FPGA PI 不稳定，回退 D2-125，不继续硬推。

