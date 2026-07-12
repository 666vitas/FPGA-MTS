import importlib.util
import os
import sys
from pathlib import Path

import numpy as np

from redpitaya_lock_host.custom_fpga_backend import (
    EXPECTED_VERSION,
    CustomFpgaBackendError,
    build_basic_lock_config,
    build_update_p_lock_config,
    build_lock_config_from_counts,
    find_zero_crossing_candidates,
    resolve_target_transition,
    status_payload_has_expected_magic,
    missing_magic_guidance,
    validate_basic_lock_capture,
)


ROOT = Path(__file__).resolve().parents[1]


def make_capture_payload(count: int = 256) -> dict:
    x = np.linspace(-1.0, 1.0, count)
    config = build_basic_lock_config(safe_min_v=0.80, safe_max_v=0.90)
    ch4 = np.linspace(config.safe_min_counts, config.safe_max_counts, count)
    error = 260.0 * x * np.exp(-(x * 3.5) ** 2)
    return {
        "magic": "0x4D545330",
        "version": "0x00030001",
        "mode": 1,
        "enable": 1,
        "saturated": False,
        "out2_counts": int(ch4[count // 2]),
        "lock_error_counts": 0,
        "lock_correction_limit_counts": 128,
        "capture_decimation": 1024,
        "points": [
            {
                "index": idx,
                "ch1_counts": int(80 * np.exp(-((x[idx]) * 6.0) ** 2)),
                "ch2_counts": int(3000 * np.sin(idx / 3)),
                "ch3_counts": int(error[idx]),
                "ch4_counts": int(ch4[idx]),
            }
            for idx in range(count)
        ],
    }


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


def test_basic_lock_pzt_range_generates_scan_and_capture_parameters() -> None:
    config = build_basic_lock_config(safe_min_v=0.80, safe_max_v=0.90)

    assert round(config.offset_v, 6) == 0.85
    assert round(config.amp_v, 6) == 0.05
    assert config.freq_hz == 10.0
    assert config.step_counts == 1
    assert config.capture_length == 2048
    assert config.capture_decimation == round(125_000_000 / (10 * 2048))
    assert config.safe_min_counts <= config.safe_max_counts


def test_basic_lock_rejects_invalid_pzt_range() -> None:
    for safe_min, safe_max in ((0.9, 0.8), (-1.2, 0.2), (0.0, 1.2)):
        try:
            build_basic_lock_config(safe_min_v=safe_min, safe_max_v=safe_max)
        except CustomFpgaBackendError:
            pass
        else:
            raise AssertionError("invalid PZT range was accepted")


def test_basic_lock_capture_validation_rejects_zero_flat_and_out_of_range_data() -> None:
    config = build_basic_lock_config(safe_min_v=0.80, safe_max_v=0.90)
    out2 = np.linspace(config.safe_min_counts, config.safe_max_counts, 128)

    try:
        validate_basic_lock_capture(
            ch1_counts=np.zeros(128),
            ch3_counts=np.sin(np.linspace(0, 8, 128)) * 20,
            ch4_counts=out2,
            safe_min_counts=config.safe_min_counts,
            safe_max_counts=config.safe_max_counts,
            saturated=False,
        )
    except CustomFpgaBackendError as exc:
        assert "CH1/PD" in str(exc)
    else:
        raise AssertionError("all-zero PD data was accepted")

    try:
        validate_basic_lock_capture(
            ch1_counts=np.sin(np.linspace(0, 8, 128)) * 20,
            ch3_counts=np.zeros(128),
            ch4_counts=out2,
            safe_min_counts=config.safe_min_counts,
            safe_max_counts=config.safe_max_counts,
            saturated=False,
        )
    except CustomFpgaBackendError as exc:
        assert "CH3/error" in str(exc)
    else:
        raise AssertionError("flat error data was accepted")

    try:
        validate_basic_lock_capture(
            ch1_counts=np.sin(np.linspace(0, 8, 128)) * 20,
            ch3_counts=np.sin(np.linspace(0, 8, 128)) * 20,
            ch4_counts=out2 + 1000,
            safe_min_counts=config.safe_min_counts,
            safe_max_counts=config.safe_max_counts,
            saturated=False,
        )
    except CustomFpgaBackendError as exc:
        assert "safe range" in str(exc)
    else:
        raise AssertionError("out-of-range OUT2 data was accepted")


def test_basic_lock_zero_crossing_finder_rejects_edges_and_flat_baseline() -> None:
    flat = np.zeros(256)
    out2 = np.linspace(6500, 7300, 256)

    assert find_zero_crossing_candidates(error_counts=flat, out2_counts=out2) == []

    edge_error = np.ones(256) * 100
    edge_error[:2] = -100
    assert find_zero_crossing_candidates(error_counts=edge_error, out2_counts=out2) == []


def test_basic_lock_zero_crossing_finder_detects_dispersion_candidate() -> None:
    x = np.linspace(-1.0, 1.0, 512)
    error = 260.0 * x * np.exp(-(x * 3.5) ** 2)
    out2 = np.linspace(6500, 7300, 512)

    candidates = find_zero_crossing_candidates(error_counts=error, out2_counts=out2)

    assert candidates
    assert abs(candidates[0].index - 255) < 20
    assert 6500 <= candidates[0].out2_counts <= 7300


def test_pd_click_resolves_nearby_ch3_error_zero_crossing() -> None:
    count = 512
    x = np.linspace(-1.0, 1.0, count)
    error = 260.0 * x * np.exp(-(x * 3.5) ** 2)
    out2 = np.linspace(6500, 7300, count)

    resolved = resolve_target_transition(
        error_counts=error,
        out2_counts=out2,
        clicked_index=250,
        safe_min_counts=6400,
        safe_max_counts=7400,
        saturated=False,
        search_radius=80,
    )

    assert resolved.valid
    assert abs(resolved.index - 255) < 20
    assert 6500 <= resolved.out2_counts <= 7300
    assert abs(resolved.slope) > 0


def test_pd_click_without_zero_crossing_is_rejected() -> None:
    with np.testing.assert_raises(CustomFpgaBackendError):
        resolve_target_transition(
            error_counts=np.ones(256) * 42,
            out2_counts=np.linspace(6500, 7300, 256),
            clicked_index=128,
            safe_min_counts=6400,
            safe_max_counts=7400,
        )


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
    assert "BASIC LOCK" in source
    assert "PZT safe min" in source
    assert "PZT safe max" in source
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
        assert window.basic_lock_button.text() == "BASIC LOCK"
        assert window.basic_safe_button.text() == "SAFE"
        assert not window.custom_advanced_body.isVisible()
        assert window.custom_lock_button.text() == "LOCK HERE"
        assert window.custom_apply_p_button.text() == "APPLY P"
        assert [window.custom_kp.itemText(index) for index in range(window.custom_kp.count())] == ["0", "4", "8", "16", "32"]
        assert window.custom_correction_limit_counts.value() == 128
        assert window.custom_lock_limit_counts.value() == 8191
        assert window.custom_capture_once_button.text() == "Capture Once"
        assert window.custom_start_live_button.text() == "Start Live"
        assert window.custom_stop_live_button.text() == "Stop Live"
        assert window.custom_live_interval_ms.currentText() == "1000"
        assert set(window.custom_scope_curves) == {"ch1", "ch2", "ch3", "ch4"}
    finally:
        window.close()
        app.processEvents()


def test_live_capture_does_not_reenter_while_capture_in_flight() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    calls = []
    try:
        window.live_capture_active = True
        window.capture_in_flight = True
        window._start_custom_fpga_operation = lambda operation, preserve_basic=False: calls.append(operation)

        window._run_live_capture_cycle()

        assert calls == []
    finally:
        window.close()
        app.processEvents()


def test_live_capture_schedules_next_only_after_capture_finished() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    class FakeTimer:
        def __init__(self) -> None:
            self.started = []
            self.stopped = False

        def start(self, interval: int) -> None:
            self.started.append(interval)

        def stop(self) -> None:
            self.stopped = True

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    fake_timer = FakeTimer()
    try:
        window.custom_live_timer = fake_timer
        window.live_capture_active = True
        window.capture_in_flight = True
        window.current_custom_operation = "capture"
        window._restore_after_custom_fpga_operation = lambda: None
        window._continue_basic_lock_after_success = lambda operation, payload: None

        window._on_custom_fpga_finished({"operation": "capture", "payload": make_capture_payload(), "stderr": ""})

        assert not window.capture_in_flight
        assert fake_timer.started == [1000]
        assert window.current_custom_operation is None
    finally:
        window.close()
        app.processEvents()


def test_stop_live_prevents_future_capture_scheduling() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    class FakeTimer:
        def __init__(self) -> None:
            self.started = []
            self.stopped = False

        def start(self, interval: int) -> None:
            self.started.append(interval)

        def stop(self) -> None:
            self.stopped = True

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    fake_timer = FakeTimer()
    try:
        window.custom_live_timer = fake_timer
        window.live_capture_active = True
        window._stop_live_capture("test stop")
        window._schedule_next_live_capture()

        assert not window.live_capture_active
        assert fake_timer.stopped
        assert fake_timer.started == []
    finally:
        window.close()
        app.processEvents()


def test_channel_scale_and_center_do_not_mutate_raw_capture_data() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload(make_capture_payload())
        before = window.custom_scope_data["ch1"].copy()

        # Toggle auto range off/on — display changes, raw data unchanged
        window.custom_scope_auto_range_check.setChecked(False)
        window._fit_custom_scope_ranges()
        window.custom_scope_auto_range_check.setChecked(True)
        window._fit_custom_scope_ranges()

        np.testing.assert_array_equal(window.custom_scope_data["ch1"], before)
        # Y range should be set (non-empty)
        y_range = window.custom_scope_plot.viewRange()[1]
        assert y_range[0] < y_range[1]
    finally:
        window.close()
        app.processEvents()


def test_basic_lock_internal_safe_step_does_not_abort_state_machine() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    calls = []
    try:
        def fake_start(operation: str, *, preserve_basic: bool = False) -> None:
            calls.append((operation, preserve_basic))

        window._start_custom_fpga_operation = fake_start
        window.basic_lock_active = True
        window.basic_lock_queue = ["safe", "scan"]

        window._continue_basic_lock()

        assert calls == [("safe", True)]
        assert window.basic_lock_active
        assert window.basic_lock_queue == ["scan"]
        assert "SAFE" in window.basic_status_label.text()
    finally:
        window.close()
        app.processEvents()


def test_lock_here_requires_confirmed_lock_point_not_pending_candidate() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload(make_capture_payload())

        assert window.pending_lock_point is not None
        assert window.selected_lock_point is None

        window._start_custom_fpga_operation("lock")

        assert "LOCK HERE requires" in window.custom_warning_text.toPlainText()
        assert window.current_custom_operation is None
    finally:
        window.close()
        app.processEvents()


def test_confirm_lock_point_promotes_pending_zero_crossing_only() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._confirm_pending_lock_point()
        assert window.selected_lock_point is None

        window._render_custom_capture_payload(make_capture_payload())
        pending = dict(window.pending_lock_point)
        window._confirm_pending_lock_point()

        assert window.selected_lock_point == pending
        assert "confirmed" in window.selected_lock_label.text()
    finally:
        window.close()
        app.processEvents()


def test_basic_lock_lock_here_stops_at_p_lock_kp_zero_without_auto_gain() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.basic_lock_active = True
        window.basic_lock_queue = []
        window.custom_kp.setCurrentText("16")

        window._continue_basic_lock_after_success("lock", {})

        assert not window.basic_lock_active
        assert window.basic_lock_queue == []
        assert window.custom_kp.currentText() == "0"
        assert "P_LOCK" in window.basic_status_label.text()
        assert "Kp=0" in window.basic_status_label.text()
    finally:
        window.close()
        app.processEvents()


def test_custom_scope_empty_capture_reports_missing_real_fpga_interface() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload({"points": []})

        stats = window.custom_scope_stats.text()
        assert "custom_debug_capture unavailable" in stats
        assert "CAPTURE_CTRL" in stats
        assert "no register-only fallback" in stats
        assert window.custom_scope_placeholder.isVisible()
        assert window.basic_candidate_label.text().startswith("candidate: unavailable")
        assert all(not curve.isVisible() for curve in window.custom_scope_curves.values())
    finally:
        window.close()
        app.processEvents()


def test_basic_lock_capture_failure_transitions_to_safe_fail() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    calls = []
    try:
        def fake_start(operation: str, *, preserve_basic: bool = False) -> None:
            calls.append((operation, preserve_basic))

        window._start_custom_fpga_operation = fake_start
        window.basic_lock_active = True
        window.current_custom_operation = "capture"

        window._on_custom_fpga_failed("capture timeout")
        app.processEvents()

        assert not window.basic_lock_active
        assert window.basic_lock_queue == []
        assert "SAFE_FAIL" in window.basic_status_label.text()
        assert "capture failed" in window.basic_status_label.text()
        assert calls == [("safe", False)]
        assert "Custom FPGA capture failed" in window.custom_register_summary.text()
    finally:
        window.close()
        app.processEvents()


def test_gui_startup_probe_reads_status_without_scpi_overlay() -> None:
    source = (ROOT / "redpitaya_lock_host" / "main_window.py").read_text(encoding="utf-8")

    assert "def _startup_custom_register_probe" in source
    assert '_start_custom_fpga_operation("status", preserve_basic=True)' in source
    assert "does not start redpitaya_scpi" in source


def test_waveform_plot_dark_theme_uses_visible_axes_curves_and_placeholder() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.waveform_plot import DEFAULT_CURVE, PLOT_FOREGROUND, WaveformPlot
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    plot = WaveformPlot("Custom FPGA Scope", "Counts")
    try:
        assert PLOT_FOREGROUND.lower() != "#000000"
        assert DEFAULT_CURVE.lower() != "#000000"
        assert plot.placeholder is not None
        plot.set_placeholder_text("custom_debug_capture not available")
        assert plot.placeholder.isVisible()
        plot.set_data(np.arange(16), np.linspace(-10, 10, 16))
        assert not plot.placeholder.isVisible()
        assert plot.curve.isVisible()
        assert len(plot.curve.xData) == 16
        assert len(plot.curve.yData) == 16
    finally:
        plot.close()
        app.processEvents()


def test_custom_scope_render_payload_shows_curves_range_and_candidate() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        count = 256
        x = np.linspace(-1.0, 1.0, count)
        config = build_basic_lock_config(safe_min_v=0.80, safe_max_v=0.90)
        ch4 = np.linspace(config.safe_min_counts, config.safe_max_counts, count)
        error = 240.0 * x * np.exp(-(x * 3.2) ** 2)
        payload = {
            "capture_decimation": 1024,
            "mode": 1,
            "saturated": False,
            "out2_counts": int(ch4[count // 2]),
            "lock_correction_limit_counts": 128,
            "points": [
                {
                    "index": idx,
                    "ch1_counts": int(50 * np.sin(idx / 12)),
                    "ch2_counts": int(3000 * np.sin(idx / 3)),
                    "ch3_counts": int(error[idx]),
                    "ch4_counts": int(ch4[idx]),
                }
                for idx in range(count)
            ],
        }

        window._render_custom_capture_payload(payload)

        # All 4 curves have data
        for key in ("ch1", "ch2", "ch3", "ch4"):
            curve = window.custom_scope_curves[key]
            assert len(curve.xData) == count, f"{key} xData length mismatch"
            assert len(curve.yData) == count, f"{key} yData length mismatch"
        # Placeholder hidden
        assert not window.custom_scope_placeholder.isVisible()
        # Y range includes data
        y_range = window.custom_scope_plot.viewRange()[1]
        assert y_range[0] <= float(np.nanmin(error))
        assert y_range[1] >= float(np.nanmax(ch4))
        # BASIC LOCK candidates found
        assert window.basic_lock_candidates
        assert window.selected_lock_point is None
        assert window.pending_lock_point is not None
        assert int(window.pending_lock_point["index"]) != 0
        # Stats show non-zero Vpp
        stats = window.custom_scope_stats.text()
        assert "Vpp" in stats
    finally:
        window.close()
        app.processEvents()


def test_custom_scope_embedded_split_plots_render_real_capture_points() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.show()
        app.processEvents()
        count = 2048
        phase = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
        triangle = 6962.0 + 410.0 * (2.0 * np.abs(2.0 * (np.arange(count) / count) - 1.0) - 1.0)
        error = 42.0 * np.sin(phase) + 8.0 * np.sin(phase * 3.0)
        payload = {
            "capture_decimation": 1024,
            "mode": 1,
            "saturated": False,
            "out2_counts": int(triangle[count // 2]),
            "lock_correction_limit_counts": 128,
            "points": [
                {
                    "index": idx,
                    "ch1_counts": int(120 * np.sin(phase[idx])),
                    "ch2_counts": int(2800 * np.sin(phase[idx] * 64.0)),
                    "ch3_counts": int(error[idx]),
                    "ch4_counts": int(triangle[idx]),
                }
                for idx in range(count)
            ],
        }

        window._render_custom_capture_payload(payload)
        app.processEvents()

        # Single plot with 4 overlaid curves
        assert hasattr(window, "custom_scope_plot")
        plot_item = window.custom_scope_plot.getPlotItem()
        assert plot_item.getAxis("bottom").isVisible()
        assert plot_item.getAxis("left").isVisible()

        # All 4 curves have data
        for key in ("ch1", "ch2", "ch3", "ch4"):
            curve = window.custom_scope_curves[key]
            assert len(curve.xData) == count, f"{key} xData length mismatch"
            assert len(curve.yData) == count, f"{key} yData length mismatch"
        assert window.custom_scope_curves["ch3"].isVisible()
        assert window.custom_scope_curves["ch4"].isVisible()
        assert not window.custom_scope_placeholder.isVisible()
    finally:
        window.close()
        app.processEvents()


def test_custom_scope_data_has_all_four_channels_after_capture() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload(make_capture_payload())

        assert window.custom_scope_data is not None
        for key in ("ch1", "ch2", "ch3", "ch4", "time_s"):
            assert key in window.custom_scope_data, f"missing {key} in custom_scope_data"
            assert window.custom_scope_data[key].size > 0, f"{key} is empty"
    finally:
        window.close()
        app.processEvents()


def test_custom_scope_stats_shows_nonzero_vpp_after_capture() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload(make_capture_payload())

        stats = window.custom_scope_stats.text()
        assert "Vpp" in stats
        assert "IN1 / PD" in stats
        assert "IN2 / REF" in stats
        assert "OUT1 / laser_error" in stats
        assert "OUT2 / selected_out2" in stats
        assert "MODE" in stats
    finally:
        window.close()
        app.processEvents()


def test_custom_scope_empty_points_shows_placeholder_not_fake_waveform() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload({"points": []})

        assert window.custom_scope_data is None
        assert window.custom_scope_placeholder.isVisible()
        for curve in window.custom_scope_curves.values():
            assert not curve.isVisible()
            xd = curve.xData
            assert xd is None or len(xd) == 0
    finally:
        window.close()
        app.processEvents()


def test_safe_range_violation_shows_out2_value_and_range() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.basic_pzt_min_v.setValue(0.80)
        window.basic_pzt_max_v.setValue(0.90)
        config = build_basic_lock_config(safe_min_v=0.80, safe_max_v=0.90)

        # OUT2 outside safe range
        payload = {
            "magic": "0x4D545330",
            "version": "0x00030001",
            "saturated": False,
            "out2_counts": config.safe_min_counts - 100,
            "out2_volts": (config.safe_min_counts - 100) / 8191.0,
            "lock_error_counts": 0,
        }
        hazard = window._capture_payload_hazard(payload)

        assert hazard is not None
        assert "OUT2 is outside" in hazard
        assert "safe_min" in hazard
        assert "safe_max" in hazard
        assert "suggestion" in hazard
    finally:
        window.close()
        app.processEvents()


def test_custom_scope_reset_view_restores_auto_range() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload(make_capture_payload())

        window.custom_scope_auto_range_check.setChecked(False)
        assert not window.custom_scope_auto_range_check.isChecked()

        window._reset_custom_scope_view()

        assert window.custom_scope_auto_range_check.isChecked()
    finally:
        window.close()
        app.processEvents()


def test_single_plot_curves_rendered_with_data_after_capture() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        payload = make_capture_payload(count=512)
        window._render_custom_capture_payload(payload)

        for key in ("ch1", "ch2", "ch3", "ch4"):
            curve = window.custom_scope_curves[key]
            xd = curve.xData
            yd = curve.yData
            assert xd is not None and len(xd) == 512, f"{key} xData wrong"
            assert yd is not None and len(yd) == 512, f"{key} yData wrong"
        assert not window.custom_scope_placeholder.isVisible()
    finally:
        window.close()
        app.processEvents()


def test_default_ch2_hidden_ch1_ch3_ch4_visible() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._render_custom_capture_payload(make_capture_payload())

        assert window.custom_scope_checks["ch1"].isChecked()
        assert window.custom_scope_checks["ch3"].isChecked()
        assert window.custom_scope_checks["ch4"].isChecked()
        assert not window.custom_scope_checks["ch2"].isChecked()
    finally:
        window.close()
        app.processEvents()
