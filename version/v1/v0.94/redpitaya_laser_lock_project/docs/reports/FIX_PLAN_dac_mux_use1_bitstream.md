# FIX_PLAN_dac_mux_use1_bitstream

## 0. 本文件作用

本文件只分析 `USE_LASER_LOCK_CORE=1` 时 DAC mux 接入方案，不修改 RTL，不修改 Vivado 工程，不运行 Vivado。

当前目标是：先让 `USE_LASER_LOCK_CORE=1` 可以稳定 `Generate Bitstream` 成功，再考虑 `v1ab IN1 -> OUT1` 上板测试。

本文件不是 patch 执行记录，只是给 GPT / 用户审查的修正方案。

## 1. 当前排查结论

当前已知结论：

- 官方 baseline 可以 `Generate Bitstream` 成功；
- 当前开发工程在 `USE_LASER_LOCK_CORE=0` 时可以 `Generate Bitstream` 成功；
- 当前开发工程在 `USE_LASER_LOCK_CORE=1` 时之前 bitstream 失败；
- `USE_LASER_LOCK_CORE=0` 只是官方回退路径，不能用于 `v1ab IN1 -> OUT1` 测试；
- 因此当前优先检查 `laser_error` 接入 `dac_a_sum / dac_b_sum` 的 DAC mux 方案。

新手可以这样理解：

```text
USE=0 能过：官方 DAC 路线大体没问题。
USE=1 失败：一打开 laser_lock_core 到 DAC 的接入路径就出问题。
所以先查 mux 接入，不要急着写 mixer。
```

## 2. 官方 dac_a_sum / dac_b_sum 原始写法

官方干净 top：

```text
E:\new\fpga_lock\v94\guanfang-v0.94\v0.94\rtl\red_pitaya_top.sv
```

官方相关代码片段：

```systemverilog
logic        [14-1:0] dac_dat_a, dac_dat_b;
logic        [14-1:0] dac_a    , dac_b    ;
logic signed [15-1:0] dac_a_sum, dac_b_sum;

// Sumation of ASG and PID signal perform saturation before sending to DAC
assign dac_a_sum = asg_dat[0] + pid_dat[0];
assign dac_b_sum = asg_dat[1] + pid_dat[1];

// saturation
assign dac_a = (^dac_a_sum[15-1:15-2]) ? {dac_a_sum[15-1], {13{~dac_a_sum[15-1]}}} : dac_a_sum[14-1:0];
assign dac_b = (^dac_b_sum[15-1:15-2]) ? {dac_b_sum[15-1], {13{~dac_b_sum[15-1]}}} : dac_b_sum[14-1:0];
```

官方原始路径：

```text
asg_dat[0] + pid_dat[0] -> dac_a_sum
asg_dat[1] + pid_dat[1] -> dac_b_sum
```

然后继续走官方后级：

```text
dac_a_sum / dac_b_sum
  -> saturation
  -> dac_a / dac_b
  -> dac_dat_a / dac_dat_b 寄存器
  -> DAC ODDR
  -> dac_dat_o / dac_wrt_o / dac_sel_o / dac_clk_o / dac_rst_o
```

这条官方后级不要改。

## 3. 当前开发版 dac_a_sum / dac_b_sum 写法

当前开发 top：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

当前开发版新增开关和 laser 信号：

```systemverilog
// USE_LASER_LOCK_CORE = 0 keeps the official ASG + PID DAC path.
// LASER_LOCK_OUTPUT_MODE: 0 = IN1/pd_i -> OUT1, 1 = IN2/ref_i -> OUT1.
localparam logic USE_LASER_LOCK_CORE = 1'b0;
localparam int   LASER_LOCK_OUTPUT_MODE = 0;

logic signed [14-1:0] laser_error;
logic signed [14-1:0] laser_control;
```

当前开发版 `laser_lock_core` 接入：

```systemverilog
laser_lock_core #(
  .OUTPUT_MODE(LASER_LOCK_OUTPUT_MODE)
) i_laser_lock_core (
  .clk_i     (adc_clk      ),
  .rstn_i    (adc_rstn     ),
  .pd_i      (adc_dat[0]   ),
  .ref_i     (adc_dat[1]   ),
  .error_o   (laser_error  ),
  .control_o (laser_control)
);
```

当前开发版 `dac_a_sum / dac_b_sum` 写法：

```systemverilog
assign dac_a_sum = USE_LASER_LOCK_CORE
                 ? {laser_error[14-1], laser_error}
                 : asg_dat[0] + pid_dat[0];

assign dac_b_sum = USE_LASER_LOCK_CORE
                 ? 15'sd0
                 : asg_dat[1] + pid_dat[1];
```

也就是说：

```text
USE=0:
  dac_a_sum = asg_dat[0] + pid_dat[0]
  dac_b_sum = asg_dat[1] + pid_dat[1]

USE=1:
  dac_a_sum = sign_extend(laser_error)
  dac_b_sum = 15'sd0
```

## 4. 当前写法的风险分析

### 4.1 组合 mux 直接进入 DAC 高速路径

当前 mux 直接写在 `dac_a_sum / dac_b_sum` 的组合赋值中：

```systemverilog
assign dac_a_sum = USE_LASER_LOCK_CORE
                 ? {laser_error[14-1], laser_error}
                 : asg_dat[0] + pid_dat[0];
```

`dac_a_sum` 后面紧接 saturation、`dac_dat_a / dac_dat_b` 寄存器和 DAC ODDR。最近 `USE=0` 虽然 bitstream 成功，但仍出现：

```text
WNS = -0.005 ns
failing endpoint = 1
主要路径在 pll_dac_clk_1x / DAC ODDR 附近
```

这说明 DAC 附近本来就比较敏感。把新的组合 mux 直接放进这个路径，可能改变实现和时序。

### 4.2 dac_b_sum 直接常量 15'sd0 是否改变官方路径优化

当前 `USE=1` 时：

```systemverilog
assign dac_b_sum = USE_LASER_LOCK_CORE
                 ? 15'sd0
                 : asg_dat[1] + pid_dat[1];
```

这在功能上是合理的，因为 v1ab 暂时不使用 `OUT2`。但从综合实现角度看，`dac_b_sum` 的 `USE=1` 分支变成常量，可能让 Vivado 对 DAC B 相关路径做不同优化。

这不一定是错误，但排查时应注意：

- 是否先只替换 DAC A；
- 是否暂时保持 DAC B 官方路径；
- 是否减少同时改 A/B 两路带来的不确定性。

### 4.3 signed 位宽是否明确

当前 `dac_a_sum` 是：

```systemverilog
logic signed [15-1:0] dac_a_sum;
```

当前 laser 分支是：

```systemverilog
{laser_error[14-1], laser_error}
```

这个表达式位宽是 15 bit，但是否被 Vivado 以完全符合预期的 signed 方式处理，建议进一步显式化。

更清楚的写法是先拆成明确的 15-bit signed 中间信号：

```systemverilog
logic signed [15-1:0] dac_a_sum_laser;
assign dac_a_sum_laser = {laser_error[13], laser_error};
```

这样对新手和综合器都更直观。

### 4.4 是否可能改变官方 DAC 路径时序

可能。

原因不是 `laser_error` 逻辑复杂，而是它改变了 `dac_a_sum / dac_b_sum` 的来源结构。官方原始路径是：

```text
asg_dat + pid_dat -> dac_sum -> saturation -> DAC output register
```

当前变成：

```text
(laser path 或 official path) -> mux -> dac_sum -> saturation -> DAC output register
```

即使 `USE_LASER_LOCK_CORE` 是 localparam，Vivado 仍会根据不同分支综合出不同结构。`USE=1` 和 `USE=0` 的实现结果可能不同。

### 4.5 是否可能导致 DRC / routing 异常

可能，但当前不能直接下结论。

已知事实是：

- `USE=0` 成功；
- `USE=1` 之前失败；
- 差异集中在 laser path 接入 DAC 求和路径；
- 因此优先排查 mux 接入方案是合理的。

但如果修正 DAC mux 后仍失败，还要继续查：

- 非预期 LED/HK 差异；
- timing / DRC 具体路径；
- 是否有 run 缓存或实现状态问题；
- 是否需要从官方 clean top 重新应用最小 patch。

### 4.6 是否需要在 mux 前或 mux 后加寄存器

可以考虑，但不建议第一步就做复杂寄存。

优先顺序建议：

1. 先做方案 A：显式拆出 official 和 laser 两条 15-bit signed 中间信号；
2. 如果仍失败，再考虑方案 B：在 `adc_clk` 域先寄存 `laser_error_ext`，再送入 `dac_a_sum_laser`；
3. 如果还失败，再考虑更小范围 patch，例如只替换 DAC A，不动 DAC B。

## 5. 推荐更保守的修改方案

### 方案 A：保持组合 mux，但显式拆出 official 和 laser 两条 15-bit signed 中间信号

概念代码：

```systemverilog
logic signed [15-1:0] dac_a_sum_official;
logic signed [15-1:0] dac_b_sum_official;
logic signed [15-1:0] dac_a_sum_laser;
logic signed [15-1:0] dac_b_sum_laser;

assign dac_a_sum_official = asg_dat[0] + pid_dat[0];
assign dac_b_sum_official = asg_dat[1] + pid_dat[1];

assign dac_a_sum_laser = {laser_error[13], laser_error};
assign dac_b_sum_laser = 15'sd0;

assign dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser    : dac_a_sum_official;
assign dac_b_sum = USE_LASER_LOCK_CORE ? dac_b_sum_laser    : dac_b_sum_official;
```

这个方案的优点：

- 不改官方 saturation；
- 不改 DAC ODDR；
- 不改 DAC 输出引脚；
- 不改 PLL / BUFG / ADC IO / PS / XDC；
- 位宽更明确；
- official path 和 laser path 更清楚；
- patch 很小，适合作为第一步排查。

这个方案的代价：

- 仍然是组合 mux；
- 如果失败原因是 DAC 附近组合路径或布线压力，方案 A 可能还不够。

### 方案 B：在 adc_clk 域先寄存 laser_error_ext，再送 dac_a_sum_laser

概念代码：

```systemverilog
logic signed [15-1:0] laser_error_ext;
logic signed [15-1:0] laser_error_ext_r;

assign laser_error_ext = {laser_error[13], laser_error};

always @(posedge adc_clk) begin
  if (!adc_rstn)
    laser_error_ext_r <= 15'sd0;
  else
    laser_error_ext_r <= laser_error_ext;
end

assign dac_a_sum_laser = laser_error_ext_r;
```

这个方案是否更安全：

- 对 `laser_error` 输出做了一拍寄存，能让进入 DAC mux 的 laser 分支更稳定；
- `laser_lock_core` 本来使用 `adc_clk` 和 `adc_rstn`，因此在 `adc_clk` 域寄存比较自然；
- 它可能减少从 `laser_lock_core` 到 DAC mux 的组合路径不确定性。

代价：

- 增加 1 拍延迟；
- 多了一个寄存器阶段；
- 如果 `adc_clk` 和 `dac_clk_1x` 虽然同源但相位/约束关系敏感，后续仍需观察 timing；
- 比方案 A 稍微多改一点，不适合作为最小第一步。

注意：

方案 B 仍然不修改 ODDR、DAC 输出、PLL、BUFG、ADC IO、PS、XDC。

## 6. 推荐采用哪个方案

推荐先采用：

```text
方案 A：保持组合 mux，但显式拆出 official 和 laser 两条 15-bit signed 中间信号。
```

原因：

1. 当前目标只是先让 `USE_LASER_LOCK_CORE=1` 可以 bitstream 成功，不追求复杂功能；
2. 方案 A 改动最小；
3. 方案 A 不引入新寄存器、不引入额外时钟域讨论；
4. 方案 A 能把 official path、laser path、mux 输出写得更清楚；
5. 如果方案 A 仍失败，再进入方案 B 或更小范围策略。

推荐的排查策略是：

```text
第一步：方案 A
第二步：如果仍失败，方案 B
第三步：如果仍失败，只替换 DAC A，不动 DAC B
第四步：如果仍失败，从官方 clean top 重新应用最小 patch
```

## 7. 禁止修改范围

本次修正方案明确禁止修改：

- DAC ODDR；
- `dac_dat_o`；
- `dac_wrt_o`；
- `dac_sel_o`；
- `dac_clk_o`；
- `dac_rst_o`；
- PLL；
- BUFG；
- ADC IO；
- PS/AXI/DDR；
- XDC/SDC；
- `laser_lock_core.sv`；
- `output_protect.sv`。

也就是说，本次只允许讨论：

```text
red_pitaya_top.sv 中 dac_a_sum / dac_b_sum mux 附近的接入写法。
```

## 8. 后续执行步骤

建议后续流程：

1. GPT 审查本 `FIX_PLAN`；
2. Codex 生成 patch；
3. 备份 `red_pitaya_top.sv`；
4. 应用 patch；
5. 设置 `USE_LASER_LOCK_CORE=1`；
6. `Reset Runs`；
7. `Run Synthesis`；
8. `Run Implementation`；
9. `Generate Bitstream`；
10. 若成功，再进入 `v1ab IN1 -> OUT1` 上板测试。

在第 10 步之前：

- 不要开始 `v1c mixer`；
- 不要接板子；
- 不要接 `D2-125`；
- 不要接真实 `PD`；
- 不要接激光器反馈。

## 9. 如果仍然失败怎么办

如果方案 A 应用后 `USE_LASER_LOCK_CORE=1` 仍然失败，下一步建议按以下顺序缩小问题：

1. 从官方干净 top 重新应用最小 `v1ab` patch。

目的：

```text
排除当前开发 top 中历史差异或非预期改动的影响。
```

2. 或只接 `laser_error`，但保持 `dac_b_sum` 官方路径。

概念：

```systemverilog
assign dac_a_sum = USE_LASER_LOCK_CORE ? dac_a_sum_laser : dac_a_sum_official;
assign dac_b_sum = dac_b_sum_official;
```

目的：

```text
只验证 DAC A / OUT1，不同时改变 DAC B / OUT2。
```

3. 或暂时只替换 DAC A，不动 DAC B。

这和第 2 点类似，适合 `v1ab IN1 -> OUT1`，因为当前阶段本来只需要 OUT1。

4. 或检查 timing / DRC 具体路径。

需要重点保存：

```text
DRC 错误完整文本
failing endpoint
timing path
涉及 clock
涉及 cell / net
```

如果 DRC 仍集中在 I/O 或 ODDR 附近，还要回头检查：

- `led_o` 非预期差异；
- DAC ODDR 附近路径；
- 是否有 run 缓存；
- 是否需要 clean build。

当前仍然不要开始 `v1c mixer`。
