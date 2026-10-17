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


def test_a_decision_holds_only_for_the_reading_it_was_made_on():
    # Two drafted requirements are accepted, beside a decision on a row no longer read. Then one
    # is drafted again, with a tree no one has seen.
    def reviewed(redrafted, decided=()):
        rules = RuleSet(
            courses=(
                course("PHI2012F", MinYearOfStudy(min_year_of_study=2)),
                course("REL2040F", redrafted),
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
                "courses", "REL2040F", "Second-year status.", "refused_year_of_study"
            ),
        )
        return compare(2026, rules, readings, (), decided=decided)

    first = reviewed(MinYearOfStudy(min_year_of_study=2))
    decided = [
        {**row.model_dump(mode="json"), "decision": "accept"} for row in first.rows
    ]
    decided.append(
        {"id": "requirement/GON9999F", "fingerprint": "0", "decision": "accept"}
    )
    again = reviewed(MinYearOfStudy(min_year_of_study=2), decided)
    assert (again.pending, again.returned) == ((), ("requirement/GON9999F",))
    changed = reviewed(MinYearOfStudy(min_year_of_study=3), decided)
    assert [(row.id, row.decision) for row in changed.rows] == [
        ("requirement/PHI2012F", "accept"),
        ("requirement/REL2040F", None),
    ]
    assert changed.pending == ("requirement/REL2040F",)
    assert changed.returned == ("requirement/GON9999F", "requirement/REL2040F")


def test_a_decision_is_checked_before_it_counts():
    # 2023 approved EEE2004F's rule. In 2026 each course prints new words, refused by the grammar,
    # and is decided as its comment says. EEE2010F's rule, read with certainty, names EEE1006F,
    # known only through an equivalence, which is rejected.
    previous = Snapshot(
        rules=approved_2023(
            courses=(
                course("EEE2004F", CourseNeed(course="EEE2001F", need="pass"), 2023),
            )
        ),
        readings=(reading("courses", "EEE2004F", "EEE2001F"),),
    )
    unknown = "p. 1: {}'s rule names {}, which isn't loaded, printed or equivalent"
    decisions = {
        # a corrected leaf with no need
        "EEE2001F": ("correct", {"course": "EEE2008F"}, None),
        # a correction with no tree
        "EEE2002F": ("correct", None, None),
        # a new course, so rejecting would leave it needing nothing
        "EEE2003F": ("reject", None, None),
        # 2023's rule kept
        "EEE2004F": ("reject", None, None),
        # a tree beside accept
        "EEE2005F": ("accept", {"course": "EEE2008F", "need": "pass"}, None),
        # its draft names a code the year doesn't hold, and no note says why
        "EEE2006F": ("accept", None, None),
        # a correction naming a mistyped code, and no note says why
        "EEE2007F": ("correct", {"course": "EEE2O08F", "need": "pass"}, None),
        # a correction the year holds
        "EEE2008F": ("correct", {"course": "EEE2001F", "need": "pass"}, None),
        "EEE2009F": ("acept", None, None),
    }
    courses = [course(code, Refer(refer=code)) for code in decisions]
    courses[5] = course("EEE2006F", CourseNeed(course="EEE9998F", need="pass"))
    known = CourseNeed(course="EEE1006F", need="pass")
    rules = RuleSet(
        courses=(*courses, course("EEE2010F", known)),
        equivalences=tuple(
            Equivalence(handbook_year=2026, course_code=a, counts_as=b)
            for a, b in (("EEE1006F", "EEE1008F"), ("MAM1020F", "MAM1023F"))
        ),
    )
    readings = (
        *(
            reading("courses", code, f"{code} in new words", "refused_free_text")
            for code in decisions
        ),
        reading("courses", "EEE2010F", "EEE1006F"),
        reading("equivalences", "EEE1006F/EEE1008F", "A reason.", "not_printed"),
        reading("equivalences", "MAM1020F/MAM1023F", "A reason.", "not_printed"),
    )
    failed = Failure(
        place="p. 1",
        what=unknown.format("EEE2006F", "EEE9998F").removeprefix("p. 1: "),
        flags=("courses", "EEE2006F"),
    )
    checks = (Check(name=TREE_CODES, failures=(failed,)),)
    first = compare(2026, rules, readings, checks, previous=previous)
    decided = [row.model_dump(mode="json") for row in first.rows]
    for row in decided:
        name = row["id"].split("/", 1)[1]
        if name in decisions:
            row["decision"], row["corrected"], row["note"] = decisions[name]
    by_id = {row["id"]: row for row in decided}
    by_id["equivalence/EEE1006F/EEE1008F"]["decision"] = "reject"
    by_id["equivalence/MAM1020F/MAM1023F"]["decision"] = "correct"
    by_id["equivalence/MAM1020F/MAM1023F"]["corrected"] = {"made": "up"}
    review = compare(2026, rules, readings, checks, previous=previous, decided=decided)
    assert {(problem.row, problem.note) for problem in review.problems} == {
        ("requirement/EEE2001F", False),
        ("requirement/EEE2002F", False),
        ("requirement/EEE2003F", False),
        ("requirement/EEE2005F", False),
        ("requirement/EEE2006F", True),
        ("requirement/EEE2007F", True),
        ("requirement/EEE2009F", False),
        ("equivalence/MAM1020F/MAM1023F", False),
        (None, False),
    }
    # The mistyped code is named, and so is the rule the rejected equivalence leaves unmet
    texts = {problem.row: problem.text for problem in review.problems}
    assert unknown.format("EEE2007F", "EEE2O08F") in texts["requirement/EEE2007F"]
    assert [problem.text for problem in review.problems if problem.row is None] == [
        unknown.format("EEE2010F", "EEE1006F")
    ]
    # The decisions that stand, EEE2004F's, EEE2008F's and the rejected equivalence's, aren't pending,
    # and a change waits for its decision to be usable
    assert set(review.pending) == {problem.row for problem in review.problems} - {None}
    approved = {d.entity_key: d.approved for d in review.deltas}
    assert (approved["EEE2006F"], approved["EEE2008F"]) == (None, True)


def test_each_decision_sets_the_year_and_is_recorded_with_its_change():
    # 2023 approved five courses. In 2026 three print new words, refused by the grammar, two are
    # gone, and two courses and an equivalence are new. Every code named is printed somewhere.
    def needs(code):
        return CourseNeed(course=code, need="pass")

    previous = Snapshot(
        rules=approved_2023(
            courses=tuple(
                course(code, needs(f"EEE200{n}F"), 2023)
                for n, code in enumerate(
                    ("EEE3001F", "EEE3002F", "EEE3003F", "EEE3004F", "EEE3005F"), 1
                )
            )
        ),
        readings=tuple(
            reading("courses", f"EEE300{n}F", f"EEE200{n}F", place=f"p. {n}")
            for n in range(1, 6)
        ),
    )
    draft = AnyOf(any=(needs("EEE2009F"), Refer(refer="or permission")))
    rules = RuleSet(
        courses=(
            course("EEE3001F", draft),
            course("EEE3002F", draft, convener="Dr B Made-Up"),
            course("EEE3003F", draft),
            course("EEE3006F", draft),
            course("EEE3007F", draft),
        ),
        equivalences=(
            Equivalence(
                handbook_year=2026, course_code="EEE1006F", counts_as="EEE1008F"
            ),
        ),
    )
    readings = (
        *(
            reading("courses", code, f"{code}'s new words", "refused_free_text")
            for code in ("EEE3001F", "EEE3002F", "EEE3003F", "EEE3006F", "EEE3007F")
        ),
        reading("equivalences", "EEE1006F/EEE1008F", "A reason.", "not_printed"),
    )

    def run(decided=()):
        return compare(
            2026,
            rules,
            readings,
            (),
            entries=[f"EEE200{n}F" for n in range(1, 10)],
            previous=previous,
            decided=decided,
        )

    # The correction is typed with its leaves out of order
    corrected = {
        "any": [{"refer": "permission"}, {"course": "EEE2003F", "need": "pass"}]
    }
    decisions = {
        "requirement/EEE3001F": ("reject", None),
        "requirement/EEE3002F": ("reject", None),
        "requirement/EEE3003F": ("correct", corrected),
        "requirement/EEE3006F": ("accept", None),
        "removal/EEE3004F": ("reject", None),
        "removal/EEE3005F": ("accept", None),
        "equivalence/EEE1006F/EEE1008F": ("reject", None),
    }
    decided = [row.model_dump(mode="json") for row in run().rows]
    for row in decided:
        row["decision"], row["corrected"] = decisions.get(row["id"], (None, None))
    review = run(decided)

    def as_stored(code, rule, convener="Dr A Made-Up"):
        return course(code, rule, convener=convener).model_dump(
            mode="json", exclude={"handbook_year"}
        )

    assert [(d.entity_key, d.approved, d.corrected_value) for d in review.deltas] == [
        # Rejected, so 2023's row stands
        ("EEE3001F", False, None),
        # Rejected, so 2023's rule stands, but beside the new convener, read with certainty: a
        # correction of what was read
        ("EEE3002F", True, as_stored("EEE3002F", needs("EEE2002F"), "Dr B Made-Up")),
        # Corrected, with its leaves in canonical order
        (
            "EEE3003F",
            True,
            as_stored(
                "EEE3003F",
                AnyOf(any=(needs("EEE2003F"), Refer(refer="permission"))),
            ),
        ),
        # A rejected removal keeps 2023's row, and an accepted one removes it
        ("EEE3004F", False, None),
        ("EEE3005F", True, None),
        ("EEE3006F", True, None),
        # Not decided yet
        ("EEE3007F", None, None),
        # A rejected addition is never added
        ("EEE1006F/EEE1008F", False, None),
    ]
    assert review.pending == ("requirement/EEE3007F",)
