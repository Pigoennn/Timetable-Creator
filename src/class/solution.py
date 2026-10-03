from student import Student
from tutor import Tutor

alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1']

class Solution:
    self.timetable: dict
    self.timetable_classrooms: dict

    self.students: list[Student]
    self.tutors: list[Tutor]

    self.classrooms: list[str]

    self.maths_names: dict[int, str]
    self.english_names: dict[int, str]

    self.grade_stats = dict[int, int]
    self.classes_needed = dict[int, int]