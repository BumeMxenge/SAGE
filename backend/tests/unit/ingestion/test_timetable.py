# Checks the timetable reader on a small workbook built here in the 2026 workbook's layout: merged
# blocks become meetings by the handbook's period key, parallel sections are one meeting, a meeting
# on two sheets is stored once with the right links, and the sheets rebuild from what's stored
from datetime import time

import openpyxl
import pytest

from sage.ingestion.sources import Alternatives, SourceError
from sage.ingestion.timetable import read, round_trip, stored

# The handbook's key (p. 10): each period's label and starting hour, on rows 5 to 14 of a block
KEY = (
    ("1", 8),
    ("2", 9),
    ("3", 10),
    ("4", 11),
    ("5", 12),
    ("M", 13),
    ("6", 14),
    ("7", 15),
    ("8", 16),
    ("9", 17),
)
SHEETS = {"EB009": ("EB009EEE01",), "EB809": ("EB809EEE01",), "Labs": ()}
TAKING = {
    "EEE2045F": {"EB009EEE01", "EB809EEE01"},
    "MEC1009F": {"EB009EEE01"},
    "HUB4049F": {"EB009EEE01"},
    "EEE3090F": {"EB009EEE01"},
}
YEARS = {
    ("EB009EEE01", "EEE2045F"): 2,
    ("EB809EEE01", "EEE2045F"): 2,
    ("EB009EEE01", "MEC1009F"): 2,
    ("EB009EEE01", "HUB4049F"): 2,
    ("EB009EEE01", "EEE3090F"): 3,
}
KNOWN = set(TAKING) | {"EEE3096S", "EEE3097S", "EEE3098S"}
LAB = Alternatives(
    course="EEE3096S", group="lab", cells=("Labs!O11:O14", "Labs!M11:M14")
)


def block(sheet, title):
    # A block at the top of a sheet, laid out as the workbook's are: its title across the grid, each
    # semester's heading and days, and the period key down each semester's side
    sheet["A1"] = title
    sheet.merge_cells("A1:O1")
    for column, semester in ((1, "Semester 1"), (9, "Semester 2")):
        sheet.cell(2, column, f"Mainstream EE - {semester}")
        sheet.cell(3, column, semester)
        for offset, day in enumerate(
            ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
        ):
            sheet.cell(3, column + 2 + offset, day)
        sheet.cell(4, column, "Start Time")
        sheet.cell(4, column + 1, "Period")
        for row, (period, hour) in enumerate(KEY, start=5):
            sheet.cell(row, column, time(hour))
            sheet.cell(row, column + 1, period if period == "M" else int(period))


def meeting(sheet, cells, text):
    sheet[cells.split(":")[0]] = text
    if ":" in cells:
        sheet.merge_cells(cells)


@pytest.fixture
def workbook(tmp_path):
    book = openpyxl.Workbook()
    eb009 = book.active
    eb009.title = "EB009"
    block(eb009, "2ND YEAR")
    meeting(eb009, "C7:C8", "EEE2045F\n(5068)")  # Monday, periods 3 and 4
    meeting(eb009, "D7:D8", "EEE2045F\n(5323)")  # Tuesday, on this sheet alone
    meeting(eb009, "C10", "HUB4049F (13546)")  # Monday, the meridian
    meeting(
        eb009, "C11:C14", "MEC1009F\n(5234, 5287 or 5797)"
    )  # Monday, periods 6 to 9
    eb009["K16"] = "Note: Students also take EEE4124C, but this is purely online (5552)"
    eb809 = book.create_sheet("EB809")
    block(eb809, "2ND YEAR")
    meeting(eb809, "C7:C8", "EEE2045F\n(5068)")
    labs = book.create_sheet("Labs")
    block(labs, "WHITE LAB")
    meeting(labs, "O7:O8", "EEE3097/8S")  # Friday in semester 2, periods 3 and 4
    meeting(labs, "G11:G14", "EEE3090F")  # Friday, with no section
    meeting(labs, "M11:M14", "EEE3096S")  # Wednesday's lab, the alternative to Friday's
    meeting(labs, "O11:O14", "EEE3096S")
    # A hidden sheet the manifest doesn't list, which is never read
    hidden = book.create_sheet("Temporary")
    hidden["A1"] = "A rough plan for next year"
    hidden.sheet_state = "hidden"
    path = tmp_path / "timetable.xlsx"
    book.save(path)
    return read(path, SHEETS)


def test_the_sheets_read_as_meetings_by_the_period_key(workbook):
    timetable = stored(workbook, SHEETS, TAKING, (LAB,), 2026, KNOWN)
    slots = {
        (
            s.course_code,
            s.term,
            s.day,
            s.start_time,
            s.end_time,
            s.kind,
            s.choice_group,
            s.choice,
        ): s
        for s in timetable.slots
    }
    # Times from the handbook's key: period 3 is 10:00 to 10:45 and period 4 ends at 11:45,
    # periods 6 to 9 run 14:00 to 17:45, and the meridian 13:00 to 14:00
    assert set(slots) == {
        ("EEE2045F", "sem1", 1, time(10), time(11, 45), None, None, None),
        ("EEE2045F", "sem1", 2, time(10), time(11, 45), None, None, None),
        ("HUB4049F", "sem1", 1, time(13), time(14), None, None, None),
        ("MEC1009F", "sem1", 1, time(14), time(17, 45), None, None, None),
        ("EEE3097S", "sem2", 5, time(10), time(11, 45), "lab", None, None),
        ("EEE3098S", "sem2", 5, time(10), time(11, 45), "lab", None, None),
        ("EEE3090F", "sem1", 5, time(14), time(17, 45), "lab", None, None),
        ("EEE3096S", "sem2", 5, time(14), time(17, 45), "lab", "lab", "A"),
        ("EEE3096S", "sem2", 3, time(14), time(17, 45), "lab", "lab", "B"),
    }
    # Monday's EEE2045F is on both curricula's sheets, so it needs no link; Tuesday's only on one
    tuesday = slots["EEE2045F", "sem1", 2, time(10), time(11, 45), None, None, None]
    assert [(link.slot_id, link.curriculum_code) for link in timetable.links] == [
        (tuesday.id, "EB009EEE01")
    ]
    assert [(note.sheet, note.cell) for note in workbook.notes] == [("EB009", "K16")]
    # The sheets rebuild from what's stored, and a lost link shows on the sheet it should have kept
    # the meeting off
    assert round_trip(workbook, timetable, SHEETS, YEARS, KNOWN) == ()
    unlinked = timetable.model_copy(update={"links": ()})
    assert round_trip(workbook, unlinked, SHEETS, YEARS, KNOWN) == (
        "EB809 lacks (2, 'sem1', 2, '3', '4', 'EEE2045F'), which a stored meeting gives",
    )


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        # A cell that isn't a meeting, on a period row
        (lambda book: book["EB009"].cell(9, 5, "TBC"), "EB009!E9 isn't a meeting"),
        # A value outside every column the layout uses
        (
            lambda book: book["EB009"].cell(20, 20, "staff only"),
            "EB009!T20 fits no reading",
        ),
        # A listed sheet that's hidden
        (
            lambda book: setattr(book["Labs"], "sheet_state", "hidden"),
            "The Labs sheet is hidden",
        ),
    ],
)
def test_a_cell_the_reader_cannot_place_stops_it(tmp_path, change, refusal):
    book = openpyxl.Workbook()
    book.active.title = "EB009"
    block(book["EB009"], "2ND YEAR")
    block(book.create_sheet("Labs"), "WHITE LAB")
    change(book)
    path = tmp_path / "timetable.xlsx"
    book.save(path)
    with pytest.raises(SourceError, match=refusal):
        read(path, {"EB009": ("EB009EEE01",), "Labs": ()})
