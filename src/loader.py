import csv
import os
from typing import TextIO

STUDENT_CSV_HEADERS = "Timestamp,Email Address,First Name,Last Name"
FIRST_DAY_COLUMN = 6        # Timestamp, Email, First Name, Last Name, Year Level, Location, then one column per day


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
