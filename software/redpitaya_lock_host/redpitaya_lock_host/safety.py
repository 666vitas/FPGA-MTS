"""Safety checks and last-resort shutdown hooks."""

import atexit
from dataclasses import dataclass
from typing import Callable


MIN_FREQUENCY_HZ = 0.1
MAX_FREQUENCY_HZ = 1000.0
MIN_AMPLITUDE_V = 0.0
MAX_AMPLITUDE_V = 1.0
MAX_OUTPUT_ABS_V = 1.0


@dataclass(frozen=True)
class ScanSettings:
    frequency_hz: float = 50.0
    amplitude_v: float = 0.2
    offset_v: float = 0.0


@dataclass(frozen=True)
class OutputSettings:
    channel: int
    waveform: str = "sine"
    frequency_hz: float = 1000.0
    amplitude_v: float = 0.05
    offset_v: float = 0.0
    phase_deg: float = 0.0
    output_range_v: float = 1.0


class SafetyError(ValueError):
    """Raised when requested output settings violate experiment limits."""


_shutdown_callbacks: list[Callable[[], None]] = []
_atexit_registered = False


def register_safe_shutdown(callback: Callable[[], None]) -> None:
    """Register a Python-exit fallback for the active hardware client."""
    global _atexit_registered
    if callback not in _shutdown_callbacks:
        _shutdown_callbacks.append(callback)
    if not _atexit_registered:
        atexit.register(run_safe_shutdown_callbacks)
        _atexit_registered = True


def unregister_safe_shutdown(callback: Callable[[], None]) -> None:
    if callback in _shutdown_callbacks:
        _shutdown_callbacks.remove(callback)


def run_safe_shutdown_callbacks() -> None:
    """Best-effort fallback for normal Python exits."""
    for callback in list(_shutdown_callbacks):
        try:
            callback()
        except Exception:
            pass


def validate_scan_settings(
    frequency_hz: float,
    amplitude_v: float,
    offset_v: float,
) -> ScanSettings:
    """Validate OUT2 triangle settings before sending SCPI commands."""
    frequency_hz = float(frequency_hz)
    amplitude_v = float(amplitude_v)
    offset_v = float(offset_v)

    if not MIN_FREQUENCY_HZ <= frequency_hz <= MAX_FREQUENCY_HZ:
        raise SafetyError(
            f"frequency_hz must be {MIN_FREQUENCY_HZ:g} to {MAX_FREQUENCY_HZ:g} Hz"
        )
    if not MIN_AMPLITUDE_V <= amplitude_v <= MAX_AMPLITUDE_V:
        raise SafetyError(
            f"amplitude_v must be {MIN_AMPLITUDE_V:g} to {MAX_AMPLITUDE_V:g} V"
        )
    if abs(offset_v) + amplitude_v > MAX_OUTPUT_ABS_V:
        raise SafetyError("abs(offset_v) + amplitude_v must be <= 1.0 V")

    return ScanSettings(
        frequency_hz=frequency_hz,
        amplitude_v=amplitude_v,
        offset_v=offset_v,
    )


def validate_output_settings(
    channel: int,
    waveform: str,
    frequency_hz: float,
    amplitude_v: float,
    offset_v: float,
    phase_deg: float = 0.0,
    output_range_v: float = 1.0,
) -> OutputSettings:
    channel = int(channel)
    if channel not in {1, 2}:
        raise SafetyError("output channel must be 1 or 2")
    waveform = str(waveform).strip().lower()
    if waveform not in {"sine", "square", "triangle", "sawtooth"}:
        raise SafetyError("waveform must be sine, square, triangle, or sawtooth")
    frequency_hz = float(frequency_hz)
    amplitude_v = float(amplitude_v)
    offset_v = float(offset_v)
    phase_deg = float(phase_deg)
    output_range_v = float(output_range_v)
    if frequency_hz <= 0:
        raise SafetyError("frequency_hz must be > 0")
    if amplitude_v < 0:
        raise SafetyError("amplitude_v must be >= 0")
    if abs(offset_v) + amplitude_v > output_range_v:
        raise SafetyError("abs(offset_v) + amplitude_v must be <= output_range_v")
    return OutputSettings(
        channel=channel,
        waveform=waveform,
        frequency_hz=frequency_hz,
        amplitude_v=amplitude_v,
        offset_v=offset_v,
        phase_deg=phase_deg,
        output_range_v=output_range_v,
    )
