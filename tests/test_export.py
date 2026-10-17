import csv
from dataclasses import replace
from datetime import datetime

from src.classes.schedule import ONLINE, Schedule
from src.classes.session import EARLY, LATE, Session
from src.classes.student import Student
from src.classes.timetable_class import Class
from src.classes.tutor import Availability
from src.export import errors_report, timetable_rows, unplaced_reason, write_timetable
from tests.conftest import TEMPLATE, make_tutor

OLD_EXPORT = TEMPLATE / "timetable.csv"     # a timetable the old app exported, as it looks in Google Sheets
ROOMS = ["201", "205", "206", "207", "208"]
SUBJECT_CODES = {"MAT": "Maths", "ENG": "English"}

TUESDAY_EARLY = Session("Tuesday", EARLY)
SATURDAY_LATE = Session("Saturday", LATE)


def read_rows(path) -> list[list[str]]:
    with open(path, newline="") as file:
        return list(csv.reader(file))


def schedule_from_export(rows: list[list[str]], settings) -> Schedule:
    """ Rebuild the classes from an exported timetable """
    schedule = Schedule(list(ROOMS))
    tutors = {}
    block_height = 5 + settings.class_size

    for day in settings.student_days:
        day_row = next(index for index, row in enumerate(rows) if row[1] == day)

        for offset, time in enumerate((EARLY, LATE)):
            top = day_row + 2 + offset * block_height
            block = rows[top:top + block_height]
            assert block[0][0] == time

            for column in range(1, len(block[0])):
                name, tutor_name, class_time, room, class_type, *student_names = [row[column] for row in block]
                if not name:
                    continue

                # physical rooms always sit in their own column
                if room != ONLINE:
                    assert column == 1 + ROOMS.index(room)

                classroom = Class(Session(day, time), room, online=room == ONLINE)
                classroom.name = name
                classroom.subject = SUBJECT_CODES[name.split()[1]]
                classroom.year_level = class_type.removeprefix("Normal ")
                classroom.tutor = tutors.setdefault(tutor_name, make_tutor(tutor_name, classroom.subject, [], {}))
                assert class_time == settings.class_time(day, classroom.subject, time)

                for student_name in filter(None, student_names):
                    online = student_name.endswith(" (OL)")
                    student = Student("", "", "", classroom.year_level, ONLINE if online else "In-Person", [])
                    student.name = student_name.removesuffix(" (OL)")
                    classroom.students.append(student)

                schedule.classes.append(classroom)

    return schedule


def test_reproduces_the_old_export(settings, tmp_path):
    expected = read_rows(OLD_EXPORT)
    schedule = schedule_from_export(expected, settings)
    assert len(schedule.classes) == 48

    write_timetable(str(tmp_path / "timetable.csv"), schedule, settings)

    assert read_rows(tmp_path / "timetable.csv") == expected


def test_lines_match_the_template(settings, tmp_path):
    write_timetable(str(tmp_path / "timetable.csv"), Schedule(list(ROOMS)), settings)
    text = (tmp_path / "timetable.csv").read_bytes()

    # Google Sheets exports with CRLF too
    assert text.count(b"\r\n") == len(read_rows(OLD_EXPORT))


def make_class(session, room, subject="Maths", year_level="8", students=(), name="SEL MAT 8A") -> Class:
    classroom = Class(session, room, online=room == ONLINE)
    classroom.subject = subject
    classroom.year_level = year_level
    classroom.name = name
    classroom.tutor = make_tutor("Tim Tutor", subject, [year_level], {})
    for student in students:
        classroom.add_student(student)
    return classroom


def column(rows, session, column_index, settings):
    day_row = next(index for index, row in enumerate(rows) if row[1] == session.day)
    top = day_row + 2 + (0 if session.time == EARLY else 5 + settings.class_size)
    return [row[column_index] for row in rows[top:top + 5 + settings.class_size]]


def test_class_column(settings):
    online_student = Student("", "Ann", "Lee", "8", ONLINE, [SATURDAY_LATE])
    student = Student("", "Bo", "Kim", "8", "In-Person", [SATURDAY_LATE])
    schedule = Schedule(["201", "205"])
    schedule.classes.append(make_class(SATURDAY_LATE, "205", "English", students=[online_student, student],
                                       name="SEL ENG 8A"))

    rows = timetable_rows(schedule, settings)

    assert column(rows, SATURDAY_LATE, 1, settings) == ["", "", "", "", "", "", "", "", "", ""]
    assert column(rows, SATURDAY_LATE, 2, settings) == ["SEL ENG 8A", "Tim T", "2:00 - 4:00 pm", "205", "Normal 8",
                                                        "Ann L (OL)", "Bo K", "", "", ""]


def test_online_classes_come_after_the_rooms(settings):
    schedule = Schedule(["201", "205"])
    schedule.classes += [make_class(TUESDAY_EARLY, ONLINE, name="SEL MAT 8A"),
                         make_class(TUESDAY_EARLY, ONLINE, name="SEL MAT 8B"),
                         make_class(TUESDAY_EARLY, "201", name="SEL MAT 8C")]

    rows = timetable_rows(schedule, settings)
    header = next(index for index, row in enumerate(rows) if row[1] == "Tuesday") + 1

    assert rows[header] == ["", "In-Person", "", "Online", ""]
    assert rows[header + 1] == ["Early", "SEL MAT 8C", "", "SEL MAT 8A", "SEL MAT 8B"]
    assert all(len(row) == 5 for row in rows)


def test_rows_follow_the_class_size(settings):
    small = timetable_rows(Schedule(list(ROOMS)), replace(settings, class_size=3))
    normal = timetable_rows(Schedule(list(ROOMS)), settings)

    days = len(settings.student_days)
    assert len(normal) - len(small) == days * 2 * 2


# --- Errors.txt ---------------------------------------------------------------

def test_errors_report(settings):
    year_5 = Student("ann@example.com", "Ann", "Lee Smith", "5", "Online", [TUESDAY_EARLY, SATURDAY_LATE])
    year_5.unplaceable = {"Maths", "English"}
    placed = Student("bo@example.com", "Bo", "Kim", "8", "In-Person", [TUESDAY_EARLY])

    english_tutor = make_tutor("Eve English", "English", ["5"], {SATURDAY_LATE: Availability.POTENTIAL})
    report = errors_report([year_5, placed], [english_tutor], datetime(2026, 10, 17, 14, 3, 9))

    assert report == (
        "Timetable created 17/10/2026 14:03:09\n"
        "Students who did not receive a class: 1\n"
        "\n"
        "(Maths, English)\n"
        "Ann Lee Smith\n"
        "ann@example.com\n"
        "Year 5\n"
        "Attendance Method: Online\n"
        "Availabilities: Early Tuesday, Late Saturday\n"
        "Maths: No tutor teaches Year 5 Maths\n"
        "English: The Year 5 English classes and tutors at their times were all taken\n"
    )


def test_errors_report_with_everyone_placed():
    report = errors_report([], [], datetime(2026, 1, 2, 3, 4, 5))
    assert report == "Timetable created 02/01/2026 03:04:05\nStudents who did not receive a class: 0\n"


def test_unplaced_reason_when_the_tutors_are_busy_at_other_times():
    student = Student("", "Ann", "Lee", "8", "In-Person", [TUESDAY_EARLY])
    tutor = make_tutor("Tim Tutor", "Maths", ["8"], {TUESDAY_EARLY: Availability.UNAVAILABLE,
                                                    SATURDAY_LATE: Availability.AVAILABLE})

    assert unplaced_reason(student, "Maths", [tutor]) == "No Year 8 Maths tutor is available at their times"
