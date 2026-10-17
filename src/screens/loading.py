import traceback

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from src.classes.solution import Solution


class LoadingScreen(QWidget):
    """ Shows the progress while the timetable is being made """

    progress_bar: QProgressBar
    message: QLabel

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Creating the timetable")
        self.setMinimumWidth(440)

        title = QLabel("Creating the timetable")
        title.setProperty("role", "heading")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.message = QLabel()
        self.message.setProperty("role", "muted")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.message)

        self.set_progress(0, "Loading...")

    def set_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(percent)
        self.message.setText(message)


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
