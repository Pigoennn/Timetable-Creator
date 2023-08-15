import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

'''app = QApplication(sys.argv)
dWindow = PyUI.loadUi("displayscren.ui")
dWindow.setWindowTitle("Timetable")'''

class FinalWindow(QWidget): # Class for the final window
    maindictionary = {} # Dictionary of class indexes/pointers
    classList = [] # List of classroom objects
    studentList = [] # List of student objects
    tutorList = [] # List of tutor objects
    earlylatetimes = {} # Class timings

    def __init__(self, numberofdays, maxnumberofclasses):
        super().__init__() # Super initiation

        self.setWindowTitle("Timetable") # Set the title
        self.daylist = numberofdays # List of all possible days to be displayed
        self.createTable(numberofdays, maxnumberofclasses) # Create a table
        self.createInfoLabel() # Create an information label
        self.createPushButton() # Create a push button
        self.resize(920,480) # Resize the button

        self.show() # SHOW THYSELF

        self.grid = QGridLayout() # Grid Layout
        # Add all the items to the grid
        self.grid.addWidget(self.table,0,0)
        self.grid.addWidget(self.button,1,0,alignment=Qt.AlignmentFlag.AlignRight)
        self.grid.addWidget(self.info,0,1)
        self.grid.setColumnStretch(0,1)
        self.grid.setColumnMinimumWidth(1,100)
         # Find way to put button on the right

        self.setLayout(self.grid)

        # Run a function when a cell is selected
        self.table.selectionModel().selectionChanged.connect(self.onSelection)
    
    def onSelection(self, selected): # Used to change info label when cell is clicked
        # Run a try just in case a header was clicked or the cell has "None" attached to it
        try:
            cell = selected.indexes()[0]
            cell = [cell.row(),cell.column()]
            classname = self.table.item(cell[0],cell[1]).text()
            for classroom in FinalWindow.classList:
                if classroom.name == classname:
                    return self.setInfoLabel(classroom)
            return self.clearinfolabel()
        except IndexError: # If header clicked
            pass
        except AttributeError: # If empty cell
            self.clearinfolabel()

    def clearinfolabel(self): # Clear the info Label
        self.info.setText("")

    def setInfoLabel(self, focusclass: object): 
        infoList = []
        time = FinalWindow.earlylatetimes["Weekday" if focusclass.day in ["Monday","Tuesday","Wednesday","Thursday","Friday"] else "Weekend"][focusclass.subject][focusclass.time]
        time = time.split(" - ")
        infoList.append(f'<h3>{focusclass.day}</h3>') # Day
        infoList.append(f'<h4>{time[0]}</h4>')  # Time Start
        infoList.append(f'<h5>-</h5>')
        infoList.append(f'<h4>{time[1]}</h4>') # Time End
        infoList.append('<h4>ㅤ</h4>')
        infoList.append(f'<h4>SEL{focusclass.yearlevel}</h4>') # Year Level
        infoList.append(f'<h4>{focusclass.subject}</h4>') # Subject
        infoList.append(f'<h4>{FinalWindow.tutorList[focusclass.students[0]].name}</h4>') # Tutor
        infoList.append("ㅤ")
        # Students
        for student in focusclass.students[1:]:
            infoList.append(f'<h5>{FinalWindow.studentList[student].name}</h5>')
        information = '\n'.join(infoList)
        self.info.setText(information) # Change the info label

    def createInfoLabel(self): # Create the info label
        self.info = QLabel("")
        self.info.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.info.setFont(QFont("Nunito Sans"))

    def createPushButton(self): # Create the push button
        self.button = QPushButton("Download as CSV")
        self.button.setFixedSize(130,30)
        self.button.setToolTip("Download the timetable into a csv")
        # Style sheet
        self.button.setStyleSheet('''
        QPushButton {
            color: black;
            background-color: #87E2E8;
            border-style: outset;
            border-radius: 10px;
            min-width: 8em;
            padding: 6px;
        }
        QPushButton:hover {
            background-color: #9bf6fc;
        }
        QPushButton:pressed {
            background-color: #73ced4;
            border-style: inset;
        }
        QToolTip {
            padding: 2px;
            border-width: 1px;
            border-radius: 5px;
        }
        ''')

    def createTable(self, numberofdays: list, maxnumberofclasses: list): # Create the table that will be displayed
        # Create a table
        self.table = QTableWidget(len(numberofdays) * 2, len(maxnumberofclasses)) # Set the number of rows and columns based on the number of classes and max number of rooms
        self.table.setShowGrid(True) # Show grid lines
        for i in range(self.table.rowCount()):
            self.table.setRowHeight(i,40) # Change size of each row
        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i,100) # Change size of each column
        self.table.setEditTriggers(QAbstractItemView.EditTrigger(0)) # Turn off editing
        templist = list(maxnumberofclasses) # Represents the columns
        for i in templist:
            if "Online" in i:
                templist[templist.index(i)] = "Online"
        self.table.setHorizontalHeaderLabels(templist) # Title header for the columns
        daylist = list(numberofdays)
        for i in daylist: # Add a blank item after each non-blank item
            if i != "":
                daylist.insert(daylist.index(i) + 1,"")
        # For the day printing later
        self.table.setVerticalHeaderLabels(daylist) # Title header for the rows
        row = -1
        # Add the class that is in the respective room at the respective time 
        for day in FinalWindow.maindictionary.keys():
            if day in daylist:    
                for session in FinalWindow.maindictionary[day].keys():
                    # Set the row and column
                    row += 1
                    column = 0 
                    for room in FinalWindow.maindictionary[day][session].keys():
                        # Check if each class has more than two students meaning it is viable
                        if len(FinalWindow.classList[FinalWindow.maindictionary[day][session][room]].students) >= 2:
                            # Add the name of the class to the item in the row and column and set the alignment to middle 
                            self.table.setItem(row, column, QTableWidgetItem(FinalWindow.classList[FinalWindow.maindictionary[day][session][room]].name))
                            self.table.item(row, column).setTextAlignment(Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignHCenter)
                        else:
                            # If not, set it as empty cell
                            self.table.setItem(row, column, QTableWidgetItem(""))
                        column += 1 # Next column