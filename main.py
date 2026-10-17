import sys

from PyQt6.QtWidgets import QApplication

from src.config import Settings, load_settings
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

        # TODO: run Solution(self.settings) once the algorithm exists (phases 3-4)
        self.start_screen.set_info_label(f"Loaded {len(students)} students, {len(tutors)} tutors and {len(rooms)} rooms")


def main() -> None:
    app = QApplication(sys.argv)

    settings = load_settings(resource_path("settings.txt"))
    start_screen = StartScreen(resource_path("src/ui_files/start_screen.ui"))
    controller = Main(settings, start_screen)

    start_screen.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
