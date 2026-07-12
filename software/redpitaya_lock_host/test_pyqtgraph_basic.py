import sys
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

QCoreApplication.setAttribute(
    Qt.ApplicationAttribute.AA_UseSoftwareOpenGL
)

pg.setConfigOption("useOpenGL", False)
pg.setConfigOption("background", "k")
pg.setConfigOption("foreground", "w")

app = QApplication(sys.argv)

x = np.linspace(0, 1, 2000)
y = np.sin(2 * np.pi * 10 * x)

window = pg.plot(
    x,
    y,
    title="PyQtGraph Basic Test"
)
window.setWindowTitle("PyQtGraph Basic Test")
window.resize(1000, 600)
window.show()

sys.exit(app.exec())
