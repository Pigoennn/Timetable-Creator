from typing import NamedTuple

EARLY = "Early"
LATE = "Late"
TIMES = (EARLY, LATE)


class Session(NamedTuple):
    """ One teaching slot, e.g. Session("Tuesday", "Early"). Replaces the old "ETuesday" strings """

    day: str
    time: str       # EARLY or LATE

    def other_half(self) -> "Session":
        """ The other session on the same day (Early <-> Late) """
        return Session(self.day, LATE if self.time == EARLY else EARLY)

    def __str__(self) -> str:
        return f"{self.time} {self.day}"
