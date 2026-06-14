# Red Pitaya 硬件速查卡

## 0. 本文件作用

本文件告诉你 Red Pitaya STEMlab 125-14 这块板子你用得着的接口都在哪、怎么接、什么不能接。

## 1. 前面板接口（慢速 I/O 那面）

Red Pitaya 有两排接口。你主要用高速那面（SMA 接口那面）：

```
  [IN1]  [IN2]    [OUT1]  [OUT2]
   SMA    SMA       SMA     SMA
```

| 接口 | 你的用法 | 对应 FPGA 信号 |
|---|---|---|
| IN1 | 接 PD 信号 | `adc_dat[0]` |
| IN2 | 接外部 4.6 MHz REF（已衰减） | `adc_dat[1]` |
| OUT1 | 接示波器，输出 FPGA error signal | DAC A 通道 |
| OUT2 | 暂不使用 | DAC B 通道 |

## 2. 输入安全参数

**这是最重要的部分。违反会损坏板子。**

| 参数 | 值 |
|---|---|
| 高速 ADC 输入量程（IN1/IN2） | ±1 V（差分输入范围，单端使用时参考此值） |
| 输入绝对最大额定值 | 查阅 Red Pitaya 官方硬件手册 |
| 输入阻抗 | 1 MΩ |
| ADC 分辨率 | 14 bit |
| ADC 采样率 | 125 MSPS |

安全规则：

- **任何输入信号先用示波器确认幅度**，再接入 IN1/IN2
- **4.6 MHz REF 必须先衰减**到 ±1 V 以内再接入 IN2
- **6.32 Vpp 的原模拟 mixer 参考信号绝对不能直接接 IN2**
- **EOM 驱动信号（约 8.93 Vpp）绝对不能接 Red Pitaya**
- 不确定时，先衰减、再量、再接

## 3. 输出参数

| 参数 | 值 |
|---|---|
| 高速 DAC 输出量程（OUT1/OUT2） | ±1 V |
| DAC 分辨率 | 14 bit |
| DAC 采样率 | 125 MSPS |

输出可以直接用 SMA-BNC 线接示波器。

## 4. 接线实物

你需要这些线：

| 线缆 | 用途 |
|---|---|
| SMA-SMA 或 SMA-BNC 线 | IN1 接 PD、IN2 接 REF、OUT1 接示波器 |
| BNC T 型接头 | 把信号分两路（一路进 Red Pitaya，一路进示波器监视） |
| 信号衰减器 | 如果 REF 或 PD 信号太大，串在输入前面 |

建议接线方式（以测试 IN1 为例）：

```
信号发生器 OUT -> BNC T 接头 -> 示波器 CH2（监视）
                  |
                  -> SMA 线 -> Red Pitaya IN1
Red Pitaya OUT1 -> SMA-BNC 线 -> 示波器 CH1
```

这样示波器同时看到输入和输出，方便对比。

## 5. 上电和加载 Bitstream

### 上电

1. 用 Micro-USB 或配套电源给 Red Pitaya 供电
2. 网线连接 Red Pitaya 和电脑（用于 SSH 和 bitstream 加载）
3. LED 亮起表示启动中

### 加载 Bitstream

生成 `.bit` 文件后，通常通过网络加载：

```bash
# 把 .bit 转成 .bit.bin
# 把 .bit.bin 复制到 Red Pitaya
scp red_pitaya_top.bit.bin root@<redpitaya-ip>:/root/
# SSH 进去加载
ssh root@<redpitaya-ip>
cat /root/red_pitaya_top.bit.bin > /dev/xdevcfg
```

注意：具体加载方式因 Red Pitaya 系统版本不同可能有差异。第一次操作时先查官方文档。

## 6. 不要做的事

| 禁止 | 后果 |
|---|---|
| 把 6.32 Vpp REF 直接接 IN2 | 输入超范围，可能削顶或损坏 |
| 把 EOM 驱动（8.93 Vpp）接任何 Red Pitaya 接口 | 电压远超承受范围，可能损坏 |
| 热插拔 SMA 线 | 可能产生瞬间高压 |
| 在没有接入示波器的情况下直接接 D2-125 | 不知道 OUT1 实际输出是否安全 |
| 修改官方 top 的 ODDR/PLL/PS/XDC | 破坏板级时序和稳定性 |

## 7. 你现在只需要记住

```
先示波器 → 再接入
先衰减 → 再接入
不接 D2-125 → 直到示波器确认安全
```
