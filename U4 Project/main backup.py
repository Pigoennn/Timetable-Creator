import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6 import uic as PyUI
from math import ceil

app = QApplication(sys.argv)

sWindow = PyUI.loadUi("startingScren.ui")
sWindow.setWindowTitle("Timetable Creator")

#csv file directory holder variables
studentCSV = "/Users/jonathan/Downloads/Student Availability Spreadsheet (Form Responses) - Form Responses 1 (2).csv"
tutorCSV = "/Users/jonathan/Downloads/Tutor Availability Spreadsheet - Availabilities (3).csv"

def changeInfoLabel(text: str):  # This is much easier to type
    sWindow.infoTextLabel.setText(text)

def getFileName(type):
    global studentCSV, tutorCSV
    file_filter = 'Data File (*.csv)'
    response = QFileDialog.getOpenFileName(
        sWindow,
        "Choose the csv file",
        filter = file_filter
    )
    print(str(response))
    if not str(response) == "('', '')":
        if type == "student":
            studentCSV = str(response[0])
            print(studentCSV)
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
            print(tutorCSV)     
            sWindow.tutorAvailabilityButton.setText(tutorCSV)

def fileVerification(): #Verify if the csv files are correct
    if studentCSV == "" or tutorCSV == "":
        return False
    verified = 0
    with open(tutorCSV, 'r') as file:
        bigFile = file.read().splitlines()
        if bigFile[0] == str(',"') and "Tutor Availability" in bigFile[1]: #Check for the Tutor Availability title
            print("tutor passed")
            verified += 1
    with open(studentCSV, 'r') as file:
        bigFile2 = file.read().splitlines()
        if "Timestamp,Email Address,First Name,Last Name,Year Level" in bigFile2[0]: #Check the columns
            for eachStudent in bigFile2: #Check if any students gave a misinput
                templist = eachStudent.split(',')
                emptyChoices = 0
                for eachOption in templist:
                    if eachOption == "":
                        emptyChoices += 1
                if emptyChoices >= 3:
                    print("set to zero")
                    verified = 0 #Set verified to 0 if a student has an incorrect choice. This ensures that verified cannot reach 2 and thus is not verified.
            verified += 1
            print("this happened")
    print(verified)
    return bool(verified == 2) #If both tests are passed, then it is verified

timetable = {} #Timetable of Classe Times
timetableClassrooms = {} #Timetable of Classrooms
studentList = [] #List of student class
tutorList = [] #List of tutors class
availableClassrooms = [] #which Classrooms are available
classroomList = [] #list of all the classrooms (useful for later)
alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'Q1', 'R1', 'S1', 'T1', 'U1', 'V1', 'W1', 'X1', 'Y1', 'Z1']
mathsyearlevelnaming = {}
englishyearlevelnaming = {}
yearlevelstats = {} #statistics of all the year level
yearlevelclassesneeded = {} #classes still needed for each year level
numberOfClasses = 0

def programBegin(): #Begin the creation process
    global timetable, numberOfStudents, studentList, availableClassrooms, timetableClassrooms, classroomList, numberOfClasses, mathsyearlevelnaming, englishyearlevelnaming
    if not fileVerification():  #Check the files first if they are correct
        return changeInfoLabel("Please select the correct .csv sheet") #stop function if not verified
    #begin class creating process
    #start with creating possible time slots
    with open(tutorCSV, "r") as file:
        tutorSheet = file.read().splitlines()
        tutorSheet = tutorSheet[3:]
    daysPossible = tutorSheet.pop(0).split(',')[4:] #create a separate list with all the given days
    for eachOption in range(len(daysPossible)): #get rid of the missing spaces and replace it with the correct day
        if daysPossible[eachOption] == "What is the maximum number of classes you would like?":
            stopLimit = eachOption
            daysPossible = daysPossible[:eachOption]
            break
        else:
            if daysPossible[eachOption] == "":
                daysPossible[eachOption] = daysPossible[eachOption-1]
    timesPossible = tutorSheet.pop(0).split(',')[4:stopLimit+4] #create a separate list with all the given times
    for eachTime in range(len(timesPossible)): #add the given times according to the given days in a dictionary
        if daysPossible[eachTime] in timetable.keys():
            timetable[daysPossible[eachTime]].append(timesPossible[eachTime])
        else:
            timetable[daysPossible[eachTime]] = [timesPossible[eachTime]]
    for i in timetable.keys():
        print(f'{i}: {timetable[i]}')
    with open(studentCSV, "r") as file: #start student creation process
        studentSheet = file.read().splitlines()[1:]
        numberOfStudents = len(studentSheet)
        print(studentSheet)
        print("hello")
        for eachStudent in studentSheet:
            temp = eachStudent.split(',')[1:]
            for eachStat in range(len(temp)):
                if eachStat in range(5):
                    pass
                else:
                    if "Early" in temp[eachStat] and "Late" in temp[eachStat]:
                        temp[eachStat] = 3
                    elif "Early" in temp[eachStat]:
                        temp[eachStat] = 1
                    elif "Late" in eachStudent[eachStat]:
                        temp[eachStat] = 2
                    else:
                        temp[eachStat] = 0
            studentList.append(Student(temp[0],temp[1],temp[2],temp[3],temp[4],temp[5],temp[6],temp[7],temp[8],temp[9])) #Create a Class for each student
            print(studentList)
    #check for duplicates
    duplicate = True
    while duplicate == True:  # run a while loop to remove all duplicate names
        duplicate = False
        temp = []
        for eachStudent in studentList:
            temp.append(eachStudent.name)
        for i in temp:
            if temp.count(i) > 1:
                duplicate = True
                theIndex = temp.index(i)
                studentList[theIndex].updateName()  # add an additional letter
    #start creating empty classes based off tutors
    numberOfClasses = yearLevelStats()
    for eachLine in tutorSheet:  # find the number of rooms available
        if "Rooms:" in eachLine:
            # find the possible rooms via the next line after finding the key word
            availableClassrooms = tutorSheet[tutorSheet.index(eachLine)+1].split("\"")[1]
            availableClassrooms = availableClassrooms.split(',')  # turn into list
            tutorSheet = tutorSheet[0:tutorSheet.index(eachLine)]
            break
    #create tutor class
    for eachTutor in tutorSheet:
        temp = eachTutor.split(',')[1:]
        if temp[0] == "":
            pass
        else:
            print((temp[0], temp[1], temp[2], temp[3:15], temp[15], temp[16]))
            tutorList.append(Tutor(temp[0],temp[1],temp[2],temp[3:15],temp[15],temp[16])) #Create Tutor Class
    #check for any duplicate names
    duplicate = True
    while duplicate == True: #run a while loop to remove all duplicate names
        duplicate = False
        temp = []
        for eachTutor in tutorList:
            temp.append(eachTutor.name)
        for i in temp:
            if temp.count(i) > 1:
                duplicate = True
                theIndex = temp.index(i)
                tutorList[theIndex].updateName() #add an additional letter
                break
    for i in tutorList:
        print(f'{i.name} has {i.availability} and priority of {i.priority}')
    #begin the true Class creation process
    for i in timetable.keys():
        timetableClassrooms[i] = {
            "Early": {},
            "Late": {}
        }
        earlysession = True
        for j in range(2):
            if earlysession:
                session = "Early"
            else:
                session = "Late"
            for eachroom in availableClassrooms:
                classroomList.append(Class(i, session, eachroom))
                timetableClassrooms[i][session][eachroom] = len(classroomList)-1 #index identity
            earlysession = not(earlysession)
    #print(timetableClassrooms)
    #print(daysPossible)
    #print(classroomList)
    # check if any classroom is available before creating then add tutor to it and then update tutor
    while priorityCheck():
        for tutor in tutorList:
            if (tutor.priority) and len(tutor.classes) < tutor.maximum:
                for value in range(len(tutor.availability)):
                    if tutor.availability[value] == 0 or tutor.availability[value] == 3:
                        pass
                    elif tutor.availability[value] == 2:
                        temp = [daysPossible[value]]
                        #add a second value to the list, indicating whether it is the early or late session
                        if value % 2 == 0:
                            temp.append("Early") #early
                        else:
                            temp.append("Late") #late
                        if not(tutor.classplace == "Online"):
                            for eachroom in timetableClassrooms[temp[0]][temp[1]].keys(): #check for empty classroom and then create a class in it
                                if len(classroomList[timetableClassrooms[temp[0]][temp[1]][eachroom]].students) == 0:
                                    #create a Class
                                    tempindex = timetableClassrooms[temp[0]][temp[1]][eachroom]
                                    classroomList[tempindex].students.append(tutor)  # add tutor to the classroom
                                    tutor.classes.append(classroomList[tempindex]) #update Class to tutor
                                    tutor.availability[value] = 3
                                    tutor.updatepriority() #change availability to 3, meaning there is a class and update the priority
                                    classroomList[tempindex].classtype = "In-Person"
                                    tempyearlevel = defineyearlevel(tutor)
                                    enoughClassesCheck()
                                    #print(classroomList)
                                    print(tempyearlevel)
                                    classroomList[tempindex].subject = tutor.subject
                                    if tutor.subject == "Maths":
                                        classroomList[tempindex].name += f"MAT {tempyearlevel}{alphabet[mathsyearlevelnaming[tempyearlevel]]}"
                                        classroomList[tempindex].yearlevel = int(tempyearlevel)
                                        mathsyearlevelnaming[tempyearlevel] += 1
                                    elif tutor.subject == "English":
                                        classroomList[tempindex].name += f"ENG {tempyearlevel}{alphabet[englishyearlevelnaming[tempyearlevel]]}"
                                        classroomList[tempindex].yearlevel = int(tempyearlevel)
                                        englishyearlevelnaming[tempyearlevel] += 1
                                    break
                        else:
                            tempnum = howmanyonlineclasses(temp[0], temp[1])
                            classroomList.append(Class(temp[0], temp[1], f"Online{tempnum}"))
                            timetableClassrooms[temp[0]][temp[1]][f"Online{tempnum}"] = len(classroomList) - 1
                            tempindex = len(classroomList) - 1
                            classroomList[tempindex].students.append(tutor)  # add tutor to the classroom
                            # update Class to tutor
                            tutor.classes.append(classroomList[tempindex])
                            tutor.availability[value] = 3
                            # change availability to 3, meaning there is a class and update the priority
                            tutor.updatepriority()
                            classroomList[tempindex].classtype = "Online"
                            tempyearlevel = defineyearlevel(tutor)
                            enoughClassesCheck()
                            #print(classroomList)
                            print(tempyearlevel)
                            classroomList[tempindex].subject = tutor.subject
                            if tutor.subject == "Maths":
                                classroomList[tempindex].name += f"MAT {tempyearlevel}{alphabet[mathsyearlevelnaming[tempyearlevel]]}"
                                classroomList[tempindex].yearlevel = int(tempyearlevel)
                                mathsyearlevelnaming[tempyearlevel] += 1
                            elif tutor.subject == "English":
                                classroomList[tempindex].name += f"ENG {tempyearlevel}{alphabet[englishyearlevelnaming[tempyearlevel]]}"
                                classroomList[tempindex].yearlevel = int(tempyearlevel)
                                englishyearlevelnaming[tempyearlevel] += 1
                            break
    print(timetableClassrooms)
    '''
    for i in tutorList:
        print(f'{i.name}: {i.availability}')
        print(f'{i.name}: {i.classes}')
    '''
    for i in classroomList:
        print(i.name)
    #check number of classes, if not enough for each year level then add more
    temp = enoughClassesCheck()
    try:
        createOnlineClasses(temp[0],daysPossible)
        createOnlineClasses(temp[1],daysPossible)
    except Exception:
        pass
    switchScreens()

def createOnlineClasses(n: list, daysPossible): #create more classes since there aren't enough
    subject = n[0]
    amountneeded = n[1]
    #first check which tutor has the least number of classes
    while not(amountneeded == 0): #now create the classes until everything has been made
        leastlist = [None, 10000]
        for eachtutor in tutorList:  # find the tutor with least number of classes
            tempnum = len(eachtutor.classes)
            if tempnum < eachtutor.maximum and eachtutor.subject == subject:
                if tempnum < leastlist[1]:
                    leastlist = [eachtutor, tempnum]
        tutor = leastlist[0]
        for value in range(len(tutor.availability)):
            if tutor.availability == 2:
                temp = [daysPossible[value]]
                if value % 2 == 0:
                    temp.append("Early")  # early
                else:
                    temp.append("Late") #late
                tempnum = howmanyonlineclasses(temp[0], temp[1])
                classroomList.append(Class(temp[0], temp[1], f"Online{tempnum}"))
                timetableClassrooms[temp[0]][temp[1]][f"Online{tempnum}"] = len(classroomList) - 1
                tempindex = timetableClassrooms[temp[0]][temp[1]][f"Online{tempnum}"]
                classroomList[tempindex].students.append(tutor)  # add tutor to the classroom
                # update Class to tutor
                tutor.classes.append(classroomList[tempindex])
                tutor.availability[value] = 3 #change availability to 3, meaning there is a class and update the priority
                tutor.updatepriority()
                classroomList[tempindex].classtype = "Online"
                tempyearlevel = defineyearlevel(tutor)
                enoughClassesCheck()
                # print(classroomList)
                print(tempyearlevel)
                classroomList[tempindex].subject = tutor.subject
                if tutor.subject == "Maths":
                    classroomList[tempindex].name += f"MAT {tempyearlevel}{alphabet[mathsyearlevelnaming[tempyearlevel]]}"
                    classroomList[tempindex].yearlevel = int(tempyearlevel)
                    mathsyearlevelnaming[tempyearlevel] += 1
                elif tutor.subject == "English":
                    classroomList[tempindex].name += f"ENG {tempyearlevel}{alphabet[englishyearlevelnaming[tempyearlevel]]}"
                    classroomList[tempindex].yearlevel = int(tempyearlevel)
                    englishyearlevelnaming[tempyearlevel] += 1
                break
        amountneeded -= 1

def howmanyonlineclasses(day: str, session: str):
    count = 1
    for eachroom in timetableClassrooms[day][session].keys():
        if "Online" in eachroom:
            count += 1
    return count

def defineyearlevel(tutor: object):
    possibleyearlevels = tutor.yearlevels
    mostneeded = ["0",0]
    for eachyear in yearlevelclassesneeded.keys():
        if yearlevelclassesneeded[eachyear] > mostneeded[1] and eachyear in possibleyearlevels:
            mostneeded = [eachyear,yearlevelclassesneeded[eachyear]]
    return mostneeded[0]

def enoughClassesCheck(): #check if there are enough classes for all subjects
    fixingList = []
    for eachsubject in ["Maths", "English"]:
        num = 0
        for eachclass in classroomList:
            if eachclass.subject == eachsubject:
                num += 1
        if num >= numberOfClasses:
            pass
        else:
            fixingList.append([eachsubject,num - numberOfClasses])
    return fixingList

def priorityCheck(): #returns False if all tutors have a priority of 0
    for tutor in tutorList:
        print(f'{tutor.name}: {tutor.priority}')
        if tutor.priority == 0:
            pass
        else:
            return True
    return False

def yearLevelStats(): #create statistics on the year level
    print("bonjourrr")
    global yearlevelstats, mathsyearlevelnaming, englishyearlevelnaming
    for student in studentList:
        if student.yearLevel in yearlevelstats:
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

class Student:
    daylist = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"] #list of possible days
    def __init__(self, email: str, firstname: str, lastname: str, yearLevel: str, place: str,Tuesday: int,Wednesday: int,Thursday: int,Friday: int,Saturday: int):
        self.firstname = firstname
        self.lastname = lastname
        self.name = f'{firstname} {lastname[0]}'
        self.email = email
        self.yearLevel = str(yearLevel[5:])
        print(self.yearLevel)
        self.place = place
        self.lastnameinitial = 0
        templist = [Tuesday,Wednesday,Thursday,Friday,Saturday]
        self.availability = []
        self.subject = ""
        for i in range(len(templist)):
            if templist[i] == 0:
                pass
            elif templist[i] == 1:
                self.availability.append(f'E{Student.daylist[i]}')
            elif templist[i] == 2:
                self.availability.append(f'L{Student.daylist[i]}')
            else:
                self.availability.append(f'E{Student.daylist[i]}')
                self.availability.append(f'L{Student.daylist[i]}')
        self.originalavailability = list(self.availability)
        self.classes = {
            "Maths": None,
            "English": None
        }
        self.updatePriority()
        self.focussubject = "Maths"
        self.switchattempts = 0
    def updateName(self):
        self.name += self.lastname[self.lastnameinitial]
    def updatePriority(self):
        self.priority = len(self.availability)
        for i in self.classes.keys():
            if self.classes[i] != None:
                self.priority -= 1
    def switchfocus(self,subject):
        if subject == "Maths":
            self.focussubject = "English"
        else:
            self.focussubject = "Maths"
    def missingsubject(self):
        tempnum = 0
        tempvar = ""
        for item in self.classes.keys():
            if self.classes[item] == None:
                tempnum += 1
                tempvar = item
        print(tempnum)
        return [tempnum,tempvar]

class Tutor:
    daylist = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    def __init__(self,fullname: str,subject: str, yearlevel: str, listinformation:list, maximum: int, place: str):
        self.fullname = fullname.split(" ")
        self.firstname, self.lastname = self.fullname[0], self.fullname[1]
        self.name = f'{self.firstname} {self.lastname[0]}'
        self.subject = subject
        self.yearlevels = yearlevel.split('/')
        for eachyear in range(len(self.yearlevels)):
            self.yearlevels[eachyear] = self.yearlevels[eachyear].replace("\"",'')
        self.availability = listinformation
        self.lastnameinitial = 0
        self.maximum = int(maximum)
        self.classplace = place
        #change all missing inputs to 0
        for eachNumber in range(len(self.availability)):
            try:
                self.availability[eachNumber] = int(self.availability[eachNumber])
            except Exception:
                self.availability[eachNumber] = 0
        self.updatepriority() #set priority
        self.updatepriority1() #set extra priority
        self.classes = [] #create a list of all classes currently being taken
        self.extraclasses = 0
    def updateName(self):
        self.lastnameinitial += 1
        self.name += self.lastname[self.lastnameinitial]
    def updatepriority(self):
        self.priority = self.availability.count(2)
    def updatepriority1(self):
        self.newpriority = self.availability.count(1)

class Class: #create class for Classes
    def __init__(self, day: str, time: str, classroom: str):
        self.day = day
        self.time = time #early or late session
        self.classroom = classroom #which classroom is it in
        self.subject = "" #subject
        self.students = [] #list of tutor + students
        self.name = "SEL " #naming for later
        self.yearlevel = 0 #year level
        self.classtype = "" #online or offline

    def removeStudent(self, student: object):
        for i in range(len(self.students)):
            if self.students[i] == student:
                self.students.remove(i)
                return
        
sWindow.studentAvailabilityButton.clicked.connect(lambda: getFileName("student"))
sWindow.studentAvailabilityButton2.clicked.connect(lambda: getFileName("student"))
sWindow.tutorAvailabilityButton.clicked.connect(lambda: getFileName("tutor"))
sWindow.tutorAvailabilityButton2.clicked.connect(lambda: getFileName("tutor"))

sWindow.CreateTimetableButton.clicked.connect(lambda: programBegin())

###-------------------------------------------------------------------------------
#Loading Screen

lWindow = PyUI.loadUi("loadingScren.ui")
lWindow.setWindowTitle("Creating Classes...")

lWindow.progressBar.setValue(0)

def switchScreens(): #switch screens
    sWindow.close()
    lWindow.show()
    startAlgorithm()

def startAlgorithm(): #start adding students to class
    while not(checkstudents()):
        for student in studentList:
            missingclasses = student.missingsubject()
            if missingclasses[0] == 0: #check the student doesn't have enough classes
                pass #they don't need any classes
            else:
                theindex = checkviableClass(studentList.index(student),tempsubject)
                if theindex == None: #occurs if no class available
                    #first we're going to see if the student has no other option
                    #check for priority. This is the hard part
                    #find out how you're going to solve this issue
                    #REDO THIS WHOLE SECTION
                    pass
                    #force a class
                else:
                    classroomList[theindex].students.append(student)
                    student.currentClasses.append(theindex)
    print("LETS GO WE DONE")
    #rework the section
    #run two algorithms but on the same subject

def checkstudents():
    for student in studentList:
       if student.missingsubject()[0] > 0: #this means they have no missing classes
           return False
    return True

def checkPreference(student: int):
    day = studentList[student].availability.pop(0)
    studentList[student].updatePriority()
    if day[0] == "E":
        session = "Early"
    else:
        session = "Late"
    nlist = []
    for classroom in timetableClassrooms[day[1:]][session].keys():
        tempobject = classroomList[timetableClassrooms[day[1:]][session][classroom]]
        if tempobject.yearlevel == studentList[student].yearLevel and tempobject.subject == studentList[student].focussubject:
            nlist.append(timetableClassrooms[day[1:]][session][classroom])
    ###MAKE CODE IF NO CLASSES FIT THE STUDENT
    #CHECK IF STUDENT HAS NO OTHER CLASSES LEFT (DO THE SWITCHEROO IF ONE LEFT OR CREATE NEW CLASS)
    #IF NOT, JUST SKIP THE CLASS AND RETURN
    if len(nlist) == 0:
        if studentList[student].priority in [0,1]:
            attemptswitch(student, session)
    finallist = []
    for eachclass in nlist: #check if any of the classes have an open seat
        if len(classroomList[eachclass].students) < 6:
            finallist.append(eachclass)
    if len(finallist) == 0:
        finallist = list(nlist)
        studentshifting(finallist,student)
    else:
        #add a new student to the class and update all details
        addstudent(nlist[0],student)

def attemptswitch(student: int, session: str):
    chosensession = [None,None] #[day,session]
    #first, figure out if the student is switching with their other class or availability
    if len(studentList[student].availability) == 0: #this means they are switching time with already taken class
        #figure out which class is the taken one
        chosensession = [classroomList[studentList[student].classes[studentList[student].focussubject]].day, classroomList[studentList[student].classes[studentList[student].focussubject]].session]
        if classexists(chosensession[0], chosensession[1], studentList[student].yearLevel, studentList[student].focussubject):
            studentList[student].switchfocus()
        else:
            return noclassexist(student, session)
    else: #switching with their other availability
        studentList[student].availability.append(session)
        tempvar = studentList[student].availability.pop(0)
        if tempvar[0] == "E":
            tempsession = "Early"
        else:
            tempsession = "Late"
        chosensession = [tempvar[1:],tempsession]
        studentList[student].switchfocus()    
    for room in timetableClassrooms[chosensession[0]][chosensession[1]].keys():
        if len(classroomList[timetableClassrooms[chosensession[0]][chosensession[1]][room]].students) == 6 and classroomList[timetableClassrooms[chosensession[0]][chosensession[1]][room]].subject == studentList[student].subject and classroomList[timetableClassrooms[chosensession[0]][chosensession[1]][room]].subject == studentList[student].focussubject:
            if checknotsame(classroomList[timetableClassrooms[chosensession[0]][chosensession[1]][room]],student):
                addstudent(timetableClassrooms[chosensession[0]][chosensession[1]][room],student)
                studentList[student].switchattempts += 1

def noclassexist(student: int, classsession: str): #contingency plan. what happens when the student has no classes that exist
    #first step. check if any of the other availabilities are possible
    alreadytakensession = [classroomList[studentList[student].classes["Maths" if studentList[student].classes["Maths"] != None else "English"]].day, classroomList[studentList[student].classes["Maths"]].session]
    #figure out what session does and create the contingency plan. after this you are basically done
    #session is where you are going to create a class if needed
    for availability in studentList[student].availability:
        if availability[0] == "E":
            session = "Early"
        else:
            session = "Late"
        possiblelist = []
        if classexists(availability[1:], session, studentList[student].yearLevel, studentList[student].focussubject):
            for item in timetableClassrooms[availability[1:]][session]:
                if classroomList[timetableClassrooms[availability[1:]][session][item]].yearlevel == studentList[student].yearLevel and classroomList[timetableClassrooms[availability[1:]][session][item]].subject == studentList[student].focussubject:
                    possiblelist.append(timetableClassrooms[availability[1:]][session][item])

def studentshifting(nlist: list, student: int):
    # find the student with the highest priority
    tempstudent = [0, None, 0]  # First represents class, second represents index, third represents their priority
    for item in nlist:
        for eachstudent in classroomList[item].student[1:]:
            if studentList[eachstudent].priority > tempstudent[2]:
                tempstudent = [item, eachstudent,studentList[eachstudent].priority]
    # kick the student with the highest priority IF it's higher than the current student
    if tempstudent > studentList[student].priority: 
        kickstudent(item, tempstudent, student) #kicks the student and adds a new one
        return True
    else:
        return False

def kickstudent(classroom: int, studenttokick: int, studenttoadd: int):
    classroomList[classroom].removeStudent(studentList(studenttokick))
    if classroomList[classroom].subject == "Maths":
        num = 0
    else:
        num = 1
    studentList[studenttokick].currentClasses[num] = None
    studentList[studenttokick].updatePriority()
    addstudent(classroom,studenttoadd)

def addstudent(classroom: int, student: int):
    classroomList[classroom].students.append(student)
    studentList[student].classes[classroomList[classroom].subject] = classroom

def checknotsame(classroom: int, student: int):
    for i in studentList[student].classes.key():
        if studentList[student].classes[i] != None:
            tempnum = studentList[student].classes[i]
    return bool([classroomList[tempnum].day,classroomList[tempnum].session] != [classroomList[classroom].day,classroomList[classroom.session]])

def classexists(day: str, session: str, yearlevel: int, subject: str):
    for eachroom in timetableClassrooms[day][session].keys():
        if classroomList[timetableClassrooms[day][session][eachroom]].yearlevel == yearlevel and classroomList[timetableClassrooms[day][session][eachroom]].subject == subject:
            return True
    return False

sWindow.show()
sys.exit(app.exec())