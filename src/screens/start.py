import os
from typing import Callable

from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QResizeEvent
from PyQt6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout,
                             QWidget)

from src.config import Settings
from src.loader import LoaderError, load_students, load_tutor_sheet, verify_student_file, verify_tutor_file
from src.screens.theme import set_style_property

CHOOSE_BOTH = "Choose both files to continue"
FIX_FILE = "Check the file marked in red"
READY = "Ready to create the timetable"


class StartScreen(QWidget):
    """ The first screen. The user chooses the student and tutor CSV files, then creates the timetable """

    settings: Settings
    folder: str                 # where the file dialog opens, the folder of the last file chosen

    student_card: "FileCard"
    tutor_card: "FileCard"
    create_button: QPushButton
    message: QLabel

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.folder = ""

        self.setWindowTitle("Timetable Creator")
        self.setMinimumWidth(500)
        self.resize(580, 0)

        title = make_label("Timetable Creator", role="title")
        subtitle = make_label("Choose the two availability files, then create the timetable.", role="muted")

        self.student_card = FileCard(1, "Student availability", "The Google Form responses (.csv)",
                                     self.check_students)
        self.tutor_card = FileCard(2, "Tutor availability", "The tutor availability sheet (.csv)",
                                   self.check_tutors)
        for card in (self.student_card, self.tutor_card):
            card.button.clicked.connect(lambda _, card=card: self.browse(card))
            card.changed.connect(lambda card=card: self.file_changed(card))

        self.message = make_label(CHOOSE_BOTH, role="muted")
        self.message.setWordWrap(True)

        self.create_button = QPushButton("Create Timetable")
        self.create_button.setProperty("primary", True)
        self.create_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_button.setEnabled(False)

        footer = QHBoxLayout()
        footer.addWidget(self.message, stretch=1)
        footer.addWidget(self.create_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self.student_card)
        layout.addWidget(self.tutor_card)
        layout.addSpacing(8)
        layout.addLayout(footer)
        layout.addStretch()

    def get_files(self) -> tuple[str, str]:
        """ Returns the student CSV and tutor CSV paths ("" if not chosen yet) """
        return self.student_card.path, self.tutor_card.path

    def show_error(self, text: str) -> None:
        """ Show a problem found after Create Timetable was clicked """
        self.message.setText(text)
        set_style_property(self.message, "role", "")
        set_style_property(self.message, "state", "error")

    def browse(self, card: "FileCard") -> None:
        path, _ = QFileDialog.getOpenFileName(self, f"Choose the {card.title.lower()} CSV", self.folder,
                                              "CSV Files (*.csv)")
        if path:            # "" when the dialog was cancelled
            card.set_file(path)

    def file_changed(self, card: "FileCard") -> None:
        self.folder = os.path.dirname(card.path)

        cards = (self.student_card, self.tutor_card)
        self.create_button.setEnabled(all(card.ok for card in cards))
        if any(card.error for card in cards):
            self.message.setText(FIX_FILE)
        elif all(card.ok for card in cards):
            self.message.setText(READY)
        else:
            self.message.setText(CHOOSE_BOTH)
        set_style_property(self.message, "role", "muted")
        set_style_property(self.message, "state", "")

    # --- checking the files ---------------------------------------------------

    def check_students(self, path: str) -> str:
        error = verify_student_file(path)
        if error:
            raise LoaderError(error)
        return plural(len(load_students(path, self.settings)), "student")

    def check_tutors(self, path: str) -> str:
        error = verify_tutor_file(path)
        if error:
            raise LoaderError(error)
        tutors, rooms = load_tutor_sheet(path, self.settings)
        return f"{plural(len(tutors), 'tutor')} · {plural(len(rooms), 'room')}"


class FileCard(QFrame):
    """ One file to choose. Shows whether it has been chosen, which file it is and whether it looks right.
        A CSV can also be dragged onto the card """

    changed = pyqtSignal()

    number: int
    title: str
    description: str
    check: Callable[[str], str]     # returns a summary of the file, or raises LoaderError

    path: str                       # "" until a file is chosen
    summary: str
    error: str

    def __init__(self, number: int, title: str, description: str, check: Callable[[str], str]) -> None:
        super().__init__()
        self.number = number
        self.title = title
        self.description = description
        self.check = check
        self.path = ""
        self.summary = ""
        self.error = ""

        self.setObjectName("fileCard")
        self.setAcceptDrops(True)

        self.badge = QLabel()
        self.badge.setObjectName("badge")
        self.badge.setFixedSize(28, 28)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.file_label = ElidedLabel()
        self.status = make_label("")
        self.status.setWordWrap(True)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(make_label(title, role="heading"))
        text.addWidget(self.file_label)
        text.addWidget(self.status)

        self.button = QPushButton()
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.setMinimumWidth(110)      # the same width for "Choose file…" and "Change…"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)
        layout.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text, stretch=1)
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.refresh()

    @property
    def ok(self) -> bool:
        return bool(self.path) and not self.error

    def set_file(self, path: str) -> None:
        self.path = path
        try:
            self.summary, self.error = self.check(path), ""
        except LoaderError as error:
            self.summary, self.error = "", str(error)
        self.refresh()
        self.changed.emit()

    def refresh(self) -> None:
        if not self.path:
            state, badge, status = "", str(self.number), "No file chosen"
            self.file_label.set_full_text(self.description)
        else:
            state, badge, status = ("error", "!", self.error) if self.error else ("ok", "✓", self.summary)
            self.file_label.set_full_text(os.path.basename(self.path))

        # the folder is only in the tooltip, full paths are usually too long to show
        self.file_label.setToolTip(self.path)
        set_style_property(self.file_label, "role", "" if self.path else "muted")
        self.button.setText("Change…" if self.path else "Choose file…")

        self.badge.setText(badge)
        self.status.setText(status)
        set_style_property(self.status, "role", "" if self.path else "muted")
        for widget in (self, self.badge, self.status):
            set_style_property(widget, "state", state)
        self.file_label.elide()     # the restyle can change the font

    # --- drag and drop --------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if dropped_csv(event.mimeData()):
            event.acceptProposedAction()
            set_style_property(self, "dropping", True)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        set_style_property(self, "dropping", False)

    def dropEvent(self, event: QDropEvent) -> None:
        set_style_property(self, "dropping", False)
        path = dropped_csv(event.mimeData())
        if path:
            event.acceptProposedAction()
            self.set_file(path)


class ElidedLabel(QLabel):
    """ A one line label that shortens long text with "…" instead of stretching the window """

    full_text: str

    def __init__(self) -> None:
        super().__init__()
        self.full_text = ""
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def set_full_text(self, text: str) -> None:
        self.full_text = text
        self.elide()

    def elide(self) -> None:
        # cut from the middle so the end of a file name (".csv") stays visible
        self.setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideMiddle, self.width()))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.elide()


def dropped_csv(mime: QMimeData) -> str:
    """ The path of the CSV file being dragged in, or "" if it isn't a single CSV file """
    urls = mime.urls()
    if len(urls) == 1 and urls[0].isLocalFile() and urls[0].toLocalFile().lower().endswith(".csv"):
        return urls[0].toLocalFile()
    return ""


def make_label(text: str, role: str = "") -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setProperty("role", role)
    return label


def plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"
