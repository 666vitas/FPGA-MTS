"""Custom FPGA register backend over SSH and /dev/mem."""

from __future__ import annotations

import base64
import importlib.util
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from .out2_calibration import (
    COUNTS_PER_VOLT,
    out2_amplitude_to_counts,
    out2_counts_to_voltage,
    out2_voltage_to_counts,
)
from .ssh_client import RedPitayaSshClient, SshCommandResult


EXPECTED_MAGIC = 0x4D545330
EXPECTED_VERSION = 0x00030001
DEFAULT_BASE_ADDR = 0x4060_0000
DEFAULT_CLK_HZ = 125_000_000.0
ALLOWED_UPDATE_KP = (0, 4, 8, 16, 32)
BASIC_LOCK_FREQ_HZ = 10.0
BASIC_LOCK_CAPTURE_LENGTH = 2048
BASIC_LOCK_STEP_COUNTS = 1


class CustomFpgaBackendError(RuntimeError):
    """Raised when the Custom FPGA register operation fails."""


@dataclass(frozen=True)
class ScanConfig:
    offset_counts: int
    amp_counts: int
    step_counts: int
    update_div: int
    limit_counts: int


@dataclass(frozen=True)
class HoldConfig:
    hold_counts: int


@dataclass(frozen=True)
class LockConfig:
    kp: int
    ki: int
    polarity: int
    lock_bias_counts: int
    lock_limit_counts: int
    correction_limit_counts: int


@dataclass(frozen=True)
class UpdatePLockConfig:
    kp: int
    polarity: int


@dataclass(frozen=True)
class CaptureConfig:
    capture_length: int
    capture_decimation: int


@dataclass(frozen=True)
class BasicLockConfig:
    safe_min_v: float
    safe_max_v: float
    offset_v: float
    amp_v: float
    freq_hz: float
    step_counts: int
    capture_length: int
    capture_decimation: int
    limit_counts: int
    safe_min_counts: int
    safe_max_counts: int


@dataclass(frozen=True)
class ZeroCrossingCandidate:
    index: float
    out2_counts: float
    error_counts: float
    error_residual_counts: float
    score: float
    slope: float
    local_vpp: float


@dataclass(frozen=True)
class ResolvedLockPoint:
    clicked_index: int
    index: float
    out2_counts: float
    error_counts: float
    error_residual_counts: float
    slope: float
    local_vpp: float
    valid: bool
    reason: str = ""


@dataclass(frozen=True)
class LockHereConfig:
    polarity: int
    lock_limit_counts: int
    correction_limit_counts: int
    settle_s: float
    target_out2_counts: int | None = None
    target_window_counts: int = 64
    target_timeout_s: float = 5.0
    target_poll_s: float = 0.005


@dataclass(frozen=True)
class CustomFpgaResponse:
    operation: str
    payload: dict[str, Any]
    stdout: str
    stderr: str
    exit_code: int
    remote_command: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "payload": self.payload,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "remote_command": self.remote_command,
        }


def volts_to_counts(volts: float) -> int:
    return out2_voltage_to_counts(volts)


def counts_to_volts(counts: int) -> float:
    return float(int(counts)) / COUNTS_PER_VOLT


def build_basic_lock_config(
    *,
    safe_min_v: float,
    safe_max_v: float,
    clk_hz: float = DEFAULT_CLK_HZ,
) -> BasicLockConfig:
    safe_min = float(safe_min_v)
    safe_max = float(safe_max_v)
    if safe_min >= safe_max:
        raise CustomFpgaBackendError("PZT safe min voltage must be lower than safe max voltage")
    if safe_min < -1.0 or safe_max > 1.0:
        raise CustomFpgaBackendError("PZT safe range must stay inside Red Pitaya DAC +/-1 V")

    offset_v = (safe_min + safe_max) / 2.0
    amp_v = abs(safe_max - safe_min) / 2.0
    if amp_v <= 0.0:
        raise CustomFpgaBackendError("PZT safe range must have nonzero width")
    capture_decimation = max(1, int(round(float(clk_hz) / (BASIC_LOCK_FREQ_HZ * BASIC_LOCK_CAPTURE_LENGTH))))
    return BasicLockConfig(
        safe_min_v=safe_min,
        safe_max_v=safe_max,
        offset_v=offset_v,
        amp_v=amp_v,
        freq_hz=BASIC_LOCK_FREQ_HZ,
        step_counts=BASIC_LOCK_STEP_COUNTS,
        capture_length=BASIC_LOCK_CAPTURE_LENGTH,
        capture_decimation=capture_decimation,
        limit_counts=max(abs(volts_to_counts(safe_min)), abs(volts_to_counts(safe_max))),
        safe_min_counts=volts_to_counts(safe_min),
        safe_max_counts=volts_to_counts(safe_max),
    )


def signal_vpp(values: np.ndarray | list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 0.0
    return float(np.nanmax(finite) - np.nanmin(finite))


def robust_noise_counts(values: np.ndarray | list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 0.0
    median = float(np.nanmedian(finite))
    mad = float(np.nanmedian(np.abs(finite - median)))
    return 1.4826 * mad


def interpolate_zero_crossing(
    *,
    error_counts: np.ndarray | list[float],
    out2_counts: np.ndarray | list[float],
    left_index: int,
    error_setpoint_counts: float = 0.0,
) -> ZeroCrossingCandidate:
    """Linearly interpolate one CH3 sign change and its matching CH4 value."""
    error = np.asarray(error_counts, dtype=float)
    out2 = np.asarray(out2_counts, dtype=float)
    count = min(error.size, out2.size)
    index = int(left_index)
    if index < 0 or index + 1 >= count:
        raise CustomFpgaBackendError("zero crossing pair is outside the capture")

    raw0 = float(error[index])
    raw1 = float(error[index + 1])
    pzt0 = float(out2[index])
    pzt1 = float(out2[index + 1])
    setpoint = float(error_setpoint_counts)
    e0 = raw0 - setpoint
    e1 = raw1 - setpoint
    if not all(np.isfinite(value) for value in (raw0, raw1, pzt0, pzt1, setpoint)):
        raise CustomFpgaBackendError("zero crossing pair contains non-finite data")
    if e0 * e1 >= 0.0:
        raise CustomFpgaBackendError("zero crossing pair does not strictly change sign")

    delta_error = raw1 - raw0
    delta_out2 = pzt1 - pzt0
    if abs(delta_error) < 1e-12:
        raise CustomFpgaBackendError("zero crossing pair has zero error slope")
    if abs(delta_out2) < 0.5:
        raise CustomFpgaBackendError("zero crossing pair has no usable PZT change")

    fraction = -e0 / (e1 - e0)
    if fraction < 0.0 or fraction > 1.0:
        raise CustomFpgaBackendError("interpolated zero crossing falls outside the sample pair")
    zero_error = raw0 + fraction * delta_error
    zero_out2 = pzt0 + fraction * delta_out2
    return ZeroCrossingCandidate(
        index=float(index) + float(fraction),
        out2_counts=float(zero_out2),
        error_counts=float(zero_error),
        error_residual_counts=float(zero_error - setpoint),
        score=0.0,
        slope=float(delta_error / delta_out2),
        local_vpp=0.0,
    )


def validate_basic_lock_capture(
    *,
    ch1_counts: np.ndarray | list[float],
    ch3_counts: np.ndarray | list[float],
    ch4_counts: np.ndarray | list[float],
    safe_min_counts: int,
    safe_max_counts: int,
    saturated: bool,
) -> None:
    if saturated:
        raise CustomFpgaBackendError("BASIC LOCK refused: FPGA status reports saturation")
    ch1 = np.asarray(ch1_counts, dtype=float)
    ch3 = np.asarray(ch3_counts, dtype=float)
    ch4 = np.asarray(ch4_counts, dtype=float)
    if min(ch1.size, ch3.size, ch4.size) == 0:
        raise CustomFpgaBackendError("BASIC LOCK refused: capture is empty")
    if signal_vpp(ch1) < 1.0:
        raise CustomFpgaBackendError("BASIC LOCK refused: CH1/PD capture is all zero or too small")
    if signal_vpp(ch3) < 1.0:
        raise CustomFpgaBackendError("BASIC LOCK refused: CH3/error capture is all zero or too small")
    if signal_vpp(ch4) < 1.0:
        raise CustomFpgaBackendError("BASIC LOCK refused: CH4/OUT2 capture is all zero or too small")
    if float(np.nanmin(ch4)) < int(safe_min_counts) or float(np.nanmax(ch4)) > int(safe_max_counts):
        raise CustomFpgaBackendError("BASIC LOCK refused: OUT2 capture exceeded the user PZT safe range")


def find_zero_crossing_candidates(
    *,
    error_counts: np.ndarray | list[float],
    out2_counts: np.ndarray | list[float],
    max_candidates: int = 3,
) -> list[ZeroCrossingCandidate]:
    error = np.asarray(error_counts, dtype=float)
    out2 = np.asarray(out2_counts, dtype=float)
    count = min(error.size, out2.size)
    if count < 16:
        return []
    error = error[:count]
    out2 = out2[:count]
    edge = max(4, int(round(count * 0.05)))
    if edge * 2 >= count:
        return []

    window = max(5, min(51, (count // 32) | 1))
    kernel = np.ones(window, dtype=float) / float(window)
    smooth = np.convolve(error, kernel, mode="same")
    noise = max(robust_noise_counts(np.diff(smooth[edge:-edge])) * 0.25, 1.0)
    min_local_vpp = max(noise * 6.0, 3.0)
    min_abs_slope = max(noise * 0.05, 0.05)

    candidates: list[ZeroCrossingCandidate] = []
    for idx in range(edge, count - edge - 1):
        y0 = float(error[idx])
        y1 = float(error[idx + 1])
        if y0 * y1 >= 0.0:
            continue
        try:
            crossing = interpolate_zero_crossing(
                error_counts=error,
                out2_counts=out2,
                left_index=idx,
            )
        except CustomFpgaBackendError:
            continue
        crossing_index = int(round(crossing.index))
        left = max(edge, crossing_index - window)
        right = min(count - edge, crossing_index + window + 1)
        local = error[left:right]
        if local.size < 5:
            continue
        before = error[max(edge, idx - 3):idx + 1]
        after = error[idx + 1:min(count - edge, idx + 5)]
        if before.size < 2 or after.size < 2:
            continue
        before_level = float(np.nanmedian(before))
        after_level = float(np.nanmedian(after))
        if before_level * after_level >= 0.0:
            continue
        if min(abs(before_level), abs(after_level)) < noise:
            continue
        local_vpp = signal_vpp(local)
        slope = float(crossing.slope)
        if local_vpp < min_local_vpp or abs(slope) < min_abs_slope:
            continue
        score = abs(slope) * local_vpp / max(noise, 1.0)
        candidates.append(
            ZeroCrossingCandidate(
                index=float(crossing.index),
                out2_counts=float(crossing.out2_counts),
                error_counts=float(crossing.error_counts),
                error_residual_counts=float(crossing.error_residual_counts),
                score=float(score),
                slope=float(slope),
                local_vpp=float(local_vpp),
            )
        )

    unique: dict[float, ZeroCrossingCandidate] = {}
    for item in sorted(
        candidates,
        key=lambda candidate: (
            abs(candidate.error_residual_counts),
            -abs(candidate.slope),
            -candidate.score,
        ),
    ):
        if all(abs(item.index - kept.index) > window for kept in unique.values()):
            unique[item.index] = item
        if len(unique) >= max_candidates:
            break
    return sorted(
        unique.values(),
        key=lambda candidate: (
            abs(candidate.error_residual_counts),
            -abs(candidate.slope),
            -candidate.score,
        ),
    )


def resolve_target_transition(
    *,
    error_counts: np.ndarray | list[float],
    out2_counts: np.ndarray | list[float],
    clicked_index: int,
    safe_min_counts: int,
    safe_max_counts: int,
    saturated: bool = False,
    search_radius: int = 128,
) -> ResolvedLockPoint:
    """Resolve a user PD-click to a nearby valid CH3/error zero crossing."""
    if saturated:
        raise CustomFpgaBackendError("target rejected: FPGA status reports saturation")
    error = np.asarray(error_counts, dtype=float)
    out2 = np.asarray(out2_counts, dtype=float)
    count = min(error.size, out2.size)
    if count < 16:
        raise CustomFpgaBackendError("target rejected: capture is too short")
    click = int(clicked_index)
    if click < 0 or click >= count:
        raise CustomFpgaBackendError("target rejected: clicked index is outside capture")
    edge = max(4, int(round(count * 0.03)))
    if click < edge or click >= count - edge:
        raise CustomFpgaBackendError("target rejected: clicked point is too close to capture edge")
    radius = max(4, int(search_radius))
    left = max(0, click - radius)
    right = min(count, click + radius + 1)
    if right - left < 8:
        raise CustomFpgaBackendError("target rejected: search window is too small")

    candidates = find_zero_crossing_candidates(
        error_counts=error[left:right],
        out2_counts=out2[left:right],
        max_candidates=8,
    )
    if not candidates:
        raise CustomFpgaBackendError("target rejected: no valid CH3/error zero crossing near clicked PD feature")

    adjusted: list[ZeroCrossingCandidate] = []
    for item in candidates:
        idx = float(left) + float(item.index)
        if idx < edge or idx >= count - edge:
            continue
        out2_value = float(item.out2_counts)
        if out2_value < int(safe_min_counts) or out2_value > int(safe_max_counts):
            continue
        adjusted.append(
            ZeroCrossingCandidate(
                index=idx,
                out2_counts=out2_value,
                error_counts=float(item.error_counts),
                error_residual_counts=float(item.error_residual_counts),
                score=float(item.score) / max(1.0, abs(idx - click)),
                slope=float(item.slope),
                local_vpp=float(item.local_vpp),
            )
        )
    if not adjusted:
        raise CustomFpgaBackendError("target rejected: zero crossing is outside the PZT safe range or capture edge")
    best = min(
        adjusted,
        key=lambda item: (
            abs(item.error_residual_counts),
            -abs(item.slope),
            abs(item.index - click),
        ),
    )
    return ResolvedLockPoint(
        clicked_index=click,
        index=float(best.index),
        out2_counts=float(best.out2_counts),
        error_counts=float(best.error_counts),
        error_residual_counts=float(best.error_residual_counts),
        slope=float(best.slope),
        local_vpp=float(best.local_vpp),
        valid=True,
    )


def build_scan_config(
    *,
    offset_v: float,
    amp_v: float,
    freq_hz: float,
    step_counts: int,
    limit_counts: int,
    clk_hz: float = DEFAULT_CLK_HZ,
) -> ScanConfig:
    amp_counts = out2_amplitude_to_counts(amp_v)
    if amp_counts < 1:
        raise CustomFpgaBackendError("scan amplitude must be at least one DAC count")
    if freq_hz <= 0:
        raise CustomFpgaBackendError("scan frequency must be positive")
    step = max(1, int(step_counts))
    update_rate = float(freq_hz) * 4.0 * amp_counts / step
    update_div = max(1, int(round(float(clk_hz) / update_rate)))
    return ScanConfig(
        offset_counts=volts_to_counts(offset_v),
        amp_counts=amp_counts,
        step_counts=step,
        update_div=update_div,
        limit_counts=max(0, min(8191, int(limit_counts))),
    )


def build_hold_config(*, hold_v: float) -> HoldConfig:
    return HoldConfig(hold_counts=volts_to_counts(hold_v))


def build_hold_config_from_counts(*, hold_counts: int) -> HoldConfig:
    counts = int(hold_counts)
    if counts < -8191 or counts > 8191:
        raise CustomFpgaBackendError("HOLD count must be within signed 14-bit DAC range")
    return HoldConfig(hold_counts=counts)


def build_lock_config(
    *,
    kp: int,
    ki: int,
    polarity: int,
    lock_bias_v: float,
    lock_limit_counts: int,
    correction_limit_counts: int = 128,
) -> LockConfig:
    return LockConfig(
        kp=max(0, min(8191, int(kp))),
        ki=max(0, min(8191, int(ki))),
        polarity=1 if int(polarity) else 0,
        lock_bias_counts=volts_to_counts(lock_bias_v),
        lock_limit_counts=max(0, min(8191, int(lock_limit_counts))),
        correction_limit_counts=max(0, min(8191, int(correction_limit_counts))),
    )


def build_lock_config_from_counts(
    *,
    kp: int,
    ki: int,
    polarity: int,
    lock_bias_counts: int,
    lock_limit_counts: int,
    correction_limit_counts: int = 128,
) -> LockConfig:
    return LockConfig(
        kp=max(0, min(8191, int(kp))),
        ki=max(0, min(8191, int(ki))),
        polarity=1 if int(polarity) else 0,
        lock_bias_counts=max(-8191, min(8191, int(lock_bias_counts))),
        lock_limit_counts=max(0, min(8191, int(lock_limit_counts))),
        correction_limit_counts=max(0, min(8191, int(correction_limit_counts))),
    )


def build_update_p_lock_config(*, kp: int, polarity: int) -> UpdatePLockConfig:
    kp_value = int(kp)
    if kp_value not in ALLOWED_UPDATE_KP:
        allowed = ", ".join(str(value) for value in ALLOWED_UPDATE_KP)
        raise CustomFpgaBackendError(f"APPLY P Kp must be one of: {allowed}")
    return UpdatePLockConfig(kp=kp_value, polarity=1 if int(polarity) else 0)


def missing_magic_guidance(magic_text: str) -> str:
    if magic_text.upper() != "0X00000000":
        return (
            "MAGIC mismatch. SAFE/SCAN are blocked until MAGIC is 0x4D545330. "
            "Probe registers and check the loaded bitstream or base address."
        )
    return (
        "MAGIC is 0x00000000: no custom_register_bank was read. Possible causes: "
        "the device was not programmed, an old bit file is loaded, the base address "
        "is wrong, or the timing-pass bitstream must be reloaded. Probe registers "
        "before SAFE/SCAN."
    )


def status_payload_has_expected_magic(payload: dict[str, Any]) -> bool:
    magic = str(payload.get("magic", "")).strip()
    return magic.upper() == f"0X{EXPECTED_MAGIC:08X}"


def _load_scan_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "custom_fpga_scan_control.py"
    spec = importlib.util.spec_from_file_location("_custom_fpga_scan_control", script_path)
    if spec is None or spec.loader is None:
        raise CustomFpgaBackendError(f"Cannot load helper script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _remote_python_command(
    base_addr: int,
    operation: str,
    config: ScanConfig | HoldConfig | LockConfig | UpdatePLockConfig | CaptureConfig | LockHereConfig | None,
) -> str:
    helper = _load_scan_script_module().REMOTE_HELPER
    helper_b64 = base64.b64encode(helper.encode("utf-8")).decode("ascii")
    remote_args = ["--base-addr", f"0x{int(base_addr):X}", "--op", operation]
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
        ]
    elif isinstance(config, CaptureConfig):
        remote_args += [
            "--capture-length",
            str(config.capture_length),
            "--capture-decimation",
            str(config.capture_decimation),
        ]
    elif isinstance(config, LockHereConfig):
        remote_args += [
            "--polarity",
            str(config.polarity),
            "--lock-limit-counts",
            str(config.lock_limit_counts),
            "--correction-limit-counts",
            str(config.correction_limit_counts),
            "--settle-s",
            str(config.settle_s),
            "--target-window-counts",
            str(config.target_window_counts),
            "--target-timeout-s",
            str(config.target_timeout_s),
            "--target-poll-s",
            str(config.target_poll_s),
        ]
        if config.target_out2_counts is not None:
            remote_args += ["--target-out2-counts", str(config.target_out2_counts)]
    remote_python = (
        "import base64, sys; "
        f"code=base64.b64decode('{helper_b64}').decode('utf-8'); "
        "sys.argv=['rp_custom_fpga_regs.py']+"
        f"{remote_args!r}; "
        "exec(compile(code, 'rp_custom_fpga_regs.py', 'exec'))"
    )
    return "python3 -c " + shlex.quote(remote_python)


def _parse_json_stdout(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    start = text.find("{")
    if start < 0:
        raise CustomFpgaBackendError(f"Remote command did not return JSON: {text}")
    return json.loads(text[start:])


class CustomFpgaBackend:
    def __init__(
        self,
        host: str,
        username: str = "root",
        password: str = "",
        base_addr: int = DEFAULT_BASE_ADDR,
        timeout_s: float = 12.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.base_addr = int(base_addr)
        self.timeout_s = float(timeout_s)

    def probe_registers(self) -> CustomFpgaResponse:
        return self._run("probe", None, allow_nonzero=False)

    def read_status(self) -> CustomFpgaResponse:
        return self._run("status", None, allow_nonzero=False)

    def set_mode_safe(self) -> CustomFpgaResponse:
        return self._run("safe", None, allow_nonzero=False)

    def set_mode_scan(
        self,
        *,
        offset_v: float,
        amp_v: float,
        freq_hz: float,
        step_counts: int,
        limit_counts: int,
    ) -> CustomFpgaResponse:
        config = build_scan_config(
            offset_v=offset_v,
            amp_v=amp_v,
            freq_hz=freq_hz,
            step_counts=step_counts,
            limit_counts=limit_counts,
        )
        return self._run("scan", config, allow_nonzero=False)

    def set_mode_hold(self, *, hold_v: float) -> CustomFpgaResponse:
        config = build_hold_config(hold_v=hold_v)
        return self._run("hold", config, allow_nonzero=False)

    def set_mode_hold_counts(self, *, hold_counts: int) -> CustomFpgaResponse:
        """Enter existing HOLD mode with the exact raw selected OUT2 count."""
        config = build_hold_config_from_counts(hold_counts=hold_counts)
        response = self._run("hold", config, allow_nonzero=False)
        return CustomFpgaResponse(
            operation="hold-selected-count",
            payload=response.payload,
            stdout=response.stdout,
            stderr=response.stderr,
            exit_code=response.exit_code,
            remote_command=response.remote_command,
        )

    def set_mode_p_lock(
        self,
        *,
        kp: int,
        polarity: int,
        lock_bias_v: float,
        lock_limit_counts: int,
        correction_limit_counts: int = 128,
    ) -> CustomFpgaResponse:
        config = build_lock_config(
            kp=kp,
            ki=0,
            polarity=polarity,
            lock_bias_v=lock_bias_v,
            lock_limit_counts=lock_limit_counts,
            correction_limit_counts=correction_limit_counts,
        )
        return self._run("p-lock", config, allow_nonzero=False)

    def update_p_lock(
        self,
        *,
        kp: int,
        polarity: int,
    ) -> CustomFpgaResponse:
        config = build_update_p_lock_config(kp=kp, polarity=polarity)
        return self._run("update-p-lock", config, allow_nonzero=False)

    def set_mode_pi_lock(
        self,
        *,
        kp: int,
        ki: int,
        polarity: int,
        lock_bias_v: float,
        lock_limit_counts: int,
        correction_limit_counts: int = 128,
    ) -> CustomFpgaResponse:
        config = build_lock_config(
            kp=kp,
            ki=ki,
            polarity=polarity,
            lock_bias_v=lock_bias_v,
            lock_limit_counts=lock_limit_counts,
            correction_limit_counts=correction_limit_counts,
        )
        return self._run("pi-lock", config, allow_nonzero=False)

    def capture_bias(self) -> CustomFpgaResponse:
        response = self.read_status()
        if not status_payload_has_expected_magic(response.payload):
            raise CustomFpgaBackendError(missing_magic_guidance(str(response.payload.get("magic", "--"))))
        payload = dict(response.payload)
        out2_counts = int(payload.get("out2_counts", 0))
        payload["captured_lock_bias_counts"] = out2_counts
        payload["captured_lock_bias_volts_ideal"] = counts_to_volts(out2_counts)
        payload["captured_lock_bias_volts_calibrated"] = out2_counts_to_voltage(out2_counts)
        return CustomFpgaResponse(
            operation="capture-bias",
            payload=payload,
            stdout=response.stdout,
            stderr=response.stderr,
            exit_code=response.exit_code,
            remote_command=response.remote_command,
        )

    def lock_here(
        self,
        *,
        polarity: int,
        lock_limit_counts: int,
        correction_limit_counts: int = 128,
        settle_s: float = 0.5,
        target_out2_counts: int | None = None,
        target_window_counts: int = 64,
        target_timeout_s: float = 5.0,
    ) -> CustomFpgaResponse:
        config = LockHereConfig(
            polarity=polarity,
            lock_limit_counts=lock_limit_counts,
            correction_limit_counts=correction_limit_counts,
            settle_s=settle_s,
            target_out2_counts=None if target_out2_counts is None else int(target_out2_counts),
            target_window_counts=max(0, int(target_window_counts)),
            target_timeout_s=max(0.1, float(target_timeout_s)),
        )
        return self._run("lock-here", config, allow_nonzero=False)

    def capture_waveform(self, *, capture_length: int, capture_decimation: int) -> CustomFpgaResponse:
        config = CaptureConfig(
            capture_length=max(1, min(4096, int(capture_length))),
            capture_decimation=max(1, int(capture_decimation)),
        )
        return self._run("capture", config, allow_nonzero=False)

    def read_error_snapshot(self) -> CustomFpgaResponse:
        return self.read_status()

    def read_control_snapshot(self) -> CustomFpgaResponse:
        return self.read_status()

    def set_pid_params(self, *args, **kwargs) -> None:
        del args, kwargs
        raise NotImplementedError("Custom FPGA PID parameter writes are not implemented in v1 GUI control")

    def set_output_limit(self, *args, **kwargs) -> None:
        del args, kwargs
        raise NotImplementedError("Use SCAN limit-counts in v1 GUI control")

    def _run(
        self,
        operation: str,
        config: ScanConfig | HoldConfig | LockConfig | UpdatePLockConfig | CaptureConfig | LockHereConfig | None,
        *,
        allow_nonzero: bool,
    ) -> CustomFpgaResponse:
        command = _remote_python_command(self.base_addr, operation, config)
        ssh = RedPitayaSshClient(self.host, self.username, self.password, timeout_s=self.timeout_s)
        result: SshCommandResult = ssh.run(command, timeout_s=max(self.timeout_s, 20.0))
        payload = _parse_json_stdout(result.stdout) if result.stdout.strip() else {}
        response = CustomFpgaResponse(
            operation=operation,
            payload=payload,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            remote_command=command,
        )
        if result.exit_code != 0 and not allow_nonzero:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit_code={result.exit_code}"
            raise CustomFpgaBackendError(detail)
        return response


def build_scan_config_from_namespace(args: SimpleNamespace) -> ScanConfig:
    return build_scan_config(
        offset_v=args.offset_v,
        amp_v=args.amp_v,
        freq_hz=args.freq_hz,
        step_counts=args.step_counts,
        limit_counts=args.limit_counts,
        clk_hz=getattr(args, "clk_hz", DEFAULT_CLK_HZ),
    )
