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
EXPECTED_VERSION = 0x00030100
SIMPLE_VERSION = 0x00030200
SUPPORTED_VERSIONS = {EXPECTED_VERSION, SIMPLE_VERSION}

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
    "TARGET_OUT2_SHADOW": 0x60,
    "TARGET_ERROR_SETPOINT_SHADOW": 0x64,
    "TARGET_WINDOW_SHADOW": 0x68,
    "TARGET_REQUIREMENTS_SHADOW": 0x6C,
    "CORRECTION_LIMIT_SHADOW": 0x70,
    "ABSOLUTE_LIMIT_SHADOW": 0x74,
    "CONFIG_GENERATION_SHADOW": 0x78,
    "CONFIG_VALIDATION": 0x7C,
    "CAPTURE_CTRL": 0x80,
    "CAPTURE_STATUS": 0x84,
    "CAPTURE_DECIMATION": 0x88,
    "CAPTURE_LENGTH": 0x8C,
    "CAPTURE_READ_INDEX": 0x90,
    "CAPTURE_DATA_CH1": 0x94,
    "CAPTURE_DATA_CH2": 0x98,
    "CAPTURE_DATA_CH3": 0x9C,
    "CAPTURE_DATA_CH4": 0xA0,
    "ACQ_COMMAND": 0xA4,
    "ACQ_STATE": 0xA8,
    "EVENT_SEQUENCE": 0xAC,
    "EVENT_OUT2": 0xB0,
    "EVENT_ERROR": 0xB4,
    "EVENT_CONFIG_GENERATION": 0xB8,
    "EVENT_INFO": 0xBC,
    "EVENT_TIMESTAMP_LO": 0xC0,
    "EVENT_TIMESTAMP_HI": 0xC4,
    "ACTIVE_TARGET_OUT2": 0xC8,
    "ACTIVE_ERROR_SETPOINT": 0xCC,
    "ACTIVE_WINDOW": 0xD0,
    "ACTIVE_REQUIREMENTS": 0xD4,
    "ACTIVE_CORRECTION_LIMIT": 0xD8,
    "ACTIVE_ABSOLUTE_LIMIT": 0xDC,
    "FAULT_DETAIL": 0xE0,
    "L1_CAPABILITY": 0xE4,
    "CROSSING_CONFIG": 0xE8,
    "KP_ACQUIRE_TARGET": 0xEC,
    "KP_RAMP_CONFIG": 0xF0,
    "ACQUIRE_TIMEOUT": 0xF4,
    "SERVO_CONFIG": 0xF8,
    "SUPERVISOR_CONFIG0": 0xFC,
    "SUPERVISOR_CONFIG1": 0x100,
    "EVENT_LOCK_ERROR": 0x104,
    "VALIDATE_EVENT_COUNT": 0x108,
    "KP_EFFECTIVE": 0x10C,
    "SUPERVISOR_METRICS": 0x110,
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
    "TARGET_OUT2_SHADOW": 0x60,
    "TARGET_ERROR_SETPOINT_SHADOW": 0x64,
    "TARGET_WINDOW_SHADOW": 0x68,
    "TARGET_REQUIREMENTS_SHADOW": 0x6C,
    "CORRECTION_LIMIT_SHADOW": 0x70,
    "ABSOLUTE_LIMIT_SHADOW": 0x74,
    "CONFIG_GENERATION_SHADOW": 0x78,
    "CONFIG_VALIDATION": 0x7C,
    "CAPTURE_CTRL": 0x80,
    "CAPTURE_STATUS": 0x84,
    "CAPTURE_DECIMATION": 0x88,
    "CAPTURE_LENGTH": 0x8C,
    "CAPTURE_READ_INDEX": 0x90,
    "CAPTURE_DATA_CH1": 0x94,
    "CAPTURE_DATA_CH2": 0x98,
    "CAPTURE_DATA_CH3": 0x9C,
    "CAPTURE_DATA_CH4": 0xA0,
    "ACQ_COMMAND": 0xA4,
    "ACQ_STATE": 0xA8,
    "EVENT_SEQUENCE": 0xAC,
    "EVENT_OUT2": 0xB0,
    "EVENT_ERROR": 0xB4,
    "EVENT_CONFIG_GENERATION": 0xB8,
    "EVENT_INFO": 0xBC,
    "EVENT_TIMESTAMP_LO": 0xC0,
    "EVENT_TIMESTAMP_HI": 0xC4,
    "ACTIVE_TARGET_OUT2": 0xC8,
    "ACTIVE_ERROR_SETPOINT": 0xCC,
    "ACTIVE_WINDOW": 0xD0,
    "ACTIVE_REQUIREMENTS": 0xD4,
    "ACTIVE_CORRECTION_LIMIT": 0xD8,
    "ACTIVE_ABSOLUTE_LIMIT": 0xDC,
    "FAULT_DETAIL": 0xE0,
    "L1_CAPABILITY": 0xE4,
    "CROSSING_CONFIG": 0xE8,
    "KP_ACQUIRE_TARGET": 0xEC,
    "KP_RAMP_CONFIG": 0xF0,
    "ACQUIRE_TIMEOUT": 0xF4,
    "SERVO_CONFIG": 0xF8,
    "SUPERVISOR_CONFIG0": 0xFC,
    "SUPERVISOR_CONFIG1": 0x100,
    "EVENT_LOCK_ERROR": 0x104,
    "VALIDATE_EVENT_COUNT": 0x108,
    "KP_EFFECTIVE": 0x10C,
    "SUPERVISOR_METRICS": 0x110,
}

EXPECTED_MAGIC = 0x4D545330
EXPECTED_VERSION = 0x00030100
SIMPLE_VERSION = 0x00030200
SUPPORTED_VERSIONS = {EXPECTED_VERSION, SIMPLE_VERSION}
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


ACQ_STATE_NAMES = {
    0: "SAFE",
    1: "SCAN",
    2: "VALIDATING",
    3: "ARMED",
    4: "ACQUIRING",
    5: "P_LOCKED",
    6: "FAILED",
    7: "FAULT",
}


EVENT_TYPE_NAMES = {
    0: "NONE",
    1: "ARMED",
    2: "TRIGGERED",
    3: "ABORTED",
    4: "CONFIG_REJECTED",
    5: "COMMAND_REJECTED",
    6: "FAULT",
    7: "VALIDATED",
}


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
    ki_raw = regs.read(REGISTERS["KI"])
    polarity_raw = regs.read(REGISTERS["POLARITY"])
    lock_bias_raw = regs.read(REGISTERS["LOCK_BIAS"])
    acq_state_raw = regs.read(REGISTERS["ACQ_STATE"])
    acq_state = acq_state_raw & 0x7
    l1_capability = regs.read(REGISTERS["L1_CAPABILITY"])
    return {
        "magic": f"0x{magic:08X}",
        "version": f"0x{version:08X}",
        "build_capability": (
            "L1_ERROR_CROSSING"
            if version == SIMPLE_VERSION and l1_capability == 0x4C310001
            else "SIMPLE" if version == SIMPLE_VERSION
            else "D1" if version == EXPECTED_VERSION
            else "UNKNOWN"
        ),
        "l1_capability": f"0x{l1_capability:08X}",
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
        "ki": to_signed14(ki_raw),
        "polarity": polarity_raw & 1,
        "control_counts": to_signed14(control_raw),
        "control_volts": to_signed14(control_raw) / 8191.0,
        "lock_correction_limit_counts": to_signed14(regs.read(REGISTERS["LOCK_CORRECTION_LIMIT"])),
        "acquisition_state_raw": f"0x{acq_state_raw:08X}",
        "acquisition_state": acq_state,
        "acquisition_state_name": ACQ_STATE_NAMES.get(acq_state, "UNKNOWN"),
        "acquisition_event_valid": bool(acq_state_raw & (1 << 8)),
        "acquisition_active": bool(acq_state_raw & (1 << 10)),
        "acquisition_fault": bool(acq_state_raw & (1 << 11)),
        "acquisition_scan_direction": (acq_state_raw >> 14) & 0x3,
        "kp_effective": to_signed14(regs.read(REGISTERS["KP_EFFECTIVE"])),
        "validate_event_count": regs.read(REGISTERS["VALIDATE_EVENT_COUNT"]),
        "supervisor_metrics_raw": f"0x{regs.read(REGISTERS['SUPERVISOR_METRICS']):08X}",
    }


def read_acquisition_event_coherent(regs, retries=8):
    for _ in range(max(1, int(retries))):
        sequence_before = regs.read(REGISTERS["EVENT_SEQUENCE"])
        info = regs.read(REGISTERS["EVENT_INFO"])
        out2_raw = regs.read(REGISTERS["EVENT_OUT2"])
        error_raw = regs.read(REGISTERS["EVENT_ERROR"])
        lock_error_raw = regs.read(REGISTERS["EVENT_LOCK_ERROR"])
        generation = regs.read(REGISTERS["EVENT_CONFIG_GENERATION"])
        timestamp_lo = regs.read(REGISTERS["EVENT_TIMESTAMP_LO"])
        timestamp_hi = regs.read(REGISTERS["EVENT_TIMESTAMP_HI"])
        fault_detail = regs.read(REGISTERS["FAULT_DETAIL"])
        sequence_after = regs.read(REGISTERS["EVENT_SEQUENCE"])
        if sequence_before == sequence_after:
            event_type = (info >> 1) & 0x7
            return {
                "sequence": sequence_after,
                "valid": bool(info & 1),
                "event_type": event_type,
                "event_type_name": EVENT_TYPE_NAMES.get(event_type, "UNKNOWN"),
                "out2_counts": to_signed14(out2_raw),
                "error_counts": to_signed14(error_raw),
                "lock_error_counts": to_signed14(lock_error_raw),
                "scan_direction": (info >> 4) & 0x3,
                "error_crossing_direction": (info >> 6) & 0x3,
                "config_generation": generation,
                "timestamp": (timestamp_hi << 32) | timestamp_lo,
                "reject_code": fault_detail & 0xFFFF,
                "fault_code": (fault_detail >> 16) & 0xFFFF,
            }
    raise SystemExit("coherent acquisition event read failed after sequence changed repeatedly")


def acquisition_status(regs):
    status = read_status(regs)
    status["acquisition_event"] = read_acquisition_event_coherent(regs)
    return status


def write_acquisition_shadow(regs, args):
    requirements = (
        (int(args.required_scan_direction) & 0x3)
        | ((int(args.required_error_crossing_direction) & 0x3) << 2)
        | ((int(args.initial_polarity_suggestion) & 0x1) << 4)
    )
    regs.write(REGISTERS["TARGET_OUT2_SHADOW"], int(args.target_out2_counts))
    regs.write(
        REGISTERS["TARGET_ERROR_SETPOINT_SHADOW"],
        int(args.target_error_setpoint_counts),
    )
    regs.write(REGISTERS["TARGET_WINDOW_SHADOW"], int(args.target_window_counts))
    regs.write(REGISTERS["TARGET_REQUIREMENTS_SHADOW"], requirements)
    regs.write(REGISTERS["CORRECTION_LIMIT_SHADOW"], int(args.correction_limit_counts))
    regs.write(REGISTERS["ABSOLUTE_LIMIT_SHADOW"], int(args.absolute_limit_counts))
    regs.write(REGISTERS["CONFIG_GENERATION_SHADOW"], int(args.config_generation))


def write_l1_acquisition_config(regs, args):
    regs.write(
        REGISTERS["CROSSING_CONFIG"],
        (int(args.crossing_consecutive_samples) << 16)
        | int(args.crossing_hysteresis_counts),
    )
    regs.write(REGISTERS["KP_ACQUIRE_TARGET"], int(args.preloaded_kp))
    regs.write(
        REGISTERS["KP_RAMP_CONFIG"],
        (int(args.kp_ramp_div) << 16) | int(args.kp_ramp_step),
    )
    regs.write(REGISTERS["ACQUIRE_TIMEOUT"], int(args.acquire_timeout_cycles))
    regs.write(
        REGISTERS["SERVO_CONFIG"],
        (int(args.out2_slew_limit_counts) << 16) | int(args.servo_update_div),
    )
    regs.write(
        REGISTERS["SUPERVISOR_CONFIG0"],
        (int(args.divergence_windows) << 16)
        | (int(args.lock_confirm_windows) << 8)
        | int(args.observe_shift),
    )
    regs.write(
        REGISTERS["SUPERVISOR_CONFIG1"],
        (int(args.error_abs_limit_counts) << 16)
        | int(args.error_mean_limit_counts),
    )


def run_preload_acquisition(regs, args, arm, validate=False):
    require_magic(regs)
    before = read_status(regs)
    if int(before["version"], 0) not in SUPPORTED_VERSIONS:
        raise SystemExit(
            "VERSION mismatch: expected D1 0x00030100 or SIMPLE 0x00030200, "
            f"got {before['version']}"
        )
    if int(before["mode"]) != 1 or int(before["enable"]) != 1:
        raise SystemExit("FPGA acquisition requires MODE=1 SCAN and ENABLE=1")
    if bool(before["saturated"]):
        raise SystemExit("FPGA acquisition refused because STATUS reports saturation")
    if int(before["acquisition_state"]) == 2:
        raise SystemExit("target configuration writes are forbidden while acquisition is ARMED")
    if before["build_capability"] != "L1_ERROR_CROSSING":
        raise SystemExit("LOCK-MVP-L1 capability 0x4C310001 is required")
    regs.write(REGISTERS["POLARITY"], int(args.preloaded_polarity) & 1)
    write_acquisition_shadow(regs, args)
    write_l1_acquisition_config(regs, args)
    validation = regs.read(REGISTERS["CONFIG_VALIDATION"])
    if not (validation & (1 << 7)):
        raise SystemExit(f"FPGA acquisition shadow validation failed: 0x{validation:08X}")
    if arm:
        regs.write(REGISTERS["ACQ_COMMAND"], 8 if validate else 1)
    result = acquisition_status(regs)
    result["config_validation"] = f"0x{validation:08X}"
    result["config_generation"] = int(args.config_generation)
    result["target_out2_counts"] = int(args.target_out2_counts)
    result["target_error_setpoint_counts"] = int(args.target_error_setpoint_counts)
    result["target_window_counts"] = int(args.target_window_counts)
    result["required_scan_direction"] = int(args.required_scan_direction)
    result["required_error_crossing_direction"] = int(
        args.required_error_crossing_direction
    )
    result["initial_polarity_suggestion"] = int(args.initial_polarity_suggestion)
    expected_states = (2,) if validate else (3, 4, 5)
    if arm and int(result["acquisition_state"]) not in expected_states:
        raise SystemExit(
            "ARM command was written once, but FPGA did not report ARMED or P_LOCK"
        )
    result["lock_state"] = result["acquisition_state_name"]
    result["arm_intent"] = "VALIDATE" if validate else "ACTIVE"
    return result


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
    if int(status["version"], 0) not in SUPPORTED_VERSIONS:
        raise SystemExit(f"VERSION mismatch: unsupported build {status['version']}")
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
    before = acquisition_status(regs)
    before_error_setpoint = int(before["error_setpoint_counts"])
    before_lock_bias = int(before["lock_bias_counts"])
    before_mode = int(before["mode"])
    before_enable = int(before["enable"])
    before_kp = int(before["kp"])
    before_ki = int(before["ki"])
    before_polarity = int(before["polarity"])
    requested_polarity = int(args.polarity)
    requested_generation = int(args.config_generation)
    event = before["acquisition_event"]

    if int(before["version"], 0) not in SUPPORTED_VERSIONS:
        safe_exit(regs, f"VERSION mismatch: unsupported build {before['version']}")
    if before_mode != 3:
        safe_exit(regs, f"MODE=3 P_LOCK is required, got MODE={before_mode}")
    if before_enable != 1:
        safe_exit(regs, f"ENABLE=1 is required, got ENABLE={before_enable}")
    if bool(before["saturated"]):
        safe_exit(regs, "pre-update saturation is set")
    if before_ki != 0:
        safe_exit(regs, f"Apply P requires Ki=0, got Ki={before_ki}")
    if int(args.kp) not in ALLOWED_UPDATE_KP:
        safe_exit(regs, f"Kp must be one of {sorted(ALLOWED_UPDATE_KP)}, got {args.kp}")
    if int(args.kp) != 0 and int(before["acquisition_state"]) != 4:
        safe_exit(regs, "nonzero Apply P requires FPGA state P_LOCK_KP0")
    if int(args.kp) == 0 and int(before["acquisition_state"]) not in (4, 5):
        safe_exit(regs, "Apply P Kp=0 requires FPGA state P_LOCK_KP0 or P_LOCK_ACTIVE")
    if not bool(event["valid"]) or int(event["event_type"]) != 2:
        safe_exit(regs, "Apply P requires a sticky FPGA TRIGGERED event")
    if requested_generation <= 0 or int(event["config_generation"]) != requested_generation:
        safe_exit(
            regs,
            "Apply P refused because FPGA event generation does not match the confirmed target",
        )
    if before_polarity != requested_polarity and before_kp != 0:
        raise SystemExit(
            "update-p-lock refused: polarity change while Kp is nonzero. "
            "first APPLY P with --kp 0, then change polarity."
        )

    # Polarity is changed and read back while Kp is still zero.
    regs.write(REGISTERS["POLARITY"], requested_polarity)
    polarity_readback = regs.read(REGISTERS["POLARITY"]) & 1
    if polarity_readback != requested_polarity:
        safe_exit(
            regs,
            f"POLARITY readback mismatch before Apply P: expected {requested_polarity}, got {polarity_readback}",
        )
    regs.write(REGISTERS["KP"], args.kp)

    # Post-update verification keeps the FPGA in SAFE on any lock-point drift.
    after = acquisition_status(regs)
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
    if int(after["ki"]) != 0:
        safe_exit(regs, f"Ki changed during Apply P: {after['ki']}")
    if int(after["polarity"]) != requested_polarity:
        safe_exit(regs, f"POLARITY readback mismatch: expected {requested_polarity}, got {after['polarity']}")
    if bool(after["saturated"]):
        safe_exit(regs, "post-update saturation is set")

    after.update({
        "lock_state": "P_LOCK_UPDATED",
        "before_kp": before_kp,
        "before_polarity": before_polarity,
        "current_kp": int(after["kp"]),
        "current_ki": int(after["ki"]),
        "current_polarity": int(after["polarity"]),
        "error_setpoint_preserved_counts": before_error_setpoint,
        "lock_bias_preserved_counts": before_lock_bias,
        "config_generation": requested_generation,
        "update_rule": "POLARITY was verified while Kp=0, then KP was written; LOCK_BIAS and ERROR_SETPOINT were not touched.",
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
    parser.add_argument(
        "--op",
        choices=[
            "safe",
            "scan",
            "hold",
            "p-lock",
            "update-p-lock",
            "pi-lock",
            "lock-here",
            "preload-acquisition",
            "arm-acquisition",
            "validate-acquisition",
            "acquisition-status",
            "abort-acquisition",
            "clear-acquisition-event",
            "status",
            "probe",
            "capture",
        ],
        required=True,
    )
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
    parser.add_argument("--target-error-setpoint-counts", type=int, default=0)
    parser.add_argument("--target-window-counts", type=int, default=64)
    parser.add_argument("--required-scan-direction", type=int, choices=[1, 2], default=1)
    parser.add_argument(
        "--required-error-crossing-direction",
        type=int,
        choices=[1, 2],
        default=1,
    )
    parser.add_argument("--initial-polarity-suggestion", type=int, choices=[0, 1], default=0)
    parser.add_argument("--absolute-limit-counts", type=int, default=8191)
    parser.add_argument("--config-generation", type=int, default=0)
    parser.add_argument("--preloaded-kp", type=int, choices=[0, 4], default=0)
    parser.add_argument("--preloaded-polarity", type=int, choices=[0, 1], default=0)
    parser.add_argument("--crossing-hysteresis-counts", type=int, default=4)
    parser.add_argument("--crossing-consecutive-samples", type=int, default=3)
    parser.add_argument("--kp-ramp-step", type=int, default=1)
    parser.add_argument("--kp-ramp-div", type=int, default=1)
    parser.add_argument("--acquire-timeout-cycles", type=int, default=12500000)
    parser.add_argument("--servo-update-div", type=int, default=125)
    parser.add_argument("--out2-slew-limit-counts", type=int, default=1)
    parser.add_argument("--observe-shift", type=int, default=8)
    parser.add_argument("--lock-confirm-windows", type=int, default=4)
    parser.add_argument("--divergence-windows", type=int, default=4)
    parser.add_argument("--error-mean-limit-counts", type=int, default=16)
    parser.add_argument("--error-abs-limit-counts", type=int, default=32)
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
        elif args.op == "preload-acquisition":
            status = run_preload_acquisition(regs, args, False)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "arm-acquisition":
            status = run_preload_acquisition(regs, args, True)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "validate-acquisition":
            status = run_preload_acquisition(regs, args, True, validate=True)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "acquisition-status":
            require_magic(regs)
            status = acquisition_status(regs)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "abort-acquisition":
            require_magic(regs)
            regs.write(REGISTERS["ACQ_COMMAND"], 2)
            status = acquisition_status(regs)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "clear-acquisition-event":
            require_magic(regs)
            regs.write(REGISTERS["ACQ_COMMAND"], 4)
            status = acquisition_status(regs)
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        elif args.op == "capture":
            require_magic(regs)
            status = read_status(regs)
            status.update(capture_waveform(regs, args.capture_length, args.capture_decimation))
            print(json.dumps(status, indent=2, sort_keys=True))
            return
        status = acquisition_status(regs)
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
    config_generation: int


@dataclass
class AcquisitionTargetConfig:
    target_out2_counts: int
    target_error_setpoint_counts: int
    target_window_counts: int
    required_scan_direction: int
    required_error_crossing_direction: int
    initial_polarity_suggestion: int
    correction_limit_counts: int
    absolute_limit_counts: int
    config_generation: int
    preloaded_kp: int = 0
    preloaded_polarity: int = 0


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
    if getattr(args, "hold_counts", None) is not None:
        hold_counts = int(args.hold_counts)
        if hold_counts < -8191 or hold_counts > 8191:
            raise ValueError("--hold-counts must be within signed 14-bit DAC range")
        return HoldConfig(hold_counts=hold_counts)
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
        config_generation=max(0, int(args.config_generation)),
    )


def build_acquisition_target_config(args: argparse.Namespace) -> AcquisitionTargetConfig:
    target = int(args.target_out2_counts)
    setpoint = int(args.target_error_setpoint_counts)
    window = int(args.target_window_counts)
    correction = int(args.correction_limit_counts)
    absolute = int(args.absolute_limit_counts)
    if target < -8191 or target > 8191 or setpoint < -8191 or setpoint > 8191:
        raise SystemExit("acquisition target and error setpoint must be within -8191..8191")
    if window <= 0 or target - window < -8191 or target + window > 8191:
        raise SystemExit("acquisition target window exceeds signed DAC range")
    if correction < 0 or correction > absolute or absolute > 8191:
        raise SystemExit("acquisition limits must satisfy 0 <= correction <= absolute <= 8191")
    if int(args.config_generation) <= 0:
        raise SystemExit("acquisition config generation must be positive")
    return AcquisitionTargetConfig(
        target_out2_counts=target,
        target_error_setpoint_counts=setpoint,
        target_window_counts=window,
        required_scan_direction=int(args.required_scan_direction),
        required_error_crossing_direction=int(args.required_error_crossing_direction),
        initial_polarity_suggestion=int(args.initial_polarity_suggestion),
        correction_limit_counts=correction,
        absolute_limit_counts=absolute,
        config_generation=int(args.config_generation),
        preloaded_kp=int(args.preloaded_kp),
        preloaded_polarity=int(args.preloaded_polarity),
    )


def remote_command(
    args: argparse.Namespace,
    op: str,
    config: ScanConfig | HoldConfig | LockConfig | UpdatePLockConfig | AcquisitionTargetConfig | None,
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
            "--config-generation",
            str(config.config_generation),
        ]
    elif isinstance(config, AcquisitionTargetConfig):
        remote_args += [
            "--target-out2-counts",
            str(config.target_out2_counts),
            "--target-error-setpoint-counts",
            str(config.target_error_setpoint_counts),
            "--target-window-counts",
            str(config.target_window_counts),
            "--required-scan-direction",
            str(config.required_scan_direction),
            "--required-error-crossing-direction",
            str(config.required_error_crossing_direction),
            "--initial-polarity-suggestion",
            str(config.initial_polarity_suggestion),
            "--correction-limit-counts",
            str(config.correction_limit_counts),
            "--absolute-limit-counts",
            str(config.absolute_limit_counts),
            "--config-generation",
            str(config.config_generation),
            "--preloaded-kp",
            str(config.preloaded_kp),
            "--preloaded-polarity",
            str(config.preloaded_polarity),
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

    hold_parser = subparsers.add_parser("hold", help="Set fixed OUT2 voltage/count and enable HOLD mode")
    hold_source = hold_parser.add_mutually_exclusive_group()
    hold_source.add_argument("--hold-v", type=float, default=0.0)
    hold_source.add_argument("--hold-counts", type=int, default=None)

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
    update_p_parser.add_argument("--config-generation", type=int, default=0)

    def add_acquisition_arguments(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--target-out2-counts", type=int, required=True)
        command_parser.add_argument("--target-error-setpoint-counts", type=int, default=0)
        command_parser.add_argument("--target-window-counts", type=int, default=64)
        command_parser.add_argument("--required-scan-direction", type=int, choices=[1, 2], required=True)
        command_parser.add_argument(
            "--required-error-crossing-direction",
            type=int,
            choices=[1, 2],
            required=True,
        )
        command_parser.add_argument("--initial-polarity-suggestion", type=int, choices=[0, 1], default=0)
        command_parser.add_argument("--correction-limit-counts", type=int, default=128)
        command_parser.add_argument("--absolute-limit-counts", type=int, default=8191)
        command_parser.add_argument("--config-generation", type=int, required=True)
        command_parser.add_argument("--preloaded-kp", type=int, choices=[0, 4], default=0)
        command_parser.add_argument("--preloaded-polarity", type=int, choices=[0, 1], default=0)

    preload_acq_parser = subparsers.add_parser(
        "preload-acquisition",
        help="Write and validate the deterministic acquisition shadow configuration",
    )
    add_acquisition_arguments(preload_acq_parser)
    arm_acq_parser = subparsers.add_parser(
        "arm-acquisition",
        help="Write the target shadow configuration and issue exactly one FPGA ARM command",
    )
    add_acquisition_arguments(arm_acq_parser)
    subparsers.add_parser("acquisition-status", help="Read coherent acquisition state and sticky event")
    subparsers.add_parser("abort-acquisition", help="Abort an armed acquisition into SAFE")
    subparsers.add_parser("clear-acquisition-event", help="Clear the sticky acquisition event in SAFE")

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
    elif args.command in {"preload-acquisition", "arm-acquisition"}:
        config = build_acquisition_target_config(args)
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
                    # config_generation={config.config_generation}
                    # normal path applies P only to the matching triggered generation
                    """
                ).strip()
            )
        elif isinstance(config, AcquisitionTargetConfig):
            print(
                textwrap.dedent(
                    f"""
                    # deterministic acquisition target
                    # target_out2_counts={config.target_out2_counts}
                    # target_error_setpoint_counts={config.target_error_setpoint_counts}
                    # target_window_counts={config.target_window_counts}
                    # required_scan_direction={config.required_scan_direction}
                    # required_error_crossing_direction={config.required_error_crossing_direction}
                    # initial_polarity_suggestion={config.initial_polarity_suggestion}
                    # correction_limit_counts={config.correction_limit_counts}
                    # absolute_limit_counts={config.absolute_limit_counts}
                    # config_generation={config.config_generation}
                    """
                ).strip()
            )
        print_command(command)
        return 0

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
