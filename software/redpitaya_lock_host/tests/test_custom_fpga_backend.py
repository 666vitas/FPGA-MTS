import importlib.util
import os
import sys
from pathlib import Path

from redpitaya_lock_host.custom_fpga_backend import (
    EXPECTED_VERSION,
    build_update_p_lock_config,
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

    for command in ("hold", "p-lock", "pi-lock", "lock-here", "update-p-lock"):
        args = custom_fpga_scan_control.parse_args(["--host", "rp.local", command])
        assert args.command == command

    p_args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "p-lock"])
    pi_args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "pi-lock"])
    lock_here_args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "lock-here"])
    update_p_args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "update-p-lock"])
    assert p_args.kp == 0
    assert pi_args.kp == 0
    assert pi_args.ki == 0
    assert p_args.correction_limit_counts == 128
    assert lock_here_args.command == "lock-here"
    assert lock_here_args.correction_limit_counts == 128
    assert lock_here_args.target_out2_counts is None
    assert lock_here_args.target_window_counts == 64
    assert update_p_args.kp == 0


def test_update_p_lock_accepts_only_manual_small_kp_steps() -> None:
    custom_fpga_scan_control = load_scan_control_module()

    for kp in (0, 4, 8, 16, 32):
        args = custom_fpga_scan_control.parse_args(["--host", "rp.local", "update-p-lock", "--kp", str(kp)])
        config = custom_fpga_scan_control.build_update_p_lock_config(args)
        backend_config = build_update_p_lock_config(kp=kp, polarity=1)
        assert config.kp == kp
        assert backend_config.kp == kp

    try:
        custom_fpga_scan_control.parse_args(["--host", "rp.local", "update-p-lock", "--kp", "64"])
    except SystemExit:
        pass
    else:
        raise AssertionError("update-p-lock accepted a non-whitelisted Kp")


def test_update_p_lock_keeps_captured_lock_point_registers_untouched() -> None:
    custom_fpga_scan_control = load_scan_control_module()
    helper = custom_fpga_scan_control.REMOTE_HELPER

    run_start = helper.index("def run_update_p_lock(regs, args):")
    next_function = helper.index("\ndef probe_base_addresses", run_start)
    run_body = helper[run_start:next_function]
    normal_start = run_body.index("# Normal update writes only KP and POLARITY.")
    normal_end = run_body.index("# Post-update verification", normal_start)
    normal_body = run_body[normal_start:normal_end]

    assert "require_magic(regs)" in run_body
    assert "EXPECTED_VERSION" in run_body
    assert "MODE=3" in run_body
    assert "ENABLE=1" in run_body
    assert "saturation" in run_body
    assert "first APPLY P with --kp 0" in run_body
    assert 'regs.write(REGISTERS["KP"], args.kp)' in normal_body
    assert 'regs.write(REGISTERS["POLARITY"], requested_polarity)' in normal_body
    for forbidden in (
        "ERROR_SETPOINT",
        "LOCK_BIAS",
        "CAPTURE_LOCK_POINT",
        "MODE",
        "ENABLE",
        "KI",
        "INTEGRAL_RESET",
        "LOCK_LIMIT",
        "LOCK_CORRECTION_LIMIT",
    ):
        assert f'regs.write(REGISTERS["{forbidden}"]' not in normal_body


def test_update_p_lock_safes_on_post_update_lock_point_or_saturation_failure() -> None:
    custom_fpga_scan_control = load_scan_control_module()
    helper = custom_fpga_scan_control.REMOTE_HELPER

    assert "def safe_exit(regs, reason):" in helper
    assert 'regs.write(REGISTERS["KP"], 0)' in helper
    assert 'regs.write(REGISTERS["ENABLE"], 0)' in helper
    assert 'regs.write(REGISTERS["MODE"], 0)' in helper
    assert "before_error_setpoint != int(after" in helper
    assert "before_lock_bias != after_lock_bias" in helper
    assert "bool(after[\"saturated\"])" in helper


def test_remote_helper_register_map_includes_lock_here_setpoint_registers() -> None:
    custom_fpga_scan_control = load_scan_control_module()

    assert custom_fpga_scan_control.REGISTERS["ERROR_SETPOINT"] == 0x54
    assert custom_fpga_scan_control.REGISTERS["LOCK_ERROR_MONITOR"] == 0x58
    assert custom_fpga_scan_control.REGISTERS["CAPTURE_LOCK_POINT"] == 0x5C
    assert f"EXPECTED_VERSION = 0x{EXPECTED_VERSION:08X}" in custom_fpga_scan_control.REMOTE_HELPER
    assert '"lock-here"' in custom_fpga_scan_control.REMOTE_HELPER


def test_lock_here_does_not_embed_historical_board_values() -> None:
    source = (ROOT / "scripts" / "custom_fpga_scan_control.py").read_text(encoding="utf-8")
    gui_source = (ROOT / "redpitaya_lock_host" / "main_window.py").read_text(encoding="utf-8")
    backend_source = (ROOT / "redpitaya_lock_host" / "custom_fpga_backend.py").read_text(encoding="utf-8")

    combined = "\n".join([source, gui_source, backend_source])
    for forbidden in ("0.704", "0.784", "49.75", "54 counts"):
        assert forbidden not in combined


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
    assert "LOCK_BIAS source: FPGA CAPTURE_LOCK_POINT captured OUT2_MONITOR" in source
    assert "ERROR_SETPOINT source: FPGA CAPTURE_LOCK_POINT captured ERROR_MONITOR" in source
    assert "SCPI ASG output commands do not drive physical OUT2" in source
    assert "Custom FPGA Scope" in source
    assert "custom_debug_capture not available" in source
    assert "CAPTURE_CTRL, CAPTURE_STATUS, CAPTURE_DECIMATION" in source
    assert "LOCK HERE" in source
    assert "APPLY P" in source
    assert "ABORT / SAFE" in source
    assert "ARM AUTO LOCK" not in source
    assert "AUTO LOCK" not in source


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
        assert window.custom_lock_button.text() == "LOCK HERE"
        assert window.custom_apply_p_button.text() == "APPLY P"
        assert [window.custom_kp.itemText(index) for index in range(window.custom_kp.count())] == ["0", "4", "8", "16", "32"]
        assert window.custom_correction_limit_counts.value() == 128
        assert window.custom_lock_limit_counts.value() == 8191
    finally:
        window.close()
        app.processEvents()
