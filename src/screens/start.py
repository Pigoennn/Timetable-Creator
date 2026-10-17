from typing import Callable

from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog, QMainWindow

SELECTED_BUTTON_STYLE = """
    QPushButton {
        color: white;
        background-color: #645CB8;
        border-radius: 0px;
        border-color: #87E2E8;
        text-align: left;
    }
    QPushButton:hover {
        background-color: #7870cc;
    }
    QPushButton:pressed {
        background-color: #5048a4;
    }
    QToolTip {
        background-color: rgb(232, 232, 232);
        color: black;
        border-color: black;
        border-width: 2px;
    }
    """


class StartScreen:
    """ The start screen. Lets the user choose the student and tutor CSV files """

    window: QMainWindow

    student_csv: str
    tutor_csv: str

    def __init__(self, ui_file: str) -> None:
        self.window = uic.loadUi(ui_file)
        self.window.setWindowTitle("Timetable Creator")

        self.student_csv = ""
        self.tutor_csv = ""

        # each file has two buttons: the wide upload button and the small one beside it
        self.window.studentAvailabilityButton.clicked.connect(lambda: self.choose_file("student"))
        self.window.studentAvailabilityButton2.clicked.connect(lambda: self.choose_file("student"))
        self.window.tutorAvailabilityButton.clicked.connect(lambda: self.choose_file("tutor"))
        self.window.tutorAvailabilityButton2.clicked.connect(lambda: self.choose_file("tutor"))

    def show(self) -> None:
        self.window.show()

    def hide(self) -> None:
        self.window.hide()

    def connect_create(self, callback: Callable[[], None]) -> None:
        """ Run `callback` when the Create Timetable button is clicked """
        self.window.CreateTimetableButton.clicked.connect(lambda: callback())

    def set_info_label(self, text: str) -> None:
        """ Set the info label to a given string. No checks done """
        self.window.infoTextLabel.setText(text)

    def choose_file(self, csv_type: str) -> None:
        """ Open a file dialog and store the chosen CSV as the student or tutor file """
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Choose the csv file",
            filter="Data File (*.csv)"
        )

        if not path:
            return          # dialog cancelled

        if csv_type == "student":
            self.student_csv = path
            button = self.window.studentAvailabilityButton
        else:
            self.tutor_csv = path
            button = self.window.tutorAvailabilityButton

        button.setText(path)
        button.setStyleSheet(SELECTED_BUTTON_STYLE)

    def get_files(self) -> tuple[str, str]:
        """ Returns the student CSV and tutor CSV paths ("" if not chosen yet) """
        return self.student_csv, self.tutor_csv
