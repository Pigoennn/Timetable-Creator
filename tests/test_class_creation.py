from collections import Counter
from dataclasses import replace

import pytest

from src.classes.schedule import ONLINE
from src.classes.session import EARLY, LATE, Session
from src.classes.solution import Solution, relaxation_ladder
from src.classes.student import Student
from src.classes.tutor import Availability, Tutor
from src.loader import load_students, load_tutor_sheet
from tests.conftest import TEST1, TEST2

AVAILABLE = Availability.AVAILABLE
POTENTIAL = Availability.POTENTIAL

TUESDAY_EARLY = Session("Tuesday", EARLY)
TUESDAY_LATE = Session("Tuesday", LATE)
WEDNESDAY_EARLY = Session("Wednesday", EARLY)


def make_tutor(name: str, subject: str, year_levels: list[str], availability: dict[Session, Availability],
               maximum: int = 4, location: str = "In-Person") -> Tutor:
    return Tutor(name, subject, year_levels, availability, maximum, location)


def make_students(count: int, year_level: str, availability: list[Session]) -> list[Student]:
    return [Student("", f"Student{number}", "X", year_level, "In-Person", list(availability)) for number in range(count)]


def create(settings, students, tutors, rooms=("201",), seed=0) -> Solution:
    solution = Solution(settings, seed)
    solution.setup(students, tutors, list(rooms))
    solution.create_classes()
    return solution


# --- the test data ------------------------------------------------------------

def create_from_files(settings, student_csv, seed) -> Solution:
    students = load_students(str(student_csv), settings)
    tutors, rooms = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)
    return create(settings, students, tutors, rooms, seed)


@pytest.fixture(params=[(TEST1 / "student.csv", seed) for seed in range(5)]
                + [(TEST2 / "funnystudents.csv", seed) for seed in range(5)],
                ids=lambda param: f"{param[0].parent.name}-seed{param[1]}")
def solution(request, settings) -> Solution:
    student_csv, seed = request.param
    return create_from_files(settings, student_csv, seed)


def test_tutors_never_exceed_their_maximum(solution):
    for tutor in solution.tutors:
        assert len(tutor.classes) <= tutor.maximum


def test_tutors_teach_one_class_at_a_time(solution):
    for tutor in solution.tutors:
        sessions = [classroom.session for classroom in tutor.classes]
        assert len(sessions) == len(set(sessions)), tutor.name


def test_classes_are_when_the_tutor_is_available(solution):
    for classroom in solution.schedule.classes:
        assert classroom.tutor.availability_at(classroom.session) in (AVAILABLE, POTENTIAL)
        assert classroom.session.day in solution.settings.student_days


def test_classes_match_the_tutor(solution):
    for classroom in solution.schedule.classes:
        assert classroom.subject == classroom.tutor.subject
        assert classroom.year_level in classroom.tutor.year_levels
        assert classroom in classroom.tutor.classes


def test_rooms_are_not_double_booked(solution):
    rooms = Counter((classroom.session, classroom.room) for classroom in solution.schedule.classes if not classroom.online)
    assert all(count == 1 for count in rooms.values())
    assert all(classroom.room in solution.schedule.rooms
               for classroom in solution.schedule.classes if not classroom.online)


def test_online_tutors_only_teach_online(solution):
    for classroom in solution.schedule.classes:
        if classroom.tutor.location == ONLINE:
            assert classroom.online and classroom.room == ONLINE


def test_some_student_can_attend_every_class(solution):
    for classroom in solution.schedule.classes:
        assert any(student.year_level == classroom.year_level and student.is_available(classroom.session)
                   for student in solution.students)


def test_enough_classes_are_created(solution):
    # the test data has enough tutors for every year level and subject someone can teach
    made = Counter((classroom.year_level, classroom.subject) for classroom in solution.schedule.classes)
    for cohort, needed in solution.classes_needed.items():
        assert made[cohort] >= needed, cohort


def test_year_level_without_a_tutor_is_unplaceable(settings):
    # no maths tutor in test1 teaches year 5, but an english tutor does
    solution = create_from_files(settings, TEST1 / "student.csv", seed=0)
    year_5 = [student for student in solution.students if student.year_level == "5"]

    assert year_5
    assert all(student.unplaceable == {"Maths"} for student in year_5)
    assert ("5", "Maths") not in solution.classes_needed
    assert ("5", "English") in solution.classes_needed


def test_same_seed_same_classes(settings):
    def summary(solution):
        return [(c.session, c.room, c.subject, c.year_level, c.tutor.full_name) for c in solution.schedule.classes]

    assert summary(create_from_files(settings, TEST1 / "student.csv", 7)) == \
        summary(create_from_files(settings, TEST1 / "student.csv", 7))


def test_dampening_scales_classes_needed(settings):
    full = create_from_files(replace(settings, dampening=1.0), TEST1 / "student.csv", 0)
    dampened = create_from_files(replace(settings, dampening=0.5), TEST1 / "student.csv", 0)

    # 52 year 8 students in classes of 5: 11 classes, or 6 at half
    assert full.classes_needed[("8", "Maths")] == 11
    assert dampened.classes_needed[("8", "Maths")] == 6


# --- small cases --------------------------------------------------------------

def test_available_is_used_before_potentially_available(settings):
    tutor = make_tutor("Ann Lee", "Maths", ["8"], {TUESDAY_EARLY: POTENTIAL, WEDNESDAY_EARLY: AVAILABLE})
    solution = create(settings, make_students(1, "8", [TUESDAY_EARLY, WEDNESDAY_EARLY]), [tutor])

    assert [classroom.session for classroom in tutor.classes] == [WEDNESDAY_EARLY]


def test_potentially_available_is_used_when_needed(settings):
    tutor = make_tutor("Ann Lee", "Maths", ["8"], {TUESDAY_EARLY: POTENTIAL})
    create(settings, make_students(1, "8", [TUESDAY_EARLY]), [tutor])

    assert [classroom.session for classroom in tutor.classes] == [TUESDAY_EARLY]


def test_first_preference_year_level_comes_first(settings):
    tutor = make_tutor("Ann Lee", "Maths", ["7", "8"], {TUESDAY_EARLY: AVAILABLE}, maximum=1)
    students = make_students(1, "8", [TUESDAY_EARLY]) + make_students(1, "7", [TUESDAY_EARLY])
    create(settings, students, [tutor])

    assert [classroom.year_level for classroom in tutor.classes] == ["7"]


def test_later_preferences_are_used_when_needed(settings):
    tutor = make_tutor("Ann Lee", "Maths", ["7", "8"], {TUESDAY_EARLY: AVAILABLE})
    create(settings, make_students(1, "8", [TUESDAY_EARLY]), [tutor])

    assert [classroom.year_level for classroom in tutor.classes] == ["8"]


def test_classes_are_shared_between_tutors(settings):
    sessions = {TUESDAY_EARLY: AVAILABLE, WEDNESDAY_EARLY: AVAILABLE}
    tutors = [make_tutor("Ann Lee", "Maths", ["8"], sessions), make_tutor("Bo Kim", "Maths", ["8"], sessions)]

    # 6 students need 2 classes (ceil(ceil(6 / 5) * 0.75))
    solution = create(settings, make_students(6, "8", [TUESDAY_EARLY, WEDNESDAY_EARLY]), tutors, rooms=("201", "205"))

    assert solution.classes_needed[("8", "Maths")] == 2
    assert [len(tutor.classes) for tutor in tutors] == [1, 1]


def test_tutors_get_both_halves_of_a_day(settings):
    tutor = make_tutor("Ann Lee", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE, TUESDAY_LATE: AVAILABLE,
                                                   WEDNESDAY_EARLY: AVAILABLE})
    create(settings, make_students(6, "8", [TUESDAY_EARLY, TUESDAY_LATE, WEDNESDAY_EARLY]), [tutor])

    assert sorted(classroom.session for classroom in tutor.classes) == sorted([TUESDAY_EARLY, TUESDAY_LATE])


def test_no_class_when_no_student_can_attend(settings):
    tutor = make_tutor("Ann Lee", "Maths", ["8"], {WEDNESDAY_EARLY: AVAILABLE})
    solution = create(settings, make_students(3, "8", [TUESDAY_EARLY]), [tutor])

    assert solution.schedule.classes == []


def test_non_student_days_are_never_used(settings):
    tutor = make_tutor("Ann Lee", "Maths", ["8"], {Session("Monday", EARLY): AVAILABLE})
    students = make_students(3, "8", [TUESDAY_EARLY])
    solution = create(settings, students, [tutor])

    assert solution.schedule.classes == []
    assert all("Maths" in student.unplaceable for student in students)


def test_overflow_goes_online(settings):
    tutors = [make_tutor("Ann Lee", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE}),
              make_tutor("Bo Kim", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE})]
    create(settings, make_students(10, "8", [TUESDAY_EARLY]), tutors, rooms=("201",))

    assert sorted(tutor.classes[0].room for tutor in tutors) == ["201", ONLINE]


def test_online_tutor_leaves_rooms_free(settings):
    online = make_tutor("Ann Lee", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE}, location=ONLINE)
    in_person = make_tutor("Bo Kim", "English", ["8"], {TUESDAY_EARLY: AVAILABLE})
    create(settings, make_students(1, "8", [TUESDAY_EARLY]), [online, in_person], rooms=("201",))

    assert online.classes[0].online
    assert in_person.classes[0].room == "201"


def test_surplus_classes(settings):
    # 50 students give one surplus round. Dampening is tiny so only 1 class is needed up front
    tutor = make_tutor("Ann Lee", "Maths", ["8"], {TUESDAY_EARLY: AVAILABLE, TUESDAY_LATE: AVAILABLE,
                                                   WEDNESDAY_EARLY: AVAILABLE}, maximum=10)
    solution = create(replace(settings, dampening=0.01), make_students(50, "8", [TUESDAY_EARLY, TUESDAY_LATE,
                                                                                 WEDNESDAY_EARLY]), [tutor])

    assert solution.classes_needed[("8", "Maths")] == 1
    assert len(tutor.classes) > 1


def test_relaxation_ladder():
    assert [(rung.availabilities, rung.max_preference) for rung in relaxation_ladder(2)] == [
        ((AVAILABLE,), 0),
        ((AVAILABLE, POTENTIAL), 0),
        ((AVAILABLE,), 1),
        ((AVAILABLE, POTENTIAL), 1),
    ]
