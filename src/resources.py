import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(relative_path: str) -> str:
    """ Full path to a file shipped with the app. Works from source and from a PyInstaller build """
    base_path = getattr(sys, "_MEIPASS", PROJECT_ROOT)
    return os.path.join(base_path, relative_path)
