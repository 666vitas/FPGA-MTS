"""Reusable pyqtgraph waveform panel."""

from __future__ import annotations

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

    def set_data(self, x, y) -> None:
        self.curve.setData(x, y)

    def set_placeholder_text(self, text: str) -> None:
        label = pg.TextItem(text=text, color="#777777", anchor=(0.5, 0.5))
        label.setParentItem(self.plot_item)
        label.setPos(0.5, 0.0)
