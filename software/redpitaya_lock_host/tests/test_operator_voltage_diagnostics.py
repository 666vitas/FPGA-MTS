import os
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from redpitaya_lock_host.custom_fpga_backend import (
    CustomFpgaBackendError,
    build_hold_config_from_counts,
)
from redpitaya_lock_host.main_window import (
    CALIBRATION_LABEL,
    COUNTS_PER_VOLT,
    TRANSITION_JUMP_UNAVAILABLE,
    build_hold_selected_diagnostics,
    build_lock_transition_diagnostics,
    format_error_equivalent_voltage,
    format_operator_delta_voltage,
    format_operator_voltage,
    format_out2_command_counts,
    format_out2_delta_counts,
)
from redpitaya_lock_host.out2_calibration import (
    out2_counts_to_voltage,
    out2_delta_counts_to_voltage,
    out2_voltage_to_counts,
)


def identity_payload(**overrides) -> dict:
    payload = {
        "magic": "0x4D545330",
        "version": "0x00030001",
        "mode": 2,
        "enable": 1,
        "status_raw": "0x00000001",
        "saturated": False,
        "out2_counts": out2_voltage_to_counts(0.77),
        "error_counts": 12,
        "error_setpoint_counts": 10,
        "lock_error_counts": 2,
        "kp": 0,
        "polarity": 0,
    }
    payload.update(overrides)
    return payload


def confirmed_selection(generation: int = 1) -> dict:
    counts = out2_voltage_to_counts(0.77)
    return {
        "target_out2_counts": counts,
        "lock_bias_counts": counts,
        "error_setpoint_counts": 10,
        "error_residual_counts": 0.25,
        "slope": 4.5,
        "ramp_direction": "rising",
        "target_window_counts": 64,
        "capture_generation": generation,
    }


def make_window():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from redpitaya_lock_host.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    window.mock_check.setChecked(False)
    window.system_identity_communication_ok = True
    window.system_identity_matched = True
    window.system_identity_saturated = False
    window.custom_capture_generation = 1
    window.selected_lock_point = confirmed_selection()
    window.pending_lock_point = None
    window.applied_kp = 0
    window.custom_kp.setCurrentText("0")
    return app, window


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.6738, "673.8 mV"),
        (1.023, "1.023 V"),
        (None, "--"),
        (float("nan"), "Invalid"),
        (float("inf"), "Invalid"),
        (float("-inf"), "Invalid"),
    ],
)
def test_operator_absolute_voltage_format(value, expected) -> None:
    assert format_operator_voltage(value) == expected


def test_operator_delta_voltage_format_has_explicit_sign() -> None:
    assert format_operator_delta_voltage(0.0023) == "+2.3 mV"
    assert format_operator_delta_voltage(-0.00018) == "-0.18 mV"
    assert format_operator_delta_voltage(None) == "--"


def test_ch4_absolute_and_delta_use_distinct_calibration_paths() -> None:
    raw_count = 1024
    raw_before = raw_count

    assert format_out2_command_counts(raw_count) == format_operator_voltage(
        out2_counts_to_voltage(raw_count)
    )
    assert format_out2_delta_counts(raw_count) == format_operator_delta_voltage(
        out2_delta_counts_to_voltage(raw_count)
    )
    assert out2_counts_to_voltage(raw_count) != out2_delta_counts_to_voltage(raw_count)
    assert raw_count == raw_before


def test_error_equivalent_uses_ideal_count_conversion_only(monkeypatch) -> None:
    import redpitaya_lock_host.main_window as main_window

    monkeypatch.setattr(
        main_window,
        "out2_counts_to_voltage",
        lambda _counts: (_ for _ in ()).throw(AssertionError("OUT2 calibration called")),
    )

    assert format_error_equivalent_voltage(COUNTS_PER_VOLT / 2.0) == "500 mV"
    assert format_error_equivalent_voltage(-COUNTS_PER_VOLT / 1000.0, signed=True) == "-1 mV"


def test_lock_transition_diagnostics_calculates_selected_captured_deltas() -> None:
    selected = confirmed_selection()
    selected_counts = selected["target_out2_counts"]
    payload = identity_payload(
        mode=3,
        captured_lock_bias_counts=selected_counts + 16,
        captured_error_setpoint_counts=14,
        target_wait_matched=True,
        current_kp=0,
    )

    diagnostics = build_lock_transition_diagnostics(selected, payload)

    assert diagnostics["delta_bias_counts"] == 16
    assert diagnostics["delta_bias_voltage_estimate"] == out2_delta_counts_to_voltage(16)
    assert diagnostics["delta_error_setpoint_counts"] == 4
    assert diagnostics["delta_error_setpoint_ideal_voltage"] == 4 / COUNTS_PER_VOLT
    assert diagnostics["target_wait_matched"] is True
    assert diagnostics["mode"] == "P_LOCK"


def test_lock_transition_missing_capture_is_unavailable_not_selected_or_zero() -> None:
    selected = confirmed_selection()

    diagnostics = build_lock_transition_diagnostics(selected, {})

    assert diagnostics["captured_lock_bias_counts"] is None
    assert diagnostics["captured_error_setpoint_counts"] is None
    assert diagnostics["delta_bias_counts"] is None
    assert diagnostics["delta_error_setpoint_counts"] is None
    assert diagnostics["validity"] == "unavailable"
    assert diagnostics["true_scan_to_lock_jump"] == TRANSITION_JUMP_UNAVAILABLE


def test_hold_diagnostics_uses_selected_lock_bias_and_raw_readback() -> None:
    selected = confirmed_selection()
    selected_counts = selected["lock_bias_counts"]
    diagnostics = build_hold_selected_diagnostics(
        selected,
        identity_payload(out2_counts=selected_counts + 1),
    )

    assert diagnostics["hold_selected_counts"] == selected_counts
    assert diagnostics["hold_readback_counts"] == selected_counts + 1
    assert diagnostics["hold_delta_counts"] == 1
    assert diagnostics["hold_delta_voltage_estimate"] == out2_delta_counts_to_voltage(1)


def test_backend_exact_hold_config_preserves_raw_count_without_voltage_round_trip(monkeypatch) -> None:
    import redpitaya_lock_host.custom_fpga_backend as backend

    selected_counts = out2_voltage_to_counts(0.77) + 3
    monkeypatch.setattr(
        backend,
        "volts_to_counts",
        lambda _volts: (_ for _ in ()).throw(AssertionError("voltage round trip used")),
    )

    config = build_hold_config_from_counts(hold_counts=selected_counts)

    assert config.hold_counts == selected_counts
    with pytest.raises(CustomFpgaBackendError):
        build_hold_config_from_counts(hold_counts=8192)


def test_cli_exact_hold_uses_existing_hold_counts_remote_path() -> None:
    from test_custom_fpga_backend import load_scan_control_module

    module = load_scan_control_module()
    args = module.parse_args(["--host", "rp.local", "hold", "--hold-counts", "6123"])
    config = module.build_hold_config(args)
    command = module.remote_command(args, "hold", config)

    assert config.hold_counts == 6123
    assert "--hold-counts" in command[-1]
    assert "6123" in command[-1]


def test_worker_has_dedicated_hold_selected_count_operation() -> None:
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "redpitaya_lock_host" / "connection_workers.py").read_text(
        encoding="utf-8"
    )

    assert 'elif self.operation == "hold-selected-count":' in source
    assert "backend.set_mode_hold_counts" in source


def test_exact_hold_remote_branch_does_not_capture_or_write_feedback_parameters() -> None:
    from test_custom_fpga_backend import load_scan_control_module

    helper = load_scan_control_module().REMOTE_HELPER
    hold_start = helper.index('elif args.op == "hold":')
    hold_end = helper.index('elif args.op == "p-lock":', hold_start)
    hold_body = helper[hold_start:hold_end]

    assert 'regs.write(REGISTERS["HOLD_VALUE"], args.hold_counts)' in hold_body
    assert 'regs.write(REGISTERS["MODE"], 2)' in hold_body
    for forbidden in ("CAPTURE_LOCK_POINT", 'REGISTERS["KP"]', 'REGISTERS["KI"]', 'REGISTERS["POLARITY"]'):
        assert forbidden not in hold_body


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda window: setattr(window, "selected_lock_point", None), "confirmed lock point"),
        (
            lambda window: (
                setattr(window, "selected_lock_point", None),
                setattr(window, "pending_lock_point", confirmed_selection()),
            ),
            "requires Confirm",
        ),
        (lambda window: window.custom_kp.setCurrentText("4"), "requires Kp=0"),
        (lambda window: setattr(window, "capture_in_flight", True), "capture is in flight"),
        (lambda window: setattr(window, "current_custom_operation", "status"), "another FPGA operation"),
        (
            lambda window: window.selected_lock_point.update(lock_bias_counts=-8191),
            "outside the PZT safe range",
        ),
        (lambda window: setattr(window, "system_identity_saturated", True), "saturation"),
        (
            lambda window: window.selected_lock_point.update(capture_generation=0),
            "selected target is stale",
        ),
    ],
)
def test_hold_selected_count_guards_block_without_operation(mutate, message) -> None:
    app, window = make_window()
    operations = []
    try:
        mutate(window)
        window._start_custom_fpga_operation = lambda operation, preserve_basic=False: operations.append(operation)

        window._hold_selected_count()

        assert operations == []
        assert message in window.operator_alert_label.text()
    finally:
        window.worker = None
        window.close()
        app.processEvents()


def test_hold_selected_count_busy_worker_guard() -> None:
    app, window = make_window()
    operations = []
    try:
        window.worker = SimpleNamespace(isRunning=lambda: True)
        window._start_custom_fpga_operation = lambda operation, preserve_basic=False: operations.append(operation)

        window._hold_selected_count()

        assert operations == []
        assert "worker is busy" in window.operator_alert_label.text()
    finally:
        window.worker = None
        window.close()
        app.processEvents()


def test_hold_selected_count_cancel_sends_no_operation() -> None:
    app, window = make_window()
    operations = []
    try:
        window._start_custom_fpga_operation = lambda operation, preserve_basic=False: operations.append(operation)
        with patch("redpitaya_lock_host.main_window.QMessageBox.question", return_value=0):
            window._hold_selected_count()

        assert operations == []
    finally:
        window.close()
        app.processEvents()


def test_hold_selected_count_confirmation_uses_only_dedicated_hold_operation() -> None:
    from PySide6.QtWidgets import QMessageBox

    app, window = make_window()
    operations = []
    selected_before = dict(window.selected_lock_point)
    try:
        window._start_custom_fpga_operation = lambda operation, preserve_basic=False: operations.append(operation)
        with patch(
            "redpitaya_lock_host.main_window.QMessageBox.question",
            return_value=QMessageBox.Yes,
        ):
            window._hold_selected_count()

        assert operations == ["hold-selected-count"]
        assert window.selected_lock_point == selected_before
    finally:
        window.close()
        app.processEvents()


def test_hold_selected_success_state_is_not_locked_and_shows_readback() -> None:
    app, window = make_window()
    selected_counts = window.selected_lock_point["lock_bias_counts"]
    try:
        window.current_custom_operation = "hold-selected-count"
        window._on_custom_fpga_finished(
            {
                "operation": "hold-selected-count",
                "payload": identity_payload(out2_counts=selected_counts),
                "stderr": "",
            }
        )

        assert window.operator_state_label.text() == "HOLD DIAGNOSTIC / Kp=0 / NOT LOCKED"
        assert window.operator_lock_diagnostic_state_label.text() == "HOLD DIAGNOSTIC / Kp=0 / NOT LOCKED"
        assert window.last_hold_selected_diagnostics["hold_selected_counts"] == selected_counts
        assert window.last_hold_selected_diagnostics["hold_readback_counts"] == selected_counts
        assert not window.p_lock_ready
    finally:
        window.close()
        app.processEvents()


def test_lock_here_result_uses_fpga_captured_values_and_warns_on_error_delta() -> None:
    app, window = make_window()
    selected_counts = window.selected_lock_point["target_out2_counts"]
    try:
        window.current_custom_operation = "lock"
        window._on_custom_fpga_finished(
            {
                "operation": "lock",
                "payload": identity_payload(
                    mode=3,
                    current_kp=0,
                    captured_lock_bias_counts=selected_counts + 2,
                    captured_error_setpoint_counts=20,
                    target_wait_matched=True,
                ),
                "stderr": "",
            }
        )

        diagnostics = window.last_lock_transition_diagnostics
        assert diagnostics["captured_lock_bias_counts"] == selected_counts + 2
        assert diagnostics["captured_error_setpoint_counts"] == 20
        assert diagnostics["delta_error_setpoint_counts"] == 10
        assert "differ" in window.operator_alert_label.text()
        assert window.applied_kp == 0
    finally:
        window.close()
        app.processEvents()


def test_lock_here_missing_captured_values_remains_unavailable_and_not_ready() -> None:
    app, window = make_window()
    try:
        window.current_custom_operation = "lock"
        window._on_custom_fpga_finished(
            {
                "operation": "lock",
                "payload": identity_payload(mode=3, current_kp=0, target_wait_matched=True),
                "stderr": "",
            }
        )

        diagnostics = window.last_lock_transition_diagnostics
        assert diagnostics["captured_lock_bias_counts"] is None
        assert diagnostics["captured_error_setpoint_counts"] is None
        assert window.operator_lock_diagnostic_labels["captured_bias"].text() == "--"
        assert not window.p_lock_ready
    finally:
        window.close()
        app.processEvents()


@pytest.mark.parametrize(
    "payload",
    [
        identity_payload(mode=1),
        identity_payload(saturated=True, status_raw="0x00000003"),
    ],
)
def test_hold_selected_bad_readback_requests_safe(payload) -> None:
    app, window = make_window()
    operations = []
    try:
        window.current_custom_operation = "hold-selected-count"
        window._start_custom_fpga_operation = lambda operation, preserve_basic=False: operations.append(operation)
        with patch("redpitaya_lock_host.main_window.QTimer.singleShot", side_effect=lambda _delay, callback: callback()):
            window._on_custom_fpga_finished(
                {"operation": "hold-selected-count", "payload": payload, "stderr": ""}
            )

        assert operations == ["safe"]
        assert "FAILED" in window.operator_state_label.text()
        assert not window.p_lock_ready
    finally:
        window.close()
        app.processEvents()


def test_operator_view_hides_counts_and_engineer_details_retains_them() -> None:
    app, window = make_window()
    selected = window.selected_lock_point
    selected_counts = selected["target_out2_counts"]
    payload = identity_payload(
        mode=3,
        current_kp=0,
        captured_lock_bias_counts=selected_counts,
        captured_error_setpoint_counts=10,
        target_wait_matched=True,
    )
    try:
        diagnostics = build_lock_transition_diagnostics(selected, payload)
        window.last_lock_transition_diagnostics = diagnostics
        window._refresh_operator_lock_diagnostics()

        for label in window.operator_lock_diagnostic_labels.values():
            assert "counts" not in label.text().lower()
        assert not window.raw_lock_transition_details.isVisible()
        assert "selected_target_counts" in window.raw_lock_transition_details.toPlainText()
        assert str(selected_counts) in window.raw_lock_transition_details.toPlainText()
        visible_text = " ".join(
            label.text()
            for label in window.operator_lock_diagnostics_group.findChildren(type(window.operator_calibration_warning))
        )
        assert "calibrated estimate" in visible_text.lower()
        assert "ideal equivalent" in visible_text.lower()
        assert "not been independently calibrated" in window.operator_calibration_warning.text()
        assert "PZT actual voltage" not in visible_text
    finally:
        window.close()
        app.processEvents()


def test_safe_keeps_last_diagnostic_not_live_and_disconnect_marks_stale() -> None:
    app, window = make_window()
    selected = window.selected_lock_point
    selected_counts = selected["target_out2_counts"]
    diagnostics = build_lock_transition_diagnostics(
        selected,
        identity_payload(
            mode=3,
            current_kp=0,
            captured_lock_bias_counts=selected_counts,
            captured_error_setpoint_counts=10,
            target_wait_matched=True,
        ),
    )
    try:
        window.last_lock_transition_diagnostics = diagnostics
        window._mark_diagnostics_not_live(stale=False, reason="SAFE requested")
        assert window.last_lock_transition_diagnostics["live"] is False
        assert window.last_lock_transition_diagnostics["stale"] is False
        assert window.operator_lock_diagnostic_state_label.text() == "Last transition / not live"

        window._clear_system_identity("Disconnected")
        assert window.last_lock_transition_diagnostics["stale"] is True
        assert window.operator_lock_diagnostic_state_label.text() == "Last transition / stale"
    finally:
        window.close()
        app.processEvents()


def test_new_capture_clears_old_captured_binding() -> None:
    from test_custom_fpga_backend import make_capture_payload

    app, window = make_window()
    try:
        window.last_lock_transition_diagnostics = build_lock_transition_diagnostics(
            window.selected_lock_point,
            identity_payload(
                mode=3,
                current_kp=0,
                captured_lock_bias_counts=window.selected_lock_point["target_out2_counts"],
                captured_error_setpoint_counts=10,
                target_wait_matched=True,
            ),
        )

        window._render_custom_capture_payload(make_capture_payload())

        assert window.last_lock_transition_diagnostics is None
        assert window.last_hold_selected_diagnostics is None
        assert window.selected_lock_point is None
    finally:
        window.close()
        app.processEvents()


def test_operator_event_log_preserves_raw_counts_and_unavailable_values() -> None:
    app, window = make_window()
    try:
        window._record_operator_diagnostic_event(
            "select-lock-point",
            selected=window.selected_lock_point,
            payload={},
        )

        event = window.operator_diagnostic_events[-1]
        assert event["selected_target_counts"] == window.selected_lock_point["target_out2_counts"]
        assert event["captured_lock_bias_counts"] is None
        assert event["true_scan_to_lock_jump"] == TRANSITION_JUMP_UNAVAILABLE
        assert event["calibration_verified_for_loaded_pzt"] is False
    finally:
        window.close()
        app.processEvents()
