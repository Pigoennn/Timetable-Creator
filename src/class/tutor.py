

class Tutor:

    days: list[str]

    self.full_name: str
    self.first_name: str
    self.last_name: str
    self.last_name_initial: int = 0
    self.name: str

    self.subject: str
    self.year_levels: list[str] = []
    self.location: str

    self.availability: list
    self.orig_availability: list
    self.maximum: int
    
    self.classes = []                       # classes currently being taken
    self.extra_classes: int = 0


    def __init__(self, full_name: str, subject: str, year_level: str, list_information: list, maximum: int, location: str):
        self.full_name = full_name.split(" ")
        self.first_name = self.fullname[0]
        self.last_name = " ".join(self.fullname[1:])        # last name may have multiple parts
        self.name = f'{self.firstname} {self.lastname[0]}'  # default name: first name and initial of last name

        self.subject = subject
        temp: list[str] = year_level.split("/")
        for i in temp:
            self.year_levels.append(i.strip().replace("\"", ""))

        self.availability = list_information
        # change all missing inputs to 0
        for eachNumber in range(len(self.availability)):
            try:
                self.availability[eachNumber] = int(self.availability[eachNumber])
            except ValueError:
                self.availability[eachNumber] = 0
        
        self.orig_availability = list(list_information)     # original availability to store for reset purposes

        self.maximum = int(maximum)                         # maximum number of classes
        self.location = location                            # In-Person, Online or Both

        self.extra_classes = 0

    def updateName(self): # Update their name if there is a tutor with a matching name and initials
        self.last_name_initial += 1
        self.name += self.lastname[self.last_name_initial]