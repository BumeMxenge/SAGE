# Checks the complementary workbook reader on a small workbook built here from rows of the real one,
# with shortened text: offerings become members, meetings and passages, and a row that breaks one of
# the rules the workbook was typed to is refused with its number
from datetime import time

import pytest

from sage.ingestion.complementary import (
    members,
    passages,
    read,
    slots,
)
from sage.ingestion.sources import ComplementaryFile, SourceError

SOURCE = ComplementaryFile(
    file="complementary.xlsx",
    format="xlsx",
    title="A made-up workbook",
    sha256="",
    courses="Courses",
    languages="Language options",
    meetings="Meetings",
)
SCIENCE = "UCT Faculty of Science Handbook 2026 (Book 11)"
HUMANITIES = "UCT Faculty of Humanities Undergraduate Handbook 2026 (Book 9a)"
EBE = "UCT Faculty of Engineering & the Built Environment Undergraduate Handbook 2026 (Book 7a)"
ROWS = {
    "Courses": [
        (
            "AGE1002S",
            "THE HUMAN PLANET: PREHISTORY TO PRESENT",
            "Science",
            18,
            5,
            "This aim of this course is to introduce the study of archaeology.",
            "None",
            "sem2",
            "Monday - Thursday, 5th period",
            "Assignments and class tests count 50% towards the final mark",
            "Dr V J Hare",
            "None",
            SCIENCE,
            58,
        ),
        (
            "ECO1007S",
            "ECONOMICS FOR ENGINEERS",
            "Commerce",
            18,
            5,
            "ECO1007S is a one semester course that introduces students to economics.",
            "None",
            "sem2",
            "Tuesday or Wednesday, 2nd period",
            "Tests and assignments 50%; examination 50%",
            "C Mlatsheni",
            "None",
            EBE,
            "160–161",
        ),
    ],
    "Language options": [
        (
            "SLL1017F",
            "SWAHILI COMMUNICATION 1A",
            "Humanities",
            15,
            5,
            "This course will provide students with a broad overview of the language.",
            "None. This is a beginners’ course aimed at non-mother tongue speakers.",
            "sem1",
            "7th Period.",
            "Coursework 50%; exam 50%.",
            "Dr E Mahenge",
            "None",
            HUMANITIES,
            "244–245",
        )
    ],
    "Meetings": [
        ("AGE1002S", "lecture", "mon,tue,wed,thu", time(12), time(12, 45), None, None),
        # Made-up alternatives, as rows 4 and 5
        ("ECO1007S", "lecture", "tue", time(9), time(9, 45), "lecture", "A"),
        ("ECO1007S", "lecture", "wed", time(9), time(9, 45), "lecture", "B"),
        # A period with no day printed
        ("SLL1017F", "lecture", None, time(15), time(15, 45), None, None),
    ],
}


def test_offerings_become_members_meetings_and_passages(tmp_path, complementary_xlsx):
    path = complementary_xlsx(tmp_path / "complementary.xlsx", ROWS)
    workbook_read = read(path, SOURCE)
    group, readings = members(workbook_read, 2026)
    assert [(m.course_code, m.category) for m in group] == [
        ("AGE1002S", None),
        ("ECO1007S", None),
        ("SLL1017F", "languages"),
    ]
    assert [(r.entity, r.key, r.place) for r in readings] == [
        ("course_group_members", "complementary/AGE1002S", "Courses row 3"),
        ("course_group_members", "complementary/ECO1007S", "Courses row 4"),
        ("course_group_members", "complementary/SLL1017F", "Language options row 3"),
    ]
    stored = slots(workbook_read, 2026)
    assert {
        (
            s.course_code,
            s.term,
            s.day,
            s.start_time,
            s.end_time,
            s.choice_group,
            s.choice,
        )
        for s in stored
    } == {
        ("AGE1002S", "sem2", 1, time(12), time(12, 45), None, None),
        ("AGE1002S", "sem2", 2, time(12), time(12, 45), None, None),
        ("AGE1002S", "sem2", 3, time(12), time(12, 45), None, None),
        ("AGE1002S", "sem2", 4, time(12), time(12, 45), None, None),
        ("ECO1007S", "sem2", 2, time(9), time(9, 45), "lecture", "A"),
        ("ECO1007S", "sem2", 3, time(9), time(9, 45), "lecture", "B"),
        ("SLL1017F", "sem1", None, time(15), time(15, 45), None, None),
    }
    # ECO1007S is read from the faculty handbook itself, so the workbook gives it no passage
    read_passages = passages(workbook_read, 2026, {"ECO1007S"})
    assert [
        (p.course_code, p.source, p.section, p.page, p.position) for p in read_passages
    ] == [
        (
            "AGE1002S",
            SCIENCE,
            "AGE1002S The Human Planet: Prehistory to Present",
            58,
            1,
        ),
        ("SLL1017F", HUMANITIES, "SLL1017F Swahili Communication 1A", 244, 1),
    ]
    assert len({p.id for p in read_passages}) == len(read_passages)
    assert read_passages[0].content.splitlines() == [
        "Course outline: This aim of this course is to introduce the study of archaeology.",
        "Entry requirements: None",
        "Class times: Monday - Thursday, 5th period",
        "Assessment: Assignments and class tests count 50% towards the final mark",
        "Other details: None",
    ]


def test_identical_meeting_rows_stay_two_meetings(tmp_path, complementary_xlsx):
    # REL1017S's "plus two tutorials" (2026) is typed as two identical rows, as neither prints a
    # day or time, and both are stored
    tutorial = ("SLL1017F", "tutorial", None, None, None, None, None)
    rows = ROWS | {"Meetings": [*ROWS["Meetings"], tutorial, tutorial]}
    path = complementary_xlsx(tmp_path / "complementary.xlsx", rows)
    stored = slots(read(path, SOURCE), 2026)
    assert len({slot.id for slot in stored if slot.kind == "tutorial"}) == 2


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        (("Courses", "O2", "Extra"), "Courses's columns aren't the workbook's"),
        (("Courses", "O3", "stray"), "Courses row 3 has a value past its columns"),
        (("Courses", "A3", "AGE1002"), "Courses row 3: code"),
        (("Courses", "A4", "AGE1002S"), "Courses row 4: AGE1002S is listed twice"),
        (("Courses", "D3", -1), "Courses row 3: credits"),
        (("Courses", "D3", 0), None),
        (("Courses", "E3", 4), "Courses row 3: nqf_level"),
        (("Courses", "E3", 10), None),
        (("Courses", "E3", 11), "Courses row 3: nqf_level"),
        (("Courses", "H3", "semester 2"), "Courses row 3: term"),
        (("Courses", "H3", "sem1"), "term sem1 doesn't agree with AGE1002S's suffix"),
        (("Courses", "N3", "153, 247"), None),
        (("Courses", "N3", "p. 58"), "Courses row 3: pages"),
        (("Meetings", "A3", "AGE1003S"), "Meetings row 3: AGE1003S isn't listed"),
        (("Meetings", "B3", "seminar"), "Meetings row 3: kind"),
        (("Meetings", "C3", "monday"), "Meetings row 3: days"),
        (("Meetings", "E3", None), "both a start and an end, or neither"),
        (("Meetings", "E3", time(12)), "ends after it starts"),
        (("Meetings", "E3", time(12, 1)), None),
        (("Meetings", "G4", None), "both a choice group and a choice, or neither"),
        (("Meetings", "G5", "A"), "ECO1007S's choice group lecture has one choice"),
    ],
)
def test_a_row_that_breaks_a_rule_is_refused_with_its_number(
    tmp_path, complementary_xlsx, change, refusal
):
    path = complementary_xlsx(tmp_path / "complementary.xlsx", ROWS, change)
    if refusal is None:
        read(path, SOURCE)
    else:
        with pytest.raises(SourceError, match=refusal):
            read(path, SOURCE)
