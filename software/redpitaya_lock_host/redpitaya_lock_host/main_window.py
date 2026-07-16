"""PySide6 main window for Red Pitaya laser lock host V2."""

from __future__ import annotations

import time
import csv
import subprocess
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .acquisition_worker import AcquisitionWorker
from .connection_probe import ProbeResult
from .connection_workers import (
    ConnectScpiWorker,
    CustomFpgaRegisterWorker,
    DisconnectWorker,
    ProbeWorker,
    StartScpiServerWorker,
)
from .custom_fpga_backend import (
    COUNTS_PER_VOLT,
    EXPECTED_MAGIC,
    EXPECTED_VERSION,
    BasicLockConfig,
    CustomFpgaBackendError,
    build_basic_lock_config,
    find_zero_crossing_candidates,
    missing_magic_guidance,
    resolve_target_transition,
    status_payload_has_expected_magic,
    validate_basic_lock_capture,
)
from .custom_fpga_workflow import CustomFpgaMeasurements, analyze_custom_fpga_measurements
from .data_logger import save_plot_png, save_waveforms_csv, timestamped_name
from .mock_client import MockRedPitayaClient
from .out2_calibration import (
    out2_counts_to_voltage,
    out2_delta_counts_to_voltage,
    out2_voltage_to_counts,
)
from .waveform_preview import PreviewConfig, generate_waveform_preview
from .rp_scpi_client import RedPitayaScpiClient
from .safety import (
    SafetyError,
    register_safe_shutdown,
    unregister_safe_shutdown,
    validate_output_settings,
)
from .scpi_client import ScpiClient, ScpiError
from .waveform_plot import WaveformPlot


DECIMATIONS = [
    1,
    2,
    4,
    8,
    16,
    32,
    64,
    128,
    256,
    512,
    1024,
    2048,
    4096,
    8192,
    16384,
    32768,
    65536,
]

SCOPE_VOLTS_PER_DIV = (
    0.001,
    0.002,
    0.005,
    0.010,
    0.020,
    0.050,
    0.100,
    0.200,
    0.500,
    1.000,
)

SCOPE_CHANNELS = {
    "ch4": ("CH4 SCAN / OUT2", "#f2c94c", 3.0),
    "ch3": ("CH3 ERROR / OUT1", "#56b4e9", 0.0),
    "ch1": ("CH1 PD / IN1", "#59c36a", -3.0),
    "ch2": ("CH2 REF / IN2", "#f2994a", -6.0),
}

FPGA_MODE_NAMES = {
    0: "SAFE",
    1: "SCAN",
    2: "HOLD",
    3: "P_LOCK",
    4: "PI_LOCK",
}


def parse_register_value(value: object) -> int | None:
    try:
        if isinstance(value, str):
            return int(value.strip(), 0)
        return int(value)
    except (TypeError, ValueError):
        return None


def format_fpga_version(value: object) -> str:
    raw = parse_register_value(value)
    if raw is None:
        return "--"
    return f"v{(raw >> 16) & 0xFF}.{(raw >> 8) & 0xFF}.{raw & 0xFF}"


def identity_payload_matches(payload: dict[str, Any]) -> bool:
    return (
        parse_register_value(payload.get("magic")) == EXPECTED_MAGIC
        and parse_register_value(payload.get("version")) == EXPECTED_VERSION
    )


def classify_identity_error(message: str) -> str:
    text = str(message).lower()
    if any(token in text for token in ("no authentication methods available", "authentication failed", "permission denied")):
        return "Authentication failed"
    if any(token in text for token in ("no route to host", "host unreachable", "could not resolve", "name or service not known")):
        return "Host unreachable"
    if "magic mismatch" in text or "version mismatch" in text:
        return "FPGA identity mismatch"
    if any(token in text for token in ("register read", "/dev/mem", "did not return json")):
        return "Register read failed"
    return "Communication lost"


@lru_cache(maxsize=1)
def local_host_commit() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "Unavailable"
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and revision else "Unavailable"


def format_scope_voltage(value: float, *, signed: bool = False) -> str:
    """Format an ideal FPGA-count voltage for the operator-facing scope UI."""
    numeric = float(value)
    prefix = "+" if signed and numeric >= 0.0 else ""
    if abs(numeric) < 1.0:
        return f"{prefix}{numeric * 1000.0:.1f} mV"
    return f"{prefix}{numeric:.3f} V"


def format_volts_per_div(value: float) -> str:
    numeric = float(value)
    if numeric < 1.0:
        return f"{numeric * 1000.0:g} mV/div"
    return f"{numeric:g} V/div"


def choose_scope_volts_per_div(vpp_volts: float) -> float:
    """Choose the smallest 1-2-5 step that fits Vpp into about four divisions."""
    required = max(0.0, float(vpp_volts)) / 4.0
    for value in SCOPE_VOLTS_PER_DIV:
        if value >= required:
            return value
    return SCOPE_VOLTS_PER_DIV[-1]


def scope_display_transform(
    raw_y: np.ndarray,
    *,
    center: float,
    gain: float,
    vertical_offset: float,
) -> np.ndarray:
    """Return a display-only waveform copy without changing captured counts."""
    values = np.asarray(raw_y, dtype=float)
    return (values - float(center)) * float(gain) + float(vertical_offset)


def scope_auto_display_parameters(raw_y: np.ndarray) -> tuple[float, float]:
    """Choose robust display-only centering and gain for one scope channel."""
    values = np.asarray(raw_y, dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 0.0, 1.0
    center = float(np.nanmedian(finite))
    low, high = np.nanpercentile(finite, [2.0, 98.0])
    span = float(high - low)
    if span <= 0.0:
        span = float(np.nanmax(finite) - np.nanmin(finite))
    return center, 1.0 if span <= 0.0 else 2.0 / span


class LockPointSelectionError(ValueError):
    """Raised when the current capture cannot yield a safe lock point."""


def resolve_direct_error_zero_crossing(
    *,
    error_counts: np.ndarray | list[float],
    out2_counts: np.ndarray | list[float],
    clicked_index: int,
    safe_min_counts: int = -8191,
    safe_max_counts: int = 8191,
    search_radius: int = 32,
    target_window_counts: int = 64,
    saturated: bool = False,
) -> dict[str, int | float | str]:
    """Resolve an operator click to the nearest safe CH3 zero crossing."""
    error = np.asarray(error_counts, dtype=float)
    out2 = np.asarray(out2_counts, dtype=float)
    count = min(error.size, out2.size)
    if saturated or count < 16:
        raise LockPointSelectionError("No valid ERROR zero crossing in the selected region")
    error = error[:count]
    out2 = out2[:count]
    click = int(np.clip(clicked_index, 0, count - 1))
    edge = max(4, int(round(count * 0.03)))
    if click < edge or click >= count - edge:
        raise LockPointSelectionError("Selected ERROR point is too close to the capture edge")

    left = max(edge, click - max(4, int(search_radius)))
    right = min(count - edge - 1, click + max(4, int(search_radius)))
    candidates: list[tuple[int, float, int, float, str]] = []
    for index in range(left, right + 1):
        next_index = min(index + 1, count - 1)
        e0 = float(error[index])
        e1 = float(error[next_index])
        if not np.isfinite(e0) or not np.isfinite(e1):
            continue
        if e0 != 0.0 and e1 != 0.0 and e0 * e1 > 0.0:
            continue

        zero_index = index if abs(e0) <= abs(e1) else next_index
        local_left = max(edge, index - 8)
        local_right = min(count - edge - 1, index + 8)
        ramp_diffs = np.diff(out2[local_left:local_right + 1])
        ramp_diffs = ramp_diffs[np.isfinite(ramp_diffs)]
        if ramp_diffs.size < 4:
            continue
        median_ramp = float(np.nanmedian(ramp_diffs))
        if abs(median_ramp) < 0.5:
            continue
        if float(np.mean(np.sign(ramp_diffs) == np.sign(median_ramp))) < 0.8:
            continue

        slope_left = max(edge, zero_index - 1)
        slope_right = min(count - edge - 1, zero_index + 1)
        delta_out2 = float(out2[slope_right] - out2[slope_left])
        delta_error = float(error[slope_right] - error[slope_left])
        if slope_right <= slope_left or abs(delta_out2) < 0.5:
            continue
        slope = delta_error / delta_out2
        if not np.isfinite(slope) or abs(slope) < 1e-9:
            continue
        target_out2 = float(out2[zero_index])
        if target_out2 < int(safe_min_counts) or target_out2 > int(safe_max_counts):
            continue
        direction = "rising" if median_ramp > 0.0 else "falling"
        candidates.append((abs(zero_index - click), -abs(slope), zero_index, slope, direction))

    if not candidates:
        raise LockPointSelectionError("No valid ERROR zero crossing in the selected region")

    _, _, zero_index, slope, direction = min(candidates)
    target_out2_counts = int(round(float(out2[zero_index])))
    return {
        "selected_peak_index": int(zero_index),
        "zero_crossing_index": int(zero_index),
        "target_out2_counts": target_out2_counts,
        "target_out2_volts": out2_counts_to_voltage(target_out2_counts),
        "error_setpoint_counts": int(round(float(error[zero_index]))),
        "slope": float(slope),
        "ramp_direction": direction,
        "target_window_counts": int(max(1, target_window_counts)),
    }


def _nearest_ch1_peak(ch1: np.ndarray, clicked_index: int, search_radius: int) -> int:
    values = np.asarray(ch1, dtype=float)
    count = values.size
    if count < 5:
        raise LockPointSelectionError("No valid CH1 peak near selected transition")
    click = int(np.clip(clicked_index, 0, count - 1))
    left = max(1, click - max(4, int(search_radius)))
    right = min(count - 1, click + max(4, int(search_radius)))
    finite = np.isfinite(values)
    peaks = [
        index for index in range(left, right)
        if finite[index]
        and finite[index - 1]
        and finite[index + 1]
        and abs(values[index]) >= abs(values[index - 1])
        and abs(values[index]) >= abs(values[index + 1])
    ]
    if not peaks:
        window = np.arange(left, right + 1, dtype=int)
        window = window[finite[window]]
        if window.size == 0:
            raise LockPointSelectionError("No valid CH1 peak near selected transition")
        return int(window[np.argmax(np.abs(values[window]))])
    groups: list[list[int]] = []
    for index in peaks:
        if not groups or index != groups[-1][-1] + 1:
            groups.append([index])
        else:
            groups[-1].append(index)

    def group_center(group: list[int]) -> int:
        return int(np.floor((group[0] + group[-1]) / 2.0 + 0.5))

    best_group = min(
        groups,
        key=lambda group: (
            abs(group_center(group) - click),
            -max(abs(float(values[index])) for index in group),
        ),
    )
    return group_center(best_group)


def resolve_lock_point_selection(
    *,
    ch1_counts: np.ndarray | list[float],
    error_counts: np.ndarray | list[float],
    out2_counts: np.ndarray | list[float],
    clicked_index: int,
    error_setpoint_counts: float = 0.0,
    safe_min_counts: int = -8191,
    safe_max_counts: int = 8191,
    search_radius: int = 128,
    target_window_counts: int = 64,
    saturated: bool = False,
) -> dict[str, int | float | str]:
    """Resolve a CH1 click into the safest nearby CH3/CH4 lock-point candidate."""
    ch1 = np.asarray(ch1_counts, dtype=float)
    error = np.asarray(error_counts, dtype=float)
    out2 = np.asarray(out2_counts, dtype=float)
    count = min(ch1.size, error.size, out2.size)
    if saturated:
        raise LockPointSelectionError("No valid zero crossing near selected transition; adjust scan offset/amp or target window.")
    if count < 16:
        raise LockPointSelectionError("No valid zero crossing near selected transition; adjust scan offset/amp or target window.")
    ch1 = ch1[:count]
    error = error[:count]
    out2 = out2[:count]
    clicked = int(np.clip(clicked_index, 0, count - 1))
    peak = _nearest_ch1_peak(ch1, clicked, search_radius)
    edge = max(4, int(round(count * 0.03)))
    if peak < edge or peak >= count - edge:
        raise LockPointSelectionError("No valid zero crossing near selected transition; adjust scan offset/amp or target window.")

    left = max(edge, peak - max(4, int(search_radius)))
    right = min(count - edge - 1, peak + max(4, int(search_radius)))
    setpoint = float(error_setpoint_counts)
    candidates: list[tuple[float, int, float, str, int, float]] = []
    for index in range(left, right):
        e0 = float(error[index] - setpoint)
        e1 = float(error[index + 1] - setpoint)
        if not np.isfinite(e0) or not np.isfinite(e1) or e0 * e1 > 0.0:
            continue
        local_left = max(edge, index - 8)
        local_right = min(count - 1 - edge, index + 8)
        ramp_diffs = np.diff(out2[local_left:local_right + 1])
        ramp_diffs = ramp_diffs[np.isfinite(ramp_diffs)]
        if ramp_diffs.size < 4:
            continue
        median_ramp = float(np.nanmedian(ramp_diffs))
        if abs(median_ramp) < 0.5:
            continue
        same_direction = float(np.mean(np.sign(ramp_diffs) == np.sign(median_ramp)))
        if same_direction < 0.8:
            continue
        delta_out2 = float(out2[index + 1] - out2[index])
        if not np.isfinite(delta_out2) or abs(delta_out2) < 0.5:
            continue
        slope = float((error[index + 1] - error[index]) / delta_out2)
        if not np.isfinite(slope):
            continue
        target_out2 = float(out2[index] if abs(e0) <= abs(e1) else out2[index + 1])
        if target_out2 < int(safe_min_counts) or target_out2 > int(safe_max_counts):
            continue
        direction = "rising" if median_ramp > 0.0 else "falling"
        candidates.append((abs(slope), abs(index - peak), slope, direction, index, target_out2))

    if not candidates:
        # Distinguish an undetermined ramp from an ordinary missing crossing.
        local_diffs = np.diff(out2[max(edge, peak - 8):min(count - edge, peak + 9)])
        finite_diffs = local_diffs[np.isfinite(local_diffs)]
        if finite_diffs.size == 0 or abs(float(np.nanmedian(finite_diffs))) < 0.5:
            raise LockPointSelectionError("Ramp direction unavailable; cannot confirm lock point.")
        raise LockPointSelectionError("No valid zero crossing near selected transition; adjust scan offset/amp or target window.")

    # Maximum |dError/dOut2| is primary; distance to the selected CH1 peak breaks ties.
    best_abs_slope, best_distance, best_slope, direction, zero_index, target_out2 = max(
        candidates, key=lambda item: (item[0], -item[1])
    )
    return {
        "selected_peak_index": int(peak),
        "zero_crossing_index": int(zero_index),
        "target_out2_counts": int(round(target_out2)),
        "target_out2_volts": out2_counts_to_voltage(target_out2),
        "error_setpoint_counts": int(round(setpoint)),
        "slope": float(best_slope),
        "ramp_direction": direction,
        "target_window_counts": int(max(1, target_window_counts)),
    }

DISCONNECTED = "DISCONNECTED"
PROBING = "PROBING"
SSH_AVAILABLE = "SSH_AVAILABLE"
SCPI_STARTING = "SCPI_STARTING"
SCPI_READY = "SCPI_READY"
SCPI_CONNECTED = "SCPI_CONNECTED"
ACQUIRING = "ACQUIRING"
CUSTOM_FPGA_BUSY = "CUSTOM_FPGA_BUSY"
ERROR = "ERROR"


@dataclass
class OutputControl:
    enable: QCheckBox
    waveform: QComboBox
    frequency: QDoubleSpinBox
    amplitude: QDoubleSpinBox
    offset: QDoubleSpinBox
    phase: QDoubleSpinBox
    apply_button: QPushButton
    disable_button: QPushButton


class ChannelPanel(QGroupBox):
    def __init__(self, title: str, subtitle: str, y_label: str = "Voltage [V]") -> None:
        super().__init__(title)
        layout = QVBoxLayout(self)
        controls = QGridLayout()
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setWordWrap(True)
        self.stats_label = QLabel("Vpp -- | min -- | max -- | mean --")
        self.stats_label.setWordWrap(True)
        self.warning_label = QLabel("")
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #b00020; font-weight: 600;")
        self.visible_check = QCheckBox("Visible")
        self.visible_check.setChecked(True)
        self.auto_y_check = QCheckBox("Auto Y")
        self.auto_y_check.setChecked(True)
        self.scale_counts_div = QSpinBox()
        self.scale_counts_div.setRange(1, 32768)
        self.scale_counts_div.setValue(512)
        self.scale_counts_div.setToolTip("Display scale only: counts per vertical division.")
        self.center_counts = QSpinBox()
        self.center_counts.setRange(-8191, 8191)
        self.center_counts.setValue(0)
        self.center_counts.setToolTip("Display center only: does not modify captured counts.")
        self.reset_button = QPushButton("Reset")
        self.plot = WaveformPlot(title, y_label)
        self.plot.setMinimumSize(360, 230)
        self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._last_x = np.asarray([], dtype=float)
        self._last_y = np.asarray([], dtype=float)
        layout.setContentsMargins(10, 18, 10, 10)
        layout.setSpacing(6)
        controls.addWidget(self.visible_check, 0, 0)
        controls.addWidget(self.auto_y_check, 0, 1)
        controls.addWidget(QLabel("Scale counts/div"), 1, 0)
        controls.addWidget(self.scale_counts_div, 1, 1)
        controls.addWidget(QLabel("Center counts"), 2, 0)
        controls.addWidget(self.center_counts, 2, 1)
        controls.addWidget(self.reset_button, 3, 0, 1, 2)
        layout.addWidget(self.subtitle_label)
        layout.addLayout(controls)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.plot, stretch=1)
        self.visible_check.toggled.connect(self.apply_display_range)
        self.auto_y_check.toggled.connect(self.apply_display_range)
        self.scale_counts_div.valueChanged.connect(self.apply_display_range)
        self.center_counts.valueChanged.connect(self.apply_display_range)
        self.reset_button.clicked.connect(self.reset_display)

    def set_data(self, x: np.ndarray, y: np.ndarray) -> None:
        self._last_x = np.asarray(x, dtype=float).copy()
        self._last_y = np.asarray(y, dtype=float).copy()
        self.plot.set_data(self._last_x, self._last_y)
        if y.size:
            v_min = float(np.nanmin(y))
            v_max = float(np.nanmax(y))
            v_mean = float(np.nanmean(y))
            self.stats_label.setText(
                f"Vpp {v_max - v_min:.4g} | min {v_min:.4g} | "
                f"max {v_max:.4g} | mean {v_mean:.4g}"
            )
        else:
            self.stats_label.setText("Vpp -- | min -- | max -- | mean --")
        self.apply_display_range()

    def set_warning(self, text: str) -> None:
        self.warning_label.setText(text)

    def apply_display_range(self) -> None:
        visible = self.visible_check.isChecked()
        self.plot.setVisible(visible)
        self.plot.curve.setVisible(visible and self._last_y.size > 0)
        if not visible or self._last_x.size == 0 or self._last_y.size == 0:
            return
        if self.auto_y_check.isChecked():
            self.plot._fit_ranges(self._last_x, self._last_y)
            return
        half_span = float(self.scale_counts_div.value()) * 4.0
        center = float(self.center_counts.value())
        self.plot.plot_item.setYRange(center - half_span, center + half_span, padding=0.0)

    def reset_display(self) -> None:
        self.visible_check.setChecked(True)
        self.auto_y_check.setChecked(True)
        if self._last_y.size:
            self.center_counts.setValue(int(round(float(np.nanmean(self._last_y)))))
        self.apply_display_range()


class MainWindow(QMainWindow):
    def __init__(self, config: dict[str, Any], start_mock: bool = False) -> None:
        super().__init__()
        self.config = config
        self.start_mock = start_mock
        self.preview_config = PreviewConfig.from_mapping(self.config.get("preview", {}))
        self.client: RedPitayaScpiClient | MockRedPitayaClient | None = None
        self.acquisition_worker: AcquisitionWorker | None = None
        self.last_probe: ProbeResult | None = None
        self.last_waveforms = self._empty_waveforms()
        self.custom_scope_data: dict[str, np.ndarray] | None = None
        self.custom_scope_display_data: dict[str, np.ndarray] = {}
        self.custom_scope_display_state: dict[str, dict[str, float]] = {}
        self._updating_scope_display_controls = False
        self.custom_last_capture_payload: dict[str, Any] = {}
        self.selected_lock_point: dict[str, int | float] | None = None
        self.pending_lock_point: dict[str, int | float] | None = None
        self.pending_target_peak: dict[str, int | float] | None = None
        self.custom_scope_valid_for_selection = False
        self.live_capture_active = False
        self.capture_in_flight = False
        self.lock_error_over_threshold_count = 0
        self.p_lock_ready = False
        self.applied_kp = 0
        self.applied_polarity_index = 0
        self.basic_lock_active = False
        self.basic_lock_queue: list[str] = []
        self.basic_lock_config: BasicLockConfig | None = None
        self.basic_lock_candidates: list[Any] = []
        self.current_custom_operation: str | None = None
        self.connection_state = DISCONNECTED
        self.system_identity_matched = False
        self.system_identity_communication_ok = False
        self.system_identity_saturated = False
        self.last_identity_probe_time: datetime | None = None
        self.host_code_revision = local_host_commit()
        self.worker: (
            ProbeWorker
            | StartScpiServerWorker
            | ConnectScpiWorker
            | DisconnectWorker
            | CustomFpgaRegisterWorker
            | None
        ) = None
        self.current_sample_rate = 125e6 / 1024
        self._last_frame_time: float | None = None
        self._safe_shutdown_registered = False

        self.setWindowTitle("FPGA-MTS Laser Lock Scope")
        self._apply_app_font()
        self._build_ui()
        self._load_defaults()

        self.mock_timer = QTimer(self)
        self.mock_timer.setInterval(int(self.config.get("gui", {}).get("refresh_ms", 100)))
        self.mock_timer.timeout.connect(self._poll_mock_waveforms)
        self.custom_live_timer = QTimer(self)
        self.custom_live_timer.setSingleShot(True)
        self.custom_live_timer.timeout.connect(self._run_live_capture_cycle)

        self._set_connected_state(False)
        self._set_acquiring_state(False)
        self._set_connection_state(DISCONNECTED)
        self._update_sample_rate_label()
        self._redraw_from_last_waveforms()
        self.statusBar().showMessage("Disconnected")
        if not self.start_mock:
            QTimer.singleShot(0, self._startup_custom_register_probe)

    def _apply_app_font(self) -> None:
        font = QFont("Microsoft YaHei UI", 9)
        self.setFont(font)

    @staticmethod
    def _configure_form(form: QFormLayout) -> None:
        form.setContentsMargins(10, 18, 10, 10)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)

    @staticmethod
    def _style_field(widget: QWidget) -> None:
        widget.setMinimumWidth(120)
        widget.setMinimumHeight(28)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    @staticmethod
    def _style_button(button: QPushButton) -> None:
        button.setMinimumHeight(30)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _build_ui(self) -> None:
        root = QWidget(self)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(10, 10, 10, 8)
        main_layout.setSpacing(8)
        controls = self._build_controls()
        plots = self._build_plots()

        left_column = QWidget()
        left_column.setMaximumWidth(360)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self._build_operator_connection_group())
        left_layout.addWidget(self._build_operator_scan_group())
        left_layout.addWidget(self._build_system_identity_group())
        left_layout.addStretch(1)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        self.operator_waveform_group = QGroupBox("Three-Channel Waveform")
        waveform_layout = QVBoxLayout(self.operator_waveform_group)
        waveform_layout.setContentsMargins(8, 16, 8, 8)
        waveform_layout.setSpacing(6)
        waveform_layout.addWidget(self._build_channel_status_bar())
        waveform_layout.addWidget(self._build_capture_toolbar())
        waveform_layout.addWidget(plots, stretch=1)
        right_layout.addWidget(self.operator_waveform_group, stretch=1)
        right_layout.addWidget(self._build_experiment_toolbar())

        main_layout.addWidget(left_column)
        main_layout.addWidget(right_column, stretch=1)

        # Legacy engineering widgets remain alive for backend compatibility and tests,
        # but are deliberately not part of the normal experiment interface.
        self.hidden_engineering_controls = controls
        self.hidden_engineering_controls.setParent(root)
        self.hidden_engineering_controls.setVisible(False)
        self.custom_scope_raw_controls.setParent(root)
        self.custom_scope_raw_controls.setVisible(False)
        self.custom_scope_stats.setParent(root)
        self.custom_scope_stats.setVisible(False)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar(self))
        self._connect_signals()

    def _build_operator_connection_group(self) -> QGroupBox:
        self.operator_connection_group = QGroupBox("Device Connection")
        form = QFormLayout(self.operator_connection_group)
        self._configure_form(form)
        self.probe_button.setText("CONNECT")
        self.disconnect_button.setText("DISCONNECT")
        buttons = QHBoxLayout()
        buttons.addWidget(self.probe_button)
        buttons.addWidget(self.disconnect_button)
        self.operator_connection_status_label = QLabel("Disconnected")
        self.operator_connection_status_label.setStyleSheet("font-weight: 600;")
        form.addRow("Host / IP", self.host_edit)
        form.addRow("Username", self.ssh_user_edit)
        form.addRow("Password", self.ssh_password_edit)
        form.addRow(buttons)
        form.addRow("Status", self.operator_connection_status_label)
        return self.operator_connection_group

    def _build_operator_scan_group(self) -> QGroupBox:
        self.operator_scan_group = QGroupBox("PZT Scan")
        form = QFormLayout(self.operator_scan_group)
        self._configure_form(form)
        self.custom_scan_button.setText("START SCAN")
        self.scan_stop_safe_button = QPushButton("STOP / SAFE")
        self._style_button(self.scan_stop_safe_button)
        buttons = QHBoxLayout()
        buttons.addWidget(self.custom_scan_button)
        buttons.addWidget(self.scan_stop_safe_button)
        self.operator_scan_state_label = QLabel("SAFE")
        self.operator_scan_state_label.setStyleSheet("font-weight: 700;")
        form.addRow("Scan center", self.custom_offset_v)
        form.addRow("Scan amplitude", self.custom_amp_v)
        form.addRow("Scan frequency", self.custom_freq_hz)
        form.addRow("PZT safe min", self.basic_pzt_min_v)
        form.addRow("PZT safe max", self.basic_pzt_max_v)
        form.addRow(buttons)
        form.addRow("Status", self.operator_scan_state_label)
        return self.operator_scan_group

    def _build_system_identity_group(self) -> QGroupBox:
        self.system_identity_group = QGroupBox("System Identity")
        form = QFormLayout(self.system_identity_group)
        form.setContentsMargins(10, 16, 10, 8)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(4)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.system_connection_value = QLabel("Disconnected")
        self.system_host_value = QLabel(self._target_host())
        self.system_fpga_version_value = QLabel("--")
        self.system_identity_value = QLabel("Unknown")
        self.system_mode_value = QLabel("UNKNOWN")
        self.system_output_value = QLabel("Unknown")
        self.system_last_probe_title = QLabel("Last probe")
        self.system_last_probe_value = QLabel("--")
        self.system_bitstream_value = QLabel("Build date unavailable")
        self.system_bitstream_value.setToolTip(
            "Not encoded in the current FPGA register protocol."
        )
        self.system_host_code_value = QLabel(self.host_code_revision)
        self.system_host_code_value.setToolTip(
            "Local host repository commit; does not identify the loaded bitstream."
        )
        self.system_identity_error_label = QLabel("")
        self.system_identity_error_label.setWordWrap(True)
        self.system_identity_error_label.setStyleSheet("color: #b00020; font-weight: 600;")
        self.system_identity_refresh_button = QPushButton("REFRESH IDENTITY")
        self._style_button(self.system_identity_refresh_button)

        form.addRow("Connection", self.system_connection_value)
        form.addRow("Host", self.system_host_value)
        form.addRow("FPGA", self.system_fpga_version_value)
        form.addRow("Identity", self.system_identity_value)
        form.addRow("Mode", self.system_mode_value)
        form.addRow("Output", self.system_output_value)
        form.addRow(self.system_last_probe_title, self.system_last_probe_value)
        form.addRow("Bitstream", self.system_bitstream_value)
        form.addRow("Host code", self.system_host_code_value)
        form.addRow(self.system_identity_refresh_button)
        form.addRow(self.system_identity_error_label)
        return self.system_identity_group

    def _update_system_identity_host(self) -> None:
        if hasattr(self, "system_host_value"):
            self.system_host_value.setText(self._target_host())

    def _refresh_system_identity(self) -> None:
        self._update_system_identity_host()
        self.system_identity_error_label.setText("")
        self._start_custom_fpga_operation("status", preserve_basic=True)

    def _clear_system_identity(self, connection: str, error: str = "") -> None:
        self.system_identity_matched = False
        self.system_identity_communication_ok = False
        self.system_identity_saturated = False
        self.system_connection_value.setText(connection)
        self.system_fpga_version_value.setText("--")
        self.system_identity_value.setText("Unknown")
        self.system_mode_value.setText("UNKNOWN")
        self.system_output_value.setText("Unknown")
        self.system_identity_error_label.setText(error)
        self.system_identity_group.setToolTip("")
        self._update_system_identity_host()
        if self.last_identity_probe_time is None:
            self.system_last_probe_title.setText("Last probe")
            self.system_last_probe_value.setText("--")
        else:
            self.system_last_probe_title.setText("Last successful probe")
            self.system_last_probe_value.setText(
                self.last_identity_probe_time.strftime("%H:%M:%S")
            )

    def _update_system_identity_from_payload(
        self,
        payload: dict[str, Any],
        *,
        record_probe: bool,
    ) -> None:
        required = ("magic", "version", "mode", "enable", "status_raw")
        if any(parse_register_value(payload.get(key)) is None for key in required):
            if record_probe:
                self._clear_system_identity("Connected", "Register read failed")
                self.operator_alert_label.setText("Register read failed")
                self._apply_button_state(self.connection_state)
            return

        magic = int(parse_register_value(payload["magic"]))
        version = int(parse_register_value(payload["version"]))
        mode = int(parse_register_value(payload["mode"]))
        enable = int(parse_register_value(payload["enable"]))
        status = int(parse_register_value(payload["status_raw"]))
        saturated = bool(payload.get("saturated", bool(status & 0x2)))

        self.system_identity_communication_ok = True
        self.system_identity_matched = identity_payload_matches(payload)
        self.system_identity_saturated = saturated
        self.system_connection_value.setText("Connected")
        self.system_fpga_version_value.setText(format_fpga_version(version))
        self.system_identity_value.setText(
            "Matched" if self.system_identity_matched else "Mismatch"
        )
        self.system_mode_value.setText(FPGA_MODE_NAMES.get(mode, "UNKNOWN"))
        self.system_output_value.setText(
            "Saturated" if saturated else ("Enabled" if enable else "Disabled")
        )
        identity_message = (
            "Saturation detected"
            if saturated
            else ("" if self.system_identity_matched else "FPGA identity mismatch")
        )
        self.system_identity_error_label.setText(identity_message)
        self.operator_connection_status_label.setText("Connected")
        self.operator_alert_label.setText(identity_message)
        self._update_system_identity_host()

        details = (
            f"MAGIC   0x{magic:08X}\n"
            f"VERSION 0x{version:08X}\n"
            f"MODE    {mode}\n"
            f"ENABLE  {enable}\n"
            f"STATUS  0x{status:08X}"
        )
        self.system_identity_group.setToolTip(details)
        for label in (
            self.system_fpga_version_value,
            self.system_identity_value,
            self.system_mode_value,
            self.system_output_value,
        ):
            label.setToolTip(details)

        if record_probe:
            self.last_identity_probe_time = datetime.now()
            self.system_last_probe_title.setText("Last probe")
            self.system_last_probe_value.setText(
                self.last_identity_probe_time.strftime("%H:%M:%S")
            )
        if saturated:
            self._stop_live_capture("Saturation detected; Live stopped")
        elif not self.system_identity_matched:
            self._stop_live_capture("FPGA identity mismatch; Live stopped")
        self._apply_button_state(self.connection_state)

    def _build_channel_status_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.channel_card_groups: dict[str, QGroupBox] = {}
        self.channel_card_labels: dict[str, QLabel] = {}
        calibration_tip = (
            "Ideal voltage conversion from FPGA counts; hardware calibration not yet verified"
        )
        titles = {"ch4": "CH4 SCAN", "ch3": "CH3 ERROR", "ch1": "CH1 PD"}
        for key in ("ch4", "ch3", "ch1"):
            _title, color, _position = SCOPE_CHANNELS[key]
            summary = QLabel(f"{titles[key]} | Vpp --")
            summary.setToolTip(calibration_tip)
            summary.setStyleSheet(
                f"color: {color}; font-weight: 700; border: 1px solid {color}; padding: 6px;"
            )
            layout.addWidget(summary, stretch=1)
            self.channel_card_groups[key] = summary
            self.channel_card_labels[key] = summary
        return bar

    def _build_capture_toolbar(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        buttons = QHBoxLayout()
        self.custom_start_live_button.setText("RUN")
        self.custom_stop_live_button.setText("STOP")
        self.custom_capture_once_button.setText("SINGLE")
        self.custom_scope_default_button.setText("AUTO DISPLAY")
        for button in (
            self.custom_start_live_button,
            self.custom_stop_live_button,
            self.custom_capture_once_button,
            self.custom_scope_default_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.custom_scope_timebase_label = QLabel("Window -- ms | Time -- ms/div | Scan -- Hz")
        layout.addWidget(self.custom_scope_timebase_label)
        return panel

    def _build_experiment_toolbar(self) -> QGroupBox:
        self.operator_lock_group = QGroupBox("Manual Lock Point and P Lock")
        panel = self.operator_lock_group
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(6)

        lock_row = QHBoxLayout()
        self.custom_pick_lock_button = QPushButton("PICK LOCK POINT")
        self.custom_pick_lock_button.setCheckable(True)
        self._style_button(self.custom_pick_lock_button)
        self.custom_confirm_lock_point_button.setText("CONFIRM")
        self.custom_lock_button.setText("LOCK HERE")
        self.custom_safe_button.setText("SAFE")
        self.custom_safe_button.setStyleSheet("font-weight: 700; color: #ffffff; background: #a32020;")
        for button in (
            self.custom_pick_lock_button,
            self.custom_confirm_lock_point_button,
            self.custom_lock_button,
        ):
            lock_row.addWidget(button)
        lock_row.addWidget(QLabel("Kp"))
        lock_row.addWidget(self.custom_kp)
        lock_row.addWidget(QLabel("Polarity"))
        self.custom_polarity.clear()
        self.custom_polarity.addItem("Normal", "normal")
        self.custom_polarity.addItem("Invert", "invert")
        lock_row.addWidget(self.custom_polarity)
        lock_row.addWidget(self.custom_apply_p_button)
        lock_row.addWidget(self.custom_safe_button)
        layout.addLayout(lock_row)

        status_row = QHBoxLayout()
        self.operator_state_label = QLabel("SAFE")
        self.operator_state_label.setStyleSheet("font-weight: 700; color: #72d6ff;")
        self.operator_candidate_label = QLabel(
            "Candidate lock point | PZT: -- | Direction: -- | Status: Not selected"
        )
        self.operator_candidate_label.setWordWrap(True)
        self.operator_alert_label = QLabel("")
        self.operator_alert_label.setStyleSheet("color: #ff8a80; font-weight: 600;")
        status_row.addWidget(self.operator_state_label)
        status_row.addWidget(self.operator_candidate_label, stretch=1)
        status_row.addWidget(self.operator_alert_label)
        layout.addLayout(status_row)

        self.lock_point_selection_mode = QComboBox(panel)
        self.lock_point_selection_mode.addItem("Direct ERROR Zero Crossing")
        self.lock_point_selection_mode.setVisible(False)
        return panel

    def _build_controls(self) -> QWidget:
        content = QWidget()
        content.setMinimumWidth(430)
        content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addWidget(self._connection_group())
        self.app_mode_tabs = QTabWidget()
        self.app_mode_tabs.addTab(self._custom_fpga_observe_page(), "Custom FPGA Observe")
        self.app_mode_tabs.addTab(self._lock_workflow_page(), "Lock Workflow")
        self.app_mode_tabs.addTab(self._data_log_page(), "Data Log")
        layout.addWidget(self.app_mode_tabs, stretch=1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setMinimumWidth(430)
        scroll.resize(460, scroll.height())
        scroll.setMaximumWidth(680)
        scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        return scroll

    def _connection_group(self) -> QGroupBox:
        group = QGroupBox("Custom FPGA Lock Host")
        form = QFormLayout(group)
        self._configure_form(form)
        self.host_edit = QLineEdit()
        self.resolved_ip_combo = QComboBox()
        self.resolved_ip_combo.setEditable(True)
        self.ssh_user_edit = QLineEdit("root")
        self.ssh_password_edit = QLineEdit()
        self.ssh_password_edit.setEchoMode(QLineEdit.Password)
        self.mock_check = QCheckBox("Mock Mode")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Custom FPGA Mode"])
        self.mode_explain_label = QLabel("")
        self.mode_explain_label.setWordWrap(True)
        self.probe_button = QPushButton("Probe")
        self.start_scpi_button = QPushButton("Start SCPI Server")
        self.connect_scpi_button = QPushButton("Connect SCPI")
        self.start_scpi_button.setVisible(False)
        self.connect_scpi_button.setVisible(False)
        self.disconnect_button = QPushButton("Disconnect")
        self.connection_status = QTextEdit()
        self.connection_status.setReadOnly(True)
        self.connection_status.setMaximumHeight(110)
        self.connection_status.setMinimumHeight(80)
        self.connection_status.setPlainText("SSH -- | Web -- | SCPI -- | IP --")
        self.scpi_warning_label = QLabel(
            "Custom FPGA Lock Host only: do not start redpitaya_scpi overlay here. "
            "Official SCPI/ASG controls are hidden from the main lock workflow."
        )
        self.scpi_warning_label.setWordWrap(True)
        self.scpi_warning_label.setStyleSheet("color: #9a5b00;")
        button_row = QGridLayout()
        button_row.setHorizontalSpacing(8)
        button_row.setVerticalSpacing(6)
        button_row.addWidget(self.probe_button, 0, 0)
        button_row.addWidget(self.disconnect_button, 0, 1)
        for widget in (
            self.host_edit,
            self.resolved_ip_combo,
            self.ssh_user_edit,
            self.ssh_password_edit,
            self.mode_combo,
        ):
            self._style_field(widget)
        for button in (
            self.probe_button,
            self.start_scpi_button,
            self.connect_scpi_button,
            self.disconnect_button,
        ):
            self._style_button(button)
        form.addRow("Host", self.host_edit)
        form.addRow("resolved IP", self.resolved_ip_combo)
        form.addRow("SSH user", self.ssh_user_edit)
        form.addRow("SSH password", self.ssh_password_edit)
        form.addRow("host mode", self.mode_combo)
        form.addRow(self.mock_check)
        form.addRow(button_row)
        form.addRow(self.connection_status)
        form.addRow(self.mode_explain_label)
        form.addRow(self.scpi_warning_label)
        return group

    def _hardware_bringup_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._output_group())
        layout.addWidget(self._acquisition_group())
        layout.addWidget(self._export_group())
        layout.addStretch(1)
        return page

    def _custom_fpga_observe_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        wiring = QLabel(
            "IN1 = PD/MTS after analog BPF + amplifier, < +/-1 V\n"
            "IN2 = 4.6 MHz REF, < +/-1 V\n"
            "OUT1 = FPGA laser_error -> oscilloscope\n"
            "OUT2 = selected_out2 -> laser dedicated PZT / Scan input for SCAN and P_LOCK\n"
            "Never connect OUT2 to laser current modulation, D2-125 outputs, or any other output terminal."
        )
        wiring.setWordWrap(True)
        layout.addWidget(wiring)
        layout.addWidget(self._custom_fpga_control_group())

        group = QGroupBox("Manual Oscilloscope Readings")
        form = QFormLayout(group)
        self._configure_form(form)
        self.obs_out1_vpp = self._measurement_spin(" Vpp")
        self.obs_out1_min = self._measurement_spin(" V")
        self.obs_out1_max = self._measurement_spin(" V")
        self.obs_out2_vpp = self._measurement_spin(" Vpp")
        self.obs_out2_min = self._measurement_spin(" V")
        self.obs_out2_max = self._measurement_spin(" V")
        self.obs_pd_vpp = self._measurement_spin(" Vpp")
        self.obs_ref_amp = self._measurement_spin(" V")
        self.obs_notes = QTextEdit()
        self.obs_notes.setMinimumHeight(70)
        self.obs_notes.setPlaceholderText("Scope observations, wiring, fast drift/jump notes")
        self.obs_analyze_button = QPushButton("Analyze Observe Readings")
        self._style_button(self.obs_analyze_button)
        self.obs_result_label = QLabel("OUT2/OUT1 ratio -- | safety --")
        self.obs_result_label.setWordWrap(True)
        self.obs_result_label.setStyleSheet("font-weight: 600;")
        form.addRow("OUT1 error Vpp", self.obs_out1_vpp)
        form.addRow("OUT1 error min", self.obs_out1_min)
        form.addRow("OUT1 error max", self.obs_out1_max)
        form.addRow("OUT2 control Vpp", self.obs_out2_vpp)
        form.addRow("OUT2 control min", self.obs_out2_min)
        form.addRow("OUT2 control max", self.obs_out2_max)
        form.addRow("PD / absorption Vpp", self.obs_pd_vpp)
        form.addRow("REF amplitude", self.obs_ref_amp)
        form.addRow("notes", self.obs_notes)
        form.addRow(self.obs_analyze_button)
        form.addRow(self.obs_result_label)
        layout.addWidget(group)
        layout.addStretch(1)
        return page

    def _custom_fpga_control_group(self) -> QGroupBox:
        group = QGroupBox("Custom FPGA Control")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 18, 10, 10)
        layout.setSpacing(8)

        basic_group = QGroupBox("BASIC LOCK")
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setContentsMargins(10, 18, 10, 10)
        basic_layout.setSpacing(8)
        basic_form = QFormLayout()
        self._configure_form(basic_form)
        self.basic_pzt_min_v = self._custom_double_spin(0.80, -1.0, 1.0, 4, " V")
        self.basic_pzt_max_v = self._custom_double_spin(0.90, -1.0, 1.0, 4, " V")
        self.basic_lock_button = QPushButton("BASIC LOCK")
        self.basic_safe_button = QPushButton("SAFE")
        self._style_button(self.basic_lock_button)
        self._style_button(self.basic_safe_button)
        self.basic_status_label = QLabel("state: IDLE")
        self.basic_status_label.setWordWrap(True)
        self.basic_status_label.setStyleSheet("font-weight: 600;")
        self.basic_candidate_label = QLabel("candidate: --")
        self.basic_candidate_label.setWordWrap(True)
        basic_buttons = QHBoxLayout()
        basic_buttons.setSpacing(8)
        basic_buttons.addWidget(self.basic_lock_button)
        basic_buttons.addWidget(self.basic_safe_button)
        basic_form.addRow("PZT safe min", self.basic_pzt_min_v)
        basic_form.addRow("PZT safe max", self.basic_pzt_max_v)
        basic_layout.addLayout(basic_form)
        basic_layout.addLayout(basic_buttons)
        basic_layout.addWidget(self.basic_status_label)
        basic_layout.addWidget(self.basic_candidate_label)

        advanced_group = QGroupBox("Advanced")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(advanced_group)
        advanced_layout.setContentsMargins(10, 18, 10, 10)
        advanced_layout.setSpacing(8)
        self.custom_advanced_body = QWidget()
        advanced_body_layout = QVBoxLayout(self.custom_advanced_body)
        advanced_body_layout.setContentsMargins(0, 0, 0, 0)
        advanced_body_layout.setSpacing(8)
        self.custom_advanced_body.setVisible(False)
        advanced_group.toggled.connect(self.custom_advanced_body.setVisible)
        form = QFormLayout()
        self._configure_form(form)
        self.custom_base_addr_edit = QLineEdit("0x40600000")
        self.custom_offset_v = self._custom_double_spin(0.85, -1.0, 1.0, 4, " V")
        self.custom_amp_v = self._custom_double_spin(0.05, 0.0, 1.0, 4, " V")
        self.custom_freq_hz = self._custom_double_spin(10.0, 0.001, 100000.0, 3, " Hz")
        self.custom_step_counts = QSpinBox()
        self.custom_step_counts.setRange(1, 8191)
        self.custom_step_counts.setValue(1)
        self.custom_limit_counts = QSpinBox()
        self.custom_limit_counts.setRange(0, 8191)
        self.custom_limit_counts.setValue(8191)
        self.custom_hold_v = self._custom_double_spin(0.0, -1.0, 1.0, 4, " V")
        self.custom_kp = QComboBox()
        self.custom_kp.addItems(["0", "4", "8", "16", "32"])
        self.custom_ki = QSpinBox()
        self.custom_ki.setRange(0, 8191)
        self.custom_ki.setValue(0)
        self.custom_ki.setToolTip("Current LOCK path is P-only; Ki/PI is disabled in the timing-friendly RTL.")
        self.custom_ki.setEnabled(False)
        self.custom_polarity = QComboBox()
        self.custom_polarity.addItems(["normal", "invert"])
        self.custom_lock_bias_v = self._custom_double_spin(0.0, -1.0, 1.0, 4, " V")
        self.custom_lock_bias_v.setToolTip("LOCK does not use this voltage estimate; it captures OUT2_MONITOR counts.")
        self.custom_lock_limit_counts = QSpinBox()
        self.custom_lock_limit_counts.setRange(0, 8191)
        self.custom_lock_limit_counts.setValue(8191)
        self.custom_correction_limit_counts = QSpinBox()
        self.custom_correction_limit_counts.setRange(0, 8191)
        self.custom_correction_limit_counts.setValue(128)
        self.custom_zero_threshold_counts = QSpinBox()
        self.custom_zero_threshold_counts.setRange(1, 8191)
        self.custom_zero_threshold_counts.setValue(64)
        self.custom_capture_length = QSpinBox()
        self.custom_capture_length.setRange(1, 4096)
        self.custom_capture_length.setValue(2048)
        self.custom_capture_decimation = QSpinBox()
        self.custom_capture_decimation.setRange(1, 1_000_000)
        self.custom_capture_decimation.setValue(1024)
        self.custom_capture_view_mode = QComboBox()
        self.custom_capture_view_mode.addItems(["Lock View", "REF Debug"])
        self.custom_ref_debug_decimation = QComboBox()
        self.custom_ref_debug_decimation.addItems(["1", "2", "4", "8"])
        self.custom_live_interval_ms = QComboBox()
        self.custom_live_interval_ms.addItems(["500", "1000", "2000"])
        self.custom_live_interval_ms.setCurrentText("1000")
        self.capture_time_window_label = QLabel("capture window: --")
        self.capture_time_window_label.setWordWrap(True)
        for widget in (
            self.custom_base_addr_edit,
            self.custom_offset_v,
            self.custom_amp_v,
            self.custom_freq_hz,
            self.custom_step_counts,
            self.custom_limit_counts,
            self.custom_hold_v,
            self.custom_kp,
            self.custom_polarity,
            self.custom_lock_bias_v,
            self.custom_lock_limit_counts,
            self.custom_correction_limit_counts,
            self.custom_zero_threshold_counts,
            self.custom_capture_length,
            self.custom_capture_decimation,
            self.custom_capture_view_mode,
            self.custom_ref_debug_decimation,
            self.custom_live_interval_ms,
        ):
            self._style_field(widget)
        self.custom_offset_v.setToolTip("SCAN triangle center voltage estimate for OUT2/PZT.")
        self.custom_amp_v.setToolTip("SCAN triangle half amplitude in volts; OUT2 sweeps offset-v +/- amp-v.")
        self.custom_freq_hz.setToolTip("SCAN triangle frequency request.")
        self.custom_step_counts.setToolTip("Ramp generator step size in DAC counts per update tick.")
        self.custom_limit_counts.setToolTip("Absolute SCAN OUT2 limit in DAC counts.")
        self.custom_hold_v.setToolTip("HOLD output voltage estimate when using HOLD mode.")
        self.custom_kp.setToolTip("Manual P-only gain step; allowed values are 0, 4, 8, 16, 32.")
        self.custom_polarity.setToolTip("Feedback polarity. Change polarity only after APPLY P with Kp=0.")
        self.custom_correction_limit_counts.setToolTip("Maximum P correction amplitude around LOCK_BIAS, in counts.")
        self.custom_zero_threshold_counts.setToolTip("LOCK HERE waits until OUT2 is within this count window of the confirmed target.")
        self.custom_capture_length.setToolTip("Number of custom_debug_capture samples.")
        self.custom_capture_decimation.setToolTip("FPGA capture decimation; display-only scope timing, not physical gain.")
        self.captured_bias_label = QLabel("captured lock_bias: -- counts / -- V calibrated")
        self.captured_bias_label.setToolTip("LOCK_BIAS is captured by FPGA from OUT2_MONITOR at LOCK HERE.")
        self.captured_bias_label.setWordWrap(True)
        for widget in (self.basic_pzt_min_v, self.basic_pzt_max_v):
            self._style_field(widget)
        form.addRow("base address", self.custom_base_addr_edit)
        form.addRow("offset-v", self.custom_offset_v)
        form.addRow("amp-v", self.custom_amp_v)
        form.addRow("freq-hz", self.custom_freq_hz)
        form.addRow("step-counts", self.custom_step_counts)
        form.addRow("limit-counts", self.custom_limit_counts)
        form.addRow("hold-v", self.custom_hold_v)
        form.addRow("Kp manual step", self.custom_kp)
        form.addRow("Ki raw (disabled)", self.custom_ki)
        form.addRow("polarity", self.custom_polarity)
        form.addRow("manual lock-bias-v (not used by LOCK)", self.custom_lock_bias_v)
        form.addRow("lock-limit-counts", self.custom_lock_limit_counts)
        form.addRow("correction-limit-counts", self.custom_correction_limit_counts)
        form.addRow("target-window-counts", self.custom_zero_threshold_counts)
        form.addRow("capture view", self.custom_capture_view_mode)
        form.addRow("capture-length", self.custom_capture_length)
        form.addRow("capture-decimation", self.custom_capture_decimation)
        form.addRow("REF debug decimation", self.custom_ref_debug_decimation)
        form.addRow("refresh interval", self.custom_live_interval_ms)
        form.addRow(self.capture_time_window_label)
        form.addRow("captured bias", self.captured_bias_label)
        self.selected_lock_label = QLabel("selected lock point: click current scan waveform first")
        self.selected_lock_label.setToolTip(
            "ERROR_SETPOINT is captured by FPGA as ERROR_MONITOR at LOCK HERE; LOCK_ERROR is ERROR_MONITOR - ERROR_SETPOINT."
        )
        self.selected_lock_label.setWordWrap(True)
        form.addRow("selected point", self.selected_lock_label)

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(8)
        buttons.setVerticalSpacing(6)
        self.custom_probe_button = QPushButton("Probe Registers")
        self.custom_status_button = QPushButton("Status")
        self.custom_safe_button = QPushButton("SAFE")
        self.custom_scan_button = QPushButton("SCAN")
        self.custom_hold_button = QPushButton("HOLD")
        self.custom_p_lock_button = QPushButton("P_LOCK")
        self.custom_pi_lock_button = QPushButton("PI_LOCK")
        self.custom_capture_bias_button = QPushButton("Capture Bias")
        self.custom_lock_button = QPushButton("LOCK HERE")
        self.custom_apply_p_button = QPushButton("APPLY P")
        self.custom_arm_auto_lock_button = QPushButton("LOCK HERE")
        self.custom_abort_auto_lock_button = QPushButton("ABORT / SAFE")
        self.custom_unlock_button = QPushButton("UNLOCK / SAFE")
        self.custom_capture_waveform_button = QPushButton("Capture Waveform")
        self.custom_capture_once_button = QPushButton("Capture Once")
        self.custom_start_live_button = QPushButton("Start Live")
        self.custom_stop_live_button = QPushButton("Stop Live")
        self.custom_select_target_check = QCheckBox("Select Target Transition")
        self.custom_confirm_lock_point_button = QPushButton("Confirm Lock Point")
        for button in (
            self.custom_probe_button,
            self.custom_status_button,
            self.custom_safe_button,
            self.custom_scan_button,
            self.custom_hold_button,
            self.custom_p_lock_button,
            self.custom_pi_lock_button,
            self.custom_capture_bias_button,
            self.custom_lock_button,
            self.custom_apply_p_button,
            self.custom_arm_auto_lock_button,
            self.custom_abort_auto_lock_button,
            self.custom_unlock_button,
            self.custom_capture_waveform_button,
            self.custom_capture_once_button,
            self.custom_start_live_button,
            self.custom_stop_live_button,
            self.custom_confirm_lock_point_button,
        ):
            self._style_button(button)
        self.custom_select_target_check.setToolTip(
            "Click the CH1/PD plot near a target absorption feature; GUI resolves the nearby CH3/error zero crossing."
        )
        self.custom_p_lock_button.setVisible(False)
        self.custom_pi_lock_button.setVisible(False)
        self.custom_arm_auto_lock_button.setVisible(False)
        buttons.addWidget(self.custom_probe_button, 0, 0)
        buttons.addWidget(self.custom_status_button, 0, 1)
        buttons.addWidget(self.custom_safe_button, 1, 0)
        buttons.addWidget(self.custom_scan_button, 1, 1)
        buttons.addWidget(self.custom_hold_button, 2, 0)
        buttons.addWidget(self.custom_capture_bias_button, 2, 1)
        buttons.addWidget(self.custom_lock_button, 3, 0)
        buttons.addWidget(self.custom_apply_p_button, 3, 1)
        buttons.addWidget(self.custom_unlock_button, 4, 0)
        buttons.addWidget(self.custom_abort_auto_lock_button, 4, 1)
        buttons.addWidget(self.custom_capture_waveform_button, 5, 0, 1, 2)
        buttons.addWidget(self.custom_capture_once_button, 6, 0)
        buttons.addWidget(self.custom_start_live_button, 6, 1)
        buttons.addWidget(self.custom_stop_live_button, 7, 0)
        buttons.addWidget(self.custom_confirm_lock_point_button, 7, 1)
        buttons.addWidget(self.custom_select_target_check, 8, 0, 1, 2)

        self.custom_register_summary = QLabel(
            "MAGIC -- | VERSION -- | MODE -- | ENABLE -- | STATUS -- | OUT2 --"
        )
        self.custom_register_summary.setWordWrap(True)
        self.custom_register_summary.setStyleSheet("font-weight: 600;")
        self.custom_warning_text = QTextEdit()
        self.custom_warning_text.setReadOnly(True)
        self.custom_warning_text.setMinimumHeight(90)
        self.custom_warning_text.setPlainText(
            "First enter SCAN and capture the current waveform. Click the desired zero point, then press LOCK HERE. "
            "FPGA CAPTURE_LOCK_POINT latches ERROR_SETPOINT and LOCK_BIAS in the same clk_i domain, then enters "
            "MODE=3 P_LOCK with Kp=0/Ki=0. Use APPLY P for 0/4/8/16/32 manual gain steps without recapturing "
            "LOCK_BIAS or ERROR_SETPOINT. Change polarity only after APPLY P with Kp=0. Historical CSV values are not used as lock parameters."
        )

        advanced_body_layout.addLayout(form)
        advanced_body_layout.addLayout(buttons)
        advanced_layout.addWidget(self.custom_advanced_body)
        layout.addWidget(basic_group)
        layout.addWidget(advanced_group)
        layout.addWidget(self.custom_register_summary)
        layout.addWidget(self.custom_warning_text)
        return group

    def _custom_double_spin(
        self,
        value: float,
        minimum: float,
        maximum: float,
        decimals: int,
        suffix: str,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setSingleStep(0.01)
        spin.setValue(value)
        spin.setSuffix(suffix)
        return spin

    def _lock_workflow_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.lock_step_combo = QComboBox()
        self.lock_step_combo.addItems(
            [
                "1. Input Safety Check",
                "2. Error Signal Observe",
                "3. Control Output Observe",
                "4. Direction / Polarity Check",
                "5. Gain / Limit Check",
                "6. Ready for Low-gain Lock Test",
                "7. Future Lock Engage",
                "8. Future Relock",
            ]
        )
        self.lock_step_detail = QLabel("")
        self.lock_step_detail.setWordWrap(True)
        mapping = QLabel(
            "D2-125 Aux Servo Output -> disconnect; Custom FPGA OUT2 provides selected_out2 to laser dedicated PZT / Scan input\n"
            "D2-125 Error Input -> FPGA mixer + LPF -> laser_error\n"
            "D2-125 Servo Output -> do not parallel with Red Pitaya OUT2\n"
            "SCAN -> GUI writes custom_register_bank/ramp_generator for OUT2 triangle\n"
            "Click current waveform target -> LOCK HERE -> FPGA captures ERROR_SETPOINT and LOCK_BIAS, then enters MODE=3 P_LOCK"
        )
        mapping.setWordWrap(True)
        layout.addWidget(QLabel("Lock Workflow Step"))
        layout.addWidget(self.lock_step_combo)
        layout.addWidget(self.lock_step_detail)
        layout.addWidget(mapping)
        future = QLabel(
            "Current LOCK is P-only. Ki/PI and custom IN1/IN2 waveform capture remain disabled until RTL/debug buffer validation."
        )
        future.setWordWrap(True)
        future.setStyleSheet("color: #9a5b00; font-weight: 600;")
        layout.addWidget(future)
        layout.addStretch(1)
        return page

    def _data_log_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.experiment_log_notes = QTextEdit()
        self.experiment_log_notes.setMinimumHeight(110)
        self.experiment_log_notes.setPlaceholderText("Experiment notes, wiring, decisions, next steps")
        self.export_experiment_log_button = QPushButton("Export Experiment Log")
        self._style_button(self.export_experiment_log_button)
        self.experiment_log_status = QLabel("Exports Markdown to docs/experiment_logs/")
        self.experiment_log_status.setWordWrap(True)
        layout.addWidget(self.experiment_log_notes)
        layout.addWidget(self.export_experiment_log_button)
        layout.addWidget(self.experiment_log_status)
        layout.addStretch(1)
        return page

    def _measurement_spin(self, suffix: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-10.0, 10.0)
        spin.setDecimals(5)
        spin.setSingleStep(0.01)
        spin.setSuffix(suffix)
        self._style_field(spin)
        return spin

    def _output_group(self) -> QGroupBox:
        group = QGroupBox("Output Control")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 18, 10, 10)
        layout.setSpacing(8)
        boundary_note = QLabel(
            "SCPI Output Control is only for official ASG/overlay testing. "
            "For the current custom FPGA bitstream, use Custom FPGA Observe -> "
            "Custom FPGA Control -> SCAN."
        )
        boundary_note.setWordWrap(True)
        boundary_note.setStyleSheet("color: #9a5b00; font-weight: 600;")
        layout.addWidget(boundary_note)
        self.out1 = self._build_output_control("OUT1", 1, "sine", 1000.0)
        self.out2 = self._build_output_control("OUT2", 2, "triangle", 50.0)
        tabs = QTabWidget()
        tabs.addTab(self._output_control_group("OUT1", self.out1), "OUT1")
        tabs.addTab(self._output_control_group("OUT2", self.out2), "OUT2")
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        layout.addWidget(tabs)
        return group

    def _build_output_control(
        self,
        label: str,
        channel: int,
        waveform: str,
        frequency: float,
    ) -> OutputControl:
        del label, channel
        enable = QCheckBox("enable")
        waveform_combo = QComboBox()
        waveform_combo.addItems(["sine", "square", "triangle", "sawtooth"])
        waveform_combo.setCurrentText(waveform)
        self._style_field(waveform_combo)
        frequency_spin = QDoubleSpinBox()
        frequency_spin.setRange(0.001, 10_000_000.0)
        frequency_spin.setDecimals(3)
        frequency_spin.setValue(frequency)
        frequency_spin.setSuffix(" Hz")
        self._style_field(frequency_spin)
        amplitude_spin = QDoubleSpinBox()
        amplitude_spin.setRange(0.0, 1.0)
        amplitude_spin.setDecimals(4)
        amplitude_spin.setValue(0.05)
        amplitude_spin.setSuffix(" V")
        self._style_field(amplitude_spin)
        offset_spin = QDoubleSpinBox()
        offset_spin.setRange(-1.0, 1.0)
        offset_spin.setDecimals(4)
        offset_spin.setValue(0.0)
        offset_spin.setSuffix(" V")
        self._style_field(offset_spin)
        phase_spin = QDoubleSpinBox()
        phase_spin.setRange(-360.0, 360.0)
        phase_spin.setDecimals(2)
        phase_spin.setValue(0.0)
        phase_spin.setSuffix(" deg")
        self._style_field(phase_spin)
        apply_button = QPushButton("Apply")
        disable_button = QPushButton("Disable")
        self._style_button(apply_button)
        self._style_button(disable_button)
        return OutputControl(
            enable=enable,
            waveform=waveform_combo,
            frequency=frequency_spin,
            amplitude=amplitude_spin,
            offset=offset_spin,
            phase=phase_spin,
            apply_button=apply_button,
            disable_button=disable_button,
        )

    def _output_control_group(self, title: str, control: OutputControl) -> QGroupBox:
        group = QGroupBox(title)
        form = QFormLayout(group)
        self._configure_form(form)
        group.setMinimumHeight(280)
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(control.apply_button)
        buttons.addWidget(control.disable_button)
        form.addRow(control.enable)
        form.addRow("waveform", control.waveform)
        form.addRow("frequency_hz", control.frequency)
        form.addRow("amplitude_v", control.amplitude)
        form.addRow("offset_v", control.offset)
        form.addRow("phase_deg", control.phase)
        form.addRow(buttons)
        return group

    def _acquisition_group(self) -> QGroupBox:
        group = QGroupBox("Acquisition")
        form = QFormLayout(group)
        self._configure_form(form)
        self.decimation_combo = QComboBox()
        self.decimation_combo.addItems([str(value) for value in DECIMATIONS])
        self._style_field(self.decimation_combo)
        self.sample_rate_label = QLabel("")
        self.refresh_rate_label = QLabel("actual refresh_rate: -- Hz")
        self.start_acq_button = QPushButton("Start Acquisition")
        self.stop_acq_button = QPushButton("Stop Acquisition")
        self._style_button(self.start_acq_button)
        self._style_button(self.stop_acq_button)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.start_acq_button)
        row.addWidget(self.stop_acq_button)
        form.addRow("decimation", self.decimation_combo)
        form.addRow("sample_rate", self.sample_rate_label)
        form.addRow(self.refresh_rate_label)
        form.addRow(row)
        return group

    def _export_group(self) -> QGroupBox:
        group = QGroupBox("Data Export")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 18, 10, 10)
        layout.setSpacing(8)
        self.save_csv_button = QPushButton("Save CSV")
        self.save_png_button = QPushButton("Save PNG")
        self._style_button(self.save_csv_button)
        self._style_button(self.save_png_button)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Experiment notes")
        self.notes_edit.setMinimumHeight(80)
        self.notes_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        layout.addWidget(self.save_csv_button)
        layout.addWidget(self.save_png_button)
        layout.addWidget(self.notes_edit, stretch=1)
        return group

    def _build_plots(self) -> QWidget:
        panel = QWidget()
        self.plots_panel = panel
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.custom_scope_group = QWidget()
        scope_layout = QVBoxLayout(self.custom_scope_group)
        scope_layout.setContentsMargins(0, 0, 0, 0)
        scope_layout.setSpacing(6)

        # Stats summary at top (compact)
        self.custom_scope_stats = QLabel("custom_debug_capture not available")
        self.custom_scope_stats.setWordWrap(True)

        # Single pyqtgraph PlotWidget — 4 curves overlaid
        scope_axis_row = QHBoxLayout()
        scope_axis_row.addWidget(QLabel("Scope axis"))
        self.custom_scope_x_axis_combo = QComboBox()
        self.custom_scope_x_axis_combo.addItem("time (ms)")
        self.custom_scope_x_axis_combo.setToolTip("Display-only Lock View axis; raw capture indices and values remain unchanged.")
        self.custom_scope_x_axis_combo.currentTextChanged.connect(lambda _text: self._refresh_scope_display())
        scope_axis_row.addWidget(self.custom_scope_x_axis_combo)
        scope_axis_row.addStretch()
        self.hidden_scope_axis_controls = QWidget()
        self.hidden_scope_axis_controls.setLayout(scope_axis_row)
        self.hidden_scope_axis_controls.setVisible(False)

        self.custom_scope_plot = pg.PlotWidget()
        self.custom_scope_plot.setBackground("#05070a")
        self.custom_scope_plot.showGrid(x=True, y=True, alpha=0.25)
        self.custom_scope_plot.setLabel("bottom", "time", units="ms")
        self.custom_scope_plot.setLabel("left", "Channel position", units="div")
        self.custom_scope_plot.setMinimumHeight(300)
        self.custom_scope_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.custom_scope_plot.setMenuEnabled(False)
        self.custom_scope_plot.setMouseEnabled(x=True, y=True)

        # Axis theme (dark)
        axis_pen = pg.mkPen("#e6edf3", width=1.0)
        for axis_name in ("bottom", "left", "top", "right"):
            axis = self.custom_scope_plot.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen(axis_pen)
            axis.setTickPen(axis_pen)

        # 4 overlaid curves
        curve_colors = {
            "ch1": "#59c36a",
            "ch2": "#f2994a",
            "ch3": "#56b4e9",
            "ch4": "#f2c94c",
        }
        curve_labels = {
            "ch1": "CH1 IN1 / PD",
            "ch2": "CH2 IN2 / REF",
            "ch3": "CH3 OUT1 / laser_error",
            "ch4": "CH4 OUT2 / selected_out2",
        }
        self.custom_scope_curves = {}
        for key in ("ch1", "ch3", "ch4", "ch2"):
            color = curve_colors[key]
            curve = self.custom_scope_plot.plot(
                [], [], pen=pg.mkPen(color, width=1.4), name=curve_labels[key]
            )
            curve.setDownsampling(auto=True, method="peak")
            curve.setClipToView(True)
            self.custom_scope_curves[key] = curve

        # Placeholder text centered in view box
        self.custom_scope_placeholder = pg.TextItem(
            text="custom_debug_capture not available",
            color="#e6edf3", anchor=(0.5, 0.5),
        )
        self.custom_scope_plot.addItem(self.custom_scope_placeholder)

        # Target peak marker (purple dotted) and zero-crossing marker (yellow dashed)
        self.custom_target_marker = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen("#7f3fbf", width=1.1, style=Qt.PenStyle.DotLine),
        )
        self.custom_zero_marker = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen("#ffcc00", width=1.2, style=Qt.PenStyle.DashLine),
        )
        self.custom_target_marker.setVisible(False)
        self.custom_zero_marker.setVisible(False)
        self.custom_scope_plot.addItem(self.custom_target_marker)
        self.custom_scope_plot.addItem(self.custom_zero_marker)
        self.custom_target_window_region = pg.LinearRegionItem(
            values=(0.0, 0.0),
            orientation="vertical",
            movable=False,
            brush=pg.mkBrush(127, 63, 191, 45),
            pen=pg.mkPen("#7f3fbf", width=0.8, style=Qt.PenStyle.DotLine),
        )
        self.custom_target_window_region.setVisible(False)
        self.custom_target_window_region.setZValue(-10)
        self.custom_scope_plot.addItem(self.custom_target_window_region)
        self.custom_candidate_markers: list[pg.InfiniteLine] = []
        self.custom_ground_markers: dict[str, pg.InfiniteLine] = {}
        for key in ("ch4", "ch3", "ch1", "ch2"):
            _title, color, position = SCOPE_CHANNELS[key]
            marker = pg.InfiniteLine(
                pos=position,
                angle=0,
                movable=False,
                pen=pg.mkPen(color, width=0.8, style=Qt.PenStyle.DotLine),
            )
            marker.setVisible(key != "ch2")
            self.custom_scope_plot.addItem(marker)
            self.custom_ground_markers[key] = marker

        # Click handler for direct CH3/ERROR zero-crossing selection.
        self.custom_scope_plot.scene().sigMouseClicked.connect(self._on_custom_scope_clicked)

        scope_layout.addWidget(self.custom_scope_plot, stretch=1)

        # Operator display controls use physical volts/div and channel positions.
        self.custom_scope_curve_labels = curve_labels
        self.custom_scope_vertical_defaults = {
            key: metadata[2] for key, metadata in SCOPE_CHANNELS.items()
        }
        self.custom_scope_checks = {}
        self.custom_scope_volts_div_combos = {}
        self.custom_scope_position_spins = {}
        self.custom_scope_channel_auto_buttons = {}
        self.custom_scope_auto_scale_checks = {}
        self.custom_scope_scale_spins = {}
        self.custom_scope_vertical_spins = {}
        self.custom_scope_channel_reset_buttons = {}
        controls_grid = QGridLayout()
        controls_grid.setHorizontalSpacing(8)
        controls_grid.setVerticalSpacing(3)
        for column, label in enumerate(("Channel", "Visible", "Volts/Div", "Position", "")):
            controls_grid.addWidget(QLabel(label), 0, column)

        default_visible = {"ch1", "ch3", "ch4"}
        default_vdiv = {"ch4": 0.100, "ch3": 0.020, "ch1": 0.050, "ch2": 0.500}
        for row, key in enumerate(("ch4", "ch3", "ch1", "ch2"), start=1):
            title, color, default_position = SCOPE_CHANNELS[key]
            channel_label = QLabel(title)
            channel_label.setStyleSheet(f"color: {color}; font-weight: 600;")
            controls_grid.addWidget(channel_label, row, 0)
            visible = QCheckBox()
            visible.setChecked(key in default_visible)
            visible.setToolTip("Display only: does not change captured data or FPGA state.")
            volts_div = QComboBox()
            for value in SCOPE_VOLTS_PER_DIV:
                volts_div.addItem(format_volts_per_div(value), value)
            volts_div.setCurrentIndex(SCOPE_VOLTS_PER_DIV.index(default_vdiv[key]))
            volts_div.setToolTip("Display-only volts per division; FPGA counts and parameters are unchanged.")
            position = QDoubleSpinBox()
            position.setRange(-8.0, 8.0)
            position.setDecimals(1)
            position.setSingleStep(0.5)
            position.setSuffix(" div")
            position.setValue(default_position)
            position.setToolTip("Display-only ground position for this channel.")
            channel_auto = QPushButton("Channel Auto")
            channel_auto.setToolTip("Choose volts/div from this channel's current Vpp only.")
            self._style_button(channel_auto)

            controls_grid.addWidget(visible, row, 1)
            controls_grid.addWidget(volts_div, row, 2)
            controls_grid.addWidget(position, row, 3)
            controls_grid.addWidget(channel_auto, row, 4)
            self.custom_scope_checks[key] = visible
            self.custom_scope_volts_div_combos[key] = volts_div
            self.custom_scope_position_spins[key] = position
            self.custom_scope_channel_auto_buttons[key] = channel_auto

            visible.toggled.connect(self._update_custom_scope_visibility)
            volts_div.currentIndexChanged.connect(
                lambda _index, scope_key=key: self._on_scope_volts_div_changed(scope_key)
            )
            position.valueChanged.connect(
                lambda _value, scope_key=key: self._on_scope_position_changed(scope_key)
            )
            channel_auto.clicked.connect(
                lambda _checked=False, scope_key=key: self._auto_set_scope_channel(scope_key)
            )

        self.hidden_scope_channel_controls = QWidget()
        self.hidden_scope_channel_controls.setLayout(controls_grid)
        self.hidden_scope_channel_controls.setVisible(False)

        # Raw display gain controls remain available only in Engineer Details.
        self.custom_scope_raw_controls = QGroupBox("Raw Display Diagnostics")
        raw_grid = QGridLayout(self.custom_scope_raw_controls)
        for column, label in enumerate(("Channel", "Auto raw gain", "Raw gain", "Raw position", "")):
            raw_grid.addWidget(QLabel(label), 0, column)
        for row, key in enumerate(("ch4", "ch3", "ch1", "ch2"), start=1):
            raw_grid.addWidget(QLabel(curve_labels[key]), row, 0)
            auto_scale = QCheckBox()
            auto_scale.setChecked(True)
            auto_scale.setToolTip("Recalculate display center and gain from the current capture only.")
            scale = QDoubleSpinBox()
            scale.setRange(0.000001, 1_000_000.0)
            scale.setDecimals(6)
            scale.setValue(1.0)
            scale.setToolTip("Display gain only: does not change captured counts or physical gain.")
            vertical = QDoubleSpinBox()
            vertical.setRange(-20.0, 20.0)
            vertical.setDecimals(2)
            vertical.setSingleStep(0.5)
            vertical.setValue(self.custom_scope_vertical_defaults[key])
            vertical.setToolTip("Display-only vertical position. Markers and click time stay on raw capture indices.")
            reset = QPushButton("Reset display")
            reset.setToolTip("Restore this channel's automatic display center, gain, and default vertical position.")
            self._style_button(reset)
            raw_grid.addWidget(auto_scale, row, 1)
            raw_grid.addWidget(scale, row, 2)
            raw_grid.addWidget(vertical, row, 3)
            raw_grid.addWidget(reset, row, 4)
            self.custom_scope_auto_scale_checks[key] = auto_scale
            self.custom_scope_scale_spins[key] = scale
            self.custom_scope_vertical_spins[key] = vertical
            self.custom_scope_channel_reset_buttons[key] = reset
            auto_scale.toggled.connect(lambda _checked, scope_key=key: self._refresh_scope_display(scope_key))
            scale.valueChanged.connect(lambda _value, scope_key=key: self._refresh_scope_display(scope_key))
            vertical.valueChanged.connect(lambda _value, scope_key=key: self._on_raw_scope_position_changed(scope_key))
            reset.clicked.connect(lambda _checked=False, scope_key=key: self._reset_scope_channel_display(scope_key))

        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)
        self.custom_scope_default_button = QPushButton("Scope Default")
        self.custom_scope_default_button.setToolTip("Restore CH4 top, CH3 middle, CH1 bottom, and hide CH2.")
        self.custom_scope_default_button.clicked.connect(self._apply_scope_default_layout)
        self._style_button(self.custom_scope_default_button)
        controls_row.addWidget(self.custom_scope_default_button)
        self.custom_scope_auto_range_check = QCheckBox("View Auto Range")
        self.custom_scope_auto_range_check.setChecked(True)
        self.custom_scope_auto_range_check.toggled.connect(self._update_custom_scope_visibility)
        controls_row.addWidget(self.custom_scope_auto_range_check)
        self.custom_scope_reset_button = QPushButton("Reset View")
        self.custom_scope_reset_button.clicked.connect(self._reset_custom_scope_view)
        self._style_button(self.custom_scope_reset_button)
        controls_row.addWidget(self.custom_scope_reset_button)
        controls_row.addStretch()
        raw_grid.addLayout(controls_row, 5, 0, 1, 5)
        layout.addWidget(self.custom_scope_group, stretch=1)
        return panel

    def _connect_signals(self) -> None:
        self.probe_button.clicked.connect(self.probe_connection)
        self.start_scpi_button.clicked.connect(self.start_scpi_server)
        self.connect_scpi_button.clicked.connect(self.connect_scpi)
        self.disconnect_button.clicked.connect(self.disconnect_from_device)
        self.system_identity_refresh_button.clicked.connect(self._refresh_system_identity)
        self.host_edit.textChanged.connect(lambda _text: self._update_system_identity_host())
        self.resolved_ip_combo.currentTextChanged.connect(
            lambda _text: self._update_system_identity_host()
        )
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.app_mode_tabs.currentChanged.connect(self._on_app_mode_tab_changed)
        self.custom_probe_button.clicked.connect(lambda: self._start_custom_fpga_operation("probe"))
        self.custom_status_button.clicked.connect(lambda: self._start_custom_fpga_operation("status"))
        self.custom_safe_button.clicked.connect(lambda: self._start_custom_fpga_operation("safe"))
        self.scan_stop_safe_button.clicked.connect(lambda: self._start_custom_fpga_operation("safe"))
        self.custom_scan_button.clicked.connect(lambda: self._start_custom_fpga_operation("scan"))
        self.custom_hold_button.clicked.connect(lambda: self._start_custom_fpga_operation("hold"))
        self.custom_p_lock_button.clicked.connect(lambda: self._start_custom_fpga_operation("p-lock"))
        self.custom_pi_lock_button.clicked.connect(lambda: self._start_custom_fpga_operation("pi-lock"))
        self.custom_capture_bias_button.clicked.connect(lambda: self._start_custom_fpga_operation("capture-bias"))
        self.custom_lock_button.clicked.connect(lambda: self._start_custom_fpga_operation("lock"))
        self.custom_apply_p_button.clicked.connect(lambda: self._start_custom_fpga_operation("update-p-lock"))
        self.custom_abort_auto_lock_button.clicked.connect(lambda: self._start_custom_fpga_operation("safe"))
        self.custom_unlock_button.clicked.connect(lambda: self._start_custom_fpga_operation("safe"))
        self.custom_capture_waveform_button.clicked.connect(lambda: self._start_custom_fpga_operation("capture"))
        self.custom_capture_once_button.clicked.connect(self._capture_once)
        self.custom_start_live_button.clicked.connect(self._start_live_capture)
        self.custom_stop_live_button.clicked.connect(self._stop_live_capture)
        self.custom_confirm_lock_point_button.clicked.connect(self._confirm_pending_lock_point)
        self.custom_pick_lock_button.toggled.connect(self._set_lock_point_selection_active)
        self.custom_select_target_check.toggled.connect(self._sync_legacy_lock_point_selector)
        self.custom_polarity.currentIndexChanged.connect(self._on_polarity_selection_changed)
        self.custom_capture_view_mode.currentTextChanged.connect(self._apply_capture_view_mode)
        self.custom_ref_debug_decimation.currentTextChanged.connect(self._apply_capture_view_mode)
        self.basic_lock_button.clicked.connect(self._start_basic_lock)
        self.basic_safe_button.clicked.connect(lambda: self._start_custom_fpga_operation("safe"))
        self.obs_analyze_button.clicked.connect(self._analyze_observe_readings)
        self.lock_step_combo.currentTextChanged.connect(self._update_lock_step_detail)
        self.export_experiment_log_button.clicked.connect(self.export_experiment_log)
        if self._scpi_controls_available():
            self.out1.apply_button.clicked.connect(lambda: self.apply_output(1, self.out1))
            self.out2.apply_button.clicked.connect(lambda: self.apply_output(2, self.out2))
            self.out1.disable_button.clicked.connect(lambda: self.disable_output(1, self.out1))
            self.out2.disable_button.clicked.connect(lambda: self.disable_output(2, self.out2))
            for control in (self.out1, self.out2):
                control.waveform.currentTextChanged.connect(self._redraw_from_last_waveforms)
                control.frequency.valueChanged.connect(self._redraw_from_last_waveforms)
                control.amplitude.valueChanged.connect(self._redraw_from_last_waveforms)
                control.offset.valueChanged.connect(self._redraw_from_last_waveforms)
                control.phase.valueChanged.connect(self._redraw_from_last_waveforms)
                control.amplitude.valueChanged.connect(lambda _=0, c=control: self._update_offset_range(c))
        if hasattr(self, "start_acq_button"):
            self.start_acq_button.clicked.connect(self.start_acquisition)
            self.stop_acq_button.clicked.connect(self.stop_acquisition)
            self.decimation_combo.currentTextChanged.connect(self._update_sample_rate_label)
        if hasattr(self, "save_csv_button"):
            self.save_csv_button.clicked.connect(self.save_csv)
            self.save_png_button.clicked.connect(self.save_png)
        self._update_lock_step_detail()

    def _set_lock_point_selection_active(self, active: bool) -> None:
        if self.custom_select_target_check.isChecked() != bool(active):
            self.custom_select_target_check.setChecked(bool(active))
        if active:
            self.operator_state_label.setText("SELECTING LOCK POINT")
            self.operator_candidate_label.setText("Click the desired ERROR zero crossing")
        elif self.selected_lock_point is None and self.pending_lock_point is None:
            self.operator_state_label.setText("CAPTURE READY" if self.custom_scope_data is not None else "SAFE")

    def _sync_legacy_lock_point_selector(self, active: bool) -> None:
        if self.custom_pick_lock_button.isChecked() != bool(active):
            self.custom_pick_lock_button.setChecked(bool(active))

    def _polarity_inverted(self) -> bool:
        value = self.custom_polarity.currentData()
        if value is None:
            value = self.custom_polarity.currentText().lower()
        return str(value).lower() == "invert"

    def _on_polarity_selection_changed(self, index: int) -> None:
        if self.applied_kp != 0:
            self.custom_polarity.blockSignals(True)
            self.custom_polarity.setCurrentIndex(self.applied_polarity_index)
            self.custom_polarity.blockSignals(False)
            message = "Return APPLY P to Kp=0 before changing polarity"
            self.operator_alert_label.setText(message)
            self.custom_warning_text.setPlainText(message)
            return
        self.applied_polarity_index = int(index)

    def _load_defaults(self) -> None:
        rp = self.config.get("red_pitaya", {})
        self.host_edit.setText(str(rp.get("host", "rp-f0cb13.local")))
        self.mock_check.setChecked(bool(self.start_mock))
        if hasattr(self, "decimation_combo"):
            self.decimation_combo.setCurrentText(str(self.config.get("acquisition", {}).get("decimation", 1024)))
        self.resolved_ip_combo.addItem(str(rp.get("host", "rp-f0cb13.local")))
        if self._scpi_controls_available():
            self._update_offset_range(self.out1)
            self._update_offset_range(self.out2)
        self._apply_capture_view_mode()
        self._on_mode_changed()

    def probe_connection(self) -> None:
        host = self.host_edit.text().strip() or "rp-f0cb13.local"
        self._set_connection_state(PROBING)
        self._append_connection_log(f"Probing {host}...")
        print(f"Probing {host}...")
        worker = ProbeWorker(host, self)
        self.worker = worker
        worker.finished_ok.connect(self._on_probe_finished)
        worker.failed.connect(self._on_probe_failed)
        worker.finished.connect(self._clear_worker)
        worker.start()

    def start_scpi_server(self) -> None:
        if not self._official_mode():
            self.statusBar().showMessage("Start SCPI Server is disabled in Custom FPGA Mode")
            return
        if self.last_probe is not None and self.last_probe.port_5000:
            message = "SCPI port 5000 is already available. Please click Connect SCPI."
            self.statusBar().showMessage(message)
            self._append_connection_log(message)
            print(message)
            self._set_connection_state(SCPI_READY)
            return
        if self.last_probe is None or not self.last_probe.port_22:
            message = "Start SCPI Server requires SSH True and SCPI False. Run Probe first."
            self.statusBar().showMessage(message)
            self._append_connection_log(message)
            print(message)
            return
        target = self._target_host()
        self._set_connection_state(SCPI_STARTING)
        self._append_connection_log("Starting redpitaya_scpi over SSH...")
        print("Starting redpitaya_scpi over SSH...")
        worker = StartScpiServerWorker(
            target,
            self.ssh_user_edit.text().strip() or "root",
            self.ssh_password_edit.text(),
            self,
        )
        self.worker = worker
        worker.finished_ok.connect(self._on_start_scpi_finished)
        worker.failed.connect(self._on_start_scpi_failed)
        worker.finished.connect(self._clear_worker)
        worker.start()

    def connect_scpi(self) -> None:
        if not self._official_mode() and not self.mock_check.isChecked():
            self.statusBar().showMessage("Connect SCPI is for Official SCPI Mode only")
            return
        if self.mock_check.isChecked():
            self.client = MockRedPitayaClient()
            idn = self.client.connect()
            self._set_connection_state(SCPI_CONNECTED)
            self.statusBar().showMessage(f"Connected mock: {idn}")
            return
        target = self._target_host()
        port = int(self.config.get("red_pitaya", {}).get("scpi_port", 5000))
        timeout_s = float(self.config.get("red_pitaya", {}).get("timeout_s", 3.0))
        self._append_connection_log(f"Connecting SCPI {target}:{port}...")
        print(f"Connecting SCPI {target}:{port}...")
        self._set_connection_state(PROBING)
        worker = ConnectScpiWorker(target, port, timeout_s, self)
        self.worker = worker
        worker.finished_ok.connect(self._on_connect_scpi_finished)
        worker.failed.connect(self._on_connect_scpi_failed)
        worker.finished.connect(self._clear_worker)
        worker.start()

    def disconnect_from_device(self) -> None:
        self.stop_acquisition(wait=False)
        if self.client is None:
            self._set_connection_state(DISCONNECTED)
            return
        client = self.client
        self.client = None
        self._unregister_safe_shutdown()
        self._append_connection_log("Disconnecting and running safe shutdown...")
        print("Disconnecting and running safe shutdown...")
        self._set_connection_state(PROBING)
        worker = DisconnectWorker(client, self)
        self.worker = worker
        worker.finished_ok.connect(self._on_disconnect_finished)
        worker.failed.connect(self._on_disconnect_failed)
        worker.finished.connect(self._clear_worker)
        worker.start()

    def _startup_custom_register_probe(self) -> None:
        if self.worker is not None or self.mock_check.isChecked():
            return
        self.custom_register_summary.setText(
            "startup probe running | MAGIC reading | VERSION reading | MODE reading | "
            "ENABLE reading | STATUS reading | OUT2 reading"
        )
        self.custom_warning_text.setPlainText(
            "Startup probe: reading Custom FPGA registers over SSH + /dev/mem. "
            "This only reads status; it does not start redpitaya_scpi and does not write FPGA registers."
        )
        self._start_custom_fpga_operation("status", preserve_basic=True)

    def _capture_once(self) -> None:
        self._stop_live_capture("Capture Once requested")
        self._start_custom_fpga_operation("capture")

    def _start_live_capture(self) -> None:
        self.live_capture_active = True
        self._apply_capture_view_mode()
        self.statusBar().showMessage("Live capture started")
        self._run_live_capture_cycle()

    def _stop_live_capture(self, reason: str = "Live capture stopped") -> None:
        self.live_capture_active = False
        if hasattr(self, "custom_live_timer"):
            self.custom_live_timer.stop()
        self.statusBar().showMessage(reason)

    def _run_live_capture_cycle(self) -> None:
        if not self.live_capture_active:
            return
        if self.capture_in_flight or self.current_custom_operation is not None:
            return
        self._start_custom_fpga_operation("capture", preserve_basic=True)

    def _schedule_next_live_capture(self) -> None:
        if not self.live_capture_active or self.capture_in_flight:
            return
        interval_ms = int(self.custom_live_interval_ms.currentText())
        self.custom_live_timer.start(interval_ms)

    def _capture_decimation_for_view(self) -> int:
        if self.custom_capture_view_mode.currentText() == "REF Debug":
            return int(self.custom_ref_debug_decimation.currentText())
        length = max(1, int(self.custom_capture_length.value()))
        freq_hz = max(0.001, float(self.custom_freq_hz.value()))
        return max(1, int(round(125_000_000.0 / (freq_hz * length))))

    def _update_capture_time_window_label(self) -> None:
        length = int(self.custom_capture_length.value())
        decimation = int(self.custom_capture_decimation.value())
        window_s = length * decimation / 125_000_000.0
        if self.custom_capture_view_mode.currentText() == "REF Debug":
            self.capture_time_window_label.setText(
                f"capture window: {window_s:.6g} s | REF Debug is for 4.6 MHz REF; "
                "it cannot also show a full 10 Hz scan period."
            )
        else:
            scan_period = 1.0 / max(0.001, float(self.custom_freq_hz.value()))
            self.capture_time_window_label.setText(
                f"capture window: {window_s:.6g} s | scan period approx {scan_period:.6g} s"
            )

    def _apply_capture_view_mode(self) -> None:
        mode = self.custom_capture_view_mode.currentText()
        self.custom_capture_length.setValue(2048)
        self.custom_capture_decimation.setValue(self._capture_decimation_for_view())
        if hasattr(self, "custom_scope_checks"):
            if mode == "REF Debug":
                visible = {"ch2"}
            else:
                visible = {"ch1", "ch3", "ch4"}
            for key, checkbox in self.custom_scope_checks.items():
                checkbox.setChecked(key in visible)
        self._update_capture_time_window_label()

    def _start_custom_fpga_operation(self, operation: str, *, preserve_basic: bool = False) -> None:
        if operation == "capture" and self.capture_in_flight:
            self.statusBar().showMessage("Capture already in flight; skipped")
            return
        if operation == "safe" and not preserve_basic:
            self._stop_live_capture("SAFE requested; Live stopped")
        if operation == "safe" and not preserve_basic:
            self.basic_lock_active = False
            self.basic_lock_queue = []
            self.p_lock_ready = False
            self.applied_kp = 0
            self.operator_state_label.setText("SAFE")
            self.operator_scan_state_label.setText("SAFE")
            self.operator_alert_label.setText("")
        if operation == "scan":
            self.operator_state_label.setText("SCANNING")
            self.operator_scan_state_label.setText("SCANNING")
        if self._official_mode():
            self.mode_combo.setCurrentText("Custom FPGA Mode")
        try:
            base_addr = int(self.custom_base_addr_edit.text().strip(), 0)
        except ValueError:
            self.statusBar().showMessage("Invalid Custom FPGA base address")
            return
        params = {}
        if operation == "scan":
            safe_min_v = float(self.basic_pzt_min_v.value())
            safe_max_v = float(self.basic_pzt_max_v.value())
            scan_center_v = float(self.custom_offset_v.value())
            scan_amplitude_v = float(self.custom_amp_v.value())
            scan_min_v = scan_center_v - scan_amplitude_v
            scan_max_v = scan_center_v + scan_amplitude_v
            if safe_min_v >= safe_max_v or scan_min_v < safe_min_v - 1e-9 or scan_max_v > safe_max_v + 1e-9:
                message = (
                    f"Scan range {format_scope_voltage(scan_min_v, signed=True)} to "
                    f"{format_scope_voltage(scan_max_v, signed=True)} is outside PZT safe range "
                    f"{format_scope_voltage(safe_min_v, signed=True)} to "
                    f"{format_scope_voltage(safe_max_v, signed=True)}"
                )
                self.operator_state_label.setText("SAFE")
                self.operator_scan_state_label.setText("SAFE")
                self.operator_alert_label.setText(message)
                self.custom_warning_text.setPlainText(message)
                self.statusBar().showMessage(message)
                return
            safe_limit_counts = min(
                8191,
                max(abs(out2_voltage_to_counts(safe_min_v)), abs(out2_voltage_to_counts(safe_max_v))),
            )
            params = {
                "offset_v": scan_center_v,
                "amp_v": scan_amplitude_v,
                "freq_hz": self.custom_freq_hz.value(),
                "step_counts": self.custom_step_counts.value(),
                "limit_counts": safe_limit_counts,
            }
        elif operation == "hold":
            params = {
                "hold_v": self.custom_hold_v.value(),
            }
        elif operation in {"p-lock", "pi-lock"}:
            params = {
                "kp": int(self.custom_kp.currentText()),
                "ki": self.custom_ki.value(),
                "polarity": 1 if self._polarity_inverted() else 0,
                "lock_bias_v": self.custom_lock_bias_v.value(),
                "lock_limit_counts": self.custom_lock_limit_counts.value(),
                "correction_limit_counts": self.custom_correction_limit_counts.value(),
            }
        elif operation == "update-p-lock":
            if int(self.custom_kp.currentText()) != 0 and not self.p_lock_ready:
                message = "APPLY P requires a successful LOCK HERE at Kp=0"
                self.operator_alert_label.setText(message)
                self.custom_warning_text.setPlainText(message)
                self.statusBar().showMessage(message)
                return
            params = {
                "kp": int(self.custom_kp.currentText()),
                "polarity": 1 if self._polarity_inverted() else 0,
            }
        elif operation == "lock":
            if self.selected_lock_point is None:
                self.custom_warning_text.setPlainText(
                    "LOCK HERE requires a target selected from the current scan waveform. "
                    "Run SCAN, Capture Waveform, click the desired zero point, then press LOCK HERE."
                )
                self.operator_alert_label.setText("Lock point not confirmed")
                self.statusBar().showMessage("LOCK HERE blocked: no waveform point selected")
                return
            if int(self.custom_kp.currentText()) != 0:
                message = "LOCK HERE requires Kp=0"
                self.operator_alert_label.setText(message)
                self.custom_warning_text.setPlainText(message)
                self.statusBar().showMessage(message)
                return
            params = {
                "polarity": 1 if self._polarity_inverted() else 0,
                "lock_limit_counts": self.custom_lock_limit_counts.value(),
                "correction_limit_counts": self.custom_correction_limit_counts.value(),
                "settle_s": 0.5,
                "target_out2_counts": int(self.selected_lock_point["out2_counts"]),
                "target_window_counts": self.custom_zero_threshold_counts.value(),
                "target_timeout_s": 5.0,
            }
        elif operation == "capture":
            self._update_capture_time_window_label()
            params = {
                "capture_length": self.custom_capture_length.value(),
                "capture_decimation": self.custom_capture_decimation.value(),
            }
        target = self._target_host()
        user = self.ssh_user_edit.text().strip() or "root"
        password = self.ssh_password_edit.text()
        message = f"Custom FPGA {operation}: SSH /dev/mem on {target}, base=0x{base_addr:08X}"
        operator_message = {
            "safe": "SAFE requested",
            "scan": "PZT scan requested",
            "capture": "Capture requested",
            "lock": "LOCK HERE requested",
            "update-p-lock": "P gain update requested",
        }.get(operation, f"{operation} requested")
        self.current_custom_operation = operation
        if operation == "capture":
            self.capture_in_flight = True
        self.statusBar().showMessage(operator_message)
        self._append_connection_log(message)
        self.custom_warning_text.setPlainText(message)
        self._set_connection_state(CUSTOM_FPGA_BUSY)
        if self.start_mock:
            self._restore_after_custom_fpga_operation()
            return
        worker = CustomFpgaRegisterWorker(
            operation,
            target,
            user,
            password,
            base_addr,
            params,
            self,
        )
        self.worker = worker
        worker.finished_ok.connect(self._on_custom_fpga_finished)
        worker.failed.connect(self._on_custom_fpga_failed)
        worker.finished.connect(self._clear_worker)
        worker.start()

    def _start_basic_lock(self) -> None:
        try:
            config = build_basic_lock_config(
                safe_min_v=self.basic_pzt_min_v.value(),
                safe_max_v=self.basic_pzt_max_v.value(),
            )
        except CustomFpgaBackendError as exc:
            self.basic_status_label.setText(f"state: SAFE_FAIL | {exc}")
            self.custom_warning_text.setPlainText(str(exc))
            self._start_custom_fpga_operation("safe")
            return

        self.basic_lock_config = config
        self.basic_lock_candidates = []
        self.selected_lock_point = None
        self.custom_scope_valid_for_selection = False
        self._apply_basic_lock_config(config)
        self.basic_lock_active = True
        self.basic_lock_queue = ["safe", "scan", "capture"]
        self.basic_status_label.setText(
            "state: SAFE -> SCAN -> CAPTURE | "
            f"offset {config.offset_v:.4f} V, amp {config.amp_v:.4f} V, "
            f"freq {config.freq_hz:.1f} Hz, decimation {config.capture_decimation}"
        )
        self.basic_candidate_label.setText("candidate: waiting for current capture")
        self._continue_basic_lock()

    def _apply_basic_lock_config(self, config: BasicLockConfig) -> None:
        self.custom_offset_v.setValue(config.offset_v)
        self.custom_amp_v.setValue(config.amp_v)
        self.custom_freq_hz.setValue(config.freq_hz)
        self.custom_step_counts.setValue(config.step_counts)
        self.custom_capture_length.setValue(config.capture_length)
        self.custom_capture_decimation.setValue(config.capture_decimation)
        self.custom_limit_counts.setValue(config.limit_counts)
        self.custom_lock_limit_counts.setValue(config.limit_counts)
        self.custom_kp.setCurrentText("0")

    def _continue_basic_lock(self) -> None:
        if not self.basic_lock_active or not self.basic_lock_queue:
            return
        next_operation = self.basic_lock_queue.pop(0)
        state_labels = {
            "safe": "SAFE",
            "scan": "SCAN",
            "capture": "CAPTURE_WAVEFORM",
            "lock": "CAPTURE_LOCK_POINT",
            "update-p-lock": "P_LOCK",
        }
        self.basic_status_label.setText(f"state: {state_labels.get(next_operation, next_operation.upper())}")
        self._start_custom_fpga_operation(next_operation, preserve_basic=True)

    def _basic_lock_fail(self, reason: str) -> None:
        self.basic_lock_active = False
        self.basic_lock_queue = []
        self.basic_status_label.setText(f"state: SAFE_FAIL | {reason}")
        self.basic_candidate_label.setText("candidate: rejected")
        self.custom_warning_text.setPlainText(reason)
        QTimer.singleShot(0, lambda: self._start_custom_fpga_operation("safe"))

    def _confirm_basic_lock_candidate(self) -> None:
        if self.pending_lock_point is None:
            self._basic_lock_fail("BASIC LOCK found no valid zero-crossing candidate")
            return
        if self.start_mock:
            self._confirm_pending_lock_point()
            self.custom_kp.setCurrentText("0")
            self.basic_lock_queue = ["lock"]
            self._continue_basic_lock()
            return
        reply = QMessageBox.question(
            self,
            "Confirm BASIC LOCK candidate",
            "Use the highlighted zero-crossing candidate for LOCK HERE with Kp=0? "
            "After P_LOCK is stable, use APPLY P manually for Kp=4/8/16/32.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            self.basic_lock_active = False
            self.basic_lock_queue = []
            self.basic_status_label.setText("state: candidate ready, waiting for user")
            return
        self._confirm_pending_lock_point()
        self.custom_kp.setCurrentText("0")
        self.basic_lock_queue = ["lock"]
        self._continue_basic_lock()

    def _continue_basic_lock_after_success(self, operation: str, payload: dict[str, Any]) -> None:
        del payload
        if not self.basic_lock_active:
            return
        if operation == "capture":
            if self.basic_lock_candidates:
                self.basic_lock_active = False
                self.basic_lock_queue = []
                self.basic_status_label.setText(
                    "state: CANDIDATE_FOUND | click CH1 and Confirm Lock Point"
                )
            else:
                self._basic_lock_fail("BASIC LOCK failed: no valid zero-crossing candidate in current capture")
            return
        if operation == "lock":
            self.basic_lock_active = False
            self.basic_lock_queue = []
            self.custom_kp.setCurrentText("0")
            self.basic_status_label.setText(
                "state: P_LOCK | LOCK HERE captured with Kp=0; use APPLY P manually"
            )
            return
        if operation == "update-p-lock":
            self.basic_lock_active = False
            self.basic_lock_queue = []
            self.basic_status_label.setText("state: BASIC LOCK ACTIVE | monitor LOCK_ERROR / OUT2 / saturation")
            return
        QTimer.singleShot(0, self._continue_basic_lock)

    def _show_custom_waveform_capture_plan(self) -> None:
        lines = [
            "custom_debug_capture not available unless the new RTL is synthesized, implemented, bitstreamed, and loaded.",
            "Do not treat the scope plot as real FPGA waveforms until Capture Waveform returns data.",
            "",
            "Capture registers:",
            "CAPTURE_CTRL, CAPTURE_STATUS, CAPTURE_DECIMATION, CAPTURE_LENGTH, CAPTURE_READ_INDEX,",
            "CAPTURE_DATA_CH1, CAPTURE_DATA_CH2, CAPTURE_DATA_CH3, CAPTURE_DATA_CH4.",
            "",
            "CH1=IN1/PD, CH2=IN2/REF, CH3=OUT1/laser_error, CH4=OUT2/selected_out2.",
            "Custom FPGA Scope uses display-only layered traces; raw capture counts remain unchanged.",
            "4.6 MHz REF (CH2) may alias when decimation is high; it is hidden by default.",
        ]
        self.custom_warning_text.setPlainText("\n".join(lines))
        self.custom_scope_stats.setText("custom_debug_capture not available")
        self.statusBar().showMessage("Custom FPGA waveform capture requires the new debug_capture bitstream")

    def _scope_x_values(self) -> np.ndarray:
        if self.custom_scope_data is None:
            return np.asarray([], dtype=float)
        if self.custom_scope_x_axis_combo.currentText() == "time (ms)":
            return np.asarray(self.custom_scope_data.get("time_s", []), dtype=float) * 1000.0
        return np.asarray(self.custom_scope_data.get("ch4", []), dtype=float)

    def _scope_x_value(self, index: int) -> float:
        values = self._scope_x_values()
        if values.size == 0:
            return 0.0
        return float(values[int(np.clip(index, 0, values.size - 1))])

    def _set_scope_x_axis_label(self) -> None:
        if self.custom_scope_x_axis_combo.currentText() == "time (ms)":
            self.custom_scope_plot.setLabel("bottom", "time", units="ms")
        else:
            self.custom_scope_plot.setLabel("bottom", "OUT2", units="counts")

    def _update_lock_point_markers(self, lock_point: dict[str, int | float | str] | None) -> None:
        if lock_point is None:
            self.custom_target_marker.setVisible(False)
            self.custom_zero_marker.setVisible(False)
            self.custom_target_window_region.setVisible(False)
            return
        target_index = int(lock_point.get("selected_peak_index", lock_point.get("clicked_index", 0)))
        zero_index = int(lock_point.get("zero_crossing_index", lock_point.get("index", target_index)))
        target_x = self._scope_x_value(target_index)
        zero_x = self._scope_x_value(zero_index)
        window_counts = float(lock_point.get("target_window_counts", self.custom_zero_threshold_counts.value()))
        window_half_width = abs(window_counts)
        region_visible = True
        if self.custom_scope_x_axis_combo.currentText() == "time (ms)" and self.custom_scope_data is not None:
            time_ms = np.asarray(self.custom_scope_data.get("time_s", []), dtype=float) * 1000.0
            out2 = np.asarray(self.custom_scope_data.get("ch4", []), dtype=float)
            sample_count = min(time_ms.size, out2.size)
            if sample_count >= 2:
                i0 = int(np.clip(target_index - 1, 0, sample_count - 1))
                i1 = int(np.clip(target_index + 1, 0, sample_count - 1))
                delta_time_ms = float(time_ms[i1] - time_ms[i0])
                delta_counts = float(out2[i1] - out2[i0])
                if i1 > i0 and np.isfinite(delta_time_ms) and abs(delta_time_ms) > 1e-12:
                    local_counts_per_ms = delta_counts / delta_time_ms
                    if np.isfinite(local_counts_per_ms) and abs(local_counts_per_ms) > 1e-12:
                        window_half_width = abs(window_counts / local_counts_per_ms)
                    else:
                        region_visible = False
                else:
                    region_visible = False
            else:
                region_visible = False
        self.custom_target_marker.setValue(target_x)
        self.custom_target_marker.setVisible(True)
        self.custom_zero_marker.setValue(zero_x)
        self.custom_zero_marker.setVisible(True)
        if region_visible:
            self.custom_target_window_region.setRegion(
                (target_x - window_half_width, target_x + window_half_width)
            )
        self.custom_target_window_region.setVisible(region_visible)

    def _update_candidate_marker_positions(self) -> None:
        for marker, candidate in zip(self.custom_candidate_markers, self.basic_lock_candidates):
            try:
                marker.setValue(self._scope_x_value(candidate.index))
            except (RuntimeError, ValueError):
                pass

    def _scope_volts_per_div(self, key: str) -> float:
        combo = self.custom_scope_volts_div_combos[key]
        value = combo.currentData()
        return float(value if value is not None else 0.1)

    def _on_scope_volts_div_changed(self, key: str) -> None:
        if self._updating_scope_display_controls:
            return
        gain = 1.0 / (COUNTS_PER_VOLT * self._scope_volts_per_div(key))
        self._updating_scope_display_controls = True
        try:
            self.custom_scope_auto_scale_checks[key].setChecked(True)
            self.custom_scope_scale_spins[key].setValue(gain)
        finally:
            self._updating_scope_display_controls = False
        self._refresh_scope_display(key)

    def _on_scope_position_changed(self, key: str) -> None:
        if self._updating_scope_display_controls:
            return
        self._updating_scope_display_controls = True
        try:
            self.custom_scope_vertical_spins[key].setValue(
                self.custom_scope_position_spins[key].value()
            )
        finally:
            self._updating_scope_display_controls = False
        self.custom_ground_markers[key].setValue(
            self.custom_scope_position_spins[key].value()
        )
        self._refresh_scope_display(key)

    def _on_raw_scope_position_changed(self, key: str) -> None:
        if self._updating_scope_display_controls:
            return
        self._updating_scope_display_controls = True
        try:
            self.custom_scope_position_spins[key].setValue(
                self.custom_scope_vertical_spins[key].value()
            )
        finally:
            self._updating_scope_display_controls = False
        self._refresh_scope_display(key)

    def _auto_set_scope_channel(self, key: str) -> None:
        if self.custom_scope_data is None:
            return
        values = np.asarray(self.custom_scope_data.get(key, []), dtype=float)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return
        vpp_counts = float(np.nanmax(finite) - np.nanmin(finite))
        vpp_volts = (
            out2_delta_counts_to_voltage(vpp_counts)
            if key == "ch4"
            else vpp_counts / COUNTS_PER_VOLT
        )
        chosen = choose_scope_volts_per_div(vpp_volts)
        combo = self.custom_scope_volts_div_combos[key]
        index = combo.findData(chosen)
        if index >= 0:
            combo.setCurrentIndex(index)
        self.custom_scope_display_state.pop(key, None)
        self._refresh_scope_display(key)

    def _update_scope_ground_markers(self) -> None:
        for key, marker in self.custom_ground_markers.items():
            marker.setValue(self.custom_scope_position_spins[key].value())
            marker.setVisible(self.custom_scope_checks[key].isChecked())

    def _update_channel_cards(self) -> None:
        if not hasattr(self, "channel_card_labels"):
            return
        titles = {"ch4": "CH4 SCAN", "ch3": "CH3 ERROR", "ch1": "CH1 PD"}
        for key, label in self.channel_card_labels.items():
            if self.custom_scope_data is None or key not in self.custom_scope_data:
                label.setText(f"{titles[key]} | Vpp --")
                continue
            values = np.asarray(self.custom_scope_data[key], dtype=float)
            finite = values[np.isfinite(values)]
            if finite.size == 0:
                label.setText(f"{titles[key]} | Vpp --")
                continue
            vpp_counts = float(np.nanmax(finite) - np.nanmin(finite))
            if key == "ch4":
                vpp = out2_delta_counts_to_voltage(vpp_counts)
                calibration_tip = "OUT2 Vpp uses measured gain 1.18; waiting hardware re-validation"
            else:
                vpp = vpp_counts / COUNTS_PER_VOLT
                calibration_tip = "Ideal voltage conversion from FPGA counts; hardware calibration not yet verified"
            label.setText(f"{titles[key]} | Vpp {format_scope_voltage(vpp)}")
            label.setToolTip(calibration_tip)

    def _update_scope_timebase_summary(self) -> None:
        if not hasattr(self, "custom_scope_timebase_label"):
            return
        if self.custom_scope_data is None:
            self.custom_scope_timebase_label.setText(
                "Window -- ms | Time -- ms/div | Scan -- Hz"
            )
            return
        time_s = np.asarray(self.custom_scope_data.get("time_s", []), dtype=float)
        finite = time_s[np.isfinite(time_s)]
        if finite.size < 2:
            return
        window_ms = float(np.nanmax(finite) - np.nanmin(finite)) * 1000.0
        time_per_div = window_ms / 10.0
        scan_frequency = max(1e-12, float(self.custom_freq_hz.value()))
        self.custom_scope_timebase_label.setText(
            f"Window {window_ms:.3g} ms | Time {time_per_div:.3g} ms/div | "
            f"Scan {scan_frequency:.3g} Hz"
        )

    def _refresh_scope_display(self, key: str | None = None) -> None:
        if self._updating_scope_display_controls or self.custom_scope_data is None:
            return
        x_values = self._scope_x_values()
        if x_values.size == 0:
            return
        self._set_scope_x_axis_label()
        keys = (key,) if key is not None else ("ch1", "ch2", "ch3", "ch4")
        for scope_key in keys:
            raw_y = self.custom_scope_data.get(scope_key)
            if raw_y is None:
                continue
            state = self.custom_scope_display_state.setdefault(scope_key, {})
            auto_scale = self.custom_scope_auto_scale_checks[scope_key].isChecked()
            if auto_scale or "center" not in state:
                center = float(np.nanmedian(np.asarray(raw_y, dtype=float)))
                gain = 1.0 / (
                    COUNTS_PER_VOLT * self._scope_volts_per_div(scope_key)
                )
                state["center"] = center
                state["gain"] = gain
                self._updating_scope_display_controls = True
                try:
                    self.custom_scope_scale_spins[scope_key].setValue(gain)
                finally:
                    self._updating_scope_display_controls = False
            gain = float(self.custom_scope_scale_spins[scope_key].value())
            vertical_offset = float(self.custom_scope_vertical_spins[scope_key].value())
            state["gain"] = gain
            state["vertical_offset"] = vertical_offset
            display_y = scope_display_transform(
                raw_y,
                center=float(state["center"]),
                gain=gain,
                vertical_offset=vertical_offset,
            )
            self.custom_scope_display_data[scope_key] = display_y
            curve = self.custom_scope_curves[scope_key]
            curve.setData(x_values, display_y)
            curve.setVisible(self.custom_scope_checks[scope_key].isChecked())
        self._update_lock_point_markers(self.pending_lock_point or self.selected_lock_point)
        self._update_candidate_marker_positions()
        self._update_scope_ground_markers()
        self._update_channel_cards()
        self._update_scope_timebase_summary()
        self._fit_custom_scope_ranges()
        self.custom_scope_plot.update()

    def _update_custom_scope_visibility(self) -> None:
        for key, curve in self.custom_scope_curves.items():
            checkbox = self.custom_scope_checks.get(key)
            curve.setVisible(bool(checkbox is None or checkbox.isChecked()))
        self._update_scope_ground_markers()
        self._update_channel_cards()
        self._fit_custom_scope_ranges()
        self.custom_scope_plot.update()

    def _reset_scope_channel_display(self, key: str) -> None:
        self._updating_scope_display_controls = True
        try:
            self.custom_scope_auto_scale_checks[key].setChecked(True)
            self.custom_scope_vertical_spins[key].setValue(self.custom_scope_vertical_defaults[key])
            self.custom_scope_position_spins[key].setValue(self.custom_scope_vertical_defaults[key])
        finally:
            self._updating_scope_display_controls = False
        self.custom_scope_display_state.pop(key, None)
        self._refresh_scope_display(key)

    def _apply_scope_default_layout(self) -> None:
        self._updating_scope_display_controls = True
        try:
            for key in ("ch4", "ch3", "ch1", "ch2"):
                self.custom_scope_checks[key].setChecked(key != "ch2")
                self.custom_scope_auto_scale_checks[key].setChecked(True)
                self.custom_scope_vertical_spins[key].setValue(self.custom_scope_vertical_defaults[key])
                self.custom_scope_position_spins[key].setValue(self.custom_scope_vertical_defaults[key])
            self.custom_scope_auto_range_check.setChecked(True)
        finally:
            self._updating_scope_display_controls = False
        self.custom_scope_display_state.clear()
        for key in ("ch4", "ch3", "ch1", "ch2"):
            self._auto_set_scope_channel(key)
        self._refresh_scope_display()

    def _on_custom_scope_clicked(self, event: object) -> None:
        if not self.custom_select_target_check.isChecked():
            return
        if self.custom_scope_data is None or not self.custom_scope_valid_for_selection:
            self.selected_lock_label.setText("selected lock point: capture and validate current waveform first")
            return
        scene_pos = event.scenePos()
        plot_item = self.custom_scope_plot.getPlotItem()
        if not plot_item.sceneBoundingRect().contains(scene_pos):
            return
        view_pos = plot_item.vb.mapSceneToView(scene_pos)
        t = self.custom_scope_data.get("time_s")
        out2 = self.custom_scope_data.get("ch4")
        ch1 = self.custom_scope_data.get("ch1")
        error = self.custom_scope_data.get("ch3")
        x_values = self._scope_x_values()
        if t is None or out2 is None or ch1 is None or error is None or x_values.size == 0:
            return
        clicked_index = int(np.argmin(np.abs(x_values - float(view_pos.x()))))
        error_display = np.asarray(self.custom_scope_display_data.get("ch3", []), dtype=float)
        if clicked_index >= error_display.size or not np.isfinite(error_display[clicked_index]):
            return
        y_range = plot_item.vb.viewRange()[1]
        click_tolerance = max(0.25, abs(float(y_range[1]) - float(y_range[0])) * 0.04)
        if abs(float(view_pos.y()) - float(error_display[clicked_index])) > click_tolerance:
            self.operator_alert_label.setText("Click directly on the CH3 ERROR waveform")
            self.operator_candidate_label.setText("Click the desired ERROR zero crossing")
            return
        try:
            config = build_basic_lock_config(
                safe_min_v=self.basic_pzt_min_v.value(),
                safe_max_v=self.basic_pzt_max_v.value(),
            )
            selected = resolve_direct_error_zero_crossing(
                error_counts=error,
                out2_counts=out2,
                clicked_index=clicked_index,
                safe_min_counts=config.safe_min_counts,
                safe_max_counts=config.safe_max_counts,
                target_window_counts=self.custom_zero_threshold_counts.value(),
                saturated=bool(self.custom_last_capture_payload.get("saturated", False)),
            )
        except (CustomFpgaBackendError, LockPointSelectionError) as exc:
            self.pending_lock_point = None
            self.pending_target_peak = None
            message = str(exc)
            self.selected_lock_label.setText(f"pending target rejected: {message}")
            self.custom_warning_text.setPlainText(message)
            self.operator_alert_label.setText(message)
            return
        peak_index = int(selected["selected_peak_index"])
        zero_index = int(selected["zero_crossing_index"])
        selected["clicked_index"] = clicked_index
        selected["time_s"] = float(t[zero_index])
        selected["out2_counts"] = int(selected["target_out2_counts"])
        selected["error_counts"] = int(round(float(error[zero_index])))
        self.pending_lock_point = {
            **selected,
            "index": zero_index,
        }
        self.pending_target_peak = {
            "index": peak_index,
            "time_s": float(t[peak_index]),
            "out2_counts": int(round(float(out2[peak_index]))),
        }
        self._apply_button_state(self.connection_state)
        self._update_lock_point_markers(self.pending_lock_point)
        self.operator_state_label.setText("WAITING FOR CONFIRMATION")
        self.operator_alert_label.setText("")
        self.operator_candidate_label.setText(
            "Candidate lock point | "
            f"PZT: {format_scope_voltage(float(selected['target_out2_volts']))} | "
            f"Direction: {str(selected['ramp_direction']).title()} | "
            "Status: Waiting for confirmation"
        )
        self.selected_lock_label.setText(
            "pending lock point: "
            f"peak {peak_index}, zero {zero_index}, OUT2 {selected['target_out2_counts']} counts / "
            f"{selected['target_out2_volts']:.6g} V, ERROR_SETPOINT {selected['error_setpoint_counts']} counts, "
            f"slope {selected['slope']:.6g}, ramp {selected['ramp_direction']}. "
            "Press Confirm Lock Point before LOCK HERE."
        )

    def _confirm_pending_lock_point(self) -> None:
        if self.pending_lock_point is None:
            self.selected_lock_label.setText("selected lock point: no valid pending zero crossing to confirm")
            self.operator_alert_label.setText("Lock point not confirmed")
            return
        self.selected_lock_point = dict(self.pending_lock_point)
        self._update_lock_point_markers(self.selected_lock_point)
        self.custom_pick_lock_button.setChecked(False)
        self.operator_state_label.setText("LOCK POINT CONFIRMED")
        self.operator_alert_label.setText("")
        self.operator_candidate_label.setText(
            "Candidate lock point | "
            f"PZT: {format_scope_voltage(float(self.selected_lock_point['target_out2_volts']))} | "
            f"Direction: {str(self.selected_lock_point['ramp_direction']).title()} | "
            "Status: Confirmed"
        )
        self.selected_lock_label.setText(
            "selected lock point confirmed: "
            f"peak {int(self.selected_lock_point['selected_peak_index'])}, "
            f"zero {int(self.selected_lock_point['zero_crossing_index'])}, "
            f"OUT2 {int(self.selected_lock_point['target_out2_counts'])} counts / "
            f"{float(self.selected_lock_point['target_out2_volts']):.6g} V, "
            f"ERROR_SETPOINT {int(self.selected_lock_point['error_setpoint_counts'])}, "
            f"slope {float(self.selected_lock_point['slope']):.6g}, "
            f"ramp {self.selected_lock_point['ramp_direction']}"
        )
        self._apply_button_state(self.connection_state)

    def _render_custom_capture_payload(self, payload: dict[str, Any]) -> None:
        self.custom_last_capture_payload = dict(payload)
        points = payload.get("points", [])
        if not points:
            reason = (
                "custom_debug_capture unavailable: Capture Waveform returned no points from the real FPGA. "
                "No fake waveform is shown. Required FPGA/register path: CAPTURE_CTRL, CAPTURE_STATUS, "
                "CAPTURE_DECIMATION, CAPTURE_LENGTH, CAPTURE_READ_INDEX, CAPTURE_DATA_CH1..CH4. "
                "There is no register-only fallback for IN1/IN2/laser_error/OUT2 waveform capture; "
                "single status reads only provide snapshots such as ERROR_MONITOR and OUT2_MONITOR."
            )
            self.custom_scope_data = None
            self.custom_scope_display_data.clear()
            self.selected_lock_point = None
            self.pending_lock_point = None
            self.pending_target_peak = None
            self.p_lock_ready = False
            self.custom_scope_valid_for_selection = False
            self.custom_confirm_lock_point_button.setEnabled(False)
            self.custom_lock_button.setEnabled(False)
            self.custom_apply_p_button.setEnabled(False)
            self.custom_target_marker.setVisible(False)
            self.custom_zero_marker.setVisible(False)
            self.selected_lock_label.setText("selected lock point: capture current scan waveform first")
            self.basic_candidate_label.setText("candidate: unavailable | custom_debug_capture returned no points")
            self.custom_scope_stats.setText(reason)
            self.operator_state_label.setText("SAFE")
            self.operator_candidate_label.setText("Capture unavailable")
            self.operator_alert_label.setText("Communication lost")
            self._update_channel_cards()
            self._update_scope_timebase_summary()
            self.custom_scope_placeholder.setVisible(True)
            for curve in self.custom_scope_curves.values():
                curve.setData([], [])
                curve.setVisible(False)
            self._clear_candidate_markers()
            return

        labels = {
            "ch1": "IN1 / PD",
            "ch2": "IN2 / REF",
            "ch3": "OUT1 / laser_error",
            "ch4": "OUT2 / selected_out2",
        }
        indices = np.asarray([int(item.get("index", idx)) for idx, item in enumerate(points)], dtype=float)
        decimation = max(1, int(payload.get("capture_decimation", 1)))
        t = indices * decimation / 125_000_000.0
        data = {
            "time_s": t,
            "ch1": np.asarray([int(item.get("ch1_counts", 0)) for item in points], dtype=float),
            "ch2": np.asarray([int(item.get("ch2_counts", 0)) for item in points], dtype=float),
            "ch3": np.asarray([int(item.get("ch3_counts", 0)) for item in points], dtype=float),
            "ch4": np.asarray([int(item.get("ch4_counts", 0)) for item in points], dtype=float),
        }
        self.custom_scope_data = data
        self.selected_lock_point = None
        self.pending_lock_point = None
        self.pending_target_peak = None
        self.p_lock_ready = False
        self.custom_confirm_lock_point_button.setEnabled(False)
        self.custom_lock_button.setEnabled(False)
        self.custom_apply_p_button.setEnabled(False)
        self.operator_state_label.setText("CAPTURE READY")
        self.operator_candidate_label.setText(
            "Candidate lock point | PZT: -- | Direction: -- | Status: Not selected"
        )
        self.operator_alert_label.setText("")
        self.custom_pick_lock_button.setChecked(False)

        self.custom_scope_placeholder.setVisible(False)

        # Hide markers on new capture
        self.custom_target_marker.setVisible(False)
        self.custom_zero_marker.setVisible(False)
        self.custom_target_window_region.setVisible(False)

        # Plot display copies only; custom_scope_data remains the raw capture source.
        self._refresh_scope_display()

        # Force plot update
        self.custom_scope_plot.update()
        self.custom_scope_plot.repaint()

        # Verify curves have data after setData
        rendered_ok = True
        for key in ("ch1", "ch2", "ch3", "ch4"):
            xd = self.custom_scope_curves[key].xData
            if xd is None or len(xd) == 0:
                rendered_ok = False
                break
        if not rendered_ok:
            self.custom_warning_text.setPlainText(
                "capture data exists but plot render failed: "
                "one or more curves have zero-length xData after setData. "
                "Check pyqtgraph PlotDataItem.setData() call."
            )

        # Normal capture only validates whether manual selection is safe. Automatic
        # candidate search remains available to the hidden legacy BASIC LOCK path.
        self._clear_candidate_markers()
        self.basic_lock_candidates = []
        self.custom_scope_valid_for_selection = False
        try:
            manual_config = build_basic_lock_config(
                safe_min_v=self.basic_pzt_min_v.value(),
                safe_max_v=self.basic_pzt_max_v.value(),
            )
            validate_basic_lock_capture(
                ch1_counts=data["ch1"],
                ch3_counts=data["ch3"],
                ch4_counts=data["ch4"],
                safe_min_counts=manual_config.safe_min_counts,
                safe_max_counts=manual_config.safe_max_counts,
                saturated=bool(payload.get("saturated", False)),
            )
        except CustomFpgaBackendError as exc:
            self.basic_candidate_label.setText(f"candidate: rejected | {exc}")
        else:
            self.custom_scope_valid_for_selection = True
        if self.basic_lock_active:
            self.basic_lock_candidates = self._find_and_render_basic_candidates(payload, data)

        # Build stats summary
        stats_lines = []
        detail_lines = []
        for key, label in labels.items():
            values = data[key]
            if values.size:
                vpp = np.nanmax(values) - np.nanmin(values)
                if key == "ch4":
                    detail_lines.append(
                        f"{label}: Vpp {vpp:.0f} counts / {out2_delta_counts_to_voltage(vpp):.6g} V calibrated | "
                        f"min {np.nanmin(values):.0f} counts / {out2_counts_to_voltage(np.nanmin(values)):.6g} V calibrated | "
                        f"max {np.nanmax(values):.0f} counts / {out2_counts_to_voltage(np.nanmax(values)):.6g} V calibrated | "
                        f"mean {np.nanmean(values):.1f} counts / {out2_counts_to_voltage(np.nanmean(values)):.6g} V calibrated"
                    )
                else:
                    detail_lines.append(
                        f"{label}: Vpp {vpp:.0f} counts / {vpp / COUNTS_PER_VOLT:.6g} V ideal | "
                        f"min {np.nanmin(values):.0f} counts / {np.nanmin(values) / COUNTS_PER_VOLT:.6g} V ideal | "
                        f"max {np.nanmax(values):.0f} counts / {np.nanmax(values) / COUNTS_PER_VOLT:.6g} V ideal | "
                        f"mean {np.nanmean(values):.1f} counts / {np.nanmean(values) / COUNTS_PER_VOLT:.6g} V ideal"
                    )
        for key in ("ch1", "ch3", "ch4"):
            values = data[key]
            if values.size:
                stats_lines.append(f"{key.upper()} Vpp {np.nanmax(values) - np.nanmin(values):.0f} counts")
        out2_counts = payload.get("out2_counts", "--")
        try:
            out2_volts_str = f"{out2_counts_to_voltage(int(out2_counts)):.6g} V calibrated"
        except (TypeError, ValueError):
            out2_volts_str = "-- V"
        stats_lines.insert(
            0,
            f"MODE {payload.get('mode', '--')} | OUT2 {out2_counts} counts / {out2_volts_str} | "
            f"correction_limit {payload.get('lock_correction_limit_counts', '--')} counts",
        )
        lock_bias = payload.get("captured_lock_bias_counts")
        if lock_bias is not None:
            try:
                lock_bias_v = out2_counts_to_voltage(int(lock_bias))
                detail_lines.append(f"LOCK_BIAS {lock_bias} counts / {lock_bias_v:.6g} V calibrated")
            except Exception:
                pass
        self.custom_scope_stats.setText("\n".join(stats_lines))
        self.custom_scope_stats.setToolTip("\n".join(detail_lines))

    def _fit_custom_scope_ranges(self) -> None:
        if self.custom_scope_data is None:
            return
        x_values = self._scope_x_values()
        if x_values.size == 0:
            return
        if not self.custom_scope_auto_range_check.isChecked():
            return
        # Auto-fit X range from time array
        finite_x = x_values[np.isfinite(x_values)]
        if finite_x.size:
            x_min = float(np.nanmin(finite_x))
            x_max = float(np.nanmax(finite_x))
            if x_max <= x_min:
                x_max = x_min + 1e-9
            self.custom_scope_plot.setXRange(x_min, x_max, padding=0.02)
        # Auto-fit Y range from visible curves
        y_min = float("inf")
        y_max = float("-inf")
        for key, curve in self.custom_scope_curves.items():
            if not curve.isVisible():
                continue
            y_data = curve.yData
            if y_data is None or len(y_data) == 0:
                continue
            finite_y = y_data[np.isfinite(y_data)]
            if finite_y.size:
                y_min = min(y_min, float(np.nanmin(finite_y)))
                y_max = max(y_max, float(np.nanmax(finite_y)))
        if np.isfinite(y_min) and np.isfinite(y_max):
            if y_max <= y_min:
                pad = max(abs(y_min) * 0.05, 1.0)
                y_min -= pad
                y_max += pad
            self.custom_scope_plot.setYRange(y_min, y_max, padding=0.08)

    def _reset_custom_scope_view(self) -> None:
        self.custom_scope_auto_range_check.setChecked(True)
        self._fit_custom_scope_ranges()
        self.custom_scope_plot.autoRange()
        self.custom_scope_plot.update()

    def _clear_candidate_markers(self) -> None:
        for marker in self.custom_candidate_markers:
            try:
                self.custom_scope_plot.removeItem(marker)
            except (RuntimeError, ValueError):
                pass
        self.custom_candidate_markers = []

    def _find_and_render_basic_candidates(self, payload: dict[str, Any], data: dict[str, np.ndarray]) -> list[Any]:
        self._clear_candidate_markers()
        self.custom_scope_valid_for_selection = False
        config = self.basic_lock_config
        if config is None:
            try:
                config = build_basic_lock_config(
                    safe_min_v=self.basic_pzt_min_v.value(),
                    safe_max_v=self.basic_pzt_max_v.value(),
                )
            except CustomFpgaBackendError as exc:
                self.basic_candidate_label.setText(f"candidate: blocked | {exc}")
                return []
        try:
            validate_basic_lock_capture(
                ch1_counts=data["ch1"],
                ch3_counts=data["ch3"],
                ch4_counts=data["ch4"],
                safe_min_counts=config.safe_min_counts,
                safe_max_counts=config.safe_max_counts,
                saturated=bool(payload.get("saturated", False)),
            )
        except CustomFpgaBackendError as exc:
            self.basic_candidate_label.setText(f"candidate: rejected | {exc}")
            return []

        self.custom_scope_valid_for_selection = True
        candidates = find_zero_crossing_candidates(error_counts=data["ch3"], out2_counts=data["ch4"])
        if not candidates:
            self.basic_candidate_label.setText("candidate: none | click CH1 to search the selected peak window")
            return []
        # candidates found but NOT auto-selected: pending_lock_point stays None
        # user must click via _on_custom_scope_clicked to generate pending_lock_point
        lines = []
        colors = ["#ffcc00", "#72d6ff", "#f472b6"]
        for idx, candidate in enumerate(candidates):
            marker_pos = self._scope_x_value(candidate.index)
            marker = pg.InfiniteLine(
                pos=marker_pos,
                angle=90,
                movable=False,
                pen=pg.mkPen(colors[idx % len(colors)], width=1.1, style=Qt.PenStyle.DashLine),
            )
            self.custom_scope_plot.addItem(marker)
            self.custom_candidate_markers.append(marker)
            lines.append(
                f"candidate {idx + 1}: index {candidate.index}, OUT2 {candidate.out2_counts} counts, "
                f"PZT {out2_counts_to_voltage(candidate.out2_counts):.5f} V calibrated, "
                f"ERROR {candidate.error_counts} counts, slope {candidate.slope:.3g}, "
                f"local Vpp {candidate.local_vpp:.1f}, valid yes, score {candidate.score:.1f}"
            )
        self.basic_candidate_label.setText("\n".join(lines) + "\nClick CH1/PD near the target peak to resolve a lock point.")
        return candidates

    def _capture_payload_hazard(self, payload: dict[str, Any]) -> str | None:
        if not identity_payload_matches(payload):
            return "MAGIC / VERSION readback failed; Live stopped"
        if bool(payload.get("saturated", False)):
            return "FPGA status reports saturation; Live stopped"
        try:
            config = build_basic_lock_config(
                safe_min_v=self.basic_pzt_min_v.value(),
                safe_max_v=self.basic_pzt_max_v.value(),
            )
            out2_counts = int(payload.get("out2_counts", 0))
            if out2_counts < config.safe_min_counts or out2_counts > config.safe_max_counts:
                out2_volts_val = out2_counts_to_voltage(out2_counts)
                return (
                    f"OUT2 is outside the configured PZT safe range; Live stopped.\n"
                    f"  current OUT2: {out2_counts} counts / {out2_volts_val:.6g} V calibrated\n"
                    f"  configured safe_min: {config.safe_min_counts} counts / {config.safe_min_v:.6g} V\n"
                    f"  configured safe_max: {config.safe_max_counts} counts / {config.safe_max_v:.6g} V\n"
                    f"  suggestion: adjust SCAN offset/amp to keep OUT2 within "
                    f"[{config.safe_min_counts}, {config.safe_max_counts}] counts, "
                    f"or widen PZT safe min/max range in BASIC LOCK panel"
                )
        except (CustomFpgaBackendError, TypeError, ValueError):
            pass
        try:
            lock_error = abs(int(payload.get("lock_error_counts", 0)))
            threshold = max(1, int(self.custom_correction_limit_counts.value()))
            if lock_error > threshold:
                self.lock_error_over_threshold_count += 1
            else:
                self.lock_error_over_threshold_count = 0
            if self.lock_error_over_threshold_count >= 3:
                return "LOCK_ERROR exceeded threshold for 3 consecutive reads; Live stopped"
        except (TypeError, ValueError):
            pass
        return None

    def _on_custom_fpga_finished(self, result: object) -> None:
        data = dict(result)
        operation = str(data.get("operation", "custom"))
        payload = data.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        operation_verified = identity_payload_matches(payload) and not bool(
            payload.get("saturated", False)
        )
        self._render_custom_fpga_payload(operation, payload, str(data.get("stderr", "")))
        if operation == "status" and not self.system_identity_matched:
            message = self.system_identity_error_label.text() or "FPGA identity mismatch"
        else:
            message = f"Custom FPGA {operation} complete"
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        if operation == "capture":
            self.capture_in_flight = False
            hazard = self._capture_payload_hazard(payload)
            if hazard:
                self._stop_live_capture(hazard)
                self.custom_warning_text.setPlainText(f"{hazard}\nPress SAFE if output behavior is unexpected.")
                if "saturation" in hazard.lower():
                    self.operator_alert_label.setText("Saturation detected")
                elif "MAGIC" in hazard or "VERSION" in hazard:
                    self.operator_alert_label.setText("FPGA identity mismatch")
                elif "OUT2" in hazard:
                    self.operator_alert_label.setText("OUT2 outside safe PZT range")
        if operation == "lock" and operation_verified:
            self.p_lock_ready = True
            self.applied_kp = 0
            self.applied_polarity_index = self.custom_polarity.currentIndex()
            self.operator_state_label.setText("P_LOCK Kp=0")
            self.operator_alert_label.setText("")
        elif operation == "update-p-lock" and operation_verified:
            kp = int(self.custom_kp.currentText())
            self.applied_kp = kp
            self.applied_polarity_index = self.custom_polarity.currentIndex()
            self.operator_state_label.setText("P_LOCK Kp=0" if kp == 0 else "P_LOCK ACTIVE")
            self.operator_alert_label.setText("")
        if operation == "status" and not self.system_identity_communication_ok:
            error_text = self.system_identity_error_label.text() or "Register read failed"
            self.connection_state = ERROR
            self.operator_connection_status_label.setText("Communication lost")
            self.system_connection_value.setText("Communication lost")
            self.system_identity_error_label.setText(error_text)
            self._apply_button_state(ERROR)
        else:
            self._restore_after_custom_fpga_operation()
        self._continue_basic_lock_after_success(operation, payload)
        if operation == "capture" and self.live_capture_active:
            self._schedule_next_live_capture()
        if not self.basic_lock_active:
            self.current_custom_operation = None

    def _on_custom_fpga_failed(self, text: str) -> None:
        operation = self.current_custom_operation or "custom"
        if operation == "capture":
            self.capture_in_flight = False
            self._stop_live_capture("Capture failed; Live stopped")
        self._set_connection_state(ERROR)
        guidance = text
        if "actual magic:   0x00000000" in text:
            guidance = (
                f"{text}\n\n"
                "GUI guidance: no custom_register_bank was read. Possible causes:\n"
                "- no Program Device / FPGA not loaded\n"
                "- old bit file is loaded\n"
                "- base address is wrong\n"
                "- reload the timing-pass bitstream, then Probe again"
            )
        elif operation == "capture":
            guidance = (
                f"{text}\n\n"
                "GUI guidance: custom_debug_capture did not return usable real FPGA waveform data.\n"
                "- verify the loaded bitstream includes i_custom_debug_capture\n"
                "- verify CAPTURE_CTRL/CAPTURE_STATUS/CAPTURE_DATA_CH1..CH4 registers are readable\n"
                "- no fake waveform will be displayed\n"
                "- there is no status-register fallback for full IN1/IN2/laser_error/OUT2 traces"
            )
        self.custom_register_summary.setText(
            f"Custom FPGA {operation} failed | MAGIC read failed | VERSION read failed | "
            "MODE read failed | ENABLE read failed | STATUS read failed | OUT2 read failed"
        )
        self.custom_warning_text.setPlainText(guidance)
        error_category = classify_identity_error(text)
        self._clear_system_identity("Communication lost", error_category)
        if error_category == "FPGA identity mismatch":
            self.system_identity_value.setText("Mismatch")
        self.system_identity_error_label.setToolTip(text)
        self.operator_alert_label.setText(error_category)
        self.operator_connection_status_label.setText("Communication lost")
        self.statusBar().showMessage(error_category)
        self._append_connection_log(f"Custom FPGA error: {text}")
        if self.basic_lock_active:
            self._basic_lock_fail(f"{operation} failed: {text.splitlines()[0] if text else 'unknown'}")
        else:
            self.current_custom_operation = None

    def _restore_after_custom_fpga_operation(self) -> None:
        if self.last_probe is not None and self.last_probe.port_5000 and self._official_mode():
            self._set_connection_state(SCPI_READY)
        elif self.system_identity_communication_ok or (
            self.last_probe is not None and self.last_probe.port_22
        ):
            self._set_connection_state(SSH_AVAILABLE)
        else:
            self._set_connection_state(DISCONNECTED)

    def _render_custom_fpga_payload(self, operation: str, payload: dict[str, Any], stderr: str) -> None:
        if operation != "probe":
            self._update_system_identity_from_payload(
                payload,
                record_probe=operation == "status",
            )
        if operation == "status" and not self.system_identity_communication_ok:
            self.custom_register_summary.setText("Custom FPGA status read incomplete")
            self.custom_warning_text.setPlainText("Register read failed: status payload is incomplete.")
            return
        if operation == "capture":
            self._render_custom_capture_payload(payload)

        if operation == "probe":
            found = payload.get("found_base_addr") or "--"
            lines = [
                f"Probe Registers: expected MAGIC 0x{EXPECTED_MAGIC:08X}",
                f"found_base_addr: {found}",
                str(payload.get("message", "")),
            ]
            for item in payload.get("probes", []):
                if isinstance(item, dict):
                    lines.append(
                        f"{item.get('base_addr', '--')}: magic {item.get('magic', '--')} "
                        f"version {item.get('version', '--')} match {item.get('match', False)}"
                    )
            self.custom_register_summary.setText(
                f"MAGIC probe | VERSION probe | MODE -- | ENABLE -- | STATUS -- | OUT2 -- | found {found}"
            )
            self.custom_warning_text.setPlainText("\n".join(line for line in lines if line))
            return

        magic = str(payload.get("magic", "--"))
        if not status_payload_has_expected_magic(payload):
            self.custom_register_summary.setText(
                f"custom_register_bank not found | MAGIC {magic} | SAFE/SCAN blocked"
            )
            lines = [
                "custom_register_bank not found.",
                "The FPGA bitstream may not include the register bank, or the base address is wrong.",
                "Please verify Vivado sources_1, top-level instantiation, PS-PL bus connection, and BASE_ADDR.",
                "",
                missing_magic_guidance(magic),
            ]
            if stderr.strip():
                lines.append("")
                lines.append(stderr.strip())
            self.custom_warning_text.setPlainText("\n".join(lines))
            self.operator_alert_label.setText("FPGA identity mismatch")
            return

        version = str(payload.get("version", "--"))
        if parse_register_value(version) != EXPECTED_VERSION:
            self.custom_register_summary.setText(
                f"FPGA identity mismatch | VERSION {version} | expected 0x{EXPECTED_VERSION:08X}"
            )
            self.custom_warning_text.setPlainText(
                f"VERSION mismatch: expected 0x{EXPECTED_VERSION:08X}, got {version}."
            )
            self.operator_alert_label.setText("FPGA identity mismatch")
            return
        mode = payload.get("mode", "--")
        enable = payload.get("enable", "--")
        status = str(payload.get("status_raw", "--"))
        out2_counts = payload.get("out2_counts", "--")
        error_counts = payload.get("error_counts", "--")
        error_volts = payload.get("error_volts", "--")
        error_setpoint_counts = payload.get("error_setpoint_counts", "--")
        lock_error_counts = payload.get("lock_error_counts", "--")
        control_counts = payload.get("control_counts", "--")
        try:
            out2_volts_text = f"{out2_counts_to_voltage(int(out2_counts)):.6g} V calibrated"
        except (TypeError, ValueError):
            out2_volts_text = "-- V"
        try:
            error_volts_text = f"{float(error_volts):.6g} V"
        except (TypeError, ValueError):
            error_volts_text = "-- V"
        try:
            control_volts_text = f"{out2_counts_to_voltage(int(control_counts)):.6g} V calibrated"
        except (TypeError, ValueError):
            control_volts_text = "-- V"
        self.custom_register_summary.setText(
            f"MAGIC {magic} | VERSION {version} | MODE {mode} | ENABLE {enable} | "
            f"STATUS {status} | OUT2 {out2_counts} counts / {out2_volts_text}"
        )
        captured_counts = payload.get("captured_lock_bias_counts")
        if captured_counts is not None:
            try:
                captured_volts = out2_counts_to_voltage(int(captured_counts))
                captured_text = f"{int(captured_counts)} counts / {captured_volts:.6g} V calibrated"
            except (TypeError, ValueError):
                captured_text = f"{captured_counts} counts / -- V calibrated"
            self.captured_bias_label.setText(f"captured lock_bias: {captured_text}")
        lines = [
            f"{operation.upper()} result",
            f"MAGIC: {magic}",
            f"VERSION: {version}",
            f"MODE: {mode}",
            f"ENABLE: {enable}",
            f"STATUS: {status}",
            f"OUT2: {out2_counts} counts / {out2_volts_text}",
            f"ERROR_MONITOR: {error_counts} counts / {error_volts_text}",
            f"ERROR_SETPOINT: {error_setpoint_counts} counts",
            f"LOCK_ERROR_MONITOR: {lock_error_counts} counts",
            f"CONTROL_MONITOR: {control_counts} counts / {control_volts_text}",
        ]
        if captured_counts is not None:
            lines.append(f"LOCK_BIAS source: FPGA CAPTURE_LOCK_POINT captured OUT2_MONITOR = {captured_counts} counts")
            captured_setpoint = payload.get("captured_error_setpoint_counts", error_setpoint_counts)
            lines.append(f"ERROR_SETPOINT source: FPGA CAPTURE_LOCK_POINT captured ERROR_MONITOR = {captured_setpoint} counts")
            lines.append("Calibrated OUT2 volts are software estimates; oscilloscope measurement is the DAC truth.")
        if operation in {"p-lock", "update-p-lock", "pi-lock", "lock"}:
            lines.append("Current LOCK path is P-only; Ki/PI is disabled in the timing-friendly RTL.")
            lines.append("PZT path: keep Kp low; never connect current modulation or D2-125 outputs.")
        if operation == "update-p-lock":
            lines.append(f"APPLY P state: {payload.get('lock_state', '--')}")
            lines.append(f"current Kp: {payload.get('current_kp', payload.get('kp', '--'))}")
            lines.append(f"current polarity: {payload.get('current_polarity', payload.get('polarity', '--'))}")
            lines.append(f"preserved ERROR_SETPOINT: {payload.get('error_setpoint_preserved_counts', error_setpoint_counts)} counts")
            lines.append(f"preserved LOCK_BIAS: {payload.get('lock_bias_preserved_counts', payload.get('lock_bias_counts', '--'))} counts")
        if operation == "lock":
            lines.append(f"LOCK HERE state: {payload.get('lock_state', '--')}")
            lines.append(f"target wait matched: {payload.get('target_wait_matched', '--')}")
            lines.append(f"current Kp: {payload.get('current_kp', '--')}")
            lines.append(f"current correction limit: {payload.get('correction_limit_counts', '--')}")
        if stderr.strip():
            lines.append("")
            lines.append(stderr.strip())
        self.custom_warning_text.setPlainText("\n".join(lines))

    def apply_output(self, channel: int, control: OutputControl) -> None:
        if not self._official_mode() and not isinstance(self.client, MockRedPitayaClient):
            self.statusBar().showMessage(
                "Custom FPGA Mode: OUT2 is selected_out2, not SCPI ASG; use Custom FPGA Control for the PZT path"
            )
            return
        try:
            if control.amplitude.value() >= 0.5:
                reply = QMessageBox.warning(
                    self,
                    "Confirm output amplitude",
                    "amplitude_v is single-sided amplitude. 0.5 V may be about 1 Vpp. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    self.statusBar().showMessage("Output apply cancelled")
                    return
            settings = validate_output_settings(
                channel,
                control.waveform.currentText(),
                control.frequency.value(),
                control.amplitude.value(),
                control.offset.value(),
                control.phase.value(),
                1.0,
            )
            if isinstance(self.client, RedPitayaScpiClient) and self.client.connected:
                result = self.client.apply_output(
                    channel=channel,
                    waveform=settings.waveform,
                    freq=settings.frequency_hz,
                    amp=settings.amplitude_v,
                    offset=settings.offset_v,
                    enable=control.enable.isChecked(),
                    phase_deg=settings.phase_deg,
                    output_range_v=settings.output_range_v,
                )
                for command in result.commands:
                    self._append_connection_log(f">> {command}")
                    print(f">> {command}")
                for query, value in result.readback.items():
                    line = f"<< {query} {value}"
                    self._append_connection_log(line)
                    print(line)
            elif isinstance(self.client, MockRedPitayaClient):
                pass
            else:
                self.statusBar().showMessage("Connect SCPI before applying outputs")
                return
            self._redraw_from_last_waveforms()
            message = f"OUT{channel} command sent. Verify on oscilloscope."
            self.statusBar().showMessage(message)
            self._append_connection_log(message)
            print(message)
        except Exception as exc:
            message = f"Output error: {type(exc).__name__}: {exc}"
            self.statusBar().showMessage(message)
            self._append_connection_log(message)
            print(message)

    def disable_output(self, channel: int, control: OutputControl) -> None:
        if not self._official_mode() and not isinstance(self.client, MockRedPitayaClient):
            self.statusBar().showMessage("Custom FPGA Mode: SCPI output disable is not the FPGA output control path")
            return
        control.enable.setChecked(False)
        try:
            if isinstance(self.client, RedPitayaScpiClient) and self.client.connected:
                commands = self.client.disable_output_with_log(channel)
                for command in commands:
                    self._append_connection_log(f">> {command}")
                    print(f">> {command}")
            message = f"OUT{channel} disabled"
            self.statusBar().showMessage(message)
            self._append_connection_log(message)
        except Exception as exc:
            message = f"Disable error: {type(exc).__name__}: {exc}"
            self.statusBar().showMessage(message)
            self._append_connection_log(message)
            print(message)

    def start_acquisition(self) -> None:
        if not self._official_mode() and not isinstance(self.client, MockRedPitayaClient):
            self.statusBar().showMessage("SCPI acquisition is disabled in Custom FPGA Mode")
            return
        if self.client is None or not self.client.connected:
            self.statusBar().showMessage("Connect SCPI before starting acquisition")
            return
        self.stop_acquisition(wait=True)
        self.current_sample_rate = self._sample_rate()
        self._last_frame_time = None
        if isinstance(self.client, MockRedPitayaClient):
            self.mock_timer.start()
            self._set_connection_state(ACQUIRING)
            self.statusBar().showMessage("acquiring mock data")
            return
        self.acquisition_worker = AcquisitionWorker(self.client, self._decimation(), self)
        self.acquisition_worker.data_ready.connect(self._on_acquisition_data)
        self.acquisition_worker.status.connect(self.statusBar().showMessage)
        self.acquisition_worker.error.connect(lambda text: self.statusBar().showMessage(f"acquisition error: {text}"))
        self.acquisition_worker.stopped.connect(lambda: self._set_acquiring_state(False))
        self.acquisition_worker.start()
        self._set_connection_state(ACQUIRING)
        self.statusBar().showMessage("acquiring")

    def stop_acquisition(self, wait: bool = False) -> None:
        self.mock_timer.stop()
        worker = self.acquisition_worker
        self.acquisition_worker = None
        if worker is not None:
            worker.stop()
            if wait:
                worker.wait(3000)
        if self.client is not None and self.client.connected:
            self._set_connection_state(SCPI_CONNECTED)
        else:
            self._set_acquiring_state(False)

    def _on_probe_finished(self, result: ProbeResult) -> None:
        self.last_probe = result
        self.resolved_ip_combo.clear()
        for ip in result.resolved_ips or [result.host]:
            self.resolved_ip_combo.addItem(ip)
        self._show_probe_result(result)
        if result.warning:
            self._append_connection_log(result.warning)
        if result.error:
            self._append_connection_log(result.error)
        if result.port_22:
            self._set_connection_state(SSH_AVAILABLE)
            message = "Probe complete: SSH available. Use Probe Registers / Status for Custom FPGA Lock Host."
        elif result.port_5000:
            self._set_connection_state(DISCONNECTED)
            message = "Probe complete: SCPI port is visible, but SSH is unavailable; Custom FPGA Lock Host needs SSH."
        else:
            self._set_connection_state(DISCONNECTED)
            message = "Probe complete: SSH unavailable and SCPI unavailable."
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        print(message)

    def _on_probe_failed(self, text: str) -> None:
        self._set_connection_state(ERROR)
        error_category = classify_identity_error(text)
        self._clear_system_identity("Communication lost", error_category)
        self.system_identity_error_label.setToolTip(text)
        self.operator_alert_label.setText(error_category)
        self.statusBar().showMessage(error_category)
        self._append_connection_log(f"Probe error: {text}")
        print(f"Probe error: {text}")

    def _on_start_scpi_finished(self, _result: object, port_ok: bool, log: str) -> None:
        self._append_connection_log(log)
        print(log)
        if port_ok:
            self._set_connection_state(SCPI_READY)
            message = "redpitaya_scpi started; SCPI port 5000 is available. Please click Connect SCPI."
        else:
            self._set_connection_state(ERROR)
            message = "redpitaya_scpi command finished, but PC cannot reach port 5000."
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        print(message)
        QTimer.singleShot(0, self.probe_connection)

    def _on_start_scpi_failed(self, text: str) -> None:
        self._set_connection_state(ERROR)
        message = f"SSH error while starting SCPI: {text}"
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        print(message)

    def _on_connect_scpi_finished(self, client: object, idn: str) -> None:
        self.client = client
        self._register_safe_shutdown()
        self._set_connection_state(SCPI_CONNECTED)
        message = f"SCPI connected: {idn}"
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        print(message)

    def _on_connect_scpi_failed(self, text: str) -> None:
        self.client = None
        self._set_connection_state(ERROR)
        message = f"SCPI connect error: {text}"
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        print(message)

    def _on_disconnect_finished(self, text: str) -> None:
        self._set_connection_state(DISCONNECTED)
        self.statusBar().showMessage(text)
        self._append_connection_log(text)
        print(text)

    def _on_disconnect_failed(self, text: str) -> None:
        self._set_connection_state(ERROR)
        message = f"Disconnect error: {text}"
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        print(message)

    def _clear_worker(self) -> None:
        self.worker = None

    def save_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save waveform CSV",
            str(Path.cwd() / timestamped_name("waveforms_v2", "csv")),
            "CSV files (*.csv)",
        )
        if not path:
            return
        try:
            if self.custom_scope_data is not None:
                with open(path, "w", newline="", encoding="utf-8") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(["time_s", "in1_pd_counts", "in2_ref_counts", "out1_laser_error_counts", "out2_selected_out2_counts"])
                    data = self.custom_scope_data
                    for row in zip(data["time_s"], data["ch1"], data["ch2"], data["ch3"], data["ch4"]):
                        writer.writerow(row)
            else:
                save_waveforms_csv(path, self.last_waveforms, self.notes_edit.toPlainText(), self._csv_metadata())
            self.statusBar().showMessage(f"Saved CSV: {path}")
        except OSError as exc:
            self.statusBar().showMessage(f"Save CSV error: {exc}")

    def save_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save plot PNG",
            str(Path.cwd() / timestamped_name("scope_v2", "png")),
            "PNG files (*.png)",
        )
        if not path:
            return
        try:
            save_plot_png(path, self.plots_panel)
            self.statusBar().showMessage(f"Saved PNG: {path}")
        except OSError as exc:
            self.statusBar().showMessage(f"Save PNG error: {exc}")

    def export_experiment_log(self) -> None:
        try:
            analysis = analyze_custom_fpga_measurements(self._observe_measurements())
            output_dir = Path(__file__).resolve().parents[1] / "docs" / "experiment_logs"
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / timestamped_name("experiment_log", "md")
            mode = self.app_mode_tabs.tabText(self.app_mode_tabs.currentIndex())
            ratio = "--" if analysis.out2_out1_ratio is None else f"{analysis.out2_out1_ratio:.4g}"
            with path.open("w", encoding="utf-8") as handle:
                handle.write("# Red Pitaya Host Experiment Log\n\n")
                handle.write(f"- current_mode: {mode}\n")
                handle.write(f"- current_step: {self.lock_step_combo.currentText()}\n")
                handle.write("- wiring: IN1 PD/MTS < +/-1 V; IN2 4.6 MHz REF < +/-1 V; OUT1=laser_error; OUT2=selected_out2 to laser dedicated PZT / Scan input only\n")
                handle.write(f"- out1_error_vpp: {self.obs_out1_vpp.value():.6g}\n")
                handle.write(f"- out1_error_min: {self.obs_out1_min.value():.6g}\n")
                handle.write(f"- out1_error_max: {self.obs_out1_max.value():.6g}\n")
                handle.write(f"- out2_control_vpp: {self.obs_out2_vpp.value():.6g}\n")
                handle.write(f"- out2_control_min: {self.obs_out2_min.value():.6g}\n")
                handle.write(f"- out2_control_max: {self.obs_out2_max.value():.6g}\n")
                handle.write(f"- pd_absorption_vpp: {self.obs_pd_vpp.value():.6g}\n")
                handle.write(f"- ref_amplitude: {self.obs_ref_amp.value():.6g}\n")
                handle.write(f"- out2_out1_ratio: {ratio}\n")
                handle.write(f"- safety_level: {analysis.level}\n")
                handle.write(f"- safety_judgment: {'; '.join(analysis.messages)}\n")
                handle.write(f"- next_step: {analysis.next_step}\n\n")
                handle.write("## Notes\n\n")
                handle.write(self.experiment_log_notes.toPlainText().strip() or self.obs_notes.toPlainText().strip() or "No notes.")
                handle.write("\n")
            self.experiment_log_status.setText(f"Saved {path}")
            self.statusBar().showMessage(f"Saved experiment log: {path}")
        except OSError as exc:
            self.experiment_log_status.setText(f"Export failed: {exc}")
            self.statusBar().showMessage(f"Experiment log export failed: {exc}")

    def _poll_mock_waveforms(self) -> None:
        if not isinstance(self.client, MockRedPitayaClient):
            return
        sample_count = int(self.config.get("gui", {}).get("sample_count", 2048))
        self.last_waveforms = self.client.get_waveforms(sample_count, self._decimation())
        self.current_sample_rate = self._sample_rate()
        self._redraw_from_last_waveforms()
        self._update_refresh_rate()

    def _on_acquisition_data(self, in1: object, in2: object, sample_rate: float) -> None:
        in1_array = np.asarray(in1, dtype=float)
        in2_array = np.asarray(in2, dtype=float)
        count = min(in1_array.size, in2_array.size)
        if count == 0:
            return
        self.current_sample_rate = float(sample_rate)
        t = np.arange(count, dtype=float) / self.current_sample_rate
        self.last_waveforms = {
            "time_s": t,
            "in1_v": in1_array[:count],
            "in2_v": in2_array[:count],
            "error_internal": np.zeros(count, dtype=float),
        }
        self._redraw_from_last_waveforms()
        self._update_refresh_rate()

    def _redraw_from_last_waveforms(self) -> None:
        t = self.last_waveforms["time_s"]
        in1 = self.last_waveforms["in1_v"]
        in2 = self.last_waveforms["in2_v"]
        if self._scpi_controls_available():
            out1_t, out1 = self._preview_for_control(self.out1)
            out2_t, out2 = self._preview_for_control(self.out2)
        else:
            out1_t = t
            out2_t = t
            out1 = np.zeros_like(t)
            out2 = np.zeros_like(t)
        if all(hasattr(self, name) for name in ("ch1", "ch2", "ch3", "ch4")):
            self.ch1.set_data(t, in1)
            self.ch2.set_data(t, in2)
            self.ch3.set_data(out1_t, out1)
            self.ch4.set_data(out2_t, out2)
        self._update_warnings()

    def _preview_for_control(self, control: OutputControl) -> tuple[np.ndarray, np.ndarray]:
        return generate_waveform_preview(
            waveform=control.waveform.currentText(),
            frequency_hz=control.frequency.value(),
            amplitude_v=control.amplitude.value(),
            offset_v=control.offset.value(),
            phase_deg=control.phase.value(),
            config=self.preview_config,
        )

    def _update_warnings(self) -> None:
        in1 = self.last_waveforms["in1_v"]
        in2 = self.last_waveforms["in2_v"]
        del in2
        if not all(hasattr(self, name) for name in ("ch1", "ch2", "ch3", "ch4")):
            if hasattr(self, "custom_scope_stats") and self.custom_scope_data is None:
                self.custom_scope_stats.setText("custom_debug_capture not available")
            return
        self.ch1.set_warning("clipping warning: ADC close to +/-1 V" if in1.size and np.nanmax(np.abs(in1)) >= 0.95 else "")
        self.ch2.set_warning("4.6 MHz REF may alias when decimation > 8" if self._decimation() > 8 else "")
        if self._official_mode():
            self.ch3.set_warning("Official SCPI ASG preview, not measured")
            self.ch4.set_warning("Official SCPI ASG preview, not measured")
        else:
            self.ch3.set_warning("Custom FPGA Mode: OUT1 is laser_error, not SCPI ASG")
            self.ch4.set_warning(
                "Custom FPGA Mode: OUT2 is selected_out2; LOCK is P-only to the dedicated PZT / Scan input"
            )

    def _observe_measurements(self) -> CustomFpgaMeasurements:
        return CustomFpgaMeasurements(
            out1_error_vpp=self.obs_out1_vpp.value(),
            out1_error_min=self.obs_out1_min.value(),
            out1_error_max=self.obs_out1_max.value(),
            out2_control_vpp=self.obs_out2_vpp.value(),
            out2_control_min=self.obs_out2_min.value(),
            out2_control_max=self.obs_out2_max.value(),
            pd_absorption_vpp=self.obs_pd_vpp.value(),
            ref_amplitude=self.obs_ref_amp.value(),
            notes=self.obs_notes.toPlainText(),
        )

    def _analyze_observe_readings(self) -> None:
        analysis = analyze_custom_fpga_measurements(self._observe_measurements())
        ratio = "--" if analysis.out2_out1_ratio is None else f"{analysis.out2_out1_ratio:.4g}"
        self.obs_result_label.setText(
            f"OUT2/OUT1 Vpp ratio {ratio} | {analysis.level}\n"
            f"{'; '.join(analysis.messages)}\nNext: {analysis.next_step}"
        )
        if analysis.level == "DANGER":
            self.obs_result_label.setStyleSheet("color: #b00020; font-weight: 700;")
        elif analysis.level == "WARNING":
            self.obs_result_label.setStyleSheet("color: #9a5b00; font-weight: 700;")
        else:
            self.obs_result_label.setStyleSheet("color: #146c2e; font-weight: 700;")

    def _show_probe_result(self, result: ProbeResult) -> None:
        ip_text = ", ".join(result.resolved_ips) if result.resolved_ips else "--"
        self.connection_status.setPlainText(
            f"SSH {result.port_22} | Web {result.port_80} | "
            f"SCPI {result.port_5000} | ping {result.ping_ok} | IP {ip_text}"
        )

    def _append_connection_log(self, text: str) -> None:
        existing = self.connection_status.toPlainText().strip()
        self.connection_status.setPlainText(f"{existing}\n{text}" if existing else text)
        cursor = self.connection_status.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.connection_status.setTextCursor(cursor)

    def _target_host(self) -> str:
        text = self.resolved_ip_combo.currentText().strip()
        return text or self.host_edit.text().strip() or "rp-f0cb13.local"

    def _set_connected_state(self, connected: bool) -> None:
        self._set_connection_state(SCPI_CONNECTED if connected else DISCONNECTED)

    def _set_acquiring_state(self, acquiring: bool) -> None:
        self._apply_button_state(ACQUIRING if acquiring else self.connection_state)

    def _set_connection_state(self, state: str) -> None:
        self.connection_state = state
        if hasattr(self, "operator_connection_status_label"):
            connection_text = {
                DISCONNECTED: "Disconnected",
                PROBING: "Disconnected",
                SSH_AVAILABLE: "Connected",
                SCPI_READY: "Connected",
                SCPI_CONNECTED: "Connected",
                ACQUIRING: "Connected",
                CUSTOM_FPGA_BUSY: "Connected",
                ERROR: "Communication lost",
            }.get(state, "Disconnected")
            self.operator_connection_status_label.setText(connection_text)
            if state in {DISCONNECTED, PROBING}:
                self._clear_system_identity("Disconnected")
            elif state == ERROR:
                self._clear_system_identity("Communication lost", "Communication lost")
            else:
                self.system_connection_value.setText(connection_text)
        self._apply_button_state(state)

    def _on_app_mode_tab_changed(self, index: int) -> None:
        label = self.app_mode_tabs.tabText(index)
        if label in {"Custom FPGA Observe", "Lock Workflow", "Data Log"}:
            self.mode_combo.setCurrentText("Custom FPGA Mode")
        self.statusBar().showMessage(f"Mode page: {label}")

    def _apply_button_state(self, state: str) -> None:
        official_or_mock = self._official_mode() or self.mock_check.isChecked()
        worker_running = state in {PROBING, SCPI_STARTING, CUSTOM_FPGA_BUSY}
        custom_busy = state == CUSTOM_FPGA_BUSY
        connected = state in {SCPI_CONNECTED, ACQUIRING}
        scpi_ready = state == SCPI_READY
        ssh_available = state == SSH_AVAILABLE
        acquiring = state == ACQUIRING

        self.probe_button.setEnabled(not worker_running and not connected and not ssh_available)
        self.start_scpi_button.setEnabled(
            not worker_running
            and not connected
            and self._official_mode()
            and ssh_available
            and self.last_probe is not None
            and self.last_probe.port_22
            and not self.last_probe.port_5000
        )
        self.connect_scpi_button.setEnabled(
            not worker_running
            and not connected
            and official_or_mock
            and (scpi_ready or self.mock_check.isChecked())
        )
        self.disconnect_button.setEnabled((connected or ssh_available) and not acquiring)
        self.mock_check.setEnabled(not worker_running and not connected)
        self.mode_combo.setEnabled(not worker_running and not connected)
        if hasattr(self, "start_acq_button"):
            self.start_acq_button.setEnabled(connected and not acquiring and official_or_mock)
            self.stop_acq_button.setEnabled(acquiring)
            self.decimation_combo.setEnabled(not acquiring)
        if self._scpi_controls_available():
            for control in (self.out1, self.out2):
                control.apply_button.setEnabled(connected and not acquiring and official_or_mock)
                control.disable_button.setEnabled(connected and not acquiring and official_or_mock)
        custom_enabled = (not custom_busy) and (not connected) and (not self.mock_check.isChecked())
        for button in (
            self.custom_probe_button,
            self.custom_status_button,
            self.custom_safe_button,
            self.custom_scan_button,
            self.custom_hold_button,
            self.custom_p_lock_button,
            self.custom_pi_lock_button,
            self.custom_capture_bias_button,
            self.custom_lock_button,
            self.custom_apply_p_button,
            self.custom_arm_auto_lock_button,
            self.custom_abort_auto_lock_button,
            self.custom_unlock_button,
            self.custom_capture_waveform_button,
            self.custom_capture_once_button,
            self.custom_start_live_button,
            self.custom_confirm_lock_point_button,
            self.basic_lock_button,
            self.basic_safe_button,
            self.scan_stop_safe_button,
        ):
            button.setEnabled(custom_enabled)
        self.system_identity_refresh_button.setEnabled(custom_enabled)
        identity_enabled = (
            custom_enabled
            and self.system_identity_matched
            and not self.system_identity_saturated
        )
        for button in (
            self.custom_scan_button,
            self.custom_hold_button,
            self.custom_p_lock_button,
            self.custom_pi_lock_button,
            self.custom_capture_bias_button,
            self.custom_arm_auto_lock_button,
            self.custom_capture_waveform_button,
            self.custom_capture_once_button,
            self.custom_start_live_button,
            self.custom_pick_lock_button,
            self.basic_lock_button,
        ):
            button.setEnabled(identity_enabled)
        self.custom_safe_button.setEnabled(True)
        self.scan_stop_safe_button.setEnabled(True)
        self.custom_confirm_lock_point_button.setEnabled(
            identity_enabled and self.pending_lock_point is not None
        )
        self.custom_lock_button.setEnabled(
            identity_enabled and self.selected_lock_point is not None
        )
        self.custom_apply_p_button.setEnabled(identity_enabled and self.p_lock_ready)
        self.custom_stop_live_button.setEnabled(self.live_capture_active or custom_busy)
        for widget in (
            self.basic_pzt_min_v,
            self.basic_pzt_max_v,
            self.custom_base_addr_edit,
            self.custom_offset_v,
            self.custom_amp_v,
            self.custom_freq_hz,
            self.custom_step_counts,
            self.custom_limit_counts,
            self.custom_hold_v,
            self.custom_kp,
            self.custom_ki,
            self.custom_polarity,
            self.custom_lock_bias_v,
            self.custom_lock_limit_counts,
            self.custom_correction_limit_counts,
            self.custom_zero_threshold_counts,
            self.custom_capture_length,
            self.custom_capture_decimation,
            self.custom_capture_view_mode,
            self.custom_ref_debug_decimation,
            self.custom_live_interval_ms,
        ):
            widget.setEnabled(custom_enabled)

    def _official_mode(self) -> bool:
        return self.mode_combo.currentText() == "Official SCPI Mode"

    def _scpi_controls_available(self) -> bool:
        return hasattr(self, "out1") and hasattr(self, "out2")

    def _on_mode_changed(self) -> None:
        if self._official_mode():
            self.mode_explain_label.setText(
                "Official SCPI Mode: start redpitaya_scpi if needed, connect to port 5000, "
                "control official ASG OUT1/OUT2, and acquire IN1/IN2. Starting SCPI may "
                "load official v0.94 overlay and overwrite the custom FPGA bitstream. "
                "Official SCPI Mode controls the official ASG. If a custom FPGA bitstream "
                "with USE_LASER_LOCK_CORE=1 is loaded, SCPI OUT2 commands may succeed but "
                "will not drive physical OUT2 because OUT2 is routed to selected_out2."
            )
            if all(hasattr(self, name) for name in ("ch3", "ch4")):
                self.ch3.subtitle_label.setText("official ASG generated preview, not measured")
                self.ch4.subtitle_label.setText("official ASG generated preview, not measured")
        else:
            self.mode_explain_label.setText(
                "Custom FPGA Lock Host: do not start redpitaya_scpi overlay. "
                "OUT1=laser_error (mixer+LPF). OUT2=selected_out2 from register-controlled "
                "SAFE/SCAN/HOLD/P_LOCK modes. Main flow: Probe Registers -> Status -> SAFE -> SCAN -> "
                "Capture Waveform -> click target -> LOCK HERE -> APPLY P -> UNLOCK/SAFE. Current LOCK=P-only; Ki/PI disabled. "
                "SCPI ASG output commands do not drive physical OUT2 in the current custom bitstream."
            )
            if all(hasattr(self, name) for name in ("ch3", "ch4")):
                self.ch3.subtitle_label.setText("Custom FPGA OUT1 = laser_error; not ADC measured")
                self.ch4.subtitle_label.setText("Custom FPGA OUT2 = selected_out2; dedicated PZT / Scan path")
        self._set_connected_state(self.client is not None and self.client.connected)
        self._redraw_from_last_waveforms()

    def _update_lock_step_detail(self) -> None:
        details = {
            "1. Input Safety Check": (
                "Wiring: IN1 PD/MTS after BPF+amp < +/-1 V; IN2 4.6 MHz REF < +/-1 V.\n"
                "Scope: verify IN1/IN2 before FPGA control decisions.\n"
                "Pass: both inputs safe and stable. Stop: clipping, wrong REF, or unknown scaling.\n"
                "Next: Error Signal Observe."
            ),
            "2. Error Signal Observe": (
                "Wiring: OUT1 -> oscilloscope.\n"
                "Scope: FPGA laser_error on OUT1.\n"
                "Pass: visible nonzero error-like signal. Stop: OUT1 missing, saturated, or unstable.\n"
                "Next: Control Output Observe."
            ),
            "3. Control Output Observe": (
                "Wiring: OUT2 -> laser dedicated PZT / Scan input after limit and SAFE checks.\n"
                "PZT: selected_out2 SAFE/SCAN first, then LOCK HERE Kp=0 and APPLY P on OUT2.\n"
                "Pass: OUT2 within safe limit and not rapidly climbing/jumping. Stop: OUT2 near +/-1 V.\n"
                "Next: Direction / Polarity Check."
            ),
            "4. Direction / Polarity Check": (
                "Wiring: OUT2 remains on the dedicated PZT / Scan input; no current modulation or D2-125 output parallel.\n"
                "Observe: compare OUT1 error trend and OUT2 control response.\n"
                "Pass: direction is understood. Stop: ambiguous or runaway response.\n"
                "Next: Gain / Limit Check."
            ),
            "5. Gain / Limit Check": (
                "Wiring: OUT2 remains on the dedicated PZT / Scan input.\n"
                "Observe: check OUT2/OUT1 ratio, min/max, and Vpp.\n"
                "Pass: small, bounded control output. Stop: large Vpp, random jumps, or drift.\n"
                "Next: Ready for Low-gain Lock Test."
            ),
            "6. Ready for Low-gain Lock Test": (
                "Wiring: OUT2 may drive only the laser dedicated PZT / Scan input after safety and polarity are reviewed.\n"
                "Pass: input safety, error signal, control output, polarity, and limits are documented.\n"
                "Next: Future Lock Engage.\n"
                "Not implemented until FPGA register/debug interface is available."
            ),
            "7. Future Lock Engage": (
                "Future step: host/FSM lock engagement replacing D2-125 Lock/Scan switch.\n"
                "Not implemented until FPGA register/debug interface is available."
            ),
            "8. Future Relock": (
                "Future step: lock quality judgment and relock state machine.\n"
                "Not implemented until FPGA register/debug interface is available."
            ),
        }
        self.lock_step_detail.setText(details.get(self.lock_step_combo.currentText(), ""))

    def _decimation(self) -> int:
        if not hasattr(self, "decimation_combo"):
            return int(self.config.get("acquisition", {}).get("decimation", 1024))
        return int(self.decimation_combo.currentText())

    def _sample_rate(self) -> float:
        return 125e6 / self._decimation()

    def _update_sample_rate_label(self) -> None:
        self.current_sample_rate = self._sample_rate()
        if hasattr(self, "sample_rate_label"):
            self.sample_rate_label.setText(f"{self.current_sample_rate:.6g} Sa/s")
        self._update_warnings()

    def _update_refresh_rate(self) -> None:
        now = time.monotonic()
        if self._last_frame_time is not None:
            dt = now - self._last_frame_time
            if dt > 0 and hasattr(self, "refresh_rate_label"):
                self.refresh_rate_label.setText(f"actual refresh_rate: {1.0 / dt:.2f} Hz")
        self._last_frame_time = now

    def _update_offset_range(self, control: OutputControl) -> None:
        max_offset = max(0.0, 1.0 - control.amplitude.value())
        value = min(max(control.offset.value(), -max_offset), max_offset)
        control.offset.blockSignals(True)
        control.offset.setRange(-max_offset, max_offset)
        control.offset.setValue(value)
        control.offset.blockSignals(False)
        self._redraw_from_last_waveforms()

    def _csv_metadata(self) -> dict[str, Any]:
        metadata = {
            "mock_mode": self.mock_check.isChecked(),
            "mode": self.mode_combo.currentText(),
            "target_host": self._target_host(),
            "decimation": self._decimation(),
            "sample_rate": self.current_sample_rate,
            "preview_cycles": self.preview_config.cycles,
            "preview_max_points": self.preview_config.max_points,
            "preview_note": "Custom FPGA Lock Host does not use Official SCPI OUT1/OUT2 preview controls",
            "error_internal": "not implemented; requires FPGA debug buffer",
        }
        if self._scpi_controls_available():
            metadata.update(
                {
                    "out1_waveform": self.out1.waveform.currentText(),
                    "out1_frequency_hz": self.out1.frequency.value(),
                    "out1_amplitude_v": self.out1.amplitude.value(),
                    "out1_offset_v": self.out1.offset.value(),
                    "out2_waveform": self.out2.waveform.currentText(),
                    "out2_frequency_hz": self.out2.frequency.value(),
                    "out2_amplitude_v": self.out2.amplitude.value(),
                    "out2_offset_v": self.out2.offset.value(),
                }
            )
        return metadata

    def _register_safe_shutdown(self) -> None:
        if not self._safe_shutdown_registered:
            register_safe_shutdown(self._safe_shutdown_atexit)
            self._safe_shutdown_registered = True

    def _unregister_safe_shutdown(self) -> None:
        if self._safe_shutdown_registered:
            unregister_safe_shutdown(self._safe_shutdown_atexit)
            self._safe_shutdown_registered = False

    def _safe_shutdown_atexit(self) -> None:
        if isinstance(self.client, RedPitayaScpiClient) and self.client.connected:
            try:
                self.client.safe_shutdown_outputs()
            except Exception:
                pass

    @staticmethod
    def _empty_waveforms() -> dict[str, np.ndarray]:
        t = np.linspace(0.0, 0.01, 1024)
        zeros = np.zeros_like(t)
        return {
            "time_s": t,
            "in1_v": zeros,
            "in2_v": zeros,
            "error_internal": zeros,
        }

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_live_capture("Window closing; Live stopped")
        self.stop_acquisition(wait=True)
        if isinstance(self.client, RedPitayaScpiClient) and self.client.connected:
            try:
                self.client.safe_shutdown_outputs()
            except (ScpiError, OSError) as exc:
                QMessageBox.warning(self, "Safe shutdown warning", str(exc))
        self._unregister_safe_shutdown()
        event.accept()
