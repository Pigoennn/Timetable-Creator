import os
import sys
from datetime import datetime

from PyQt6.QtWidgets import QApplication

from src.classes.solution import Solution
from src.config import Settings, load_settings
from src.export import write_errors, write_timetable
from src.loader import LoaderError, load_students, load_tutor_sheet, verify_files
from src.resources import resource_path
from src.screens.start import StartScreen


class Main:
    """ Connects the screens to the timetable solution """

    settings: Settings
    start_screen: StartScreen

    def __init__(self, settings: Settings, start_screen: StartScreen) -> None:
        self.settings = settings
        self.start_screen = start_screen
        self.start_screen.connect_create(self.create_timetable)

    def create_timetable(self) -> None:
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

        solution = Solution(self.settings)
        solution.setup(students, tutors, rooms)
        solution.execute()

        # TODO: show the loading and timetable screens, and save the CSV from there (phase 6)
        folder = os.path.dirname(student_csv)
        write_timetable(os.path.join(folder, "timetable.csv"), solution.schedule, self.settings)
        write_errors(os.path.join(folder, "Errors.txt"), students, tutors, datetime.now())

        missing = sum(1 for student in students if student.unplaceable)
        self.start_screen.set_info_label(f"Created {len(solution.schedule.classes)} classes for {len(students)} "
                                         f"students. {missing} students are missing a class. "
                                         f"Saved timetable.csv and Errors.txt next to the student file")


def main() -> None:
    app = QApplication(sys.argv)

    settings = load_settings(resource_path("settings.txt"))
    start_screen = StartScreen(resource_path("src/ui_files/start_screen.ui"))
    controller = Main(settings, start_screen)

    start_screen.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
