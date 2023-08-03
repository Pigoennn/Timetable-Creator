import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6 import uic as PyUI
from math import ceil

app = QApplication(sys.argv)
sWindow = PyUI.loadUi("startingScren.ui")
sWindow.setWindowTitle("Timetable Creator")

# csv file directory holder variables
studentCSV = "/Users/jonathan/Downloads/Student Availability Spreadsheet (Form Responses) - Form Responses 1 (4).csv"
tutorCSV = "/Users/jonathan/Downloads/Tutor Availability Spreadsheet - Availabilities (3).csv"

dampeningfactor = 1 # dampening factor for class creation

def changeInfoLabel(text: str):  # This is much easier to type
    sWindow.infoTextLabel.setText(text)


def getFileName(type):
    global studentCSV, tutorCSV
    file_filter = 'Data File (*.csv)'
    response = QFileDialog.getOpenFileName(
        sWindow,
        "Choose the csv file",
        filter=file_filter
    )
    # print(str(response))
    if not str(response) == "('', '')":
        if type == "student":
            studentCSV = str(response[0])
            # print(studentCSV)
            sWindow.studentAvailabilityButton.setText(studentCSV)
            sWindow.studentAvailabilityButton.setStyleSheet("""
            QPushButton{
	            color: rgb(255,255,255);
	            background-color: #645CB8;
	            border-radius: 0px;
	            border: 1px solid #87E2E8;
                text-align: left;
            }

            QToolTip{
            	background-color: rgb(232, 232, 232);
            	color: rgb(0, 0, 0);
            	border-color: rgb(0, 0, 0);
            	border-width: 2px;
            }
            """
            )
        elif type == "tutor":
            tutorCSV = str(response[0])
            # print(tutorCSV)
            sWindow.tutorAvailabilityButton.setText(tutorCSV)


def fileVerification():  # Verify if the csv files are correct
    if studentCSV == "" or tutorCSV == "":
        return False
    verified = 0
    with open(tutorCSV, 'r') as file:
        bigFile = file.read().splitlines()
        # Check for the Tutor Availability title
        if bigFile[0] == str(',"') and "Tutor Availability" in bigFile[1]:
            print("tutor passed")
            verified += 1
    with open(studentCSV, 'r') as file:
        print('student happening')
        bigFile2 = file.read().splitlines()
        # Check the columns
        if "Timestamp,Email Address,First Name,Last Name," in bigFile2[0]:
            for eachStudent in bigFile2:  # Check if any students gave a misinput
                templist = eachStudent.split(',')
                emptyChoices = 0
                for eachOption in templist:
                    if eachOption == "":
                        emptyChoices += 1
                if emptyChoices >= 4:
                    print("set to zero")
                    # Set verified to 0 if a student has an incorrect choice. This ensures that verified cannot reach 2 and thus is not verified.
                    verified = 0
            verified += 1
            print("this happened")
    print(verified)
    return bool(verified == 2)  # If both tests are passed, then it is verified


timetable = {}  # Timetable of Classe Times
timetableClassrooms = {}  # Timetable of Classrooms
studentList = []  # List of student class
tutorList = []  # List of tutors class
availableClassrooms = []  # which Classrooms are available
classroomList = []  # list of all the classrooms (useful for later)
alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1']
mathsyearlevelnaming = {}
englishyearlevelnaming = {}
yearlevelstats = {}  # statistics of all the year level
yearlevelclassesneeded = {}  # classes still needed for each year level
numberOfClasses = 0

def fixtemp(n: list):
    templist = []
    for item in range(len(n)):
        if n[item] != "":
            if n[item][0] == "\"":
                templist.append(item)
    final = list(n)
    num = 0
    for i in templist:
        final[i-num] = f'{final[i-num][1:]} {final.pop(i+1-num)[:-1]}'
        num += 1
    return final

def howmanyonlineclasses(day: str, session: str):
    count = 1
    for eachroom in timetableClassrooms[day][session].keys():
        if "Online" in eachroom:
            count += 1
    return count

def defineyearlevel(tutor: int):
    classesNeeded()
    possibleyearlevels = tutorList[tutor].yearlevels
    mostneeded = ["0", 0]
    for eachyear in yearlevelclassesneeded.keys():
        if yearlevelclassesneeded[eachyear] > mostneeded[1] and eachyear in possibleyearlevels:
            mostneeded = [eachyear, yearlevelclassesneeded[eachyear]]
    return mostneeded[0]

def priorityCheck():  # returns False if all tutors have a priority of 0
    for tutor in tutorList:
        print(f'{tutor.name}: {tutor.priority}')
        print("ayo")
        if tutor.priority == 0 or len(tutor.classes) == tutor.maximum:
            pass
        else:
            return True
    return False

def yearLevelStats():  # create statistics on the year level
    print("bonjourrr")
    global yearlevelstats, mathsyearlevelnaming, englishyearlevelnaming
    for student in studentList:
        if student.yearLevel in yearlevelstats.keys():
            yearlevelstats[student.yearLevel] += 1
        else:
            yearlevelstats[student.yearLevel] = 1
    print(yearlevelstats)
    num = 0
    for i in yearlevelstats.values():
        num += 1
    for eachkey in yearlevelstats.keys():
        mathsyearlevelnaming[eachkey] = 0
        englishyearlevelnaming[eachkey] = 0
    classesNeeded()
    return num

def classesNeeded():
    global yearlevelclassesneeded
    for eachkey in yearlevelstats.keys():
        yearlevelclassesneeded[eachkey] = ceil(yearlevelstats[eachkey] / 5)

def checkclasses(yearlevel: int):
    print(yearlevelclassesneeded[str(yearlevel)] * dampeningfactor)
    tempnum = ceil(yearlevelclassesneeded[str(yearlevel)] * dampeningfactor)
    #print("Tempnum: " + str(tempnum))
    dict1 = {
        "Maths": tempnum,
        "English": tempnum
    }
    for eachclass in classroomList:
        #print(f'Value of {eachclass.yearlevel} with type of {type(eachclass.yearlevel)}')
        #print(f'{yearlevel} and {type(yearlevel)}')
        if eachclass.yearlevel == yearlevel:
            dict1[eachclass.subject] -= 1
    print(dict1)
    for i in dict1.keys():
        if dict1[i] > 0:
            return True
    return False

class Student:
    daylist = ["Tuesday", "Wednesday", "Thursday","Friday", "Saturday"]  # list of possible days

    def __init__(self, email: str, firstname: str, lastname: str, yearLevel: str, place: str, Tuesday: int, Wednesday: int, Thursday: int, Friday: int, Saturday: int):
        self.firstname = firstname
        self.lastname = lastname
        self.name = f'{firstname} {lastname[0]}'
        self.email = email
        self.yearLevel = str(yearLevel[5:])
        self.place = place
        self.lastnameinitial = 0
        self.templist = [Tuesday, Wednesday, Thursday, Friday, Saturday]
        self.availability = []
        self.subject = ""
        for i in range(len(self.templist)):
            match self.templist[i]:
                case 0:
                    pass
                case 1:
                    self.availability.append(f'E{Student.daylist[i]}')
                case 2:
                    self.availability.append(f'L{Student.daylist[i]}')
                case _:
                    self.availability.append(f'E{Student.daylist[i]}')
                    self.availability.append(f'L{Student.daylist[i]}')
        self.originalavailability = list(self.availability)
        print(self.availability)
        self.classes = {
            "Maths": None,
            "English": None
        }
        self.updatePriority()
        self.switchattempts = 0

    def updateName(self):
        self.lastnameinitial += 1
        self.name += self.lastname[self.lastnameinitial]

    def updatePriority(self):
        self.priority = len(self.availability)
        for i in self.classes.keys():
            if self.classes[i] != None:
                self.priority -= 1
    
    def switching(self): # reset availability and remove the class already in it
        self.availability = list(self.originalavailability)
        if not(self.classes["Maths"] in [None,"None"]):
            temporary = [classroomList[self.classes["Maths"]].day, classroomList[self.classes["Maths"]].time]
            for i in self.availability:
                if i == f'{temporary[1][0]}{temporary[0]}':
                    self.availability.pop(self.availability.index(i))
                    break

class Tutor:
    daylist = ["Monday", "Tuesday", "Wednesday","Thursday", "Friday", "Saturday"]

    def __init__(self, fullname: str, subject: str, yearlevel: str, listinformation: list, maximum: int, place: str):
        self.fullname = fullname.split(" ")
        self.firstname, self.lastname = self.fullname[0], self.fullname[1]
        self.name = f'{self.firstname} {self.lastname[0]}'
        self.subject = subject
        self.yearlevels = yearlevel.split('/')
        for eachyear in range(len(self.yearlevels)):
            self.yearlevels[eachyear] = self.yearlevels[eachyear].replace(
                "\"", '')
        self.availability = listinformation
        self.lastnameinitial = 0
        self.originalavailability = list(listinformation)
        self.maximum = int(maximum)
        self.classplace = place
        # change all missing inputs to 0
        for eachNumber in range(len(self.availability)):
            try:
                self.availability[eachNumber] = int(
                    self.availability[eachNumber])
            except Exception:
                self.availability[eachNumber] = 0
        self.updatepriority()  # set priority
        self.updatepriority1()  # set extra priority
        self.classes = []  # create a list of all classes currently being taken
        self.extraclasses = 0

    def updateName(self):
        self.lastnameinitial += 1
        self.name += self.lastname[self.lastnameinitial]

    def updatepriority(self):
        self.priority = self.availability.count(2)

    def updatepriority1(self):
        self.newpriority = self.availability.count(1)

class Class:  # create class for Classes
    def __init__(self, day: str, time: str, classroom: str):
        self.day = day  # what day
        self.time = time  # early or late session
        self.classroom = classroom  # which classroom is it in
        self.subject = ""  # subject
        self.students = []  # list of tutor + students
        self.name = "SEL"  # naming for later
        self.yearlevel = 0  # year level
        self.classtype = ""  # online or offline

    def removeStudent(self, student: int): # Remove a student
        print(f"The length of this thing is {len(self.students)}")
        print(bool(student in self.students[1:]))
        for students in range(len(self.students)):
            if self.students[students] == student and students != 0:
                self.students.pop(students)
                return # clear

sWindow.studentAvailabilityButton.clicked.connect(
    lambda: getFileName("student"))
sWindow.studentAvailabilityButton2.clicked.connect(
    lambda: getFileName("student"))
sWindow.tutorAvailabilityButton.clicked.connect(lambda: getFileName("tutor"))
sWindow.tutorAvailabilityButton2.clicked.connect(lambda: getFileName("tutor"))