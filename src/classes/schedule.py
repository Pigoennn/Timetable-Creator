from src.classes.session import Session
from src.classes.timetable_class import Class
from src.classes.tutor import Tutor

ONLINE = "Online"


class Schedule:
    """ Every class in the timetable, and the rooms they use """

    rooms: list[str]                    # physical rooms, from the tutor sheet
    classes: list[Class]

    def __init__(self, rooms: list[str]) -> None:
        self.rooms = rooms
        self.classes = []

    def classes_at(self, session: Session) -> list[Class]:
        return [classroom for classroom in self.classes if classroom.session == session]

    def rooms_at(self, session: Session) -> list[Class | None]:
        """ The class in each physical room at this session, in the order of the rooms (None if it's free) """
        by_room = {classroom.room: classroom for classroom in self.classes_at(session) if not classroom.online}
        return [by_room.get(room) for room in self.rooms]

    def online_at(self, session: Session) -> list[Class]:
        return [classroom for classroom in self.classes_at(session) if classroom.online]

    def layout_at(self, session: Session) -> list[Class]:
        """ The classes at this session in the order they're shown: physical rooms first, then online """
        return [classroom for classroom in self.rooms_at(session) if classroom] + self.online_at(session)

    def free_room(self, session: Session) -> str | None:
        """ The first physical room with no class at this session, or None if they're all taken """
        taken = {classroom.room for classroom in self.classes_at(session)}
        return next((room for room in self.rooms if room not in taken), None)

    def create_class(self, tutor: Tutor, session: Session, subject: str, year_level: str) -> Class:
        """ Create a class for the tutor. In-person tutors get the first free room,
        online tutors (or anyone once the rooms are all taken) get an online class """
        room = self.free_room(session) if tutor.location != ONLINE else None

        classroom = Class(session, room or ONLINE, online=room is None)
        classroom.subject = subject
        classroom.year_level = year_level
        classroom.tutor = tutor

        tutor.classes.append(classroom)
        self.classes.append(classroom)
        return classroom

    def remove_class(self, classroom: Class) -> None:
        """ Delete a class. Any students in it lose their place """
        for student in list(classroom.students):
            classroom.remove_student(student)

        classroom.tutor.classes.remove(classroom)
        self.classes.remove(classroom)
