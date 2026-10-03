from student import Student
from tutor import Tutor

alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1']

from student import Student
from tutor import Tutor
from timetable_class import Class

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

        # TODO:
        # - Continue the _setup_tutor function
        # - Find out why I'm finding the number of irrelevant rooms
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

    
    def _setup_tutor(self):
        for tutor in self.tutor_sheet:
            temp = tutor.split(",")[1:]         # first column empty
