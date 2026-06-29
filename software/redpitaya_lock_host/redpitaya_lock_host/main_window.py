"""PySide6 main window for Red Pitaya laser lock host V2."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QTimer
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
    DisconnectWorker,
    ProbeWorker,
    StartScpiServerWorker,
)
from .data_logger import save_plot_png, save_waveforms_csv, timestamped_name
from .mock_client import MockRedPitayaClient
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
        self.client: RedPitayaScpiClient | MockRedPitayaClient | None = None
        self.acquisition_worker: AcquisitionWorker | None = None
        self.last_probe: ProbeResult | None = None
        self.last_waveforms = self._empty_waveforms()
        self.connection_state = DISCONNECTED
        self.worker: ProbeWorker | StartScpiServerWorker | ConnectScpiWorker | DisconnectWorker | None = None
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
        layout.addWidget(self._output_group())
        layout.addWidget(self._acquisition_group())
        layout.addWidget(self._export_group())
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setMinimumWidth(430)
        scroll.resize(460, scroll.height())
        scroll.setMaximumWidth(680)
        scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        return scroll

    def _connection_group(self) -> QGroupBox:
        group = QGroupBox("Connection")
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
        self.mode_combo.addItems(["Official SCPI Mode", "Custom FPGA Mode"])
        self.mode_explain_label = QLabel("")
        self.mode_explain_label.setWordWrap(True)
        self.probe_button = QPushButton("Probe")
        self.start_scpi_button = QPushButton("Start SCPI Server")
        self.connect_scpi_button = QPushButton("Connect SCPI")
        self.disconnect_button = QPushButton("Disconnect")
        self.connection_status = QTextEdit()
        self.connection_status.setReadOnly(True)
        self.connection_status.setMaximumHeight(110)
        self.connection_status.setMinimumHeight(80)
        self.connection_status.setPlainText("SSH -- | Web -- | SCPI -- | IP --")
        self.scpi_warning_label = QLabel(
            "Starting redpitaya_scpi may load official v0.94 overlay and may "
            "overwrite the currently loaded custom FPGA bitstream."
        )
        self.scpi_warning_label.setWordWrap(True)
        self.scpi_warning_label.setStyleSheet("color: #9a5b00;")
        button_row = QGridLayout()
        button_row.setHorizontalSpacing(8)
        button_row.setVerticalSpacing(6)
        button_row.addWidget(self.probe_button, 0, 0)
        button_row.addWidget(self.start_scpi_button, 0, 1)
        button_row.addWidget(self.connect_scpi_button, 1, 0)
        button_row.addWidget(self.disconnect_button, 1, 1)
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
        form.addRow("current mode", self.mode_combo)
        form.addRow(self.mock_check)
        form.addRow(button_row)
        form.addRow(self.connection_status)
        form.addRow(self.mode_explain_label)
        form.addRow(self.scpi_warning_label)
        return group

    def _output_group(self) -> QGroupBox:
        group = QGroupBox("Output Control")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 18, 10, 10)
        layout.setSpacing(8)
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
        grid = QGridLayout(panel)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.ch1 = ChannelPanel("CH1: IN1 / ADC measured", "real ACQ:SOUR1:DATA?")
        self.ch2 = ChannelPanel("CH2: IN2 / ADC measured", "real ACQ:SOUR2:DATA?")
        self.ch3 = ChannelPanel("CH3: OUT1 preview", "generated preview, not measured")
        self.ch4 = ChannelPanel("CH4: OUT2 preview", "generated preview, not measured")
        grid.addWidget(self.ch1, 0, 0)
        grid.addWidget(self.ch2, 0, 1)
        grid.addWidget(self.ch3, 1, 0)
        grid.addWidget(self.ch4, 1, 1)
        return panel

    def _connect_signals(self) -> None:
        self.probe_button.clicked.connect(self.probe_connection)
        self.start_scpi_button.clicked.connect(self.start_scpi_server)
        self.connect_scpi_button.clicked.connect(self.connect_scpi)
        self.disconnect_button.clicked.connect(self.disconnect_from_device)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
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
        self.start_acq_button.clicked.connect(self.start_acquisition)
        self.stop_acq_button.clicked.connect(self.stop_acquisition)
        self.decimation_combo.currentTextChanged.connect(self._update_sample_rate_label)
        self.save_csv_button.clicked.connect(self.save_csv)
        self.save_png_button.clicked.connect(self.save_png)

    def _load_defaults(self) -> None:
        rp = self.config.get("red_pitaya", {})
        self.host_edit.setText(str(rp.get("host", "rp-f0cb13.local")))
        self.mock_check.setChecked(bool(self.start_mock))
        self.decimation_combo.setCurrentText(str(self.config.get("acquisition", {}).get("decimation", 1024)))
        self.resolved_ip_combo.addItem(str(rp.get("host", "rp-f0cb13.local")))
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

    def apply_output(self, channel: int, control: OutputControl) -> None:
        if not self._official_mode() and not isinstance(self.client, MockRedPitayaClient):
            self.statusBar().showMessage(
                "Custom FPGA Mode: OUT1/OUT2 are laser_error/laser_control, not SCPI ASG"
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
        if result.port_5000:
            self._set_connection_state(SCPI_READY)
            message = "Probe complete: SCPI port 5000 is available. Please click Connect SCPI."
        elif result.port_22:
            self._set_connection_state(SSH_AVAILABLE)
            message = "Probe complete: SSH available, SCPI closed. Start SCPI Server is available."
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
        out1 = self._preview_for_control(t, self.out1)
        out2 = self._preview_for_control(t, self.out2)
        self.ch1.set_data(t, in1)
        self.ch2.set_data(t, in2)
        self.ch3.set_data(t, out1)
        self.ch4.set_data(t, out2)
        self._update_warnings()

    def _preview_for_control(self, t: np.ndarray, control: OutputControl) -> np.ndarray:
        if t.size == 0:
            return np.array([], dtype=float)
        freq = max(control.frequency.value(), 0.001)
        amp = control.amplitude.value()
        offset = control.offset.value()
        phase = np.deg2rad(control.phase.value())
        x = 2 * np.pi * freq * t + phase
        waveform = control.waveform.currentText()
        if waveform == "square":
            y = np.where(np.sin(x) >= 0, 1.0, -1.0)
        elif waveform == "triangle":
            ph = ((freq * t + control.phase.value() / 360.0) % 1.0)
            y = 2.0 * np.abs(2.0 * ph - 1.0) - 1.0
        elif waveform == "sawtooth":
            ph = ((freq * t + control.phase.value() / 360.0) % 1.0)
            y = 2.0 * ph - 1.0
        else:
            y = np.sin(x)
        return offset + amp * y

    def _update_warnings(self) -> None:
        in1 = self.last_waveforms["in1_v"]
        in2 = self.last_waveforms["in2_v"]
        del in2
        self.ch1.set_warning("clipping warning: ADC close to +/-1 V" if in1.size and np.nanmax(np.abs(in1)) >= 0.95 else "")
        self.ch2.set_warning("4.6 MHz REF may alias when decimation > 8" if self._decimation() > 8 else "")
        if self._official_mode():
            self.ch3.set_warning("Official SCPI ASG preview, not measured")
            self.ch4.set_warning("Official SCPI ASG preview, not measured")
        else:
            self.ch3.set_warning("Custom FPGA Mode: OUT1 is laser_error, not SCPI ASG")
            self.ch4.set_warning("Custom FPGA Mode: OUT2 is laser_control, scope-only")

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

    def _apply_button_state(self, state: str) -> None:
        official_or_mock = self._official_mode() or self.mock_check.isChecked()
        worker_running = state in {PROBING, SCPI_STARTING}
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
        self.start_acq_button.setEnabled(connected and not acquiring and official_or_mock)
        self.stop_acq_button.setEnabled(acquiring)
        self.decimation_combo.setEnabled(not acquiring)
        for control in (self.out1, self.out2):
            control.apply_button.setEnabled(connected and not acquiring and official_or_mock)
            control.disable_button.setEnabled(connected and not acquiring and official_or_mock)

    def _official_mode(self) -> bool:
        return self.mode_combo.currentText() == "Official SCPI Mode"

    def _on_mode_changed(self) -> None:
        if self._official_mode():
            self.mode_explain_label.setText(
                "Official SCPI Mode: start redpitaya_scpi if needed, connect to port 5000, "
                "control official ASG OUT1/OUT2, and acquire IN1/IN2. Starting SCPI may "
                "load official v0.94 overlay and overwrite the custom FPGA bitstream."
            )
            self.ch3.subtitle_label.setText("official ASG generated preview, not measured")
            self.ch4.subtitle_label.setText("official ASG generated preview, not measured")
        else:
            self.mode_explain_label.setText(
                "Custom FPGA Mode: do not start redpitaya_scpi overlay. Current RTL routes "
                "OUT1=laser_error and OUT2=laser_control. SCPI ASG output control is disabled."
            )
            self.ch3.subtitle_label.setText("Custom FPGA OUT1 = laser_error; not ADC measured")
            self.ch4.subtitle_label.setText("Custom FPGA OUT2 = laser_control; scope-only")
        self._set_connected_state(self.client is not None and self.client.connected)
        self._redraw_from_last_waveforms()

    def _decimation(self) -> int:
        return int(self.decimation_combo.currentText())

    def _sample_rate(self) -> float:
        return 125e6 / self._decimation()

    def _update_sample_rate_label(self) -> None:
        self.current_sample_rate = self._sample_rate()
        self.sample_rate_label.setText(f"{self.current_sample_rate:.6g} Sa/s")
        self._update_warnings()

    def _update_refresh_rate(self) -> None:
        now = time.monotonic()
        if self._last_frame_time is not None:
            dt = now - self._last_frame_time
            if dt > 0:
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
        return {
            "mock_mode": self.mock_check.isChecked(),
            "mode": self.mode_combo.currentText(),
            "target_host": self._target_host(),
            "decimation": self._decimation(),
            "sample_rate": self.current_sample_rate,
            "out1_waveform": self.out1.waveform.currentText(),
            "out1_frequency_hz": self.out1.frequency.value(),
            "out1_amplitude_v": self.out1.amplitude.value(),
            "out1_offset_v": self.out1.offset.value(),
            "out2_waveform": self.out2.waveform.currentText(),
            "out2_frequency_hz": self.out2.frequency.value(),
            "out2_amplitude_v": self.out2.amplitude.value(),
            "out2_offset_v": self.out2.offset.value(),
            "preview_note": "OUT1/OUT2 previews are generated, not measured",
            "error_internal": "not implemented; requires FPGA debug buffer",
        }

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
