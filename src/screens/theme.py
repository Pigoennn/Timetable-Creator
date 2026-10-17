""" The colours and stylesheet shared by every screen """
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QWidget

BACKGROUND = "#F4F5F7"
SURFACE = "#FFFFFF"
BORDER = "#D5D9E0"
TEXT = "#1F2328"
MUTED = "#6B7280"

ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
ACCENT_PRESSED = "#1E40AF"
ACCENT_SOFT = "#EFF4FF"

SUCCESS = "#15803D"
SUCCESS_BORDER = "#86CFA0"
ERROR = "#B91C1C"
ERROR_BORDER = "#F0A3A3"
ERROR_SOFT = "#FEF4F4"

STYLESHEET = f"""
QPushButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{ background-color: #F0F2F5; }}
QPushButton:pressed {{ background-color: #E4E7EC; }}
QPushButton:disabled {{ color: #A0A6B0; }}

QPushButton[primary="true"] {{
    background-color: {ACCENT};
    color: white;
    border: none;
    font-weight: bold;
    padding: 10px 22px;
}}
QPushButton[primary="true"]:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton[primary="true"]:pressed {{ background-color: {ACCENT_PRESSED}; }}
QPushButton[primary="true"]:disabled {{ background-color: #B7C6EC; color: white; }}

QLabel[role="title"] {{ font-size: 20pt; font-weight: bold; }}
QLabel[role="heading"] {{ font-weight: bold; }}
QLabel[role="muted"] {{ color: {MUTED}; }}
QLabel[state="ok"] {{ color: {SUCCESS}; }}
QLabel[state="error"] {{ color: {ERROR}; }}

QFrame#fileCard {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#fileCard[state="ok"] {{ border-color: {SUCCESS_BORDER}; }}
QFrame#fileCard[state="error"] {{ border-color: {ERROR_BORDER}; background-color: {ERROR_SOFT}; }}
QFrame#fileCard[dropping="true"] {{ border: 2px dashed {ACCENT}; background-color: {ACCENT_SOFT}; }}

QLabel#badge {{
    background-color: #E4E7EC;
    color: {MUTED};
    border-radius: 14px;
    font-weight: bold;
}}
QLabel#badge[state="ok"] {{ background-color: {SUCCESS}; color: white; }}
QLabel#badge[state="error"] {{ background-color: {ERROR}; color: white; }}

QProgressBar {{
    background-color: #E4E7EC;
    border: none;
    border-radius: 4px;
    max-height: 8px;
}}
QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 4px; }}

QToolTip {{
    background-color: {TEXT};
    color: white;
    border: none;
    padding: 4px;
}}
"""


def palette() -> QPalette:
    """ A light palette, so the app looks the same whatever the system theme is """
    colours = {
        QPalette.ColorRole.Window: BACKGROUND,
        QPalette.ColorRole.WindowText: TEXT,
        QPalette.ColorRole.Base: SURFACE,
        QPalette.ColorRole.AlternateBase: "#F7F8FA",
        QPalette.ColorRole.Text: TEXT,
        QPalette.ColorRole.Button: SURFACE,
        QPalette.ColorRole.ButtonText: TEXT,
        QPalette.ColorRole.Highlight: ACCENT,
        QPalette.ColorRole.HighlightedText: "#FFFFFF",
        QPalette.ColorRole.ToolTipBase: TEXT,
        QPalette.ColorRole.ToolTipText: "#FFFFFF",
        QPalette.ColorRole.PlaceholderText: MUTED,
    }
    result = QPalette()
    for role, colour in colours.items():
        result.setColor(role, QColor(colour))
    return result


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setPalette(palette())
    app.setStyleSheet(STYLESHEET)


def set_style_property(widget: QWidget, name: str, value: str | bool) -> None:
    """ Set a property the stylesheet looks at and restyle the widget, which Qt doesn't do by itself """
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
