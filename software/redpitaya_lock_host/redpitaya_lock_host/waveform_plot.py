"""Reusable pyqtgraph waveform panel."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QSizePolicy


PLOT_BACKGROUND = "#05070a"
PLOT_FOREGROUND = "#e6edf3"
PLOT_GRID = "#6b7280"
DEFAULT_CURVE = "#4ea1ff"


class WaveformPlot(pg.GraphicsLayoutWidget):
    def __init__(self, title: str, y_label: str, parent=None) -> None:
        super().__init__(parent=parent)
        self.setMinimumSize(320, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setBackground(PLOT_BACKGROUND)
        self.plot_item = self.addPlot(title=title)
        self.plot_item.setTitle(title, color=PLOT_FOREGROUND)
        self.plot_item.setMenuEnabled(False)
        self.plot_item.setMouseEnabled(x=True, y=True)
        self.plot_item.getViewBox().setBackgroundColor(QColor(PLOT_BACKGROUND))
        self.plot_item.showGrid(x=True, y=True, alpha=0.25)
        self.plot_item.setLabel("bottom", "time", units="s")
        self.plot_item.setLabel("left", y_label)
        self._apply_axis_theme()
        self.curve = self.plot_item.plot([], [], pen=pg.mkPen(DEFAULT_CURVE, width=1.5))
        self.curve.setDownsampling(auto=True, method="peak")
        self.curve.setClipToView(True)
        self.curve.setVisible(True)
        self.placeholder = pg.TextItem(text="", color=PLOT_FOREGROUND, anchor=(0.5, 0.5))
        self.placeholder.setParentItem(self.plot_item.getViewBox())
        self.placeholder.setPos(0.5, 0.0)
        self.placeholder.setVisible(False)

    def set_data(self, x, y) -> None:
        x_arr = np.asarray(x, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        if x_arr.size == 0 or y_arr.size == 0:
            self.clear()
            return
        count = min(x_arr.size, y_arr.size)
        x_arr = x_arr[:count]
        y_arr = y_arr[:count]
        self.curve.setData(x_arr, y_arr)
        self.curve.setVisible(True)
        self.placeholder.setVisible(False)
        self._fit_ranges(x_arr, y_arr)

    def clear(self) -> None:
        self.curve.setData([], [])
        self.curve.setVisible(False)

    def set_title(self, title: str) -> None:
        self.plot_item.setTitle(title, color=PLOT_FOREGROUND)

    def set_labels(self, x_label: str = "time", x_units: str = "s", y_label: str = "Voltage [V]") -> None:
        self.plot_item.setLabel("bottom", x_label, units=x_units)
        self.plot_item.setLabel("left", y_label)
        self._apply_axis_theme()

    def set_placeholder_text(self, text: str) -> None:
        self.placeholder.setText(text)
        self.placeholder.setColor(QColor(PLOT_FOREGROUND))
        self.placeholder.setVisible(bool(text))

    def hide_placeholder(self) -> None:
        self.placeholder.setVisible(False)

    def _apply_axis_theme(self) -> None:
        axis_pen = pg.mkPen(PLOT_FOREGROUND, width=1.0)
        grid_pen = pg.mkPen(PLOT_GRID, width=0.8)
        for axis_name in ("bottom", "left", "top", "right"):
            axis = self.plot_item.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen(axis_pen)
            axis.setTickPen(axis_pen)
            axis.setGrid(80)
        self.plot_item.getAxis("bottom").setStyle(tickTextOffset=8)
        self.plot_item.getAxis("left").setStyle(tickTextOffset=8)
        del grid_pen

    def _fit_ranges(self, x_arr: np.ndarray, y_arr: np.ndarray) -> None:
        finite_x = x_arr[np.isfinite(x_arr)]
        finite_y = y_arr[np.isfinite(y_arr)]
        if finite_x.size:
            x_min = float(np.nanmin(finite_x))
            x_max = float(np.nanmax(finite_x))
            if x_max <= x_min:
                x_max = x_min + 1e-9
            self.plot_item.setXRange(x_min, x_max, padding=0.02)
        if finite_y.size:
            y_min = float(np.nanmin(finite_y))
            y_max = float(np.nanmax(finite_y))
            if y_max <= y_min:
                pad = max(abs(y_min) * 0.05, 1e-3)
                y_min -= pad
                y_max += pad
            self.plot_item.setYRange(y_min, y_max, padding=0.08)
