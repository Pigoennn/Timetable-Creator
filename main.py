import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic as PyUI
from math import floor
from random import randint

from src.screens.start import StartScreen
# from src.screens.loading 

class Main:

    self.start_window: StartScreen
    

    def __init__(self):
        pass


    def setup_start_screen(self, start_window: StartScreen) -> None:
        self.start_window = start_window
        self.start_window.CreateTimetableButton.clicked.connect(lambda: setup_data())
    

    def setup_data(self) -> None:
        if not(verify):
            return


    def verify(self) -> bool:
        """ Parent function to check if the files are up to standard """
        error = start_window.verify_file()
        if error:
            start_window.set_info_label(error)
        
        return not(bool(error))         # false if there is an error, true otherwise


if __name__ == "__main__":
    main = Main()
    main.setup_start_screen(StartScreen("src/ui_files/start_screen.ui"))
