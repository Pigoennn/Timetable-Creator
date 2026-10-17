import csv
import os
from collections import defaultdict
from collections.abc import Sequence
from typing import TextIO

from src.config import SUBJECTS, Settings
from src.classes.session import EARLY, LATE, TIMES, Session
from src.classes.student import Student
from src.classes.tutor import Availability, Tutor

STUDENT_CSV_HEADERS = "Timestamp,Email Address,First Name,Last Name"
FIRST_DAY_COLUMN = 6        # Timestamp, Email, First Name, Last Name, Year Level, Location, then one column per day

# tutor sheet column headings, used to find the columns instead of hardcoding their positions
TUTOR_NAME_HEADING = "Name"
TUTOR_SUBJECT_HEADING = "Subject"
TUTOR_YEAR_LEVEL_HEADING = "Year Level"
TUTOR_MAXIMUM_HEADING = "What is the maximum number of classes you would like?"
TUTOR_LOCATION_HEADING = "Online or In-Person?"
ROOMS_HEADING = "Rooms:"


class LoaderError(ValueError):
    """ A CSV file could not be turned into students or tutors. The message is shown to the user """


def verify_files(student_csv: str, tutor_csv: str) -> str:
    """ Check the files look like the student and tutor sheets. Returns an error message, or "" if they're fine """
    if not student_csv and not tutor_csv:
        return "Please select your CSV files"
    if not student_csv:
        return "Please select a Student CSV file"
    if not tutor_csv:
        return "Please select a Tutor CSV file"

    for path, verify in ((tutor_csv, _verify_tutor_file), (student_csv, _verify_student_file)):
        try:
            with open(path, newline="", encoding="utf-8-sig") as file:
                error = verify(file)
        except (OSError, UnicodeDecodeError):
            return f"Could not read {os.path.basename(path)}"

        if error:
            return error

    return ""


def _verify_tutor_file(file: TextIO) -> str:
    # the sheet's title cell spans two lines, so a real export always starts like this
    lines = file.read().splitlines()
    if len(lines) < 2 or lines[0] != ',"' or "Tutor Availability" not in lines[1]:
        return "Incorrect Tutor file"
    return ""


def _verify_student_file(file: TextIO) -> str:
    rows = list(csv.reader(file))
    if not rows or STUDENT_CSV_HEADERS not in ",".join(rows[0]):
        return "Incorrect Student file"

    for line_number, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue        # blank line

        if len(row) <= FIRST_DAY_COLUMN:
            return f"Line {line_number} of the Student file is missing columns"

        # every student needs at least two sessions to be given both subjects
        sessions = sum(("Early" in answer) + ("Late" in answer) for answer in row[FIRST_DAY_COLUMN:])
        if sessions < 2:
            return f"Student {row[2]} {row[3]} gave fewer than 2 available sessions"

    return ""


def load_students(student_csv: str, settings: Settings) -> list[Student]:
    """ Read the student form responses. Each day column is matched to settings.student_days in order """
    with open(student_csv, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.reader(file))[1:]       # skip the headings

    students = []
    for line_number, row in enumerate(rows, start=2):
        if not any(row):
            continue        # blank line

        day_answers = row[FIRST_DAY_COLUMN:]
        if len(day_answers) != len(settings.student_days):
            raise LoaderError(f"Line {line_number} of the Student file has {len(day_answers)} day columns "
                              f"but settings.txt has {len(settings.student_days)} student days")

        _, email, first_name, last_name, year_level, location = (cell.strip() for cell in row[:FIRST_DAY_COLUMN])

        # an answer can contain "Early", "Late" or both
        availability = [
            Session(day, time)
            for day, answer in zip(settings.student_days, day_answers)
            for time in TIMES
            if time in answer
        ]

        students.append(Student(email, first_name, last_name, year_level.removeprefix("Year").strip(),
                                location, availability))

    make_names_unique(students)
    return students


def load_tutor_sheet(tutor_csv: str, settings: Settings) -> tuple[list[Tutor], list[str]]:
    """ Read the tutor availability sheet. Returns the tutors and the available rooms """
    with open(tutor_csv, newline="", encoding="utf-8-sig") as file:
        lines = file.read().splitlines()

    # Only parse the sheet from the headings row down, so the title and instructions
    # above it can't throw the parsing off (older generated test files quote them badly)
    heading_index = next((index for index, line in enumerate(lines) if TUTOR_MAXIMUM_HEADING in line), None)
    if heading_index is None:
        raise LoaderError("Could not find the column headings in the Tutor file")
    rows = list(csv.reader(lines[heading_index:]))

    headings = [heading.strip() for heading in rows[0]]
    try:
        name_column = headings.index(TUTOR_NAME_HEADING)
        subject_column = headings.index(TUTOR_SUBJECT_HEADING)
        year_level_column = headings.index(TUTOR_YEAR_LEVEL_HEADING)
        maximum_column = headings.index(TUTOR_MAXIMUM_HEADING)
        location_column = next(index for index, heading in enumerate(headings) if TUTOR_LOCATION_HEADING in heading)
    except (ValueError, StopIteration):
        raise LoaderError("The Tutor file is missing a column heading") from None

    session_columns = _tutor_session_columns(headings[year_level_column + 1:maximum_column], year_level_column + 1)
    missing_days = [day for day in settings.student_days if Session(day, EARLY) not in session_columns]
    if missing_days:
        raise LoaderError(f"The Tutor file has no columns for {', '.join(missing_days)}")

    tutors = []
    rooms = None
    # rows[1] is the session times row
    for row_index, row in enumerate(rows[2:], start=2):
        row = row + [""] * (len(headings) - len(row))       # short rows are missing trailing blanks
        name = row[name_column].strip()

        if ROOMS_HEADING in name:
            if row_index + 1 < len(rows):
                rooms = [room.strip() for room in rows[row_index + 1][name_column].split(",") if room.strip()]
            break

        if not name:
            continue        # spacer row

        tutors.append(_make_tutor(row, name, subject_column, year_level_column, maximum_column,
                                  location_column, session_columns))

    if not rooms:
        raise LoaderError("Could not find the rooms in the Tutor file")
    if not tutors:
        raise LoaderError("The Tutor file has no tutors")

    make_names_unique(tutors)
    return tutors, rooms


def _tutor_session_columns(day_headings: list[str], first_column: int) -> dict[Session, int]:
    """ Map each session to its column. Every day heading covers two columns: early then late """
    session_columns = {}
    day = ""
    for column, heading in enumerate(day_headings, start=first_column):
        if heading:
            day = heading
            time = EARLY
        elif day and Session(day, EARLY) in session_columns and Session(day, LATE) not in session_columns:
            time = LATE
        else:
            raise LoaderError(f"Unexpected column layout in the Tutor file near column {column + 1}")
        session_columns[Session(day, time)] = column

    if any(Session(session.day, LATE) not in session_columns for session in session_columns):
        raise LoaderError("Every day in the Tutor file needs an early and a late column")

    return session_columns


def _make_tutor(row: list[str], name: str, subject_column: int, year_level_column: int, maximum_column: int,
                location_column: int, session_columns: dict[Session, int]) -> Tutor:
    subject = row[subject_column].strip()
    if subject not in SUBJECTS:
        raise LoaderError(f"Tutor {name} has an unknown subject \"{subject}\"")

    year_levels = [year_level.strip() for year_level in row[year_level_column].split("/") if year_level.strip()]
    if not year_levels:
        raise LoaderError(f"Tutor {name} has no year levels")

    try:
        maximum = int(row[maximum_column])
    except ValueError:
        raise LoaderError(f"Tutor {name} has an invalid maximum number of classes") from None

    availability = {session: _parse_availability(row[column]) for session, column in session_columns.items()}

    return Tutor(name, subject, year_levels, availability, maximum, row[location_column].strip())


def _parse_availability(cell: str) -> Availability:
    """ "2" is available, "1" is potentially available, anything else (usually blank) is unavailable """
    try:
        return Availability(int(cell))
    except ValueError:
        return Availability.UNAVAILABLE


def make_names_unique(people: Sequence[Student | Tutor]) -> None:
    """
    Lengthen the last name initial of people sharing a display name until every name is unique,
    e.g. "Nina Miles" and "Nina Mack" become "Nina Mi" and "Nina Ma".
    People who still clash after using their whole last name are numbered instead.
    """
    letters = {person: 1 for person in people}

    while True:
        groups = defaultdict(list)
        for person in people:
            groups[person.name].append(person)

        clashes = [group for group in groups.values() if len(group) > 1]
        if not clashes:
            return

        for group in clashes:
            lengthened = False
            for person in group:
                if letters[person] < len(person.last_name):
                    letters[person] += 1
                    person.name = f"{person.first_name} {person.last_name[:letters[person]]}".rstrip()
                    lengthened = True

            # nobody has any letters left, e.g. two students with the same full name
            if not lengthened:
                for number, person in enumerate(group, start=1):
                    person.name = f"{person.name} ({number})"
