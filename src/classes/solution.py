from collections import Counter
from math import ceil
from random import Random
from typing import NamedTuple

from src.config import SUBJECTS, Settings
from src.classes.schedule import Schedule
from src.classes.session import Session
from src.classes.student import Student
from src.classes.tutor import Availability, Tutor

SURPLUS_STUDENTS_PER_ROUND = 50     # one round of surplus classes for every this many students


class Rung(NamedTuple):
    """ One step of the relaxation ladder """
    availabilities: tuple[Availability, ...]    # which tutor availabilities may be used
    max_preference: int                         # how far down a tutor's year levels to go (0 = first preference only)


def relaxation_ladder(preferences: int) -> list[Rung]:
    """
    Class creation rules from strictest to loosest. A looser rung is only used once the stricter
    rungs can't create any more of the classes needed. `preferences` is the longest year level
    list any tutor has.
    """
    ladder = []
    for max_preference in range(preferences):
        ladder.append(Rung((Availability.AVAILABLE,), max_preference))
        ladder.append(Rung((Availability.AVAILABLE, Availability.POTENTIAL), max_preference))
    return ladder


class Solution:
    """ Creates the classes for the timetable. Placing students into them comes in phase 4 """

    settings: Settings
    rng: Random

    students: list[Student]
    tutors: list[Tutor]
    schedule: Schedule

    classes_needed: dict[tuple[str, str], int]              # (year level, subject) -> classes to create up front
    _available_students: Counter[tuple[str, Session]]       # (year level, session) -> students available then

    def __init__(self, settings: Settings, seed: int | None = None) -> None:
        self.settings = settings
        self.rng = Random(seed)             # seeded so a run can be repeated

        self.students = []
        self.tutors = []
        self.schedule = Schedule([])

        self.classes_needed = {}
        self._available_students = Counter()

    def setup(self, students: list[Student], tutors: list[Tutor], rooms: list[str]) -> None:
        """ Give the solution the loaded students, tutors and rooms (see src/loader.py) """
        self.students = students
        self.tutors = tutors
        self.schedule = Schedule(rooms)

        self._available_students = Counter(
            (student.year_level, session) for student in students for session in student.availability
        )

    def execute(self) -> None:
        """ Build the timetable """
        self.create_classes()
        # TODO(phase 4): place the students into the classes

    def create_classes(self) -> None:
        """ Create the classes, before any students are placed """
        self._mark_unteachable_subjects()
        self.classes_needed = self._count_classes_needed()

        preferences = max((len(tutor.year_levels) for tutor in self.tutors), default=0)
        for rung in relaxation_ladder(preferences):
            self._create_needed_classes(rung)

        self._create_surplus_classes()

    def _mark_unteachable_subjects(self) -> None:
        """ Students in a year level that no tutor can teach a subject to can't be placed in that subject """
        teachable = {
            (year_level, tutor.subject)
            for tutor in self.tutors
            if any(self._can_use(tutor, session, (Availability.AVAILABLE, Availability.POTENTIAL))
                   for session in tutor.availability)
            for year_level in tutor.year_levels
        }

        for student in self.students:
            for subject in SUBJECTS:
                if (student.year_level, subject) not in teachable:
                    student.unplaceable.add(subject)

    def _count_classes_needed(self) -> dict[tuple[str, str], int]:
        """ Enough classes to fit every student, scaled by the dampening factor """
        cohorts = Counter(
            (student.year_level, subject)
            for student in self.students
            for subject in SUBJECTS
            if subject not in student.unplaceable
        )
        return {
            cohort: ceil(ceil(size / self.settings.class_size) * self.settings.dampening)
            for cohort, size in cohorts.items()
        }

    def _shortfall(self, year_level: str, subject: str) -> int:
        """ How many more classes are needed for this year level and subject """
        created = sum(1 for classroom in self.schedule.classes
                      if classroom.year_level == year_level and classroom.subject == subject)
        return self.classes_needed.get((year_level, subject), 0) - created

    def _open_demand(self, year_level: str, subject: str, session: Session) -> int:
        """ Students in the year level available at this session, minus the seats already created for them """
        classes = sum(1 for classroom in self.schedule.classes_at(session)
                      if classroom.year_level == year_level and classroom.subject == subject)
        return self._available_students[(year_level, session)] - classes * self.settings.class_size

    def _can_use(self, tutor: Tutor, session: Session, availabilities: tuple[Availability, ...]) -> bool:
        """ True if the tutor could take a new class at this session """
        return (
            not tutor.is_full()
            and session.day in self.settings.student_days
            and tutor.availability_at(session) in availabilities
            and not tutor.is_booked(session)
        )

    def _create_needed_classes(self, rung: Rung) -> None:
        """
        Create classes until every year level and subject has enough, or this rung can't create any more.
        Each pass gives every year level and subject one class (or pair) at most, so they take turns with the tutors.
        """
        while True:
            short = [cohort for cohort in self.classes_needed if self._shortfall(*cohort) > 0]
            short.sort(key=lambda cohort: self._shortfall(*cohort), reverse=True)

            created = False
            for year_level, subject in short:
                if self._create_class_for(year_level, subject, rung):
                    created = True

            if not created:
                return

    def _create_class_for(self, year_level: str, subject: str, rung: Rung) -> bool:
        """ Create one class for the year level and subject, plus its pair if possible. False if none could be made """
        choice = self._choose_tutor_and_session(year_level, subject, rung)
        if choice is None:
            return False

        tutor, session = choice
        self.schedule.create_class(tutor, session, subject, year_level)

        # give the tutor the other half of the day too, so their classes are back to back
        if self._shortfall(year_level, subject) > 0 and self._can_pair(tutor, session, year_level, rung.availabilities):
            self.schedule.create_class(tutor, session.other_half(), subject, year_level)

        return True

    def _can_pair(self, tutor: Tutor, session: Session, year_level: str,
                  availabilities: tuple[Availability, ...]) -> bool:
        """ True if the tutor could also teach the year level in the other half of the session's day """
        other_half = session.other_half()
        return (self._can_use(tutor, other_half, availabilities)
                and self._open_demand(year_level, tutor.subject, other_half) > 0)

    def _choose_tutor_and_session(self, year_level: str, subject: str, rung: Rung) -> tuple[Tutor, Session] | None:
        """
        Pick who teaches the next class and when. Prefers the tutor with the fewest classes,
        then the one who wants the year level most, then the session the most students can make,
        then a session the tutor can pair with the other half of the day.
        Only sessions where some student still needs a seat are considered.
        """
        candidates = [
            (tutor, session)
            for tutor in self.tutors
            if tutor.subject == subject
            and year_level in tutor.year_levels[:rung.max_preference + 1]
            for session in tutor.availability
            if self._can_use(tutor, session, rung.availabilities)
            and self._open_demand(year_level, subject, session) > 0
        ]
        if not candidates:
            return None

        return min(candidates, key=lambda candidate: (
            len(candidate[0].classes),
            candidate[0].year_levels.index(year_level),
            -self._open_demand(year_level, subject, candidate[1]),
            not self._can_pair(candidate[0], candidate[1], year_level, rung.availabilities),
            self.rng.random(),
        ))

    def _create_surplus_classes(self) -> None:
        """
        Most classes don't fill up, so give tutors some extra classes with their favourite year levels.
        Subjects take turns so neither gets all of them.
        """
        rounds = len(self.students) // SURPLUS_STUDENTS_PER_ROUND
        usable = (Availability.AVAILABLE, Availability.POTENTIAL)
        subjects = list(SUBJECTS)

        for _ in range(rounds):
            for tutor in self.tutors:
                if tutor.subject != subjects[0]:
                    continue

                choice = self._favourite_class(tutor, usable)
                if choice is None:
                    continue

                year_level, session = choice
                self.schedule.create_class(tutor, session, tutor.subject, year_level)

                if self._can_pair(tutor, session, year_level, (Availability.AVAILABLE,)):
                    self.schedule.create_class(tutor, session.other_half(), tutor.subject, year_level)

                subjects.append(subjects.pop(0))

    def _favourite_class(self, tutor: Tutor, availabilities: tuple[Availability, ...]) -> tuple[str, Session] | None:
        """ The tutor's most preferred year level that has students wanting a seat, and the session most of them can make """
        for year_level in tutor.year_levels:
            if (year_level, tutor.subject) not in self.classes_needed:
                continue        # no students in this year level take the subject

            sessions = [
                session for session in tutor.availability
                if self._can_use(tutor, session, availabilities)
                and self._open_demand(year_level, tutor.subject, session) > 0
            ]
            if sessions:
                best = max(sessions, key=lambda session: (self._open_demand(year_level, tutor.subject, session),
                                                          self.rng.random()))
                return year_level, best

        return None
