import pytest

from src.classes.session import EARLY, LATE, Session
from src.classes.tutor import Availability
from src.loader import LoaderError, load_students, load_tutor_sheet, verify_files
from tests.conftest import TEMPLATE, TEST1, TEST2, TUTOR_FOOTER, TUTOR_HEADER

KAYLEE = ",Kaylee Scott,Maths,8,,,,2,,2,,1,2,2,2,2,5,Online"


# --- students -----------------------------------------------------------------

def test_loads_every_student(settings):
    assert len(load_students(str(TEST1 / "student.csv"), settings)) == 80


def test_student_fields(settings):
    # placeholder,deloresherman@gmail.com,Delores,Herman,Year 8,In-Person,Early,EarlyLate,Early,,Late
    student = load_students(str(TEST1 / "student.csv"), settings)[0]

    assert student.email == "deloresherman@gmail.com"
    assert (student.first_name, student.last_name, student.name) == ("Delores", "Herman", "Delores H")
    assert student.year_level == "8"
    assert student.location == "In-Person"
    assert student.availability == [
        Session("Tuesday", EARLY),
        Session("Wednesday", EARLY),
        Session("Wednesday", LATE),
        Session("Thursday", EARLY),
        Session("Saturday", LATE),
    ]
    assert student.classes == {"Maths": None, "English": None}


def test_student_names_are_unique(settings):
    for path in (TEST1 / "student.csv", TEST2 / "funnystudents.csv"):
        names = [student.name for student in load_students(str(path), settings)]
        assert len(names) == len(set(names))


def test_clashing_student_names_are_lengthened(settings):
    students = {student.email: student for student in load_students(str(TEST2 / "funnystudents.csv"), settings)}
    assert students["ninamiles@gmail.com"].name == "Nina Mi"
    assert students["ninamack@gmail.com"].name == "Nina Ma"


def test_blank_student_lines_are_skipped(settings, write_students):
    path = write_students(
        "t,a@b.c,Ann,Lee,Year 7,Online,Early,,,,Late",
        "",
        "t,c@d.e,Bo,Kim,Year 6,In-Person,,EarlyLate,,,",
    )
    assert [student.name for student in load_students(path, settings)] == ["Ann L", "Bo K"]


def test_student_day_columns_must_match_settings(settings, write_students):
    path = write_students("t,a@b.c,Ann,Lee,Year 7,Online,Early,,,Late")      # 4 day columns, settings has 5
    with pytest.raises(LoaderError, match="Line 2"):
        load_students(path, settings)


# --- tutors -------------------------------------------------------------------

def test_loads_every_tutor_and_room(settings):
    tutors, rooms = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)
    assert len(tutors) == 23
    assert rooms == ["201", "205", "206", "207", "208"]


def test_tutor_fields(settings):
    # ,Kaylee Scott,Maths,8,,,,2,,2,,1,2,2,2,2,5,Online
    tutor = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)[0][0]

    assert (tutor.first_name, tutor.last_name, tutor.name) == ("Kaylee", "Scott", "Kaylee S")
    assert tutor.subject == "Maths"
    assert tutor.year_levels == ["8"]
    assert tutor.maximum == 5
    assert tutor.location == "Online"
    assert tutor.classes == []

    expected = {
        "Monday": (Availability.UNAVAILABLE, Availability.UNAVAILABLE),
        "Tuesday": (Availability.UNAVAILABLE, Availability.AVAILABLE),
        "Wednesday": (Availability.UNAVAILABLE, Availability.AVAILABLE),
        "Thursday": (Availability.UNAVAILABLE, Availability.POTENTIAL),
        "Friday": (Availability.AVAILABLE, Availability.AVAILABLE),
        "Saturday": (Availability.AVAILABLE, Availability.AVAILABLE),
    }
    assert tutor.availability == {
        Session(day, time): value
        for day, values in expected.items()
        for time, value in zip((EARLY, LATE), values)
    }


def test_tutor_year_levels_keep_preference_order(settings):
    tutors = {tutor.full_name: tutor for tutor in load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)[0]}
    assert tutors["India Mann"].year_levels == ["7", "6"]
    assert tutors["Brett Fulton"].year_levels == ["5", "7"]


def test_tutors_do_not_share_lists(settings):
    first, second = load_tutor_sheet(str(TEST1 / "tutor.csv"), settings)[0][:2]
    assert first.classes is not second.classes
    assert first.year_levels is not second.year_levels


def test_unknown_availability_values_are_unavailable(settings, write_tutors):
    path = write_tutors(",Ann Lee,Maths,8,x,3,2,1,,,,,,,,,4,In-Person")
    tutor = load_tutor_sheet(path, settings)[0][0]
    assert tutor.availability_at(Session("Monday", EARLY)) == Availability.UNAVAILABLE
    assert tutor.availability_at(Session("Monday", LATE)) == Availability.UNAVAILABLE
    assert tutor.availability_at(Session("Tuesday", EARLY)) == Availability.AVAILABLE
    assert tutor.availability_at(Session("Tuesday", LATE)) == Availability.POTENTIAL


def test_clashing_tutor_names_are_lengthened(settings, write_tutors):
    path = write_tutors(KAYLEE, ",Kaylee Smith,English,7,,,2,2,,,,,,,,,4,In-Person")
    assert [tutor.name for tutor in load_tutor_sheet(path, settings)[0]] == ["Kaylee Sc", "Kaylee Sm"]


@pytest.mark.parametrize("row, message", [
    (",Ann Lee,Science,8,,,2,2,,,,,,,,,4,In-Person", "unknown subject"),
    (",Ann Lee,Maths,,,,2,2,,,,,,,,,4,In-Person", "no year levels"),
    (",Ann Lee,Maths,8,,,2,2,,,,,,,,,,In-Person", "maximum number of classes"),
])
def test_invalid_tutor_rows(settings, write_tutors, row, message):
    with pytest.raises(LoaderError, match=message):
        load_tutor_sheet(write_tutors(row), settings)


def test_tutor_sheet_needs_rooms(settings, write_tutors):
    with pytest.raises(LoaderError, match="rooms"):
        load_tutor_sheet(write_tutors(KAYLEE, footer=""), settings)


def test_tutor_sheet_needs_every_student_day(settings, write_tutors):
    header = TUTOR_HEADER.replace("Saturday,,", "")
    with pytest.raises(LoaderError, match="Saturday"):
        load_tutor_sheet(write_tutors(footer=TUTOR_FOOTER, header=header), settings)


def test_tutor_sheet_needs_headings(settings, write_tutors):
    with pytest.raises(LoaderError, match="headings"):
        load_tutor_sheet(write_tutors(KAYLEE, header=',"\nTutor Availability,\n'), settings)


# --- the real Google Sheet export ---------------------------------------------

def test_real_template_is_a_valid_tutor_file():
    assert verify_files(str(TEST1 / "student.csv"), str(TEMPLATE / "tutor.csv")) == ""


def test_real_template_with_no_tutors(settings):
    with pytest.raises(LoaderError, match="no tutors"):
        load_tutor_sheet(str(TEMPLATE / "tutor.csv"), settings)


def test_real_template_with_tutors(settings, tmp_path):
    # fill in the first two blank rows under the headings, like a tutor would
    lines = (TEMPLATE / "tutor.csv").read_text().splitlines()
    heading_index = next(index for index, line in enumerate(lines) if "Name,Subject" in line)
    lines[heading_index + 2] = KAYLEE
    lines[heading_index + 3] = ",Ann Lee,English,7/8,,,1,,,,,,,,,,3,Both"
    path = tmp_path / "tutor.csv"
    path.write_text("\r\n".join(lines), newline="")

    tutors, rooms = load_tutor_sheet(str(path), settings)

    assert rooms == ["201", "205", "206", "207", "208"]
    assert [(tutor.name, tutor.subject, tutor.year_levels, tutor.maximum, tutor.location) for tutor in tutors] == [
        ("Kaylee S", "Maths", ["8"], 5, "Online"),
        ("Ann L", "English", ["7", "8"], 3, "Both"),
    ]
    assert tutors[1].availability_at(Session("Tuesday", EARLY)) == Availability.POTENTIAL
