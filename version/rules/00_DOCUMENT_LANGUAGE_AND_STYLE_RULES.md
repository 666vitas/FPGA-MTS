# 文档语言与风格规则

## 1. 文档语言规则

后续 Codex 生成或修改的项目文档，默认必须使用中文。

适用范围包括：

- `version/**/*.md`
- `docs/**/*.md`
- `software/**/*.md`
- `GPT_README.md`
- 实验 SOP
- 开发路线图
- 阶段任务说明
- 代码审查报告
- 实验记录
- 上位机说明文档
- 给用户看的 Markdown 总结

## 2. 可以保留英文的内容

中文文档不等于把所有英文都翻译掉。代码相关内容必须保留原名。

以下内容不要翻译：

- 文件路径，例如 `v0.94/rtl/laser_lock_core.sv`
- 模块名，例如 `mixer_core`、`lpf_core`、`pi_controller_seq`
- 端口名，例如 `error_o`、`control_o`、`adc_dat_i`
- 寄存器名，例如 `OUT2_MODE`、`REG_KP`、`REG_KI`
- Vivado 报告术语，例如 `WNS`、`TNS`、`Failing Endpoints`
- 命令行命令，例如 `git status`、`grep`、`vivado`
- 英文论文题目和引用

必须保留原名的常见项目术语包括：

```text
mixer_core
lpf_core
output_protect
pi_controller
pi_controller_seq
laser_lock_core
red_pitaya_top
OUT1
OUT2
IN1
IN2
error_o
control_o
CONTROL_PATH_MODE
OUTPUT_MODE
WNS
TNS
Vivado
bitstream
```

## 3. 推荐写法

推荐使用：

```text
中文解释 + 英文技术名词保留
```

推荐示例：

```text
OUT1 是 FPGA mixer + LPF 后的误差信号观察输出。
OUT2 是 FPGA control candidate / sequential PI candidate，目前只允许接示波器。
```

不要写成：

```text
OUT1 is the FPGA mixer+LPF error observation output.
OUT2 is the FPGA control candidate.
```

## 4. 文档风格

面向用户的项目文档必须写给小白实验用户看，不能只写抽象架构，也不能只堆英文缩写。

每个实验阶段必须写清：

- 目标
- 接线
- 正常现象
- 停止条件
- 通过标准
- 是否允许烧录
- 是否允许接激光器
- 是否允许接 Scan/PZT
- 保存哪些数据

同时必须明确：

- 哪些操作允许
- 哪些操作禁止
- 当前阶段是否能锁定
- 当前 OUT2 是否只能接示波器

## 5. 当前项目默认安全写法

默认情况下，面向用户的文档必须明确写出：

```text
当前 OUT2 只允许接示波器。
当前不能声称 FPGA 已经完整替代 D2-125。
当前不能声称 FPGA 已经独立真实锁定激光。
涉及 Vivado 的任务只能写用户手动操作 SOP，Codex 不自动运行 Vivado。
```
