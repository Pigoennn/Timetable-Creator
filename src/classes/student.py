# Student Class. All students will have an object that contains their name, email, year level, availability, and attendance method
class Student:

    days: list[str]

    self.first_name: str
    self.last_name: str
    self.last_name_initial: int
    self.name: str
    
    self.email: str
    self.year_level: str
    self.location: str

    self.availability: list[str]
    self.orig_availability: list[str]

    self.priority: int

    self.classes: dict[str, any]

    def __init__(self, email: str, first_name: str, last_name: str, year_level: str, location: str, availability: list[int]):
        # Update the student using the given information
        self.first_name = first_name
        self.last_name = last_name
        self.name = f'{self.first_name} {self.last_name[0]}'
        self.last_name_initial = 0

        self.email = email
        self.year_level = str(year_level[5:])
        self.location = location
        self.availability = []
        self.subject = ""

        # Update the availability based on the given information
        for i in range(len(self.availability)):
            match self.availability[i]:
                case 0: # not available
                    pass
                case 1: # early session
                    self.availability.append(f'E{Student.daylist[i]}')
                case 2: # late session
                    self.availability.append(f'L{Student.daylist[i]}')
                case 3: # both
                    self.availability.append(f'E{Student.daylist[i]}')
                    self.availability.append(f'L{Student.daylist[i]}')

        self.orig_availability = list(self.availability)
        # Classes dictionary for algorithm
        self.classes = {
            "Maths": None,
            "English": None
        }
        self.updatePriority() # Update the priority based on its length

    def update_name(self): # Update the students name (if another student has the same name and initial)
        self.last_name_initial += 1
        self.name += self.lastname[self.last_name_initial]

    def update_priority(self): # Update the students priority and reduce it if the student already has a subject
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