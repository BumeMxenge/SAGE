# Checks a year is reviewed by exception against the previous approved year, on small rulebooks built
# here: the first year is all new, an unchanged row carries over, a removal is always flagged, one row
# covers every course printing the same words, a DP draft is marked and a failed check is always a
# reason to look
from sage.domain.rules import (
    AllOfGroup,
    AnyOf,
    Course,
    CourseGroupMember,
    CourseNeed,
    CurriculumRule,
    Equivalence,
    HandbookVersion,
    MinYearOfStudy,
    Refer,
    RuleSet,
    TotalCredits,
    YearRules,
)
from sage.ingestion.checks import Check, Failure
from sage.ingestion.review import Snapshot, compare
from sage.ingestion.sources import Reading

TREE_CODES = "Every code a rule names is loaded, printed or equivalent"


def course(code, rule=None, year=2026, convener="Dr A Made-Up"):
    return Course(
        handbook_year=year,
        code=code,
        name="Made Up",
        credits=8,
        nqf_level=5,
        term="sem1",
        entry_rule=rule,
        convener=convener,
    )


def member(group, code, year=2023):
    return CourseGroupMember(handbook_year=year, group_key=group, course_code=code)


def reading(table, key, printed, flag=None, place="p. 1"):
    return Reading(entity=table, key=key, place=place, printed=printed, flag=flag)


def approved_2023(**tables):
    return RuleSet(
        handbook_versions=(HandbookVersion(year=2023, approved=True),), **tables
    )


def test_the_first_year_is_all_new():
    # With no approved year before it, every row is added. One read with certainty is accepted
    # already, and a draft or an equivalence no handbook prints is for a person.
    rules = RuleSet(
        courses=(
            course("EEE1006F", year=2023),
            course("HUB4045F", MinYearOfStudy(min_year_of_study=4), year=2023),
        ),
        equivalences=(
            Equivalence(
                handbook_year=2023, course_code="MAM1020F", counts_as="MAM1023F"
            ),
        ),
    )
    readings = (
        reading("courses", "EEE1006F", "No requirement printed"),
        reading(
            "courses",
            "HUB4045F",
            "Students must be in their fourth year of study.",
            "refused_year_of_study",
            "p. 160",
        ),
        reading(
            "equivalences",
            "MAM1020F/MAM1023F",
            "A made-up reason.",
            "not_printed",
            "2023: 46",
        ),
    )
    review = compare(2023, rules, readings, ())
    assert [
        (row.id, row.causes, row.covers, row.old, row.new) for row in review.rows
    ] == [
        (
            "requirement/HUB4045F",
            ("refused_year_of_study",),
            {"courses/HUB4045F": "p. 160"},
            {},
            {"min_year_of_study": 4},
        ),
        (
            "equivalence/MAM1020F/MAM1023F",
            ("not_printed",),
            {"equivalences/MAM1020F/MAM1023F": "2023: 46"},
            {},
            {"course_code": "MAM1020F", "counts_as": "MAM1023F"},
        ),
    ]
    assert [(d.entity_key, d.old_value, d.flag, d.approved) for d in review.deltas] == [
        ("EEE1006F", None, None, True),
        ("HUB4045F", None, "refused_year_of_study", None),
        ("MAM1020F/MAM1023F", None, "not_printed", None),
    ]
    assert (review.compared_with, review.carried) == (None, 0)


def test_an_unchanged_row_carries_over():
    rule = YearRules(
        all=(
            AllOfGroup(all_of_group="EB009EEE01-y1-core"),
            TotalCredits(total_credits=132),
        )
    )

    def rules(year, convener):
        return RuleSet(
            handbook_versions=(HandbookVersion(year=year, approved=True),),
            courses=(
                course("EEE1006F", year=year),
                course(
                    "EEE3091F",
                    CourseNeed(course="EEE2045F", need="pass"),
                    year,
                    convener,
                ),
            ),
            curriculum_rules=(
                CurriculumRule(
                    handbook_year=year,
                    curriculum_code="EB009EEE01",
                    year_of_study=1,
                    rule=rule,
                ),
            ),
            equivalences=(
                Equivalence(
                    handbook_year=year, course_code="MAM1020F", counts_as="MAM1023F"
                ),
            ),
        )

    def readings(note):
        return (
            reading("courses", "EEE1006F", "No requirement printed"),
            reading("courses", "EEE3091F", "EEE2045F"),
            reading("curriculum_rules", "EB009EEE01/1", note, "refused_free_text"),
            reading("equivalences", "MAM1020F/MAM1023F", "A reason.", "not_printed"),
        )

    previous = Snapshot(
        rules=rules(2023, "Dr A Made-Up"), readings=readings("*A note.")
    )
    # 2026 holds the same rows, but EEE3091F has a new convener and the curriculum year a new note
    review = compare(
        2026,
        rules(2026, "Dr B Made-Up"),
        readings("*Another note."),
        (),
        previous=previous,
    )
    # The new note is for a person, beside the rule 2023 approved
    assert [(row.id, row.old) for row in review.rows] == [
        (
            "rule/EB009EEE01/1",
            {
                "curriculum_rules/EB009EEE01/1": {
                    "all": [
                        {"all_of_group": "EB009EEE01-y1-core"},
                        {"total_credits": 132},
                    ]
                }
            },
        )
    ]
    # The convener, read with certainty, is accepted automatically, and EEE1006F and the
    # equivalence carry over. The note changes no rule, so it isn't a change.
    assert [(d.entity_key, d.flag, d.approved) for d in review.deltas] == [
        ("EEE3091F", None, True)
    ]
    assert (review.compared_with, review.carried) == (2023, 2)


def test_a_removal_is_always_flagged():
    # 2023 approved three first-year courses, none with anything to look at
    lines = {
        "ASL1200S": "ASL1200S Academic Literacy for Engineers ....... 8 5",
        "EEE1006F": "EEE1006F Introduction to Electronic Engineering ....... 12 5",
        "MEC1003F": "MEC1003F Engineering Drawing ....... 8 5",
    }
    previous = Snapshot(
        rules=approved_2023(
            courses=tuple(course(code, year=2023) for code in lines),
            course_group_members=(
                member("EB009EEE01-y1-core", "ASL1200S"),
                member("EB009EEE01-y1-core", "EEE1006F"),
                member("EB809EEE01-y1-core", "EEE1006F"),
                member("EB009EEE01-y1-core", "MEC1003F"),
            ),
        ),
        readings=(
            reading("courses", "ASL1200S", "No requirement printed", place="p. 167"),
            reading("courses", "EEE1006F", "No requirement printed", place="p. 127"),
            reading("courses", "MEC1003F", "No requirement printed", place="p. 140"),
            *(
                reading("course_group_members", key, lines[key[-8:]], place=place)
                for key, place in (
                    ("EB009EEE01-y1-core/ASL1200S", "p. 46"),
                    ("EB009EEE01-y1-core/EEE1006F", "p. 46"),
                    ("EB809EEE01-y1-core/EEE1006F", "p. 48"),
                    ("EB009EEE01-y1-core/MEC1003F", "p. 46"),
                )
            ),
        ),
    )
    # 2026 keeps only MEC1003F, in no list, and only notes name ASL1200S
    review = compare(
        2026,
        RuleSet(courses=(course("MEC1003F"),)),
        (reading("courses", "MEC1003F", "No requirement printed"),),
        (),
        left_out=("ASL1200S",),
        previous=previous,
    )
    # One row per course, covering the course and every list it left, with 2023's pages
    assert [(row.id, row.causes, row.covers, row.printed) for row in review.rows] == [
        (
            "removal/ASL1200S",
            ("removed", "no_entry"),
            {
                "course_group_members/EB009EEE01-y1-core/ASL1200S": "2023, p. 46",
                "courses/ASL1200S": "2023, p. 167",
            },
            lines["ASL1200S"],
        ),
        (
            "removal/EEE1006F",
            ("removed",),
            {
                "course_group_members/EB009EEE01-y1-core/EEE1006F": "2023, p. 46",
                "course_group_members/EB809EEE01-y1-core/EEE1006F": "2023, p. 48",
                "courses/EEE1006F": "2023, p. 127",
            },
            lines["EEE1006F"],
        ),
        (
            "removal/MEC1003F",
            ("removed",),
            {"course_group_members/EB009EEE01-y1-core/MEC1003F": "2023, p. 46"},
            lines["MEC1003F"],
        ),
    ]
    assert review.rows[2].old == {
        "course_group_members/EB009EEE01-y1-core/MEC1003F": {
            "group_key": "EB009EEE01-y1-core",
            "course_code": "MEC1003F",
            "category": None,
        }
    }
    # Every removed row is a change for a person
    assert [(d.entity_key, d.new_value, d.flag, d.approved) for d in review.deltas] == [
        ("EB009EEE01-y1-core/ASL1200S", None, "removed", None),
        ("EB009EEE01-y1-core/EEE1006F", None, "removed", None),
        ("EB009EEE01-y1-core/MEC1003F", None, "removed", None),
        ("EB809EEE01-y1-core/EEE1006F", None, "removed", None),
        ("ASL1200S", None, "removed", None),
        ("EEE1006F", None, "removed", None),
    ]


def test_one_row_covers_every_course_printing_the_same_words():
    # Two new courses print one year-of-study rule, a third another drafted with a refer leaf, and
    # a fourth a programme. Rows sort by cause, then by the shape of their tree.
    second_year = MinYearOfStudy(min_year_of_study=2)
    head = Refer(refer="permission of the Head of Department")
    rules = RuleSet(
        courses=(
            course("PHI2012F", second_year),
            course("PHI2016S", second_year),
            course("REL2040F", AnyOf(any=(second_year, head))),
            course(
                "BUS1036F", Refer(refer="Admission as first year Commerce students")
            ),
        )
    )
    readings = (
        reading(
            "courses",
            "PHI2012F",
            "At least second year status.",
            "refused_year_of_study",
        ),
        reading(
            "courses",
            "PHI2016S",
            "At least second year status.",
            "refused_year_of_study",
        ),
        reading(
            "courses",
            "REL2040F",
            "Second-year status or permission of the Head of Department.",
            "refused_year_of_study",
        ),
        reading(
            "courses",
            "BUS1036F",
            "Admission as first year Commerce students.",
            "refused_programme",
        ),
    )
    review = compare(2026, rules, readings, ())
    assert [(row.id, tuple(row.covers)) for row in review.rows] == [
        ("requirement/BUS1036F", ("courses/BUS1036F",)),
        ("requirement/REL2040F", ("courses/REL2040F",)),
        ("requirement/PHI2012F", ("courses/PHI2012F", "courses/PHI2016S")),
    ]


def test_a_draft_of_wording_that_prints_a_dp_is_marked():
    # Made-up wording. A DP printed as a word in a refused requirement is marked. DP inside a code
    # isn't, and nor is a DP in wording no model drafted, where only a check fails.
    printed = {
        "EEE2099F": ("EEE2045F (DP)", "refused_free_text"),
        "EEE2098F": ("A pass in ADP2001F or DPR1001S", "refused_free_text"),
        "EEE2097F": ("EEE2044S (DP)", "check_failed"),
    }
    rules = RuleSet(
        courses=tuple(
            course(code, Refer(refer=words)) for code, (words, _) in printed.items()
        )
    )
    readings = tuple(
        reading("courses", code, words, flag) for code, (words, flag) in printed.items()
    )
    failure = Failure(
        place="p. 1",
        what="EEE2097F's rule names EEE2044S, which isn't loaded, printed or equivalent",
        flags=("courses", "EEE2097F"),
    )
    review = compare(
        2026, rules, readings, (Check(name=TREE_CODES, failures=(failure,)),)
    )
    assert {row.id: row.mark for row in review.rows} == {
        "requirement/EEE2099F": "dp",
        "requirement/EEE2098F": None,
        "requirement/EEE2097F": None,
    }


def test_a_failed_check_is_always_a_reason_to_look():
    # 2023 approved MEC2045S's words, so 2026 carries them over unchanged, but a check on them fails
    # again. A draft that fails a check shows both reasons, and a failure on no row of this year's,
    # such as a timetable cell or a course the year doesn't hold, has a row of its own.
    words = "MEC2023F/S or MEC2047F/S"
    tree = AnyOf(
        any=(
            CourseNeed(course="MEC2023F", need="pass"),
            CourseNeed(course="MEC2047F", need="pass"),
        )
    )
    previous = Snapshot(
        rules=approved_2023(courses=(course("MEC2045S", tree, year=2023),)),
        readings=(reading("courses", "MEC2045S", words, "refused_mixed_and_or"),),
    )
    year_two = YearRules(
        all=(
            AllOfGroup(all_of_group="EB022EEE02-y2-core"),
            TotalCredits(total_credits=136),
        )
    )
    rules = RuleSet(
        courses=(
            course("MEC2045S", tree),
            course("CSC3002F", CourseNeed(course="MAM1000W", need="pass")),
        ),
        curriculum_rules=(
            CurriculumRule(
                handbook_year=2026,
                curriculum_code="EB022EEE02",
                year_of_study=2,
                rule=year_two,
            ),
        ),
    )
    readings = (
        reading("courses", "MEC2045S", words, "check_failed", "p. 148"),
        reading("courses", "CSC3002F", "MAM1000W.", "refused_punctuation", "p. 171"),
        reading("curriculum_rules", "EB022EEE02/2", "Second Year Core Courses (EC)"),
    )
    unknown = "{}'s rule names {}, which isn't loaded, printed or equivalent"
    totals = (
        "EB022EEE02 year 2's core table prints 136 credits, but its rows add up to 144"
    )
    checks = (
        Check(
            name=TREE_CODES,
            failures=(
                Failure(
                    place="p. 148",
                    what=unknown.format("MEC2045S", "MEC2023F"),
                    flags=("courses", "MEC2045S"),
                ),
                Failure(
                    place="p. 171",
                    what=unknown.format("CSC3002F", "MAM1000W"),
                    flags=("courses", "CSC3002F"),
                ),
                Failure(
                    place="p. 9",
                    what=unknown.format("EEE9999F", "EEE9998F"),
                    flags=("courses", "EEE9999F"),
                ),
            ),
        ),
        Check(
            name="Printed totals add up",
            failures=(
                Failure(
                    place="p. 53",
                    what=totals,
                    flags=("curriculum_rules", "EB022EEE02/2"),
                ),
            ),
        ),
        Check(
            name="The timetable rebuilds from the stored meetings",
            failures=(
                Failure(place="timetable", what="EB022 lacks a made-up meeting"),
            ),
        ),
    )
    review = compare(2026, rules, readings, checks, previous=previous)
    # The draft sorts first by its cause, then the failures, by the shape of their trees
    assert [(row.id, row.causes, row.failures) for row in review.rows] == [
        (
            "requirement/CSC3002F",
            ("refused_punctuation", "check_failed"),
            (f"p. 171: {unknown.format('CSC3002F', 'MAM1000W')}",),
        ),
        (
            f"check/p. 9: {unknown.format('EEE9999F', 'EEE9998F')}",
            ("check_failed",),
            (f"p. 9: {unknown.format('EEE9999F', 'EEE9998F')}",),
        ),
        (
            "check/timetable: EB022 lacks a made-up meeting",
            ("check_failed",),
            ("timetable: EB022 lacks a made-up meeting",),
        ),
        (
            "rule/EB022EEE02/2",
            ("check_failed",),
            (f"p. 53: {totals}",),
        ),
        (
            "requirement/MEC2045S",
            ("check_failed",),
            (f"p. 148: {unknown.format('MEC2045S', 'MEC2023F')}",),
        ),
    ]
