import importlib.util
import sys
from pathlib import Path

from redpitaya_lock_host.custom_fpga_backend import (
    status_payload_has_expected_magic,
    missing_magic_guidance,
)


ROOT = Path(__file__).resolve().parents[1]


def load_scan_control_module():
    script_path = ROOT / "scripts" / "custom_fpga_scan_control.py"
    spec = importlib.util.spec_from_file_location("_test_custom_fpga_scan_control", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_status_payload_rejects_zero_magic_string() -> None:
    payload = {"magic": "0x00000000", "version": "0x00000000"}

    assert not status_payload_has_expected_magic(payload)
    assert "no custom_register_bank was read" in missing_magic_guidance(payload["magic"])


def test_status_payload_accepts_expected_magic_string() -> None:
    payload = {"magic": "0x4D545330"}

    assert status_payload_has_expected_magic(payload)


def test_remote_helper_requires_magic_before_safe_and_scan_writes() -> None:
    source = (ROOT / "scripts" / "custom_fpga_scan_control.py").read_text(encoding="utf-8")

    safe_start = source.index('if args.op == "safe":')
    safe_require = source.index("require_magic(regs)", safe_start)
    safe_write = source.index("regs.write", safe_start)
    assert safe_require < safe_write

    scan_start = source.index('elif args.op == "scan":')
    scan_require = source.index("require_magic(regs)", scan_start)
    scan_write = source.index("regs.write", scan_start)
    assert scan_require < scan_write


def test_remote_helper_mmio_writes_do_not_flush_dev_mem_mapping() -> None:
    custom_fpga_scan_control = load_scan_control_module()
    helper = custom_fpga_scan_control.REMOTE_HELPER

    write_start = helper.index("    def write(self, offset, value):")
    next_function = helper.index("\ndef read_magic", write_start)
    write_body = helper[write_start:next_function]

    assert "self.mem.write(pack32(value))" in write_body
    assert "self.mem.flush(" not in write_body
    assert "MMIO writes are posted" in write_body
    assert "mapped store itself" in write_body


def test_remote_helper_safe_and_scan_read_back_status_after_writes() -> None:
    custom_fpga_scan_control = load_scan_control_module()
    helper = custom_fpga_scan_control.REMOTE_HELPER

    safe_start = helper.index('if args.op == "safe":')
    scan_start = helper.index('elif args.op == "scan":')
    readback_start = helper.index("status = read_status(regs)", scan_start)

    assert safe_start < readback_start
    assert scan_start < readback_start


def test_gui_text_separates_scpi_and_custom_fpga_out2_paths() -> None:
    source = (ROOT / "redpitaya_lock_host" / "main_window.py").read_text(encoding="utf-8")

    assert "OUT2 = FPGA laser_control" not in source
    assert "OUT2=laser_control" not in source
    assert "OUT2 is laser_control" not in source
    assert "OUT2 = selected_out2 (SAFE/SCAN from custom_register_bank + ramp_generator) -> oscilloscope only" in source
    assert "SCPI Output Control is only for official ASG/overlay testing" in source
    assert "SCPI OUT2 commands may succeed" in source
    assert "will not drive physical OUT2" in source
    assert "Custom FPGA Observe -> Probe Registers -> Status -> SAFE/SCAN" in source
