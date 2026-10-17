from dataclasses import replace

import pytest

from src.classes import tidy_up
from src.classes.schedule import ONLINE, Schedule
from src.classes.session import EARLY, LATE, Session
from src.classes.solution import Solution
from src.classes.student import Student
from src.classes.tutor import Availability
from src.loader import load_students, load_tutor_sheet
from tests.conftest import TEST1, TEST2, make_tutor

AVAILABLE = Availability.AVAILABLE

TUESDAY_EARLY = Session("Tuesday", EARLY)
TUESDAY_LATE = Session("Tuesday", LATE)
WEDNESDAY_EARLY = Session("Wednesday", EARLY)


def make_student(name: str, availability: list[Session], year_level: str = "8", location: str = "In-Person") -> Student:
    return Student("", name, "X", year_level, location, availability)


def tutor_for(*sessions: Session, location: str = "In-Person", year_levels=("8",), maximum: int = 4):
    return make_tutor("Tim Tutor", "Maths", list(year_levels), {session: AVAILABLE for session in sessions},
                      maximum=maximum, location=location)


def class_with(schedule: Schedule, tutor, session: Session, students, year_level: str = "8"):
    classroom = schedule.create_class(tutor, session, "Maths", year_level)
    for student in students:
        classroom.add_student(student)
    return classroom


# --- the test data ------------------------------------------------------------

@pytest.fixture(params=[(TEST1 / "student.csv", seed) for seed in range(5)]
                + [(TEST2 / "funnystudents.csv", seed) for seed in range(5)],
                ids=lambda param: f"{param[0].parent.name}-seed{param[1]}")
def solution(request, settings) -> Solution:
    student_csv, seed = request.param
    tutors, rooms = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)

    solution = Solution(settings, seed)
    solution.setup(load_students(str(student_csv), settings), tutors, rooms)
    solution.execute()
    return solution


def location_mismatches(schedule: Schedule) -> int:
    return sum(tidy_up.location_mismatch(student, classroom)
               for classroom in schedule.classes for student in classroom.students)


def test_no_more_merges_are_possible(solution):
    assert tidy_up.merge_small_classes(solution.schedule, solution.settings.class_size) == 0


def test_no_more_location_fixes_are_possible(solution):
    before = location_mismatches(solution.schedule)
    tidy_up.match_student_locations(solution.schedule, solution.settings.class_size)
    assert location_mismatches(solution.schedule) == before


def test_in_person_tutors_only_go_online_when_the_rooms_are_full(solution):
    for classroom in solution.schedule.classes:
        if classroom.online and classroom.tutor.location != ONLINE:
            assert solution.schedule.free_room(classroom.session) is None


def test_tutors_keep_one_room_for_the_day(solution):
    for classroom in solution.schedule.classes:
        late = [other for other in classroom.tutor.classes if other.session == classroom.session.other_half()]
        if not classroom.online and late and not late[0].online:
            assert classroom.room == late[0].room


def test_rooms_are_not_double_booked(solution):
    for classroom in solution.schedule.classes:
        if not classroom.online:
            assert classroom.room in solution.schedule.rooms
            assert sum(other.room == classroom.room for other in solution.schedule.classes_at(classroom.session)) == 1


def test_class_names_are_unique(solution):
    names = [classroom.name for classroom in solution.schedule.classes]
    assert all(names)
    assert len(names) == len(set(names))


# --- merging one-student classes ----------------------------------------------

def test_one_student_class_is_merged(settings):
    schedule = Schedule(["201", "205"])
    ann = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY])
    alone = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [ann])
    other = class_with(schedule, tutor_for(WEDNESDAY_EARLY), WEDNESDAY_EARLY, [make_student("Bo", [WEDNESDAY_EARLY]),
                                                                              make_student("Cy", [WEDNESDAY_EARLY])])

    assert tidy_up.merge_small_classes(schedule, settings.class_size) == 1

    assert schedule.classes == [other]
    assert ann.classes["Maths"] is other
    assert alone.tutor.classes == []


def test_one_student_class_stays_when_nothing_has_room(settings):
    schedule = Schedule(["201", "205"])
    ann = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY])
    class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [ann])
    class_with(schedule, tutor_for(WEDNESDAY_EARLY), WEDNESDAY_EARLY, [make_student("Bo", [WEDNESDAY_EARLY])])
    class_with(schedule, tutor_for(TUESDAY_LATE), TUESDAY_LATE, [make_student("Cy", [TUESDAY_LATE])])

    # Ann can only reach Wednesday, and it's full. Bo can't reach Tuesday
    assert tidy_up.merge_small_classes(schedule, class_size=1) == 0
    assert len(schedule.classes) == 3


def test_merge_frees_a_tutor_for_a_backup_class(settings):
    # Tim can only teach once. Merging Ann into Ula's class frees him to teach Zoe
    tim = tutor_for(TUESDAY_EARLY, year_levels=("8", "7"), maximum=1)
    ula = tutor_for(WEDNESDAY_EARLY)
    ann = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY])
    bo = make_student("Bo", [WEDNESDAY_EARLY])
    zoe = make_student("Zoe", [TUESDAY_EARLY], year_level="7")
    for student in (ann, bo, zoe):
        student.unplaceable.add("English")

    solution = Solution(settings, seed=0)
    solution.setup([ann, bo, zoe], [tim, ula], ["201", "205"])
    class_with(solution.schedule, tim, TUESDAY_EARLY, [ann])
    class_with(solution.schedule, ula, WEDNESDAY_EARLY, [bo])

    solution.fill_gaps()

    assert ann.classes["Maths"] is bo.classes["Maths"]
    assert zoe.classes["Maths"].tutor is tim
    assert zoe.unplaceable == {"English"}


# --- rooms --------------------------------------------------------------------

def test_in_person_tutor_gets_a_room_that_comes_free():
    schedule = Schedule(["201"])
    leaving = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [])
    squeezed = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [])
    assert squeezed.online

    schedule.remove_class(leaving)
    tidy_up.use_free_rooms(schedule)

    assert not squeezed.online and squeezed.room == "201"


def test_online_tutor_stays_online():
    schedule = Schedule(["201"])
    online = class_with(schedule, tutor_for(TUESDAY_EARLY, location=ONLINE), TUESDAY_EARLY, [])

    tidy_up.use_free_rooms(schedule)

    assert online.online and online.room == ONLINE


def test_tutor_keeps_their_early_room_for_the_late_class():
    schedule = Schedule(["201", "205"])
    tim = tutor_for(TUESDAY_EARLY, TUESDAY_LATE)
    class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [])
    early = class_with(schedule, tim, TUESDAY_EARLY, [])
    holder = class_with(schedule, tutor_for(TUESDAY_LATE), TUESDAY_LATE, [])
    late = class_with(schedule, tim, TUESDAY_LATE, [])
    late.room, holder.room = "201", "205"
    assert early.room == "205"
    tidy_up.keep_tutors_in_one_room(schedule)

    assert late.room == early.room == "205"
    assert holder.room == "201"


def test_tutor_takes_a_free_room_for_the_late_class():
    schedule = Schedule(["201", "205"])
    tim = tutor_for(TUESDAY_EARLY, TUESDAY_LATE)
    early = class_with(schedule, tim, TUESDAY_EARLY, [])
    late = class_with(schedule, tim, TUESDAY_LATE, [])
    late.room = "205"

    tidy_up.keep_tutors_in_one_room(schedule)

    assert late.room == early.room == "201"


# --- online and in-person students ---------------------------------------------

def test_mismatched_students_swap():
    schedule = Schedule(["201"])
    online_student = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY], location=ONLINE)
    in_person_student = make_student("Bo", [TUESDAY_EARLY, WEDNESDAY_EARLY])
    in_person = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [online_student])
    online = class_with(schedule, tutor_for(WEDNESDAY_EARLY, location=ONLINE), WEDNESDAY_EARLY, [in_person_student])

    tidy_up.match_student_locations(schedule, class_size=5)

    assert online_student.classes["Maths"] is online
    assert in_person_student.classes["Maths"] is in_person


def test_no_swap_when_it_clashes_with_the_other_subject():
    schedule = Schedule(["201"])
    online_student = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY], location=ONLINE)
    in_person_student = make_student("Bo", [TUESDAY_EARLY, WEDNESDAY_EARLY])
    in_person = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [online_student])
    class_with(schedule, tutor_for(WEDNESDAY_EARLY, location=ONLINE), WEDNESDAY_EARLY, [in_person_student])

    english = schedule.create_class(make_tutor("Eve English", "English", ["8"], {}), WEDNESDAY_EARLY, "English", "8")
    english.add_student(online_student)

    tidy_up.match_student_locations(schedule, class_size=5)

    assert online_student.classes["Maths"] is in_person


def test_mismatched_student_moves_to_a_class_with_room():
    schedule = Schedule(["201"])
    online_student = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY], location=ONLINE)
    others = [make_student(name, [TUESDAY_EARLY]) for name in ("Bo", "Cy")]
    class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [online_student] + others)
    online = class_with(schedule, tutor_for(WEDNESDAY_EARLY, location=ONLINE), WEDNESDAY_EARLY, [])

    tidy_up.match_student_locations(schedule, class_size=5)

    assert online_student.classes["Maths"] is online


def test_move_does_not_leave_a_one_student_class():
    schedule = Schedule(["201"])
    online_student = make_student("Ann", [TUESDAY_EARLY, WEDNESDAY_EARLY], location=ONLINE)
    in_person = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY,
                           [online_student, make_student("Bo", [TUESDAY_EARLY])])
    class_with(schedule, tutor_for(WEDNESDAY_EARLY, location=ONLINE), WEDNESDAY_EARLY, [])

    tidy_up.match_student_locations(schedule, class_size=5)

    assert online_student.classes["Maths"] is in_person


# --- names --------------------------------------------------------------------

def test_classes_are_named_in_timetable_order(settings):
    schedule = Schedule(["201", "205"])
    online = class_with(schedule, tutor_for(TUESDAY_EARLY, location=ONLINE), TUESDAY_EARLY, [])
    wednesday = class_with(schedule, tutor_for(WEDNESDAY_EARLY), WEDNESDAY_EARLY, [])
    late = class_with(schedule, tutor_for(TUESDAY_LATE), TUESDAY_LATE, [])
    room_205 = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [])
    room_205.room = "205"
    room_201 = class_with(schedule, tutor_for(TUESDAY_EARLY), TUESDAY_EARLY, [])
    year_7 = class_with(schedule, tutor_for(TUESDAY_LATE, year_levels=("7",)), TUESDAY_LATE, [], year_level="7")
    english = schedule.create_class(make_tutor("Eve English", "English", ["8"], {}), TUESDAY_LATE, "English", "8")

    tidy_up.name_classes(schedule, settings.student_days)

    assert [room_201.name, room_205.name, online.name, late.name, wednesday.name] == [
        "SEL MAT 8A", "SEL MAT 8B", "SEL MAT 8C", "SEL MAT 8D", "SEL MAT 8E"]
    assert year_7.name == "SEL MAT 7A"
    assert english.name == "SEL ENG 8A"


@pytest.mark.parametrize("number, letters", [(1, "A"), (26, "Z"), (27, "AA"), (52, "AZ"), (53, "BA")])
def test_class_letter(number, letters):
    assert tidy_up.class_letter(number) == letters
