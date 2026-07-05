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
}


REMOTE_HELPER = r"""
import argparse
import json
import mmap
import os
import struct
import sys

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
}

EXPECTED_MAGIC = 0x4D545330


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
        self.mem.flush()


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


def read_status(regs):
    status = regs.read(REGISTERS["STATUS"])
    out2_raw = regs.read(REGISTERS["OUT2_MONITOR"])
    return {
        "magic": f"0x{regs.read(REGISTERS['MAGIC']):08X}",
        "version": f"0x{regs.read(REGISTERS['VERSION']):08X}",
        "mode": regs.read(REGISTERS["MODE"]),
        "enable": regs.read(REGISTERS["ENABLE"]) & 1,
        "status_raw": f"0x{status:08X}",
        "enabled": bool(status & 1),
        "saturated": bool(status & 2),
        "out2_counts": to_signed14(out2_raw),
        "out2_volts": to_signed14(out2_raw) / 8191.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-addr", default="0x40600000")
    parser.add_argument("--op", choices=["safe", "scan", "status"], required=True)
    parser.add_argument("--offset-counts", type=int, default=6962)
    parser.add_argument("--amp-counts", type=int, default=410)
    parser.add_argument("--step-counts", type=int, default=1)
    parser.add_argument("--update-div", type=int, default=1524)
    parser.add_argument("--limit-counts", type=int, default=8191)
    args = parser.parse_args()

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
        print(json.dumps(read_status(regs), indent=2, sort_keys=True))
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


def remote_command(args: argparse.Namespace, op: str, config: ScanConfig | None) -> list[str]:
    helper_b64 = base64.b64encode(REMOTE_HELPER.encode("utf-8")).decode("ascii")
    remote_args = [
        "--base-addr",
        f"0x{args.base_addr:X}",
        "--op",
        op,
    ]
    if config is not None:
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

    subparsers.add_parser("status", help="Read magic/version/status/out2 monitor")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config = build_scan_config(args) if args.command == "scan" else None
    command = remote_command(args, args.command, config)

    if args.print_command:
        if config is not None:
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
        print_command(command)
        return 0

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
