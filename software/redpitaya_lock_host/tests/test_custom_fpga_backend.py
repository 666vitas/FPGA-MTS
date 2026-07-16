import importlib.util
import os
import sys
from pathlib import Path

import numpy as np

from redpitaya_lock_host.custom_fpga_backend import (
    EXPECTED_MAGIC,
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
from redpitaya_lock_host.main_window import (
    LockPointSelectionError,
    classify_identity_error,
    choose_scope_volts_per_div,
    format_fpga_version,
    format_scope_voltage,
    identity_payload_matches,
    resolve_direct_error_zero_crossing,
    resolve_lock_point_selection,
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


def make_identity_payload(**overrides) -> dict:
    payload = {
        "magic": f"0x{EXPECTED_MAGIC:08X}",
        "version": f"0x{EXPECTED_VERSION:08X}",
        "mode": 0,
        "enable": 0,
        "status_raw": "0x00000000",
        "saturated": False,
        "out2_counts": 0,
    }
    payload.update(overrides)
    return payload


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


def test_system_identity_formats_version_and_requires_magic_and_version() -> None:
    assert format_fpga_version("0x00030001") == "v3.0.1"
    assert format_fpga_version("--") == "--"
    assert identity_payload_matches(make_identity_payload())
    assert not identity_payload_matches(make_identity_payload(magic="0x00000000"))
    assert not identity_payload_matches(make_identity_payload(version="0x00030000"))


def test_system_identity_error_classification_is_specific() -> None:
    assert classify_identity_error("No authentication methods available") == "Authentication failed"
    assert classify_identity_error("No route to host") == "Host unreachable"
    assert classify_identity_error("VERSION mismatch") == "FPGA identity mismatch"
    assert classify_identity_error("/dev/mem register read failed") == "Register read failed"
    assert classify_identity_error("SSH connection closed") == "Communication lost"


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


# ── resolve_lock_point_selection unit tests ──────────────────────────


def test_resolve_lock_point_from_ch1_peak_to_ch3_zero_crossing() -> None:
    """Click near a CH1 peak: resolver finds CH1 peak, nearby CH3 ZC, and CH4 ramp."""
    count = 512
    x = np.linspace(-1.0, 1.0, count)
    # CH1: single absorption dip near index 250
    ch1 = 80.0 * np.exp(-((x - 0.0) * 6.0) ** 2)
    # CH3: dispersion-shaped error with zero crossing near index 255
    error = 260.0 * x * np.exp(-(x * 3.5) ** 2)
    # CH4: monotonically increasing ramp
    out2 = np.linspace(6500, 7300, count)
    result = resolve_lock_point_selection(
        ch1_counts=ch1,
        error_counts=error,
        out2_counts=out2,
        clicked_index=252,
        error_setpoint_counts=0.0,
        safe_min_counts=6400,
        safe_max_counts=7400,
    )
    assert result["selected_peak_index"] == 256  # CH1 peak at center
    assert abs(result["zero_crossing_index"] - 255) < 5
    assert result["ramp_direction"] == "rising"
    assert abs(result["slope"]) > 0.0
    assert 6500 <= result["target_out2_counts"] <= 7300


def test_resolve_lock_point_prefers_max_slope_zero_crossing() -> None:
    """When multiple ZCs exist in the window, pick the one with largest |dError/dOut2|."""
    count = 512
    ch1 = np.ones(count, dtype=float) * 10.0
    ch1[240:260] = 80.0  # simple peak around index 250
    out2 = np.linspace(6500, 7300, count)
    # Two zero crossings: one at index 200 (gentle slope), one at 250 (steep slope)
    error = np.zeros(count, dtype=float)
    error[195:205] = np.linspace(-5.0, 5.0, 10)   # gentle crossing at ~200
    error[245:255] = np.linspace(-20.0, 20.0, 10)  # steep crossing at ~250
    result = resolve_lock_point_selection(
        ch1_counts=ch1,
        error_counts=error,
        out2_counts=out2,
        clicked_index=250,
        safe_min_counts=6400,
        safe_max_counts=7400,
    )
    # Steeper ZC near 250 should be preferred over gentle one near 200
    assert abs(result["zero_crossing_index"] - 249) < 6


def test_resolve_lock_point_prefers_closer_when_slopes_similar() -> None:
    """When two ZCs have similar |dError/dOut2|, prefer the one closer to CH1 peak."""
    count = 512
    ch1 = np.ones(count, dtype=float) * 10.0
    ch1[248:260] = 80.0  # peak near 254
    out2 = np.linspace(6500, 7300, count)
    error = np.zeros(count, dtype=float)
    # Two similar-slope ZCs: one far (220), one near (250)
    error[215:225] = np.linspace(-10.0, 10.0, 10)   # far from peak
    error[245:255] = np.linspace(-10.0, 10.0, 10)   # near peak
    result = resolve_lock_point_selection(
        ch1_counts=ch1,
        error_counts=error,
        out2_counts=out2,
        clicked_index=254,
        safe_min_counts=6400,
        safe_max_counts=7400,
    )
    # Closer ZC near 249 should be preferred
    assert abs(result["zero_crossing_index"] - 249) <= 5


def test_resolve_lock_point_detects_ramp_rising() -> None:
    """Monotonically increasing CH4/OUT2 -> ramp_direction='rising'."""
    count = 256
    ch1 = np.ones(count, dtype=float) * 40.0
    ch1[120:140] = 90.0
    error = np.zeros(count, dtype=float)
    error[125:135] = np.linspace(-15.0, 15.0, 10)
    out2 = np.linspace(6000, 8000, count)
    result = resolve_lock_point_selection(
        ch1_counts=ch1,
        error_counts=error,
        out2_counts=out2,
        clicked_index=130,
        safe_min_counts=5000,
        safe_max_counts=8191,
    )
    assert result["ramp_direction"] == "rising"


def test_resolve_lock_point_detects_ramp_falling() -> None:
    """Monotonically decreasing CH4/OUT2 -> ramp_direction='falling'."""
    count = 256
    ch1 = np.ones(count, dtype=float) * 40.0
    ch1[120:140] = 90.0
    error = np.zeros(count, dtype=float)
    error[125:135] = np.linspace(15.0, -15.0, 10)
    out2 = np.linspace(8000, 6000, count)
    result = resolve_lock_point_selection(
        ch1_counts=ch1,
        error_counts=error,
        out2_counts=out2,
        clicked_index=130,
        safe_min_counts=5000,
        safe_max_counts=8191,
    )
    assert result["ramp_direction"] == "falling"


def test_resolve_lock_point_rejects_when_ramp_direction_unavailable() -> None:
    """Flat CH4/OUT2 with no clear direction -> LockPointSelectionError."""
    count = 256
    ch1 = np.ones(count, dtype=float) * 40.0
    ch1[120:140] = 90.0
    error = np.zeros(count, dtype=float)
    error[125:135] = np.linspace(-15.0, 15.0, 10)
    out2 = np.ones(count, dtype=float) * 6000.0  # flat
    with np.testing.assert_raises(LockPointSelectionError):
        resolve_lock_point_selection(
            ch1_counts=ch1,
            error_counts=error,
            out2_counts=out2,
            clicked_index=130,
            safe_min_counts=5000,
            safe_max_counts=8191,
        )


def test_resolve_lock_point_rejects_no_zero_crossing() -> None:
    """No CH3 sign change in window -> LockPointSelectionError."""
    count = 256
    ch1 = np.ones(count, dtype=float) * 40.0
    ch1[120:140] = 90.0
    error = np.ones(count, dtype=float) * 42.0  # no ZC
    out2 = np.linspace(6500, 7300, count)
    with np.testing.assert_raises(LockPointSelectionError):
        resolve_lock_point_selection(
            ch1_counts=ch1,
            error_counts=error,
            out2_counts=out2,
            clicked_index=130,
            safe_min_counts=6400,
            safe_max_counts=7400,
        )


def test_resolve_lock_point_rejects_outside_pzt_safe_range() -> None:
    """Zero crossing OUT2 value outside safe range -> LockPointSelectionError."""
    count = 256
    ch1 = np.ones(count, dtype=float) * 40.0
    ch1[120:140] = 90.0
    error = np.zeros(count, dtype=float)
    error[125:135] = np.linspace(-15.0, 15.0, 10)
    out2 = np.linspace(8000, 9000, count)  # outside safe 6400-7400
    with np.testing.assert_raises(LockPointSelectionError):
        resolve_lock_point_selection(
            ch1_counts=ch1,
            error_counts=error,
            out2_counts=out2,
            clicked_index=130,
            safe_min_counts=6400,
            safe_max_counts=7400,
        )


def test_resolve_lock_point_rejects_click_near_edge() -> None:
    """Clicked index near capture edge -> LockPointSelectionError."""
    count = 512
    ch1 = np.ones(count, dtype=float) * 40.0
    ch1[5:15] = 90.0
    error = np.zeros(count, dtype=float)
    error[8:18] = np.linspace(-15.0, 15.0, 10)
    out2 = np.linspace(6500, 7300, count)
    with np.testing.assert_raises(LockPointSelectionError):
        resolve_lock_point_selection(
            ch1_counts=ch1,
            error_counts=error,
            out2_counts=out2,
            clicked_index=10,
            safe_min_counts=6400,
            safe_max_counts=7400,
        )


def test_resolve_lock_point_rejects_on_saturated_flag() -> None:
    """saturated=True -> LockPointSelectionError immediately."""
    count = 256
    ch1 = np.ones(count, dtype=float) * 40.0
    error = np.zeros(count, dtype=float)
    error[125:135] = np.linspace(-15.0, 15.0, 10)
    out2 = np.linspace(6500, 7300, count)
    with np.testing.assert_raises(LockPointSelectionError):
        resolve_lock_point_selection(
            ch1_counts=ch1,
            error_counts=error,
            out2_counts=out2,
            clicked_index=130,
            safe_min_counts=6400,
            safe_max_counts=7400,
            saturated=True,
        )


def test_resolve_lock_point_result_contains_all_required_fields() -> None:
    """Confirm Lock Point result has all fields needed for LOCK HERE."""
    count = 512
    ch1 = np.ones(count, dtype=float) * 40.0
    ch1[120:140] = 90.0
    error = np.zeros(count, dtype=float)
    error[125:135] = np.linspace(-15.0, 15.0, 10)
    out2 = np.linspace(6500, 7300, count)
    result = resolve_lock_point_selection(
        ch1_counts=ch1,
        error_counts=error,
        out2_counts=out2,
        clicked_index=130,
        safe_min_counts=6400,
        safe_max_counts=7400,
    )
    assert isinstance(result["selected_peak_index"], int)
    assert isinstance(result["zero_crossing_index"], int)
    assert isinstance(result["target_out2_counts"], int)
    assert isinstance(result["target_out2_volts"], float)
    assert isinstance(result["error_setpoint_counts"], int)
    assert isinstance(result["slope"], float)
    assert result["ramp_direction"] in ("rising", "falling")
    assert isinstance(result["target_window_counts"], int)
    assert result["target_window_counts"] > 0


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
        assert window.custom_capture_once_button.text() == "SINGLE"
        assert window.custom_start_live_button.text() == "RUN"
        assert window.custom_stop_live_button.text() == "STOP"
        assert window.custom_live_interval_ms.currentText() == "1000"
        assert set(window.custom_scope_curves) == {"ch1", "ch2", "ch3", "ch4"}
    finally:
        window.close()
        app.processEvents()


def test_system_identity_defaults_are_unknown_and_build_date_is_unavailable() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        assert window.system_connection_value.text() == "Disconnected"
        assert window.system_identity_value.text() == "Unknown"
        assert window.system_fpga_version_value.text() == "--"
        assert window.system_mode_value.text() == "UNKNOWN"
        assert window.system_output_value.text() == "Unknown"
        assert window.system_last_probe_value.text() == "--"
        assert window.system_bitstream_value.text() == "Build date unavailable"
        assert window.system_bitstream_value.toolTip() == "Not encoded in the current FPGA register protocol."
        assert "does not identify the loaded bitstream" in window.system_host_code_value.toolTip()
        assert window.system_identity_refresh_button.text() == "REFRESH IDENTITY"
    finally:
        window.close()
        app.processEvents()


def test_system_identity_success_shows_readback_and_local_probe_time() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._update_system_identity_from_payload(
            make_identity_payload(mode=1, enable=1, status_raw="0x00000001"),
            record_probe=True,
        )

        assert window.system_connection_value.text() == "Connected"
        assert window.system_identity_value.text() == "Matched"
        assert window.system_fpga_version_value.text() == "v3.0.1"
        assert window.system_mode_value.text() == "SCAN"
        assert window.system_output_value.text() == "Enabled"
        assert window.last_identity_probe_time is not None
        assert window.system_last_probe_title.text() == "Last probe"
        assert window.system_last_probe_value.text() == window.last_identity_probe_time.strftime("%H:%M:%S")
        details = window.system_identity_group.toolTip()
        assert "MAGIC   0x4D545330" in details
        assert "VERSION 0x00030001" in details
        assert "MODE    1" in details
        assert "ENABLE  1" in details
    finally:
        window.close()
        app.processEvents()


def test_system_identity_magic_and_version_mismatch_disable_dangerous_actions() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.mock_check.setChecked(False)
        window._update_system_identity_from_payload(make_identity_payload(), record_probe=True)
        window._apply_button_state("DISCONNECTED")
        assert window.custom_scan_button.isEnabled()
        assert window.custom_start_live_button.isEnabled()
        assert window.custom_capture_once_button.isEnabled()
        assert window.custom_pick_lock_button.isEnabled()

        for payload in (
            make_identity_payload(magic="0x00000000"),
            make_identity_payload(version="0x00030000"),
        ):
            window._update_system_identity_from_payload(payload, record_probe=True)
            assert window.system_identity_value.text() == "Mismatch"
            assert not window.custom_scan_button.isEnabled()
            assert not window.custom_start_live_button.isEnabled()
            assert not window.custom_capture_once_button.isEnabled()
            assert not window.custom_pick_lock_button.isEnabled()
            assert not window.custom_confirm_lock_point_button.isEnabled()
            assert not window.custom_lock_button.isEnabled()
            assert not window.custom_apply_p_button.isEnabled()
            assert window.custom_safe_button.isEnabled()
            assert window.scan_stop_safe_button.isEnabled()
    finally:
        window.close()
        app.processEvents()


def test_system_identity_saturation_and_unknown_mode_are_explicit() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.mock_check.setChecked(False)
        for mode, expected in {
            0: "SAFE",
            1: "SCAN",
            2: "HOLD",
            3: "P_LOCK",
            4: "PI_LOCK",
        }.items():
            window._update_system_identity_from_payload(
                make_identity_payload(mode=mode),
                record_probe=False,
            )
            assert window.system_mode_value.text() == expected

        window._update_system_identity_from_payload(
            make_identity_payload(mode=99, enable=1, status_raw="0x00000003", saturated=True),
            record_probe=True,
        )
        assert window.system_mode_value.text() == "UNKNOWN"
        assert window.system_output_value.text() == "Saturated"
        assert not window.custom_scan_button.isEnabled()
        assert not window.custom_start_live_button.isEnabled()
        assert not window.custom_capture_once_button.isEnabled()
        assert window.custom_safe_button.isEnabled()
    finally:
        window.close()
        app.processEvents()


def test_incomplete_status_payload_clears_stale_identity_as_register_failure() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._update_system_identity_from_payload(make_identity_payload(), record_probe=True)
        window._on_custom_fpga_finished(
            {
                "operation": "status",
                "payload": {"magic": f"0x{EXPECTED_MAGIC:08X}"},
                "stderr": "",
            }
        )

        assert window.system_connection_value.text() == "Communication lost"
        assert window.system_identity_value.text() == "Unknown"
        assert window.system_fpga_version_value.text() == "--"
        assert window.system_mode_value.text() == "UNKNOWN"
        assert window.system_output_value.text() == "Unknown"
        assert window.system_identity_error_label.text() == "Register read failed"
        assert window.system_last_probe_title.text() == "Last successful probe"
    finally:
        window.close()
        app.processEvents()


def test_system_identity_failure_clears_stale_readback_and_classifies_authentication() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._update_system_identity_from_payload(make_identity_payload(mode=2, enable=1), record_probe=True)
        successful_time = window.last_identity_probe_time
        window.current_custom_operation = "status"

        window._on_custom_fpga_failed("SSH command failed: No authentication methods available")

        assert window.system_connection_value.text() == "Communication lost"
        assert window.system_identity_value.text() == "Unknown"
        assert window.system_fpga_version_value.text() == "--"
        assert window.system_mode_value.text() == "UNKNOWN"
        assert window.system_output_value.text() == "Unknown"
        assert window.system_identity_error_label.text() == "Authentication failed"
        assert "No authentication methods available" in window.system_identity_error_label.toolTip()
        assert window.last_identity_probe_time == successful_time
        assert window.system_last_probe_title.text() == "Last successful probe"
    finally:
        window.close()
        app.processEvents()


def test_refresh_identity_requests_only_read_only_status_operation() -> None:
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
        window._start_custom_fpga_operation = (
            lambda operation, preserve_basic=False: calls.append((operation, preserve_basic))
        )

        window._refresh_system_identity()

        assert calls == [("status", True)]
        worker_source = (ROOT / "redpitaya_lock_host" / "connection_workers.py").read_text(encoding="utf-8")
        backend_source = (ROOT / "redpitaya_lock_host" / "custom_fpga_backend.py").read_text(encoding="utf-8")
        assert 'elif self.operation == "status":\n                response = backend.read_status()' in worker_source
        assert 'def read_status(self) -> CustomFpgaResponse:\n        return self._run("status", None, allow_nonzero=False)' in backend_source
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


def test_single_stops_run_and_requests_exactly_one_capture() -> None:
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
        window._start_custom_fpga_operation = lambda operation, preserve_basic=False: calls.append(operation)

        window._capture_once()

        assert calls == ["capture"]
        assert not window.live_capture_active
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
        from PySide6.QtCore import QPointF
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    class ScopeClick:
        def __init__(self, scene_pos) -> None:
            self._scene_pos = scene_pos

        def scenePos(self):
            return self._scene_pos

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.show()
        window._render_custom_capture_payload(make_capture_payload())
        app.processEvents()

        # After rendering capture, no selection has been made yet
        assert window.pending_lock_point is None
        assert window.selected_lock_point is None

        # Click the ERROR trace near a valid transition to create only a pending point.
        clicked_index = len(window.custom_scope_data["ch3"]) // 2
        plot_item = window.custom_scope_plot.getPlotItem()
        time_target = window.custom_scope_data["time_s"][clicked_index] * 1000.0
        error_y = float(window.custom_scope_display_data["ch3"][clicked_index])
        scene_pos = plot_item.vb.mapViewToScene(QPointF(float(time_target), error_y))
        window.custom_select_target_check.setChecked(True)
        window._on_custom_scope_clicked(ScopeClick(scene_pos))

        # Now a pending lock point exists
        assert window.pending_lock_point is not None
        assert window.selected_lock_point is None

        # LOCK HERE should be blocked without confirmed lock point
        window._start_custom_fpga_operation("lock")

        assert "LOCK HERE requires" in window.custom_warning_text.toPlainText()
        assert window.current_custom_operation is None
    finally:
        window.close()
        app.processEvents()


def test_confirm_lock_point_promotes_pending_zero_crossing_only() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtCore import QPointF
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    class ScopeClick:
        def __init__(self, scene_pos) -> None:
            self._scene_pos = scene_pos

        def scenePos(self):
            return self._scene_pos

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.show()
        # Without any pending lock point, confirm should not set selected
        window._confirm_pending_lock_point()
        assert window.selected_lock_point is None

        # Render capture and simulate a click to create pending
        window._render_custom_capture_payload(make_capture_payload())
        app.processEvents()
        assert window.pending_lock_point is None  # No pending until click

        # Simulate user clicking directly on the ERROR trace.
        clicked_index = len(window.custom_scope_data["ch3"]) // 2
        plot_item = window.custom_scope_plot.getPlotItem()
        time_target = window.custom_scope_data["time_s"][clicked_index] * 1000.0
        error_y = float(window.custom_scope_display_data["ch3"][clicked_index])
        scene_pos = plot_item.vb.mapViewToScene(QPointF(float(time_target), error_y))
        window.custom_select_target_check.setChecked(True)
        window._on_custom_scope_clicked(ScopeClick(scene_pos))

        assert window.pending_lock_point is not None
        pending = dict(window.pending_lock_point)
        assert window.selected_lock_point is None

        window._confirm_pending_lock_point()

        assert window.selected_lock_point == pending
        assert "confirmed" in window.selected_lock_label.text()
        # Verify all required fields are present
        assert "selected_peak_index" in window.selected_lock_point
        assert "zero_crossing_index" in window.selected_lock_point
        assert "target_out2_counts" in window.selected_lock_point
        assert "target_out2_volts" in window.selected_lock_point
        assert "error_setpoint_counts" in window.selected_lock_point
        assert "ramp_direction" in window.selected_lock_point
        assert "slope" in window.selected_lock_point
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


def test_basic_lock_capture_after_new_semantics_stops_queue_without_auto_confirm() -> None:
    """After capture finds candidates, the state machine stops and waits for user click/Confirm."""
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
        window._render_custom_capture_payload(make_capture_payload())
        assert window.basic_lock_candidates
        assert window.pending_lock_point is None

        window.basic_lock_queue = ["capture"]
        window._continue_basic_lock_after_success("capture", {})

        assert not window.basic_lock_active
        assert window.basic_lock_queue == []
        assert window.pending_lock_point is None
        assert "CANDIDATE_FOUND" in window.basic_status_label.text()
        assert "click CH1 and Confirm Lock Point" in window.basic_status_label.text()
        assert "SAFE_FAIL" not in window.basic_status_label.text()
    finally:
        window.close()
        app.processEvents()


def test_pending_lock_point_cleared_on_new_capture() -> None:
    """A new capture resets pending_lock_point so stale selections aren't reused."""
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
        assert window.pending_lock_point is None  # cleared on new capture
        assert window.selected_lock_point is None
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
        # Y range follows layered display copies, not the raw OUT2 DC offset.
        y_range = window.custom_scope_plot.viewRange()[1]
        visible_curves = [curve for curve in window.custom_scope_curves.values() if curve.isVisible()]
        display_min = min(float(np.nanmin(curve.yData)) for curve in visible_curves)
        display_max = max(float(np.nanmax(curve.yData)) for curve in visible_curves)
        assert y_range[0] <= display_min
        assert y_range[1] >= display_max
        assert not np.array_equal(window.custom_scope_curves["ch4"].yData, ch4)
        # Normal capture does not run or display automatic candidate search.
        assert window.basic_lock_candidates == []
        assert window.custom_candidate_markers == []
        assert window.selected_lock_point is None
        assert window.pending_lock_point is None  # auto-detection no longer writes pending
        # Stats show non-zero Vpp
        stats = window.custom_scope_stats.text()
        assert "Vpp" in stats
    finally:
        window.close()
        app.processEvents()


def test_scope_display_transform_returns_a_scaled_offset_copy() -> None:
    from redpitaya_lock_host.main_window import scope_display_transform

    raw = np.asarray([4000.0, 4500.0, 5000.0])
    display = scope_display_transform(raw, center=4500.0, gain=0.01, vertical_offset=3.0)

    assert np.array_equal(raw, np.asarray([4000.0, 4500.0, 5000.0]))
    assert np.allclose(display, np.asarray([-2.0, 3.0, 8.0]))
    assert not np.shares_memory(raw, display)


def test_scope_default_layers_display_copies_but_keeps_raw_capture_stats() -> None:
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
        raw_ch4 = np.asarray([point["ch4_counts"] for point in payload["points"]], dtype=float)
        raw_ch1 = np.asarray([point["ch1_counts"] for point in payload["points"]], dtype=float)
        window._render_custom_capture_payload(payload)

        assert np.array_equal(window.custom_scope_data["ch4"], raw_ch4)
        assert np.array_equal(window.custom_scope_data["ch1"], raw_ch1)
        assert not np.array_equal(window.custom_scope_curves["ch4"].yData, raw_ch4)
        assert np.median(window.custom_scope_curves["ch4"].yData) > np.median(window.custom_scope_curves["ch3"].yData)
        assert np.median(window.custom_scope_curves["ch3"].yData) > np.median(window.custom_scope_curves["ch1"].yData)
        expected_ch1_span = np.ptp(raw_ch1) * window.custom_scope_scale_spins["ch1"].value()
        raw_ch3 = window.custom_scope_data["ch3"]
        expected_ch3_span = np.ptp(raw_ch3) * window.custom_scope_scale_spins["ch3"].value()
        assert np.isclose(np.ptp(window.custom_scope_curves["ch1"].yData), expected_ch1_span)
        assert np.isclose(np.ptp(window.custom_scope_curves["ch3"].yData), expected_ch3_span)
        assert f"mean {np.nanmean(raw_ch4):.1f}" in window.custom_scope_stats.toolTip()
    finally:
        window.close()
        app.processEvents()


def test_scope_default_restores_three_layer_visibility_and_positions() -> None:
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
        window.custom_scope_checks["ch2"].setChecked(True)
        window.custom_scope_vertical_spins["ch4"].setValue(-9.0)
        window.custom_scope_auto_scale_checks["ch1"].setChecked(False)

        window.custom_scope_default_button.click()

        assert window.custom_scope_checks["ch4"].isChecked()
        assert window.custom_scope_checks["ch3"].isChecked()
        assert window.custom_scope_checks["ch1"].isChecked()
        assert not window.custom_scope_checks["ch2"].isChecked()
        assert window.custom_scope_auto_scale_checks["ch1"].isChecked()
        assert window.custom_scope_vertical_spins["ch4"].value() == 3.0
        assert window.custom_scope_vertical_spins["ch3"].value() == 0.0
        assert window.custom_scope_vertical_spins["ch1"].value() == -3.0
    finally:
        window.close()
        app.processEvents()


def test_scope_manual_scale_and_vertical_position_only_change_display_copy() -> None:
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
        raw = window.custom_scope_data["ch4"].copy()
        center = window.custom_scope_display_state["ch4"]["center"]
        window.custom_scope_auto_scale_checks["ch4"].setChecked(False)
        window.custom_scope_scale_spins["ch4"].setValue(0.02)
        window.custom_scope_vertical_spins["ch4"].setValue(5.0)

        assert np.array_equal(window.custom_scope_data["ch4"], raw)
        assert np.allclose(window.custom_scope_curves["ch4"].yData, (raw - center) * 0.02 + 5.0)
    finally:
        window.close()
        app.processEvents()


def test_normal_capture_does_not_render_automatic_candidate_markers() -> None:
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

        assert window.basic_lock_candidates == []
        assert window.custom_candidate_markers == []
        assert window.custom_scope_valid_for_selection
    finally:
        window.close()
        app.processEvents()


def test_candidate_markers_remain_on_fixed_time_axis() -> None:
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
        window._render_custom_capture_payload(make_capture_payload())

        assert window.basic_lock_candidates
        window.custom_scope_x_axis_combo.setCurrentText("OUT2 counts")
        window._refresh_scope_display()

        assert window.custom_scope_x_axis_combo.currentText() == "time (ms)"
        for marker, candidate in zip(window.custom_candidate_markers, window.basic_lock_candidates):
            assert marker.value() == float(window.custom_scope_data["time_s"][candidate.index]) * 1000.0
    finally:
        window.close()
        app.processEvents()


def test_target_and_zero_markers_keep_raw_time_after_layered_display() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtCore import QPointF
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    class ScopeClick:
        def __init__(self, scene_pos) -> None:
            self._scene_pos = scene_pos

        def scenePos(self):
            return self._scene_pos

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.show()
        window._render_custom_capture_payload(make_capture_payload())
        app.processEvents()
        clicked_index = len(window.custom_scope_data["ch3"]) // 2
        plot_item = window.custom_scope_plot.getPlotItem()
        time_target = window.custom_scope_data["time_s"][clicked_index] * 1000.0
        scene_pos = plot_item.vb.mapViewToScene(QPointF(float(time_target), 0.0))
        window.custom_select_target_check.setChecked(True)

        window._on_custom_scope_clicked(ScopeClick(scene_pos))

        assert window.pending_lock_point is not None
        peak_index = int(window.pending_lock_point["selected_peak_index"])
        zero_index = int(window.pending_lock_point["zero_crossing_index"])
        assert window.custom_target_marker.value() == float(
            window.custom_scope_data["time_s"][peak_index]
        ) * 1000.0
        assert window.custom_zero_marker.value() == float(
            window.custom_scope_data["time_s"][zero_index]
        ) * 1000.0
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
        assert "CH1 Vpp" in stats
        assert "CH3 Vpp" in stats
        assert "CH4 Vpp" in stats
        assert "MODE" in stats
        detail = window.custom_scope_stats.toolTip()
        assert "IN1 / PD" in detail
        assert "IN2 / REF" in detail
        assert "OUT1 / laser_error" in detail
        assert "OUT2 / selected_out2" in detail
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


def test_lock_point_target_window_uses_current_x_axis_units() -> None:
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
        target_index = 128
        zero_index = 130
        window_counts = 64.0
        lock_point = {
            "selected_peak_index": target_index,
            "zero_crossing_index": zero_index,
            "target_window_counts": window_counts,
        }

        assert window.custom_scope_x_axis_combo.count() == 1
        assert window.custom_scope_x_axis_combo.currentText() == "time (ms)"
        window._update_lock_point_markers(lock_point)
        time_region = window.custom_target_window_region.getRegion()
        time_target = float(window.custom_scope_data["time_s"][target_index]) * 1000.0
        i0 = target_index - 1
        i1 = target_index + 1
        delta_counts = float(window.custom_scope_data["ch4"][i1] - window.custom_scope_data["ch4"][i0])
        delta_time_ms = float(window.custom_scope_data["time_s"][i1] - window.custom_scope_data["time_s"][i0]) * 1000.0
        expected_window_ms = abs(window_counts / (delta_counts / delta_time_ms))

        assert window.custom_target_window_region.isVisible()
        assert np.isclose(window.custom_target_marker.value(), time_target)
        assert np.isclose((time_region[0] + time_region[1]) / 2.0, time_target)
        assert np.isclose((time_region[1] - time_region[0]) / 2.0, expected_window_ms)
        assert (time_region[1] - time_region[0]) < 100.0
    finally:
        window.close()
        app.processEvents()


def test_scope_voltage_format_and_volts_per_div_steps() -> None:
    assert format_scope_voltage(0.1995) == "199.5 mV"
    assert format_scope_voltage(-0.0124, signed=True) == "-12.4 mV"
    assert format_scope_voltage(1.25) == "1.250 V"
    assert choose_scope_volts_per_div(0.1995) == 0.050
    assert choose_scope_volts_per_div(0.053) == 0.020


def test_project_scope_defaults_hide_counts_and_engineer_details() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication, QGroupBox, QLabel, QPushButton
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.show()
        window._render_custom_capture_payload(make_capture_payload())
        app.processEvents()

        assert window.custom_scope_x_axis_combo.currentText() == "time (ms)"
        assert window.custom_scope_x_axis_combo.count() == 1
        assert not window.hidden_engineering_controls.isVisible()
        assert not window.custom_scope_raw_controls.isVisible()
        assert not window.custom_scope_stats.isVisible()
        assert "counts" in window.custom_scope_stats.text()

        visible_groups = {
            group.title()
            for group in window.centralWidget().findChildren(QGroupBox)
            if group.isVisible()
        }
        assert visible_groups == {
            "Device Connection",
            "PZT Scan",
            "System Identity",
            "Three-Channel Waveform",
            "Manual Lock Point and P Lock",
        }

        for key in ("ch4", "ch3", "ch1"):
            text = window.channel_card_labels[key].text()
            assert "Vpp" in text
            assert "mV" in text or " V" in text
            assert "counts" not in text
        assert set(window.channel_card_labels) == {"ch4", "ch3", "ch1"}
        assert not window.custom_scope_curves["ch2"].isVisible()
        assert window.custom_scope_default_button.text() == "AUTO DISPLAY"

        main_text = " ".join(
            [label.text() for label in window.centralWidget().findChildren(QLabel) if label.isVisible()]
            + [button.text() for button in window.centralWidget().findChildren(QPushButton) if button.isVisible()]
        )
        assert "counts" not in main_text.lower()
        assert "Advanced / Engineer Details" not in main_text
        assert "BASIC LOCK" not in main_text
        assert "CH1 Peak Assisted" not in main_text
    finally:
        window.close()
        app.processEvents()


def test_scope_channel_cards_show_only_vpp_in_voltage() -> None:
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
        values = window.custom_scope_data["ch4"] / 8191.0
        text = window.channel_card_labels["ch4"].text()

        assert f"Vpp {format_scope_voltage(float(np.ptp(values)))}" in text
        assert text.startswith("CH4 SCAN | Vpp ")
        assert "Min" not in text
        assert "Max" not in text
        assert "Mean" not in text
        assert "counts" not in text
        assert "hardware calibration not yet verified" in window.channel_card_labels["ch4"].toolTip()
    finally:
        window.close()
        app.processEvents()


def test_each_channel_has_independent_volts_div_and_ground_position() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        ch3_before = window.custom_scope_volts_div_combos["ch3"].currentData()
        ch4_combo = window.custom_scope_volts_div_combos["ch4"]
        ch4_combo.setCurrentIndex(ch4_combo.findData(0.200))
        window.custom_scope_position_spins["ch4"].setValue(4.5)

        assert window.custom_scope_volts_div_combos["ch4"].currentData() == 0.200
        assert window.custom_scope_volts_div_combos["ch3"].currentData() == ch3_before
        assert np.isclose(window.custom_ground_markers["ch4"].value(), 4.5)
        assert np.isclose(window.custom_scope_vertical_spins["ch4"].value(), 4.5)
    finally:
        window.close()
        app.processEvents()


def test_auto_set_changes_display_only() -> None:
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
        raw_before = {
            key: values.copy() for key, values in window.custom_scope_data.items()
        }
        fpga_before = (
            window.custom_offset_v.value(),
            window.custom_amp_v.value(),
            window.custom_freq_hz.value(),
            window.custom_step_counts.value(),
            window.custom_zero_threshold_counts.value(),
        )
        window.custom_scope_position_spins["ch4"].setValue(-2.0)

        window.custom_scope_default_button.click()

        for key, values in raw_before.items():
            np.testing.assert_array_equal(window.custom_scope_data[key], values)
        assert fpga_before == (
            window.custom_offset_v.value(),
            window.custom_amp_v.value(),
            window.custom_freq_hz.value(),
            window.custom_step_counts.value(),
            window.custom_zero_threshold_counts.value(),
        )
        assert window.custom_scope_position_spins["ch4"].value() == 3.0
        assert window.custom_scope_checks["ch4"].isChecked()
        assert window.custom_scope_checks["ch3"].isChecked()
        assert window.custom_scope_checks["ch1"].isChecked()
        assert not window.custom_scope_checks["ch2"].isChecked()
    finally:
        window.close()
        app.processEvents()


def test_direct_error_zero_crossing_is_default_and_only_creates_pending() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtCore import QPointF
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    class ScopeClick:
        def __init__(self, scene_pos) -> None:
            self._scene_pos = scene_pos

        def scenePos(self):
            return self._scene_pos

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.mock_check.setChecked(False)
        window._update_system_identity_from_payload(make_identity_payload(), record_probe=True)
        window.show()
        window._render_custom_capture_payload(make_capture_payload())
        app.processEvents()
        candidate_index = len(window.custom_scope_data["ch3"]) // 2
        x_value = float(window.custom_scope_data["time_s"][candidate_index]) * 1000.0
        plot_item = window.custom_scope_plot.getPlotItem()
        scan_y = float(window.custom_scope_display_data["ch4"][candidate_index])
        error_y = float(window.custom_scope_display_data["ch3"][candidate_index])
        scan_scene_pos = plot_item.vb.mapViewToScene(QPointF(x_value, scan_y))
        error_scene_pos = plot_item.vb.mapViewToScene(QPointF(x_value, error_y))

        assert window.lock_point_selection_mode.currentText() == "Direct ERROR Zero Crossing"
        assert window.lock_point_selection_mode.count() == 1
        window.custom_pick_lock_button.setChecked(True)
        window._on_custom_scope_clicked(ScopeClick(scan_scene_pos))

        assert window.pending_lock_point is None
        assert "CH3 ERROR" in window.operator_alert_label.text()

        window._on_custom_scope_clicked(ScopeClick(error_scene_pos))

        assert window.pending_lock_point is not None
        assert window.selected_lock_point is None
        assert window.operator_state_label.text() == "WAITING FOR CONFIRMATION"
        assert "Status: Waiting for confirmation" in window.operator_candidate_label.text()
        assert "counts" not in window.operator_candidate_label.text()
        assert window.custom_confirm_lock_point_button.isEnabled()
        assert not window.custom_apply_p_button.isEnabled()

        pending = dict(window.pending_lock_point)
        window._confirm_pending_lock_point()
        assert window.selected_lock_point == pending
        assert window.operator_state_label.text() == "LOCK POINT CONFIRMED"
        assert "Status: Confirmed" in window.operator_candidate_label.text()
        assert window.custom_lock_button.isEnabled()
    finally:
        window.close()
        app.processEvents()


def test_direct_error_zero_crossing_resolver_uses_nearest_valid_crossing() -> None:
    count = 256
    out2 = np.linspace(6500.0, 7300.0, count)
    error = np.arange(count, dtype=float) - 130.0

    result = resolve_direct_error_zero_crossing(
        error_counts=error,
        out2_counts=out2,
        clicked_index=128,
        safe_min_counts=6400,
        safe_max_counts=7400,
    )

    assert result["zero_crossing_index"] == 130
    assert result["selected_peak_index"] == 130
    assert result["ramp_direction"] == "rising"
    assert abs(float(result["slope"])) > 0.0


def test_lock_here_requires_confirmed_point_and_kp_zero() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window.selected_lock_point = {"out2_counts": 7000}
        window.custom_kp.setCurrentText("4")

        window._start_custom_fpga_operation("lock")

        assert window.current_custom_operation is None
        assert "requires Kp=0" in window.custom_warning_text.toPlainText()
        assert not window.p_lock_ready
    finally:
        window.close()
        app.processEvents()


def test_apply_p_polarity_and_safe_button_guards() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        window._apply_button_state("CUSTOM_FPGA_BUSY")
        assert window.custom_safe_button.isEnabled()
        assert window.scan_stop_safe_button.isEnabled()

        window._apply_button_state("DISCONNECTED")
        window.custom_kp.setCurrentText("4")
        assert not window.custom_apply_p_button.isEnabled()
        window._start_custom_fpga_operation("update-p-lock")
        assert window.current_custom_operation is None
        assert "successful LOCK HERE at Kp=0" in window.operator_alert_label.text()

        window.custom_polarity.setCurrentIndex(0)
        window.applied_polarity_index = 0
        window.applied_kp = 4
        window.custom_polarity.setCurrentIndex(1)
        assert window.custom_polarity.currentIndex() == 0
        assert "Kp=0" in window.operator_alert_label.text()
    finally:
        window.close()
        app.processEvents()


def test_scan_range_is_blocked_outside_visible_pzt_safe_limits() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication
        from redpitaya_lock_host.main_window import MainWindow
    except ImportError:
        return

    app = QApplication.instance() or QApplication([])
    window = MainWindow({}, start_mock=True)
    try:
        assert np.isclose(window.custom_offset_v.value(), 0.85)
        assert np.isclose(window.custom_amp_v.value(), 0.05)
        window.custom_amp_v.setValue(0.10)

        window._start_custom_fpga_operation("scan")

        assert window.current_custom_operation is None
        assert window.operator_scan_state_label.text() == "SAFE"
        assert "outside PZT safe range" in window.operator_alert_label.text()
    finally:
        window.close()
        app.processEvents()
