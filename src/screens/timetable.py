import os
from datetime import datetime
from typing import Callable
from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QAbstractItemView, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QWidget)

from src.classes.schedule import ONLINE
from src.classes.session import TIMES, Session
from src.classes.solution import Solution
from src.classes.timetable_class import Class
from src.config import Settings
from src.export import display_name, write_errors, write_timetable

class TimetableScreen(QWidget):
    """ The finished timetable: a row for each session and a column for each room, then the online classes """

    solution: Solution
    settings: Settings
    save_folder: str                        # where the save dialogs start
    created: datetime

    sessions: list[Session]                 # one per row
    cells: dict[tuple[int, int], Class]     # (row, column) -> the class shown there

    def __init__(self, solution: Solution, settings: Settings, save_folder: str, created: datetime) -> None:
        super().__init__()
        self.solution = solution
        self.settings = settings
        self.save_folder = save_folder
        self.created = created

        self.setWindowTitle("Timetable")
        self.resize(920, 480)

        self.create_table()

        self.details = QLabel("")
        self.details.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.details.setMinimumWidth(180)

        self.status = QLabel(self.missing_summary())

        self.errors_button = self.create_button("Save Errors.txt", "Save the students who didn't get a class",
                                                self.save_errors)
        self.csv_button = self.create_button("Download as CSV", "Download the timetable into a csv",
                                             self.save_timetable)
        self.csv_button.setProperty("primary", True)

        buttons = QHBoxLayout()
        buttons.addWidget(self.status, stretch=1)
        buttons.addWidget(self.errors_button)
        buttons.addWidget(self.csv_button)

        grid = QGridLayout()
        grid.addWidget(self.table, 0, 0)
        grid.addWidget(self.details, 0, 1)
        grid.addLayout(buttons, 1, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        self.setLayout(grid)

    # --- the table ------------------------------------------------------------

    def create_table(self) -> None:
        schedule = self.solution.schedule
        self.sessions = [Session(day, time) for day in self.settings.student_days for time in TIMES]
        online_columns = max((len(schedule.online_at(session)) for session in self.sessions), default=0)

        self.table = QTableWidget(len(self.sessions), len(schedule.rooms) + online_columns)
        self.table.setHorizontalHeaderLabels(schedule.rooms + [ONLINE] * online_columns)
        self.table.setVerticalHeaderLabels([f"{session.day} {session.time}" for session in self.sessions])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setDragEnabled(False)
        self.table.setAlternatingRowColors(True)

        self.cells = {}
        for row, session in enumerate(self.sessions):
            self.table.setRowHeight(row, 40)
            for column, classroom in enumerate(schedule.rooms_at(session) + schedule.online_at(session)):
                if classroom is None:
                    continue
                item = QTableWidgetItem(classroom.name)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
                self.cells[(row, column)] = classroom

        for column in range(self.table.columnCount()):
            self.table.setColumnWidth(column, 100)

        self.table.currentCellChanged.connect(lambda row, column, *_: self.show_details(row, column))

    def show_details(self, row: int, column: int) -> None:
        """ Show the class in the cell beside the table, or nothing for an empty cell """
        classroom = self.cells.get((row, column))
        self.details.setText(class_details(classroom, self.settings) if classroom else "")

    # --- saving ---------------------------------------------------------------

    def missing_summary(self) -> str:
        missing = sum(1 for student in self.solution.students if student.unplaceable)
        if missing == 0:
            return "Every student has their classes"
        return f"{missing} student{'s' if missing != 1 else ''} did not get every class (see Errors.txt)"

    def save_timetable(self) -> None:
        path = self.ask_save_path("Save the timetable", "timetable.csv", "CSV File (*.csv)")
        if path:
            self.save(path, lambda: write_timetable(path, self.solution.schedule, self.settings))

    def save_errors(self) -> None:
        path = self.ask_save_path("Save the errors", "Errors.txt", "Text File (*.txt)")
        if path:
            self.save(path, lambda: write_errors(path, self.solution.students, self.solution.tutors, self.created))

    def ask_save_path(self, title: str, file_name: str, file_filter: str) -> str:
        """ The chosen path, or "" if the dialog was cancelled """
        path, _ = QFileDialog.getSaveFileName(self, title, os.path.join(self.save_folder, file_name), file_filter)
        return path

    def save(self, path: str, write: Callable[[], None]) -> None:
        try:
            write()
        except OSError as error:
            self.status.setText(f"Could not save {os.path.basename(path)}: {error.strerror}")
            return
        self.save_folder = os.path.dirname(path)
        self.status.setText(f"Saved {os.path.basename(path)}")

    @staticmethod
    def create_button(text: str, tooltip: str, callback: Callable[[], None]) -> QPushButton:
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: callback())
        return button


def class_details(classroom: Class, settings: Settings) -> str:
    """ Rich text describing a class, for the label beside the table """
    session = classroom.session

    lines = [
        f"<h3>{escape(classroom.name)}</h3>",
        f"<h4>{session.day}<br>{settings.class_time(session.day, classroom.subject, session.time)}</h4>",
        f"<p>Year {escape(classroom.year_level)} {classroom.subject}<br>"
        f"Tutor: {escape(classroom.tutor.name)}<br>"
        f"Room: {escape(ONLINE if classroom.online else classroom.room)}</p>",
        f"<p><b>Students ({len(classroom.students)}/{settings.class_size})</b><br>"
        + "<br>".join(escape(display_name(student)) for student in classroom.students) + "</p>",
    ]
    return "\n".join(lines)
