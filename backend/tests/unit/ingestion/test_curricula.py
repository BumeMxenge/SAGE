# Checks the curriculum reader on tables printed in the 2023 and 2026 handbooks: each year's tables
# become groups, members and one rule, a line no rule can hold becomes a note for a person, and each
# core table's total is kept to check. Expected values are read off the page by hand.
import pytest

from sage.ingestion.curricula import Listed, Subtotal, read
from sage.ingestion.handbook import Handbook, Page
from sage.ingestion.sources import Section, SourceError
from sage.shared.rules import (
    AllOfGroup,
    ChooseFromGroup,
    CreditsFromGroups,
    CurriculumRule,
    TotalCredits,
    YearRules,
)

DEPARTMENT = "Electrical Engineering"


def rule(curriculum, year, *parts):
    return CurriculumRule(
        handbook_year=2026,
        curriculum_code=curriculum,
        year_of_study=year,
        rule=YearRules(all=parts),
    )


def members_of(curricula):
    found = {}
    for member in curricula.members:
        found.setdefault(member.group_key, []).append(member.course_code)
    return found


def test_a_curriculum_reads_as_printed(handbook):
    # EB009EEE01's second to fourth years (2026, pages 48 and 49)
    curricula = read(
        handbook, Section(section=DEPARTMENT, pages=(48, 49)), 2026, DEPARTMENT
    )
    assert [(c.code, c.name, c.department) for c in curricula.curricula] == [
        (
            "EB009EEE01",
            "Bachelor of Science in Engineering in Electrical Engineering 4-year curriculum",
            DEPARTMENT,
        )
    ]
    assert curricula.rules == (
        rule(
            "EB009EEE01",
            2,
            AllOfGroup(all_of_group="EB009EEE01-y2-core"),
            TotalCredits(total_credits=144),
        ),
        rule(
            "EB009EEE01",
            3,
            AllOfGroup(all_of_group="EB009EEE01-y3-core"),
            CreditsFromGroups(credits=18, from_groups=("complementary",)),
            TotalCredits(total_credits=146),
        ),
        rule(
            "EB009EEE01",
            4,
            AllOfGroup(all_of_group="EB009EEE01-y4-core"),
            ChooseFromGroup(choose=1, from_group="EB009EEE01-y4-group-1"),
            CreditsFromGroups(
                credits=48,
                from_groups=("EB009EEE01-y4-group-1", "EB009EEE01-y4-group-2"),
            ),
            TotalCredits(total_credits=138),
        ),
    )
    assert {group.group_key: group.label for group in curricula.groups} == {
        "EB009EEE01-y2-core": "Second Year Core Courses (EE)",
        "EB009EEE01-y3-core": "Third Year Core Courses (EE)",
        "EB009EEE01-y4-core": "Fourth Year Core Courses (EE)",
        "EB009EEE01-y4-group-1": "Fourth Year Elective Core Courses (EE)",
        "EB009EEE01-y4-group-2": (
            "And further courses from (timetable and pre-requisite permitting)"
        ),
        "complementary": "Approved complementary studies courses",
    }
    assert members_of(curricula) == {
        "EB009EEE01-y2-core": [
            "EEE2045F",
            "EEE2046F",
            "MAM2083F",
            "MEC1003F",
            "MEC1009F",
            "EEE2044S",
            "EEE2047S",
            "EEE2048S",
            "MAM2084S",
            "PHY2010S",
        ],
        "EB009EEE01-y3-core": [
            "EEE3088F",
            "EEE3089F",
            "EEE3090F",
            "EEE3091F",
            "EEE3092F",
            "EEE3093S",
            "EEE3094S",
            "EEE3098S",
            "EEE3100S",
            "EEE3000X",
        ],
        "EB009EEE01-y4-core": [
            "EEE4113F",
            "CML4607F",
            "EEE4125C",
            "EEE4124C",
            "EEE4022S",
        ],
        "EB009EEE01-y4-group-1": ["EEE4126F", "EEE4118F", "EEE4121F"],
        "EB009EEE01-y4-group-2": ["EEE4114F", "EEE4117F", "HUB4049F"],
    }
    # Each reading names its table as handbook_deltas allows it
    assert {r.entity for r in curricula.readings} == {
        "curricula",
        "curriculum_rules",
        "course_groups",
        "course_group_members",
    }
    # Only the footnote about the 576-credit curriculum needs a person, on year 2's rule, whose
    # table runs onto the footnote's page: the complementary list and the timetable warning hold no
    # rule
    assert [(r.key, r.place, r.printed) for r in curricula.readings if r.flag] == [
        (
            "EB009EEE01/2",
            "pp. 48-49",
            (
                "*CON2026S is a core course in the 576 cr. curriculum and students should "
                "register for an approved Complementary Studies course of at least 8 credits "
                "(timetable permitting) to meet the core requirements if CON2026S is outstanding."
            ),
        )
    ]
    # Year 2: 7 × 16 + 2 × 8 = 128 + 16 = 144. Year 3: 7 × 16 + 2 × 8 + 18 for the slot + 0 = 146.
    # Year 4's core: 16 + 10 + 16 + 8 + 40 = 90.
    assert curricula.subtotals == (
        Subtotal(curriculum="EB009EEE01", year=2, page=48, printed=144, summed=144),
        Subtotal(curriculum="EB009EEE01", year=3, page=49, printed=146, summed=146),
        Subtotal(curriculum="EB009EEE01", year=4, page=49, printed=90, summed=90),
    )
    assert (
        Listed(
            curriculum="EB009EEE01",
            year=3,
            code="EEE3000X",
            credits=0,
            nqf_level=7,
            page=49,
        )
        in curricula.listed
    )
    # The footnote's CON2026S is in scope with every course a row prints
    assert curricula.scope == {"CON2026S"} | {
        code for codes in members_of(curricula).values() for code in codes
    }
    # The introduction and each table are units in printed order, and a table's notes stay with it,
    # even over a page break
    assert [(unit.section, unit.page) for unit in curricula.units] == [
        (
            "Bachelor of Science in Engineering in Electrical Engineering 4-year curriculum",
            48,
        ),
        ("Second Year Core Courses (EE)", 48),
        ("Third Year Core Courses (EE)", 49),
        ("Fourth Year Core Courses (EE)", 49),
        ("Fourth Year Elective Core Courses (EE)", 49),
    ]
    assert {unit.curriculum_code for unit in curricula.units} == {"EB009EEE01"}
    assert curricula.units[1].content.startswith("Second Year Core Courses (EE)")
    assert curricula.units[1].content.endswith(
        "requirements if CON2026S is outstanding."
    )


def test_an_elective_table_reads_its_instructions_wildcard_and_range():
    # Electrical and Computer Engineering's third and fourth years (2026, pages 53 and 54), 2023's
    # optional courses for Mechatronics (page 56) and two CSC 3rd-year entries (2026, page 171),
    # set on one page
    lines = (
        "Electrical Engineering",
        "",
        "Bachelor of Science in Engineering in Electrical and Computer Engineering 4-year",
        "curriculum",
        "BSc(Engineering)(Electrical and Computer Engineering)[EB022EEE02]",
        "",
        "Third Year Elective Core Courses (EC)",
        (
            "Select two out of the following three courses. Your choices will have an impact on "
            "which 4th year"
        ),
        "electives can be taken the following year.",
        "Code Course NQF Credits NQF Level",
        "CSC2002S Computer Science 2002 ................................... 24 6",
        "EEE3093S Communication & Network Engineering ..................... 16 7",
        "EEE3094S Control Systems Engineering ............................. 16 7",
        "Total credits per year (minimum) ........................................ 154-162",
        "",
        "Fourth Year Elective Core Courses (EC)",
        "Select courses amounting to at least 48 credits from the following:",
        "At least two courses from:",
        "Code Course NQF Credits NQF Level",
        "EEE4114F Digital Signal Processing ............................... 16 8",
        "EEE4118F Process Control & Instrumentation ....................... 16 8",
        "And further courses from (timetable and pre-requisite permitting):",
        "Code Course NQF Credits NQF Level",
        "CSC3xxx Approved 3rd year Computer Science course ................ 36 7",
        "HUB4049F Introduction to Medical Imaging & Image Processing ....... 16 8",
        "Total credits per year (minimum) ............................... 138",
        "",
        "Optional Courses",
        (
            "The following courses may be of interest, timetable and pre-requisite permitting, and "
            "require"
        ),
        "approval:",
        "Code Course NQF Credits NQF Level",
        "EEE2051L Practical Electronics, Components, Modules & Design ..... 8 6",
        "HUB2005F Introduction to Medical Engineering ..................... 8 6",
        "",
        "CSC3002F NETWORKS AND OPERATING SYSTEMS",
        "36 NQF credits at NQF level 7",
        "CSC3003S ADVANCED PROGRAMMING & ALGORITHMS",
        "36 NQF credits at NQF level 7",
    )
    book = Handbook([Page(number=53, lines=lines)])
    curricula = read(
        book, Section(section=DEPARTMENT, pages=(53, 53)), 2026, DEPARTMENT
    )
    # A name printed over two lines
    assert curricula.curricula[0].name == (
        "Bachelor of Science in Engineering in Electrical and Computer Engineering 4-year "
        "curriculum"
    )
    assert curricula.rules == (
        # "Select two out of three", and the range's minimum
        rule(
            "EB022EEE02",
            3,
            ChooseFromGroup(choose=2, from_group="EB022EEE02-y3-group-1"),
            TotalCredits(total_credits=154),
        ),
        rule(
            "EB022EEE02",
            4,
            ChooseFromGroup(choose=2, from_group="EB022EEE02-y4-group-1"),
            CreditsFromGroups(
                credits=48,
                from_groups=("EB022EEE02-y4-group-1", "EB022EEE02-y4-group-2"),
            ),
            TotalCredits(total_credits=138),
        ),
    )
    # CSC3xxx stands for every 3rd-year CSC entry in the book
    assert curricula.expanded == {"CSC3xxx": ("CSC3002F", "CSC3003S")}
    assert members_of(curricula)["EB022EEE02-y4-group-2"] == [
        "CSC3002F",
        "CSC3003S",
        "HUB4049F",
    ]
    # The optional courses are in scope, but no group holds them, as no rule picks them
    assert {"EEE2051L", "HUB2005F"} <= curricula.scope
    assert not {"EEE2051L", "HUB2005F"} & {m.course_code for m in curricula.members}


ELECTIVES = (
    "Electrical Engineering",
    "",
    "Bachelor of Science in Engineering in Electrical and Computer Engineering 4-year",
    "BSc(Engineering)(Electrical and Computer Engineering)[EB022EEE02]",
    "",
    "Fourth Year Elective Core Courses (EC)",
    "Code Course NQF Credits NQF Level",
)


@pytest.mark.parametrize(
    ("rows", "refusal"),
    [
        # A wildcard that stands for no entry in the book
        (
            ("CSC3xxx Approved 3rd year Computer Science course ...... 36 7",),
            "No entry's code starts with CSC3",
        ),
        # Electives with no instruction to pick them
        (
            ("EEE4114F Digital Signal Processing ...... 16 8",),
            "EB022EEE02 year 4's electives have no rule to pick them",
        ),
    ],
)
def test_a_table_the_reader_cannot_read_is_refused(rows, refusal):
    book = Handbook([Page(number=54, lines=ELECTIVES + rows)])
    with pytest.raises(SourceError, match=refusal):
        read(book, Section(section=DEPARTMENT, pages=(54, 54)), 2026, DEPARTMENT)
