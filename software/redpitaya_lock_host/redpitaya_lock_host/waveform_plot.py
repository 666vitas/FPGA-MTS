"""Reusable pyqtgraph waveform panel."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QSizePolicy


class WaveformPlot(pg.GraphicsLayoutWidget):
    def __init__(self, title: str, y_label: str, parent=None) -> None:
        super().__init__(parent=parent)
        self.setMinimumSize(320, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_item = self.addPlot(title=title)
        self.plot_item.showGrid(x=True, y=True, alpha=0.25)
        self.plot_item.setLabel("bottom", "time", units="s")
        self.plot_item.setLabel("left", y_label)
        self.curve = self.plot_item.plot([], [], pen=pg.mkPen("#1f77b4", width=1.5))
        self.curve.setDownsampling(auto=True, method="peak")
        self.curve.setClipToView(True)

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
        self._fit_ranges(x_arr, y_arr)

    def clear(self) -> None:
        self.curve.setData([], [])

    def set_title(self, title: str) -> None:
        self.plot_item.setTitle(title)

    def set_labels(self, x_label: str = "time", x_units: str = "s", y_label: str = "Voltage [V]") -> None:
        self.plot_item.setLabel("bottom", x_label, units=x_units)
        self.plot_item.setLabel("left", y_label)

    def set_placeholder_text(self, text: str) -> None:
        label = pg.TextItem(text=text, color="#777777", anchor=(0.5, 0.5))
        label.setParentItem(self.plot_item)
        label.setPos(0.5, 0.0)

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
