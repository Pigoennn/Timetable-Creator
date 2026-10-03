import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6 import uic as PyUI

from openingScreen import *

app = QApplication(sys.argv)

lWindow = PyUI.loadUi("loadingScren.ui")
lWindow.setWindowTitle("Creating Classes...")

lWindow.progressBar.setValue(0)

def switchScreens():
    global sWindow
    sWindow.close()
    lWindow.show()

sWindow.show()
sys.exit(app.exec())
