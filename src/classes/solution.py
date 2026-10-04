from student import Student
from tutor import Tutor

alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1']

from student import Student
from tutor import Tutor
from timetable_class import Class

from math import ceil

TUTOR_ASSIGNED      = 3
TUTOR_AVAILABLE     = 2
TUTOR_POTENTIAL     = 1
TUTOR_UNAVAILABLE   = 0

class Solution:

    self.student_sheet: list[str]
    self.tutor_sheet: list[str]

    self.days: list[str]

    self.timetable: dict[str, list[str]]
    self.timetable_classrooms: dict[str, dict[str, Class]]      # timetable[day][time] = class

    self.students: list[Student]
    self.tutors: list[Tutor]

    self.classrooms: list[str]

    self.maths_names: dict[int, str]
    self.english_names: dict[int, str]

    self.cohort_stats = dict[int, int]
    self.classes_needed = dict[int, int]

    def __init__(self):
        pass

    def setup(self, student_csv: str, tutor_csv: str) -> None:
        """ Setup the need information before starting the algorithm """
        with open(tutor_csv, "r") as file:
            self.tutor_sheet = (file.read().splitlines())[3:]

        """
        Spreadsheet has Monday start from column E and uses 2 columns for every day.
        Unknown how many days will be available so the end column index is unknown for now.
        """
        final_column_heading = "What is the maximum number of classes you would like?"
        self.days: list[str] = self.tutor_sheet.pop(0).split(",")[4:]

        # clean up the header row and find the last column
        for day in range(len(self.days)):
            if days[day] == "":
                days[day] = days[day-1]
            elif days[day] == final_column_heading:
                end_column = day
                break

        """
        Next row has all the available times.
        Store these times into the dictionary
        """
        times = self.tutor_sheet.pop(0).split(",")[4:stopLimit+4]     # +4 to account for the offset during calculation
        for time in range(len(times)):
            if days[time] in self.timetable.keys():
                self.timetable[days[time]].append(times[time])
            else:
                self.timetable[days[time]] = [times[time]]
        

        self._setup_students(student_csv)
        self._cohort_statistics()

        self._setup_tutors(tutor_csv)
        self.classrooms = self.tutor_sheet[0].split("\"")[1].split(",")

        # TODO:
        # - Decide whether or not to add a separate class for setting up
    
    def _setup_students(self, student_csv: str):
        with open(student_csv, "r") as file:
            student_sheet = file.read().splitlines()[1:]

        for student in student_sheet:
            data = list(map(lambda x: x.replace("\"", ""), student.split(",")[1:]))
            
            # replace each time slot with a number
            for index, slot in enumerate(data):
                if slot < 5:
                    continue        # ignore first 5 indexes of list
            
                if "Early" in data[slot] and "Late" in data[slot]:
                    data[slot] = 3
                elif "Late" in data[slot]:
                    data[slot] = 2
                elif "Early" in data[slot]:
                    data[slot] = 1
                else:
                    data[slot] = 0
                
            self.students.append(Student(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9]))

        _fix_duplicates(self.student_list)
        return
        
    
    def _fix_duplicates(people: list[Student | Tutor]):
        """ Get list of people with duplicate naming """
        seen = set()
        duplicates = []

        for person in people:
            name = person.name

            # if name seen before, add them to the matching group in duplicates
            if name in seen:
                found = False
                for group in duplicates:
                    if group[0].name == name:
                        group.append(person)
                        found = True
                        break
                
                if not(found):
                    duplicates.append([people])
        
        for group in duplicates:
            for i in range(len(group)):
                for j in range(i+1):
                    group[i].update_name()

    
    def _cohort_statistics():
        """ Create statistics for each year level """

        for student in self.students: # Find the year level of each student and update the dictionary
            if student.year_level in self.cohort_stats.keys():
                cohort_stats[student.year_level] += 1
            else:
                cohort_stats[student.yearLevel] = 1

        for key in cohort_stats.keys():         # Let the naming dictionaries know what year levels exist
            self.maths_names[key] = 0
            self.english_names[key] = 0

    
    def _setup_tutors(self) -> None:
        """ Set up the tutor list """
        for tutor in self.tutor_sheet:
            temp = tutor.split(",")[1:]         # first column empty

            # check it's not the end
            if "Rooms:" in temp[0]:
                final_index = self.tutor_sheet.index(tutor)
                self.tutor_sheet = self.tutor_sheet[final_index+1:]
                break

            if not(temp[0]):
                self.tutors.append(Tutor(temp[0],temp[1],temp[2],temp[3:15],temp[15],temp[16]))

        _fix_duplicates(self.tutors)


    def _year_level_cleaning(self) -> None:
        """ Clean up the year levels.
        Remove year levels that are not possible and calculate classes needed """
        removal_list = []
        for year_level in self.cohort_stats:
            if _is_feasible_year(year_level):
                removal_list.append(year_level)
                self.cohort_stats[year_level] = 0

        if removal_list:
            for student in self.students:
                if student.year_level in removal_list:
                    for i in student.classes.keys():
                        student.classes[i] = None

        for key in self.cohort_stats.keys():
            self.classes_needed[key] = ceil(cohort_stats[key] / 5)
        
        return


    def _is_feasible_year(self, year_level: str) -> bool:
        """ Checks if a year level is possible by checking if there is less classes than
        the maximum number of classes. Not a perfect check """

        classes = {
            "Maths": 0,
            "English": 0
        }
        for tutor in self.tutors:
            if year_level in tutor.year_levels:
                classes[tutor.subject] += tutor.availability.count(1) + tutor.availability.count(2)

        return [i for i in classes.values() if i < self.cohort_stats[year_level]]

    def _need_more_classes(self, year_level: str) -> bool:
        num = ceil(self.classes_needed[year_level])

        needed = {
            "Maths": num,
            "English": num
        }
        
        # reduce respective subject by 1 if it matches year level
        for session in self.classrooms:
            if session.year_level == year_level:
                needed[session.subject] -= 1
        
        return bool([i for i in needed.values() if i > 0])


    def _build_timetable_grid(self) -> None:
        """
        Create the timetable dictionary and lists.
        One empty Class per (day, session, room).

        self.classrooms is the ordered registry of every Class object;
        self.timetable_classrooms maps day -> session -> room -> Class.
        """
        for day in self.timetable.keys():
            self.timetable_classrooms[day] = {
                "Early": {},
                "Late": {}
            }

            for session in ("Early", "Late"):
                for room in self.available_classrooms:
                    classroom = Class(day, session, room)
                    self.classrooms.append(classroom)
                    self.timetable_classrooms[day][session][room] = classroom


    def _count_online_classes(self, day: str, time: str) -> int:
        """ Count the number of online classes. """
        count = 0
        for room in self.timetable_classrooms[day][time].keys():
            if "Online" in room:
                count += 1
        return count


    def _find_availability_index(self, session: str) -> int:
        """ Find the index of the session in the tutor availability list """
        index = Tutor.days.index(session[1:]) * 2       # * 2 for spreadsheet formalities (not scalable)
        return index + (1 if session[0] == "L" else 0)


    def _bind_class(self, classroom: Class, tutor: Tutor, session: str,
                      subject: str, year_level: str, class_type: str) -> None:
        """ Bind a tutor to a class and mark their slot as used. """
        classroom.students.append(tutor)
        classroom.subject = subject
        classroom.yearlevel = year_level
        classroom.classtype = class_type

        tutor.classes.append(classroom)
        tutor.availability[self._availability_index(session)] = TUTOR_ASSIGNED      # mark slot used


    def _create_class(self, tutor: Tutor, session: str, subject: str,
                      year_level: str) -> Class:
        """
        creates a class. `session` should look like "EMonday" or "LFriday".

        Returns the Class that was created.
        """
        time = "Early" if session[0] == "E" else "Late"
        day = session[1:]

        # attempt to assign a classroom if not online
        if tutor.location != "Online":
            for classroom in self.timetable_classrooms[day][time].values():
                if not classroom.students:
                    self._occupy_class(classroom, tutor, session, subject, year_level, "In-Person")
                    return classroom

        # no free room, or the tutor is online -> mint a new online room
        count = self._count_online_classes(day, time)
        classroom = Class(day, time, f"Online{count}")
        self.classrooms.append(classroom)
        self.timetable_classrooms[day][time][f"Online{count}"] = classroom
        self._occupy_class(classroom, tutor, session, subject, year_level, "Online")

        return classroom


    def _relaxation_ladder(self) -> list:
        """Ordered scheduling policies, least permissive first.

        (priorities, max_preference):
          priorities     - availability values treated as usable
                           (2 = available, 1 = potentially available)
          max_preference - how far down a tutor's year_levels list we may look

        Replaces the original attemptcounter / indexallowed mutation, which
        could spin forever.
        """
        return [
            ([TUTOR_AVAILABLE], 0),
            ([TUTOR_AVAILABLE, TUTOR_POTENTIAL], 0),
            ([TUTOR_AVAILABLE], 1),
            ([TUTOR_AVAILABLE, TUTOR_POTENTIAL], 1),
            ([TUTOR_AVAILABLE], 2),
            ([TUTOR_AVAILABLE, TUTOR_POTENTIAL], 2),
        ]


    def _can_teach(self, tutor: Tutor, year_level: str, rung) -> bool:
        priorities, max_preference = rung
        if year_level not in tutor.year_levels:
            return False
        if tutor.year_levels.index(year_level) > max_preference:
            return False
        if len(tutor.classes) >= tutor.maximum:
            return False
        window = tutor.availability[self.tutor_day_start:self.tutor_day_end]
        return any(priority in window for priority in priorities)

    def _pick_session(self, tutor: Tutor, priorities: list) -> str | None:
        """Pick a random usable slot ('EMonday'/'LFriday'), or None."""
        options = [
            index for index, value in enumerate(tutor.availability)
            if value in priorities and self.days[index] in Student.days
        ]
        if not options:
            return None
        index = self.rng.choice(options)
        return f"{'E' if index % 2 == 0 else 'L'}{self.days[index]}"

    def _slot_is_usable(self, tutor: Tutor, session: str, priorities: list) -> bool:
        index = self._availability_index(session)
        return tutor.availability[index] in priorities and self.days[index] in Student.days

    def _paired_session(self, session: str) -> str:
        return ("L" if session[0] == "E" else "E") + session[1:]

    def _create_pair(self, tutor: Tutor, year_level: str, rung) -> int:
        """Create up to two classes (the early/late pair) for one tutor."""
        priorities, _ = rung

        session = self._pick_session(tutor, priorities)
        if session is None:
            return 0

        created = 1
        self._create_class(tutor, session, tutor.subject, year_level)

        if len(tutor.classes) < tutor.maximum:
            other = self._paired_session(session)
            if self._slot_is_usable(tutor, other, priorities):
                self._create_class(tutor, other, tutor.subject, year_level)
                created += 1
        return created

    def _fill_year_level(self, year_level: str) -> None:
        """Port of the main 'while checkclasses(...)' loop.

        Walks the relaxation ladder; on each rung it makes passes over the
        tutors until a pass creates nothing, then relaxes further.
        """
        for rung in self._relaxation_ladder():
            while self._need_more_classes(year_level):
                created = 0
                for tutor in self.tutors:
                    if not self._can_teach(tutor, year_level, rung):
                        continue
                    created += self._create_pair(tutor, year_level, rung)
                if created == 0:
                    break

    def _create_surplus_classes(self) -> None:
        """ Create extra classes as most classes are usually not full. """
        surplus = floor(self.number_of_students / 50)
        subjects = ["Maths", "English"]

        for _ in range(surplus):
            for tutor in self.tutors:
                if tutor.subject != subjects[0] or len(tutor.classes) >= tutor.maximum:
                    continue
                window = tutor.availability[self.tutor_day_start:self.tutor_day_end]
                if not any(value in window for value in (1, 2)):
                    continue

                session = self._pick_session(tutor, [1, 2])
                if session is None:
                    continue

                year_level = tutor.year_levels[0]
                self._create_class(tutor, session, tutor.subject, year_level)

                if len(tutor.classes) < tutor.maximum:
                    other = self._paired_session(session)
                    if self._slot_is_usable(tutor, other, [2]):
                        self._create_class(tutor, other, tutor.subject, year_level)

                subjects.append(subjects.pop(0))


    def _setup_classes(self):
        year_levels: list[str] = list(year_levels.keys())

        current_year_level = year_levels.pop(0)
        
        while _need_more_classes(current_year_level):
            pass


    def execute():
        ...

    # TODO:
    # - fix up the rung thing
    # - fix up all the naming and comments
    # - create the actual algorithm
    # - move everything here into a separate file and class