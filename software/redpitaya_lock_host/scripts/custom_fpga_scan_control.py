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
from pathlib import Path

try:
    from redpitaya_lock_host.out2_calibration import (
        COUNTS_PER_VOLT,
        out2_amplitude_to_counts,
        out2_voltage_to_counts,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from redpitaya_lock_host.out2_calibration import (
        COUNTS_PER_VOLT,
        out2_amplitude_to_counts,
        out2_voltage_to_counts,
    )

DEFAULT_CLK_HZ = 125_000_000.0
DEFAULT_BASE_ADDR = 0x4060_0000
ALLOWED_UPDATE_KP = (0, 4, 8, 16, 32)

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
    "ERROR_SETPOINT": 0x54,
    "LOCK_ERROR_MONITOR": 0x58,
    "CAPTURE_LOCK_POINT": 0x5C,
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
    "ERROR_SETPOINT": 0x54,
    "LOCK_ERROR_MONITOR": 0x58,
    "CAPTURE_LOCK_POINT": 0x5C,
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
EXPECTED_VERSION = 0x00030001
ALLOWED_UPDATE_KP = {0, 4, 8, 16, 32}
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
    error_setpoint_raw = regs.read(REGISTERS["ERROR_SETPOINT"])
    lock_error_raw = regs.read(REGISTERS["LOCK_ERROR_MONITOR"])
    kp_raw = regs.read(REGISTERS["KP"])
    polarity_raw = regs.read(REGISTERS["POLARITY"])
    lock_bias_raw = regs.read(REGISTERS["LOCK_BIAS"])
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
        "error_setpoint_counts": to_signed14(error_setpoint_raw),
        "error_setpoint_volts": to_signed14(error_setpoint_raw) / 8191.0,
        "lock_bias_counts": to_signed14(lock_bias_raw),
        "lock_bias_volts": to_signed14(lock_bias_raw) / 8191.0,
        "lock_error_counts": to_signed14(lock_error_raw),
        "lock_error_volts": to_signed14(lock_error_raw) / 8191.0,
        "kp": to_signed14(kp_raw),
        "polarity": polarity_raw & 1,
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


def run_lock_here(regs, args):
    require_magic(regs)
    status = read_status(regs)
    if status["version"] != f"0x{EXPECTED_VERSION:08X}":
        raise SystemExit(f"VERSION mismatch: expected 0x{EXPECTED_VERSION:08X}, got {status['version']}")
    if int(status["mode"]) != 1:
        raise SystemExit("LOCK HERE requires MODE=1 SCAN first")
    if int(status["enable"]) != 1:
        raise SystemExit("LOCK HERE requires ENABLE=1 while scanning")
    if bool(status["saturated"]):
        raise SystemExit("LOCK HERE refused because STATUS reports saturation")

    target_wait_matched = False
    if args.target_out2_counts is not None:
        target = int(args.target_out2_counts)
        window = max(0, int(args.target_window_counts))
        deadline = time.time() + max(0.1, float(args.target_timeout_s))
        while time.time() <= deadline:
            status = read_status(regs)
            if int(status["mode"]) != 1 or int(status["enable"]) != 1 or bool(status["saturated"]):
                raise SystemExit("LOCK HERE target wait aborted: SCAN/ENABLE/saturation precondition changed")
            if abs(int(status["out2_counts"]) - target) <= window:
                target_wait_matched = True
                break
            time.sleep(max(0.001, float(args.target_poll_s)))
        if not target_wait_matched:
            raise SystemExit("LOCK HERE timed out before OUT2 reached the selected target window")

    correction_limit = max(0, min(8191, int(args.correction_limit_counts)))
    lock_limit = max(0, min(8191, int(args.lock_limit_counts)))
    if lock_limit < abs(int(status["out2_counts"])) + correction_limit:
        raise SystemExit(
            "LOCK HERE refused: lock_limit_counts must be >= "
            "abs(current OUT2_MONITOR) + correction_limit_counts"
        )

    regs.write(REGISTERS["KP"], 0)
    regs.write(REGISTERS["KI"], 0)
    regs.write(REGISTERS["POLARITY"], args.polarity)
    regs.write(REGISTERS["LOCK_CORRECTION_LIMIT"], correction_limit)
    regs.write(REGISTERS["LOCK_LIMIT"], lock_limit)
    regs.write(REGISTERS["INTEGRAL_RESET"], 1)
    regs.write(REGISTERS["CAPTURE_LOCK_POINT"], 1)
    time.sleep(max(0.02, float(args.settle_s)))
    readback = read_status(regs)
    if int(readback["mode"]) != 3:
        regs.write(REGISTERS["KP"], 0)
        regs.write(REGISTERS["ENABLE"], 0)
        regs.write(REGISTERS["MODE"], 0)
        raise SystemExit("LOCK HERE failed: MODE did not read back as 3")

    readback.update({
        "lock_state": "P_LOCK_ACTIVE_KP0",
        "captured_error_setpoint_counts": readback["error_setpoint_counts"],
        "captured_lock_bias_counts": to_signed14(regs.read(REGISTERS["LOCK_BIAS"])),
        "captured_lock_bias_volts_ideal": to_signed14(regs.read(REGISTERS["LOCK_BIAS"])) / 8191.0,
        "current_kp": 0,
        "current_ki": 0,
        "correction_limit_counts": correction_limit,
        "target_wait_matched": target_wait_matched,
        "target_out2_counts": args.target_out2_counts,
        "target_window_counts": args.target_window_counts,
        "lock_bias_source": "FPGA CAPTURE_LOCK_POINT captured OUT2_MONITOR in clk_i domain",
        "error_setpoint_source": "FPGA CAPTURE_LOCK_POINT captured ERROR_MONITOR in clk_i domain",
    })
    return readback


def safe_exit(regs, reason):
    regs.write(REGISTERS["KP"], 0)
    regs.write(REGISTERS["ENABLE"], 0)
    regs.write(REGISTERS["MODE"], 0)
    raise SystemExit(f"update-p-lock aborted and SAFE executed: {reason}")


def run_update_p_lock(regs, args):
    require_magic(regs)
    before = read_status(regs)
    before_error_setpoint = int(before["error_setpoint_counts"])
    before_lock_bias = int(before["lock_bias_counts"])
    before_mode = int(before["mode"])
    before_enable = int(before["enable"])
    before_kp = int(before["kp"])
    before_polarity = int(before["polarity"])
    requested_polarity = int(args.polarity)

    if before["version"] != f"0x{EXPECTED_VERSION:08X}":
        safe_exit(regs, f"VERSION mismatch: expected 0x{EXPECTED_VERSION:08X}, got {before['version']}")
    if before_mode != 3:
        safe_exit(regs, f"MODE=3 P_LOCK is required, got MODE={before_mode}")
    if before_enable != 1:
        safe_exit(regs, f"ENABLE=1 is required, got ENABLE={before_enable}")
    if bool(before["saturated"]):
        safe_exit(regs, "pre-update saturation is set")
    if int(args.kp) not in ALLOWED_UPDATE_KP:
        safe_exit(regs, f"Kp must be one of {sorted(ALLOWED_UPDATE_KP)}, got {args.kp}")
    if before_polarity != requested_polarity and before_kp != 0:
        raise SystemExit(
            "update-p-lock refused: polarity change while Kp is nonzero. "
            "first APPLY P with --kp 0, then change polarity."
        )

    # Normal update writes only KP and POLARITY.
    regs.write(REGISTERS["KP"], args.kp)
    regs.write(REGISTERS["POLARITY"], requested_polarity)

    # Post-update verification keeps the FPGA in SAFE on any lock-point drift.
    after = read_status(regs)
    after_lock_bias = int(after["lock_bias_counts"])
    if int(after["mode"]) != 3:
        safe_exit(regs, f"MODE changed after update: {after['mode']}")
    if int(after["enable"]) != 1:
        safe_exit(regs, f"ENABLE changed after update: {after['enable']}")
    if before_error_setpoint != int(after["error_setpoint_counts"]):
        safe_exit(regs, "ERROR_SETPOINT changed during update-p-lock")
    if before_lock_bias != after_lock_bias:
        safe_exit(regs, "LOCK_BIAS changed during update-p-lock")
    if int(after["kp"]) != int(args.kp):
        safe_exit(regs, f"KP readback mismatch: expected {args.kp}, got {after['kp']}")
    if int(after["polarity"]) != requested_polarity:
        safe_exit(regs, f"POLARITY readback mismatch: expected {requested_polarity}, got {after['polarity']}")
    if bool(after["saturated"]):
        safe_exit(regs, "post-update saturation is set")

    after.update({
        "lock_state": "P_LOCK_UPDATED",
        "before_kp": before_kp,
        "before_polarity": before_polarity,
        "current_kp": int(after["kp"]),
        "current_polarity": int(after["polarity"]),
        "error_setpoint_preserved_counts": before_error_setpoint,
        "lock_bias_preserved_counts": before_lock_bias,
        "update_rule": "Only KP and POLARITY were written; LOCK_BIAS and ERROR_SETPOINT were not touched.",
    })
    return after


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
    parser.add_argument("--op", choices=["safe", "scan", "hold", "p-lock", "update-p-lock", "pi-lock", "lock-here", "status", "probe", "capture"], required=True)
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
    parser.add_argument("--settle-s", type=float, default=0.5)
    parser.add_argument("--target-out2-counts", type=int, default=None)
    parser.add_argument("--target-window-counts", type=int, default=64)
    parser.add_argument("--target-timeout-s", type=float, default=5.0)
    parser.add_argument("--target-poll-s", type=float, default=0.005)
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
        elif args.op == "update-p-lock":
            status = run_update_p_lock(regs, args)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
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
        elif args.op == "lock-here":
            status = run_lock_here(regs, args)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "capture":
            require_magic(regs)
            status = read_status(regs)
            status.update(capture_waveform(regs, args.capture_length, args.capture_decimation))
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


@dataclass
class UpdatePLockConfig:
    kp: int
    polarity: int


def volts_to_counts(volts: float) -> int:
    return out2_voltage_to_counts(volts)


def build_scan_config(args: argparse.Namespace) -> ScanConfig:
    offset_counts = volts_to_counts(args.offset_v)
    amp_counts = out2_amplitude_to_counts(args.amp_v)
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


def build_update_p_lock_config(args: argparse.Namespace) -> UpdatePLockConfig:
    return UpdatePLockConfig(
        kp=int(args.kp),
        polarity=1 if str(args.polarity).lower() in {"1", "invert", "inverted", "negative"} else 0,
    )


def remote_command(
    args: argparse.Namespace,
    op: str,
    config: ScanConfig | HoldConfig | LockConfig | UpdatePLockConfig | None,
) -> list[str]:
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
    elif isinstance(config, UpdatePLockConfig):
        remote_args += [
            "--kp",
            str(config.kp),
            "--polarity",
            str(config.polarity),
        ]
    elif op == "capture":
        remote_args += [
            "--capture-length",
            str(args.capture_length),
            "--capture-decimation",
            str(args.capture_decimation),
        ]
    elif op == "lock-here":
        polarity = 1 if str(args.polarity).lower() in {"1", "invert", "inverted", "negative"} else 0
        remote_args += [
            "--polarity",
            str(polarity),
            "--lock-limit-counts",
            str(args.lock_limit_counts),
            "--correction-limit-counts",
            str(args.correction_limit_counts),
            "--settle-s",
            str(args.settle_s),
            "--target-window-counts",
            str(args.target_window_counts),
            "--target-timeout-s",
            str(args.target_timeout_s),
            "--target-poll-s",
            str(args.target_poll_s),
        ]
        if args.target_out2_counts is not None:
            remote_args += ["--target-out2-counts", str(args.target_out2_counts)]
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

    update_p_parser = subparsers.add_parser(
        "update-p-lock",
        help="Apply manual P gain/polarity after LOCK HERE without recapturing LOCK_BIAS or ERROR_SETPOINT",
    )
    update_p_parser.add_argument("--kp", type=int, choices=ALLOWED_UPDATE_KP, default=0)
    update_p_parser.add_argument("--polarity", choices=["normal", "invert", "0", "1"], default="normal")

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
    lock_here_parser = subparsers.add_parser(
        "lock-here",
        help="Capture current ERROR/OUT2 in FPGA and enter MODE=3 P_LOCK with Kp=0",
    )
    lock_here_parser.add_argument("--polarity", choices=["normal", "invert", "0", "1"], default="normal")
    lock_here_parser.add_argument("--lock-limit-counts", type=int, default=8191)
    lock_here_parser.add_argument("--correction-limit-counts", type=int, default=128)
    lock_here_parser.add_argument("--settle-s", type=float, default=0.5)
    lock_here_parser.add_argument("--target-out2-counts", type=int, default=None)
    lock_here_parser.add_argument("--target-window-counts", type=int, default=64)
    lock_here_parser.add_argument("--target-timeout-s", type=float, default=5.0)
    lock_here_parser.add_argument("--target-poll-s", type=float, default=0.005)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "scan":
        config = build_scan_config(args)
    elif args.command == "hold":
        config = build_hold_config(args)
    elif args.command == "p-lock":
        config = build_lock_config(args, pi=False)
    elif args.command == "update-p-lock":
        config = build_update_p_lock_config(args)
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
        elif isinstance(config, UpdatePLockConfig):
            print(
                textwrap.dedent(
                    f"""
                    # update-p-lock parameters
                    # kp={config.kp}
                    # polarity={config.polarity}
                    # normal path writes only KP and POLARITY
                    """
                ).strip()
            )
        print_command(command)
        return 0

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
