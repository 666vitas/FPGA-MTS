import sys
import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication
from redpitaya_lock_host.waveform_plot import WaveformPlot

QCoreApplication.setAttribute(
    Qt.ApplicationAttribute.AA_UseSoftwareOpenGL
)

pg.setConfigOption("useOpenGL", False)

app = QApplication(sys.argv)

x = np.linspace(0.0, 0.1, 2048)
y = 5000.0 + 300.0 * np.sin(2.0 * np.pi * 10.0 * x)

window = WaveformPlot(
    "Project WaveformPlot Test",
    "Counts"
)

window.set_data(x, y)
window.resize(1000, 600)
window.show()

sys.exit(app.exec())
