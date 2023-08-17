import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic as PyUI
from math import floor
from random import randint

from startupscren import * # starting screen (screen where you input your csv files)
from displayscren import * # finishing screen (screen where you view classes and download the csv file)

def programBegin(): # Start the entire algorithm
    start()

def start(): # Begin the creation process
    global timetable, numberOfStudents, studentList, availableClassrooms, timetableClassrooms, classroomList, studentCSV, tutorCSV
    from startupscren import studentCSV, tutorCSV

    error = fileVerification()  # Check the files first if they are correct
    if error:  # If there is no error, passes
        return changeInfoLabel(error) # stop function if not verified
    # begin class creating process

    # start with creating possible time slots
    with open(tutorCSV, "r") as file:
        tutorSheet = file.read().splitlines() # Split the file into a list with each line as an item
        tutorSheet = tutorSheet[3:] # Remove the first three as they are unneeded
    daysPossible = tutorSheet.pop(0).split(',')[4:] # create a separate list with all the given days
    for eachOption in range(len(daysPossible)): # get rid of the missing spaces and replace it with the correct day
        if daysPossible[eachOption] == "What is the maximum number of classes you would like?": # Check if end column has been reached
            stopLimit = eachOption # Set the stop limit for ease later
            daysPossible = daysPossible[:eachOption]
            break
        else:
            if daysPossible[eachOption] == "": # Set the empty space as the previous day
                daysPossible[eachOption] = daysPossible[eachOption-1]
    timesPossible = tutorSheet.pop(0).split(',')[4:stopLimit+4] # create a separate list with all the given times
    for eachTime in range(len(timesPossible)): # add the given times according to the given days in a dictionary
        if daysPossible[eachTime] in timetable.keys(): # Create timetable
            timetable[daysPossible[eachTime]].append(timesPossible[eachTime])
        else:
            timetable[daysPossible[eachTime]] = [timesPossible[eachTime]]
    
    # Start Student Creation Process
    with open(studentCSV, "r") as file:
        studentSheet = file.read().splitlines()[1:] # Convert file into list with each line as an item
        for eachStudent in studentSheet:
            # Convert each line into a temporary list with each relevant data
            temp = eachStudent.split(',')[1:] # The first column of the csv file is for timestamps, so remove straight away
            temp = fixtemp(temp) # Remove any " if any at all
            # Create the student's availabilities based on their given responses
            for eachStat in range(len(temp)):
                if eachStat in range(5): # Ignore the first 5 indexes of the list (not relevant)
                    pass
                else:
                    if "Early" in temp[eachStat] and "Late" in temp[eachStat]: # If available for both Early and Late, set it to 3
                        temp[eachStat] = 3
                    elif "Early" in temp[eachStat]: # If only available for Early session, set it to 1
                        temp[eachStat] = 1
                    elif "Late" in temp[eachStat]: # If only available for Late session, set it to 2
                        temp[eachStat] = 2
                    else:
                        temp[eachStat] = 0 # Not available
            # Create a Student object to represent the student
            studentList.append(Student(temp[0],temp[1],temp[2],temp[3],temp[4],temp[5],temp[6],temp[7],temp[8],temp[9]))
    numberOfStudents = len(studentList)
    duplicate = True
    # Check for students with same name and initial
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

    yearLevelStats() # Create the statistics for the year levels

    # Find the number of irrelevant rooms
    for eachLine in tutorSheet:
        if "Rooms:" in eachLine:  # Check for the line with the relevant phrase in it
            # find the possible rooms via the next line after finding the key word
            availableClassrooms = tutorSheet[tutorSheet.index(eachLine)+1].split("\"")[1]
            availableClassrooms = availableClassrooms.split(',')  # turn into list
            tutorSheet = tutorSheet[0:tutorSheet.index(eachLine)]  # Remove all irrelevant rows
            break

    # Start converting the tutors into Classes
    for eachTutor in tutorSheet:
        temp = eachTutor.split(',')[1:] # Ignore first column as it is always empty
        if temp[0] == "": # If empty, skip it
            pass
        else:
            tutorList.append(Tutor(temp[0],temp[1],temp[2],temp[3:15],temp[15],temp[16])) # Create the Tutor Class
    # Check for any duplicate names
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
    
    # Begin the class creation process
    # Set up the timetableClassrooms dictionary
    for i in timetable.keys():
        # Create a rooted dictionary for each day to represent the early and late sessions
        timetableClassrooms[i] = {
            "Early": {},
            "Late": {}
        }
        # Now add the rooms as keys to each rooted dictionary
        earlysession = True # Used to switch between early and late session
        for j in range(2):
            if earlysession:
                session = "Early" 
            else:
                session = "Late"
            for eachroom in availableClassrooms:
                classroomList.append(Class(i, session, eachroom)) # Create the class Class to represent each room
                timetableClassrooms[i][session][eachroom] = len(classroomList)-1 #index identity
            earlysession = not(earlysession)
    
    # Remove any impossible year levels
    yearlevelcleaning()   

    # Begin creating classes by going through each possible year level
    allyearlevels = list(yearlevelstats.keys())
    tempyearlevel = allyearlevels.pop(0)
    currentpriority = [2] # List that contains that acceptable availabilities
    indexallowed = 0    # Used for only getting classes outside the tutor's first priority if needed
    attemptcounter = 0 # Number of attempts
    while checkclasses(tempyearlevel):
        # Create a class using createClass function
        # First we find a tutor that has the year level and is not maxed out on classes and matches the requirements
        attemptcounter += 1
        for tutor in tutorList:
            if tempyearlevel in tutor.yearlevels and tutor.yearlevels.index(tempyearlevel) <= indexallowed and len(tutor.classes) < tutor.maximum and [i for i in currentpriority if i in tutor.availability[startnum:endnum]]:
                # Once found, randomly pick one of their priorities
                try:
                    value = tutor.availability.index(0)
                except ValueError: # Just in case they're full on availabilities
                    try: 
                        value = tutor.availability.index(3)
                    except ValueError:
                        value = randint(0, len(tutor.availability) - 1)
                while not(daysPossible[value] in Student.daylist and tutor.availability[value] in currentpriority):
                    value = randint(0,len(tutor.availability) - 1)
                day = daysPossible[value]  # Check which day it is
                if value % 2 == 0:  # is it early or late session
                    day = f'E{day}'
                else:
                    day = f'L{day}'
                createclass(tutorList.index(tutor), day, tutor.subject, tempyearlevel)  # Create the class with the tutor
                # Attempt to create another session for the tutor with the other time blocking
                if len(tutor.classes) < tutor.maximum: # Check first that they can fit another class
                    match value % 2:
                        case 0: # If just created an early session, create a late session
                            if tutor.availability[value + 1] in currentpriority:
                                day = "L" + day[1:]
                                createclass(tutorList.index(tutor), day, tutor.subject, tempyearlevel)
                        case 1: # If just created a late session, create an early session
                            if tutor.availability[value - 1] in currentpriority:
                                day = "E" + day[1:]
                                createclass(tutorList.index(tutor),day, tutor.subject, tempyearlevel)
        # If the year level is completed, switch to the next year level
        # If no more year levels are available then it is complete
        if not(checkclasses(tempyearlevel)):
            try:
                tempyearlevel = allyearlevels.pop(0)
                if 1 in currentpriority:
                    currentpriority.remove(1)
                attemptcounter = 0
                indexallowed = 0
            except IndexError:
                pass
        # If not enough classes can be made, first extend the year level range, then append 1 to the priority counter
        if attemptcounter == 15:
            currentpriority.append(1)
        elif attemptcounter % 5 == 0:
            indexallowed += 1
        elif attemptcounter > 10000:
            print("FUCK")
            return Exception
    
    # Attempt to create more classrooms for higher chance of less students without any classes
    # The exact same thing as the above algorithm except that it switches between English and Maths subjects randomly and takes the tutor's first year level preference
    if not(1 in currentpriority):
        currentpriority.append(1)
    reallycoolnumber = floor(numberOfStudents / 50)
    currentsubject = ["Maths", "English"]
    for i in range(reallycoolnumber):
        for tutor in tutorList:
            if len(tutor.classes) < tutor.maximum and tutor.subject == currentsubject[0] and [i for i in currentpriority if i in tutor.availability[startnum:endnum]]:
                try:
                    chosen = tutor.availability.index(3)
                except ValueError:
                    chosen = tutor.availability.index(0)
                while (tutor.availability[chosen] == 0 or tutor.availability[chosen] == 3) or not(daysPossible[chosen] in Student.daylist):
                    chosen = randint(0,len(tutor.availability)-1)
                day = daysPossible[chosen]  # which day is it
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
                currentsubject.append(currentsubject.pop(0))  # Recycle the first subject to the back

    # Now that everything has been setup, begin assigning students to classes
    switchScreens()

# If the button is clicked attempt to start the algorithm
sWindow.CreateTimetableButton.clicked.connect(lambda: programBegin())

###-------------------------------------------------------------------------------
# Loading Screen

lWindow = PyUI.loadUi(findui("UIfiles/loadingScren.ui"))
lWindow.setWindowTitle("Creating Classes...")

lWindow.progressBar.setValue(0) # Set the progress bar to 0%
completelydoomed = [] # List of students who are completely doomed

def switchScreens(): # Switch screens
    lWindow.show()
    sWindow.close()
    startAlgorithm()

def startAlgorithm(): # Begin adding students to classes through the Gale Shapley Algorithm
    mainsubject = "Maths" # Begin with Maths as the focus subject
    print("fadjkadfssadfklasfklkldfs")
    while not(checkstudents(mainsubject)):
        for student in range(len(studentList)):
            if studentList[student].classes[mainsubject] == None:
                # Run the algorithm with the selected student
                if modifiedGaleShapley(student,mainsubject): # Returns True if the student successfully found a class
                    pass
                else:
                    # If failed, check that the student still has other availabilities, otherwise set them as doomed
                    if len(studentList[student].availability) == 0:
                        studentList[student].classes[mainsubject] = "None"
            else:
                pass
        
        # If all students either have a subject or are doomed, switch to English or end the algorithm
        if checkstudents(mainsubject):
            if mainsubject == "Maths":
                mainsubject = "English"
                for student in range(len(studentList)):
                    studentList[student].switching() # Reset all students' availabilities
    endOfAlgorithm() # Begin the finishing touches

def modifiedGaleShapley(student: int, subject: str):
    ### A modified version of the Gale Shapley Algorithm. The proposers will be the students and the proposed-to will be the classes
    ### The classes will want the student with the smallest priority
    # get the next availability of the student
    day = studentList[student].availability.pop(0)
    studentList[student].updatePriority()  # update the student's priority
    # check whether it's an early or late session
    session = earlyorlate(day[0])

    nlist = []  # list of all possible classes that fit the conditions
    # Check each classroom in the session that fits the year level and subject
    for classroom in timetableClassrooms[day[1:]][session].keys():
        if classroomList[timetableClassrooms[day[1:]][session][classroom]].yearlevel == studentList[student].yearLevel and classroomList[timetableClassrooms[day[1:]][session][classroom]].subject == subject:
            nlist.append(timetableClassrooms[day[1:]][session][classroom])

    # If no available classrooms, attempt to switch classes (usually does not work) otherwise return False
    if len(nlist) == 0:
        if studentList[student].priority == 0:  # If no classes possible
            if attemptswitch(student, subject):
                return True
            else:
                # Set to string None which the algorithm will skip
                studentList[student].classes[subject] = "None"
        else:  # Else return False
            return False

    for eachclass in nlist:  # check if any of the classes have an open seat
        if len(classroomList[eachclass].students) < 6:
            # Add a student to the class which will return True
            return addstudent(eachclass, student)

    # If all classes are full, call upon the studentshifting function
    return studentshifting(nlist, student)

def endOfAlgorithm():
    global classroomList, tutorList, completelydoomed
    # First start by removing all classes with one teacher only
    for eachclass in (classroomList):
        if len(eachclass.students) == 1:
            classroomDelete(classroomList.index(eachclass))
    
    # Begin back up classes creation algorithm
    contingencyplan()
    statuscheck()

    # Now clean up all the classes for QoL purposes
    onlineclassroomswitching()
    findofflineonlinestudents() # Try to clean the classes
    classroomswitching() 
    remainingstudents()
    # now that all classes have been made and cleaned, begin naming them
    classnaming()
    finishingscreen() # Switch to the final screen

def remainingstudents(): # Create a text file for any students who have no class available
    remains = []
    for student in studentList:
        if "None" in student.classes.values():
            remains.append(student)
    from datetime import datetime
    with open("Errors.txt", "w") as errorfile:
        errorfile.write(f'{datetime.now().strftime("%H:%M:%S")}\n')
        errorfile.write(f"Students who did not receive a class: {len(remains)}\n\n")
        for student in remains:
            errorfile.write(f'({",".join([i for i in student.classes.keys() if student.classes[i] == "None"])})\n{student.name}\n{student.email}\nYear {student.yearLevel}\nAttendance Method: {student.place}\nAvailabilities: {student.originalavailability}\n')
            errorfile.write("\n")
    return

def classnaming(): # Give each class a name
    global englishyearlevelnaming, mathsyearlevelnaming, classroomList, timetableClassrooms
    # Go through every available class and name them
    for classroom in classroomList:
        if len(classroom.students) >= 2: # Check that is not an empty class
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
        elif len(classroom.students) == 1: # Delete the class if it has only 1 student
            classroomDelete(classroomList.index(classroom))
    
    # Switch online class
    for day in timetableClassrooms.keys(): # Check each day
        for session in timetableClassrooms[day].keys(): # Check each session of the day
            importantlist = [i for i in timetableClassrooms[day][session].keys() if "Online" in i] # Make a list with all Online sessions
            if importantlist: # Check that the list is not empty before running the function
                removeonlineclassrooms(day, session, importantlist)

def removeonlineclassrooms(day: str, session: str, nlist: list):
    global timetableClassrooms
    # Remove all unnecessary (empty) online classroom
    poppinglist = []
    for room in nlist:
        if len(classroomList[timetableClassrooms[day][session][room]].students) <= 1: # Check that there is only a tutor
            poppinglist.append(room)
    for popping in poppinglist: # Remove each unnecessary classroom
        timetableClassrooms[day][session].pop(popping)

def backup(unavailable: dict): # Check all students that have "None" in their availabilities
    global doomedstudentlist
    doomedstudentlist = []
    for student in range(len(studentList)): # Find all students without a class
        for subject in studentList[student].classes.keys():
            if studentList[student].classes[subject] == "None" and not(student in doomedstudentlist):
                doomedstudentlist.append(student)
    return whatclasses(unavailable)

def contingencyplan(): # Final attempt to create a class for all students
    asdfdict = {}

    for i in yearlevelstats.keys():
        asdfdict[i] = {
            "Maths": [],
            "English": []
        }
    
    dictionary = backup(asdfdict) # Back up function needs a dictionary that represents the unavailable session, so we send an empty dictionary in

    # now that we have the most common times needed, take the most popular time and find a tutor with an availability for that time
    # if no tutor has an availability for that time, remove it, which is what the following variable is for

    unavailablesessions = {} # some sessions may not be possible. this dictionary will hold the data

    # Set up the unavailable sessions with rooted dictionaries for each year level with each subject
    for yearlevel in dictionary.keys(): 
        unavailablesessions[yearlevel] = {}
        for subject in dictionary[yearlevel].keys():
            unavailablesessions[yearlevel][subject] = []
    while dictionary != {}:
        statuscheck() # Set the progress bar

        # Start by finding the most popular session time and its subject and year level
        classfocus = findMax(dictionary) # returns [session, subject, yearlevel]

        # Find all tutors with this availability and subject and year level and not maxed on classes.
        # Set up the conditions first
        temptutorlist = [] # List for all possible tutors
        # Find the availability that represents the session
        num = Tutor.daylist.index(classfocus[0][1:]) * 2
        if classfocus[0][0] == "L":
            num += 1

        # Now that the conditions have been stated, find all tutors that fit the conditions
        for tutor in range(len(tutorList)):
            if tutorList[tutor].availability[num] in [1, 2] and tutorList[tutor].subject == classfocus[1] and classfocus[2] in tutorList[tutor].yearlevels and len(tutorList[tutor].classes) < tutorList[tutor].maximum:
                temptutorlist.append(tutor)
        # If the tutor list is empty, than the session is unavailable and add it to unavailablesessions dictionary
        if len(temptutorlist) == 0:
            unavailablesessions[classfocus[2]][classfocus[1]].append(classfocus[0])
        else:
            # find tutor with least amount of classes
            min = [None, float('inf')]  # [tutorindex, length of their classes]
            for eachtutor in temptutorlist:
                tempamount = len(tutorList[eachtutor].classes)
                # find least amount of classes
                if tempamount <= min[1]:
                    # If the priority is the same, see who wants the year level more via lower index in yearlevel attribute. Pass if they are the same
                    if tempamount == min[1] and tutorList[eachtutor].yearlevels.index(classfocus[2]) > tutorList[min[0]].yearlevels.index(classfocus[2]):
                        pass
                    else:
                        min = [eachtutor, tempamount]
            # create a class with the chosen tutor
            newclass = createclass(min[0], classfocus[0], classfocus[1], classfocus[2]) # tutor, session, subject, year level
            appendingstudentlist = newkids(newclass) # Find 5 (or less) students with the lowest priorities
            for eachstudent in appendingstudentlist:
                addstudent(newclass, eachstudent) # Add them to the class
        # Update the dictionary
        dictionary = backup(unavailablesessions)

def classroomDelete(classroom: int):
    global classroomList
    # Remove the classroom to default settings and remove it from the tutor
    temptutor = classroomList[classroom].students.pop(0) # remove the tutor who is the only student
    tutorList[temptutor].classes.remove(classroom) # remove the class from the tutor
    classroomList[classroom].yearlevel = "0" # set the year level to 0
    # find out which availability the class represented
    num = Tutor.daylist.index(classroomList[classroom].day) * 2 
    match classroomList[classroom].time:
        case "Early":
            num += 0
        case "Late":
            num += 1
    tutorList[temptutor].availability[num] = tutorList[temptutor].originalavailability[num] # update the availability to its original

def checkstudents(subject: str):    # Check that all students have a class for a certain subject
    statuscheck() # Update the progres bar
    # Verify they have a class by checking that the class is not None (NoneType not String)
    for student in studentList:
       if student.classes[subject] == None: # They are missing a class
           return False
    return True

def statuscheck(): # Check what percentage of students that do not have None or "None" in their classes (a.k.a. How many students have classes)
    tempnum = 0 # Counter
    for student in studentList:
        for i in student.classes.keys():
            if not student.classes[i] in [None,"None"]:
                tempnum += 0.5
    finalvalue = int(tempnum * 100 / numberOfStudents) # Find it as a percentage
    lWindow.progressBar.setValue(finalvalue) # Set the progress bar to the percentage

doomedstudentlist = []

def attemptswitch(student: int, subject: str): # try to switch a student in using their old availabilities
    possiblesessions = [] # List of classroom id
    # Check each session in the student's original availability and see if any possible sessions exist
    for eachsession in studentList[student].originalavailability:
        tempvar = earlyorlate(eachsession[0])
        for item in timetableClassrooms[eachsession[1:]][tempvar].keys():
            # Check if the class fits the conditions
            if classroomList[timetableClassrooms[eachsession[1:]][tempvar][item]].yearlevel == studentList[student].yearLevel and classroomList[timetableClassrooms[eachsession[1:]][tempvar][item]].subject == subject:
                possiblesessions.append(timetableClassrooms[eachsession[1:]][tempvar][item])
    if len(possiblesessions) == 0:
        return False # no classes available
    else:
        return studentshifting(possiblesessions, student) # Attempt to shift students

def earlyorlate(n: str): # quick function to see if early or late session
    match n:
        case "E": # If it starts with E, it's early
            return "Early"
        case "L":
            return "Late"  # If it starts with L, it's late

def newkids(classroom: int): # function finds the lowest priority students and returns them
    session = f'{classroomList[classroom].time[0]}{classroomList[classroom].day}' # Session as a string
    theyearlevel = classroomList[classroom].yearlevel # Year level
    potentiallist = [] # list of all potential students
    for student in doomedstudentlist:
        # check if the session is in the availability and matching year level and does not have a class at this time
        if session in studentList[student].originalavailability and studentList[student].yearLevel == theyearlevel and checknotsame(classroom, student):
            potentiallist.append(student)
    return bubblesort5(potentiallist) # Return the 5 students with the lowest priority via Bubble Sort

def bubblesort5(nlist: list): # do bubble sort in ascending order but only for the first 5 or less indexes
    # Sort the list via their priority minus the number of classes they need (for higher priority)
    for i in range(len(nlist)):
        if i == 5:
            return nlist[:5] # return only the first 5 indexes of the list (remove the last one)
        min = len(studentList[nlist[i]].originalavailability) - len([k for k in studentList[nlist[i]].classes.values() if k in [None,"None"]])
        for j in range(i + 1,len(nlist)):
            if len(studentList[nlist[j]].originalavailability) - len([k for k in studentList[nlist[i]].classes.values() if k in [None, "None"]]) < min:
                min = len(studentList[nlist[j]].originalavailability) - len([k for k in studentList[nlist[i]].classes.values() if k in [None, "None"]])
                nlist[i], nlist[j] = nlist[j], nlist[i]
    return nlist # if the maximum of 5 students is not reached, return the whole list

def whatclasses(unavailable: dict): # Find out which classes are still needed unless they are not possible
    global doomedstudentlist
    dictionary = {}
    # Set the dictionary up with a rooted dictionary that contains each subject
    for i in yearlevelstats.keys():
        dictionary[i] = {
            "Maths": {},
            "English": {}
        }
    # Check each student and obtain their availability
    for student in doomedstudentlist:
        missingsubject = [i for i in studentList[student].classes.keys() if studentList[student].classes[i] == "None"] # Make a list with each subject that the student is missing
        tempvar = [i for i in studentList[student].classes.values() if not(i in [None, "None"])]
        if tempvar:
            classroomobject = classroomList[tempvar[0]]  # Get the student's current class as an object
        else:
            classroomobject = Class("None","None","None") # If the student doesn't have a current class, make an empty one
        for availability in studentList[student].originalavailability: # Check each of the student's availability
            if not(classroomobject.time == earlyorlate(availability[0]) and classroomobject.day == availability[1:]): # Check that the current availability does not clash with the student's current class
                for subject in missingsubject:
                    try:
                        dictionary[studentList[student].yearLevel][subject][availability] += 1 # Add it to the dictionary if it exists
                    except KeyError:
                        # If it currently doesn't exist, check that it is NOT unavailable first and then add it if it is
                        if not(availability in unavailable[studentList[student].yearLevel][subject]): # Check that it is not an unavailable availability
                            dictionary[studentList[student].yearLevel][subject][availability] = 1
    
    # Clean the dictionary of any empty rooted dictionaries
    ultimatedestroylist = [] # Ultimate destroy list for removing year levels
    for yearlevel in dictionary.keys():
        destroylist = [] # Destroy list for removing subjects
        for subject in dictionary[yearlevel].keys():
            if dictionary[yearlevel][subject] == {}:
                destroylist.append(subject) # Add the subject to the destroy list if empty dictionary
    
        for eachsubject in destroylist: # Remove all subjects in the destroy list
            dictionary[yearlevel].pop(eachsubject)

        if dictionary[yearlevel] == {}: # Now check if the year level is empty, if it is, add it to the ultimate destroy list
            ultimatedestroylist.append(yearlevel)

    for destruction in ultimatedestroylist: # Remove all year levels in the ultimate destroy list
        dictionary.pop(destruction)

    return dictionary # Return the dictionary

def createclass(tutor: int, session: str, thesubject: str, yearlevel: str): # create a brand new class and return its index
    global classroomList, tutorList
    time = earlyorlate(session[0]) # Find if the session is early or late

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
                tutorList[tutor].availability[whichavailabilityindex(session)] = 3  # Set the classtype
                return num
    
    # create online class if not returned
    tempnum = howmanyonlineclasses(session[1:],time) # Find which online class
    classroomList.append(Class(session[1:],time,f'Online{tempnum}')) # Create a new Class object
    num = len(classroomList) - 1 # Find the index of the Class object

    timetableClassrooms[session[1:]][time][f'Online{tempnum}'] = num # Add a new session for Online classroom
    classroomList[num].students.append(tutor)   # Add the tutor
    tutorList[tutor].classes.append(num)    # Add the class to the tutor
    classroomList[num].subject = thesubject # Set the subject
    classroomList[num].yearlevel = yearlevel    # Set the year level
    # set the availability as 3
    tutorList[tutor].availability[whichavailabilityindex(session)] = 3
    classroomList[num].classtype = "Online"  # Set the classtype
    return num

def whichavailabilityindex(session: str): # Find which index the session would be in the tutor availability list
    num = Tutor.daylist.index(session[1:]) * 2 # First find the index according to the Tutor Daylist
    # Then check whether it's an early or late session
    match session[0]:
        case "E":
            num += 0
        case "L":
            num += 1
    return num

def findMax(dictionary: dict): # find the maximum value in the dictionary
    max = [0, 0, "", "0"] # [value, session, subject, yearlevel]
    # Check each year level via linear search
    for eachyearlevel in dictionary.keys():
        # Check each subject
        for eachsubject in dictionary[eachyearlevel].keys():
            # Check each availability
            for eachsession in dictionary[eachyearlevel][eachsubject].keys():
                # If the value is larger than the current largest value, then set the maximum to that value
                if dictionary[eachyearlevel][eachsubject][eachsession] > max[0]:
                    max = [dictionary[eachyearlevel][eachsubject][eachsession], eachsession, eachsubject, eachyearlevel]
    return max[1:] # [session, subject, yearlevel]

def studentshifting(classlist: list, student: int): # see if any students have a lower priority than the current one
    # find the student with the largest priority
    tempstudent = [0, None, -2]  # [class index, student index, priority]
    # Check each student in each classroom in the classlist to look for the highest priority
    for item in classlist:
        # Check each student in the classroom
        for eachstudent in classroomList[item].students[1:]:
            if studentList[eachstudent].priority >= tempstudent[2] and eachstudent != tempstudent[1]: # check for higher priority and not the same student
                tempstudent = [item, eachstudent, studentList[eachstudent].priority]
    
    # kick the student with the highest priority IF it's higher than the current student
    if tempstudent[2] > studentList[student].priority and tempstudent[1] != None:
        kickstudent(tempstudent[0], tempstudent[1], student) # kicks the student and adds a new one
        return True
    else:
        return False

def kickstudent(classroom: int, studenttokick: int, studenttoadd: int): # kick a student out and replace them with the new student
    classroomList[classroom].removeStudent(studenttokick) # Remove the desired student
    addstudent(classroom,studenttoadd) # Add the new student

def addstudent(classroom: int, student: int): # add a student to class
    classroomList[classroom].students.append(student) # Append the student to the classroom's student list
    studentList[student].classes[classroomList[classroom].subject] = classroom # Add the classroom to the student's classes dictionary
    return True # Return True for Gale Shapley Algorithm

def checknotsame(classroom: int, student: int): # check that the student does not already have a class during that time
    found = False # Set a variable to check if you found it or not
    # Find the classroom that is not set as "None" or None
    for i in studentList[student].classes.values():
        if not(i in [None,"None"]):
            tempnum = i
            found = True
    # If both are classes are None/"None", then return True as the student is not in any classrooms
    # Else, check that the day and time of the focus classroom and compare it to the student's classroom 
    if found:
        return bool([classroomList[tempnum].day,classroomList[tempnum].time] != [classroomList[classroom].day,classroomList[classroom].time])
    else:
        return True

###-------------------------------------------------------------------------------------------------------------------
# Class Cleaning Functions

def findofflineonlinestudents(): # Try to switch any in-person students that are in an online class with a student in an online class
    # Check each student in each day session
    for day in timetableClassrooms.keys():
        for session in timetableClassrooms[day].keys():
            inpersonstudentlist = [] # List for offline students in online class
            # Search each online classroom for offline students
            for onlineclassroom in [i for i in timetableClassrooms[day][session].keys() if ("Online" in classroomList[timetableClassrooms[day][session][i]].name and len(classroomList[timetableClassrooms[day][session][i]].students) >= 2)]: # Looks through each classroom that is online and has at least 1 student
                for offlinestudent in classroomList[timetableClassrooms[day][session][onlineclassroom]].students[1:]: 
                    if studentList[offlinestudent].place == "In-Person": # Check if the student is offline
                        inpersonstudentlist.append([offlinestudent,onlineclassroom]) # Append a list containing the offline student and their classroom
    canswitch(inpersonstudentlist)

    for day in timetableClassrooms.keys():
        for session in timetableClassrooms[day].keys():
            onlinestudentlist = []  # List for online student in offline class
            # Search each offline classroom for online students
            # Looks through each classroom that is offline and has at least 1 student
            for offlineclassroom in [i for i in timetableClassrooms[day][session].keys() if (not ("Online" in classroomList[timetableClassrooms[day][session][i]].name) and len(classroomList[timetableClassrooms[day][session][i]].students) >= 2)]:
                for onlinestudent in classroomList[timetableClassrooms[day][session][offlineclassroom]].students[1:]:
                    # Check if the student is online
                    if studentList[onlinestudent].place == "Online":
                        # Append a list containing the online student and their classroom
                        onlinestudentlist.append([onlinestudent,timetableClassrooms[day][session][offlineclassroom]])
    canmove(onlinestudentlist)
    return
        
def canswitch(nlist: list): # Go through each given student's availability and attempt to switch them with an online student
    while nlist:
        # Reset the variables
        focusstudent = nlist.pop(0)
        focusstudent, focusclassroom = focusstudent[0], focusstudent[1]
        breaking = False # Indicates whether or not you have switched (needed so you don't switch again randomly) and causes a chain break so it can start working on the next student
        # Check each availability
        for availability in studentList[focusstudent].originalavailability:
            # Check each offline room in the day session 
            for room in timetableClassrooms[availability[1:]][earlyorlate(availability[0])].keys():
                # Check if the classroom has the same subject and year level
                if classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].yearlevel == studentList[focusstudent].yearLevel and classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].subject == classroomList[focusclassroom].subject and not("Online" in room):
                    # If it does, check if it's full on students. If it is, go through each student and see if they are an online student
                    if len(classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].students) == 6:
                        for onlinestudent in classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].students:
                            if studentList[onlinestudent].place == "Online" and availability in studentList[onlinestudent].availability and checknotsame(classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]],onlinestudent):
                                # If the student is an online student AND has an availability in the chosen student's classroom AND is not currently taking a class at that time, then switch them
                                switchstudents(focusstudent, focusclassroom, onlinestudent, timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room])
                                breaking = True
                                break
                    # If the classroom isn't full, remove the student from their current classroom and add them to that classroom
                    else:
                        classroomList[focusclassroom].removeStudent(focusstudent)
                        addstudent(classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]],focusstudent)
                        breaking = True
                if breaking:
                    break
                else:
                    pass
            if breaking:
                break
            else:
                pass
    return

def canmove(onlinelist:list): # Go through each given student's availability and attempt to add them to an available online class
    while onlinelist:
        # Reset the varaibles
        student = onlinelist.pop(0)
        student, classroom = student[0], student[1]
        breaking = False # Indicates whether or not you have switched (needed so you don't switch again randomly) and causes a chain break so it can start working on the next student
        # Go through each availability
        for availability in studentList[student].originalavailability:
            # Check each room in that availability
            for room in timetableClassrooms[availability[1:]][earlyorlate(availability[0])].keys():
                # Check that the classroom fits the condition (Online, yearlevel and subject)
                print(timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room])
                print(type(timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]))
                if classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].yearlevel == studentList[student].yearLevel and classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].subject == classroomList[classroom].subject and "Online" in room:
                    # Check that the classroom has space
                    if len(classroomList[timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room]].students) < 6:
                        classroomList[classroom].removeStudent(student) # Remove the student from previous classroom
                        addstudent(timetableClassrooms[availability[1:]][earlyorlate(availability[0])][room], student) # Add the student to the new classroom
                        breaking = True # Begin breaking 
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
    subject = classroomList[classroom1].subject # Set the subject
    # First swap the students around
    classroomList[classroom1].students[classroomList[classroom1].students[1:].index(student1) + 1], classroomList[classroom2].students[classroomList[classroom2].students[1:].index(student2) + 1] = student2, student1
    # Next, swap their availabilities around
    studentList[student1].classes[subject], studentList[student2].classes[subject] = classroom2, classroom1
    return

def classroomswitching(): # If on any day, a tutor has a class in both early and late session, switch the rooms so that they have the same room in both session
    for day in timetableClassrooms.keys(): # Check each day
        for room in timetableClassrooms[day]["Early"].keys(): # Now check each room in the "Early" Session
            # Verify that the classroom is valid and not online before focusing on the tutor
            if len(classroomList[timetableClassrooms[day]["Early"][room]].students) >= 2 and not ("Online" in classroomList[timetableClassrooms[day]["Early"][room]].classroom) and not(tutorList[classroomList[timetableClassrooms[day]["Early"][room]].students[0]].classplace == "Online"):
                tutorname = tutorList[classroomList[timetableClassrooms[day]["Early"][room]].students[0]].name # Focus on the tutor
                # Check each late session on the same day. If the tutor is teaching any of these classes, switch them
                for lateroom in timetableClassrooms[day]["Late"].keys():
                    # Check the conditions
                    if len(classroomList[timetableClassrooms[day]["Late"][lateroom]].students) >= 2 and tutorList[classroomList[timetableClassrooms[day]["Late"][lateroom]].students[0]].name == tutorname and not("Online" in lateroom):
                        classroomswitch(timetableClassrooms[day]["Late"][room],timetableClassrooms[day]["Late"][lateroom]) # Switch the classrooms around
                        break

def onlineclassroomswitching(): # If any tutor that wants to teach In-Person is teaching an online class, try to switch them to an offline class
    ''' TRY TO MOVE THIS EARLIER '''
    for day in timetableClassrooms.keys(): # Check each day 
        for session in timetableClassrooms[day].keys(): # Check each session
            # Check each online room for an offline tutor
            for onlineroom in [i for i in timetableClassrooms[day][session].keys() if "Online" in i and len(classroomList[timetableClassrooms[day][session][i]].students) >= 2]:
                if tutorList[classroomList[timetableClassrooms[day][session][onlineroom]].students[0]].classplace != "Online":
                    # Check each offline room if it is empty
                    for offlineroom in [j for j in timetableClassrooms[day][session].keys() if not ("Online" in j) and len(classroomList[timetableClassrooms[day][session][j]].students) <= 1]:
                        # Switch them if true
                        classroomswitch(timetableClassrooms[day][session][offlineroom], timetableClassrooms[day][session][onlineroom])
                        timetableClassrooms[day][session].pop(onlineroom)
                        break

def classroomswitch(classroom1: int, classroom2: int): # Switch two classrooms
    global timetableClassrooms, classroomList
    day = classroomList[classroom1].day # Set the day
    session = classroomList[classroom1].time # Set the session
    room1 = classroomList[classroom1].classroom # Set the first room
    room2 = classroomList[classroom2].classroom # Set the second room
    # Switch the room's pointers
    timetableClassrooms[day][session][room1], timetableClassrooms[day][session][room2] = timetableClassrooms[day][session][room2], timetableClassrooms[day][session][room1]
    # Switch the classrooms of both classes around
    classroomList[classroom1].classroom, classroomList[classroom2].classroom = classroomList[classroom2].classroom, classroomList[classroom1].classroom

###--------------------------------------------------------------------------
# Information Display Section

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

def finishingscreen(): # Display the software
    setdWindow()    # Create the display window
    lWindow.close() # Close the loading screen

def setdWindow():
    global dWindow, earlylatetimes
    # Find the most number of classes stated. This will be the number of rows
    maximum = []
    for i in timetableClassrooms.keys():
        for j in timetableClassrooms[i].keys():
            if len(timetableClassrooms[i][j].keys()) > len(maximum):
                maximum = list(timetableClassrooms[i][j].keys())
    
    # Share the data with the Final Window
    FinalWindow.maindictionary = dict(timetableClassrooms)  # Classroom Dictionary with each pointer
    FinalWindow.classList = list(classroomList) # Classroom Object List
    FinalWindow.tutorList = list(tutorList) # Tutor Object List
    FinalWindow.studentList = list(studentList) # Student Object List
    FinalWindow.earlylatetimes = dict(earlylatetimes)   # Relevant timings for each class based on their session
    dWindow = FinalWindow(Student.daylist, maximum) # Create the Window and save it as an object variable
    dWindow.button.clicked.connect(csvoutput)   # Add the function to the button

def csvoutput():  # This will be the output for the csv
    ### The template for the CSV is already online. Now all we have to do is create the csv so that it follows the format
    # Begin creating the csv file
    global timetableClassrooms
    with open("timetable.csv", "w") as file:    # Open the CSV, Reset it and Begin Writing 
        # Write down the Monday Workshop and Colour Legend Box
        file.write(",\n"*2)
        file.write(",Monday (Workshops),,,Colour Legend\n")
        file.write("Early\n")
        file.write(",\n" * 5)
        file.write("Late\n")
        file.write(",\n" * 5)

        # Begin writing down the classes for each day
        dayfocus = 0 # Monday (skipped)
        while dayfocus < 5:
            file.write(",\n"*2) # Spacing between boxes
            dayfocus += 1 # Switch to the next day
            day = Tutor.daylist[dayfocus] # Set the day
            # Headers
            file.write(f',{day}\n,In-Person')
            file.write(","*len(availableClassrooms))
            file.write("Online\n")
            # Create a list where each item is a rooted list that represents each row in the csv
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
                    # Add the students
                    for option in range(5,10):
                        try:
                            if studentList[theclass.students[option-4]].place == "Online": # Add (OL) to the Student's name if they are mainly an online student (useful for admin team)
                                templist[option].append(studentList[theclass.students[option-4]].name + " (OL)")
                            else:
                                templist[option].append(studentList[theclass.students[option-4]].name)
                        except IndexError: # If no more students, leave it blank
                            templist[option].append("")
                # now input it into the file:
                for line in templist:
                    string = ",".join(line)
                    file.write(string + "\n")
    dWindow.button.setText("Done!")
    # Below Code is for checking for any errors or missing students during development phase. 
    # Errors refer to students in a class that they aren't able to attend. Missing students refer to students who do not have a class (will happen often)
    '''tutorstats()
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
    print(dict1)'''

sWindow.show()
sys.exit(app.exec())