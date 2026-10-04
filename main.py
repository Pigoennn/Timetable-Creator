import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic as PyUI
from math import floor
from random import randint

from src.screens.start import StartScreen
# from src.screens.loading 

from src.classes.solution import Solution

class Main:

    self.solution: Solution
    self.start_window: StartScreen


    def __init__(self, solution: Solution):
        self.solution = solution


    def setup_start_screen(self, start_window: StartScreen) -> None:
        self.start_window = start_window
        self.start_window.CreateTimetableButton.clicked.connect(lambda: self.execute())


    def execute(self):
        self.setup_data()
        self.solution.execute()

    

    def setup_data(self) -> None:
        if not(verify()):
            return
        
        student_csv, tutor_csv = self.start_window.get_files()
        self.solution.setup(student_csv, tutor_csv)

        
    def verify(self) -> bool:
        """ Parent function to check if the files are up to standard """
        error = start_window.verify_file()
        if error:
            start_window.set_info_label(error)
        
        return not(bool(error))         # false if there is an error, true otherwise


if __name__ == "__main__":
    main = Main(Solution())
    main.setup_start_screen(StartScreen("src/ui_files/start_screen.ui"))
