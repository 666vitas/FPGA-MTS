"""Minimal SSH client for the v3REG-0 custom FPGA scan registers.

This script does not use SCPI and does not start redpitaya_scpi. It sends a
small Python /dev/mem helper to the Red Pitaya over SSH and executes it there.
Run it only after the matching custom FPGA bitstream has been manually loaded.
"""

from __future__ import annotations

import argparse
import base64
import json
import shlex
import subprocess
import sys
import textwrap
from dataclasses import dataclass


COUNTS_PER_VOLT = 8191.0
DEFAULT_CLK_HZ = 125_000_000.0
DEFAULT_BASE_ADDR = 0x4060_0000

REGISTERS = {
    "MAGIC": 0x00,
    "VERSION": 0x04,
    "MODE": 0x08,
    "ENABLE": 0x0C,
    "SCAN_OFFSET": 0x10,
    "SCAN_AMP": 0x14,
    "SCAN_STEP": 0x18,
    "SCAN_UPDATE_DIV": 0x1C,
    "OUT2_LIMIT": 0x20,
    "STATUS": 0x24,
    "OUT2_MONITOR": 0x28,
    "HOLD_VALUE": 0x2C,
    "KP": 0x30,
    "POLARITY": 0x34,
    "LOCK_BIAS": 0x38,
    "LOCK_LIMIT": 0x3C,
    "ERROR_MONITOR": 0x40,
    "CONTROL_MONITOR": 0x44,
    "KI": 0x48,
    "INTEGRAL_RESET": 0x4C,
    "LOCK_CORRECTION_LIMIT": 0x50,
    "CAPTURE_CTRL": 0x80,
    "CAPTURE_STATUS": 0x84,
    "CAPTURE_DECIMATION": 0x88,
    "CAPTURE_LENGTH": 0x8C,
    "CAPTURE_READ_INDEX": 0x90,
    "CAPTURE_DATA_CH1": 0x94,
    "CAPTURE_DATA_CH2": 0x98,
    "CAPTURE_DATA_CH3": 0x9C,
    "CAPTURE_DATA_CH4": 0xA0,
}


REMOTE_HELPER = r"""
import argparse
import json
import mmap
import os
import struct
import sys
import time

REGISTERS = {
    "MAGIC": 0x00,
    "VERSION": 0x04,
    "MODE": 0x08,
    "ENABLE": 0x0C,
    "SCAN_OFFSET": 0x10,
    "SCAN_AMP": 0x14,
    "SCAN_STEP": 0x18,
    "SCAN_UPDATE_DIV": 0x1C,
    "OUT2_LIMIT": 0x20,
    "STATUS": 0x24,
    "OUT2_MONITOR": 0x28,
    "HOLD_VALUE": 0x2C,
    "KP": 0x30,
    "POLARITY": 0x34,
    "LOCK_BIAS": 0x38,
    "LOCK_LIMIT": 0x3C,
    "ERROR_MONITOR": 0x40,
    "CONTROL_MONITOR": 0x44,
    "KI": 0x48,
    "INTEGRAL_RESET": 0x4C,
    "LOCK_CORRECTION_LIMIT": 0x50,
    "CAPTURE_CTRL": 0x80,
    "CAPTURE_STATUS": 0x84,
    "CAPTURE_DECIMATION": 0x88,
    "CAPTURE_LENGTH": 0x8C,
    "CAPTURE_READ_INDEX": 0x90,
    "CAPTURE_DATA_CH1": 0x94,
    "CAPTURE_DATA_CH2": 0x98,
    "CAPTURE_DATA_CH3": 0x9C,
    "CAPTURE_DATA_CH4": 0xA0,
}

EXPECTED_MAGIC = 0x4D545330
PROBE_BASE_ADDRS = [
    0x40000000,
    0x40100000,
    0x40200000,
    0x40300000,
    0x40400000,
    0x40500000,
    0x40600000,
    0x40700000,
]


def to_signed14(value):
    value &= 0x3FFF
    if value & 0x2000:
        value -= 0x4000
    return value


def pack32(value):
    return struct.pack("<I", value & 0xFFFFFFFF)


def unpack32(raw):
    return struct.unpack("<I", raw)[0]


class RegisterWindow:
    def __init__(self, base_addr):
        self.base_addr = int(base_addr)
        self.page_size = mmap.PAGESIZE
        self.page_base = self.base_addr & ~(self.page_size - 1)
        self.page_offset = self.base_addr - self.page_base
        self.fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mem = mmap.mmap(
            self.fd,
            self.page_size,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=self.page_base,
        )

    def close(self):
        self.mem.close()
        os.close(self.fd)

    def read(self, offset):
        pos = self.page_offset + offset
        self.mem.seek(pos)
        return unpack32(self.mem.read(4))

    def write(self, offset, value):
        pos = self.page_offset + offset
        self.mem.seek(pos)
        self.mem.write(pack32(value))
        # Do not call mmap.flush() for /dev/mem MMIO registers.
        # On some Red Pitaya Linux kernels, mmap.flush() on /dev/mem raises
        # OSError: [Errno 22] Invalid argument. MMIO writes are posted by the
        # mapped store itself; a follow-up read/status is used for verification.


def read_magic(regs):
    return regs.read(REGISTERS["MAGIC"])


def require_magic(regs):
    magic = read_magic(regs)
    if magic == EXPECTED_MAGIC:
        return magic

    print(
        "ERROR: custom FPGA register MAGIC mismatch.\n"
        f"  actual magic:   0x{magic:08X}\n"
        f"  expected magic: 0x{EXPECTED_MAGIC:08X}\n"
        "No registers were written.\n"
        "Possible causes:\n"
        "  - old bitstream is loaded\n"
        "  - --base-addr is wrong\n"
        "  - sys[6] is not connected to custom_register_bank",
        file=sys.stderr,
    )
    raise SystemExit(2)


def warn_missing_magic(magic):
    if magic == EXPECTED_MAGIC:
        return
    print(
        "WARNING: SSH connected and /dev/mem read completed, but custom_register_bank was not found.\n"
        f"  actual magic:   0x{magic:08X}\n"
        f"  expected magic: 0x{EXPECTED_MAGIC:08X}\n"
        "Do not run safe or scan yet.\n"
        "Possible causes:\n"
        "  - bitstream was not actually loaded\n"
        "  - an old bit file was loaded\n"
        "  - FPGA configuration was lost after Program Device or board reboot\n"
        "  - base address is different; run probe",
        file=sys.stderr,
    )


def read_status(regs):
    magic = regs.read(REGISTERS["MAGIC"])
    version = regs.read(REGISTERS["VERSION"])
    status = regs.read(REGISTERS["STATUS"])
    out2_raw = regs.read(REGISTERS["OUT2_MONITOR"])
    error_raw = regs.read(REGISTERS["ERROR_MONITOR"])
    control_raw = regs.read(REGISTERS["CONTROL_MONITOR"])
    return {
        "magic": f"0x{magic:08X}",
        "version": f"0x{version:08X}",
        "mode": regs.read(REGISTERS["MODE"]),
        "enable": regs.read(REGISTERS["ENABLE"]) & 1,
        "status_raw": f"0x{status:08X}",
        "enabled": bool(status & 1),
        "saturated": bool(status & 2),
        "out2_counts": to_signed14(out2_raw),
        "out2_volts": to_signed14(out2_raw) / 8191.0,
        "error_counts": to_signed14(error_raw),
        "error_volts": to_signed14(error_raw) / 8191.0,
        "control_counts": to_signed14(control_raw),
        "control_volts": to_signed14(control_raw) / 8191.0,
        "lock_correction_limit_counts": to_signed14(regs.read(REGISTERS["LOCK_CORRECTION_LIMIT"])),
    }


def capture_waveform(regs, length, decimation):
    length = max(1, min(4096, int(length)))
    decimation = max(1, int(decimation))
    regs.write(REGISTERS["CAPTURE_DECIMATION"], decimation)
    regs.write(REGISTERS["CAPTURE_LENGTH"], length)
    regs.write(REGISTERS["CAPTURE_CTRL"], 1)
    for _ in range(2000):
        status = regs.read(REGISTERS["CAPTURE_STATUS"])
        if status & 0x2:
            break
        time.sleep(0.002)
    status = regs.read(REGISTERS["CAPTURE_STATUS"])
    if not (status & 0x2):
        raise SystemExit("capture timeout: custom_debug_capture did not report done")
    points = []
    for index in range(length):
        regs.write(REGISTERS["CAPTURE_READ_INDEX"], index)
        points.append({
            "index": index,
            "ch1_counts": to_signed14(regs.read(REGISTERS["CAPTURE_DATA_CH1"])),
            "ch2_counts": to_signed14(regs.read(REGISTERS["CAPTURE_DATA_CH2"])),
            "ch3_counts": to_signed14(regs.read(REGISTERS["CAPTURE_DATA_CH3"])),
            "ch4_counts": to_signed14(regs.read(REGISTERS["CAPTURE_DATA_CH4"])),
        })
    return {
        "capture_status": f"0x{status:08X}",
        "capture_length": length,
        "capture_decimation": decimation,
        "ref_alias_warning": "4.6 MHz REF may alias when decimation is high.",
        "points": points,
    }


def sample_status_series(regs, sample_count, interval_s):
    samples = []
    for index in range(max(2, int(sample_count))):
        status = read_status(regs)
        status["sample_index"] = index
        samples.append(status)
        time.sleep(max(0.001, float(interval_s)))
    return samples


def select_zero_crossing(samples, threshold, edge_margin_counts):
    candidates = []
    threshold = max(1, int(threshold))
    edge_margin_counts = max(0, int(edge_margin_counts))
    for prev, cur in zip(samples, samples[1:]):
        prev_error = int(prev["error_counts"])
        cur_error = int(cur["error_counts"])
        prev_out2 = int(prev["out2_counts"])
        cur_out2 = int(cur["out2_counts"])
        crosses_down = prev_error > threshold and cur_error <= 0
        crosses_up = prev_error < -threshold and cur_error >= 0
        if not (crosses_down or crosses_up):
            continue
        if abs(cur_out2) >= (8191 - edge_margin_counts):
            continue
        delta_out2 = cur_out2 - prev_out2
        delta_error = cur_error - prev_error
        slope = 0.0 if delta_out2 == 0 else abs(float(delta_error) / float(delta_out2))
        candidates.append({
            "sample_index": cur["sample_index"],
            "out2_counts": cur_out2,
            "out2_volts": cur_out2 / 8191.0,
            "error_counts": cur_error,
            "slope_abs_d_error_d_out2": slope,
        })
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item["slope_abs_d_error_d_out2"], reverse=True)[0]


def run_auto_lock(regs, args):
    require_magic(regs)
    status = read_status(regs)
    if status["version"] != "0x00030000":
        raise SystemExit(f"VERSION mismatch: expected 0x00030000, got {status['version']}")
    if int(status["mode"]) != 1:
        raise SystemExit("AUTO LOCK requires MODE=1 SCAN first")
    if float(args.scan_freq_hz) > 1.0:
        print("WARNING: AUTO LOCK is safer at scan freq 0.2~1 Hz.", file=sys.stderr)

    samples = sample_status_series(regs, args.sample_count, args.sample_interval_s)
    zero = select_zero_crossing(samples, args.zero_threshold, args.edge_margin_counts)
    if zero is None:
        return {
            "auto_lock_state": "LOCK_FAILED",
            "abort_reason": "no qualifying error zero-crossing found",
            "sample_count": len(samples),
        }

    correction_limit = max(0, min(8191, int(args.correction_limit_counts)))
    regs.write(REGISTERS["ENABLE"], 0)
    regs.write(REGISTERS["LOCK_BIAS"], int(zero["out2_counts"]))
    regs.write(REGISTERS["LOCK_CORRECTION_LIMIT"], correction_limit)
    regs.write(REGISTERS["LOCK_LIMIT"], max(0, min(8191, int(args.lock_limit_counts))))
    regs.write(REGISTERS["KP"], 0)
    regs.write(REGISTERS["KI"], 0)
    regs.write(REGISTERS["POLARITY"], args.polarity)
    regs.write(REGISTERS["INTEGRAL_RESET"], 1)
    regs.write(REGISTERS["MODE"], 3)
    regs.write(REGISTERS["ENABLE"], 1)
    time.sleep(max(0.1, float(args.settle_s)))
    readback = read_status(regs)
    if int(readback["mode"]) != 3:
        regs.write(REGISTERS["KP"], 0)
        regs.write(REGISTERS["ENABLE"], 0)
        regs.write(REGISTERS["MODE"], 0)
        raise SystemExit("AUTO LOCK failed: MODE did not read back as 3")

    trend = []
    previous_abs_error = abs(int(readback["error_counts"]))
    for kp in (4, 8, 16, 32):
        regs.write(REGISTERS["KP"], kp)
        time.sleep(max(0.1, float(args.kp_step_s)))
        step_status = read_status(regs)
        abs_error = abs(int(step_status["error_counts"]))
        trend.append({
            "kp": kp,
            "abs_error_counts": abs_error,
            "out2_counts": int(step_status["out2_counts"]),
            "saturated": bool(step_status["saturated"]),
        })
        if step_status["saturated"] or abs(int(step_status["out2_counts"])) > int(args.abort_out2_counts):
            regs.write(REGISTERS["KP"], 0)
            regs.write(REGISTERS["ENABLE"], 0)
            regs.write(REGISTERS["MODE"], 0)
            return {
                "auto_lock_state": "LOCK_FAILED",
                "abort_reason": "saturated or OUT2 too close to limit; polarity may be wrong",
                "selected_zero_crossing": zero,
                "error_trend": trend,
            }
        if abs_error > max(previous_abs_error + int(args.error_growth_counts), int(previous_abs_error * 1.5)):
            regs.write(REGISTERS["KP"], 0)
            regs.write(REGISTERS["ENABLE"], 0)
            regs.write(REGISTERS["MODE"], 0)
            return {
                "auto_lock_state": "LOCK_FAILED",
                "abort_reason": "error increased during Kp ramp; polarity may be wrong",
                "selected_zero_crossing": zero,
                "error_trend": trend,
            }
        previous_abs_error = min(previous_abs_error, abs_error)

    final_status = read_status(regs)
    final_status.update({
        "auto_lock_state": "LOCK_HOLDING",
        "selected_zero_crossing": zero,
        "current_kp": 32,
        "correction_limit_counts": correction_limit,
        "error_trend": trend,
        "abort_reason": "",
    })
    return final_status


def probe_base_addresses():
    results = []
    found_base = None
    for base_addr in PROBE_BASE_ADDRS:
        item = {"base_addr": f"0x{base_addr:08X}"}
        try:
            regs = RegisterWindow(base_addr)
            try:
                magic = regs.read(REGISTERS["MAGIC"])
                version = regs.read(REGISTERS["VERSION"])
            finally:
                regs.close()
            item["magic"] = f"0x{magic:08X}"
            item["version"] = f"0x{version:08X}"
            item["match"] = magic == EXPECTED_MAGIC
            if magic == EXPECTED_MAGIC and found_base is None:
                found_base = base_addr
        except Exception as exc:
            item["error"] = str(exc)
            item["match"] = False
        results.append(item)

    message = "custom_register_bank not found; reload the current timing-clean bitstream or check the base address."
    if found_base is not None:
        message = f"custom_register_bank found; use --base-addr 0x{found_base:08X}"

    return {
        "expected_magic": f"0x{EXPECTED_MAGIC:08X}",
        "found_base_addr": None if found_base is None else f"0x{found_base:08X}",
        "message": message,
        "probes": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-addr", default="0x40600000")
    parser.add_argument("--op", choices=["safe", "scan", "hold", "p-lock", "pi-lock", "status", "probe", "capture", "auto-lock"], required=True)
    parser.add_argument("--offset-counts", type=int, default=6962)
    parser.add_argument("--amp-counts", type=int, default=410)
    parser.add_argument("--step-counts", type=int, default=1)
    parser.add_argument("--update-div", type=int, default=1524)
    parser.add_argument("--limit-counts", type=int, default=8191)
    parser.add_argument("--hold-counts", type=int, default=0)
    parser.add_argument("--kp", type=int, default=0)
    parser.add_argument("--ki", type=int, default=0)
    parser.add_argument("--polarity", type=int, choices=[0, 1], default=0)
    parser.add_argument("--lock-bias-counts", type=int, default=0)
    parser.add_argument("--lock-limit-counts", type=int, default=8191)
    parser.add_argument("--correction-limit-counts", type=int, default=128)
    parser.add_argument("--capture-length", type=int, default=2048)
    parser.add_argument("--capture-decimation", type=int, default=1024)
    parser.add_argument("--sample-count", type=int, default=256)
    parser.add_argument("--sample-interval-s", type=float, default=0.02)
    parser.add_argument("--zero-threshold", type=int, default=10)
    parser.add_argument("--edge-margin-counts", type=int, default=256)
    parser.add_argument("--scan-freq-hz", type=float, default=0.5)
    parser.add_argument("--settle-s", type=float, default=0.5)
    parser.add_argument("--kp-step-s", type=float, default=1.0)
    parser.add_argument("--abort-out2-counts", type=int, default=7800)
    parser.add_argument("--error-growth-counts", type=int, default=20)
    args = parser.parse_args()

    if args.op == "probe":
        print(json.dumps(probe_base_addresses(), indent=2, sort_keys=True))
        return

    regs = RegisterWindow(int(args.base_addr, 0))
    try:
        if args.op == "safe":
            require_magic(regs)
            regs.write(REGISTERS["ENABLE"], 0)
            regs.write(REGISTERS["MODE"], 0)
        elif args.op == "scan":
            require_magic(regs)
            regs.write(REGISTERS["ENABLE"], 0)
            regs.write(REGISTERS["SCAN_OFFSET"], args.offset_counts)
            regs.write(REGISTERS["SCAN_AMP"], args.amp_counts)
            regs.write(REGISTERS["SCAN_STEP"], args.step_counts)
            regs.write(REGISTERS["SCAN_UPDATE_DIV"], max(1, args.update_div))
            regs.write(REGISTERS["OUT2_LIMIT"], args.limit_counts)
            regs.write(REGISTERS["MODE"], 1)
            regs.write(REGISTERS["ENABLE"], 1)
        elif args.op == "hold":
            require_magic(regs)
            regs.write(REGISTERS["ENABLE"], 0)
            regs.write(REGISTERS["HOLD_VALUE"], args.hold_counts)
            regs.write(REGISTERS["MODE"], 2)
            regs.write(REGISTERS["ENABLE"], 1)
        elif args.op == "p-lock":
            require_magic(regs)
            regs.write(REGISTERS["ENABLE"], 0)
            regs.write(REGISTERS["KP"], args.kp)
            regs.write(REGISTERS["KI"], 0)
            regs.write(REGISTERS["POLARITY"], args.polarity)
            regs.write(REGISTERS["LOCK_BIAS"], args.lock_bias_counts)
            regs.write(REGISTERS["LOCK_CORRECTION_LIMIT"], args.correction_limit_counts)
            regs.write(REGISTERS["LOCK_LIMIT"], args.lock_limit_counts)
            regs.write(REGISTERS["INTEGRAL_RESET"], 1)
            regs.write(REGISTERS["MODE"], 3)
            regs.write(REGISTERS["ENABLE"], 1)
        elif args.op == "pi-lock":
            require_magic(regs)
            regs.write(REGISTERS["ENABLE"], 0)
            regs.write(REGISTERS["KP"], args.kp)
            regs.write(REGISTERS["KI"], args.ki)
            regs.write(REGISTERS["POLARITY"], args.polarity)
            regs.write(REGISTERS["LOCK_BIAS"], args.lock_bias_counts)
            regs.write(REGISTERS["LOCK_CORRECTION_LIMIT"], args.correction_limit_counts)
            regs.write(REGISTERS["LOCK_LIMIT"], args.lock_limit_counts)
            regs.write(REGISTERS["INTEGRAL_RESET"], 1)
            regs.write(REGISTERS["MODE"], 4)
            regs.write(REGISTERS["ENABLE"], 1)
        elif args.op == "capture":
            require_magic(regs)
            status = read_status(regs)
            status.update(capture_waveform(regs, args.capture_length, args.capture_decimation))
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "auto-lock":
            status = run_auto_lock(regs, args)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        status = read_status(regs)
        if args.op == "status":
            warn_missing_magic(int(status["magic"], 16))
        print(json.dumps(status, indent=2, sort_keys=True))
    finally:
        regs.close()


if __name__ == "__main__":
    main()
"""


@dataclass
class ScanConfig:
    offset_counts: int
    amp_counts: int
    step_counts: int
    update_div: int
    limit_counts: int


@dataclass
class HoldConfig:
    hold_counts: int


@dataclass
class LockConfig:
    kp: int
    ki: int
    polarity: int
    lock_bias_counts: int
    lock_limit_counts: int
    correction_limit_counts: int


def volts_to_counts(volts: float) -> int:
    counts = int(round(volts * COUNTS_PER_VOLT))
    return max(-8191, min(8191, counts))


def build_scan_config(args: argparse.Namespace) -> ScanConfig:
    offset_counts = volts_to_counts(args.offset_v)
    amp_counts = abs(volts_to_counts(args.amp_v))
    if amp_counts < 1:
        raise SystemExit("scan amplitude must be at least one DAC count")
    if args.freq_hz <= 0:
        raise SystemExit("scan frequency must be positive")
    step_counts = max(1, int(args.step_counts))
    update_rate = args.freq_hz * 4.0 * amp_counts / step_counts
    update_div = max(1, int(round(args.clk_hz / update_rate)))
    return ScanConfig(
        offset_counts=offset_counts,
        amp_counts=amp_counts,
        step_counts=step_counts,
        update_div=update_div,
        limit_counts=max(0, min(8191, int(args.limit_counts))),
    )


def build_hold_config(args: argparse.Namespace) -> HoldConfig:
    return HoldConfig(hold_counts=volts_to_counts(args.hold_v))


def build_lock_config(args: argparse.Namespace, *, pi: bool) -> LockConfig:
    return LockConfig(
        kp=max(0, min(8191, int(args.kp))),
        ki=max(0, min(8191, int(args.ki if pi else 0))),
        polarity=1 if str(args.polarity).lower() in {"1", "invert", "inverted", "negative"} else 0,
        lock_bias_counts=volts_to_counts(args.lock_bias_v),
        lock_limit_counts=max(0, min(8191, int(args.lock_limit_counts))),
        correction_limit_counts=max(0, min(8191, int(args.correction_limit_counts))),
    )


def remote_command(args: argparse.Namespace, op: str, config: ScanConfig | HoldConfig | LockConfig | None) -> list[str]:
    helper_b64 = base64.b64encode(REMOTE_HELPER.encode("utf-8")).decode("ascii")
    remote_args = [
        "--base-addr",
        f"0x{args.base_addr:X}",
        "--op",
        op,
    ]
    if isinstance(config, ScanConfig):
        remote_args += [
            "--offset-counts",
            str(config.offset_counts),
            "--amp-counts",
            str(config.amp_counts),
            "--step-counts",
            str(config.step_counts),
            "--update-div",
            str(config.update_div),
            "--limit-counts",
            str(config.limit_counts),
        ]
    elif isinstance(config, HoldConfig):
        remote_args += [
            "--hold-counts",
            str(config.hold_counts),
        ]
    elif isinstance(config, LockConfig):
        remote_args += [
            "--kp",
            str(config.kp),
            "--ki",
            str(config.ki),
            "--polarity",
            str(config.polarity),
            "--lock-bias-counts",
            str(config.lock_bias_counts),
            "--lock-limit-counts",
            str(config.lock_limit_counts),
            "--correction-limit-counts",
            str(config.correction_limit_counts),
        ]
    elif op == "capture":
        remote_args += [
            "--capture-length",
            str(args.capture_length),
            "--capture-decimation",
            str(args.capture_decimation),
        ]
    elif op == "auto-lock":
        polarity = 1 if str(args.polarity).lower() in {"1", "invert", "inverted", "negative"} else 0
        remote_args += [
            "--sample-count",
            str(args.sample_count),
            "--sample-interval-s",
            str(args.sample_interval_s),
            "--zero-threshold",
            str(args.zero_threshold),
            "--edge-margin-counts",
            str(args.edge_margin_counts),
            "--scan-freq-hz",
            str(args.scan_freq_hz),
            "--polarity",
            str(polarity),
            "--lock-limit-counts",
            str(args.lock_limit_counts),
            "--correction-limit-counts",
            str(args.correction_limit_counts),
            "--settle-s",
            str(args.settle_s),
            "--kp-step-s",
            str(args.kp_step_s),
            "--abort-out2-counts",
            str(args.abort_out2_counts),
            "--error-growth-counts",
            str(args.error_growth_counts),
        ]
    remote_python = (
        "import base64, sys; "
        f"code=base64.b64decode('{helper_b64}').decode('utf-8'); "
        "sys.argv=['rp_custom_fpga_regs.py']+"
        f"{remote_args!r}; "
        "exec(compile(code, 'rp_custom_fpga_regs.py', 'exec'))"
    )
    target = f"{args.user}@{args.host}" if args.user else args.host
    remote_cmd = "python3 -c " + shlex.quote(remote_python)
    return ["ssh", target, remote_cmd]


def quote_powershell_arg(value: str) -> str:
    if value and all(ch.isalnum() or ch in "-_./:@\\" for ch in value):
        return value
    return "'" + value.replace("'", "''") + "'"


def print_command(command: list[str]) -> None:
    print(" ".join(quote_powershell_arg(part) for part in command))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control v3REG-0 Custom FPGA SAFE/SCAN registers over SSH."
    )
    parser.add_argument("--host", required=True, help="Red Pitaya hostname or IP")
    parser.add_argument("--user", default="root", help="SSH user, default: root")
    parser.add_argument("--base-addr", type=lambda value: int(value, 0), default=DEFAULT_BASE_ADDR)
    parser.add_argument("--clk-hz", type=float, default=DEFAULT_CLK_HZ)
    parser.add_argument("--print-command", action="store_true", help="Print SSH command instead of executing it")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("safe", help="Disable OUT2 and select SAFE mode")

    scan_parser = subparsers.add_parser("scan", help="Set scan parameters and enable SCAN mode")
    scan_parser.add_argument("--offset-v", type=float, default=0.85)
    scan_parser.add_argument("--amp-v", type=float, default=0.05)
    scan_parser.add_argument("--freq-hz", type=float, default=50.0)
    scan_parser.add_argument("--step-counts", type=int, default=1)
    scan_parser.add_argument("--limit-counts", type=int, default=8191)

    hold_parser = subparsers.add_parser("hold", help="Set fixed OUT2 voltage and enable HOLD mode")
    hold_parser.add_argument("--hold-v", type=float, default=0.0)

    p_lock_parser = subparsers.add_parser("p-lock", help="Enable proportional lock mode; Kp defaults to zero")
    p_lock_parser.add_argument("--kp", type=int, default=0, help="Fixed-point Kp, 256 = gain 1.0")
    p_lock_parser.add_argument("--polarity", choices=["normal", "invert", "0", "1"], default="normal")
    p_lock_parser.add_argument("--lock-bias-v", type=float, default=0.0)
    p_lock_parser.add_argument("--lock-limit-counts", type=int, default=8191)
    p_lock_parser.add_argument("--correction-limit-counts", type=int, default=128)

    pi_lock_parser = subparsers.add_parser("pi-lock", help="Enable PI lock mode; Kp/Ki default to zero")
    pi_lock_parser.add_argument("--kp", type=int, default=0, help="Fixed-point Kp, 256 = gain 1.0")
    pi_lock_parser.add_argument("--ki", type=int, default=0, help="Fixed-point Ki, 256 = gain 1.0 per sample")
    pi_lock_parser.add_argument("--polarity", choices=["normal", "invert", "0", "1"], default="normal")
    pi_lock_parser.add_argument("--lock-bias-v", type=float, default=0.0)
    pi_lock_parser.add_argument("--lock-limit-counts", type=int, default=8191)
    pi_lock_parser.add_argument("--correction-limit-counts", type=int, default=128)

    subparsers.add_parser("status", help="Read magic/version/status/out2 monitor")
    subparsers.add_parser("probe", help="Read magic/version at candidate GP0 base addresses")
    capture_parser = subparsers.add_parser("capture", help="Capture custom_debug_capture waveform data")
    capture_parser.add_argument("--capture-length", type=int, default=2048)
    capture_parser.add_argument("--capture-decimation", type=int, default=1024)
    auto_parser = subparsers.add_parser("auto-lock", help="Candidate P-only auto lock from SCAN zero crossing")
    auto_parser.add_argument("--sample-count", type=int, default=256)
    auto_parser.add_argument("--sample-interval-s", type=float, default=0.02)
    auto_parser.add_argument("--zero-threshold", type=int, default=10)
    auto_parser.add_argument("--edge-margin-counts", type=int, default=256)
    auto_parser.add_argument("--scan-freq-hz", type=float, default=0.5)
    auto_parser.add_argument("--polarity", choices=["normal", "invert", "0", "1"], default="normal")
    auto_parser.add_argument("--lock-limit-counts", type=int, default=8191)
    auto_parser.add_argument("--correction-limit-counts", type=int, default=128)
    auto_parser.add_argument("--settle-s", type=float, default=0.5)
    auto_parser.add_argument("--kp-step-s", type=float, default=1.0)
    auto_parser.add_argument("--abort-out2-counts", type=int, default=7800)
    auto_parser.add_argument("--error-growth-counts", type=int, default=20)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "scan":
        config = build_scan_config(args)
    elif args.command == "hold":
        config = build_hold_config(args)
    elif args.command == "p-lock":
        config = build_lock_config(args, pi=False)
    elif args.command == "pi-lock":
        config = build_lock_config(args, pi=True)
    else:
        config = None
    command = remote_command(args, args.command, config)

    if args.print_command:
        if isinstance(config, ScanConfig):
            print(
                textwrap.dedent(
                    f"""
                    # computed scan parameters
                    # offset_counts={config.offset_counts}
                    # amp_counts={config.amp_counts}
                    # step_counts={config.step_counts}
                    # update_div={config.update_div}
                    # limit_counts={config.limit_counts}
                    """
                ).strip()
            )
        elif isinstance(config, HoldConfig):
            print(f"# computed hold parameter\n# hold_counts={config.hold_counts}")
        elif isinstance(config, LockConfig):
            print(
                textwrap.dedent(
                    f"""
                    # computed lock parameters
                    # kp={config.kp}
                    # ki={config.ki}
                    # polarity={config.polarity}
                    # lock_bias_counts={config.lock_bias_counts}
                    # lock_limit_counts={config.lock_limit_counts}
                    # correction_limit_counts={config.correction_limit_counts}
                    """
                ).strip()
            )
        print_command(command)
        return 0

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
