# 任务路由

## 通用流程

1. 读取 `STATUS.md` 和 `CURRENT_REVIEW_MANIFEST.md`，再读取入口、规则和任务文件。
2. 运行只读状态检查，记录 branch/HEAD/工作区改动和冲突。
3. 指定一个主类别和一个最小可验证目标。
4. 列出允许修改文件和明确不修改项。
5. 定位真实调用链，实施最小修改。
6. 按验证矩阵验证，报告未运行项和证据等级。
7. 使用交接模板输出中文结果。

## 分类检查

### Repository review

输出当前读取文件、主线、代码直接事实、文档/实验事实、不能确认项、旧污染、风险和最小安全动作。不要用历史文件补全缺失证据。

### FPGA RTL

检查 14-bit signed、乘法位宽、算术右移、截断/饱和、pipeline latency、reset、MODE、SAFE 默认值、OUT2 最终来源、DAC 限幅、仿真同步和 `.xpr` source set。没有 Vivado 输出不能声称 synthesis/timing。

### Register protocol

同步阅读 `custom_register_bank.sv`、`custom_fpga_scan_control.py`、backend、workers、tests、README/STATUS/log。核对地址、读写语义、`MAGIC`、`VERSION`、默认值、signed 扩展、readback、向后兼容和 bitstream 身份。

### Python host / GUI

同步检查 `main_window.py`、backend、workers、scan control、`waveform_plot.py`、tests 和上位机日志。保持 `capture_in_flight` 防重入、完成后更新再 single-shot、Stop 后不再 capture、异常停止 Live、不显示假波形、显示控制不写 FPGA。

### Vivado

只检查 `.xpr`、source set、脚本、报告和日志。区分 synthesis、implementation、timing、bitstream、烧录和上板验证；默认不执行 Vivado、生成 bitstream 或烧录。

### Experiment preparation

必须给出接线、前置条件、SAFE 起点、参数、操作顺序、示波器观察、PASS、FAIL、记录项和停止条件。涉及 OUT2/PZT 时加载 `experiment-safety.md`。

### Documentation

STATUS 顶部保持当前快照，DEVELOPMENT_LOG 只追加历史；代码完成写成等待验证，不写成硬件通过；用户明确禁止修改状态/日志时不改并报告冲突。

### AI / automatic optimization

只有用户明确授权才进入。确认基础 P_LOCK、稳定采集、日志格式、指标、标签和安全 fallback；先离线分析/建议，不能绕过限幅和 SAFE，不能进入 125 MHz 快速环。
