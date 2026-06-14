# REPORT_v1ab_passthrough_debug

## 0. 本报告作用

本报告记录 `v1ab_passthrough_debug` 的代码生成和仿真验证。

本版本目标是先实现 `v1a` 和 `v1b` 的直通调试功能，用来上板验证 Red Pitaya `IN1/IN2` 输入路径。

## 1. 本次生成/修改了哪些文件

| 文件 | 类型 | 作用 |
|---|---|---|
| `redpitaya_laser_lock_project\rtl\laser_lock_core.sv` | 修改 | 增加 `OUTPUT_MODE` 参数，支持 `pd_i` 或 `ref_i` 直通到 `error_o` |
| `redpitaya_laser_lock_project\rtl\output_protect.sv` | 修改 | 实现 14 bit 输出保护：reset 或 `enable_i=0` 时输出 0 |
| `redpitaya_laser_lock_project\sim\tb_laser_lock_core_v1ab.sv` | 新增 | 自检 testbench，同时测试 `OUTPUT_MODE=0` 和 `OUTPUT_MODE=1` |
| `redpitaya_laser_lock_project\docs\reports\REPORT_v1ab_passthrough_debug.md` | 新增 | 本报告 |
| `redpitaya_laser_lock_project\docs\board_tests\BOARD_TEST_v1ab_passthrough_debug.md` | 新增 | 上板测试说明 |

## 2. 功能说明

`laser_lock_core` 当前只有两个调试模式：

| `OUTPUT_MODE` | 功能 | 用途 |
|---:|---|---|
| 0 | `error_o = pd_i` | 验证 `IN1 -> OUT1` |
| 1 | `error_o = ref_i` | 验证 `IN2 -> OUT1`，特别是 4.6 MHz `REF` 输入 |
| 其他 | `error_o = 0` | 防止误设参数时输出未知信号 |

`control_o` 始终为 `14'sd0`。

本版本不实现：

- mixer；
- LPF；
- BPF；
- PID；
- sweep；
- AI。

## 3. 没有修改官方工程

本次明确没有修改以下官方目录：

```text
rtl
project
sim
ip
sdc
```

本次也没有修改：

```text
rtl\red_pitaya_top.sv
red_pitaya_top.sv
Vivado 工程
```

本次没有复制官方 top，没有生成 integration patch。

## 4. 如何运行 testbench

建议在 Vivado Tcl Console 或 PowerShell 中运行：

```text
cd E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim
xvlog -sv ..\rtl\output_protect.sv ..\rtl\laser_lock_core.sv tb_laser_lock_core_v1ab.sv
xelab tb_laser_lock_core_v1ab -s tb_laser_lock_core_v1ab_sim
xsim tb_laser_lock_core_v1ab_sim -runall
```

## 5. testbench 成功标准

testbench 必须打印：

```text
V1AB PASSTHROUGH DEBUG TEST PASSED
```

自检内容包括：

- 125 MHz clock；
- reset 期间两个 DUT 输出都为 0；
- `dut_pd` 使用 `OUTPUT_MODE=0`，`error_o` 跟随 `pd_i`；
- `dut_ref` 使用 `OUTPUT_MODE=1`，`error_o` 跟随 `ref_i`；
- `pd_i` 正数、负数、0 都能正确测试；
- `ref_i` 正数、负数、0 都能正确测试；
- 两个 DUT 的 `control_o` 始终为 0；
- 失败时用 `$fatal` 终止仿真。

## 6. 仿真结果

已使用 Vivado Simulator 2020.1 运行自检 testbench。

实际运行命令：

```text
xvlog -sv ..\..\rtl\output_protect.sv ..\..\rtl\laser_lock_core.sv ..\tb_laser_lock_core_v1ab.sv
xelab tb_laser_lock_core_v1ab -s tb_laser_lock_core_v1ab_sim
xsim tb_laser_lock_core_v1ab_sim -runall
```

仿真通过，终端输出：

```text
V1AB PASSTHROUGH DEBUG TEST PASSED
```

说明：

- `xvlog` 通过，SystemVerilog 语法分析通过；
- `xelab` 通过，模块例化和 elaboration 通过；
- `xsim` 通过，所有自检检查通过；
- 本次没有生成波形截图，只记录文字仿真结果。

## 7. 后续为什么还不能直接上板

虽然 core-only testbench 可以验证 `laser_lock_core` 自己的逻辑，但它还没有接入官方 Red Pitaya top。

要真正上板，还必须先完成：

1. 生成 `INTEGRATION_PLAN_v1ab_passthrough_debug.md`；
2. 明确 `adc_dat[0]`、`adc_dat[1]` 如何接到 `pd_i/ref_i`；
3. 明确 `error_o` 如何接到 DAC A / OUT1 路径；
4. 明确保留官方 saturation、格式转换、ODDR；
5. 经用户确认后，再决定是否修改项目内 `vendor_shell` 或生成官方 top patch。

## 8. 下一步

下一步是生成：

```text
docs\integration\INTEGRATION_PLAN_v1ab_passthrough_debug.md
```

在这个 integration plan 通过审查之前，不应该修改官方 `red_pitaya_top.sv`，也不应该修改 Vivado 工程。
