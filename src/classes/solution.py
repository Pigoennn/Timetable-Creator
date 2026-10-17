from collections import Counter, deque
from math import ceil
from random import Random
from typing import Callable, NamedTuple

from src.config import SUBJECTS, Settings
from src.classes.schedule import ONLINE, Schedule
from src.classes.session import Session
from src.classes import tidy_up
from src.classes.student import Student
from src.classes.timetable_class import Class
from src.classes.tutor import Availability, Tutor

SURPLUS_STUDENTS_PER_ROUND = 50     # one round of surplus classes for every this many students

Progress = Callable[[int, str], None]   # (percent, what's happening)

# roughly how far through a run each stage starts, by how long they take
PLACING_STARTS = 15
TIDYING_STARTS = 95


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
    """ Creates the classes for the timetable and places the students into them """

    settings: Settings
    rng: Random

    students: list[Student]
    tutors: list[Tutor]
    schedule: Schedule

    classes_needed: dict[tuple[str, str], int]              # (year level, subject) -> classes to create up front
    _available_students: Counter[tuple[str, Session]]       # (year level, session) -> students available then

    _progress: Progress
    _last_progress: tuple[int, str] | None

    def __init__(self, settings: Settings, seed: int | None = None) -> None:
        self.settings = settings
        self.rng = Random(seed)             # seeded so a run can be repeated

        self.students = []
        self.tutors = []
        self.schedule = Schedule([])

        self.classes_needed = {}
        self._available_students = Counter()

        self._progress = lambda percent, message: None
        self._last_progress = None

    def setup(self, students: list[Student], tutors: list[Tutor], rooms: list[str]) -> None:
        """ Give the solution the loaded students, tutors and rooms (see src/loader.py) """
        self.students = students
        self.tutors = tutors
        self.schedule = Schedule(rooms)

        self._available_students = Counter(
            (student.year_level, session) for student in students for session in student.availability
        )

    def execute(self, progress: Progress | None = None) -> None:
        """ Build the timetable. `progress` is called with (percent, message) as it goes """
        if progress is not None:
            self._progress = progress

        self._report(0, "Creating classes")
        self.create_classes()
        self.place_students()
        self._report(TIDYING_STARTS, "Tidying up")
        self.fill_gaps()
        self.tidy_up()
        self._report(100, "Done")

    def _report(self, percent: int, message: str) -> None:
        """ Pass progress on, skipping repeats """
        if (percent, message) != self._last_progress:
            self._last_progress = (percent, message)
            self._progress(percent, message)

    def tidy_up(self) -> None:
        """ Improve the finished timetable, then name the classes (see src/classes/tidy_up.py) """
        tidy_up.use_free_rooms(self.schedule)
        tidy_up.match_student_locations(self.schedule, self.settings.class_size)
        tidy_up.keep_tutors_in_one_room(self.schedule)
        tidy_up.name_classes(self.schedule, self.settings.student_days)

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

    # --- placing students -----------------------------------------------------

    def place_students(self) -> None:
        """ Place every student into the classes created so far, one subject at a time """
        for number, subject in enumerate(SUBJECTS):
            self._place_subject(subject, done=number / len(SUBJECTS))

    def _place_subject(self, subject: str, done: float = 0) -> None:
        """
        Deferred acceptance: students ask for their favourite class first. A class that is over-full
        keeps the students with the fewest other options, and bumps the rest to ask for their next choice.
        Students who run out of choices are left for the backup classes.
        `done` is the fraction of all placing finished before this subject, for the progress.
        """
        students = [student for student in self.students if student.needs_class(subject)]

        # working out the choices is the slow part of a run
        choices = {}
        for count, student in enumerate(students):
            choices[student] = self._class_choices(student, subject)
            fraction = done + count / len(students) / len(SUBJECTS)
            self._report(PLACING_STARTS + int((TIDYING_STARTS - PLACING_STARTS) * fraction),
                         f"Placing {subject} students")

        # classes would rather have students with fewer choices; ties are random so nobody is always bumped
        tie_break = {student: self.rng.random() for student in students}
        def bump_order(student: Student) -> tuple[int, float]:
            return len(choices[student]), tie_break[student]

        next_choice = {student: 0 for student in students}
        asking = deque(students)

        while asking:
            student = asking.popleft()
            if next_choice[student] == len(choices[student]):
                continue        # out of choices

            classroom = choices[student][next_choice[student]]
            next_choice[student] += 1
            classroom.add_student(student)

            if len(classroom.students) > self.settings.class_size:
                bumped = max(classroom.students, key=bump_order)
                classroom.remove_student(bumped)
                asking.append(bumped)

    def _class_choices(self, student: Student, subject: str) -> list[Class]:
        """
        The classes a student could go to for a subject, best first:
        - classes that don't take the student's only time left for their other subjects
        - classes that match whether the student is online or in person
        - classes that leave the most times free for their other subjects
        - the order the student's availability is in
        """
        other_subjects = [other for other in SUBJECTS if other != subject and student.needs_class(other)]

        def other_choices(classroom: Class) -> int:
            return sum(1 for other in self._open_classes(student, other_subjects)
                       if other.session != classroom.session)

        def rank(classroom: Class) -> tuple[bool, bool, int, int]:
            remaining = other_choices(classroom)
            return (
                bool(other_subjects) and remaining == 0,
                (student.location == ONLINE) != classroom.online,
                -remaining,
                student.availability.index(classroom.session),
            )

        return sorted(self._open_classes(student, [subject]), key=rank)

    def _open_classes(self, student: Student, subjects: list[str]) -> list[Class]:
        """ Classes in these subjects for the student's year level, at times the student is free """
        return [
            classroom for classroom in self.schedule.classes
            if classroom.subject in subjects
            and classroom.year_level == student.year_level
            and student.is_available(classroom.session)
            and not student.is_booked(classroom.session)
        ]

    # --- backup classes -------------------------------------------------------

    def fill_gaps(self) -> None:
        """
        Merge one-student classes into other classes and create backup classes, until neither helps.
        A merge can free a tutor for a backup class, and backup classes can leave one-student classes to merge.
        Anyone still without a class afterwards is marked unplaceable for that subject.
        """
        while True:
            merged = tidy_up.merge_small_classes(self.schedule, self.settings.class_size)
            created = self.create_backup_classes()
            if not merged and not created:
                break

        for student in self.students:
            for subject in SUBJECTS:
                if student.needs_class(subject):
                    student.unplaceable.add(subject)

    def create_backup_classes(self) -> int:
        """
        Create classes for the students who still need one, at the time most of them can make.
        Empty classes are removed first so their tutors can teach these instead. Returns how many were created.
        """
        for classroom in [classroom for classroom in self.schedule.classes if not classroom.students]:
            self.schedule.remove_class(classroom)

        no_tutor: set[tuple[str, str, Session]] = set()     # (year level, subject, session) nobody can teach
        created = 0

        while True:
            demand = self._backup_demand(no_tutor)
            if not demand:
                break

            (year_level, subject, session), _ = demand.most_common(1)[0]
            tutor = self._backup_tutor(year_level, subject, session)
            if tutor is None:
                no_tutor.add((year_level, subject, session))
                continue

            classroom = self.schedule.create_class(tutor, session, subject, year_level)
            created += 1

            # the students with the fewest other times get the seats first
            waiting = [
                student for student in self.students
                if student.year_level == year_level and student.needs_class(subject)
                and student.is_available(session) and not student.is_booked(session)
            ]
            waiting.sort(key=lambda student: sum(
                1 for other in student.availability
                if not student.is_booked(other) and (year_level, subject, other) not in no_tutor
            ))
            for student in waiting[:self.settings.class_size]:
                classroom.add_student(student)

        return created

    def _backup_demand(self, no_tutor: set[tuple[str, str, Session]]) -> Counter[tuple[str, str, Session]]:
        """ How many students without a class could make each (year level, subject, session) """
        return Counter(
            (student.year_level, subject, session)
            for student in self.students
            for subject in SUBJECTS
            if student.needs_class(subject)
            for session in student.availability
            if not student.is_booked(session) and (student.year_level, subject, session) not in no_tutor
        )

    def _backup_tutor(self, year_level: str, subject: str, session: Session) -> Tutor | None:
        """ The tutor with the fewest classes who can teach this, preferring ones who want the year level more """
        candidates = [
            tutor for tutor in self.tutors
            if tutor.subject == subject and year_level in tutor.year_levels
            and self._can_use(tutor, session, (Availability.AVAILABLE, Availability.POTENTIAL))
        ]
        return min(candidates, default=None, key=lambda tutor: (
            len(tutor.classes),
            tutor.year_levels.index(year_level),
            tutor.availability_at(session) != Availability.AVAILABLE,
        ))
