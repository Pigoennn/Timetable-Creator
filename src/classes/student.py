from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import SUBJECTS
from src.classes.session import Session

if TYPE_CHECKING:
    from src.classes.timetable_class import Class


class Student:
    """ A student and their answers from the availability form """

    email: str
    first_name: str
    last_name: str
    name: str                           # display name, made unique by the loader

    year_level: str                     # "8", not "Year 8"
    location: str                       # "In-Person" or "Online"

    availability: list[Session]         # in the order they appear on the form

    classes: dict[str, Class | None]    # subject -> class, None if not placed yet
    unplaceable: set[str]               # subjects no class could be found for

    def __init__(self, email: str, first_name: str, last_name: str, year_level: str,
                 location: str, availability: list[Session]) -> None:
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.name = f"{first_name} {last_name[:1]}".strip()

        self.year_level = year_level
        self.location = location

        self.availability = availability

        self.classes = {subject: None for subject in SUBJECTS}
        self.unplaceable = set()

    def needs_class(self, subject: str) -> bool:
        """ True if the student still needs a class for the subject and one might be found """
        return self.classes[subject] is None and subject not in self.unplaceable

    def is_available(self, session: Session) -> bool:
        return session in self.availability

    def is_booked(self, session: Session) -> bool:
        """ True if the student already has a class at this session """
        return any(classroom is not None and classroom.session == session for classroom in self.classes.values())
