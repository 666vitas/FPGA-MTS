# v3REG-0 P0-1 MAGIC 预校验修复记录

日期：2026-07-05

## 修复目标

修复 Claude 审查指出的 P0-1：`custom_fpga_scan_control.py` 在 `safe` 和 `scan` 写寄存器前缺少 `MAGIC` 预校验。

## 修复内容

修改文件：

```text
software/redpitaya_lock_host/scripts/custom_fpga_scan_control.py
```

远端 `REMOTE_HELPER` 新增：

```text
read_magic(regs)
require_magic(regs)
```

`safe` 执行顺序：

```text
打开 RegisterWindow
-> require_magic()
-> 写 ENABLE=0
-> 写 MODE=0
-> 打印 status
```

`scan` 执行顺序：

```text
打开 RegisterWindow
-> require_magic()
-> 写 ENABLE=0
-> 写 SCAN_OFFSET
-> 写 SCAN_AMP
-> 写 SCAN_STEP
-> 写 SCAN_UPDATE_DIV
-> 写 OUT2_LIMIT
-> 写 MODE=1
-> 写 ENABLE=1
-> 打印 status
```

`status` 仍然只读，不写寄存器。

## MAGIC 不匹配行为

如果实际读取值不是 `0x4D545330`：

```text
1. 打印清楚错误信息；
2. 显示实际 magic；
3. 显示期望 magic 0x4D545330；
4. 提示可能原因：
   - old bitstream is loaded
   - --base-addr is wrong
   - sys[6] is not connected to custom_register_bank
5. 立即非零退出；
6. 不写 MODE / ENABLE / SCAN_OFFSET / SCAN_AMP / SCAN_STEP / SCAN_UPDATE_DIV / OUT2_LIMIT。
```

## 本次未做

```text
未修改 RTL。
未运行 Vivado synthesis / implementation。
未生成 bitstream / bin。
未烧录 Red Pitaya。
未连接 Red Pitaya 执行真实 safe / scan。
未进入 HOLD / P_LOCK / PI_LOCK / AI / 自动锁定。
```

## 用户下一步

用户仍需手动完成：

```text
1. Vivado synthesis / implementation；
2. timing 通过后生成 bitstream；
3. 烧录 Red Pitaya；
4. 只接 OUT2 到示波器；
5. 先运行 status，确认 MAGIC=0x4D545330；
6. 再运行 safe / scan 做 OUT2 示波器验证；
7. 不接 Scan/PZT、激光器、D2-125 Servo Output、D2-125 Aux Output。
```

