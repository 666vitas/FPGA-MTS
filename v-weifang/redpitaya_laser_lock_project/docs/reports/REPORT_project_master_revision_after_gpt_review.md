# REPORT project master revision after GPT review

## 0. 本报告作用

本报告记录根据 GPT 审查意见，对 `docs\project_master` 中主线文档进行的小幅修订。

本次没有重写全部内容，没有删除已有内容，只做增量补充和局部结构调整。

## 1. 修改了哪些文件

本次修改了以下文件：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\01_CURRENT_STATUS_SUMMARY.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\02_VERSION_ROADMAP_V1_TO_AI.md
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\project_master\03_VERSION_EXECUTION_CHECKLISTS.md
```

新增本报告：

```text
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\docs\reports\REPORT_project_master_revision_after_gpt_review.md
```

## 2. 具体修订内容

`01_CURRENT_STATUS_SUMMARY.md`：

- 新增 `## 6. 当前马上执行的操作`；
- 明确当前立即执行顺序是确认 Vivado Sources、确认 `USE_LASER_LOCK_CORE = 1'b1`、确认 `LASER_LOCK_OUTPUT_MODE = 0`、运行 synthesis / implementation / bitstream；
- 明确上板只测 `IN1 -> OUT1`；
- 明确不接 `D2-125`、不接真实 `PD`、不接激光器反馈。

`02_VERSION_ROADMAP_V1_TO_AI.md`：

- 在 `v1c_mixer_only` 中补充第一次上板可先用 `100 kHz / 100 kHz` 较低频同频信号确认 mixer 链路，再切到 `4.6 MHz`；
- 在 `v1f_bpf_enable` 中补充 BPF 系数必须根据 ADC 采样率、`4.6 MHz` 中心频率、带宽和定点位宽计算；
- 明确不能直接照搬模拟滤波器参数。

`03_VERSION_EXECUTION_CHECKLISTS.md`：

- 将原 `v1ab 执行清单` 拆成：

```text
v1ab-1：Vivado 编译检查
v1ab-2：上板测试 IN1 -> OUT1
v1ab-3：上板测试 IN2 -> OUT1
```

- 增加 Vivado 报错时应发给 GPT 的信息；
- 明确 `v1ab-3` 的前提是 `v1ab-2` 已通过；
- 明确 `OUTPUT_MODE=1` 后需要重新 synthesis / implementation / bitstream。

## 3. 没有修改 RTL

本次没有修改任何 RTL。

没有修改：

```text
E:\new\fpga_lock\v94\v0.94\rtl
E:\new\fpga_lock\v94\v0.94\redpitaya_laser_lock_project\rtl
```

## 4. 没有运行 Vivado

本次没有运行 Vivado。

没有执行：

```text
Run Synthesis
Run Implementation
Generate Bitstream
```

也没有修改 Vivado 工程。

## 5. 下一步建议

下一步建议进入：

```text
v1ab-1：Vivado 编译检查
```

具体顺序：

1. 打开 Vivado `.xpr`；
2. 确认 `Design Sources` 中已有 `laser_lock_core.sv` 和 `output_protect.sv`；
3. 确认 `i_laser_lock_core` 出现在 `red_pitaya_top` 层级下；
4. 确认 `USE_LASER_LOCK_CORE = 1'b1`；
5. 确认 `LASER_LOCK_OUTPUT_MODE = 0`；
6. `Run Synthesis`；
7. `Run Implementation`；
8. `Generate Bitstream`；
9. 通过后再进入 `v1ab-2：上板测试 IN1 -> OUT1`。
