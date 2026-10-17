from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from src.classes.session import Session

if TYPE_CHECKING:
    from src.classes.timetable_class import Class


class Availability(IntEnum):
    """ What a tutor wrote in a timeslot on the availability sheet """
    UNAVAILABLE = 0     # left blank
    POTENTIAL = 1       # "potentially available"
    AVAILABLE = 2


class Tutor:
    """ A tutor and everything they put on the availability sheet """

    full_name: str
    first_name: str
    last_name: str
    name: str                                   # display name, made unique by the loader

    subject: str
    year_levels: list[str]                      # in order of preference
    location: str                               # "In-Person", "Online" or "Both"

    availability: dict[Session, Availability]   # never changes; booked sessions come from `classes`
    maximum: int                                # maximum number of classes they want

    classes: list[Class]

    def __init__(self, full_name: str, subject: str, year_levels: list[str],
                 availability: dict[Session, Availability], maximum: int, location: str) -> None:
        self.full_name = full_name
        self.first_name, _, self.last_name = full_name.partition(" ")     # last name may have multiple parts
        self.name = f"{self.first_name} {self.last_name[:1]}".strip()

        self.subject = subject
        self.year_levels = year_levels
        self.location = location

        self.availability = availability
        self.maximum = maximum

        self.classes = []

    def availability_at(self, session: Session) -> Availability:
        return self.availability.get(session, Availability.UNAVAILABLE)

    def is_booked(self, session: Session) -> bool:
        """ True if the tutor is already teaching at this session """
        return any(classroom.session == session for classroom in self.classes)

    def is_full(self) -> bool:
        return len(self.classes) >= self.maximum
