from pathlib import Path

import pytest

from src.classes.session import Session
from src.classes.tutor import Availability, Tutor
from src.config import Settings, load_settings
from src.resources import resource_path

TEST1 = Path(resource_path("testing/test1"))
TEST2 = Path(resource_path("testing/test2"))
TEMPLATE = Path(resource_path("testing/template"))     # blank export of the real Google Sheet

STUDENT_HEADER = "Timestamp,Email Address,First Name,Last Name\n"

# same layout as the real export
TUTOR_HEADER = (
    ',"\n'
    'Tutor Availability",,,,,,,,,,,,,,,,\n'
    ',,,,,,,,"Please put your availabilities in. Use ""2"" if available",,,,\n'
    ",Name,Subject,Year Level,Monday,,Tuesday,,Wednesday,,Thursday,,Friday,,Saturday,,"
    "What is the maximum number of classes you would like?,Online or In-Person?\n"
    ",,,(Put in preference),a,b,a,b,a,b,a,b,a,b,c,d,,Or Both?\n"
)
TUTOR_FOOTER = ',,,,,,,,,,\n,Rooms:,,,,,,,,,,,Help:,,,,,\n,"201,205",,,,\n'


@pytest.fixture
def settings() -> Settings:
    return load_settings(resource_path("settings.txt"))


@pytest.fixture
def write_students(tmp_path):
    """ Write student rows (without the header) to a csv and return its path """
    def write(*rows: str) -> str:
        path = tmp_path / "students.csv"
        path.write_text(STUDENT_HEADER + "".join(row + "\n" for row in rows))
        return str(path)
    return write


@pytest.fixture
def write_tutors(tmp_path):
    """ Write tutor rows to a csv between the usual headings and rooms footer, and return its path """
    def write(*rows: str, header: str = TUTOR_HEADER, footer: str = TUTOR_FOOTER) -> str:
        path = tmp_path / "tutors.csv"
        path.write_text(header + "".join(row + "\n" for row in rows) + footer)
        return str(path)
    return write


def make_tutor(name: str, subject: str, year_levels: list[str], availability: dict[Session, Availability],
               maximum: int = 4, location: str = "In-Person") -> Tutor:
    return Tutor(name, subject, year_levels, availability, maximum, location)
