"""
Writes the finished timetable to a CSV in the layout of the Google Sheets timetable template,
and the students who couldn't be placed to Errors.txt.
"""
import csv
from datetime import datetime

from src.classes.schedule import ONLINE, Schedule
from src.classes.session import TIMES, Session
from src.classes.student import Student
from src.classes.timetable_class import Class
from src.classes.tutor import Availability, Tutor
from src.config import Settings

CLASS_HEADER_ROWS = 5           # name, tutor, time, room, class type; the students go underneath
ONLINE_STUDENT_SUFFIX = " (OL)"
MONDAY_ROWS = 5                 # empty rows under each Monday session


# --- timetable.csv ------------------------------------------------------------

def write_timetable(path: str, schedule: Schedule, settings: Settings) -> None:
    with open(path, "w", newline="") as file:
        csv.writer(file).writerows(timetable_rows(schedule, settings))


def timetable_rows(schedule: Schedule, settings: Settings) -> list[list[str]]:
    """
    Column A labels the sessions. Each physical room has its own column after that, in the order
    of the tutor sheet, and the online classes follow. Every row is padded to the same width.
    """
    block_height = CLASS_HEADER_ROWS + settings.class_size

    # the Monday workshops box and colour legend are filled in by hand
    rows = [[], [], ["", "Monday (Workshops)", "", "", "Colour Legend"]]
    rows += [["Early"]] + [[] for _ in range(MONDAY_ROWS)]
    rows += [["Late"]] + [[] for _ in range(MONDAY_ROWS)]

    for day in settings.student_days:
        rows += [[], [], ["", day], ["", "In-Person"] + [""] * (len(schedule.rooms) - 1) + ["Online"]]

        for time in TIMES:
            session = Session(day, time)
            block = [[time]] + [[""] for _ in range(block_height - 1)]

            for classroom in schedule.rooms_at(session) + schedule.online_at(session):
                cells = class_cells(classroom, settings) if classroom else [""] * block_height
                for row, cell in zip(block, cells):
                    row.append(cell)

            rows += block

    width = max(len(row) for row in rows)
    return [row + [""] * (width - len(row)) for row in rows]


def class_cells(classroom: Class, settings: Settings) -> list[str]:
    """ One class's column, top to bottom """
    session = classroom.session
    students = [student.name + (ONLINE_STUDENT_SUFFIX if student.location == ONLINE else "")
                for student in classroom.students]

    return [
        classroom.name,
        classroom.tutor.name,
        settings.class_time(session.day, classroom.subject, session.time),
        ONLINE if classroom.online else classroom.room,
        f"Normal {classroom.year_level}",
    ] + students + [""] * (settings.class_size - len(students))


# --- Errors.txt ---------------------------------------------------------------

def write_errors(path: str, students: list[Student], tutors: list[Tutor], created: datetime) -> None:
    with open(path, "w") as file:
        file.write(errors_report(students, tutors, created))


def errors_report(students: list[Student], tutors: list[Tutor], created: datetime) -> str:
    unplaced = [student for student in students if student.unplaceable]

    lines = [f"Timetable created {created:%d/%m/%Y %H:%M:%S}",
             f"Students who did not receive a class: {len(unplaced)}", ""]

    for student in unplaced:
        subjects = [subject for subject in student.classes if subject in student.unplaceable]
        lines += [
            f"({', '.join(subjects)})",
            f"{student.first_name} {student.last_name}",
            student.email,
            f"Year {student.year_level}",
            f"Attendance Method: {student.location}",
            f"Availabilities: {', '.join(str(session) for session in student.availability)}",
        ]
        lines += [f"{subject}: {unplaced_reason(student, subject, tutors)}" for subject in subjects]
        lines.append("")

    return "\n".join(lines)


def unplaced_reason(student: Student, subject: str, tutors: list[Tutor]) -> str:
    cohort = f"Year {student.year_level} {subject}"
    teachers = [tutor for tutor in tutors if tutor.subject == subject and student.year_level in tutor.year_levels]

    if not teachers:
        return f"No tutor teaches {cohort}"
    if not any(tutor.availability_at(session) != Availability.UNAVAILABLE
               for tutor in teachers for session in student.availability):
        return f"No {cohort} tutor is available at their times"
    return f"The {cohort} classes and tutors at their times were all taken"
