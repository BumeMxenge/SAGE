# Checks a year ingests end to end from small sources built here: the handbook's own entries win over
# the workbook's copies, requirements are translated grammar first, a check's failure flags the row
# it names, ingesting writes nothing and asks no model, drafting takes earlier years' drafts,
# wording the previous approved year printed keeps the rule it approved, a review sitting saves each
# decision as it's made, approving waits for every row and writes a snapshot that reads back and
# loads, and a year already loaded is only replaced when asked
import hashlib
import json
from datetime import UTC, datetime, time, timedelta

import openpyxl
import pytest

from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.domain.rules import (
    AllOf,
    AnyOf,
    Course,
    CourseNeed,
    HandbookVersion,
    Refer,
    RuleSet,
)
from sage.ingestion.review import Snapshot
from sage.ingestion.sources import Reading
from sage.services.ingest import (
    Sitting,
    YearLoaded,
    approve,
    approved_snapshot,
    ingest,
    load,
    review_file,
    review_year,
)

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


def sources(
    tmp_path,
    handbook_pdf,
    complementary_xlsx,
    timetable_block,
    pages=PAGES,
    change=None,
):
    folder = tmp_path / "sources" / "2026"
    folder.mkdir(parents=True)
    handbook_pdf(folder / "handbook.pdf", pages)
    complementary_xlsx(folder / "complementary.xlsx", WORKBOOK, change)
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
    courses = {
        c.code: (c.name, c.term, c.entry_rule, c.convener) for c in run.rules.courses
    }
    assert courses == {
        # The grammar reads EEE3100S's requirement
        "EEE3100S": (
            "Energy Systems and Grids I",
            "sem2",
            CourseNeed(course="PHY1013S", need="pass"),
            "Associate Professor D Oyedokun",
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
            "D R Geduld",
        ),
        # Read from the handbook, which prints its entry, rather than the workbook's copy
        "ECO1007S": ("Economics for Engineers", "sem2", None, "C Mlatsheni"),
        # Not stated in its entry, which doesn't mean there's no requirement
        "AGE1002S": (
            "The Human Planet: Prehistory to Present",
            "sem2",
            Refer(refer=NOT_STATED),
            "Dr V J Hare",
        ),
        "SLL1017F": (
            "Swahili Communication 1A",
            "sem1",
            Refer(refer=BEGINNERS),
            "Dr E Mahenge",
        ),
    }
    # What a reviewer reads for a course and where to find it: its printed requirement with any
    # co-requisite, or the workbook's words
    readings = {
        r.key: (r.place, r.printed) for r in run.readings if r.entity == "courses"
    }
    assert readings["PHY1013S"] == (
        "p. 188",
        "EEE1006F Co-requisites: MAM1020F (or equivalent)",
    )
    assert readings["ECO1007S"] == ("p. 138", "No requirement printed")
    assert readings["SLL1017F"] == (
        f"{HUMANITIES}, p. 244 (Language options row 3)",
        BEGINNERS,
    )
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
    # Rows per table and source, counted from the sources above: one curriculum printing years 1
    # and 3, their core groups and the complementary group, PHY1013S and EEE3100S in the core
    # groups, and all three workbook offerings in the complementary group. PHY1013S meets on the
    # sheet of the one curriculum taking it, so its meeting needs no link.
    assert run.rows == {
        "curricula": {"handbook": 1},
        "curriculum_rules": {"handbook": 2},
        "courses": {"handbook": 3, "complementary workbook": 2},
        "course_groups": {"handbook": 3},
        "course_group_members": {"handbook": 2, "complementary workbook": 3},
        "equivalences": {"equivalences": 1},
        "timetable_slots": {"timetable": 1, "complementary workbook": 2},
        "timetable_slot_curricula": {"timetable": 0},
        "passages": {"handbook": 6, "complementary workbook": 2},
    }
    # The candidate rulebook holds exactly the rows the report counts
    assert run.rules.handbook_versions == (HandbookVersion(year=2026),)
    assert {table: len(getattr(run.rules, table)) for table in run.rows} == {
        table: sum(counts.values()) for table, counts in run.rows.items()
    }
    # The handbook's passages in printed order, then the workbook's own, less ECO1007S's, each
    # entry's linked to its course
    assert [
        (p.source, p.position, p.section, p.course_code) for p in run.rules.passages
    ] == [
        (
            EBE,
            1,
            "Bachelor of Science in Engineering in Electrical Engineering 4-year curriculum",
            None,
        ),
        (EBE, 2, "First Year Core Courses (EE)", None),
        (EBE, 3, "Third Year Core Courses (EE)", None),
        (EBE, 4, "EEE3100S Energy Systems and Grids I", "EEE3100S"),
        (EBE, 5, "ECO1007S Economics for Engineers", "ECO1007S"),
        (EBE, 6, "PHY1013S Physics B for Engineers", "PHY1013S"),
        (SCIENCE, 1, "AGE1002S The Human Planet: Prehistory to Present", "AGE1002S"),
        (HUMANITIES, 1, "SLL1017F Swahili Communication 1A", "SLL1017F"),
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


def approved(year, printed):
    # An approved year whose courses printed these words, each with the rule approved for them
    return Snapshot(
        rules=RuleSet(
            handbook_versions=(HandbookVersion(year=year, approved=True),),
            courses=tuple(
                Course(
                    handbook_year=year,
                    code=code,
                    name="Made Up",
                    credits=8,
                    nqf_level=5,
                    term="sem1",
                    entry_rule=rule,
                )
                for code, (_, rule) in printed.items()
            ),
        ),
        readings=tuple(
            Reading(entity="courses", key=code, place="p. 1", printed=words)
            for code, (words, _) in printed.items()
        ),
    )


def test_wording_the_previous_approved_year_printed_keeps_its_rule(
    tmp_path, handbook_pdf, complementary_xlsx, timetable_block
):
    # PHY1013S printing only its co-requisite, and SLL1017F's requirement typed across two lines
    pages = [list(page) for page in PAGES]
    pages[2].remove("Course entry requirements: EEE1006F")
    typed = ("Language options", "G3", BEGINNERS.replace(" aimed", "\naimed"))
    sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block, pages, typed)
    co_requisite = "Co-requisites: MAM1020F (or equivalent)"
    alongside = AnyOf(
        any=(
            CourseNeed(course="MAM1020F", need="concurrent"),
            Refer(refer="or equivalent"),
        )
    )
    passed = AnyOf(
        any=(CourseNeed(course="MAM1020F", need="pass"), Refer(refer="or equivalent"))
    )
    beginners = Refer(refer="This is a beginners’ course.")
    # 2023 approved these words for other courses, other words for PHY1013S, and a requirement in
    # the co-requisite's words, which is another rule. 2020, and 2026 itself, aren't compared with.
    years = {
        2020: {"PHY1099S": (co_requisite, None)},
        2023: {
            "PHY1099S": (co_requisite, alongside),
            "PHY1098S": ("MAM1020F (or equivalent)", passed),
            "PHY1013S": ("EEE1006F", CourseNeed(course="EEE1006F", need="pass")),
            "SLL1099F": (BEGINNERS, beginners),
        },
        2026: {"PHY1099S": (co_requisite, None)},
    }
    for year, printed in years.items():
        path = tmp_path / "rules" / str(year) / "rulebook.json"
        path.parent.mkdir(parents=True)
        path.write_text(approved(year, printed).model_dump_json(), encoding="utf-8")
    run = ingest(2026, data=tmp_path)
    rules = {c.code: c.entry_rule for c in run.rules.courses}
    assert (rules["PHY1013S"], rules["SLL1017F"]) == (alongside, beginners)
    # Neither keeps the grammar's cause, as 2023 approved their words, but a carried rule is still
    # checked: no course here is MAM1020F
    flags = {r.key: r.flag for r in run.readings if r.entity == "courses"}
    assert (flags["PHY1013S"], flags["SLL1017F"]) == ("check_failed", None)
    assert run.carried == ("PHY1013S", "SLL1017F")


def test_a_sitting_saves_each_decision_and_a_rerun_keeps_them(
    tmp_path, handbook_pdf, complementary_xlsx, timetable_block
):
    sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block)
    candidate, _ = review_year(2026, data=tmp_path)
    # A sitting from 09:00 to 09:12, by a made-up clock
    start = datetime(2026, 10, 18, 9, tzinfo=UTC)
    times = iter([start, *[start + timedelta(minutes=12)] * 9])
    path = review_file(2026, tmp_path)
    sitting = Sitting(candidate, path, lambda: next(times))
    # The planted year-3 total fails a check, so accepting it needs a note, and without one the row
    # stays as it was
    problems = sitting.decide("rule/EB009EEE01/3", "accept")
    assert [problem.note for problem in problems] == [True]
    assert sitting.decide("rule/EB009EEE01/3", "accept", note="Made up") == ()
    assert sitting.decide("requirement/PHY1013S", "accept") == ()
    assert sitting.end() == [(12.0, 2)]
    _, review = review_year(2026, data=tmp_path)
    assert {
        row.id: (row.decision, row.note) for row in review.rows if row.decision
    } == {
        "rule/EB009EEE01/3": ("accept", "Made up"),
        "requirement/PHY1013S": ("accept", None),
    }
    assert json.loads(path.read_text(encoding="utf-8"))["sittings"] == [
        {
            "start": "2026-10-18T09:00:00+00:00",
            "end": "2026-10-18T09:12:00+00:00",
            "decided": 2,
        }
    ]


def accept_all(data, but=()):
    # Accepts each row of the made-up year's review but those named, with a note where a check fails
    candidate, review = review_year(2026, data=data)
    sitting = Sitting(
        candidate, review_file(2026, data), lambda: datetime(2026, 10, 18, tzinfo=UTC)
    )
    for row in review.rows:
        if row.id not in but:
            note = "Made up" if row.failures else None
            assert sitting.decide(row.id, "accept", note=note) == ()
    return candidate


def test_approve_refuses_while_one_row_is_pending(
    tmp_path, handbook_pdf, complementary_xlsx, timetable_block
):
    sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block)
    accept_all(tmp_path, but={"requirement/SLL1017F"})
    review, snapshot = approve(2026, data=tmp_path)
    assert (review.pending, snapshot) == (("requirement/SLL1017F",), None)
    assert not (tmp_path / "rules" / "2026" / "rulebook.json").exists()


def test_an_approved_year_survives_the_snapshot_round_trip(
    tmp_path, handbook_pdf, complementary_xlsx, timetable_block
):
    sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block)
    candidate = accept_all(tmp_path)
    _, snapshot = approve(2026, data=tmp_path)
    assert approved_snapshot(2026, tmp_path) == snapshot
    store = InMemoryRuleRepository()
    load(snapshot, store, replace=False)
    assert store.get(2026) == snapshot.rules
    # Every row accepted as read, now approved, with where each was printed
    rules = snapshot.rules
    assert rules.handbook_versions == (HandbookVersion(year=2026, approved=True),)
    assert (rules.courses, rules.passages) == (
        candidate.rules.courses,
        candidate.rules.passages,
    )
    assert snapshot.readings == candidate.readings
    # In a first year every row is a change: accepted automatically where nothing needed a
    # person, and accepted by one where something did
    flags = {
        (d.entity, d.entity_key): (d.flag, d.approved) for d in rules.handbook_deltas
    }
    assert flags[("courses", "EEE3100S")] == (None, True)
    assert flags[("courses", "PHY1013S")] == ("refused_or_equivalent", True)
    assert flags[("curriculum_rules", "EB009EEE01/3")] == ("check_failed", True)
    assert len(flags) == sum(
        len(getattr(rules, table))
        for table in (
            "curricula",
            "curriculum_rules",
            "courses",
            "course_groups",
            "course_group_members",
            "equivalences",
        )
    )


def test_a_kept_removal_keeps_its_row_and_where_it_was_printed(
    tmp_path, handbook_pdf, complementary_xlsx, timetable_block
):
    # 2023 approved a course the made-up 2026 no longer prints, and its removal is rejected
    sources(tmp_path, handbook_pdf, complementary_xlsx, timetable_block)
    path = tmp_path / "rules" / "2023" / "rulebook.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        approved(
            2023, {"EEE9001F": ("No requirement printed", None)}
        ).model_dump_json(),
        encoding="utf-8",
    )
    candidate = accept_all(tmp_path, but={"removal/EEE9001F"})
    sitting = Sitting(
        candidate,
        review_file(2026, tmp_path),
        lambda: datetime(2026, 10, 18, tzinfo=UTC),
    )
    assert sitting.decide("removal/EEE9001F", "reject") == ()
    _, snapshot = approve(2026, data=tmp_path)
    kept = next(c for c in snapshot.rules.courses if c.code == "EEE9001F")
    assert kept.handbook_year == 2026
    # The next year reads its words from here
    assert (
        Reading(
            entity="courses",
            key="EEE9001F",
            place="p. 1",
            printed="No requirement printed",
        )
        in snapshot.readings
    )


def test_a_loaded_year_is_replaced_only_when_asked():
    store = InMemoryRuleRepository()
    first = approved(2097, {"TST1001F": ("First words", None)})
    second = approved(2097, {"TST1002F": ("Second words", None)})
    load(first, store, replace=False)
    with pytest.raises(YearLoaded):
        load(second, store, replace=False)
    assert store.get(2097) == first.rules
    load(second, store, replace=True)
    assert store.get(2097) == second.rules
