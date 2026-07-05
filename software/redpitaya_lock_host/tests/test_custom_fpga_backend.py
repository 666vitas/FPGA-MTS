from pathlib import Path

from redpitaya_lock_host.custom_fpga_backend import (
    status_payload_has_expected_magic,
    missing_magic_guidance,
)


ROOT = Path(__file__).resolve().parents[1]


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
