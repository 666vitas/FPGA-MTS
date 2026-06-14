# Vivado 基础操作 SOP

## 0. 本文件作用

本文件给 FPGA/Verilog/Vivado 新手说明 Vivado 中最基本的操作顺序。

注意：当前任务没有开始 Vivado 集成。本文件只是后续操作说明。

## 1. 我需要理解什么

Vivado 基本流程：

```text
Add Sources
  -> Run Synthesis
  -> Run Implementation
  -> Generate Bitstream
```

小白解释：

| 步骤 | 含义 |
|---|---|
| `Add Sources` | 把 `.sv` 文件加入工程 |
| `Run Synthesis` | 把 Verilog/SystemVerilog 翻译成 FPGA 逻辑 |
| `Run Implementation` | 把逻辑放进具体 FPGA 资源并布线 |
| `Generate Bitstream` | 生成可以加载到板子的 `.bit` 文件 |

## 2. 我需要操作什么

后续真正进入 Vivado 时，一般操作是：

1. 打开官方 Vivado 工程。
2. 确认要加入的是项目内自定义文件。
3. 用 `Add Sources` 加入 RTL。
4. 用 `Add Sources` 或 `Add Simulation Sources` 加入 testbench。
5. 先跑仿真。
6. 再跑 `Run Synthesis`。
7. 再跑 `Run Implementation`。
8. 最后 `Generate Bitstream`。

## 3. 我需要发给 GPT 什么

Vivado 报错时，把这些信息发给 GPT：

```text
1. 当前操作步骤：Run Synthesis / Run Implementation / Generate Bitstream
2. 完整错误信息
3. 修改过的文件列表
4. 当前版本名
5. 是否修改过 red_pitaya_top.sv
```

不要只截图最后一行，尽量复制完整错误文本。

## 4. Codex 应该生成什么

进入 Vivado 前，Codex 应该先生成：

```text
docs\integration\INTEGRATION_PLAN_<version>.md
docs\reports\REPORT_<version>.md
docs\board_tests\BOARD_TEST_<version>.md
```

如果需要修改 top，Codex 应该生成 patch 或详细修改说明，而不是直接乱改。

## 5. 成功标准是什么

Vivado 阶段成功标准：

- Synthesis 没有 error；
- Implementation 没有 error；
- Timing 没有严重失败；
- Bitstream 生成成功；
- 输出文件版本明确；
- 上板测试前已有 BOARD_TEST。

## 6. 失败怎么排查

| 错误类型 | 常见原因 | 先查什么 |
|---|---|---|
| module not found | 文件没加入 Vivado | `Add Sources` |
| port mismatch | 端口名或位宽不一致 | 模块实例化 |
| syntax error | SystemVerilog 语法问题 | 报错行附近 |
| multiple drivers | 一个信号被多个 always/assign 驱动 | 信号赋值位置 |
| timing failed | 路径太慢或跨时钟域 | 是否引入复杂逻辑 |

## 7. 不要碰/不要改

新手阶段不要随便改：

```text
PLL
ODDR
PS/AXI/DDR
XDC/SDC
red_pitaya_ps.sv
官方 scope/ASG/PID/HK 源码
```

## 8. 现在只需要记住什么

Vivado 不是第一步。第一步永远是：

```text
testbench 通过 + integration plan 通过审查
```
