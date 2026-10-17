import traceback

from PyQt6 import uic
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMainWindow

from src.classes.solution import Solution


class LoadingScreen:
    """ Shows the progress while the timetable is being made """

    window: QMainWindow

    def __init__(self, ui_file: str) -> None:
        self.window = uic.loadUi(ui_file)
        self.window.setWindowTitle("Creating Classes...")
        self.set_progress(0, "Loading...")

    def show(self) -> None:
        self.window.show()

    def close(self) -> None:
        self.window.close()

    def set_progress(self, percent: int, message: str) -> None:
        self.window.progressBar.setValue(percent)
        self.window.label.setText(message)


class SolutionWorker(QObject):
    """ Runs a solution on a background thread so the window keeps responding """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    solution: Solution

    def __init__(self, solution: Solution) -> None:
        super().__init__()
        self.solution = solution

    def run(self) -> None:
        try:
            self.solution.execute(self.progress.emit)
        except Exception as error:      # a crash on the thread would otherwise vanish silently
            traceback.print_exc()
            self.failed.emit(f"Something went wrong making the timetable: {error}")
            return
        self.finished.emit()
