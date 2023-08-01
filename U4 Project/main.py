import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6 import uic as PyUI
from math import ceil

from startupscren import *

sWindow.CreateTimetableButton.clicked.connect(lambda: programBegin())

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
    with open(studentCSV, "r") as file: # start student creation process
        studentSheet = file.read().splitlines()[1:]
        numberOfStudents = len(studentSheet)
        #print(studentSheet)
        print("hello")
        for eachStudent in studentSheet:
            temp = eachStudent.split(',')[1:]
            temp = fixtemp(temp)
            for eachStat in range(len(temp)):
                if eachStat in range(5):
                    pass
                else:
                    #print("-"*32)
                    #print(temp[eachStat])
                    if "Early" in temp[eachStat] and "Late" in temp[eachStat]:
                        temp[eachStat] = 3
                    elif "Early" in temp[eachStat]:
                        temp[eachStat] = 1
                    elif "Late" in temp[eachStat]:
                        temp[eachStat] = 2
                    else:
                        temp[eachStat] = 0
            #print("Printing temp")
            #print(temp)
            studentList.append(Student(temp[0],temp[1],temp[2],temp[3],temp[4],temp[5],temp[6],temp[7],temp[8],temp[9])) #Create a Class for each student
            #print(studentList)
    # check for duplicates
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
                                    classroomList[tempindex].students.append(tutorList.index(tutor))  # add tutor to the classroom
                                    tutor.classes.append(tempindex) #update Class to tutor
                                    tutor.availability[value] = 3
                                    tutor.updatepriority() #change availability to 3, meaning there is a class and update the priority
                                    classroomList[tempindex].classtype = "In-Person"
                                    tempyearlevel = defineyearlevel(tutorList.index(tutor))
                                    enoughClassesCheck()
                                    #print(classroomList)
                                    #print(tempyearlevel)
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
                            classroomList[tempindex].students.append(tutorList.index(tutor))  # add tutor to the classroom
                            # update Class to tutor
                            tutor.classes.append(tempindex)
                            tutor.availability[value] = 3
                            # change availability to 3, meaning there is a class and update the priority
                            tutor.updatepriority()
                            classroomList[tempindex].classtype = "Online"
                            tempyearlevel = defineyearlevel(tutorList.index(tutor))
                            #print(classroomList)
                            print(tempyearlevel)
                            classroomList[tempindex].subject = tutor.subject
                            match tutor.subject:
                                case "Maths":
                                    classroomList[tempindex].name += f"MAT {tempyearlevel}{alphabet[mathsyearlevelnaming[tempyearlevel]]}"
                                    classroomList[tempindex].yearlevel = int(tempyearlevel)
                                    mathsyearlevelnaming[tempyearlevel] += 1
                                case "English":
                                    classroomList[tempindex].name += f"ENG {tempyearlevel}{alphabet[englishyearlevelnaming[tempyearlevel]]}"
                                    classroomList[tempindex].yearlevel = int(tempyearlevel)
                                    englishyearlevelnaming[tempyearlevel] += 1
                            break
                        break
                
    #print(timetableClassrooms)
    for i in tutorList:
        print(f'{i.name}: {i.availability}')
        print(f'{i.name}: {[classroomList[j].name for j in i.classes]}')

    for i in classroomList:
        if not i.name == "SEL ":
            print(f'{i.name} has a subject of {i.subject}')

    #check number of classes, if not enough for each year level then add more
    temp = enoughClassesCheck()
    while len(temp) > 0:
        createOnlineClasses(temp.pop(0),daysPossible)
    switchScreens()

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
    mainsubject = "Maths"
    while not(checkstudents(mainsubject)):
        for student in range(len(studentList)):
            if studentList[student].classes[mainsubject] == None:
                #print(studentList[student].name)
                if checkPreference(student,mainsubject):
                    pass
                else:
                    # occurs if no class available
                    # first we're going to see if the student has no other option
                    # check for priority. This is the hard part
                    # find out how you're going to solve this issue
                    # REDO THIS WHOLE SECTION
                    print("Failed")
                    ### WORK ON THIS BIT HELLO RIGHT HERE PLEASE WORK HERE PLEASE WORK HERE PLEASE WORK HERE PLEASE WORK HERE
            else:
                pass
        if checkstudents(mainsubject):
            #for i in studentList:
            #    print(f'{i.name}: {i.classes}')
            if mainsubject == "Maths":
                mainsubject = "English"
                for student in range(len(studentList)):
                    studentList[student].switching()
    #just some testing
    for i in studentList:
        print(f'{i.name}: {i.classes}')
    print(doomedstudentlist)
    print("LETS GO WE DONE")
    for i in [10,25,21,45,30,26,57]:
        print(classroomList[i].name)
        print(classroomList[i].subject)
        print(tutorList[classroomList[i].students[0]].name)
    for i in tutorList:
        if i.name == "Testing O":
            print(i.availability)
            print(i.classes)
        elif i.name == "Testing F":
            print(i.availability)
            print(i.classes)
    for i in studentList:
        if i.name == "Cheese H":
            print(i.availability)
    print(timetableClassrooms)
    # Now that most students are complete, remove all teachers 
    

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

def checkPreference(student: int, subject: str):
    global badstudentlist
    day = studentList[student].availability.pop(0) # get the next availability of the student
    #print(day)
    studentList[student].updatePriority() # update the student's priority
    session = earlyorlate(day[0]) # check whether it's an early or late session
    #print(session)
    nlist = [] # list of all possible classes that fit the conditions
    #print(timetableClassrooms[day[1:]][session])
    #print(f'Year Level: {studentList[student].yearLevel}')
    #print(f'Subject: {subject}')
    #print(len(timetableClassrooms[day[1:]][session].keys()))
    for classroom in timetableClassrooms[day[1:]][session].keys(): # check of all the classrooms
        #print("Details:")
        #print(classroomList[timetableClassrooms[day[1:]][session][classroom]].name)
        #print(classroomList[timetableClassrooms[day[1:]][session][classroom]].yearlevel)
        #print(classroomList[timetableClassrooms[day[1:]][session][classroom]].subject)
        if classroomList[timetableClassrooms[day[1:]][session][classroom]].yearlevel == int(studentList[student].yearLevel) and classroomList[timetableClassrooms[day[1:]][session][classroom]].subject == subject:
            nlist.append(timetableClassrooms[day[1:]][session][classroom])
    ###MAKE CODE IF NO CLASSES FIT THE STUDENT
    #CHECK IF STUDENT HAS NO OTHER CLASSES LEFT (DO THE SWITCHEROO IF ONE LEFT OR CREATE NEW CLASS)
    #IF NOT, JUST SKIP THE CLASS AND RETURN
    #print(nlist)
    #print("hiii")
    if len(nlist) == 0:
        if studentList[student].priority == 0:
            if attemptswitch(student, session, subject):
                return True
            else:
                badstudentlist.append(student)
                studentList[student].classes[subject] = "None"
        else:
            return False
    for eachclass in nlist: #check if any of the classes have an open seat
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

def noclassexist(listoffailedstudents: list, subject: str): #contingency plan. what happens when the students have no classes that exist
    unavailablesessions = []
    tempdict = whatclasses(listoffailedstudents, unavailablesessions)
    # now that we have the most common times needed, take the most popular time and find a tutor with an availability for that time
    # if no tutor has an availability for that time, remove it
    while tempdict != {}:
        classfocus = findMax(tempdict)
        # now find which tutor has an availability for this time
        temptutorlist = []
        num = Tutor.daylist.index(classfocus[0][1:]) * 2
        if classfocus[0][0] == "L":
            num += 1
        for tutor in range(len(tutorList)): # find all tutors with this availability and subject
            if tutorList[tutor].availability[num] in [1,2] and tutorList[tutor].subject == subject and classfocus[1] in tutorList[tutor].yearlevels:
                temptutorlist.append(tutor)
        if len(temptutorlist) == 0:
            unavailablesessions.append(classfocus)
        else:
            # find tutor with least amount of classes
            min = [None,10000]
            for eachtutor in temptutorlist:
                tempamount = len(tutorList[eachtutor].classes)
                if tempamount < min[1] and tempamount < tutorList[eachtutor].maximum: # find minimum and check that their classes does not go above maximum
                    min = [eachtutor,tempamount]
            newclass = createclass(min[0], classfocus[0], subject, classfocus[1]) # create a class with the tutor
            appendingstudentlist = newkids(newclass, listoffailedstudents)
            for eachstudent in appendingstudentlist:
                addstudent(newclass, eachstudent)
                listoffailedstudents.pop(listoffailedstudents.index(eachstudent))
        tempdict = whatclasses(listoffailedstudents, unavailablesessions)
    ### What to do with doomed students???
    ### Also ensure the students dont already have a class at that time when creating a new class for them

def newkids(classroom: int, failedstudents: list): # function finds the lowest priority students and returns them
    session = f'{classroomList[classroom].time[0]}{classroomList[classroom].day}' # define the two variables for ease
    theyearlevel = classroomList[classroom].yearlevel
    potentiallist = [] # list of all potential students
    for student in failedstudents:
        # check if the session is in the availability and matching year level and does not have a class at this time
        if session in studentList[student].originalavailability and int(studentList[student].yearLevel) == theyearlevel and checknotsame(classroom, student):
            potentiallist.append(student)
    return bubblesort5(potentiallist)

def bubblesort5(nlist: list): # do bubble sort ascending but only for the first 5 indexes
    for i in range(len(nlist)):
        if i == 5:
            return nlist[0:6] # return only the first 5 indexes of the list
        min = len(studentList[nlist[i]].originalavailability)
        for j in range(len(nlist[i:])):
            if len(studentList[nlist[j]].originalavailability) < min:
                min = len(studentList[nlist[j]].originalavailability)
                nlist[i], nlist[j] = nlist[j], nlist[i]

def whatclasses(list1: list, bannedclasses: list):
    global doomedstudentlist
    dictionary = {}
    for i in yearlevelstats.keys():
        dictionary[i] = {}
    for student in list1:  # find out most common class needed and make them
        changesmade = False
        for availability in studentList[student].originalavailability:
            if not(studentList[student].yearLevel in [j[0] for j in bannedclasses] and availability in [i[0] for i in bannedclasses]) :
                # above if statement checks that the availability is not in the banned lists
                changesmade = True
                dictionary[studentList[student].yearLevel][availability] += 1
        if not(changesmade) and not(student in doomedstudentlist):
            ### CREATE THE DOOMED LIST
            doomedstudentlist.append(student)
    return dictionary

def createclass(tutor: int, session: str, thesubject: str, yearlevel: int): # create a brand new class
    time = earlyorlate(session[0])
    for eachroom in timetableClassrooms[session[1:]][time].keys(): # find an available classroom
        num = timetableClassrooms[session[1:]][time][eachroom]
        if len(classroomList[num].students) == 0:
            classroomList[num].students.append(tutor)
            tutorList[tutor].classes.append(num)
            classroomList[num].subject = thesubject
            classroomList[num].yearlevel = yearlevel
            return num
    # create online class if not returned
    tempnum = howmanyonlineclasses(session[1:],[time])
    classroomList.append(Class(session[1:],time,f'Online{tempnum}'))
    timetableClassrooms[session[1:]][time][f'Online{tempnum}'] = len(classroomList) - 1
    classroomList[tempnum].students.append(tutor)
    tutorList[tutor].classes.append(tempnum)
    classroomList[tempnum].subject = thesubject
    classroomList[tempnum].yearlevel = yearlevel
    return tempnum

def findMax(dictionary: dict): # find the maximum value in the dictionary
    max = [0,0,0] # [session, value, yearlevel]
    for eachyearlevel in dictionary:
        for eachsession in eachyearlevel:
            if dictionary[eachyearlevel][eachsession] > max[1]:
                max = [eachsession,dictionary[eachyearlevel][eachsession],eachyearlevel]
    return [max[0],max[2]]

def studentshifting(nlist: list, student: int): # see if any students have a lower priority than the current one
    # find the student with the highest priority
    print("shifting")
    tempstudent = [0, None, 0]  # First represents class, second represents index, third represents their priority
    for item in nlist:
        for eachstudent in classroomList[item].student[1:]:
            if studentList[eachstudent].priority > tempstudent[2]:
                tempstudent = [item, eachstudent,studentList[eachstudent].priority]
    # kick the student with the highest priority IF it's higher than the current student
    if tempstudent[2] > studentList[student].priority: 
        kickstudent(item, tempstudent, student) #kicks the student and adds a new one
        return True
    else:
        return False

def kickstudent(classroom: int, studenttokick: int, studenttoadd: int): # kick a student out and replace them with the new student
    print("kicking")
    classroomList[classroom].removeStudent(studentList(studenttokick))
    studentList[studenttokick].classes[classroomList[classroom].subject] = None
    studentList[studenttokick].updatePriority()
    addstudent(classroom,studenttoadd)

def addstudent(classroom: int, student: int): # add a student to class
    print("adding")
    classroomList[classroom].students.append(student)
    studentList[student].classes[classroomList[classroom].subject] = classroom

def checknotsame(classroom: int, student: int): # check that the student does not already have a class during that time
    found = False
    for i in studentList[student].classes.key():
        if studentList[student].classes[i] != None:
            tempnum = studentList[student].classes[i]
            found = True
    if found:
        return bool([classroomList[tempnum].day,classroomList[tempnum].session] != [classroomList[classroom].day,classroomList[classroom.session]])
    else:
        return True

def classexists(day: str, session: str, yearlevel: int, subject: str): # check if a class fitting the conditions exist
    for eachroom in timetableClassrooms[day][session].keys():
        if classroomList[timetableClassrooms[day][session][eachroom]].yearlevel == yearlevel and classroomList[timetableClassrooms[day][session][eachroom]].subject == subject:
            return True
    return False

sWindow.show()
sys.exit(app.exec())