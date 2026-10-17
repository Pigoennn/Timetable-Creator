"""
Passes that tidy up a finished timetable: they move students, rooms and online classes around
without breaking any rule (availability, class size, one class at a time, room bookings).
"""
from src.classes.schedule import ONLINE, Schedule
from src.classes.session import EARLY, TIMES, Session
from src.classes.student import Student
from src.classes.timetable_class import Class

CLASS_NAME_PREFIX = "SEL"


def location_mismatch(student: Student, classroom: Class) -> bool:
    """ True if an online student is in an in-person class, or the other way around """
    return (student.location == ONLINE) != classroom.online


def can_move(student: Student, classroom: Class, to: Class) -> bool:
    """ Can the student leave `classroom` for `to`, a class in the same subject? """
    return (to is not classroom
            and to.year_level == classroom.year_level
            and student.is_available(to.session)
            and (to.session == classroom.session or not student.is_booked(to.session)))


def move_student(student: Student, classroom: Class, to: Class) -> None:
    classroom.remove_student(student)
    to.add_student(student)


def merge_small_classes(schedule: Schedule, class_size: int) -> int:
    """
    Move the student out of each one-student class into another class with room, and remove the class.
    Returns how many classes were removed.
    """
    merged = 0
    for classroom in list(schedule.classes):
        if len(classroom.students) != 1:
            continue

        student = classroom.students[0]
        options = [
            other for other in schedule.classes
            if other.subject == classroom.subject and not other.is_full(class_size)
            and len(other.students) > 0 and can_move(student, classroom, other)
        ]
        if not options:
            continue

        best = min(options, key=lambda other: (location_mismatch(student, other),
                                               student.availability.index(other.session)))
        move_student(student, classroom, best)
        schedule.remove_class(classroom)
        merged += 1

    return merged


def use_free_rooms(schedule: Schedule) -> None:
    """ In-person tutors who were put online because the rooms ran out get any room that has come free """
    for classroom in schedule.classes:
        if classroom.online and classroom.tutor.location != ONLINE:
            room = schedule.free_room(classroom.session)
            if room is not None:
                classroom.room = room
                classroom.online = False


def match_student_locations(schedule: Schedule, class_size: int) -> None:
    """
    Move or swap students so fewer of them are in a class that doesn't match how they attend.
    Every change lowers the number of mismatches, so this always finishes.
    """
    changed = True
    while changed:
        changed = False
        for classroom in list(schedule.classes):
            for student in [student for student in classroom.students if location_mismatch(student, classroom)]:
                if _improve_location(schedule, class_size, student, classroom):
                    changed = True


def _improve_location(schedule: Schedule, class_size: int, student: Student, classroom: Class) -> bool:
    same_subject = [other for other in schedule.classes
                    if other.subject == classroom.subject and can_move(student, classroom, other)]

    # moving out (rather than swapping) mustn't leave a one-student class behind
    if len(classroom.students) > 2:
        for other in same_subject:
            if not other.is_full(class_size) and not location_mismatch(student, other):
                move_student(student, classroom, other)
                return True

    for other in same_subject:
        for partner in other.students:
            before = location_mismatch(student, classroom) + location_mismatch(partner, other)
            after = location_mismatch(student, other) + location_mismatch(partner, classroom)
            if after < before and can_move(partner, other, classroom):
                classroom.remove_student(student)
                other.remove_student(partner)
                classroom.add_student(partner)
                other.add_student(student)
                return True

    return False


def keep_tutors_in_one_room(schedule: Schedule) -> None:
    """ A tutor teaching both halves of a day in person keeps their early room for the late class """
    for early in list(schedule.classes):
        if early.session.time != EARLY or early.online:
            continue

        late = next((classroom for classroom in early.tutor.classes
                     if classroom.session == early.session.other_half() and not classroom.online), None)
        if late is None or late.room == early.room:
            continue

        # whoever has the room in the late session swaps with them
        holder = next((classroom for classroom in schedule.rooms_at(late.session) if classroom
                       and classroom.room == early.room), None)
        if holder is not None:
            holder.room = late.room
        late.room = early.room


def name_classes(schedule: Schedule, days: tuple[str, ...]) -> None:
    """ Name the classes e.g. "SEL MAT 8A", lettered in the order they appear in the timetable """
    counts: dict[tuple[str, str], int] = {}
    for day in days:
        for time in TIMES:
            for classroom in schedule.layout_at(Session(day, time)):
                key = (classroom.subject, classroom.year_level)
                counts[key] = counts.get(key, 0) + 1
                classroom.name = (f"{CLASS_NAME_PREFIX} {classroom.subject[:3].upper()} "
                                  f"{classroom.year_level}{class_letter(counts[key])}")


def class_letter(number: int) -> str:
    """ 1 -> A, 26 -> Z, 27 -> AA, like spreadsheet columns """
    letters = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters
