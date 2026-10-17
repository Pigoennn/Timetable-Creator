from __future__ import annotations

from typing import TYPE_CHECKING

from src.classes.session import Session

if TYPE_CHECKING:
    from src.classes.student import Student
    from src.classes.tutor import Tutor


class Class:
    """ One class: a tutor teaching a subject to a year level, in a room, at a session """

    session: Session
    room: str
    online: bool

    subject: str
    year_level: str
    tutor: Tutor | None
    students: list[Student]             # students only, the tutor is kept separately

    name: str                           # e.g. "SEL MAT 8A", given at the end

    def __init__(self, session: Session, room: str, online: bool = False) -> None:
        self.session = session
        self.room = room
        self.online = online

        self.subject = ""
        self.year_level = ""
        self.tutor = None
        self.students = []

        self.name = ""

    def is_running(self) -> bool:
        """ A class only runs if it has a tutor and at least one student """
        return self.tutor is not None and bool(self.students)

    def is_full(self, class_size: int) -> bool:
        return len(self.students) >= class_size

    def add_student(self, student: Student) -> None:
        self.students.append(student)
        student.classes[self.subject] = self

    def remove_student(self, student: Student) -> None:
        self.students.remove(student)
        student.classes[self.subject] = None
