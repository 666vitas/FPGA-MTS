import importlib.util
import os
import sys
from pathlib import Path

from redpitaya_lock_host.custom_fpga_backend import (
    build_lock_config_from_counts,
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

    for marker in (
        'if args.op == "safe":',
        'elif args.op == "scan":',
        'elif args.op == "hold":',
        'elif args.op == "p-lock":',
        'elif args.op == "pi-lock":',
    ):
        op_start = source.index(marker)
        op_require = source.index("require_magic(regs)", op_start)
        op_write = source.index("regs.write", op_start)
        assert op_require < op_write


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
    hold_start = helper.index('elif args.op == "hold":')
    p_lock_start = helper.index('elif args.op == "p-lock":')
    pi_lock_start = helper.index('elif args.op == "pi-lock":')
    readback_start = helper.index("status = read_status(regs)", pi_lock_start)

    assert safe_start < readback_start
    assert scan_start < readback_start
    assert hold_start < readback_start
    assert p_lock_start < readback_start
    assert pi_lock_start < readback_start


def test_one_click_lock_bias_uses_out2_monitor_counts_not_voltage_estimate() -> None:
    config = build_lock_config_from_counts(
        kp=256,
        ki=123,
        polarity=1,
        lock_bias_counts=4522,
        lock_limit_counts=8191,
        correction_limit_counts=128,
    )

    assert config.lock_bias_counts == 4522
    assert config.kp == 256
    assert config.ki == 123
    assert config.polarity == 1
    assert config.lock_limit_counts == 8191
    assert config.correction_limit_counts == 128


def test_custom_fpga_cli_exposes_hold_p_lock_and_pi_lock_without_default_gain() -> None:
    custom_fpga_scan_control = load_scan_control_module()

    for command in ("hold", "p-lock", "pi-lock"):
        args = custom_fpga_scan_control.parse_args(["--host", "rp.local", command])
        assert args.command == command

    p_args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "p-lock"])
    pi_args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "pi-lock"])
    auto_args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "auto-lock"])
    assert p_args.kp == 0
    assert pi_args.kp == 0
    assert pi_args.ki == 0
    assert p_args.correction_limit_counts == 128
    assert auto_args.command == "auto-lock"
    assert auto_args.correction_limit_counts == 128


def test_gui_text_separates_scpi_and_custom_fpga_out2_paths() -> None:
    source = (ROOT / "redpitaya_lock_host" / "main_window.py").read_text(encoding="utf-8")

    assert "OUT2 = FPGA laser_control" not in source
    assert "OUT2=laser_control" not in source
    assert "OUT2 is laser_control" not in source
    assert "Custom FPGA Lock Host" in source
    assert "Official SCPI/ASG controls are hidden from the main lock workflow" in source
    assert "Capture Bias" in source
    assert "UNLOCK / SAFE" in source
    assert "Current LOCK=P-only; Ki/PI disabled" in source
    assert "LOCK_BIAS source: captured OUT2_MONITOR" in source
    assert "SCPI ASG output commands do not drive physical OUT2" in source
    assert "Custom FPGA Scope" in source
    assert "custom_debug_capture not available" in source
    assert "CAPTURE_CTRL, CAPTURE_STATUS, CAPTURE_DECIMATION" in source
    assert "ARM AUTO LOCK" in source
    assert "ABORT AUTO LOCK" in source


def test_gui_startup_does_not_require_legacy_scpi_output_controls() -> None:
    source = (ROOT / "redpitaya_lock_host" / "main_window.py").read_text(encoding="utf-8")

    assert 'addTab(self._hardware_bringup_page(), "Hardware Bring-up")' not in source
    assert "def _scpi_controls_available(self)" in source
    assert "if self._scpi_controls_available():" in source


def test_main_window_constructs_without_legacy_scpi_output_controls() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        assert not hasattr(window, "out1")
        assert not hasattr(window, "out2")
        assert window.custom_probe_button.text() == "Probe Registers"
        assert window.custom_lock_button.text() == "LOCK"
        assert window.custom_arm_auto_lock_button.text() == "ARM AUTO LOCK"
        assert window.custom_correction_limit_counts.value() == 128
    finally:
        window.close()
        app.processEvents()
