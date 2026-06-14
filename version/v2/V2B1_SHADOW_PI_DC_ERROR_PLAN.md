# V2B1_SHADOW_PI_DC_ERROR_PLAN

本文档定义当前真实接线下的下一阶段：`v2B1 Shadow PI DC Error 旁路测试`。本阶段只把已经完成的 v2A `pi_controller.sv` 第一次接入 Red Pitaya 主工程的输入/输出影子链路，不能理解为 FPGA 已经替代 D2-125。

## 1. 当前真实接线图

当前实验台真实接线如下：

```text
模拟 mixer 后 error
-> D2-125 Error Input
-> D2-125 Servo
-> Servo Output
-> 三通
   +-> 激光器电源
   +-> 激光器锁定控制端

D2-125 Aux Servo Output
-> 激光器电源 Scan

D2-125 Ramp
-> 示波器 CH1

D2-125 DC Error
-> 示波器 CH3
-> 后续 Red Pitaya IN1

Red Pitaya OUT2
-> 后续示波器 CH4
```

当前真正完成扫描、找谱线、缩小扫描范围和锁定任务的仍然是 D2-125。Red Pitaya 目前还没有用 OUT2 真实控制激光。

## 2. v2A 已完成内容

v2A / v2a-1 / v2a-2 已完成的是 FPGA 版 D2-125 Servo Core，而不是完整 D2-125 替代。

D2-125 中对应的功能段是：

```text
D2-125 Error Input
-> Servo PI/PID
-> Servo Output
```

FPGA 中对应为：

```text
error_i
-> pi_controller.sv
-> control_o
```

v2a-1 已完成 P-only。v2a-2 已完成 PI + integrator + anti-windup。`pi_controller.sv` 已完成独立 XSim，v2A2 仿真报告记录：

```text
tb_pi_controller summary: tests=165 pass=165 fail=0
```

这只证明 `pi_controller.sv` 独立 testbench 通过，不证明它已经进入主工程，不证明 OUT2 可用，不证明 FPGA 已替代 D2-125。

v2A 仍未完成：

```text
v2A 还没有接入 red_pitaya_top；
v2A 还没有接 OUT2；
v2A 还没有生成 bitstream；
v2A 还没有上板；
v2A 还没有控制激光。
```

## 3. D2-125 功能映射表

| D2-125 功能 | 当前由谁完成 | v2A 是否完成 | 后续 FPGA 替代阶段 |
|---|---|---|---|
| Error Input 接收误差 | D2-125 | 部分完成：`pi_controller` 有 `error_i`，但未接真实输入 | v2B1 |
| Servo PI/PID 计算 | D2-125 | 已完成 PI 核心 | v2A / v2B1 |
| Servo Output 输出控制 | D2-125 | 未完成，OUT2 未接入 | v2B1 / v2D / v2F |
| Ramp 扫描 | D2-125 Ramp / Aux | 未完成 | 后续 v3 |
| Aux Servo Output -> Scan | D2-125 | 未完成 | 后续 ramp / scan 替代 |
| Scan / Lock 切换 | D2-125 面板 Lock | 未完成 | 后续 FSM |
| 自动寻峰 / 重锁 | 人工 + D2-125 | 未完成 | 后续 v4/v5 |

## 4. v2B1 代码目标

下一步代码任务目标应写成：

```text
Red Pitaya IN1
-> sign / scale
-> pi_controller.sv
-> control_o
-> Red Pitaya OUT2
-> 示波器 CH4
```

第一版参数建议：

```text
Kp = 极小值
Ki = 0
output_limit = 极小安全值
polarity = 0
pid_ce = 1 kHz 或 10 kHz
```

说明：

```text
第一版只做 P-only Shadow PI；
Ki=0 是为了避免积分导致输出慢慢顶死；
OUT2 只接示波器；
D2-125 继续真实锁定。
```

v2B1 不是重新写 PI。v2B1 是把已经完成的 v2A `pi_controller` 第一次接入主工程输入输出链路。

## 5. v2B1 实验测试 SOP

### 实验前

```text
1. 保持 D2-125 原锁定链路不变；
2. 确认 D2-125 可以正常扫到谱线并锁定；
3. 确认示波器 CH1 = D2-125 Ramp；
4. 确认示波器 CH3 = D2-125 DC Error；
5. Red Pitaya OUT2 暂时不接任何激光器输入。
```

### 上板第一轮

```text
1. 烧录 v2B1 bitstream；
2. Red Pitaya IN1 接 D2-125 DC Error Monitor；
3. Red Pitaya OUT2 接示波器 CH4；
4. D2-125 继续锁定激光；
5. 观察 CH3 和 CH4 的关系。
```

### 示波器观察

```text
CH1：D2-125 Ramp
CH3：D2-125 DC Error
CH4：FPGA OUT2 control
```

判断标准：

```text
1. CH3 接近 0 时，CH4 应接近 0 或小范围变化；
2. CH3 正负变化时，CH4 应有对应方向变化；
3. CH4 不能随机跳变；
4. CH4 不能长时间饱和；
5. CH4 不能超过 output_limit；
6. Ki=0 时，CH4 不应出现积分式慢慢爬升。
```

异常处理：

```text
CH4 方向反了：下一版切换 polarity；
CH4 太大：减小 Kp 或 output_limit；
CH4 没反应：检查 IN1 输入、ADC 路由、OUT2 路由；
CH4 饱和：减小 Kp，并检查 DC Error offset；
CH4 噪声过大：降低 Kp，确认 DC Error 幅度和接地。
```

## 6. 本阶段禁止事项

```text
不重新写 pi_controller.sv；
不继续优化 v2A；
不替代 D2-125 Ramp；
不替代 D2-125 Aux Servo Output；
不替代 D2-125 Servo Output；
不让 OUT2 接激光；
不让 OUT2 与 D2-125 Servo Output 并联；
不做 scan/lock 状态机；
不做上位机 GUI；
不做 AI；
不做自动锁定；
不直接声称 FPGA 已锁定激光。
```

## 7. 下一条代码任务标题草案

```text
v2B1 Shadow PI DC Error to OUT2 RTL Integration
```

本标题只是下一步任务草案。本文档任务不执行该代码任务。
