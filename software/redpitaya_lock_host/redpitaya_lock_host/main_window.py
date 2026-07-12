"""PySide6 main window for Red Pitaya laser lock host V2."""

from __future__ import annotations

import time
import csv
from dataclasses import dataclass
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
    EXPECTED_MAGIC,
    BasicLockConfig,
    CustomFpgaBackendError,
    build_basic_lock_config,
    find_zero_crossing_candidates,
    missing_magic_guidance,
    status_payload_has_expected_magic,
    validate_basic_lock_capture,
)
from .custom_fpga_workflow import CustomFpgaMeasurements, analyze_custom_fpga_measurements
from .data_logger import save_plot_png, save_waveforms_csv, timestamped_name
from .mock_client import MockRedPitayaClient
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
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setWordWrap(True)
        self.stats_label = QLabel("Vpp -- | min -- | max -- | mean --")
        self.stats_label.setWordWrap(True)
        self.warning_label = QLabel("")
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #b00020; font-weight: 600;")
        self.plot = WaveformPlot(title, y_label)
        self.plot.setMinimumSize(360, 230)
        self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.setContentsMargins(10, 18, 10, 10)
        layout.setSpacing(6)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.plot, stretch=1)

    def set_data(self, x: np.ndarray, y: np.ndarray) -> None:
        self.plot.set_data(x, y)
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

    def set_warning(self, text: str) -> None:
        self.warning_label.setText(text)


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
        self.selected_lock_point: dict[str, int | float] | None = None
        self.custom_scope_valid_for_selection = False
        self.basic_lock_active = False
        self.basic_lock_queue: list[str] = []
        self.basic_lock_config: BasicLockConfig | None = None
        self.basic_lock_candidates: list[Any] = []
        self.current_custom_operation: str | None = None
        self.connection_state = DISCONNECTED
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

        self.setWindowTitle("Red Pitaya Laser Lock Host V2")
        self._apply_app_font()
        self._build_ui()
        self._load_defaults()

        self.mock_timer = QTimer(self)
        self.mock_timer.setInterval(int(self.config.get("gui", {}).get("refresh_ms", 100)))
        self.mock_timer.timeout.connect(self._poll_mock_waveforms)

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
        main_layout = QVBoxLayout(root)
        body = QSplitter()
        controls = self._build_controls()
        plots = self._build_plots()
        body.addWidget(controls)
        body.addWidget(plots)
        body.setChildrenCollapsible(False)
        body.setSizes([460, 1140])
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)
        main_layout.addWidget(body, stretch=1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar(self))
        self._connect_signals()

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
        self.custom_offset_v = self._custom_double_spin(0.0, -1.0, 1.0, 4, " V")
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
        ):
            self._style_field(widget)
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
        form.addRow("capture-length", self.custom_capture_length)
        form.addRow("capture-decimation", self.custom_capture_decimation)
        self.captured_bias_label = QLabel("captured lock_bias: -- counts / -- V ideal")
        self.captured_bias_label.setWordWrap(True)
        form.addRow("captured bias", self.captured_bias_label)
        self.selected_lock_label = QLabel("selected lock point: click current scan waveform first")
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
        ):
            self._style_button(button)
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
        layout.setSpacing(8)
        self.custom_scope_group = QGroupBox("Custom FPGA Scope")
        scope_layout = QVBoxLayout(self.custom_scope_group)
        scope_layout.setContentsMargins(10, 18, 10, 10)
        self.custom_scope_plot_top = WaveformPlot("Custom FPGA Scope - PD / Error", "Counts")
        self.custom_scope_plot_bottom = WaveformPlot("Custom FPGA Scope - OUT2 / REF", "Counts")
        self.custom_scope_plot = self.custom_scope_plot_top
        self.custom_scope_plot_top.clear()
        self.custom_scope_plot_bottom.clear()
        self.custom_scope_plot_top.set_placeholder_text("custom_debug_capture not available")
        self.custom_scope_plot_bottom.set_placeholder_text("custom_debug_capture not available")
        self.custom_scope_curves = {
            "ch1": self.custom_scope_plot_top.plot_item.plot([], [], pen=pg.mkPen("#1f77b4", width=1.3), name="IN1 / PD"),
            "ch2": self.custom_scope_plot_bottom.plot_item.plot([], [], pen=pg.mkPen("#ff7f0e", width=1.3), name="IN2 / REF"),
            "ch3": self.custom_scope_plot_top.plot_item.plot([], [], pen=pg.mkPen("#2ca02c", width=1.5), name="OUT1 / laser_error"),
            "ch4": self.custom_scope_plot_bottom.plot_item.plot([], [], pen=pg.mkPen("#d62728", width=1.5), name="OUT2 / selected_out2"),
        }
        self.custom_lock_marker = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#7f3fbf", width=1.2, style=Qt.PenStyle.DashLine),
        )
        self.custom_lock_marker_bottom = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#7f3fbf", width=1.2, style=Qt.PenStyle.DashLine),
        )
        self.custom_lock_marker.setVisible(False)
        self.custom_lock_marker_bottom.setVisible(False)
        self.custom_scope_plot_top.plot_item.addItem(self.custom_lock_marker)
        self.custom_scope_plot_bottom.plot_item.addItem(self.custom_lock_marker_bottom)
        self.custom_candidate_markers: list[pg.InfiniteLine] = []
        self.custom_scope_plot_top.scene().sigMouseClicked.connect(self._on_custom_scope_clicked)
        self.custom_scope_plot_bottom.scene().sigMouseClicked.connect(self._on_custom_scope_clicked)
        checkbox_row = QHBoxLayout()
        self.custom_scope_checks = {}
        for key, label in (
            ("ch1", "IN1 / PD"),
            ("ch2", "IN2 / REF"),
            ("ch3", "OUT1 / laser_error"),
            ("ch4", "OUT2 / selected_out2"),
        ):
            checkbox = QCheckBox(label)
            checkbox.setChecked(key in {"ch1", "ch3", "ch4"})
            checkbox.toggled.connect(self._update_custom_scope_visibility)
            self.custom_scope_checks[key] = checkbox
            checkbox_row.addWidget(checkbox)
        checkbox_row.addStretch(1)
        self.custom_scope_stats = QLabel("custom_debug_capture not available")
        self.custom_scope_stats.setWordWrap(True)
        scope_layout.addLayout(checkbox_row)
        scope_layout.addWidget(self.custom_scope_stats)
        scope_layout.addWidget(self.custom_scope_plot_top, stretch=1)
        scope_layout.addWidget(self.custom_scope_plot_bottom, stretch=1)
        layout.addWidget(self.custom_scope_group, stretch=1)
        return panel

    def _connect_signals(self) -> None:
        self.probe_button.clicked.connect(self.probe_connection)
        self.start_scpi_button.clicked.connect(self.start_scpi_server)
        self.connect_scpi_button.clicked.connect(self.connect_scpi)
        self.disconnect_button.clicked.connect(self.disconnect_from_device)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.app_mode_tabs.currentChanged.connect(self._on_app_mode_tab_changed)
        self.custom_probe_button.clicked.connect(lambda: self._start_custom_fpga_operation("probe"))
        self.custom_status_button.clicked.connect(lambda: self._start_custom_fpga_operation("status"))
        self.custom_safe_button.clicked.connect(lambda: self._start_custom_fpga_operation("safe"))
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

    def _start_custom_fpga_operation(self, operation: str, *, preserve_basic: bool = False) -> None:
        if operation == "safe" and not preserve_basic:
            self.basic_lock_active = False
            self.basic_lock_queue = []
        if self._official_mode():
            self.mode_combo.setCurrentText("Custom FPGA Mode")
        try:
            base_addr = int(self.custom_base_addr_edit.text().strip(), 0)
        except ValueError:
            self.statusBar().showMessage("Invalid Custom FPGA base address")
            return
        params = {}
        if operation == "scan":
            params = {
                "offset_v": self.custom_offset_v.value(),
                "amp_v": self.custom_amp_v.value(),
                "freq_hz": self.custom_freq_hz.value(),
                "step_counts": self.custom_step_counts.value(),
                "limit_counts": self.custom_limit_counts.value(),
            }
        elif operation == "hold":
            params = {
                "hold_v": self.custom_hold_v.value(),
            }
        elif operation in {"p-lock", "pi-lock"}:
            params = {
                "kp": int(self.custom_kp.currentText()),
                "ki": self.custom_ki.value(),
                "polarity": 1 if self.custom_polarity.currentText() == "invert" else 0,
                "lock_bias_v": self.custom_lock_bias_v.value(),
                "lock_limit_counts": self.custom_lock_limit_counts.value(),
                "correction_limit_counts": self.custom_correction_limit_counts.value(),
            }
        elif operation == "update-p-lock":
            params = {
                "kp": int(self.custom_kp.currentText()),
                "polarity": 1 if self.custom_polarity.currentText() == "invert" else 0,
            }
        elif operation == "lock":
            if self.selected_lock_point is None:
                self.custom_warning_text.setPlainText(
                    "LOCK HERE requires a target selected from the current scan waveform. "
                    "Run SCAN, Capture Waveform, click the desired zero point, then press LOCK HERE."
                )
                self.statusBar().showMessage("LOCK HERE blocked: no waveform point selected")
                return
            params = {
                "polarity": 1 if self.custom_polarity.currentText() == "invert" else 0,
                "lock_limit_counts": self.custom_lock_limit_counts.value(),
                "correction_limit_counts": self.custom_correction_limit_counts.value(),
                "settle_s": 0.5,
                "target_out2_counts": int(self.selected_lock_point["out2_counts"]),
                "target_window_counts": self.custom_zero_threshold_counts.value(),
                "target_timeout_s": 5.0,
            }
        elif operation == "capture":
            params = {
                "capture_length": self.custom_capture_length.value(),
                "capture_decimation": self.custom_capture_decimation.value(),
            }
        target = self._target_host()
        user = self.ssh_user_edit.text().strip() or "root"
        password = self.ssh_password_edit.text()
        message = f"Custom FPGA {operation}: SSH /dev/mem on {target}, base=0x{base_addr:08X}"
        self.current_custom_operation = operation
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        self.custom_warning_text.setPlainText(message)
        self._set_connection_state(CUSTOM_FPGA_BUSY)
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
        if self.selected_lock_point is None:
            self._basic_lock_fail("BASIC LOCK found no valid zero-crossing candidate")
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
        self.custom_kp.setCurrentText("0")
        self.basic_lock_queue = ["lock"]
        self._continue_basic_lock()

    def _continue_basic_lock_after_success(self, operation: str, payload: dict[str, Any]) -> None:
        del payload
        if not self.basic_lock_active:
            return
        if operation == "capture":
            if self.basic_lock_candidates:
                self.basic_status_label.setText("state: CANDIDATE_FOUND | waiting for confirmation")
                QTimer.singleShot(0, self._confirm_basic_lock_candidate)
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
            "4.6 MHz REF may alias when decimation is high.",
        ]
        self.custom_warning_text.setPlainText("\n".join(lines))
        self.custom_scope_stats.setText("custom_debug_capture not available")
        self.statusBar().showMessage("Custom FPGA waveform capture requires the new debug_capture bitstream")

    def _update_custom_scope_visibility(self) -> None:
        for key, curve in getattr(self, "custom_scope_curves", {}).items():
            checkbox = self.custom_scope_checks.get(key)
            curve.setVisible(bool(checkbox is None or checkbox.isChecked()))
        self._fit_custom_scope_ranges()
        for plot in (self.custom_scope_plot_top, self.custom_scope_plot_bottom):
            plot.plot_item.update()
            plot.update()

    def _on_custom_scope_clicked(self, event: object) -> None:
        if self.custom_scope_data is None or not self.custom_scope_valid_for_selection:
            self.selected_lock_point = None
            self.selected_lock_label.setText("selected lock point: capture and validate current waveform first")
            return
        scene_pos = event.scenePos()
        if self.custom_scope_plot_top.plot_item.sceneBoundingRect().contains(scene_pos):
            plot = self.custom_scope_plot_top
        elif self.custom_scope_plot_bottom.plot_item.sceneBoundingRect().contains(scene_pos):
            plot = self.custom_scope_plot_bottom
        else:
            return
        view_pos = plot.plot_item.vb.mapSceneToView(scene_pos)
        t = self.custom_scope_data.get("time_s")
        out2 = self.custom_scope_data.get("ch4")
        error = self.custom_scope_data.get("ch3")
        if t is None or out2 is None or error is None or t.size == 0:
            return
        if self.basic_lock_candidates:
            nearest = min(
                self.basic_lock_candidates,
                key=lambda candidate: abs(float(t[candidate.index]) - float(view_pos.x())),
            )
            index = int(nearest.index)
        else:
            return
        self.selected_lock_point = {
            "index": index,
            "time_s": float(t[index]),
            "out2_counts": int(round(float(out2[index]))),
            "error_counts": int(round(float(error[index]))),
        }
        self.custom_lock_marker.setValue(float(t[index]))
        self.custom_lock_marker_bottom.setValue(float(t[index]))
        self.custom_lock_marker.setVisible(True)
        self.custom_lock_marker_bottom.setVisible(True)
        self.selected_lock_label.setText(
            "selected lock point: "
            f"index {index}, OUT2 {int(round(float(out2[index])))} counts, "
            f"ERROR {int(round(float(error[index])))} counts"
        )

    def _render_custom_capture_payload(self, payload: dict[str, Any]) -> None:
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
            self.selected_lock_point = None
            self.custom_scope_valid_for_selection = False
            self.custom_lock_marker.setVisible(False)
            self.custom_lock_marker_bottom.setVisible(False)
            self.selected_lock_label.setText("selected lock point: capture current scan waveform first")
            self.basic_candidate_label.setText("candidate: unavailable | custom_debug_capture returned no points")
            self.custom_scope_stats.setText(reason)
            self.custom_scope_plot_top.set_placeholder_text("custom_debug_capture not available: no real FPGA points")
            self.custom_scope_plot_bottom.set_placeholder_text("custom_debug_capture not available: no real FPGA points")
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
        for key, curve in self.custom_scope_curves.items():
            curve.setData(t, data[key])
            curve.setVisible(True)
        self.custom_scope_plot_top.hide_placeholder()
        self.custom_scope_plot_bottom.hide_placeholder()
        self._update_custom_scope_visibility()
        self._fit_custom_scope_ranges()
        for plot in (self.custom_scope_plot_top, self.custom_scope_plot_bottom):
            plot.show()
            plot.plot_item.showAxis("bottom", True)
            plot.plot_item.showAxis("left", True)
            plot.plot_item.update()
            plot.update()

        self.basic_lock_candidates = self._find_and_render_basic_candidates(payload, data)

        stats_lines = []
        for key, label in labels.items():
            values = data[key]
            if values.size:
                stats_lines.append(
                    f"{label}: Vpp {np.nanmax(values) - np.nanmin(values):.0f} counts | "
                    f"min {np.nanmin(values):.0f} | max {np.nanmax(values):.0f} | mean {np.nanmean(values):.1f}"
                )
        stats_lines.append("4.6 MHz REF may alias when decimation is high.")
        stats_lines.append(
            f"MODE {payload.get('mode', '--')} | Kp not captured in status | "
            f"current OUT2 {payload.get('out2_counts', '--')} | "
            f"correction_limit {payload.get('lock_correction_limit_counts', '--')}"
        )
        self.custom_scope_stats.setText("\n".join(stats_lines))

    def _fit_custom_scope_ranges(self) -> None:
        if self.custom_scope_data is None:
            return
        t = self.custom_scope_data.get("time_s")
        if t is None or t.size == 0:
            return
        visible_top = [
            np.asarray(self.custom_scope_data[key], dtype=float)
            for key in ("ch1", "ch3")
            if self.custom_scope_checks[key].isChecked()
        ]
        visible_bottom = [
            np.asarray(self.custom_scope_data[key], dtype=float)
            for key in ("ch4", "ch2")
            if self.custom_scope_checks[key].isChecked()
        ]
        if visible_top:
            self.custom_scope_plot_top._fit_ranges(np.asarray(t, dtype=float), np.concatenate(visible_top))
        if visible_bottom:
            self.custom_scope_plot_bottom._fit_ranges(np.asarray(t, dtype=float), np.concatenate(visible_bottom))

    def _clear_candidate_markers(self) -> None:
        for marker in getattr(self, "custom_candidate_markers", []):
            for plot in (self.custom_scope_plot_top, self.custom_scope_plot_bottom):
                try:
                    plot.plot_item.removeItem(marker)
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

        candidates = find_zero_crossing_candidates(error_counts=data["ch3"], out2_counts=data["ch4"])
        if not candidates:
            self.basic_candidate_label.setText("candidate: none | no valid non-edge zero crossing")
            return []
        self.custom_scope_valid_for_selection = True
        t = data["time_s"]
        lines = []
        colors = ["#ffcc00", "#72d6ff", "#f472b6"]
        for idx, candidate in enumerate(candidates):
            marker = pg.InfiniteLine(
                pos=float(t[candidate.index]),
                angle=90,
                movable=False,
                pen=pg.mkPen(colors[idx % len(colors)], width=1.1, style=Qt.PenStyle.DashLine),
            )
            marker_bottom = pg.InfiniteLine(
                pos=float(t[candidate.index]),
                angle=90,
                movable=False,
                pen=pg.mkPen(colors[idx % len(colors)], width=1.1, style=Qt.PenStyle.DashLine),
            )
            self.custom_scope_plot_top.plot_item.addItem(marker)
            self.custom_scope_plot_bottom.plot_item.addItem(marker_bottom)
            self.custom_candidate_markers.append(marker)
            self.custom_candidate_markers.append(marker_bottom)
            lines.append(
                f"candidate {idx + 1}: index {candidate.index}, OUT2 {candidate.out2_counts} counts, "
                f"PZT {candidate.out2_counts / 8191.0:.5f} V ideal, "
                f"ERROR {candidate.error_counts} counts, slope {candidate.slope:.3g}, "
                f"local Vpp {candidate.local_vpp:.1f}, valid yes, score {candidate.score:.1f}"
            )
        best = candidates[0]
        self.selected_lock_point = {
            "index": best.index,
            "time_s": float(t[best.index]),
            "out2_counts": best.out2_counts,
            "error_counts": best.error_counts,
        }
        self.custom_lock_marker.setValue(float(t[best.index]))
        self.custom_lock_marker_bottom.setValue(float(t[best.index]))
        self.custom_lock_marker.setVisible(True)
        self.custom_lock_marker_bottom.setVisible(True)
        self.selected_lock_label.setText(
            f"selected lock point: candidate 1, index {best.index}, OUT2 {best.out2_counts} counts, "
            f"ERROR {best.error_counts} counts"
        )
        self.basic_candidate_label.setText("\n".join(lines))
        return candidates

    def _on_custom_fpga_finished(self, result: object) -> None:
        data = dict(result)
        operation = str(data.get("operation", "custom"))
        payload = data.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        self._render_custom_fpga_payload(operation, payload, str(data.get("stderr", "")))
        message = f"Custom FPGA {operation} complete"
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        self._restore_after_custom_fpga_operation()
        self._continue_basic_lock_after_success(operation, payload)
        if not self.basic_lock_active:
            self.current_custom_operation = None

    def _on_custom_fpga_failed(self, text: str) -> None:
        operation = self.current_custom_operation or "custom"
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
        self.statusBar().showMessage(f"Custom FPGA error: {text.splitlines()[0] if text else 'unknown'}")
        self._append_connection_log(f"Custom FPGA error: {text}")
        if self.basic_lock_active:
            self._basic_lock_fail(f"{operation} failed: {text.splitlines()[0] if text else 'unknown'}")
        else:
            self.current_custom_operation = None

    def _restore_after_custom_fpga_operation(self) -> None:
        if self.last_probe is not None and self.last_probe.port_5000 and self._official_mode():
            self._set_connection_state(SCPI_READY)
        elif self.last_probe is not None and self.last_probe.port_22:
            self._set_connection_state(SSH_AVAILABLE)
        else:
            self._set_connection_state(DISCONNECTED)

    def _render_custom_fpga_payload(self, operation: str, payload: dict[str, Any], stderr: str) -> None:
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
            return

        version = str(payload.get("version", "--"))
        mode = payload.get("mode", "--")
        enable = payload.get("enable", "--")
        status = str(payload.get("status_raw", "--"))
        out2_counts = payload.get("out2_counts", "--")
        out2_volts = payload.get("out2_volts", "--")
        error_counts = payload.get("error_counts", "--")
        error_volts = payload.get("error_volts", "--")
        error_setpoint_counts = payload.get("error_setpoint_counts", "--")
        lock_error_counts = payload.get("lock_error_counts", "--")
        control_counts = payload.get("control_counts", "--")
        control_volts = payload.get("control_volts", "--")
        try:
            out2_volts_text = f"{float(out2_volts):.6g} V"
        except (TypeError, ValueError):
            out2_volts_text = "-- V"
        try:
            error_volts_text = f"{float(error_volts):.6g} V"
        except (TypeError, ValueError):
            error_volts_text = "-- V"
        try:
            control_volts_text = f"{float(control_volts):.6g} V"
        except (TypeError, ValueError):
            control_volts_text = "-- V"
        self.custom_register_summary.setText(
            f"MAGIC {magic} | VERSION {version} | MODE {mode} | ENABLE {enable} | "
            f"STATUS {status} | OUT2 {out2_counts} counts / {out2_volts_text}"
        )
        captured_counts = payload.get("captured_lock_bias_counts")
        captured_volts = payload.get("captured_lock_bias_volts_ideal")
        if captured_counts is not None:
            try:
                captured_text = f"{int(captured_counts)} counts / {float(captured_volts):.6g} V ideal"
            except (TypeError, ValueError):
                captured_text = f"{captured_counts} counts / -- V ideal"
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
            lines.append("Ideal volts are register-scale estimates only; oscilloscope measurement is the DAC truth.")
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
        message = f"Probe error: {text}"
        self.statusBar().showMessage(message)
        self._append_connection_log(message)
        print(message)

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

        self.probe_button.setEnabled(not worker_running and not connected)
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
        self.disconnect_button.setEnabled(connected and not acquiring)
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
            self.basic_lock_button,
            self.basic_safe_button,
        ):
            button.setEnabled(custom_enabled)
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
        self.stop_acquisition(wait=True)
        if isinstance(self.client, RedPitayaScpiClient) and self.client.connected:
            try:
                self.client.safe_shutdown_outputs()
            except (ScpiError, OSError) as exc:
                QMessageBox.warning(self, "Safe shutdown warning", str(exc))
        self._unregister_safe_shutdown()
        event.accept()
