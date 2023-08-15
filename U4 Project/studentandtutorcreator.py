from random import randint, choice, shuffle

namelist = open("Names.txt", "r").read().splitlines()
usednames = []

statistics = open("chance.txt", "r").read().splitlines()
dampeningfactor = float(statistics[5])
statistics = statistics[1].split(" / ")
stats = {}
while len(statistics) > 0:
    temp = statistics.pop(0).split(",")
    stats[temp[0]] = temp[1]
total = sum(stats.values()) # Should be 100
if not total == 100:
    total = 100

yearlevelvalues = []
yearlevelstats = {}

for item in stats.keys():
    yearlevelstats[item] = 0
    for i in range(stats[item]):
        yearlevelvalues.append(item)

def createstudents(number: int):
    global usednames,namelist, yearlevelstats
    with open("student.csv", "w") as file:
        file.write("Timestamp,Email Address,First Name,Last Name\n")
        for i in range(number):
            usednames.append(namelist.pop(randint(0,len(namelist)-1)))
            tempname = usednames[-1].split(" ")
            firstname,lastname = tempname[0], tempname[1]
            yearlevel = "Year "
            temp = choice(yearlevelvalues)
            yearlevelstats[temp] += 1
            yearlevel += temp
            match randint(0,9):
                case 9:
                    place = "Online"
                case _:
                    place = "In-Person"
            dayavailability = []
            for j in range(5):
                dayavailability.append(earlylatechoose())
            while dayavailability.count("") > 3 or (dayavailability.count("") == 4 and dayavailability.count("EarlyLate") == 1):
                dayavailability[randint(0,4)] = earlylatechoose()
            file.write(f'placeholder,{firstname.lower()}{lastname.lower()}@gmail.com,{firstname},{lastname},{yearlevel},{place},{",".join(dayavailability)}\n')

def earlylatechoose():
    chance = randint(1, 100)
    if chance in range(1, 31):
        return "Early"
    elif chance in range(31, 61):
        return "Late"
    elif chance in range(61, 71):
        return "EarlyLate"
    else:
        return ""

def createtutors():
    global usednames,namelist, yearlevelstats
    with open("tutor.csv","w") as file:
        for item in [",'","Tutor Availability",",",",",","]:
            file.write(f'{item}\n')
        while [i for i in yearlevelstats.keys() if yearlevelstats[i] > 0]:
            usednames.append(namelist.pop(randint(0,len(namelist)-1)))
            tempname = usednames[-1]
            match randint(0,1):
                case 0:
                    subject = "Maths"
                case 1:
                    subject = "English"
            chance = randint(1, 100)
            yearlevel = []
            if chance % 2 == 0:
                yearlevel.append("8")
            if chance % 3 == 0:
                yearlevel.append("7")
            if chance % 5 == 0:
                yearlevel.append("6")
            if not yearlevel:
                yearlevel.append("8")
            for j in yearlevel:
                yearlevelstats[j] -= 1
            availability = []
            for i in range(6):
                availability.append(availabilitychoose())
                availability.append(availabilitychoose(availability[-1],True))
            while availability.count("") > 10 or availability.count(2) <= 2:
                chance = randint(0,11)
                if availability[chance] == "":
                    match chance % 2:
                        case 1:
                            availability.append(availabilitychoose(availability[chance-1],True))
                        case 0:
                            availability.append(availabilitychoose())
            maxclasses = minimumcount(availability)
            match randint(1,5):
                case 5:
                    place = "Online"
                case _:
                    place = "In-Person"
            file.write(f',{tempname},{subject},{"/".join(yearlevel)},{",".join(availability)},{maxclasses},{place}\n')

def availabilitychoose(last = 3, latesession = False):
    if not(latesession) or last == "":
        choice = randint(1,10)
        if choice in range(1,6):
            return "2"
        elif choice in range(6,9):
            return "1"
        else:
            return ""
    else:
        match randint(1,10):
            case 10:
                return ""
            case _:
                return last

def minimumcount(nlist: list):
    min = nlist.count(2)
    if 2 < min <= 4:
        return min
    else:
        return randint(4,12)

userinput = input("Number of students ")

createstudents(int(userinput))



print("DONE")