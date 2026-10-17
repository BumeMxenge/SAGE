# Checks a year ingests end to end from small sources built here: the handbook's own entries win over
# the workbook's copies, requirements are translated grammar first, a check's failure flags the row
# it names, a dry run writes nothing and asks no model, and drafting takes earlier years' drafts
import hashlib
import json
from datetime import time

import openpyxl

from sage.domain.rules import AllOf, AnyOf, CourseNeed, Refer
from sage.services.ingest import ingest

EBE = "UCT Faculty of Engineering & the Built Environment Undergraduate Handbook 2026 (Book 7a)"
SCIENCE = "UCT Faculty of Science Handbook 2026 (Book 11)"
HUMANITIES = "UCT Faculty of Humanities Undergraduate Handbook 2026 (Book 9a)"
# Printed text from the 2026 handbook, arranged on three pages. Year 1 lists PHY1013S with a footnote
# naming CON2026S, whose entry these pages leave out, and year 3's total is planted wrong: its row
# and slot add up to 16 + 18 = 34, not 40. EEE3100S's requirement is made up, to name a loaded course.
PAGES = [
    [
        "PROGRAMMES OF STUDY 48",
        "Electrical Engineering",
        "",
        "Bachelor of Science in Engineering in Electrical Engineering 4-year curriculum",
        "BSc(Engineering)(Electrical Engineering)[EB009EEE01]",
        "",
        "First Year Core Courses (EE)",
        "",
        "Code Course NQF Credits NQF Level",
        "PHY1013S Physics B for Engineers ............................... 18 5",
        "Total credits per year ......................................... 18",
        "",
        "*CON2026S is a core course in the 576 cr. curriculum and students should register for an",
        "approved Complementary Studies course of at least 8 credits (timetable permitting).",
        "",
        "Third Year Core Courses (EE)",
        "",
        "Code Course NQF Credits NQF Level",
        "EEE3100S Energy Systems & Grids I .............................. 16 7",
        "*Approved Complementary Studies Elective F/S/P/L .................. 18",
        "Total credits per year (minimum) ............................... 40",
        "*See separate list of approved complementary studies courses",
    ],
    [
        "DEPARTMENTS IN THE FACULTY AND COURSES OFFERED 138",
        "EEE3100S ENERGY SYSTEMS AND GRIDS I",
        "16 NQF credits at NQF level 7",
        "Convener: Associate Professor D Oyedokun",
        "Course entry requirements: PHY1013S",
        "Course outline:",
        "This course aims to develop further skills and knowledge in power systems engineering.",
        "Assessment: Please refer to the official course handout document.",
        "",
        "ECO1007S ECONOMICS FOR ENGINEERS",
        "18 NQF credits at NQF level 5",
        "Convener: C Mlatsheni",
        "Course outline:",
        "ECO1007S is a one semester course that introduces students to economics.",
        "Assessment: Tests and assignments 50%; examination 50%.",
    ],
    [
        "DEPARTMENTS IN OTHER FACULTIES AND COURSES OFFERED 188",
        "PHY1013S PHYSICS B FOR ENGINEERS",
        "18 NQF credits at NQF level 5; First-year, second semester course.",
        "Convener: D R Geduld",
        "Course entry requirements: EEE1006F",
        "Co-requisites: MAM1020F (or equivalent)",
        "Course outline:",
        "The course is the second part of the first year engineering Physics sequence.",
        "Assessment: Class record counts 50%; one 2-hour examination counts 50%.",
    ],
]
NOT_STATED = "Not stated in course entry."
BEGINNERS = "None. This is a beginners’ course aimed at non-mother tongue speakers."
WORKBOOK = {
    "Courses": [
        (
            "AGE1002S",
            "THE HUMAN PLANET: PREHISTORY TO PRESENT",
            "Science",
            18,
            5,
            "Archaeology.",
        )
        + (
            NOT_STATED,
            "sem2",
            "Monday - Thursday, 5th period",
            "Tests",
            "Dr V J Hare",
            "None",
        )
        + (SCIENCE, 58),
        (
            "ECO1007S",
            "ECONOMICS FOR ENGINEERS",
            "Commerce",
            18,
            5,
            "Economics.",
            NOT_STATED,
        )
        + ("sem2", "2nd period", "Tests", "C Mlatsheni", "None", EBE, 160),
    ],
    "Language options": [
        (
            "SLL1017F",
            "SWAHILI COMMUNICATION 1A",
            "Humanities",
            15,
            5,
            "Swahili.",
            BEGINNERS,
        )
        + (
            "sem1",
            "7th Period.",
            "Coursework",
            "Dr E Mahenge",
            "None",
            HUMANITIES,
            244,
        ),
    ],
    "Meetings": [
        ("AGE1002S", "lecture", "mon", time(12), time(12, 45), None, None),
        ("SLL1017F", "lecture", None, time(15), time(15, 45), None, None),
    ],
}
MANIFEST = """
year = 2026
department = "Electrical Engineering"

[handbook]
file = "handbook.pdf"
format = "pdf"
title = "{ebe}"
url = "https://example.org/handbook.pdf"
sha256 = "{handbook}"

[[handbook.passages]]
section = "Electrical Engineering"
pages = [48, 48]

[timetable]
file = "timetable.xlsx"
format = "xlsx"
title = "A made-up timetable"
sha256 = "{timetable}"

[timetable.sheets]
EB009 = ["EB009EEE01"]
Labs = []

[complementary]
file = "complementary.xlsx"
format = "xlsx"
title = "A made-up workbook"
sha256 = "{complementary}"
courses = "Courses"
languages = "Language options"
meetings = "Meetings"

[equivalences]
file = "equivalences.csv"
format = "csv"
title = "Made-up equivalences"
sha256 = "{equivalences}"
"""


def sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block):
    folder = tmp_path / "sources" / "2026"
    folder.mkdir(parents=True)
    handbook_pdf(folder / "handbook.pdf", PAGES)
    complementary_xlsx(folder / "complementary.xlsx", WORKBOOK)
    # PHY1013S on Monday at 08:00 in its year's block, and a lab for EEE2041F, which no curriculum
    # here lists
    book = openpyxl.Workbook()
    book.active.title = "EB009"
    timetable_block(book["EB009"], "1ST YEAR")
    book["EB009"]["K5"] = "PHY1013S (2377)"
    timetable_block(book.create_sheet("Labs"), "SASOL LAB")
    book["Labs"]["D11"] = "EEE2041F"
    book.save(folder / "timetable.xlsx")
    (folder / "equivalences.csv").write_text(
        "code,counts_as,reason,page\nEEE1006F,EEE1008F,A replaced code.,2026: 48\n",
        encoding="utf-8",
    )
    fingerprints = {
        name: hashlib.sha256((folder / file).read_bytes()).hexdigest()
        for name, file in (
            ("handbook", "handbook.pdf"),
            ("timetable", "timetable.xlsx"),
            ("complementary", "complementary.xlsx"),
            ("equivalences", "equivalences.csv"),
        )
    }
    (folder / "manifest.toml").write_text(
        MANIFEST.format(ebe=EBE, **fingerprints), encoding="utf-8"
    )


def test_a_year_ingests_into_a_candidate_rulebook(
    tmp_path, handbook_pdf, complementary_xlsx, timetable_block
):
    sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block)
    run = ingest(2026, data=tmp_path)
    courses = {c.code: (c.name, c.term, c.entry_rule) for c in run.rules.courses}
    assert courses == {
        # The grammar reads EEE3100S's requirement
        "EEE3100S": (
            "Energy Systems and Grids I",
            "sem2",
            CourseNeed(course="PHY1013S", need="pass"),
        ),
        # The grammar refuses the co-requisite, which stands as a refer leaf until it's drafted
        "PHY1013S": (
            "Physics B for Engineers",
            "sem2",
            AllOf(
                all=(
                    CourseNeed(course="EEE1006F", need="pass"),
                    Refer(refer="MAM1020F (or equivalent)"),
                )
            ),
        ),
        # Read from the handbook, which prints its entry, rather than the workbook's copy
        "ECO1007S": ("Economics for Engineers", "sem2", None),
        # Not stated in its entry, which doesn't mean there's no requirement
        "AGE1002S": (
            "The Human Planet: Prehistory to Present",
            "sem2",
            Refer(refer=NOT_STATED),
        ),
        "SLL1017F": ("Swahili Communication 1A", "sem1", Refer(refer=BEGINNERS)),
    }
    flags = {(r.entity, r.key): r.flag for r in run.readings if r.flag}
    assert flags == {
        ("courses", "PHY1013S"): "refused_or_equivalent",
        ("courses", "SLL1017F"): "refused_free_text",
        ("curriculum_rules", "EB009EEE01/1"): "refused_free_text",
        ("curriculum_rules", "EB009EEE01/3"): "check_failed",
        ("equivalences", "EEE1006F/EEE1008F"): "not_printed",
    }
    assert {c.name: len(c.failures) for c in run.checks if c.failures} == {
        "Printed totals add up": 1,
        "Every timetable code is a course the rulebook holds": 1,
    }
    assert run.left_out == ("CON2026S",)
    assert run.unprinted == ("ECO1007S",)
    assert run.rows["courses"] == {"handbook": 3, "complementary workbook": 2}
    assert run.rows["timetable_slots"] == {"timetable": 1, "complementary workbook": 2}
    # The handbook's passages in printed order, then the workbook's own, less ECO1007S's
    assert [(p.source, p.position, p.section) for p in run.rules.passages] == [
        (
            EBE,
            1,
            "Bachelor of Science in Engineering in Electrical Engineering 4-year curriculum",
        ),
        (EBE, 2, "First Year Core Courses (EE)"),
        (EBE, 3, "Third Year Core Courses (EE)"),
        (EBE, 4, "EEE3100S Energy Systems and Grids I"),
        (EBE, 5, "ECO1007S Economics for Engineers"),
        (EBE, 6, "PHY1013S Physics B for Engineers"),
        (SCIENCE, 1, "AGE1002S The Human Planet: Prehistory to Present"),
        (HUMANITIES, 1, "SLL1017F Swahili Communication 1A"),
    ]
    # Nothing is written and no model is asked
    assert run.translations.calls == 0
    assert not (tmp_path / "rules").exists()


class Drafter:
    # Stands in for the model, and keeps what it's asked
    model = "a made-up model"

    def __init__(self):
        self.asked = []

    def draft(self, printed, need):
        self.asked.append(printed)
        return {"refer": printed}


def test_a_year_takes_the_drafts_of_the_years_before_it(
    tmp_path, handbook_pdf, complementary_xlsx, timetable_block
):
    sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block)
    # PHY1013S's co-requisite as 2023 drafted it, in E2's prompt's tree for that wording, and as a
    # later year drafted it differently
    co_requisite = "MAM1020F (or equivalent)"
    for year, tree in (
        (
            2023,
            {
                "any": [
                    {"course": "MAM1020F", "need": "concurrent"},
                    {"refer": "or equivalent"},
                ]
            },
        ),
        (2027, {"refer": co_requisite}),
    ):
        cache = tmp_path / "rules" / str(year) / "drafts.json"
        cache.parent.mkdir(parents=True)
        drafts = {"concurrent": {co_requisite: {"model": "made up", "tree": tree}}}
        cache.write_text(json.dumps(drafts), encoding="utf-8")
    drafter = Drafter()
    run = ingest(2026, drafter, data=tmp_path)
    # Only the wording no earlier year drafted is asked for
    assert drafter.asked == [BEGINNERS]
    rules = {c.code: c.entry_rule for c in run.rules.courses}
    assert rules["PHY1013S"] == AllOf(
        all=(
            CourseNeed(course="EEE1006F", need="pass"),
            AnyOf(
                any=(
                    CourseNeed(course="MAM1020F", need="concurrent"),
                    Refer(refer="or equivalent"),
                )
            ),
        )
    )
