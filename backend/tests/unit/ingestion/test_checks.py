# Checks each check across the sources fires on one planted inconsistency, and only on it: each case
# holds a row that agrees beside the one that doesn't
import pytest

from sage.ingestion import checks
from sage.ingestion.complementary import Offering
from sage.ingestion.curricula import Listed, Subtotal
from sage.ingestion.handbook import Entry
from sage.ingestion.timetable import Printed
from sage.shared.rules import AnyOf, Course, CourseNeed, Equivalence


def entry(code, credits=16, nqf_level=7, term=None, name="Energy Systems and Grids I"):
    return Entry(
        codes=(code,),
        name=name,
        credits=credits,
        nqf_level=nqf_level,
        term=term,
        convener=None,
        requirement=None,
        corequisite=None,
        page=138,
        content="",
    )


def listed(code, credits=16, nqf_level=7):
    return Listed(
        curriculum="EB022EEE02",
        year=2,
        code=code,
        credits=credits,
        nqf_level=nqf_level,
        page=53,
    )


def meeting(code, semester="sem1"):
    return Printed(
        sheet="Labs",
        cells="D27:D30",
        codes=(code,),
        year=None,
        semester=semester,
        day=2,
        first="6",
        last="9",
    )


def course(code, *named):
    leaves = tuple(CourseNeed(course=c, need="pass") for c in named)
    return Course(
        handbook_year=2026,
        code=code,
        name="A course",
        credits=16,
        nqf_level=7,
        term="sem1",
        entry_rule=AnyOf(any=leaves) if leaves else None,
    )


def offering(code, credits):
    return Offering(
        sheet="Courses",
        row=12,
        code=code,
        name="ENERGY SYSTEMS AND GRIDS I",
        faculty="Commerce",
        credits=credits,
        nqf_level=7,
        outline="",
        requirement="Not stated in course entry.",
        term="sem2",
        class_times="",
        assessment="",
        convener="",
        details="None",
        handbook="A handbook",
        pages="160",
    )


@pytest.mark.parametrize(
    ("check", "failure"),
    [
        (
            # A Labs cell for a course no curriculum lists, beside one settled as excluded
            lambda: checks.known_codes(
                [meeting("EEE3090F"), meeting("EEE2041F"), meeting("EEE3099S")],
                {"EEE3090F"},
                {"EEE2041F"},
            ),
            ("Labs!D27:D30", "EEE3099S isn't in the rulebook", None),
        ),
        (
            lambda: checks.entries(
                [listed("EEE3100S"), listed("ASL1200S")],
                {"EEE3100S": entry("EEE3100S")},
            ),
            (
                "p. 53",
                "EB022EEE02 lists ASL1200S, which has no entry",
                ("curriculum_rules", "EB022EEE02/2"),
            ),
        ),
        (
            # The boundary: credits agree but the NQF level doesn't
            lambda: checks.credits(
                [listed("EEE3100S"), listed("EEE3091F", nqf_level=6)],
                {"EEE3100S": entry("EEE3100S"), "EEE3091F": entry("EEE3091F")},
            ),
            (
                "p. 53 and p. 138",
                "EB022EEE02 lists EEE3091F at 16 credits and NQF level 6, its entry 16 and 7",
                ("courses", "EEE3091F"),
            ),
        ),
        (
            lambda: checks.terms(
                {
                    "PHY1012F": entry("PHY1012F", term="sem1"),
                    "PHY1013S": entry("PHY1013S", term="sem1"),
                },
                [],
            ),
            ("p. 138", "PHY1013S's entry prints sem1", ("courses", "PHY1013S")),
        ),
        (
            # A quarter fits its semester's columns; a second-semester course doesn't fit the first's
            lambda: checks.terms(
                {}, [meeting("EEE4125C", "sem2"), meeting("EEE2044S")]
            ),
            ("Labs!D27:D30", "EEE2044S is printed in sem1", None),
        ),
        (
            # Loaded, printed and equivalent codes are known; CSC1010H is none of them
            lambda: checks.tree_codes(
                [
                    course("EEE2045F"),
                    course("CSC2001F", "EEE2045F", "MAM1021F", "EEE1006F", "CSC1010H"),
                ],
                {"CSC2001F": "p. 169"},
                {"MAM1021F"},
                [
                    Equivalence(
                        handbook_year=2026, course_code="EEE1006F", counts_as="EEE1008F"
                    )
                ],
            ),
            (
                "p. 169",
                "CSC2001F's rule names CSC1010H, which isn't loaded, printed or equivalent",
                ("courses", "CSC2001F"),
            ),
        ),
        (
            lambda: checks.round_trip(["EB009 lacks a meeting a stored meeting gives"]),
            ("timetable", "EB009 lacks a meeting a stored meeting gives", None),
        ),
        (
            # 2026's EB022 year 2, whose ten rows add up to 144 while page 53 prints 136
            lambda: checks.totals(
                [
                    Subtotal(
                        curriculum="EB009EEE01",
                        year=2,
                        page=48,
                        printed=144,
                        summed=144,
                    ),
                    Subtotal(
                        curriculum="EB022EEE02",
                        year=2,
                        page=53,
                        printed=136,
                        summed=144,
                    ),
                ]
            ),
            (
                "p. 53",
                "EB022EEE02 year 2's core table prints 136 credits, but its rows add up to 144",
                ("curriculum_rules", "EB022EEE02/2"),
            ),
        ),
        (
            lambda: checks.overlaps(
                [offering("EEE3100S", 16), offering("EEE3093S", 18)],
                {"EEE3100S": entry("EEE3100S"), "EEE3093S": entry("EEE3093S")},
            ),
            (
                "Courses row 12 and p. 138",
                "EEE3093S is typed with credits 18, printed 16",
                ("courses", "EEE3093S"),
            ),
        ),
    ],
)
def test_each_check_fires_on_one_planted_inconsistency(check, failure):
    place, what, flags = failure
    assert check().failures == (checks.Failure(place=place, what=what, flags=flags),)


def test_a_settled_exclusion_is_reported_not_failed():
    # EEE2041F's Labs cells were left out at C1's Stop 1, so they never stop a year's approval
    check = checks.known_codes([meeting("EEE2041F")], set(), {"EEE2041F"})
    assert check.failures == ()
    assert check.reported == (
        checks.Failure(place="Labs!D27:D30", what="EEE2041F isn't in the rulebook"),
    )
