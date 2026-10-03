# class Class. Each class is stored as an object that has details on the day, early/late session, classroom location, tutor and students
class Class: 
    def __init__(self, day: str, time: str, classroom: str):
        self.day = day  # what day
        self.time = time  # early or late session
        self.classroom = classroom  # which classroom is it in
        self.subject = ""  # subject
        self.students = []  # list of tutor + students
        self.name = "SEL"  # naming for later
        self.yearlevel = "0"  # year level
        self.classtype = ""  # online or offline

    def removeStudent(self, student: int): # Remove a student from a class
        for students in range(len(self.students)):
            if self.students[students] == student and students != 0:
                self.students.pop(students)
                studentList[student].classes[self.subject] = None
                studentList[student].updatePriority()
                return