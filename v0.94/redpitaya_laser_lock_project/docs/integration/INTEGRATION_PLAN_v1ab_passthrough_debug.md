# INTEGRATION_PLAN_v1ab_passthrough_debug

## 0. 本文件作用

本文件只规划如何把已经通过仿真的 `laser_lock_core` 接入 Red Pitaya 官方 top。

本文件不直接修改：

```text
rtl\red_pitaya_top.sv
Vivado 工程
官方 rtl/project/sim/ip/sdc
```

大白话解释：`laser_lock_core` 现在像一个已经在桌面上测试过的小电路模块，但它还没有接到 Red Pitaya 的 ADC 输入和 DAC 输出。本文件就是接线方案，告诉后面真正改 top 时应该怎么接、哪些地方不能碰、怎么回退。

## 1. 当前已有成果

当前已经完成：

| 成果 | 文件 | 状态 |
|---|---|---|
| `laser_lock_core.sv` | `redpitaya_laser_lock_project\rtl\laser_lock_core.sv` | 已生成 |
| `output_protect.sv` | `redpitaya_laser_lock_project\rtl\output_protect.sv` | 已生成 |
| `tb_laser_lock_core_v1ab.sv` | `redpitaya_laser_lock_project\sim\tb_laser_lock_core_v1ab.sv` | 已通过仿真 |
| 上板测试说明 | `redpitaya_laser_lock_project\docs\board_tests\BOARD_TEST_v1ab_passthrough_debug.md` | 已生成 |
| 任务报告 | `redpitaya_laser_lock_project\docs\reports\REPORT_v1ab_passthrough_debug.md` | 已生成 |

仿真成功标志：

```text
V1AB PASSTHROUGH DEBUG TEST PASSED
```

但是当前还不能上板。

原因是：`laser_lock_core` 目前只是项目目录里的自定义 RTL，还没有接入官方 `red_pitaya_top.sv`。也就是说，Red Pitaya 的 `adc_dat[0]`、`adc_dat[1]` 还没有真正送进 `pd_i/ref_i`，`error_o` 也还没有真正接到 DAC A / OUT1 路径。

## 2. v1ab 集成目标

目标接线如下：

```text
clk_i  <- adc_clk
rstn_i <- adc_rstn
pd_i   <- adc_dat[0]
ref_i  <- adc_dat[1]

error_o   -> DAC A saturation 前候选路径
control_o -> 第一阶段保持 0，不输出有效控制量
```

新手解释：

- `adc_clk` 是 ADC 数据所在的时钟；
- `adc_rstn` 是 ADC 相关逻辑的 active-low reset；
- `adc_dat[0]` 是 `IN1` 的 ADC 数据候选，用来验证 `PD -> IN1 -> OUT1`；
- `adc_dat[1]` 是 `IN2` 的 ADC 数据候选，用来验证 `REF -> IN2 -> OUT1`；
- `error_o` 是要送到 `OUT1` 的调试输出；
- `control_o` 第一阶段固定为 0，不希望 `OUT2` 输出未知控制量。

## 3. 需要在 top 中新增哪些信号

后续真正修改 top 时，建议新增以下信号：

| 信号名 | 位宽 | signed/unsigned | 来源 | 去向 | 作用 |
|---|---:|---|---|---|---|
| `laser_error` | 14 bit | signed | `laser_lock_core.error_o` | DAC A saturation 前候选路径 | 作为 `OUT1` 调试输出 |
| `laser_control` | 14 bit | signed | `laser_lock_core.control_o` | DAC B saturation 前候选路径或固定 0 | 第一阶段保持 0，避免 `OUT2` 乱输出 |

概念声明：

```systemverilog
logic signed [13:0] laser_error;
logic signed [13:0] laser_control;
```

注意：这只是概念代码片段，不代表本文件已经修改官方 top。

## 4. laser_lock_core 如何实例化

后续在 top 中的概念实例化如下：

```systemverilog
localparam int LASER_LOCK_OUTPUT_MODE = 0; // 0: pd_i -> error_o, 1: ref_i -> error_o

laser_lock_core #(
    .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)
) i_laser_lock_core (
    .clk_i    (adc_clk),
    .rstn_i   (adc_rstn),
    .pd_i     (adc_dat[0]),
    .ref_i    (adc_dat[1]),
    .error_o  (laser_error),
    .control_o(laser_control)
);
```

`OUTPUT_MODE` 的含义：

| `OUTPUT_MODE` | 用途 | 上板目标 |
|---:|---|---|
| 0 | `error_o = pd_i` | v1a：验证 `IN1 -> OUT1` |
| 1 | `error_o = ref_i` | v1b：验证 `IN2 -> OUT1`，特别是 4.6 MHz `REF` 输入 |

重要说明：

- `OUTPUT_MODE=0` 和 `OUTPUT_MODE=1` 是编译时参数；
- 如果用参数方式切换模式，两个模式需要分别生成 bitstream；
- 每次修改 `OUTPUT_MODE` 后，都需要重新 `Run Synthesis`、`Run Implementation`、`Generate Bitstream`；
- 第一阶段不要为了省事加入 PS/AXI 动态参数控制。

## 5. DAC A 路径如何接入

根据 L03 DAC 路径学习结论，必须遵守：

```text
不要直接驱动 dac_dat_o。
不要修改 ODDR。
不要修改 dac_wrt_o、dac_sel_o、dac_clk_o、dac_rst_o。
```

`error_o` 应接在 DAC A saturation 前，也就是 `dac_a_sum` 附近。

建议加入一个回退开关：

```systemverilog
localparam logic USE_LASER_LOCK_CORE = 1'b1;
```

### 5.1 官方路径

当：

```text
USE_LASER_LOCK_CORE = 0
```

保持官方路径：

```systemverilog
dac_a_sum = asg_dat[0] + pid_dat[0];
dac_b_sum = asg_dat[1] + pid_dat[1];
```

### 5.2 laser_lock_core 路径

当：

```text
USE_LASER_LOCK_CORE = 1
```

使用：

```systemverilog
dac_a_sum = {laser_error[13], laser_error};
dac_b_sum = 15'sd0;
```

这里的：

```systemverilog
{laser_error[13], laser_error}
```

意思是把 14-bit signed 的 `laser_error` 符号扩展成 15-bit signed，送到原本 `dac_a_sum` 的位置。

### 5.3 为什么 DAC B 第一阶段输出 0

第一阶段 `control_o` 固定为 0，不做 PID，不控制激光器。

所以建议：

```systemverilog
dac_b_sum = 15'sd0;
```

原因：

- 不希望 `OUT2` 输出未知控制量；
- 上板调试只看 `OUT1`；
- 如果 `OUT2` 有明显波形，可以帮助判断 DAC A/B 是否接反；
- 后续 PID 阶段再认真启用 `control_o -> OUT2`。

## 6. 必须保留的官方逻辑

后续集成时必须保留：

| 官方逻辑 | 为什么不能改 |
|---|---|
| saturation | 防止 DAC 输出超范围 |
| signed-to-unsigned / negative-slope conversion | 官方 DAC 数据格式转换，和板级 DAC 极性有关 |
| DAC ODDR | 负责真正把 DAC 数据按硬件时序送出 FPGA |
| PLL | 产生 ADC/DAC 所需时钟 |
| BUFG | 官方时钟全局缓冲 |
| ADC IO | 负责把板级 ADC 数据变成 `adc_dat` |
| PS/AXI/DDR | 官方系统控制和处理器接口 |
| XDC | 板级管脚和时序约束 |

新手必须明白：我们要接入的是“算法输出到 DAC 求和前的位置”，不是重写 Red Pitaya 的底层硬件接口。

## 7. 两种集成策略比较

### 7.1 策略 A：复制官方 top 到 vendor_shell

路径：

```text
redpitaya_laser_lock_project\vendor_shell\red_pitaya_top_laser.sv
```

做法：把官方 `rtl\red_pitaya_top.sv` 复制到项目目录的 `vendor_shell`，先在副本中实验接线。

优点：

- 官方原始 top 完全不动；
- 对新手更安全；
- 便于反复试验和做注释；
- 出错不会污染官方工程。

缺点：

- 后续要让 Vivado 使用这个副本，需要额外配置；
- 如果官方 top 后续有变化，需要手动同步；
- 可能出现“副本能看懂，但 Vivado 工程实际仍用官方 top”的混淆。

### 7.2 策略 B：生成 patch，后续手动应用到官方 red_pitaya_top.sv

做法：Codex 生成 patch 或详细 diff，用户审查后手动应用到官方 `rtl\red_pitaya_top.sv`。

优点：

- 更接近最终 Vivado 工程；
- 不容易出现“副本没有被 Vivado 使用”的问题；
- 后续综合实现路径更直接。

缺点：

- 风险更高；
- 新手容易误改官方工程；
- 回退需要非常清楚；
- patch 必须经过 GPT 和用户审查。

### 7.3 比较表

| 项目 | 策略 A：vendor_shell 副本 | 策略 B：patch |
|---|---|---|
| 哪个更安全 | 更安全 | 风险较高 |
| 哪个更适合新手 | 更适合学习和试验 | 需要更严格审查 |
| 哪个更适合后续 Vivado 工程 | 需要额外配置 | 更直接 |
| 回退难度 | 简单，删除或忽略副本即可 | 需要反向 patch 或手动回退 |
| 当前推荐 | 推荐先用 | 暂不直接用 |

当前推荐：

```text
先采用策略 A：vendor_shell 副本实验。
```

但是注意：本任务不复制 top。是否创建 `vendor_shell\red_pitaya_top_laser.sv`，应在用户审查本 integration plan 后再决定。

## 8. Vivado 操作前检查清单

真正打开 Vivado 前必须确认：

| 检查项 | 状态 |
|---|---|
| RTL 已通过 testbench | 必须确认 |
| GPT 已审查 RTL | 必须确认 |
| integration plan 已审查 | 必须确认 |
| 明确 `OUTPUT_MODE` | `0` 或 `1`，不能含糊 |
| 明确 `USE_LASER_LOCK_CORE` | `1` 才走 laser core，`0` 回退官方路径 |
| 不接 `D2-125` | `OUT1` 先接示波器 |
| 不接激光器反馈 | 第一阶段禁止 |
| `REF` 已安全衰减 | 特别是不能把 6.32 Vpp 直接进 `IN2` |
| 知道如何回退官方路径 | `USE_LASER_LOCK_CORE = 0` |

## 9. 上板测试对应关系

参考：

```text
redpitaya_laser_lock_project\docs\board_tests\BOARD_TEST_v1ab_passthrough_debug.md
```

对应关系：

| `OUTPUT_MODE` | 测试目标 | 接线 |
|---:|---|---|
| 0 | `IN1 -> OUT1` | 信号发生器进 `IN1`，`OUT1` 接示波器 |
| 1 | `IN2 -> OUT1` | 安全衰减后的 4.6 MHz `REF` 进 `IN2`，`OUT1` 接示波器 |

注意：

- `OUT1` 先接示波器；
- 不接 `D2-125`；
- 不接激光器反馈；
- v1b 不能把 6.32 Vpp 参考信号直接接入 `IN2`。

## 10. 风险和失败排查

| 现象 | 可能原因 | 排查方法 |
|---|---|---|
| `OUT1` 无信号 | `laser_error` 没有接入 DAC A，或 `USE_LASER_LOCK_CORE=0` | 检查 `dac_a_sum` mux 和参数 |
| `OUT1/OUT2` 接反 | DAC A/B 映射或 mux 接反 | 示波器同时看 `OUT1` 和 `OUT2` |
| `OUT1` 削顶 | 输入过大，或 signed/unsigned 格式错误 | 降低输入幅度，检查符号扩展和官方格式转换 |
| reset 未释放 | `output_protect` 输出 0 | 检查 `adc_rstn` 和 PLL lock 状态 |
| 测错输入通道 | `OUTPUT_MODE` 设置错误 | v1a 用 `OUTPUT_MODE=0`，v1b 用 `OUTPUT_MODE=1` |
| `IN2` 看不到 4.6 MHz | `REF` 没进 `IN2` 或衰减后太小 | 先用示波器直接量 `IN2` 前的 REF |
| 官方 ASG/PID 路径失效 | mux 没有保留官方回退路径 | 设 `USE_LASER_LOCK_CORE=0` 验证官方路径 |

## 11. 仿真命令路径修正说明

如果当前目录是：

```text
redpitaya_laser_lock_project\sim
```

推荐命令是：

```text
xvlog -sv ..\rtl\output_protect.sv ..\rtl\laser_lock_core.sv tb_laser_lock_core_v1ab.sv
xelab tb_laser_lock_core_v1ab -s tb_laser_lock_core_v1ab_sim
xsim tb_laser_lock_core_v1ab_sim -runall
```

不要混淆：

| 当前目录 | 正确 RTL 路径 |
|---|---|
| `redpitaya_laser_lock_project\sim` | `..\rtl\laser_lock_core.sv` |
| `redpitaya_laser_lock_project\sim\v1ab_xsim_run` | `..\..\rtl\laser_lock_core.sv` |

小白解释：`..` 表示回到上一级目录。你站在 `sim` 目录里时，只要回一级就到 `redpitaya_laser_lock_project`，所以 RTL 是 `..\rtl`。如果你站在 `sim\v1ab_xsim_run` 里，就要回两级，所以是 `..\..\rtl`。

## 12. 下一步建议

下一步不是直接上板。

推荐顺序：

1. GPT 审查本文件：

```text
docs\integration\INTEGRATION_PLAN_v1ab_passthrough_debug.md
```

2. 决定使用 `vendor_shell` 还是 patch；
3. 用户明确允许后，再生成具体修改 diff；
4. 然后进入 Vivado；
5. Vivado 通过后，再按 `BOARD_TEST_v1ab_passthrough_debug.md` 做示波器验证。

在以上步骤完成前，不修改官方 `red_pitaya_top.sv`，不修改 Vivado 工程，不接 `D2-125`，不接激光器反馈。
