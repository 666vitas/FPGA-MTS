# 02 ADC 输入路径追踪

实验定义：

- IN1 = PD 采集到的饱和吸收/MTS 光强信号
- IN2 = 外部信号发生器提供的 EOM 同源参考信号

阅读对象：

- `rtl/red_pitaya_top.sv`

原则：本文件只追踪 ADC 输入路径，不修改官方代码，不写新模块，不写 Verilog。

## 1. 顶层 ADC 外部端口

在 `red_pitaya_top` 顶层端口中，ADC 相关外部端口有：

| 端口名 | 方向 | 代码声明 | 说明 |
|---|---|---|---|
| `adc_dat_i` | input | `input logic [MNA-1:0] [16-1:0] adc_dat_i` | ADC 数据输入 |
| `adc_clk_i` | input | `input logic [2-1:0] adc_clk_i` | ADC 差分时钟输入，注释为 `{p,n}` |
| `adc_clk_o` | output | `output logic [2-1:0] adc_clk_o` | 可选 ADC clock source 输出，注释写 unused，`[0]=p; [1]=n` |
| `adc_cdcs_o` | output | `output logic adc_cdcs_o` | ADC clock duty cycle stabilizer |

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 94-98 行 `// ADC`、`adc_dat_i`、`adc_clk_i`、`adc_clk_o`、`adc_cdcs_o`

补充观察：

- `adc_clk_i` 通过 `IBUFDS i_clk` 进入 FPGA 内部，生成 `adc_clk_in`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 218-219 行。
- `adc_clk_o[0]` 和 `adc_clk_o[1]` 由两个 `ODDR` 输出，时钟使用 `adc_clk_daisy`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 387-388 行。
- `adc_cdcs_o` 被固定赋值为 `1'b1`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 390 行。

## 2. `adc_dat_i` 的维度和位宽

代码声明：

```systemverilog
input logic [MNA-1:0] [16-1:0] adc_dat_i
```

解释：

- `MNA` 是 acquisition module 的数量，默认值为 `2`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 52-57 行。
- `[MNA-1:0]` 表示有 `MNA` 路 ADC 数据。默认 `MNA=2`，因此是 `[1:0]`，也就是 `adc_dat_i[0]` 和 `adc_dat_i[1]` 两路。
- `[16-1:0]` 表示每一路 ADC 数据宽度为 16 bit，即 `[15:0]`。
- 所以在默认配置下，`adc_dat_i` 可以理解为“两路 ADC，每路 16 bit”：
  - `adc_dat_i[0][15:0]`
  - `adc_dat_i[1][15:0]`
- 声明中没有 `signed`，因此按 SystemVerilog 语义它是 unsigned `logic` 数据。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 56 行 `parameter MNA = 2`
- 位置/关键词：第 95 行 `input logic [MNA-1:0] [16-1:0] adc_dat_i`

## 3. `adc_dat_i[0]` 和 `adc_dat_i[1]` 是否对应 IN1/IN2？

在 top 代码里可以确认的是：

- `adc_dat_i[0]` 经过转换后成为 `adc_dat[0]`，并在 scope 实例中标注为 `CH 1`。
- `adc_dat_i[1]` 经过转换后成为 `adc_dat[1]`，并在 scope 实例中标注为 `CH 2`。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 397 行 `adc_dat_raw[0] = adc_dat_i[0][16-1:2]`
- 位置/关键词：第 398 行 `adc_dat_raw[1] = adc_dat_i[1][16-1:2]`
- 位置/关键词：第 519 行 `.adc_a_i(adc_dat[0]) // CH 1`
- 位置/关键词：第 520 行 `.adc_b_i(adc_dat[1]) // CH 2`

结合你的实验定义，推荐暂定：

- IN1/PD 光强信号 -> Red Pitaya ADC CH1 -> 候选信号 `adc_dat[0]`
- IN2/EOM 同源参考信号 -> Red Pitaya ADC CH2 -> 候选信号 `adc_dat[1]`

但这不能只靠 `red_pitaya_top.sv` 完全确认。`adc_dat_i[0]` 是否物理对应前面板 IN1、`adc_dat_i[1]` 是否物理对应前面板 IN2，需要结合板卡原理图、XDC 约束或官方硬件文档确认。

结论：不确定，需要结合板卡原理图或文档确认。

## 4. `adc_dat_raw` 如何由 `adc_dat_i` 得到

代码中先声明：

```systemverilog
logic [2-1:0] [14-1:0] adc_dat_raw;
```

这表示 `adc_dat_raw` 是 2 路、每路 14 bit 的内部原始 ADC 数据。

转换关系：

```text
adc_dat_raw[0] = adc_dat_i[0][15:2]
adc_dat_raw[1] = adc_dat_i[1][15:2]
```

也就是说，top 从每路 16-bit ADC 输入中取高 14 bit，丢弃最低 2 bit。代码注释写着 `lowest 2 bits reserved for 16bit ADC`。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 392 行 `logic [2-1:0] [14-1:0] adc_dat_raw`
- 位置/关键词：第 394-395 行注释 `lowest 2 bits reserved for 16bit ADC`
- 位置/关键词：第 397-398 行 `assign adc_dat_raw[0/1] = adc_dat_i[0/1][16-1:2]`

## 5. `adc_dat` 如何由 `adc_dat_raw` 得到

`adc_dat` 在 `posedge adc_clk` 下寄存生成：

```text
adc_dat[0] <= digital_loop ? dac_a : {adc_dat_raw[0][13], ~adc_dat_raw[0][12:0]}
adc_dat[1] <= digital_loop ? dac_b : {adc_dat_raw[1][13], ~adc_dat_raw[1][12:0]}
```

含义：

- 正常情况下，`digital_loop = 0`，`adc_dat[x]` 来自 `adc_dat_raw[x]`。
- 转换方式保留最高位 `adc_dat_raw[x][13]`，取反低 13 位 `adc_dat_raw[x][12:0]`。
- 代码注释明确写了 `transform into 2's complement (negative slope)`，也就是把 ADC 的 unsigned negative-slope 格式转换成 two's complement 格式。
- 如果 `digital_loop = 1`，`adc_dat[0]` 不是外部 ADC，而是 `dac_a`；`adc_dat[1]` 不是外部 ADC，而是 `dac_b`。这是数字回环调试路径。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 400 行注释 `transform into 2's complement (negative slope)`
- 位置/关键词：第 401-404 行 `always @(posedge adc_clk)`、`adc_dat[0] <= digital_loop ? dac_a : ...`
- 位置/关键词：第 445-453 行 `red_pitaya_hk` 输出 `digital_loop`

## 6. `adc_dat` 的类型 `SBA_T`

`SBA_T` 在 top 中用 `localparam type` 定义：

```systemverilog
localparam type SBA_T = logic signed [14-1:0];  // acquire
```

因此：

- `SBA_T` 是 signed。
- 位宽是 14 bit，即 `[13:0]`。
- `adc_dat` 声明为 `SBA_T [MNA-1:0] adc_dat`，所以默认有 2 路 signed 14-bit ADC 内部数据。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 182-186 行 `localparam type SBA_T = logic signed [14-1:0]`、`SBA_T [MNA-1:0] adc_dat`

## 7. `adc_dat[0]` 和 `adc_dat[1]` 当前送到哪些模块

### 送到 `red_pitaya_scope`

连接关系：

```text
adc_dat[0] -> red_pitaya_scope.adc_a_i  // CH 1
adc_dat[1] -> red_pitaya_scope.adc_b_i  // CH 2
adc_clk    -> red_pitaya_scope.adc_clk_i
adc_rstn   -> red_pitaya_scope.adc_rstn_i
```

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 517-522 行 `red_pitaya_scope i_scope`

意义：scope 是当前官方工程里观察 ADC 数据的主要路径。对本项目来说，它可用于观察 IN1/PD 光强和 IN2/参考信号。

### 送到 `red_pitaya_pid`

连接关系：

```text
adc_dat[0] -> red_pitaya_pid.dat_a_i
adc_dat[1] -> red_pitaya_pid.dat_b_i
adc_clk    -> red_pitaya_pid.clk_i
adc_rstn   -> red_pitaya_pid.rstn_i
```

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 577-584 行 `red_pitaya_pid i_pid`

意义：当前官方 PID 直接接收 ADC 数据。但对 MTS/饱和吸收稳频来说，IN1 是光强信号，不是最终误差信号；未来应先经过 `laser_lock_core` 或 MTS 解调链路生成 error，再决定是否送 PID。

### 是否送到其他模块

在 `rtl/red_pitaya_top.sv` 当前阅读范围内，`adc_dat[0]` 和 `adc_dat[1]` 直接作为数据输入明确送到：

- `red_pitaya_scope`
- `red_pitaya_pid`

另有间接相关路径：

- `sys_bus_if ps_sys/sys` 使用 `adc_clk`/`adc_rstn`，但不使用 `adc_dat` 数据。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 207-209 行。
- `red_pitaya_asg` 使用 `adc_clk`/`adc_rstn` 作为时钟复位，但不接收 `adc_dat`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 554-559 行。
- `red_pitaya_daisy` 使用 `adc_clk`/`adc_rstn` 作为并行 TX 和 system bus 时钟复位，但不接收 `adc_dat`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 604-638 行。

结论：在 top 代码中未看到 `adc_dat[0/1]` 直接送入其他数据处理模块。不确定，需要人工确认其他 generate、include 或工程配置是否有未展开连接；当前 `red_pitaya_top.sv` 中没有。

## 8. `adc_dat` 使用哪个时钟

`adc_dat` 在这个 always block 中生成：

```text
always @(posedge adc_clk)
```

所以 `adc_dat[0]` 和 `adc_dat[1]` 属于 `adc_clk` 时钟域。

`adc_clk` 来源：

```text
adc_clk_i[1:0]
  -> IBUFDS i_clk
  -> adc_clk_in
  -> red_pitaya_pll.clk_adc
  -> pll_adc_clk
  -> BUFG bufg_adc_clk
  -> adc_clk
```

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 218-219 行 `IBUFDS i_clk`
- 位置/关键词：第 221-233 行 `red_pitaya_pll pll`
- 位置/关键词：第 236 行 `BUFG bufg_adc_clk`
- 位置/关键词：第 401 行 `always @(posedge adc_clk)`

`adc_rstn` 来源：

```text
adc_rstn <= frstn[0] & pll_locked
```

其中：

- `frstn` 来自 `red_pitaya_ps` 的 `.fclk_rstn_o(frstn)`。
- `pll_locked` 来自 `red_pitaya_pll` 的 `.pll_locked(pll_locked)`。
- `adc_rstn` 在 `posedge adc_clk` 下寄存生成，是 active-low reset。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 131-132 行 `fclk`、`frstn`
- 位置/关键词：第 256-258 行 `adc_rstn <= frstn[0] & pll_locked`
- 位置/关键词：第 275-300 行 `red_pitaya_ps ps` 输出 `fclk_rstn_o(frstn)`
- 位置/关键词：第 221-233 行 `red_pitaya_pll` 输出 `pll_locked`

## 9. 未来新增 `laser_lock_core` 的 ADC 输入建议

基于你的实验定义，推荐连接：

- PD 输入：`adc_dat[0]`
- 参考输入：`adc_dat[1]`

推荐端口命名：

| 未来 `laser_lock_core` 端口名 | 建议连接 | 含义 |
|---|---|---|
| `clk_i` | `adc_clk` | 激光稳频核心工作时钟 |
| `rstn_i` | `adc_rstn` | active-low reset |
| `pd_i` | `adc_dat[0]` | IN1，PD 饱和吸收/MTS 光强信号 |
| `ref_i` | `adc_dat[1]` | IN2，EOM 同源参考信号 |
| `pd_valid_i` | 不确定，需要人工确认 | 当前 top 没有 ADC valid 信号 |
| `ref_valid_i` | 不确定，需要人工确认 | 当前 top 没有 ADC valid 信号 |

重要边界：

- `adc_dat[0]`/`adc_dat[1]` 在代码中对应 CH1/CH2，但是否对应你实验接线里的 IN1/IN2，需要结合板卡原理图或文档确认。
- 当前 top 没有发现单独的 ADC sample valid 信号；从代码看，`adc_dat` 每个 `adc_clk` 周期更新一次。是否需要 valid 端口取决于后续设计风格。结论：不确定，需要人工确认。

证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 401-404 行 `adc_dat[0/1]` 在 `adc_clk` 下更新
- 位置/关键词：第 517-522 行 scope 标注 `adc_dat[0]` 为 CH1、`adc_dat[1]` 为 CH2

## 10. ADC 路径图

```text
外部 ADC 数据端口
  adc_dat_i[MNA-1:0][15:0]
      |
      | 默认 MNA=2
      | adc_dat_i[0][15:0]  候选 IN1/PD
      | adc_dat_i[1][15:0]  候选 IN2/EOM reference
      | 不确定，需要板卡资料确认物理 IN1/IN2 映射
      |
      v
截位
  adc_dat_raw[0] = adc_dat_i[0][15:2]
  adc_dat_raw[1] = adc_dat_i[1][15:2]
      |
      v
格式转换，posedge adc_clk
  adc_dat[0] = {adc_dat_raw[0][13], ~adc_dat_raw[0][12:0]}
  adc_dat[1] = {adc_dat_raw[1][13], ~adc_dat_raw[1][12:0]}
      |
      | 14-bit signed two's complement, adc_clk 域
      |
      +-------------------------> red_pitaya_scope
      |                            adc_a_i = adc_dat[0]  // CH1
      |                            adc_b_i = adc_dat[1]  // CH2
      |
      +-------------------------> red_pitaya_pid
      |                            dat_a_i = adc_dat[0]
      |                            dat_b_i = adc_dat[1]
      |
      +-------------------------> laser_lock_core 候选输入
                                   pd_i  = adc_dat[0]
                                   ref_i = adc_dat[1]
```

证据主线：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 95 行 `adc_dat_i`
- 位置/关键词：第 392-398 行 `adc_dat_raw`
- 位置/关键词：第 400-404 行 `adc_dat`
- 位置/关键词：第 517-522 行 `red_pitaya_scope`
- 位置/关键词：第 577-584 行 `red_pitaya_pid`

## 11. ADC 相关信号表

| 信号名 | 位宽 | signed/unsigned | 时钟域 | 当前用途 | 和稳频项目关系 |
|---|---:|---|---|---|---|
| `adc_dat_i` | 默认 2 路 x 16 bit | unsigned `logic` | 外部 ADC 接口；进入 FPGA 前不属于内部 `adc_clk` 寄存域 | 顶层 ADC 数据输入 | 原始 IN1/IN2 数据入口候选；物理映射不确定，需要人工确认 |
| `adc_dat_i[0]` | 16 bit | unsigned `logic` | 外部 ADC 接口 | 生成 `adc_dat_raw[0]` | 候选 IN1/PD 光强数据；不确定，需要板卡资料确认 |
| `adc_dat_i[1]` | 16 bit | unsigned `logic` | 外部 ADC 接口 | 生成 `adc_dat_raw[1]` | 候选 IN2/EOM 同源参考；不确定，需要板卡资料确认 |
| `adc_clk_i` | 2 bit | unsigned `logic` | 外部差分时钟 | 经 `IBUFDS` 生成 `adc_clk_in` | ADC 采样时钟源 |
| `adc_clk_in` | 1 bit | unsigned `logic` | PLL 输入侧 | `red_pitaya_pll.clk` 输入 | 生成内部 ADC/DAC 相关时钟的源头 |
| `pll_adc_clk` | 1 bit | unsigned `logic` | PLL 输出 | 经 BUFG 生成 `adc_clk` | 稳频核心推荐时钟的前级 |
| `adc_clk` | 1 bit | unsigned `logic` | `adc_clk` 域 | 生成 `adc_dat`，驱动 scope、ASG、PID、system bus 等 | 推荐 `laser_lock_core.clk_i` |
| `adc_rstn` | 1 bit | unsigned `logic` | `adc_clk` 域 | ADC 域 active-low reset | 推荐 `laser_lock_core.rstn_i` |
| `adc_clk_o` | 2 bit | unsigned `logic` | 由 `adc_clk_daisy` 驱动 ODDR | 可选 ADC clock source 输出，注释 unused | 暂时不作为稳频核心输入 |
| `adc_cdcs_o` | 1 bit | unsigned `logic` | 组合常量 | 固定为 `1'b1` | ADC 硬件辅助控制；暂时不改 |
| `adc_dat_raw` | 2 路 x 14 bit | unsigned `logic` | 组合截位信号 | `adc_dat_i[x][15:2]` | 调试理解 ADC 格式时重要；通常不直接给算法用 |
| `adc_dat_raw[0]` | 14 bit | unsigned `logic` | 组合截位信号 | 生成 `adc_dat[0]` | IN1 的格式转换前内部数据候选 |
| `adc_dat_raw[1]` | 14 bit | unsigned `logic` | 组合截位信号 | 生成 `adc_dat[1]` | IN2 的格式转换前内部数据候选 |
| `SBA_T` | 14 bit | signed | 类型定义，不是信号 | 定义 acquire stream 数据类型 | 决定 `adc_dat` 是 signed 14-bit |
| `adc_dat` | 默认 2 路 x 14 bit | signed `SBA_T` | `adc_clk` 域 | 转换后的内部 ADC 数据 | 未来 `laser_lock_core` 最推荐使用的 ADC 输入 |
| `adc_dat[0]` | 14 bit | signed `SBA_T` | `adc_clk` 域 | 送 scope CH1、PID input 1 | 推荐 `pd_i`，候选 IN1/PD |
| `adc_dat[1]` | 14 bit | signed `SBA_T` | `adc_clk` 域 | 送 scope CH2、PID input 2 | 推荐 `ref_i`，候选 IN2/EOM reference |
| `digital_loop` | 1 bit | unsigned `logic` | `adc_clk` 相关使用；由 HK 配置 | 选择 `adc_dat` 来自外部 ADC 还是 DAC 回环 | 实验时必须确认关闭，否则 IN1/IN2 不是真实外部输入 |

表格证据：

- 文件：`rtl/red_pitaya_top.sv`
- 模块：`red_pitaya_top`
- 位置/关键词：第 94-98 行 ADC 顶层端口
- 位置/关键词：第 155-186 行 ADC 时钟、reset、`SBA_T`、`adc_dat`
- 位置/关键词：第 218-258 行 `adc_clk`、`adc_rstn` 来源
- 位置/关键词：第 387-404 行 ADC IO 和数据转换
- 位置/关键词：第 517-522 行 scope 连接
- 位置/关键词：第 577-584 行 PID 连接

## 12. 当前结论和不确定项

已确认：

1. `adc_dat_i` 是默认 2 路、每路 16 bit 的顶层 ADC 数据输入。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 56 行、第 95 行。
2. top 只取 `adc_dat_i[x][15:2]` 作为 14-bit `adc_dat_raw[x]`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 392-398 行。
3. `adc_dat_raw` 被转换为 two's complement/negative-slope 格式后形成 signed 14-bit `adc_dat`。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 400-404 行。
4. `adc_dat[0]` 当前送入 scope CH1 和 PID input 1；`adc_dat[1]` 当前送入 scope CH2 和 PID input 2。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 517-522 行、第 577-584 行。
5. `adc_dat` 属于 `adc_clk` 域，`adc_rstn` 是 `adc_clk` 下由 `frstn[0] & pll_locked` 生成的 active-low reset。证据：`rtl/red_pitaya_top.sv`，模块 `red_pitaya_top`，第 218-258 行、第 401 行。

不确定，需要人工确认：

1. `adc_dat_i[0]` 是否物理等于前面板 IN1，`adc_dat_i[1]` 是否物理等于前面板 IN2，需要结合 Red Pitaya 板卡原理图、XDC 约束或官方硬件文档确认。
2. 你的实验接线如果定义 IN1=PD、IN2=EOM reference，那么代码层面的候选连接是 `pd_i=adc_dat[0]`、`ref_i=adc_dat[1]`，但最终仍需硬件文档和实测确认。
3. 当前 top 中没有看到 ADC sample valid 信号；是否需要在未来 `laser_lock_core` 端口中加入 valid，需要根据后续时序设计确认。
