from __future__ import annotations

import os

import numpy as np
import pytest

from redpitaya_lock_host.main_window import (
    LockPointSelectionError,
    estimate_local_ramp_direction,
    resolve_direct_error_zero_crossing,
)


def _quantized_ramp(
    *,
    count: int = 4096,
    center: int = 2048,
    rising: bool = True,
) -> np.ndarray:
    start, stop = (6100.0, 6592.0) if rising else (6592.0, 6100.0)
    return np.rint(np.linspace(start, stop, count))


def _persistent_error(
    *,
    count: int = 4096,
    crossing: float = 2048.25,
    slope: float = 0.8,
) -> np.ndarray:
    return np.rint((np.arange(count, dtype=float) - crossing) * slope)


def _resolve(
    error: np.ndarray,
    out2: np.ndarray,
    clicked_index: int = 2048,
    **kwargs: object,
) -> dict[str, object]:
    return resolve_direct_error_zero_crossing(
        error_counts=error,
        out2_counts=out2,
        time_s=np.arange(error.size, dtype=float) * 2.0e-6,
        clicked_index=clicked_index,
        safe_min_counts=6000,
        safe_max_counts=6700,
        **kwargs,
    )


def test_local_ramp_fit_recovers_quantized_low_amplitude_rising_direction() -> None:
    estimate = estimate_local_ramp_direction(_quantized_ramp(), 2048)

    assert estimate.valid
    assert estimate.direction == "rising"
    assert estimate.slope_counts_per_sample > 0.0
    assert estimate.predicted_delta_counts >= 3.0
    assert estimate.fit_window == (2032, 2064)


def test_local_ramp_fit_recovers_quantized_low_amplitude_falling_direction() -> None:
    estimate = estimate_local_ramp_direction(_quantized_ramp(rising=False), 2048)

    assert estimate.valid
    assert estimate.direction == "falling"
    assert estimate.slope_counts_per_sample < 0.0
    assert estimate.predicted_delta_counts >= 3.0


def test_local_ramp_fit_rejects_triangle_turnaround() -> None:
    out2 = np.rint(6446.0 - np.abs(np.arange(4096) - 2048) * 0.25)

    estimate = estimate_local_ramp_direction(out2, 2048)

    assert not estimate.valid
    assert estimate.rejection_reason == "RAMP_TURNAROUND_TOO_CLOSE"


def test_local_ramp_fit_rejects_turnaround_offset_from_crossing() -> None:
    out2 = np.rint(6446.0 - np.abs(np.arange(4096) - 2056) * 0.25)

    estimate = estimate_local_ramp_direction(out2, 2048)

    assert not estimate.valid
    assert estimate.rejection_reason == "RAMP_TURNAROUND_TOO_CLOSE"


def test_low_amplitude_60_mvpp_quantized_scan_resolves_crossing() -> None:
    result = _resolve(_persistent_error(), _quantized_ramp())

    assert abs(float(result["zero_crossing_index"]) - 2048.5) <= 1.0
    assert result["ramp_direction"] == "rising"
    assert float(result["ramp_predicted_delta_counts"]) >= 3.0
    assert int(result["candidate_count"]) >= 1


def test_low_amplitude_falling_scan_preserves_direction_and_error_direction() -> None:
    result = _resolve(_persistent_error(slope=-0.8), _quantized_ramp(rising=False))

    assert result["ramp_direction"] == "falling"
    assert result["error_crossing_direction"] == "pos_to_neg"
    assert float(result["slope"]) > 0.0


def test_exact_zero_sample_bracketed_by_stable_opposite_signs_is_accepted() -> None:
    error = _persistent_error(crossing=2048.0)
    error[2048] = 0.0

    result = _resolve(error, _quantized_ramp())

    assert float(result["zero_crossing_index"]) == 2048.0
    assert float(result["error_residual_counts"]) == 0.0


def test_zero_plateau_uses_plateau_center() -> None:
    error = np.full(4096, -20.0)
    error[2046:2051] = 0.0
    error[2051:] = 20.0

    result = _resolve(error, _quantized_ramp())

    assert float(result["zero_crossing_index"]) == 2048.0


def test_click_40_samples_away_still_finds_nearest_crossing() -> None:
    result = _resolve(_persistent_error(), _quantized_ramp(), clicked_index=2008)

    assert abs(float(result["zero_crossing_index"]) - 2048.5) <= 1.0
    assert int(result["search_left"]) <= 2048 <= int(result["search_right"])


def test_multiple_crossings_prioritize_nearest_click_not_steepest() -> None:
    error = np.full(4096, -30.0)
    error[1988:1998] = np.linspace(-30.0, 30.0, 10)
    error[1998:2068] = 30.0
    error[2068:2098] = np.linspace(30.0, -30.0, 30)
    error[2098:] = -30.0

    result = _resolve(error, _quantized_ramp(), clicked_index=2050)

    assert float(result["zero_crossing_index"]) > 2068.0
    assert int(result["candidate_count"]) == 2


def test_turnaround_rejection_exposes_specific_code() -> None:
    out2 = np.rint(6446.0 - np.abs(np.arange(4096) - 2048) * 0.25)

    with pytest.raises(LockPointSelectionError) as caught:
        _resolve(_persistent_error(), out2)

    assert caught.value.code == "RAMP_TURNAROUND_TOO_CLOSE"
    assert caught.value.diagnostics["rejection_counts_by_reason"]["RAMP_TURNAROUND_TOO_CLOSE"] >= 1


def test_noise_only_crossing_rejected_with_signal_quality_code() -> None:
    rng = np.random.default_rng(941)
    error = rng.integers(-1, 2, size=4096).astype(float)

    with pytest.raises(LockPointSelectionError) as caught:
        _resolve(error, _quantized_ramp())

    assert caught.value.code in {"ERROR_SNR_TOO_LOW", "ERROR_SLOPE_TOO_LOW", "MULTIPLE_AMBIGUOUS_CANDIDATES"}
    assert float(caught.value.diagnostics["local_error_vpp"]) <= 2.0


def test_outside_safe_range_rejection_has_specific_code_and_limits() -> None:
    with pytest.raises(LockPointSelectionError) as caught:
        resolve_direct_error_zero_crossing(
            error_counts=_persistent_error(),
            out2_counts=_quantized_ramp() + 1000.0,
            clicked_index=2048,
            safe_min_counts=6100,
            safe_max_counts=6550,
        )

    assert caught.value.code == "OUT2_OUTSIDE_SAFE_RANGE"
    assert caught.value.diagnostics["safe_min_counts"] == 6100
    assert caught.value.diagnostics["safe_max_counts"] == 6550


def test_saturation_rejection_is_immediate_and_specific() -> None:
    with pytest.raises(LockPointSelectionError) as caught:
        _resolve(_persistent_error(), _quantized_ramp(), saturated=True)

    assert caught.value.code == "SATURATION_ACTIVE"
    assert caught.value.diagnostics["candidate_count"] == 0


def test_no_sign_change_and_unbracketed_zero_have_distinct_codes() -> None:
    with pytest.raises(LockPointSelectionError) as no_change:
        _resolve(np.full(4096, 8.0), _quantized_ramp())
    assert no_change.value.code == "NO_SIGN_CHANGE"

    error = np.full(4096, 8.0)
    error[2048] = 0.0
    with pytest.raises(LockPointSelectionError) as unbracketed:
        _resolve(error, _quantized_ramp())
    assert unbracketed.value.code == "EXACT_ZERO_NOT_BRACKETED"


def test_large_amplitude_adjacent_sign_change_regression() -> None:
    count = 512
    out2 = np.linspace(5800.0, 6800.0, count)
    error = np.arange(count, dtype=float) - 250.25

    result = resolve_direct_error_zero_crossing(
        error_counts=error,
        out2_counts=out2,
        clicked_index=245,
        safe_min_counts=5700,
        safe_max_counts=6900,
    )

    assert float(result["zero_crossing_index"]) == 250.25
    assert result["ramp_direction"] == "rising"


def test_gui_selection_remains_pending_until_confirm_and_never_auto_arms() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        pytest.skip("PySide6 unavailable")

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        candidate = _resolve(_persistent_error(), _quantized_ramp())
        window.pending_lock_point = dict(candidate)
        window.custom_capture_generation = 1
        window.custom_acquisition_service.adopt_capture_id(1)
        window.pending_lock_point["capture_generation"] = 1
        window.pending_lock_point["out2_counts"] = int(candidate["target_out2_counts"])
        window.pending_lock_point["lock_bias_counts"] = int(candidate["target_out2_counts"])
        window.pending_lock_point["lock_bias_volts"] = float(candidate["target_out2_volts"])
        window.selected_lock_point = None
        window.current_custom_operation = None

        assert window.selected_lock_point is None
        assert window.current_custom_operation is None

        window._confirm_pending_lock_point()

        assert window.selected_lock_point is not None
        assert window.current_custom_operation is None
        assert window.last_arm_intent == "NONE"
    finally:
        window.close()
        app.processEvents()


@pytest.mark.parametrize("change", ["scan", "parameter", "disconnect"])
def test_gui_context_change_invalidates_confirmed_target(change: str) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from redpitaya_lock_host.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        candidate = _resolve(_persistent_error(), _quantized_ramp())
        window.custom_capture_generation = 1
        window.custom_acquisition_service.adopt_capture_id(1)
        window.pending_lock_point = dict(candidate)
        window.pending_lock_point.update(
            capture_generation=1,
            out2_counts=int(candidate["target_out2_counts"]),
            lock_bias_counts=int(candidate["target_out2_counts"]),
            lock_bias_volts=float(candidate["target_out2_volts"]),
        )
        window._confirm_pending_lock_point()
        assert window.selected_lock_point is not None
        old_epoch = window.custom_context_epoch
        if change == "scan":
            window._start_custom_fpga_operation("scan")
        elif change == "parameter":
            window.custom_freq_hz.setValue(window.custom_freq_hz.value() + 1.0)
        else:
            window._set_connection_state("DISCONNECTED")
        assert window.selected_lock_point is None
        assert window.pending_lock_point is None
        assert window.custom_acquisition_service.capture_id == 0
        assert not window.p_lock_ready
        window._deliver_custom_response(old_epoch, {"operation": "capture", "payload": {}})
        assert "STALE RESPONSE" in window.operator_state_label.text()
        assert window.custom_acquisition_service.capture_id == 0
    finally:
        window.close()
        app.processEvents()
