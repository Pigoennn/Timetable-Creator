import os
import sys
from datetime import datetime

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication

from src.classes.solution import Solution
from src.config import Settings, load_settings
from src.loader import LoaderError, load_students, load_tutor_sheet, verify_files
from src.resources import resource_path
from src.screens.loading import LoadingScreen, SolutionWorker
from src.screens.start import StartScreen
from src.screens.timetable import TimetableScreen


class Main:
    """ Connects the screens to the timetable solution """

    settings: Settings
    start_screen: StartScreen
    loading_screen: LoadingScreen
    timetable_screen: TimetableScreen | None

    solution: Solution | None
    save_folder: str
    thread: QThread | None
    worker: SolutionWorker | None

    def __init__(self, settings: Settings, start_screen: StartScreen, loading_screen: LoadingScreen) -> None:
        self.settings = settings
        self.start_screen = start_screen
        self.loading_screen = loading_screen
        self.timetable_screen = None

        self.solution = None
        self.save_folder = ""
        self.thread = None
        self.worker = None

        self.start_screen.connect_create(self.create_timetable)

    def create_timetable(self) -> None:
        """ Check and load the chosen files, then make the timetable on a background thread """
        student_csv, tutor_csv = self.start_screen.get_files()

        error = verify_files(student_csv, tutor_csv)
        if error:
            self.start_screen.set_info_label(error)
            return

        try:
            students = load_students(student_csv, self.settings)
            tutors, rooms = load_tutor_sheet(tutor_csv, self.settings)
        except LoaderError as error:
            self.start_screen.set_info_label(str(error))
            return

        self.solution = Solution(self.settings)
        self.solution.setup(students, tutors, rooms)
        self.save_folder = os.path.dirname(student_csv)

        self.start_screen.hide()
        self.loading_screen.set_progress(0, "Loading...")
        self.loading_screen.show()

        # the worker lives on the thread, so its signals reach the screens through the event loop
        self.thread = QThread()
        self.worker = SolutionWorker(self.solution)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.loading_screen.set_progress)
        self.worker.finished.connect(self.show_timetable)
        self.worker.failed.connect(self.show_failure)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

        self.thread.start()

    def show_timetable(self) -> None:
        self.timetable_screen = TimetableScreen(self.solution, self.settings, self.save_folder, datetime.now())
        self.loading_screen.close()
        self.timetable_screen.show()

    def show_failure(self, message: str) -> None:
        self.loading_screen.close()
        self.start_screen.set_info_label(message)
        self.start_screen.show()


def main() -> None:
    app = QApplication(sys.argv)

    settings = load_settings(resource_path("settings.txt"))
    start_screen = StartScreen(resource_path("src/ui_files/start_screen.ui"))
    loading_screen = LoadingScreen(resource_path("src/ui_files/loading_screen.ui"))
    controller = Main(settings, start_screen, loading_screen)

    start_screen.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
