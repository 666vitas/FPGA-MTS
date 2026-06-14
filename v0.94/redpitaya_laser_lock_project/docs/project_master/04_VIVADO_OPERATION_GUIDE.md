# Vivado 操作指南

## 0. Vivado 只能打开 .xpr

Vivado 不是“打开一个文件夹”就会自动综合里面所有 `.sv` 文件。

必须记住：

```text
Vivado 打开的是 .xpr 工程。
文件存在于目录中，不代表 Vivado 会综合它。
必须确认 Sources 中有该文件。
```

例如：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
```

即使这个文件已经在磁盘上，如果 Vivado `Sources` 里没有它，综合时仍可能报：

```text
module laser_lock_core not found
```

## 1. 当前推荐开发方式

当前三个目录角色：

```text
开发区：
E:\new\fpga_lock\v94\v0.94

官方干净原版：
E:\new\fpga_lock\v94\guanfang-v0.94\v0.94

项目资料：
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project
```

原则：

- Vivado 后续在 `E:\new\fpga_lock\v94\v0.94` 中开发；
- `guanfang-v0.94\v0.94` 只读，不修改；
- 文档、报告、测试 SOP 继续留在 `redpitaya_laser_lock_project`；
- 参与综合的 RTL 优先放在 `E:\new\fpga_lock\v94\v0.94\rtl`。

## 2. Add Sources 操作

当前 `v1ab` 需要 Vivado 看到：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

操作路径：

```text
Flow Navigator
  -> Project Manager
  -> Add Sources
  -> Add or create design sources
  -> Add Files
```

选择文件后，确认它们出现在 `Sources` 的 `Design Sources` 中。

新手容易犯的错误：

- 只把文件复制到 `rtl` 目录，但没有 Add Sources；
- Add 到 `Simulation Sources`，但没有 Add 到 `Design Sources`；
- 添加了旧路径，例如 `redpitaya_laser_lock_project\rtl` 下的文件，而不是当前开发区 `v0.94\rtl` 下的文件。

当前推荐使用：

```text
E:\new\fpga_lock\v94\v0.94\rtl\laser_lock_core.sv
E:\new\fpga_lock\v94\v0.94\rtl\output_protect.sv
```

## 3. 确认 top

`red_pitaya_top.sv` 是 top。

不要把下面这些文件 `Set as Top`：

```text
laser_lock_core.sv
output_protect.sv
mixer_core.sv
lpf_core.sv
```

它们是被 top 调用的子模块，不是整个 FPGA 工程的顶层。

当前应确认：

```text
E:\new\fpga_lock\v94\v0.94\rtl\red_pitaya_top.sv
```

在 Vivado 中作为顶层模块 `red_pitaya_top`。

## 4. Run Synthesis

操作：

```text
Flow Navigator -> Synthesis -> Run Synthesis
```

如果弹出保存或启动选项，按当前工程默认设置继续。

成功标准：

- 没有 `ERROR`；
- 如果有 `WARNING`，先记录，不要忽略；
- `laser_lock_core` 和 `output_protect` 没有 module not found。

报错处理：

- 复制完整错误文本；
- 记录错误发生在哪个文件和行号；
- 不要只截图最后一行；
- 把错误发给 GPT/Codex 时同时说明当前版本，例如 `v1ab`。

## 5. Run Implementation

操作：

```text
Flow Navigator -> Implementation -> Run Implementation
```

Implementation 是把综合后的逻辑放进具体 FPGA 资源，并做布局布线。

成功标准：

- 没有 error；
- timing 不应有严重失败；
- 没有未约束或关键 IO 错误。

如果失败：

- 先不要改 RTL；
- 读报错；
- 判断是 timing、约束、资源、还是 top 连接问题；
- 生成 `CORRECTION_xxx.md` 再修正。

## 6. Generate Bitstream

操作：

```text
Flow Navigator -> Program and Debug -> Generate Bitstream
```

成功后会生成 `.bit` 文件。后续如何加载到 Red Pitaya，需要按当前工程已有流程或板卡 SOP 操作。

注意：

- 每次改 `LASER_LOCK_OUTPUT_MODE` 都要重新综合、实现、生成 bitstream；
- `OUTPUT_MODE` 是编译时参数，不是上板后按钮；
- bitstream 文件名和版本要记录清楚，例如 `v1ab_OUTPUT_MODE0` 或 `v1ab_OUTPUT_MODE1`。

## 7. 常见 Vivado 错误

| 错误 | 常见原因 | 先检查什么 |
|---|---|---|
| `module not found` | 文件没有加入 `Design Sources` | Add Sources 是否包含 `.sv` |
| `already declared` | 同名模块或信号重复定义 | 是否添加了两个不同路径的同名文件 |
| `syntax error near logic` | 文件未按 SystemVerilog 解析 | 文件类型是否识别为 SystemVerilog |
| `top module not found` | top 设置错误 | top 是否为 `red_pitaya_top` |
| `file not in project` | 只复制到目录，没有加入工程 | `Sources` 列表 |
| SystemVerilog 识别问题 | `.sv` 文件被当成 Verilog | 文件属性或 Vivado 语言设置 |

处理原则：

```text
先看 Sources
再看 top
再看报错行
最后才改代码
```

不要一看到 Vivado 报错就开始大改 RTL。很多错误只是文件没加进工程。
