# Checks what Explore Electives says of each course: one course per status, with its reason written
# out by hand. A reason names only the part of a rule she hasn't met, or the part still open, where
# words such as "or equivalent" keep whole the list they continue.
from uuid import UUID

from sage.engine.eligibility import EntryRuleEligibility
from sage.shared.rules import (
    AllOf,
    AnyOf,
    Course,
    CourseNeed,
    Equivalence,
    Refer,
    RuleSet,
)
from sage.shared.students import CourseHistoryLine, Student

STUDENT = Student(id=UUID(int=7), curriculum_code="EB000AAA01", intake_year=2025)


def course(code: str, rule=None, credits: int = 16) -> Course:
    return Course(
        handbook_year=2026,
        code=code,
        name="Made Up",
        credits=credits,
        nqf_level=7,
        term="sem1",
        entry_rule=rule,
    )


def line(code: str, result: str, mark: int | None, credits: int) -> CourseHistoryLine:
    return CourseHistoryLine(
        student_id=STUDENT.id,
        academic_year=2025,
        term="sem1",
        course_code=code,
        course_name="Made Up",
        credits=credits,
        result=result,
        mark=mark,
    )


def test_each_status_with_its_reason(result_symbols):
    first, second = (
        CourseNeed(course=code, need="pass") for code in ("AAA1000F", "AAA1001F")
    )
    printed = Refer(refer="Not stated in course entry.")
    rules = RuleSet(
        courses=(
            course("AAA1000F"),
            course("EEE1008F", credits=12),
            course("AAA1002F"),
            course("AAA2000S", AllOf(all=(first, second))),
            course("AAA2001S", AnyOf(any=(printed, second))),
        ),
        # As the approved 2026 has EEE1006F count as EEE1008F
        equivalences=(
            Equivalence(
                handbook_year=2026, course_code="EEE1006F", counts_as="EEE1008F"
            ),
        ),
    )
    history = [line("AAA1000F", "1", 80, 16), line("EEE1006F", "3", 59, 12)]
    symbols = {row.symbol: row for row in result_symbols}
    found = EntryRuleEligibility().check(
        rules.courses, history, rules, symbols, STUDENT
    )
    assert {code: (row.status, row.reason) for code, row in found.items()} == {
        "AAA1000F": ("not_eligible", "You've already passed AAA1000F."),
        "EEE1008F": (
            "not_eligible",
            "You've already passed EEE1006F, which counts as EEE1008F.",
        ),
        "AAA1002F": ("eligible", None),
        "AAA2000S": (
            "not_eligible",
            "It needs AAA1001F, which your record doesn't show yet.",
        ),
        "AAA2001S": (
            "check",
            (
                'It needs "Not stated in course entry." SAGE can\'t check this, so confirm '
                "it with your advisor."
            ),
        ),
    }


def test_words_that_continue_a_list_keep_the_whole_list(result_symbols):
    # As CSC3002F's maths list ends "or equivalent" (p. 171). She has passed AAA1000F alone, so
    # every branch fails but the words, and each still reads as printed, with no second "or".
    first, second, third, fourth = (
        CourseNeed(course=code, need="pass")
        for code in ("AAA1000F", "AAA1001S", "AAA1002F", "AAA1003F")
    )
    rule = AnyOf(
        any=(
            AllOf(all=(first, second)),
            third,
            fourth,
            Refer(refer="or equivalent"),
        )
    )
    rules = RuleSet(courses=(course("AAA3000S", rule),))
    history = [line("AAA1000F", "1", 80, 16)]
    symbols = {row.symbol: row for row in result_symbols}
    found = EntryRuleEligibility().check(
        rules.courses, history, rules, symbols, STUDENT
    )
    assert found["AAA3000S"].reason == (
        'It needs one of (AAA1000F and AAA1001S), AAA1002F or AAA1003F "or equivalent". SAGE '
        "can't check this, so confirm it with your advisor."
    )
