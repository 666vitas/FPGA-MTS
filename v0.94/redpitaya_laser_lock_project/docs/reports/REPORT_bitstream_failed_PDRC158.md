# REPORT bitstream failed PDRC-158

## 0. 本报告作用

本报告记录当前 Vivado bitstream 生成失败的问题，便于后续排查和避免误判方向。

## 1. 当前状态

当前 `synthesis` 已通过。

说明：RTL 至少已经通过综合阶段，Vivado 可以把当前设计翻译成 FPGA 逻辑网表。

## 2. 失败阶段

当前失败发生在 bitstream 生成阶段。

也就是说，问题不是发生在最早的语法解析或 synthesis 阶段，而是在实现后生成 bitstream 前后的 DRC 检查中暴露。

## 3. 失败原因

Vivado 报告的失败原因是：

```text
DRC PDRC-158 Routing mux contention
```

该错误表示布线资源或 mux 选择存在冲突。当前错误更像是 FPGA 实现/布线/器件资源层面的 DRC 问题，而不是普通 SystemVerilog 语法错误。

## 4. 错误集中位置

错误集中在：

```text
ILOGIC_X0Y*
```

`ILOGIC` 通常与 FPGA 输入侧 I/O logic 资源相关。当前记录只说明错误集中区域，不直接推断具体根因。

## 5. 当前判断

当前判断：

```text
不优先怀疑 laser_lock_core 逻辑。
```

原因：

- synthesis 已通过；
- 当前错误是 `PDRC-158 Routing mux contention`；
- 错误集中在 `ILOGIC_X0Y*`；
- `laser_lock_core` 当前 v1ab 逻辑很简单，主要是 `pd_i/ref_i` passthrough 和输出保护。

这并不等于 `laser_lock_core` 一定无关，只是排查优先级不应先放在继续改 MTS RTL 上。

## 6. 下一步排查顺序

建议按以下顺序排查：

1. `Reset Runs` 后重跑。

```text
Reset Runs
Run Synthesis
Run Implementation
Generate Bitstream
```

2. 如果仍然失败，切换到官方干净原版 baseline：

```text
E:\new\fpga_lock\v94\guanfang-v0.94\v0.94
```

3. 跑官方 `guanfang-v0.94` baseline，比较 baseline 是否也失败。

判断逻辑：

- 如果官方 baseline 也出现类似 `PDRC-158`，优先怀疑工程环境、Vivado run 状态、器件/约束/官方工程兼容问题；
- 如果官方 baseline 通过，而当前开发工程失败，再回头比较当前 `v0.94` 与官方 baseline 的 top、约束、工程设置和新增 RTL 集成差异。

## 7. 明确禁止

在该问题没有定位前，明确禁止：

- 不要继续写 `v1c_mixer`；
- 不要修改 MTS RTL；
- 不要接板子；
- 不要接 `D2-125`。

当前优先任务不是增加功能，而是确认当前 bitstream 失败是否来自 Vivado run 状态、官方 baseline、工程差异或真实设计冲突。
