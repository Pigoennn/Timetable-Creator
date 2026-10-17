# Timetable Creator

A desktop app that turns a student availability form and a tutor availability sheet into a week of Maths and
English classes, then exports the timetable as a CSV laid out like the timetable Google Sheet.

## Running it

Developed and tested on Python 3.14.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

1. Choose the student CSV and the tutor CSV, then press **Create Timetable**.
2. A progress bar shows while the classes are made. Small centres take well under a second, around 1,000 students
   takes about 15 seconds.
3. The timetable has a row for each day and session and a column for each room, then the online classes.
   Click a class to see its tutor and students. Online students are marked "(OL)".
4. **Download as CSV** saves the timetable. **Save Errors.txt** saves the students who didn't get every class
   and why.

## Input files

**Student CSV**: the Google Form export. Columns are Timestamp, Email Address, First Name, Last Name, Year Level
("Year 8"), "In-Person" or "Online", then one column per student day containing `Early`, `Late`, `EarlyLate` or
blank.

**Tutor CSV**: the tutor availability Google Sheet downloaded as CSV (`testing/template/tutor.csv` is a blank
copy). Each tutor row has their name, subject (`Maths` or `English`), year levels in order of preference (`8/7`),
an early and a late column per day with `2` (available), `1` (potentially available) or blank, the maximum number
of classes and "In-Person", "Online" or "Both". The rooms go in the cell below `Rooms:`, separated by commas.

## Settings

`settings.txt` holds the days, the class times shown in the export, the class size and the dampening factor
(above 1 makes more classes than strictly needed, below 1 fewer).

## How classes are made

1. **Class creation**: works out how many classes each subject and year level needs and gives them to tutors at
   times when both tutors and students are free.
2. **Placement**: students are placed subject by subject with deferred acceptance, so each student ends up in the
   best class they can get given everyone else's choices.
3. **Filling gaps**: one-student classes are merged where possible and backup classes are made for anyone left
   over. Students that still can't be placed go in Errors.txt.
4. **Tidying up**: online classes with in-person tutors take any free rooms, online and in-person students are
   swapped into matching classes, tutors keep one room for the evening, and classes are named
   (`SEL MAT 8A`, `SEL ENG 7B`, ...) in timetable order.

## Project layout

```
main.py                 starts the app and connects the screens
settings.txt
src/
  config.py             reads settings.txt
  loader.py             checks and reads the CSV files
  export.py             writes the timetable CSV and Errors.txt
  classes/              the models and the scheduling (no Qt in here)
  screens/              start, loading and timetable screens
  ui_files/             Qt Designer files
tests/                  pytest suite
testing/                sample data and the random data generator
```

## Tests

```sh
.venv/bin/python -m pytest
```

The GUI tests run without opening any windows. `tests/test_export.py` checks that the export matches an old
export of the real sheet (`testing/template/timetable.csv`) cell for cell.

## Test data

`testing/test1` and `testing/test2` hold sample files. To make more:

```sh
.venv/bin/python testing/testing_creator.py 200 --out testing/test3 --seed 1
```

This writes a `student.csv` and a matching `tutor.csv`. The year level and attendance mix comes from
`testing/chance.txt`.
