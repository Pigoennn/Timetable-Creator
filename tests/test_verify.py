import pytest

from src.loader import verify_files
from tests.conftest import TEST1, TEST2

STUDENTS = str(TEST1 / "student.csv")
TUTORS = str(TEST1 / "tutor.csv")


@pytest.mark.parametrize("student_csv, tutor_csv, message", [
    ("", "", "Please select your CSV files"),
    ("", TUTORS, "Please select a Student CSV file"),
    (STUDENTS, "", "Please select a Tutor CSV file"),
    (STUDENTS, STUDENTS, "Incorrect Tutor file"),
    (TUTORS, TUTORS, "Incorrect Student file"),
    ("missing.csv", TUTORS, "Could not read missing.csv"),
])
def test_bad_files(student_csv, tutor_csv, message):
    assert verify_files(student_csv, tutor_csv) == message


@pytest.mark.parametrize("student_csv", [STUDENTS, str(TEST2 / "funnystudents.csv")])
def test_good_files(student_csv):
    assert verify_files(student_csv, TUTORS) == ""


def test_student_with_one_session(write_students):
    path = write_students("t,a@b.c,Lonely,Student,Year 8,In-Person,Early,,,,")
    assert verify_files(path, TUTORS) == "Student Lonely Student gave fewer than 2 available sessions"


def test_one_day_with_both_sessions_is_enough(write_students):
    path = write_students("t,a@b.c,Busy,Student,Year 8,In-Person,,,EarlyLate,,")
    assert verify_files(path, TUTORS) == ""


def test_short_student_row(write_students):
    assert verify_files(write_students("t,a@b.c,Ann"), TUTORS) == "Line 2 of the Student file is missing columns"
