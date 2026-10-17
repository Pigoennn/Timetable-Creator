from dataclasses import replace

import pytest

from src.classes.schedule import ONLINE
from src.classes.session import EARLY, LATE, Session
from src.classes.solution import Solution
from src.classes.student import Student
from src.classes.tutor import Availability
from src.config import SUBJECTS
from src.loader import load_students, load_tutor_sheet
from tests.conftest import TEST1, TEST2, make_tutor

AVAILABLE = Availability.AVAILABLE
POTENTIAL = Availability.POTENTIAL

TUESDAY_EARLY = Session("Tuesday", EARLY)
TUESDAY_LATE = Session("Tuesday", LATE)
WEDNESDAY_EARLY = Session("Wednesday", EARLY)


def make_student(name: str, availability: list[Session], year_level: str = "8", location: str = "In-Person") -> Student:
    return Student("", name, "X", year_level, location, availability)


def setup(settings, students, tutors, rooms=("201", "205")) -> Solution:
    solution = Solution(settings, seed=0)
    solution.setup(students, tutors, list(rooms))
    return solution


# --- the test data ------------------------------------------------------------

@pytest.fixture(params=[(TEST1 / "student.csv", seed) for seed in range(5)]
                + [(TEST2 / "funnystudents.csv", seed) for seed in range(5)],
                ids=lambda param: f"{param[0].parent.name}-seed{param[1]}")
def solution(request, settings) -> Solution:
    student_csv, seed = request.param
    students = load_students(str(student_csv), settings)
    tutors, rooms = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)

    solution = Solution(settings, seed)
    solution.setup(students, tutors, rooms)
    solution.execute()
    return solution


def placements(solution):
    return [(student, classroom) for classroom in solution.schedule.classes for student in classroom.students]


def test_students_are_available_for_their_classes(solution):
    for student, classroom in placements(solution):
        assert student.is_available(classroom.session)


def test_students_have_one_class_at_a_time(solution):
    for student in solution.students:
        sessions = [classroom.session for classroom in student.classes.values() if classroom is not None]
        assert len(sessions) == len(set(sessions)), student.name


def test_classes_are_not_over_full(solution):
    for classroom in solution.schedule.classes:
        assert 1 <= len(classroom.students) <= solution.settings.class_size


def test_classes_match_the_students(solution):
    for student, classroom in placements(solution):
        assert classroom.year_level == student.year_level
        assert student.classes[classroom.subject] is classroom


def test_every_class_a_student_has_is_in_the_schedule(solution):
    for student in solution.students:
        for subject, classroom in student.classes.items():
            if classroom is not None:
                assert classroom in solution.schedule.classes
                assert student in classroom.students
                assert classroom.subject == subject


def test_every_student_is_placed_or_unplaceable(solution):
    for student in solution.students:
        for subject in SUBJECTS:
            assert (student.classes[subject] is None) == (subject in student.unplaceable), (student.name, subject)


def test_tutor_rules_still_hold_with_backup_classes(solution):
    for tutor in solution.tutors:
        sessions = [classroom.session for classroom in tutor.classes]
        assert len(tutor.classes) <= tutor.maximum
        assert len(sessions) == len(set(sessions))
        assert all(tutor.availability_at(session) in (AVAILABLE, POTENTIAL) for session in sessions)
        assert all(classroom in solution.schedule.classes for classroom in tutor.classes)


def test_unplaced_students_really_have_no_option(solution):
    """ Nobody is left out while a class has room for them or a tutor could teach them """
    for student in solution.students:
        free_sessions = [session for session in student.availability if not student.is_booked(session)]

        for subject in student.unplaceable:
            for classroom in solution.schedule.classes:
                if (classroom.subject == subject and classroom.year_level == student.year_level
                        and classroom.session in free_sessions):
                    assert len(classroom.students) == solution.settings.class_size

            for tutor in solution.tutors:
                if tutor.subject == subject and student.year_level in tutor.year_levels and not tutor.is_full():
                    assert not any(tutor.availability_at(session) in (AVAILABLE, POTENTIAL)
                                   and not tutor.is_booked(session)
                                   for session in free_sessions)


def test_only_impossible_students_are_left_out(solution):
    # the test data has tutors for everything except year 5 maths
    unplaced = {(student.year_level, subject) for student in solution.students for subject in student.unplaceable}
    assert unplaced <= {("5", "Maths")}


# --- small cases --------------------------------------------------------------

def test_students_with_fewer_options_keep_their_seat(settings):
    # one seat per class. Bo asks for Tuesday first but can also do Wednesday, Ann can only do Tuesday
    tutor = make_tutor("Tim Tutor", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE, WEDNESDAY_EARLY: AVAILABLE})
    bo = make_student("Bo", [TUESDAY_EARLY, WEDNESDAY_EARLY])
    ann = make_student("Ann", [TUESDAY_EARLY])
    solution = setup(replace(settings, class_size=1), [bo, ann], [tutor])
    tuesday = solution.schedule.create_class(tutor, TUESDAY_EARLY, "Maths", "8")
    wednesday = solution.schedule.create_class(tutor, WEDNESDAY_EARLY, "Maths", "8")

    solution.place_students()

    assert ann.classes["Maths"] is tuesday
    assert bo.classes["Maths"] is wednesday


def test_students_prefer_classes_matching_how_they_attend(settings):
    in_person_tutor = make_tutor("Tim Tutor", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE})
    online_tutor = make_tutor("Olly Online", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE}, location=ONLINE)
    online_student = make_student("Bo", [TUESDAY_EARLY], location=ONLINE)
    in_person_student = make_student("Ann", [TUESDAY_EARLY])
    solution = setup(settings, [online_student, in_person_student], [in_person_tutor, online_tutor])
    in_person = solution.schedule.create_class(in_person_tutor, TUESDAY_EARLY, "Maths", "8")
    online = solution.schedule.create_class(online_tutor, TUESDAY_EARLY, "Maths", "8")

    solution.place_students()

    assert online_student.classes["Maths"] is online
    assert in_person_student.classes["Maths"] is in_person


def test_first_subject_leaves_room_for_the_second(settings):
    # the online maths class suits the online student better, but it's on the only english day
    online_tutor = make_tutor("Olly Online", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE}, location=ONLINE)
    maths_tutor = make_tutor("Tim Tutor", "Maths", ["8"], {WEDNESDAY_EARLY: AVAILABLE})
    english_tutor = make_tutor("Eve English", "English", ["8"], {TUESDAY_EARLY: AVAILABLE})
    student = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY], location=ONLINE)
    solution = setup(settings, [student], [online_tutor, maths_tutor, english_tutor])
    solution.schedule.create_class(online_tutor, TUESDAY_EARLY, "Maths", "8")
    solution.schedule.create_class(maths_tutor, WEDNESDAY_EARLY, "Maths", "8")
    solution.schedule.create_class(english_tutor, TUESDAY_EARLY, "English", "8")

    solution.place_students()

    assert student.classes["Maths"].session == WEDNESDAY_EARLY
    assert student.classes["English"].session == TUESDAY_EARLY


def test_backup_class_for_students_left_over(settings):
    tutor = make_tutor("Tim Tutor", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE, TUESDAY_LATE: POTENTIAL})
    students = [make_student(f"S{number}", [TUESDAY_EARLY, TUESDAY_LATE]) for number in range(7)]
    solution = setup(replace(settings, class_size=5), students, [tutor])
    solution.schedule.create_class(tutor, TUESDAY_EARLY, "Maths", "8")

    solution.place_students()
    assert sum(student.needs_class("Maths") for student in students) == 2

    solution.create_backup_classes()

    assert [classroom.session for classroom in tutor.classes] == [TUESDAY_EARLY, TUESDAY_LATE]
    assert all(student.classes["Maths"] is not None for student in students)


def test_backup_seats_go_to_students_with_fewer_options(settings):
    tutor = make_tutor("Tim Tutor", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE}, maximum=1)
    flexible = make_student("Bo", [TUESDAY_EARLY, WEDNESDAY_EARLY])
    stuck = make_student("Ann", [TUESDAY_EARLY])
    solution = setup(replace(settings, class_size=1), [flexible, stuck], [tutor])

    solution.fill_gaps()

    assert stuck.classes["Maths"] is not None
    assert flexible.unplaceable == {"Maths", "English"}


def test_empty_classes_are_removed_and_free_their_tutor(settings):
    # the tutor's only class is at a time nobody can make, but their other slot works for a backup class
    tutor = make_tutor("Tim Tutor", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE, WEDNESDAY_EARLY: AVAILABLE}, maximum=1)
    student = make_student("Ann", [WEDNESDAY_EARLY])
    solution = setup(settings, [student], [tutor])
    empty = solution.schedule.create_class(tutor, TUESDAY_EARLY, "Maths", "8")

    solution.place_students()
    solution.create_backup_classes()

    assert empty not in solution.schedule.classes
    assert [classroom.session for classroom in tutor.classes] == [WEDNESDAY_EARLY]
    assert student.classes["Maths"] is tutor.classes[0]


def test_unplaceable_when_no_tutor_is_free(settings):
    tutor = make_tutor("Tim Tutor", "Maths", ["8"], {WEDNESDAY_EARLY: AVAILABLE})
    student = make_student("Ann", [TUESDAY_EARLY])
    solution = setup(settings, [student], [tutor])

    solution.fill_gaps()

    assert solution.schedule.classes == []
    assert student.unplaceable == {"Maths", "English"}
