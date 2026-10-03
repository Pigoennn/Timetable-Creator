import os
import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic as PyUI
from math import ceil
from configparser import ConfigParser

SELECTED_BUTTON_STYLE = """
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

STUDENT_CSV_HEADERS = "Timestamp,Email Address,First Name,Last Name"

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

def changeInfoLabel(text: str):
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
            print(studentCSV)
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
            print(tutorCSV)
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

def howmanyonlineclasses(day: str, session: str): # Find the number of already existing online classes for naming
    count = 1
    for eachroom in timetableClassrooms[day][session].keys():
        if "Online" in eachroom: # If the word "Online" is in the name of room, then add 1 to the counter
            count += 1
    return count



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

# File starts here

class StartScreen:
    """ Class to represent the Start screen. Includes all the buttons and file grabbing """

    self.studentCSV: str
    self.tutorCSV: str

    self.app: QApplication
    self.window: PyUI

    self.dampening_factor: float

    def __init__(self, ui_location: str, settings_file: str) -> None:
        self.app = QApplication(sys.argv)
        self.window = PyUI.loadUi(_get_location(ui_location))
        self.window.setWindowTitle("Timetable Creator")

        self.window.studentAvailabilityButton.clicked.connect(lambda: getFileName("student"))
        self.window.studentAvailabilityButton2.clicked.connect(lambda: getFileName("student"))
        self.window.tutorAvailabilityButton.clicked.connect(lambda: getFileName("tutor"))
        self.window.tutorAvailabilityButton2.clicked.connect(lambda: getFileName("tutor"))

    
    def _read_settings(self, settings_file: str):
        config = ConfigParser()
        config.read(settings_file)

        Student.days = config["Days"]["studentdays"].split(",")
        Tutor.days = config["Days"]["tutordays"].split(",")

        self.dampening_factor = float(config["Configs"]["dampening"])


    def _get_location(original: str) -> str:
        """ Get the full location of a file """
        try:
            basepath = sys._MEIPASS
        except AttributeError:
            basepath = os.path.abspath(".")
            relativepath = original
        else:
            mainthing = os.path.split(original)[1]
            relativepath = mainthing
        return os.path.join(basepath, relativepath)

    def set_info_label(text: str) -> None:
        """ Set the info label to a given string. No checks done """
        self.window.infoTextLabel.setText(text)

    def get_file(self, csv_type: str):
        """ Retrieve a CSV file TODO fix this """
        file_filter = "Data File (*.csv)"

        # open folder
        response = QFileDialog.getOpenFileName(
            self.window,
            "Choose the csv file",
            filter = file_filter
        )

        # skip if nothing returned
        if not response[0] or not response[1]:
            return

        # update the buttons
        if csv_type == "student":
            self.studentCSV = str(response[0])
            print(f"{studentCSV} selected for the student availabilities")

            self.window.studentAvailabilityButton.setText(self.studentCSV)
            self.window.studentAvailabilityButton.setStyleSheet(SELECTED_BUTTON_STYLE)
        elif csv_type == "tutor":
            self.tutorCSV = str(response[0])
            print(f"{tutorCSV} selected for the tutor availabilities")

            self.window.tutorAvailabilityButton.setText(self.tutorCSV)
            self.window.tutorAvailabilityButton.setStyleSheet(SELECTED_BUTTON_STYLE)


    def verify_file(self) -> str:
        """ Verifies if a given file fits the standards of either the student or tutor csv file """
        if self.studentCSV == "" and self.tutorCSV == "":
            return "Please select your CSV files"
        if self.studentCSV == "":
            return "Please select a Student CSV file"
        if self.tutorCSV == "":
            return "Please select a Tutor CSV file"
        
        with open(self.tutorCSV, "r") as tutor_file:
            tutor_availabilities = tutor_file.read().splitlines()
            if not(tutor_availabilities[0] == str(',"') and "Tutor Availability" in bigFile[1]):
                return "Tutor file has inconsistencies"
            
        with open(self.studentCSV, "r") as student_file:
            student_availabilities = file.read().splitlines()

            if not(STUDENT_CSV_HEADERS in student_availabilities[0]):
                return "Student file has inconsistencies"
            
            for student in student_availabilities:  # Check if any students gave a misinput
                temp_list = student.split(',')
                empty_choices = 0
                chose_both_times = False
                for option in temp_list:
                    if option == "":
                        empty_choices += 1
                    elif "Early" in option and "Late" in option:
                        chose_both_times = True
                if empty_choices >= 4 and not(chose_both_times): # If a student has only given one choice and the choice is not both early and late, then it fails
                    return f"Student {student[2], student[3]} has error"