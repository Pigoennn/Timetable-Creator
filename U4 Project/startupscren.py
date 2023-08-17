import os
import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic as PyUI
from math import ceil

# csv file directory holder variables
studentCSV = ""
tutorCSV = ""

def findui(original: str):
    try:
        basepath = sys._MEIPASS
    except AttributeError:
        basepath = os.path.abspath(".")
        relativepath = original
    else:
        mainthing = os.path.split(original)[1]
        relativepath = mainthing
    return os.path.join(basepath, relativepath)

app = QApplication(sys.argv)
sWindow = PyUI.loadUi(findui("UIfiles/startingScren.ui"))
sWindow.setWindowTitle("Timetable Creator")

def changeInfoLabel(text: str):  # For changing the info label (This is much easier to type)
    sWindow.infoTextLabel.setText(text)

def getFileName(type): # Opens the computer's folders and retrieves the directory of the selected file
    global studentCSV, tutorCSV
    file_filter = 'Data File (*.csv)'
    # Open the folder:
    response = QFileDialog.getOpenFileName(
        sWindow,
        "Choose the csv file",
        filter = file_filter
    )
    # Check if file was not empty, then identify which button was pressed
    if not str(response) == "('', '')":
        # Update student csv file if student
        if type == "student":
            studentCSV = str(response[0])
            # Change the text of the file to the directory
            sWindow.studentAvailabilityButton.setText(studentCSV)
            # Set the stylesheet of the button
            sWindow.studentAvailabilityButton.setStyleSheet("""
            QPushButton {
	            color: white;
	            background-color: #645CB8;
	            border-radius: 0px;
	            border-color: #87E2E8;
                text-align: left;
                transition: background-color 5s;
            }
            QPushButton:hover {
	            background-color: #7870cc;
            }
            QPushButton:pressed {
                background-color: #5048a4;
            }
            QToolTip{
            	background-color: rgb(232, 232, 232);
            	color: black;
            	border-color: black;
            	border-width: 2px;
            }
            """
            )
        # Update tutor csv file if tutor
        elif type == "tutor":
            tutorCSV = str(response[0])
            # Change the text of the file to the directory
            sWindow.tutorAvailabilityButton.setText(tutorCSV)
            # Set the stylesheet
            sWindow.tutorAvailabilityButton.setStyleSheet("""
            QPushButton{
	            color: white;
	            background-color: #645CB8;
	            border-radius: 0px;
	            border-color: #87E2E8;
                text-align: left;
                transition: background-color 5s;
            }
            QPushButton:hover {
	            background-color: #7870cc;
            }
            QPushButton:pressed {
                background-color: #5048a4;
            }
            QToolTip{
            	background-color: rgb(232, 232, 232);
            	color: black;
            	border-color: black;
            	border-width: 2px;
            }
            """
            )

def fileVerification():  # Verify if the csv files are correct
    message = ""
    if studentCSV == "" and tutorCSV == "":
        return "Please select your CSV Files" # If nothing given, instantly reject it
    elif studentCSV == "":
        return "Please select a Student CSV File"
    elif tutorCSV == "":
        return "Please select a Tutor CSV File"
    with open(tutorCSV, 'r') as file:
        bigFile = file.read().splitlines()
        # Check for the Tutor Availability title
        if not(bigFile[0] == str(',"') and "Tutor Availability" in bigFile[1]):
            return "Incorrect Tutor File"
    with open(studentCSV, 'r') as file:
        bigFile2 = file.read().splitlines()
        # Check the columns
        if "Timestamp,Email Address,First Name,Last Name" in bigFile2[0]:
            for eachStudent in bigFile2:  # Check if any students gave a misinput
                templist = eachStudent.split(',')
                emptyChoices = 0
                earlyandlatechoice = False
                for eachOption in templist:
                    if eachOption == "":
                        emptyChoices += 1
                    elif "Early" in eachOption and "Late" in eachOption:
                        earlyandlatechoice = True
                if emptyChoices >= 4 and not(earlyandlatechoice): # If a student has only given one choice and the choice is not both early and late, then it fails
                    return f"Student {eachStudent[2], eachStudent[3]} has error"
        else:
            return "Incorrect Student File"
    return message  # If both tests are passed, then it is verified

timetable = {}  # Timetable of Class Times
timetableClassrooms = {}  # Timetable of Classrooms
studentList = []  # List of student class
tutorList = []  # List of tutors class
availableClassrooms = []  # which Classrooms are available
classroomList = []  # list of all the classrooms (useful for later)
alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1']
mathsyearlevelnaming = {} # Naming dictionary for later
englishyearlevelnaming = {} # Naming dictionary for later
yearlevelstats = {}  # statistics of all year levels
yearlevelclassesneeded = {}  # classes still needed for each year level

def fixtemp(n: list): # Remove any " marks in each item in the given list
    list1 = list(n)
    for i in range(len(list1)):
        list1[i] = list1[i].replace("\"", "") # Replace each " in a string with nothing (if there is no " then nothing happens)
    return list1

def howmanyonlineclasses(day: str, session: str): # Find the number of already existing online classes for naming
    count = 1
    for eachroom in timetableClassrooms[day][session].keys():
        if "Online" in eachroom: # If the word "Online" is in the name of room, then add 1 to the counter
            count += 1
    return count

def yearLevelStats():  # create statistics on the year level
    global yearlevelstats, mathsyearlevelnaming, englishyearlevelnaming
    for student in studentList: # Find the year level of each student and update the dictionary
        if student.yearLevel in yearlevelstats.keys():
            yearlevelstats[student.yearLevel] += 1
        else:
            yearlevelstats[student.yearLevel] = 1
    for eachkey in yearlevelstats.keys(): # Let the naming dictionaries know what year levels exist
        mathsyearlevelnaming[eachkey] = 0
        englishyearlevelnaming[eachkey] = 0

def yearlevelcleaning():
    global yearlevelstats, studentList
    removallist = []
    for yearlevel in yearlevelstats.keys():
        if metaphoricallyspeakingISITPOSSIBLE(yearlevel):
            removallist.append(yearlevel)
            yearlevelstats[yearlevel] = 0
    if removallist:
        for student in studentList:
            if student.yearLevel in removallist:
                for i in student.classes.keys():
                    student.classes[i] = "None"
    return classesNeeded()

def metaphoricallyspeakingISITPOSSIBLE(yearlevel: str):
    amount = {
        "Maths": 0,
        "English": 0
    }
    for tutor in tutorList:
        if yearlevel in tutor.yearlevels:
            amount[tutor.subject] += tutor.availability.count(2) + tutor.availability.count(1)
    return [i for i in amount.keys() if amount[i] < yearlevelstats[yearlevel]]

def classesNeeded(): # Find the number of classes needed based on the population of the year level divided by 5 as there are 5 students in each class
    global yearlevelclassesneeded
    for eachkey in yearlevelstats.keys():
        yearlevelclassesneeded[eachkey] = ceil(yearlevelstats[eachkey] / 5) # Divide by 5 as there are 5 students in each class
    return

def checkclasses(yearlevel: str): # Check if there are enough classes for the chosen year level of each subject
    tempnum = ceil(yearlevelclassesneeded[yearlevel] * dampeningfactor) # Find the number of classes needed and multiply it by the dampening factor
    # Use a dictionary to hold the number of classes needed for each subject
    dict1 = {
        "Maths": tempnum,
        "English": tempnum
    }
    # Check each class and reduce the respective subject by 1 if it matches the year level
    for eachclass in classroomList:
        if eachclass.yearlevel == yearlevel:
            dict1[eachclass.subject] -= 1
    # Now check that the number of classes needed is negative otherwise there are not enough classes
    for i in dict1.keys():
        if dict1[i] > 0:
            return True
    return False

# Student Class. All students will have an object that contains their name, email, year level, availability, and attendance method
class Student:
    def __init__(self, email: str, firstname: str, lastname: str, yearLevel: str, place: str, Tuesday: int, Wednesday: int, Thursday: int, Friday: int, Saturday: int):
        # Update the student using the given information
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
        # Update the availability based on the given information
        for i in range(len(self.templist)):
            match self.templist[i]:
                case 0: # Is not available
                    pass
                case 1: # Available during the early session
                    self.availability.append(f'E{Student.daylist[i]}')
                case 2: # Available during the late session
                    self.availability.append(f'L{Student.daylist[i]}')
                case 3: # Available during both
                    self.availability.append(f'E{Student.daylist[i]}')
                    self.availability.append(f'L{Student.daylist[i]}')
        self.originalavailability = list(self.availability) # Copy the current availability for resetting
        # Classes dictionary for algorithm
        self.classes = {
            "Maths": None,
            "English": None
        }
        self.updatePriority() # Update the priority based on its length

    def updateName(self): # Update the students name (if another student has the same name and initial)
        self.lastnameinitial += 1
        self.name += self.lastname[self.lastnameinitial]

    def updatePriority(self): # Update the students priority and reduce it if the student already has a subject
        self.priority = len(self.availability)
        for i in self.classes.keys():
            if self.classes[i] != None: # Check if class not available then reduce priority
                self.priority -= 1
        if self.priority < 0:
            self.priority = 0
    
    def switching(self): # reset availability and remove the student's current class
        self.availability = list(self.originalavailability) # reset
        if not(self.classes["Maths"] in [None,"None"]): # Check if they actually have a Math Class
            temporary = [classroomList[self.classes["Maths"]].day, classroomList[self.classes["Maths"]].time] # Format it into the student availability format
            for i in self.availability: # Find which class is the already taken class
                if i == f'{temporary[1][0]}{temporary[0]}':
                    self.availability.pop(self.availability.index(i))
                    break
               
# Tutor Class. All tutors will have an object that represents their name, subject, year level, teaching method and availability informatino
class Tutor:
    def __init__(self, fullname: str, subject: str, yearlevel: str, listinformation: list, maximum: int, place: str):
        self.fullname = fullname.split(" ") # Fullname
        self.firstname, self.lastname = self.fullname[0], " ".join(self.fullname[1:]) # First and last name
        self.name = f'{self.firstname} {self.lastname[0]}' # Default name. First name and first letter of last name
        self.subject = subject # What subject they teach
        self.yearlevels = yearlevel.split('/') # List of year levels they teach
        for eachyear in range(len(self.yearlevels)): # Remove any " still remaining
            self.yearlevels[eachyear] = self.yearlevels[eachyear].replace("\"", '')
        self.availability = listinformation # Availability of the tutor
        self.lastnameinitial = 0 # Their current last name initial
        self.originalavailability = list(listinformation) # Original availability if needed to reset
        self.maximum = int(maximum) # Maximum number of classes they can teach
        self.classplace = place # In-Person, Online or Both
        # change all missing inputs to 0
        for eachNumber in range(len(self.availability)):
            try:
                self.availability[eachNumber] = int(self.availability[eachNumber])
            except Exception:
                self.availability[eachNumber] = 0
        self.classes = []  # create a list of all classes currently being taken
        self.extraclasses = 0

    def updateName(self): # Update their name if there is a tutor with a matching name and initials
        self.lastnameinitial += 1
        self.name += self.lastname[self.lastnameinitial]

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

sWindow.studentAvailabilityButton.clicked.connect(lambda: getFileName("student"))
sWindow.studentAvailabilityButton2.clicked.connect(lambda: getFileName("student"))
sWindow.tutorAvailabilityButton.clicked.connect(lambda: getFileName("tutor"))
sWindow.tutorAvailabilityButton2.clicked.connect(lambda: getFileName("tutor"))

with open("settings.txt", "r") as settingsfile:
    setting = settingsfile.read().splitlines()
    for line in range(len(setting)):
        setting[line] = setting[line].split(" = ") # Split the string into two different lists
    # thepossibledays for a student
    Student.daylist = setting[0][1].split(",")
    # thepossibledays for a tutor
    Tutor.daylist = setting[1][1].split(",")
    if not(Tutor.daylist[0] in Student.daylist):
        startnum = 2
    else:
        startnum = 0
    if not (Tutor.daylist[-1] in Student.daylist):
        endnum = -2
    else:
        endnum = None
    # dampening factor for class creation. 1 means no dampening. >1 Means it attempts to create more classes than necessary. <1 Means it attempts to create less classes than necessary.
    dampeningfactor = float(setting[2][1])

### HELLO
### FINISH DOCUMENTATION
### CREATE SYSTEM FOR WRITING COMPLETELY BUMMED STUDENTS INTO A TXT FILE