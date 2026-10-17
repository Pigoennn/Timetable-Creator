from src.classes.student import Student
from src.loader import make_names_unique


def make_students(*full_names: str) -> list[Student]:
    students = []
    for full_name in full_names:
        first_name, _, last_name = full_name.partition(" ")
        students.append(Student("", first_name, last_name, "8", "In-Person", []))
    return students


def names(students: list[Student]) -> list[str]:
    return [student.name for student in students]


def test_unique_names_are_unchanged():
    students = make_students("John Smith", "Jane Smith", "John Doe")
    make_names_unique(students)
    assert names(students) == ["John S", "Jane S", "John D"]


def test_names_lengthen_until_they_differ():
    students = make_students("John Smith", "John Smythe", "John Doe")
    make_names_unique(students)
    assert names(students) == ["John Smi", "John Smy", "John D"]


def test_last_name_that_is_a_prefix_of_another():
    students = make_students("John Smith", "John Smithson")
    make_names_unique(students)
    assert names(students) == ["John Smith", "John Smiths"]


def test_identical_names_are_numbered():
    students = make_students("John Smith", "John Smith", "John Smythe")
    make_names_unique(students)
    assert names(students) == ["John Smith (1)", "John Smith (2)", "John Smy"]


def test_missing_last_names():
    students = make_students("Cher", "Cher", "Cher Lloyd")
    make_names_unique(students)
    assert len(set(names(students))) == 3
    assert names(students)[2] == "Cher L"


def test_multi_word_last_names_have_no_trailing_space():
    students = make_students("Mary Anne Smith", "Mary Anne Jones")
    make_names_unique(students)
    assert names(students) == ["Mary Anne S", "Mary Anne J"]
