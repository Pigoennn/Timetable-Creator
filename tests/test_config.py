import pytest

from src.config import load_settings
from src.resources import resource_path


def test_settings_file(settings):
    assert settings.student_days == ("Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
    assert settings.tutor_days[0] == "Monday"
    assert settings.dampening == 0.75
    assert settings.class_size == 5


def test_class_times(settings):
    assert settings.class_time("Tuesday", "Maths", "Early") == "5:00 - 6:30 pm"
    assert settings.class_time("Friday", "English", "Late") == "7:00 - 9:00 pm"
    assert settings.class_time("Saturday", "Maths", "Early") == "11:30 - 1:00 pm"


def write_settings(tmp_path, text: str) -> str:
    original = open(resource_path("settings.txt")).read()
    path = tmp_path / "settings.txt"
    path.write_text(text(original) if callable(text) else text)
    return str(path)


def test_missing_settings_file(tmp_path):
    with pytest.raises(ValueError, match="Could not read"):
        load_settings(str(tmp_path / "nope.txt"))


def test_missing_section(tmp_path):
    path = write_settings(tmp_path, lambda text: text.replace("[Weekend Times]", "[Something Else]"))
    with pytest.raises(ValueError, match="Weekend Times"):
        load_settings(path)


def test_student_days_must_be_tutor_days(tmp_path):
    path = write_settings(tmp_path, lambda text: text.replace("Friday,Saturday\n", "Friday,Sunday\n", 1))
    with pytest.raises(ValueError, match="Sunday"):
        load_settings(path)
