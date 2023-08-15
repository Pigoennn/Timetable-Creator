import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic as PyUI
from math import floor
from random import randint

from startupscren import * # starting screen (screen where you input your csv files)
from displayscren import * # finishing screen (screen where you view classes and download the csv file)

def programBegin(): # Begin the creation process
    global timetable, numberOfStudents, studentList, availableClassrooms, timetableClassrooms, classroomList, studentCSV, tutorCSV
    from startupscren import studentCSV, tutorCSV
    error = fileVerification()  # Check the files first if they are correct
    if error:  # If there is no error, passes
        return changeInfoLabel(error) # stop function if not verified
    # begin class creating process
    # start with creating possible time slots
    with open(tutorCSV, "r") as file:
        tutorSheet = file.read().splitlines()
        tutorSheet = tutorSheet[3:]
    daysPossible = tutorSheet.pop(0).split(',')[4:] # create a separate list with all the given days
    for eachOption in range(len(daysPossible)): # get rid of the missing spaces and replace it with the correct day
        if daysPossible[eachOption] == "What is the maximum number of classes you would like?":
            stopLimit = eachOption
            daysPossible = daysPossible[:eachOption]
            break
        else:
            if daysPossible[eachOption] == "":
                daysPossible[eachOption] = daysPossible[eachOption-1]
    timesPossible = tutorSheet.pop(0).split(',')[4:stopLimit+4] # create a separate list with all the given times
    for eachTime in range(len(timesPossible)): # add the given times according to the given days in a dictionary
        if daysPossible[eachTime] in timetable.keys():
            timetable[daysPossible[eachTime]].append(timesPossible[eachTime])
        else:
            timetable[daysPossible[eachTime]] = [timesPossible[eachTime]]
    for i in timetable.keys():
        print(f'{i}: {timetable[i]}')
    with open(studentCSV, "r") as file: # start student creation process
        studentSheet = file.read().splitlines()[1:]
        #print(studentSheet)
        print("hello")
        for eachStudent in studentSheet:
            temp = eachStudent.split(',')[1:]
            temp = fixtemp(temp)
            for eachStat in range(len(temp)):
                if eachStat in range(5):
                    pass
                else:
                    if "Early" in temp[eachStat] and "Late" in temp[eachStat]:
                        temp[eachStat] = 3
                    elif "Early" in temp[eachStat]:
                        temp[eachStat] = 1
                    elif "Late" in temp[eachStat]:
                        temp[eachStat] = 2
                    else:
                        temp[eachStat] = 0
            studentList.append(Student(temp[0],temp[1],temp[2],temp[3],temp[4],temp[5],temp[6],temp[7],temp[8],temp[9])) #Create a Class for each student
    # check for duplicates
    numberOfStudents = len(studentList)
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
    yearLevelStats()
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
            print(temp[0], temp[1], temp[2], temp[3:15], temp[15], temp[16])
            tutorList.append(Tutor(temp[0],temp[1],temp[2],temp[3:15],temp[15],temp[16])) #Create Tutor Class
    #check for any duplicate names
    duplicate = True
    while duplicate == True: # run a while loop to remove all duplicate names
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
    # clean any impossible year levels
    yearlevelcleaning()    
    # check if any classroom is available before creating then add tutor to it and then update tutor
    allyearlevels = list(yearlevelstats.keys())
    tempyearlevel = allyearlevels.pop(0)
    currentpriority = [2]
    attemptcounter = 0
    print(allyearlevels)
    print("-"*32)
    print(yearlevelclassesneeded.keys())
    print('hiya')
    print(daysPossible)
    print(Student.daylist)
    while checkclasses(tempyearlevel):
        #print("working3")
        # Create a class using createClass function
        # First we find a tutor that has the year level and is not maxed out on classes
        attemptcounter += 1
        for tutor in tutorList:
            #print(f'{tempyearlevel} vs {tutor.yearlevels}')
            if tempyearlevel in tutor.yearlevels and len(tutor.classes) < tutor.maximum and [i for i in currentpriority if i in tutor.availability[startnum:endnum]]:
                #print("happens")
                #print(tutor.availability)
                try:
                    value = tutor.availability.index(0)
                except ValueError:
                    value = tutor.availability.index(3)
                while not(daysPossible[value] in Student.daylist and tutor.availability[value] in currentpriority):
                    value = randint(0,len(tutor.availability) - 1)
                print(f'Value: {value}')
                day = daysPossible[value]  # which day is it
                print(day)
                if value % 2 == 0:  # is it early or late session
                    day = f'E{day}'
                else:
                    day = f'L{day}'
                print(f"creating for {tutor.name} on {day[1:]}")
                createclass(tutorList.index(tutor), day, tutor.subject, tempyearlevel)  # creates the class
                if len(tutor.classes) < tutor.maximum:
                    match value % 2:
                        case 0:
                            if tutor.availability[value + 1] in currentpriority:
                                day = "L" + day[1:]
                                createclass(tutorList.index(tutor), day, tutor.subject, tempyearlevel)
                        case 1:
                            if tutor.availability[value - 1] in currentpriority:
                                day = "E" + day[1:]
                                createclass(tutorList.index(tutor),day, tutor.subject, tempyearlevel)
        if not(checkclasses(tempyearlevel)):
            try:
                print("Switching")
                tempyearlevel = allyearlevels.pop(0)
            except IndexError:
                print("you done")
                pass
        if attemptcounter == 8:
            currentpriority.append(1)
    print(timetableClassrooms)
    ### CREATE CLASSROOM SPAM WHERE YOU CREATE RANDOM CLASSROOMS FOR NO REASON
    if not(1 in currentpriority):
        currentpriority.append(1)
    reallycoolnumber = floor(numberOfStudents / 50)
    currentsubject = ["Maths", "English"]
    for i in range(reallycoolnumber):
        for tutor in tutorList:
            print(tutor.availability)
            print('bongo')
            if len(tutor.classes) < tutor.maximum and tutor.subject == currentsubject[0] and [i for i in currentpriority if i in tutor.availability[startnum:endnum]]:
                chosen = tutor.availability.index(3)
                print(tutor.availability)
                print(tutor.availability[startnum:endnum])
                print(str(startnum) + " and " + str(endnum))
                print("bingo")
                while (tutor.availability[chosen] == 0 or tutor.availability[chosen] == 3) or not(daysPossible[chosen] in Student.daylist):
                    print("working on this")
                    chosen = randint(0,len(tutor.availability)-1)
                day = daysPossible[chosen]  # which day is it
                print(day)
                if chosen % 2 == 0:  # is it early or late session
                    day = f'E{day}'
                else:
                    day = f'L{day}'
                createclass(tutorList.index(tutor), day, tutor.subject, tutor.yearlevels[0])
                if len(tutor.classes) < tutor.maximum:
                    match chosen % 2:
                        case 0:
                            if tutor.availability[chosen + 1] == 2:
                                day = "L" + day[1:]
                                createclass(tutorList.index(tutor), day, tutor.subject, tutor.yearlevels[0])
                        case 1:
                            if tutor.availability[chosen - 1] == 2:
                                day = "E" + day[1:]
                                createclass(tutorList.index(tutor), day, tutor.subject, tutor.yearlevels[0])
                currentsubject.append(currentsubject.pop(0))  # Recycle the first subject to the back'''
    print(timetableClassrooms)
    for i in classroomList:
        if "Online" in i.classroom:
            print(f'{i.day} + {i.time}')
    for i in tutorList:
        print(f'{i.name}: {i.availability}, {len(i.classes)}')

    for i in classroomList:
        if i.yearlevel in ["8","7","6"] and len(i.students) == 1:
            print(f'{i.classroom} on {i.time[0]}{i.day} has a subject of {i.subject} and yearlevel of {i.yearlevel}')
    print("WE'RE HALFWAY THEREEE")
    for day in timetableClassrooms.keys():
        print(day)
        for session in timetableClassrooms[day].keys():
            print(session)
            for room in timetableClassrooms[day][session].keys():
                tempobject = classroomList[timetableClassrooms[day][session][room]]
                if len(tempobject.students) == 1:
                    print(f'Tutor: {tutorList[tempobject.students[0]].name} | Year Level: {tempobject.yearlevel}')
    switchScreens()

# If the button is clicked attempt to start the algorithm
sWindow.CreateTimetableButton.clicked.connect(lambda: programBegin())

###-------------------------------------------------------------------------------
#Loading Screen
lWindow = PyUI.loadUi("loadingScren.ui")
lWindow.setWindowTitle("Creating Classes...")

lWindow.progressBar.setValue(0)
completelydoomed = []

def switchScreens(): #switch screens
    lWindow.show()
    sWindow.close()
    startAlgorithm()

def startAlgorithm(): #start adding students to class
    mainsubject = "Maths"
    while not(checkstudents(mainsubject)):
        for student in range(len(studentList)):
            if studentList[student].classes[mainsubject] == None:
                #print(studentList[student].name)
                if modifiedGaleShapley(student,mainsubject):
                    pass
                else:
                    # occurs if no class available
                    # first we're going to see if the student has no other option
                    # check for priority. This is the hard part
                    # find out how you're going to solve this issue
                    # REDO THIS WHOLE SECTION
                    print("Failed")
                    ### WORK ON THIS BIT HELLO RIGHT HERE PLEASE WORK HERE PLEASE WORK HERE PLEASE WORK HERE PLEASE WORK HERE
                    if len(studentList[student].availability) == 0:
                        print("failed")
                        studentList[student].classes[mainsubject] = "None"
            else:
                pass
        if checkstudents(mainsubject):
            if mainsubject == "Maths":
                mainsubject = "English"
                for student in range(len(studentList)):
                    studentList[student].switching()
    # Now that most students are complete, remove all classes with only one teacher and attempt to create
    endOfAlgorithm()

def endOfAlgorithm():
    global classroomList, tutorList, completelydoomed
    # First start by removing all classes with one teacher only
    for eachclass in (classroomList):
        if len(eachclass.students) == 1:
            classroomDelete(classroomList.index(eachclass))
    # Begin back up classes creation algorithm
    contingencyplan()
    statuscheck()
    # Big check to make sure that no one is somehow in the wrong class
    for i in studentList:
        print(f'{i.name}, Year {i.yearLevel}: {i.classes}')
    '''for eachclass in classroomList:
        if len(eachclass.students) > 1:
            print(len(eachclass.students))
            if len(eachclass.students ) > 6:
                print(f'{eachclass.day}, {eachclass.time}, {eachclass.yearlevel}')
                for i in eachclass.students:
                    print(studentList[i].name)
                print("-" * 32)
            if eachclass.subject != tutorList[eachclass.students[0]].subject:
                print("TEACHER ERROR")
            for student in eachclass.students[1:]:
                if int(studentList[student].yearLevel) != eachclass.yearlevel:
                    print(eachclass.yearlevel)
                    print("STUDENT ERROR")'''
    cleaningclasses() # Try to clean the classes
    classroomswitching()
    onlineclassroomswitching()
    remainingstudents()
    # now that all classes have been made and cleaned, begin naming them
    classnaming()
    finishingscreen()
    print("HEHEHEHE FINISHED")

def remainingstudents(): # Create a text file for any students who have no class available
    remains = []
    for student in studentList:
        if "None" in student.classes.values():
            remains.append(student)
    if remains:
        from datetime import datetime
        with open("Errors.txt", "w") as errorfile:
            errorfile.write(f'{datetime.now().strftime("%H:%M:%S")}\n')
            errorfile.write(f"Students who did not receive a class: {len(remains)}\n\n")
            for student in remains:
                errorfile.write(f'({",".join([i for i in student.classes.keys() if student.classes[i] == "None"])})\n{student.name}\n{student.email}\nYear {student.yearLevel}\nAttendance Method: {student.place}\nAvailabilities: {student.originalavailability}\n')
                errorfile.write("\n")
    else:
        return

def classnaming():
    global englishyearlevelnaming, mathsyearlevelnaming, classroomList, timetableClassrooms
    # Go through every available class and name them
    for classroom in classroomList:
        if len(classroom.students) >= 2:
            yearlevel = classroom.yearlevel
            match classroom.subject:
                case "Maths":
                    subjectname = ['MAT']
                    subjectname.append(mathsyearlevelnaming[yearlevel])
                    mathsyearlevelnaming[yearlevel] += 1
                case "English":
                    subjectname = ['ENG']
                    subjectname.append(englishyearlevelnaming[yearlevel])
                    englishyearlevelnaming[yearlevel] += 1
            classroom.name = f'{classroom.name} {subjectname[0]} {yearlevel}{alphabet[subjectname[1]]}'
        elif len(classroom.students) == 1:
            classroomDelete(classroomList.index(classroom))
    # Switch online class
    for day in timetableClassrooms.keys():
        for session in timetableClassrooms[day].keys():
            if "Online1" in timetableClassrooms[day][session]:
                importantlist = [i for i in timetableClassrooms[day][session].keys() if "Online" in i]
                removeonlineclassrooms(day,session,importantlist)

    # JUST FOR PRINTING
    '''for classroom in classroomList:
        if len(classroom.students) >= 1:
            print("-" * 48)
            print(classroom.name)
            first = True
            for i in classroom.students:
                if first:
                    print(f'--> {studentList[i].name}')
                    first = False
                else:
                    print(f'-> {studentList[i].name}')   '''

def removeonlineclassrooms(day: str, session: str, nlist: list):
    global timetableClassrooms
    ### Remove all unnecessary classrooms
    for room in nlist:
        if len(classroomList[timetableClassrooms[day][session][room]].students) <= 1:
            timetableClassrooms[day][session].pop(room)

def backup(unavailable: dict):
    global doomedstudentlist
    doomedstudentlist = []
    for student in range(len(studentList)): # Find all students without a class
        for subject in studentList[student].classes.keys():
            if studentList[student].classes[subject] == "None" and not(student in doomedstudentlist):
                doomedstudentlist.append(student)
    return whatclasses(unavailable)

def contingencyplan():
    asdfdict = {}
    for i in yearlevelstats.keys():
        asdfdict[i] = {
            "Maths": [],
            "English": []
        }
    dictionary = backup(asdfdict)
    #for i in dictionary.keys():
    #    print(type(dictionary[i]))
    unavailablesessions = {} # some sessions may not be possible. this dictionary will hold the data
    for yearlevel in dictionary.keys(): 
        unavailablesessions[yearlevel] = {}
        for subject in dictionary[yearlevel].keys():
            unavailablesessions[yearlevel][subject] = []
    # now that we have the most common times needed, take the most popular time and find a tutor with an availability for that time
    # if no tutor has an availability for that time, remove it
    while dictionary != {}:
        statuscheck()
        #print("Da Dictionary: ")
        #print(dictionary)
        classfocus = findMax(dictionary) # returns [session, subject, yearlevel]
        print(classfocus)
        #print(classfocus)
        # now find which tutor has an availability for this time
        temptutorlist = []
        num = Tutor.daylist.index(classfocus[0][1:]) * 2
        if classfocus[0][0] == "L":
            num += 1
        # find all tutors with this availability and subject and year level and not maxed on classes
        for tutor in range(len(tutorList)):
            if tutorList[tutor].availability[num] in [1, 2] and tutorList[tutor].subject == classfocus[1] and classfocus[2] in tutorList[tutor].yearlevels and len(tutorList[tutor].classes) < tutorList[tutor].maximum:
                temptutorlist.append(tutor)
        if len(temptutorlist) == 0:
            unavailablesessions[classfocus[2]][classfocus[1]].append(classfocus[0])
        else:
            # find tutor with least amount of classes
            min = [None, 10000]
            for eachtutor in temptutorlist:
                tempamount = len(tutorList[eachtutor].classes)
                # find least amount of classes
                if tempamount < min[1]:
                    min = [eachtutor, tempamount]
            # create a class with the tutor
            newclass = createclass(min[0], classfocus[0], classfocus[1], classfocus[2]) # tutor, session, subject, year level
            print("Contingency Classroom has been created in " + classroomList[newclass].classroom)
            print(f'{classroomList[newclass].time} {classroomList[newclass].day}')
            #print(len(classroomList[newclass].students))
            appendingstudentlist = newkids(newclass)
            for eachstudent in appendingstudentlist:
                addstudent(newclass, eachstudent) # clear
        dictionary = backup(unavailablesessions)
    # What to do with doomed students???
    # Also ensure the students dont already have a class at that time when creating a new class for them

def classroomDelete(classroom: int):
    global classroomList
    # Remove the classroom to default settings and remove it from the tutor
    temptutor = classroomList[classroom].students.pop(0) # remove the tutor who is the only student
    tutorList[temptutor].classes.remove(classroom) # remove the class from the tutor
    num = Tutor.daylist.index(classroomList[classroom].day) * 2
    match classroomList[classroom].time:
        case "Early":
            num += 0
        case "Late":
            num += 1
    tutorList[temptutor].availability[num] = tutorList[temptutor].originalavailability[num] # update the availability to its original
    classroomList[classroom].yearlevel = "0"
    return

def checkstudents(subject):
    statuscheck()
    for student in studentList:
       if student.classes[subject] == None: #They are missing a class
           return False
    return True

def statuscheck():
    tempnum = 0
    for student in studentList:
        for i in student.classes.keys():
            if not student.classes[i] in [None,"None"]:
                tempnum += 0.5
    finalvalue = int(tempnum * 100 / numberOfStudents)
    lWindow.progressBar.setValue(finalvalue)

badstudentlist = []
doomedstudentlist = []

def modifiedGaleShapley(student: int, subject: str):
    global badstudentlist
    #print("-"*48)
    #print(f'Student: {studentList[student].name}')
    #print(f'Number: {student}')
    #print(subject)
    day = studentList[student].availability.pop(0) # get the next availability of the student
    #print(day)
    studentList[student].updatePriority() # update the student's priority
    session = earlyorlate(day[0]) # check whether it's an early or late session
    #print(session)
    nlist = [] # list of all possible classes that fit the conditions
    #print("AND SO IT BEGINS")
    #print("-*"*24)
    #print(timetableClassrooms[day[1:]][session])
    #print(f'Year Level: {studentList[student].yearLevel}')
    #print(f'Subject: {subject}')
    #print(f'Available Sessions: {len(timetableClassrooms[day[1:]][session].keys())}')
    for classroom in timetableClassrooms[day[1:]][session].keys(): # check of all the classrooms
        #print("-" * 24)
        #print(f'Session Year Level: {classroomList[timetableClassrooms[day[1:]][session][classroom]].yearlevel}')
        #print(f'Session Subject: {classroomList[timetableClassrooms[day[1:]][session][classroom]].subject}')
        if classroomList[timetableClassrooms[day[1:]][session][classroom]].yearlevel == studentList[student].yearLevel and classroomList[timetableClassrooms[day[1:]][session][classroom]].subject == subject:
            nlist.append(timetableClassrooms[day[1:]][session][classroom])
    ###MAKE CODE IF NO CLASSES FIT THE STUDENT
    #CHECK IF STUDENT HAS NO OTHER CLASSES LEFT (DO THE SWITCHEROO IF ONE LEFT OR CREATE NEW CLASS)
    #IF NOT, JUST SKIP THE CLASS AND RETURN
    print(f'Possible Classes: {nlist}')
    if len(nlist) == 0:
        if studentList[student].priority == 0:
            if attemptswitch(student, session, subject):
                exit()
                return True
            else:
                badstudentlist.append(student)
                studentList[student].classes[subject] = "None"
                print(studentList[student].name)
        else:
            return False
    for eachclass in nlist: # check if any of the classes have an open seat
        if len(classroomList[eachclass].students) < 6:
            return addstudent(eachclass, student)
    if not(studentshifting(nlist,student)): # add a new student to the class and update all details
        badstudentlist.append(student)
        studentList[student].classes[subject] = "None"
        return False
    else:
        return True

def attemptswitch(student: int, session: str, subject: str): # try to switch a student in using their old availabilities
    possiblesessions = [] # [day,session]
    for eachsession in studentList[student].originalavailability:
        tempvar = earlyorlate(eachsession[0])
        if classexists(eachsession[1:], tempvar, int(studentList[student].yearLevel), subject):
            for item in timetableClassrooms[eachsession[1:]][tempvar].keys():
                if classroomList[timetableClassrooms[eachsession[1:]][tempvar][item]].yearlevel == studentList[student].yearLevel and classroomList[timetableClassrooms[eachsession[1:]][tempvar][item]].subject == subject:
                    possiblesessions.append(timetableClassrooms[eachsession[1:]][tempvar][item])
    if len(possiblesessions) == 0:
        return False # no classes available
    else:
        return studentshifting(possiblesessions,student)

def earlyorlate(n: str): # quick function to see if early or late session
    match n:
        case "E":
            return "Early"
        case "L":
            return "Late"

def newkids(classroom: int): # function finds the lowest priority students and returns them
    session = f'{classroomList[classroom].time[0]}{classroomList[classroom].day}' # define the two variables for ease
    theyearlevel = classroomList[classroom].yearlevel
    potentiallist = [] # list of all potential students
    for student in doomedstudentlist:
        # check if the session is in the availability and matching year level and does not have a class at this time
        if session in studentList[student].originalavailability and int(studentList[student].yearLevel) == theyearlevel and checknotsame(classroom, student):
            potentiallist.append(student)
    return bubblesort5(potentiallist)

def bubblesort5(nlist: list): # do bubble sort ascending but only for the first 5 or less indexes
    for i in range(len(nlist)):
        if i == 5:
            return nlist[:5] # return only the first 5 indexes of the list
        min = len(studentList[nlist[i]].originalavailability)
        for j in range(i + 1,len(nlist)):
            if len(studentList[nlist[j]].originalavailability) < min:
                min = len(studentList[nlist[j]].originalavailability)
                nlist[i], nlist[j] = nlist[j], nlist[i]
    return nlist # occurs if there are less than 5 students possible

def whatclasses(unavailable: dict):
    #print(unavailable)
    global doomedstudentlist
    dictionary = {}
    for i in yearlevelstats.keys():
        dictionary[i] = {
            "Maths": {},
            "English": {}
        }
    for student in doomedstudentlist:  # find out most common class needed and make them
        missingsubject = [i for i in studentList[student].classes.keys() if studentList[student].classes[i] == "None"]
        #print(missingsubject)
        for availability in studentList[student].originalavailability:
            # above if statement checks that the availability is not in the banned lists
            for subject in missingsubject:
                try:
                    dictionary[studentList[student].yearLevel][subject][availability] += 1
                except KeyError:
                    if not(availability in unavailable[studentList[student].yearLevel][subject]): # Check that it is not an available subject
                        dictionary[studentList[student].yearLevel][subject][availability] = 1
            #print("_-_-"*32)
            #print(dictionary)
    # Clean the dictionary
    ultimatedestroylist = []
    for yearlevel in dictionary.keys():
        destroylist = []
        for subject in dictionary[yearlevel].keys():
            if dictionary[yearlevel][subject] == {}:
                destroylist.append(subject)
        for eachsubject in destroylist:
            dictionary[yearlevel].pop(eachsubject)
        if dictionary[yearlevel] == {}:
            ultimatedestroylist.append(yearlevel)
    for destruction in ultimatedestroylist:
        dictionary.pop(destruction)
    return dictionary

def createclass(tutor: int, session: str, thesubject: str, yearlevel: str): # create a brand new class
    time = earlyorlate(session[0])
    print("Creating class...")
    print(session)
    if tutorList[tutor].classplace != "Online":
        for eachroom in timetableClassrooms[session[1:]][time].keys(): # find an available classroom
            num = timetableClassrooms[session[1:]][time][eachroom]
            if len(classroomList[num].students) == 0:
                classroomList[num].students.append(tutor) # Add the tutor to the class
                tutorList[tutor].classes.append(num)    # Add the class to the tutor
                classroomList[num].subject = thesubject     # Set the subject
                classroomList[num].yearlevel = yearlevel    # Set the year level 
                classroomList[num].classtype = "In-Person"
                # Set the availability as 3
                tutorList[tutor].availability[whichavailabilityindex(session)] = 3
                return num
    # create online class if not returned
    tempnum = howmanyonlineclasses(session[1:],time)
    classroomList.append(Class(session[1:],time,f'Online{tempnum}'))
    num = len(classroomList) - 1
    timetableClassrooms[session[1:]][time][f'Online{tempnum}'] = num
    classroomList[num].students.append(tutor)
    tutorList[tutor].classes.append(num)
    classroomList[num].subject = thesubject
    classroomList[num].yearlevel = yearlevel
    # set the availability as 3
    tutorList[tutor].availability[whichavailabilityindex(session)] = 3
    classroomList[num].classtype = "Online"
    return num

def whichavailabilityindex(session: str):
    num = Tutor.daylist.index(session[1:]) * 2
    match session[0]:
        case "E":
            num += 0
        case "L":
            num += 1
    return num

def findMax(dictionary: dict): # find the maximum value in the dictionary
    #print("FINDING LE MAX")
    max = [0, 0, "", "0"] # [value, session, subject, yearlevel]
    for eachyearlevel in dictionary.keys():
        for eachsubject in dictionary[eachyearlevel].keys():
            for eachsession in dictionary[eachyearlevel][eachsubject].keys():
                if dictionary[eachyearlevel][eachsubject][eachsession] > max[0]:
                    max = [dictionary[eachyearlevel][eachsubject][eachsession], eachsession, eachsubject, eachyearlevel]
    #print(type(max[2]))
    return max[1:] # [session, subject, yearlevel]

def studentshifting(nlist: list, student: int): # see if any students have a lower priority than the current one
    # find the student with the largest priority
    print("shifting")
    tempstudent = [0, None, -2]  # [class index, student index, priority]
    for item in nlist:
        print(f'Classroom id: {item}, with students: {classroomList[item].students}')
        for eachstudent in classroomList[item].students[1:]:
            if studentList[eachstudent].priority >= tempstudent[2] and eachstudent != tempstudent[1]: # check for higher priority and not the same student
                tempstudent = [item, eachstudent, studentList[eachstudent].priority]
    # kick the student with the highest priority IF it's higher than the current student
    print(tempstudent)
    if tempstudent[2] > studentList[student].priority and tempstudent[1] != None:
        kickstudent(tempstudent[0], tempstudent[1], student) #kicks the student and adds a new one
        return True
    else:
        return False

def kickstudent(classroom: int, studenttokick: int, studenttoadd: int): # kick a student out and replace them with the new student
    print("kicking")
    print(f'Classroom: {classroom}, Student: {studenttokick}, Adding: {studenttoadd}')
    print(f'Length Before: {len(classroomList[classroom].students)}')
    classroomList[classroom].removeStudent(studenttokick)
    print(f'Length: {len(classroomList[classroom].students)}')
    addstudent(classroom,studenttoadd)

def addstudent(classroom: int, student: int): # add a student to class
    print("adding")
    classroomList[classroom].students.append(student)
    studentList[student].classes[classroomList[classroom].subject] = classroom
    return True

def checknotsame(classroom: int, student: int): # check that the student does not already have a class during that time
    found = False
    for i in studentList[student].classes.keys():
        if not(studentList[student].classes[i] in [None,"None"]):
            tempnum = studentList[student].classes[i]
            found = True
    if found:
        return bool([classroomList[tempnum].day,classroomList[tempnum].time] != [classroomList[classroom].day,classroomList[classroom].time])
    else:
        return True

def classexists(day: str, session: str, yearlevel: str, subject: str): # check if a class fitting the conditions exist
    for eachroom in timetableClassrooms[day][session].keys():
        if classroomList[timetableClassrooms[day][session][eachroom]].yearlevel == yearlevel and classroomList[timetableClassrooms[day][session][eachroom]].subject == subject:
            return True
    return False

###-------------------------------------------------------------------------------------------------------------------
# Class Cleaning Functions

def cleaningclasses():
    for day in timetableClassrooms.keys():
        for session in timetableClassrooms[day].keys():
            inpersonstudentlist = []
            onlinestudentlist = []
            for onlineclassroom in [i for i in timetableClassrooms[day][session].keys() if ("Online" in classroomList[timetableClassrooms[day][session][i]].name and len(classroomList[timetableClassrooms[day][session][i]].students) >= 2)]:
                for offlinestudent in classroomList[timetableClassrooms[day][session][onlineclassroom]].students[1:]:
                    if studentList[offlinestudent].place == "In-Person":
                        inpersonstudentlist.append([offlinestudent,onlineclassroom])
                if inpersonstudentlist:
                    for offlineclassroom in [i for i in timetableClassrooms[day][session].keys() if (not ("Online" in classroomList[timetableClassrooms[day][session][i]].name) and len(classroomList[timetableClassrooms[day][session][i]].students) >= 2)]:
                        for onlinestudent in classroomList[timetableClassrooms[day][session][offlineclassroom]].students[1:]:
                            if studentList[onlinestudent].place == "Online":
                                onlinestudentlist.append([onlinestudent,offlineclassroom])
                else:
                    pass
            canswitch(inpersonstudentlist,onlinestudentlist)

def canswitch(inpersonstudents: list,onlinestudents: list):
    sodoomed = []
    while len(inpersonstudents) > 0:
        student = inpersonstudents.pop(0)
        student, classroom = student[0], student[1]
        tempyearlevel, tempsubject = studentList[student].yearLevel, classroomList[classroom].subject
        switched = False
        for daclassroom in onlinestudents:
            if classroomList[daclassroom[1]].yearlevel == tempyearlevel and classroomList[daclassroom[1]].subject == tempsubject:
                switchstudents(student, classroom, daclassroom[0], daclassroom[1])
                onlinestudents.pop(onlinestudents.index(daclassroom))
                switched = True
                break
        if not switched:
            sodoomed.append([student,classroom])
    return finalattempt(sodoomed)
        
def finalattempt(nlist: list):
    while nlist:
        focusstudent = nlist.pop(0)
        focusstudent, focusclassroom = focusstudent[0], focusstudent[1]
        breaking = False
        for availability in studentList[focusstudent].originalavailability:
            for room in timetableClassrooms[availability[1:]][earlyorlate(availability[0])].keys():
                if classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].yearlevel == studentList[focusstudent].yearLevel and classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].subject == classroomList[focusclassroom].subject:
                    for onlinestudent in classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].students:
                        if studentList[onlinestudent].place == "Online" and availability in studentList[onlinestudent].availability:
                            switchstudents(focusstudent, focusclassroom, onlinestudent, timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room])
                            breaking = True
                            break
                if breaking:
                    break
                else:
                    pass
            if breaking:
                break
            else:
                pass
    return

def switchstudents(student1: int, classroom1: int, student2: int, classroom2: int):
    global timetableClassrooms, studentList, classroomList
    subject = classroomList[classroom1].subject
    # First swap the students around
    classroomList[classroom1].students[classroomList[classroom1].students[1:].index(student1) + 1], classroomList[classroom2].students[classroomList[classroom2].students[1:].index(student2) + 1] = student2, student1
    # Next, swap the availabilities around
    studentList[student1].classes[subject], studentList[student2].classes[subject] = classroom2, classroom1
    return

def classroomswitching():
    for day in timetableClassrooms.keys():
        for room in timetableClassrooms[day]["Early"].keys():
            if len(classroomList[timetableClassrooms[day]["Early"][room]].students) >= 2 and not ("Online" in classroomList[timetableClassrooms[day]["Early"][room]].classroom) and not(tutorList[classroomList[timetableClassrooms[day]["Early"][room]].students[0]].classplace == "Online"):
                tutorname = tutorList[classroomList[timetableClassrooms[day]["Early"][room]].students[0]].name
                print(tutorname)
                for lateroom in timetableClassrooms[day]["Late"].keys():
                    if len(classroomList[timetableClassrooms[day]["Late"][lateroom]].students) >= 2 and tutorList[classroomList[timetableClassrooms[day]["Late"][lateroom]].students[0]].name == tutorname:
                        print("bang bang bang")
                        classroomswitch(timetableClassrooms[day]["Late"][room],timetableClassrooms[day]["Late"][lateroom])
                        break

def onlineclassroomswitching():
    for day in timetableClassrooms.keys():
        for session in timetableClassrooms[day].keys():
            var = list(timetableClassrooms[day][session].keys())[-1]
            print("hihi")
            print(var)
            if "Online" in var and len(classroomList[timetableClassrooms[day][session][var]].students) >= 2:
                if tutorList[classroomList[timetableClassrooms[day][session][var]].students[0]].classplace != "Online":
                    for room in timetableClassrooms[day][session].keys():
                        if len(classroomList[timetableClassrooms[day][session][room]].students) <= 1 and not("Online" in room):
                            classroomswitch(timetableClassrooms[day][session][room], timetableClassrooms[day][session][var])
                            print(timetableClassrooms[day][session].pop(var))
                            break

def classroomswitch(classroom1: int, classroom2: int):
    global timetableClassrooms, classroomList
    day = classroomList[classroom1].day
    session = classroomList[classroom1].time
    room1 = classroomList[classroom1].classroom
    room2 = classroomList[classroom2].classroom
    timetableClassrooms[day][session][room1], timetableClassrooms[day][session][room2] = timetableClassrooms[day][session][room2], timetableClassrooms[day][session][room1]
    classroomList[classroom1].classroom, classroomList[classroom2].classroom = classroomList[classroom2].classroom, classroomList[classroom1].classroom

###--------------------------------------------------------------------------

# earlylatetimes[daytype][subject][session]
earlylatetimes = {
    "Weekday": {
        "Maths": {
            "Early": "5:00 - 6:30 pm",
            "Late": "7:00 - 8:30 pm"
        },
        "English": {
            "Early": "5:00 - 7:00 pm",
            "Late": "7:00 - 9:00 pm"
        }
    },
    "Weekend": {
        "Maths": {
            "Early": "11:30 - 1:00 pm",
            "Late": "2:00 - 3:30 pm"
        },
        "English": {
            "Early": "11:30 - 1:30 pm",
            "Late": "2:00 - 4:00 pm"
        }
    }
}

def finishingscreen():
    for i in tutorList[0].classes:
        print(classroomList[i].day)
        print(classroomList[i].time)
        print([studentList[j].name for j in classroomList[i].students[1:]])
    print(timetableClassrooms)
    setdWindow()
    lWindow.close()

def setdWindow():
    global dWindow, earlylatetimes
    # Find the most number of classes stated. This will be the number of rows
    maximum = []
    for i in timetableClassrooms.keys():
        for j in timetableClassrooms[i].keys():
            if len(timetableClassrooms[i][j].keys()) > len(maximum):
                maximum = list(timetableClassrooms[i][j].keys())
    # Next find the number of applicable days
    numberofdays = timetableClassrooms.keys()
    FinalWindow.maindictionary = dict(timetableClassrooms)
    FinalWindow.classList = list(classroomList)
    FinalWindow.tutorList = list(tutorList)
    FinalWindow.studentList = list(studentList)
    FinalWindow.earlylatetimes = dict(earlylatetimes)
    dWindow = FinalWindow(Student.daylist, maximum)
    dWindow.button.clicked.connect(csvoutput)

def csvoutput():  # This will be the output for the csv
    # Begin creating the csv file
    global timetableClassrooms
    with open("timetable.csv", "w") as file:
        dayfocus = 0
        # hmm
        file.write(",\n"*2)
        file.write(",Monday (Workshops),,,Colour Legend\n")
        file.write("Early\n")
        file.write(",\n" * 5)
        file.write("Late\n")
        file.write(",\n" * 5)
        while dayfocus < 5:
            file.write(",\n"*2)
            dayfocus += 1
            day = Tutor.daylist[dayfocus]
            file.write(f',{day}\n,In-Person')
            file.write(","*len(availableClassrooms))
            file.write("Online\n")
            for session in timetableClassrooms[day].keys():
                templist = [
                    [session], # Name of classroom
                    [""], # Tutor Names
                    [""], # Time
                    [""], # Classroom
                    [""], # Classtype
                    [""], # Students
                    [""],
                    [""], 
                    [""],
                    [""],
                ]
                # Begin finding all necessary information
                for classroom in timetableClassrooms[day][session].keys():
                    theclass = classroomList[timetableClassrooms[day][session][classroom]] # have an object hold the information for ease
                    # append the classname
                    if len(theclass.students) >= 2:
                        templist[0].append(theclass.name)
                    else:
                        templist[0].append("")
                    # append the tutor
                    if len(theclass.students) >= 2:
                        templist[1].append(tutorList[theclass.students[0]].name)
                    else:
                        templist[1].append("")
                    # append the time
                    if len(theclass.students) >= 2:
                        templist[2].append(earlylatetimes["Weekday" if theclass.day in Tutor.daylist[:5] else "Weekend"][theclass.subject][session])
                    else:
                        templist[2].append("")
                    # append the classroom
                    if len(theclass.students) >= 2:
                        if "Online" in theclass.classroom:
                            print(theclass.day)
                            print(theclass.classroom)
                            templist[3].append("Online")
                        else:
                            templist[3].append(theclass.classroom)
                    else:
                        templist[3].append("")
                    # append the classtype
                    if len(theclass.students) >= 2:
                        templist[4].append(f'Normal {theclass.yearlevel}')
                    else:
                        templist[4].append("")
                    for option in range(5,10):
                        try:
                            if studentList[theclass.students[option-4]].place == "Online":
                                templist[option].append(studentList[theclass.students[option-4]].name + " (OL)")
                            else:
                                templist[option].append(studentList[theclass.students[option-4]].name)
                        except IndexError:
                            templist[option].append("")
                # now input it into the file:
                for line in templist:
                    string = ",".join(line)
                    file.write(string + "\n")
    print("ta da")
    dWindow.button.setText("Done!")
    tutorstats()
    error = 0
    for i in studentList:
        for classroom in i.classes.keys():
            if not i.classes[classroom] in [None, "None"]:
                if not f'{classroomList[i.classes[classroom]].time[0]}{classroomList[i.classes[classroom]].day}' in i.originalavailability:
                    error += 1
            else:
                print("Missing")
                print(f'{i.name}: {i.yearLevel}')
    print(error)

def tutorstats():
    dict1 = {}
    for i in tutorList:
        num = str(len(i.classes))
        try:
            dict1[num] += 1
        except Exception:
            dict1[num] = 1
        if num == "0":
            print(f'{i.name}: {i.yearlevels}')
    print(dict1)

sWindow.show()
sys.exit(app.exec())