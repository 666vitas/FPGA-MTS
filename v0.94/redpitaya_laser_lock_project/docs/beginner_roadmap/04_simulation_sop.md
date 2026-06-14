# 仿真 SOP

## 0. 本文件作用

本文件说明如何用仿真先检查 RTL。

大白话：仿真就是不上板，先在电脑里用虚拟输入检查电路是否按预期工作。

## 1. 我需要理解什么

仿真包含三类文件：

| 文件 | 作用 |
|---|---|
| DUT | 要测试的模块，例如 `laser_lock_core.sv` |
| helper module | 被 DUT 调用的模块，例如 `output_protect.sv` |
| testbench | 虚拟实验台，例如 `tb_laser_lock_core_v1ab.sv` |

testbench 不会进入 FPGA。

## 2. 我需要操作什么

以 `v1ab_passthrough_debug` 为例，运行：

```text
cd E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\sim
xvlog -sv ..\rtl\output_protect.sv ..\rtl\laser_lock_core.sv tb_laser_lock_core_v1ab.sv
xelab tb_laser_lock_core_v1ab -s tb_laser_lock_core_v1ab_sim
xsim tb_laser_lock_core_v1ab_sim -runall
```

如果路径不同，要按实际位置改。

## 3. 我需要发给 GPT 什么

仿真失败时发：

```text
1. 执行的命令
2. 完整报错输出
3. 相关 RTL 文件
4. testbench 文件
5. 当前版本名
```

## 4. Codex 应该生成什么

Codex 应生成：

- 自检 testbench；
- 成功打印语句；
- `$fatal` 失败检查；
- REPORT 中记录仿真命令和结果。

## 5. 成功标准是什么

每个 testbench 都应有明确成功打印。

例如：

```text
V1AB PASSTHROUGH DEBUG TEST PASSED
```

如果没有成功打印，就不能算完全通过。

## 6. 失败怎么排查

| 现象 | 先查什么 |
|---|---|
| `xvlog` 报错 | 语法、文件路径、模块名 |
| `xelab` 报错 | 端口连接、模块缺失、参数错误 |
| `xsim` 报 `$fatal` | 功能逻辑不符合 testbench |
| 输出全是 X | reset 是否初始化，信号是否赋值 |
| 输出晚一个时钟 | 时序寄存器正常现象，确认 testbench 是否等了时钟 |

## 7. 我现在只需要记住什么

仿真通过前，不要上板。

```text
仿真是安全网。
```
