from random import Random

import pytest

from src.classes.solution import Solution
from src.loader import load_students, load_tutor_sheet, verify_files
from testing.testing_creator import NamePicker, load_chances, tutor_availability, write_files


@pytest.fixture
def files(tmp_path):
    write_files(str(tmp_path), 60, seed=3)
    return str(tmp_path / "student.csv"), str(tmp_path / "tutor.csv")


def test_made_files_load_and_solve(files, settings):
    student_csv, tutor_csv = files
    assert verify_files(student_csv, tutor_csv) == ""

    students = load_students(student_csv, settings)
    tutors, rooms = load_tutor_sheet(tutor_csv, settings)
    assert len(students) == 60 and tutors and rooms == ["201", "205", "206", "207", "208"]

    solution = Solution(settings, seed=0)
    solution.setup(students, tutors, rooms)
    solution.execute()
    assert solution.schedule.classes


def test_every_student_can_come_on_two_days(files, settings):
    for student in load_students(files[0], settings):
        assert len({session.day for session in student.availability}) >= 2


def test_same_seed_same_files(tmp_path):
    for folder in ("a", "b"):
        write_files(str(tmp_path / folder), 30, seed=7)
    for name in ("student.csv", "tutor.csv"):
        assert (tmp_path / "a" / name).read_text() == (tmp_path / "b" / name).read_text()


def test_names_are_unique_past_the_name_list():
    names = NamePicker(Random(0))
    picked = [names.pick() for _ in range(1000)]
    assert len(set(picked)) == 1000


@pytest.mark.parametrize("seed", range(50))
def test_tutors_have_two_definite_sessions(seed):
    assert tutor_availability(Random(seed)).count("2") >= 2


def test_chances_add_up_to_100():
    for section, chances in load_chances().items():
        assert sum(chances.values()) == 100, section
