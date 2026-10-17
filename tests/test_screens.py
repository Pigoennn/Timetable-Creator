import os
import time
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")      # no real windows while testing

import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog

import main as app_main
from src.classes.session import TIMES, Session
from src.classes.solution import Solution
from src.export import errors_report, timetable_rows
from src.loader import load_students, load_tutor_sheet
from src.resources import resource_path
from src.screens.loading import LoadingScreen
from src.screens.start import StartScreen
from src.screens.timetable import TimetableScreen, class_details
from tests.conftest import TEST1
from tests.test_export import read_rows

CREATED = datetime(2026, 10, 17, 9, 30)


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def solution(settings) -> Solution:
    tutors, rooms = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)
    solution = Solution(settings, seed=0)
    solution.setup(load_students(str(TEST1 / "student.csv"), settings), tutors, rooms)
    solution.execute()
    return solution


@pytest.fixture
def screen(app, solution, settings, tmp_path) -> TimetableScreen:
    return TimetableScreen(solution, settings, str(tmp_path), CREATED)


def wait_until(app: QApplication, condition, timeout: float = 10) -> None:
    """ Run the event loop until the condition is true """
    end = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < end, "timed out"
        app.processEvents()
        time.sleep(0.01)


def answer_save_dialog(monkeypatch, path) -> list:
    """ Make the save dialog choose `path` ("" = cancel). Returns the default paths it was opened with """
    opened = []
    def fake_dialog(parent, title, default, file_filter):
        opened.append(default)
        return str(path), file_filter
    monkeypatch.setattr(QFileDialog, "getSaveFileName", fake_dialog)
    return opened


# --- progress -----------------------------------------------------------------

def test_execute_reports_progress(settings):
    tutors, rooms = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)
    solution = Solution(settings, seed=0)
    solution.setup(load_students(str(TEST1 / "student.csv"), settings), tutors, rooms)

    reports = []
    solution.execute(lambda percent, message: reports.append((percent, message)))

    percents = [percent for percent, _ in reports]
    assert percents == sorted(percents)
    assert reports[0] == (0, "Creating classes") and reports[-1] == (100, "Done")
    assert {"Placing Maths students", "Placing English students", "Tidying up"} <= {message for _, message in reports}
    assert len(reports) == len(set(reports))


def test_loading_screen_shows_progress(app):
    loading = LoadingScreen(resource_path("src/ui_files/loading_screen.ui"))
    loading.set_progress(42, "Placing Maths students")

    assert loading.window.progressBar.value() == 42
    assert loading.window.label.text() == "Placing Maths students"


# --- the timetable screen -----------------------------------------------------

def test_table_matches_the_export_layout(screen, solution, settings):
    # the same columns as the csv: rooms in order, then online classes
    sessions = [Session(day, time) for day in settings.student_days for time in TIMES]
    assert [screen.table.verticalHeaderItem(row).text() for row in range(screen.table.rowCount())] == \
        [f"{session.day} {session.time}" for session in sessions]

    for row, session in enumerate(sessions):
        columns = solution.schedule.rooms_at(session) + solution.schedule.online_at(session)
        for column in range(screen.table.columnCount()):
            item = screen.table.item(row, column)
            classroom = columns[column] if column < len(columns) else None
            assert (item.text() if item else None) == (classroom.name if classroom else None)


def test_every_class_is_shown_once(screen, solution):
    assert sorted(screen.cells.values(), key=id) == sorted(solution.schedule.classes, key=id)


def test_headers(screen, solution):
    headers = [screen.table.horizontalHeaderItem(column).text() for column in range(screen.table.columnCount())]
    rooms = len(solution.schedule.rooms)
    assert headers[:rooms] == solution.schedule.rooms
    assert set(headers[rooms:]) == {"Online"}


def test_selecting_a_class_shows_its_details(screen, settings):
    (row, column), classroom = next(iter(screen.cells.items()))

    screen.table.setCurrentCell(row, column)

    assert screen.details.text() == class_details(classroom, settings)
    assert classroom.tutor.name in screen.details.text()
    assert all(student.name in screen.details.text() for student in classroom.students)


def test_selecting_an_empty_cell_clears_the_details(screen):
    (row, column), _ = next(iter(screen.cells.items()))
    empty = next((r, c) for r in range(screen.table.rowCount()) for c in range(screen.table.columnCount())
                 if (r, c) not in screen.cells)

    screen.table.setCurrentCell(row, column)
    screen.table.setCurrentCell(*empty)

    assert screen.details.text() == ""


def test_class_details_escape_names(solution, settings):
    classroom = solution.schedule.classes[0]
    classroom.students[0].name = "<b>Bo</b>"

    assert "&lt;b&gt;Bo&lt;/b&gt;" in class_details(classroom, settings)


def test_summary_counts_missing_students(screen):
    assert screen.status.text() == "5 students did not get every class (see Errors.txt)"


def test_download_csv(screen, solution, settings, monkeypatch, tmp_path):
    path = tmp_path / "out" / "my timetable.csv"
    path.parent.mkdir()
    opened = answer_save_dialog(monkeypatch, path)

    screen.csv_button.click()

    assert opened == [str(tmp_path / "timetable.csv")]
    assert read_rows(path) == timetable_rows(solution.schedule, settings)
    assert screen.status.text() == "Saved my timetable.csv"
    assert screen.save_folder == str(path.parent)


def test_save_errors(screen, solution, monkeypatch, tmp_path):
    answer_save_dialog(monkeypatch, tmp_path / "Errors.txt")

    screen.errors_button.click()

    assert (tmp_path / "Errors.txt").read_text() == errors_report(solution.students, solution.tutors, CREATED)


def test_cancelled_save_writes_nothing(screen, monkeypatch, tmp_path):
    answer_save_dialog(monkeypatch, "")

    screen.csv_button.click()

    assert list(tmp_path.iterdir()) == []
    assert screen.status.text().startswith("5 students")


def test_save_failure_is_reported(screen, monkeypatch, tmp_path):
    answer_save_dialog(monkeypatch, tmp_path / "missing folder" / "timetable.csv")

    screen.csv_button.click()

    assert screen.status.text().startswith("Could not save timetable.csv")


# --- the whole app ------------------------------------------------------------

@pytest.fixture
def controller(app, settings):
    start = StartScreen(resource_path("src/ui_files/start_screen.ui"))
    loading = LoadingScreen(resource_path("src/ui_files/loading_screen.ui"))
    controller = app_main.Main(settings, start, loading)
    start.show()
    yield controller

    if controller.thread is not None:
        controller.thread.wait()
    for window in (start.window, loading.window, controller.timetable_screen):
        if window is not None:
            window.close()


def choose_files(controller, student_csv, tutor_csv) -> None:
    controller.start_screen.student_csv = str(student_csv)
    controller.start_screen.tutor_csv = str(tutor_csv)


def test_create_shows_the_timetable(app, controller):
    choose_files(controller, TEST1 / "student.csv", TEST1 / "tutor.csv")

    controller.start_screen.window.CreateTimetableButton.click()
    assert not controller.start_screen.window.isVisible()
    wait_until(app, lambda: controller.timetable_screen is not None)

    assert controller.timetable_screen.isVisible()
    assert not controller.loading_screen.window.isVisible()
    assert controller.loading_screen.window.progressBar.value() == 100
    assert controller.timetable_screen.save_folder == str(TEST1)
    assert len(controller.timetable_screen.cells) == len(controller.solution.schedule.classes) > 0


def test_bad_files_stay_on_the_start_screen(app, controller):
    choose_files(controller, TEST1 / "tutor.csv", TEST1 / "tutor.csv")

    controller.create_timetable()

    assert controller.start_screen.window.infoTextLabel.text() == "Incorrect Student file"
    assert controller.thread is None
    assert controller.start_screen.window.isVisible()


def test_a_crash_goes_back_to_the_start_screen(app, controller, monkeypatch):
    def crash(self, progress=None):
        raise RuntimeError("boom")
    monkeypatch.setattr(Solution, "execute", crash)
    choose_files(controller, TEST1 / "student.csv", TEST1 / "tutor.csv")

    controller.create_timetable()
    wait_until(app, lambda: controller.start_screen.window.isVisible())

    assert controller.start_screen.window.infoTextLabel.text() == "Something went wrong making the timetable: boom"
    assert not controller.loading_screen.window.isVisible()
    assert controller.timetable_screen is None
