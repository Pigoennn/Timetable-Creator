from configparser import ConfigParser
from dataclasses import dataclass

SUBJECTS = ("Maths", "English")


@dataclass(frozen=True)
class Settings:
    """ Everything read from settings.txt. Passed around instead of using globals """

    student_days: tuple[str, ...]           # days students can have classes
    tutor_days: tuple[str, ...]             # days on the tutor availability sheet, in column order
    weekend_days: tuple[str, ...]

    dampening: float
    class_size: int

    class_times: dict[str, dict[str, str]]  # class_times["Weekday" | "Weekend"]["maths_early"] = "5:00 - 6:30 pm"

    def class_time(self, day: str, subject: str, time: str) -> str:
        """ The printed time of a class, e.g. class_time("Saturday", "Maths", "Early") -> "11:30 - 1:00 pm" """
        day_type = "Weekend" if day in self.weekend_days else "Weekday"
        return self.class_times[day_type][f"{subject.lower()}_{time.lower()}"]


def load_settings(settings_file: str) -> Settings:
    """ Read the settings file. Raises ValueError if it is missing anything or inconsistent """
    config = ConfigParser()
    if not config.read(settings_file):
        raise ValueError(f"Could not read settings file {settings_file}")

    try:
        settings = Settings(
            student_days=_split_list(config["Days"]["studentdays"]),
            tutor_days=_split_list(config["Days"]["tutordays"]),
            weekend_days=_split_list(config["Days"]["weekenddays"]),
            dampening=config["Configs"].getfloat("dampening"),
            class_size=config["Configs"].getint("classsize"),
            class_times={
                "Weekday": dict(config["Weekday Times"]),
                "Weekend": dict(config["Weekend Times"]),
            },
        )
    except KeyError as missing:
        raise ValueError(f"Settings file is missing {missing}") from None

    # every student day needs a column on the tutor sheet
    missing_days = [day for day in settings.student_days if day not in settings.tutor_days]
    if missing_days:
        raise ValueError(f"Student days {missing_days} are not in the tutor days")

    return settings


def _split_list(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())
