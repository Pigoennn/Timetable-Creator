from src.classes.session import EARLY, LATE, Session
from src.classes.student import Student
from src.classes.timetable_class import Class
from src.classes.tutor import Availability, Tutor

TUESDAY_EARLY = Session("Tuesday", EARLY)


def make_class() -> tuple[Class, Tutor, Student]:
    tutor = Tutor("Ann Lee", "Maths", ["8"], {TUESDAY_EARLY: Availability.AVAILABLE}, 1, "In-Person")
    student = Student("a@b.c", "Bo", "Kim", "8", "In-Person", [TUESDAY_EARLY])

    classroom = Class(TUESDAY_EARLY, "201")
    classroom.subject = "Maths"
    classroom.tutor = tutor
    tutor.classes.append(classroom)
    return classroom, tutor, student


def test_other_half():
    assert TUESDAY_EARLY.other_half() == Session("Tuesday", LATE)
    assert TUESDAY_EARLY.other_half().other_half() == TUESDAY_EARLY


def test_add_and_remove_student():
    classroom, _, student = make_class()
    assert not classroom.is_running()

    classroom.add_student(student)
    assert classroom.is_running()
    assert student.classes["Maths"] is classroom
    assert student.is_booked(TUESDAY_EARLY)
    assert not student.needs_class("Maths")

    classroom.remove_student(student)
    assert not classroom.is_running()
    assert student.needs_class("Maths")
    assert not student.is_booked(TUESDAY_EARLY)


def test_unplaceable_student_needs_no_class():
    _, _, student = make_class()
    student.unplaceable.add("English")
    assert not student.needs_class("English")
    assert student.needs_class("Maths")


def test_tutor_booking():
    _, tutor, _ = make_class()
    assert tutor.is_booked(TUESDAY_EARLY)
    assert not tutor.is_booked(TUESDAY_EARLY.other_half())
    assert tutor.is_full()
    assert tutor.availability_at(Session("Monday", EARLY)) == Availability.UNAVAILABLE


def test_class_is_full():
    classroom, _, student = make_class()
    classroom.add_student(student)
    assert classroom.is_full(1)
    assert not classroom.is_full(5)
