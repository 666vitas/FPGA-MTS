# Linien GUI 与 FPGA-MTS FIRST_LOCK GUI 分析

状态：`[CODE INSPECTED]`
结论：当前“GUI 位置不等于示波器位置”主要不是网络把 CH3 和 CH4 错开，而是 GUI 显示的是同拍 FPGA 内部数字量，示波器看到的是 DAC 后、负载后、PZT/激光响应后的物理量。网络和刷新会造成整帧陈旧，但不会改变当前 capture 内各通道的共同 sample index。

## 1. 数据显示：真实 ADC、内部计算值与物理测量

### Linien 显示什么

Linien 的 scope buffer 可选择 FPGA 内部 signal tap。未锁定时通常返回：

- `error_signal_1`：FastChain A 的 demodulated/filtered 数字信号；
- `error_signal_2` 或 `monitor_signal`：另一路 demodulated 信号或 ADC monitor；
- quadrature signals：FPGA 计算的 Q 分量；
- `slow_control_signal`：CSR 读取的慢控制数字值。

锁定时通常返回：

- `error_signal`：combined error 的 FPGA 数字值；
- `control_signal`：送往所选 fast output 的 FPGA 数字控制值；
- 可选 `monitor_signal` 和 slow control readback。

这些量并不全是“ADC 引脚的原始测量”。Linien 通过清晰的 signal routing 和 locked/unlocked 显示语义降低误判，但 control signal 仍是 DAC 前数字量，不是负载节点的独立电压测量。

### FPGA-MTS 当前显示什么

| GUI 通道 | RTL 来源 | 是真实 ADC 吗 | 能证明什么 | 不能证明什么 |
|---|---|---:|---|---|
| CH1 PD | `adc_dat[0]` | 是，ADC 数字样本 | IN1 上的 PD 波形 | 光路外部绝对标定、探测器未失真 |
| CH2 REF | `adc_dat[1]` | 是，ADC 数字样本 | IN2 上的 REF 波形 | REF 相位最优、外部幅度绝对准确 |
| CH3 ERROR | `laser_error` | 否，FPGA mixer+LPF 结果 | servo 实际使用的数字 error | OUT1 示波器电压、模拟链相位或 PZT 位置 |
| CH4 OUT2 | `selected_out2` | 否，DAC 前 command | FPGA 实际命令 count、scan/lock 切换 | DAC 后电压、PZT 端电压、PZT 位移、激光频率 |

当前 GUI 多处写成 `OUT2/PZT command voltage (calibrated estimate)`，虽已包含 estimate 警告，仍容易把“PZT command”误读为“PZT 实际电压/位置”。FIRST_LOCK 页面应以 counts 为主，并把三种量严格分开：

1. `FPGA OUT2 command counts`：CH4 / `selected_out2`，FPGA 内部真值。
2. `Estimated unloaded/previous-calibration voltage`：软件按 gain/offset 换算，必须注明校准条件和日期。
3. `Measured PZT-node voltage`：只有示波器在明确 probe、coupling、termination 和 PZT 负载下的读数才可使用这个名字。

## 2. 波形刷新、buffer、sampling 与 latency

### Linien 的处理

Linien 在板端 `AcquisitionService` 中持续轮询 triggered scope：

- sweep 状态按 sweep trigger 采集并使用 decimation；
- lock 状态等待 FPGA `lock_running` 确认后采集 error/control；
- pause 后恢复时重新 arm，并在 sweep 下丢弃第一帧，避免半帧数据；
- 数据带 hash/uuid，GUI 只接收新帧；
- GUI 对绘图做 rate limit，但 autolock selection 时暂停画面并缓存最近 spectra。

这使“显示刷新率”和“FPGA 采样率”明确分离。GUI 慢只意味着晚看到一帧，不参与 realtime lock。

### FPGA-MTS 的处理

FPGA-MTS 的 `custom_debug_capture` 在同一个 `adc_clk` 下，同一写地址、同一 decimation tick 同时写 CH1/CH2/CH3/CH4，因此帧内对齐结构正确。Host 通过 SSH 执行 `/dev/mem` helper：启动 capture、等待 done、逐索引读取四通道，再由 GUI 一次性绘图。

关键 latency 分类：

| 延迟 | 是否让同一帧 CH3/CH4 索引错开 | 实际影响 |
|---|---:|---|
| ADC/FPGA pipeline | 可能形成固定物理相位差，但 capture 索引仍共同 | CH3 是 mixer+LPF 后 error，天然落后于 ADC/plant |
| DAC pipeline / analog output | GUI CH4 不包含这段 | 示波器 OUT2 相对 command 有固定延迟和增益/offset |
| PZT + laser response | GUI CH4 不包含这段 | 同一 command 在 rising/falling 可能对应不同频率 |
| 网络/SSH | 否 | 决定何时开始 capture、何时看到整帧 |
| GUI refresh | 否 | Live Capture 可能显示 0.5–2 s 以前完成的帧 |
| 软件 x-axis mapping | 当前按 `index * decimation / 125 MHz`，结构正确 | 若实际 scan frequency 与请求值略有差异，时间标签与预期周期会有小误差 |

当前 Lock View 把 capture window 配成约 1.0 个扫描周期。它能选点，但不利于同时比较重复的 rising/falling crossing，也容易让目标靠近 frame edge。active spec 要求至少 1.2 周期、推荐 1.5–2 周期。建议最小改为 2 周期，并在 frame header 显示：`capture_id/config_generation`、capture 完成时间、scan direction、command counts。

### GUI 位置不等于示波器 cursor 的最可能解释

按优先级：

1. **比较对象不同**：GUI CH4 是 DAC 前数字 command；示波器是模拟 OUT2 或 PZT 节点。
2. **扫描方向 + PZT/激光迟滞**：同一 OUT2 command 在 rising/falling 不必对应同一谱线位置。
3. **探头/终端/负载标定不同**：`OUT2_CENTER_GAIN=1.13`、offset `0.009 V`、amplitude gain `1.18` 不是 loaded-PZT 节点的当前校准。
4. **plant 与 LPF 动态滞后**：error zero crossing 是整个 PZT/laser/photodetector/mixer/LPF 链的响应，不是 command 的瞬时函数。
5. **帧陈旧**：Live GUI 刷新和 SSH 往返可让用户拿旧帧与当前示波器比较。
6. **scan frequency 小误差**：RTL ramp 每个 position update 有候选/提交两拍，host 按理想 `update_div` 计算频率；影响通常远小于迟滞和标定。
7. **frame 内软件索引错位**：当前证据不支持；四通道共用写地址和 decimation tick。

## 3. Lock Point 选择

Linien autolock 要求用户框选包含目标线两侧 extrema 的区域，server 从 spectrum 中确定中心和 slope；simple/robust 算法最终都把“何时切 lock”的敏感动作放到 FPGA sweep 时基上。manual lock 则要求用户先用 zoom/position 居中、选择 rising/falling slope，再启锁。

FPGA-MTS 当前流程是：

```text
SCAN -> aligned capture -> PICK LOCK POINT
-> host 在点击附近寻找合格 CH3 zero crossing
-> CONFIRM（绑定 capture/config generation）
-> ARM VALIDATE
-> 用户核对 crossing 事件
-> ARM BASIC LOCK
-> FPGA 在同方向、同 guard、H/N crossing 命中时捕获实际 OUT2 bias
-> FPGA Kp soft-start -> supervisor
```

这个流程比“点击像素后立即写静态 bias”更适合真实实验，原因是 L1 不把旧 capture 中的 CH4 count 直接当最终 bias，而是在未来真实 crossing 拍捕获当时的 `selected_out2`。`PICK -> CONFIRM` 两步应保留；`ARM VALIDATE` 在第一次上板时也应保留，不能被一个“万能 BASIC LOCK”按钮隐藏。

不建议用手动 bias trim 修复 GUI/示波器差异。它改变 guard center，却不能消除 PZT 迟滞；正常路径应依赖同方向 realtime crossing 和实际 bias capture。HOLD/trim 只保留 Engineer diagnostic。

## 4. 参数设计

Linien 对用户公开的参数很多：P/I/D、offset、sweep center/amplitude、output routing/limit、filter、demod phase 等。其完整性服务于通用产品，不代表 FIRST_LOCK 需要全部暴露。

FPGA-MTS 首次锁定页面只应让用户明确确认：

- PZT safe min/max（基于真实 loaded-node 测量）；
- scan center/amplitude/frequency（或由 safe range 派生并显示只读实际值）；
- target（capture + direction + crossing）；
- `Kp=0` for VALIDATE/H3，用户批准后仅 `Kp=4`；
- polarity suggestion + 用户确认；
- correction limit 和 absolute limit（建议只读显示派生值，Engineer 模式可改）。

应隐藏或锁定：Ki、PI_LOCK、automatic relock、manual `CAPTURE_LOCK_POINT`、manual APPLY P 8/16/32、raw CSR/base address、manual lock bias、daisy、REF debug decimation。它们不应出现在 FIRST_LOCK 操作主路径。

## 5. GUI 最小修改建议

### 主页面保留

- `SAFE`：始终可见、红色、显示是否 readback confirmed。
- `SCAN`：显式进入扫描，不用 `BASIC LOCK` 一键隐式执行 SAFE/SCAN/CAPTURE。
- `CAPTURE / LIVE`：显示 frame age；选点时冻结当前 frame。
- `PICK LOCK POINT` + `CONFIRM`：保留人工确认。
- `ARM VALIDATE`：第一次硬件 gate 必需。
- `LOCK (ARM ACTIVE, Kp=0 or 4)`：名称直接表达命令，不写“自动锁定”。
- `ABORT / SAFE`：与 SAFE 等价的紧急退出。

### 主页面隐藏到 Engineer Details

- HOLD、Capture Bias、LOCK HERE、manual APPLY P；
- Kp 8/16/32、Ki、PI_LOCK；
- base address、step-counts、capture decimation、raw limits；
- bias trim；
- SCPI ASG controls（custom bitstream 下不会驱动实际 OUT2）。

### 必须增加或强化的显示

- `Frame age`、capture id、config generation、scan direction；
- CH4 标题改为 `FPGA OUT2 command (counts; DAC-pre)`；
- 另设只读 `estimated voltage (not measured)`；
- 允许人工填入 `scope measured PZT-node V`，不得由软件自动冒充；
- `MODE/ENABLE/Kp effective/polarity/saturation/LOCK_BIAS/error setpoint` readback；
- ARM VALIDATE 的 event direction、event OUT2、event ERROR、generation；
- 明确 `D2-125 Main Servo=current fast loop ON`、`D2-125 AUX physically disconnected` 检查项。

## 6. 结论

当前选点算法和 L1 FPGA crossing 路线适合 FIRST_LOCK；主要风险是用户界面仍同时保留太多 legacy/advanced 控件，并把 CH4 command 和 physical PZT node 放在相近措辞中。最小正确方向不是重做 GUI，而是：主路径只保留 `SAFE/SCAN/CAPTURE/PICK/CONFIRM/VALIDATE/LOCK`，把 counts、estimate、measured 三类量彻底分栏，并让选点时 frame 冻结且显示 age。
