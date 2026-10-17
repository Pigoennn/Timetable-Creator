""" Make a random student.csv and tutor.csv for trying out the timetable creator

    python testing/testing_creator.py 80 --out testing/test3 --seed 1
"""
import argparse
import csv
import os
from configparser import ConfigParser
from random import Random

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES_FILE = os.path.join(HERE, "Names.txt")
CHANCE_FILE = os.path.join(HERE, "chance.txt")

STUDENT_DAYS = 5                # Tuesday to Saturday
TUTOR_DAYS = 6                  # Monday to Saturday, an early and a late column each
ROOMS = "201,205,206,207,208"

TUTOR_HEADER = [
    ["", "\nTutor Availability"] + [""] * 15,
    [""] * 8 + ['Please put your availabilities in. Use "2" if available for a class, "1" if potentially '
                'availabile for a class or leave blank if unavailable '] + [""] * 9,
    ["", "Name", "Subject", "Year Level", "Monday", "", "Tuesday", "", "Wednesday", "", "Thursday", "",
     "Friday", "", "Saturday", "", "What is the maximum number of classes you would like?", "Online or In-Person?"],
    ["", "", "", "(Put in preference)"] + ["5:00 - 6:30 / 7:00", "6:30 / 7:00 - 9:00"] * 5
    + ["10:00 - 12:00", "12:00 - 2:00", "", "Or Both?"],
]
TUTOR_FOOTER = [
    [""] * 11,
    ["", "Rooms:"] + [""] * 10 + ["Help:"] + [""] * 5,
    ["", ROOMS, "", "", "", ""],
]


def load_chances(path: str = CHANCE_FILE) -> dict:
    """ Read the percentages in chance.txt into {section: {key: int}} """
    parser = ConfigParser()
    parser.optionxform = str                    # keep the keys as written
    parser.read(path)
    return {section: {key: int(value) for key, value in parser[section].items()} for section in parser.sections()}


class NamePicker:
    """ Hands out unique full names, mixing first and last names once the real ones run out """

    def __init__(self, rng: Random, path: str = NAMES_FILE) -> None:
        with open(path) as file:
            full_names = list(dict.fromkeys(line.strip() for line in file if line.strip()))
        self.rng = rng
        self.first_names = [name.split(" ")[0] for name in full_names]
        self.last_names = [name.split(" ")[-1] for name in full_names]
        self.unused = full_names
        self.rng.shuffle(self.unused)
        self.used = set()

    def pick(self) -> tuple[str, str]:
        while self.unused:
            name = self.unused.pop()
            if name not in self.used:
                self.used.add(name)
                return name.split(" ")[0], name.split(" ")[-1]

        if len(self.used) >= len(self.first_names) * len(self.last_names):
            raise ValueError("Ran out of names")
        while True:
            first, last = self.rng.choice(self.first_names), self.rng.choice(self.last_names)
            if f"{first} {last}" not in self.used:
                self.used.add(f"{first} {last}")
                return first, last


def weighted(rng: Random, chances: dict[str, int]) -> str:
    return rng.choices(list(chances), weights=list(chances.values()))[0]


# --- students -----------------------------------------------------------------

def student_availability(rng: Random, chances: dict) -> list[str]:
    """ Early/Late/EarlyLate/blank for each student day, with at least two days filled in """
    def pick() -> str:
        day = weighted(rng, chances["Student Days"])
        return "" if day == "Blank" else day

    days = [pick() for _ in range(STUDENT_DAYS)]
    while days.count("") > STUDENT_DAYS - 2:
        days[rng.randrange(STUDENT_DAYS)] = pick()
    return days


def make_students(count: int, rng: Random, names: NamePicker, chances: dict) -> list[list[str]]:
    rows = []
    for _ in range(count):
        first, last = names.pick()
        year_level = weighted(rng, chances["Year Levels"])
        location = weighted(rng, chances["Student Location"])
        rows.append(["placeholder", f"{first.lower()}{last.lower()}@gmail.com", first, last, f"Year {year_level}",
                     location] + student_availability(rng, chances))
    return rows


# --- tutors -------------------------------------------------------------------

def tutor_year_levels(rng: Random) -> list[str]:
    """ One to four year levels, mostly 8, in a random preference order """
    number = rng.randint(1, 100)
    year_levels = [year for year, divisor in (("8", 2), ("7", 3), ("6", 5)) if number % divisor == 0]
    if number % 7 == 0 or number % 10 == 0:
        year_levels.append("5")
    rng.shuffle(year_levels)
    return year_levels or ["8"]


def tutor_availability(rng: Random) -> list[str]:
    """ "2"/"1"/blank for the early and late session of each tutor day, with at least two "2"s """
    def pick() -> str:
        return rng.choices(["2", "1", ""], weights=[4, 1, 5])[0]

    cells = []
    for _ in range(TUTOR_DAYS):
        early = pick()
        # the late session is usually the same as the early one
        late = pick() if early == "" else ("" if rng.randint(1, 10) == 10 else early)
        cells += [early, late]

    while cells.count("2") < 2:
        cells[rng.randrange(len(cells))] = "2"
    return cells


def maximum_classes(rng: Random, availability: list[str]) -> int:
    available = availability.count("2")
    return available if 2 < available <= 4 else rng.randint(4, 12)


def make_tutors(students: list[list[str]], rng: Random, names: NamePicker, chances: dict) -> list[list[str]]:
    """ Add tutors until every year level has roughly enough of them for its students """
    needed = {year: 0 for year in chances["Year Levels"]}
    for student in students:
        needed[student[4].removeprefix("Year ")] += 1

    rows = []
    while any(count > 0 for count in needed.values()):
        first, last = names.pick()
        subject = rng.choice(["Maths", "English"])
        year_levels = tutor_year_levels(rng)
        for preference, year in enumerate(year_levels):
            needed[year] = needed.get(year, 0) - (4 if preference == 0 else 3)

        availability = tutor_availability(rng)
        location = weighted(rng, chances["Tutor Location"])
        rows.append(["", f"{first} {last}", subject, "/".join(year_levels), *availability,
                     str(maximum_classes(rng, availability)), location])
    return rows


# --- files --------------------------------------------------------------------

def write_files(folder: str, student_count: int, seed: int | None = None) -> None:
    rng = Random(seed)
    names = NamePicker(rng)
    chances = load_chances()

    students = make_students(student_count, rng, names, chances)
    tutors = make_tutors(students, rng, names, chances)

    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "student.csv"), "w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["Timestamp", "Email Address", "First Name", "Last Name"])
        writer.writerows(students)
    with open(os.path.join(folder, "tutor.csv"), "w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerows(TUTOR_HEADER + tutors + TUTOR_FOOTER)


def main() -> None:
    parser = argparse.ArgumentParser(description="Make a random student.csv and tutor.csv")
    parser.add_argument("students", type=int, help="how many students to make")
    parser.add_argument("--out", default=".", help="folder to write the files into (default: here)")
    parser.add_argument("--seed", type=int, help="make the same files every time")
    args = parser.parse_args()

    write_files(args.out, args.students, args.seed)
    print(f"Wrote student.csv and tutor.csv to {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
