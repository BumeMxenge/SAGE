# Whether she may take each course, as Explore Electives shows it. A course she has passed, or whose
# result is still to come, which plans count as passed, isn't for her, under its own code or one
# that counts as it. Otherwise its entry rule decides, read from her record alone, and the reason
# names what's missing or quotes the words a person must judge.
from collections.abc import Mapping, Sequence

from sage.engine.evaluator import Record, evaluate
from sage.engine.reasons import unchecked
from sage.shared.planning import Eligibility
from sage.shared.rules import Course, ResultSymbol, RuleSet
from sage.shared.students import CourseHistoryLine, Student
from sage.shared.wording import in_words


class EntryRuleEligibility:
    def check(
        self,
        courses: Sequence[Course],
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
        student: Student,
    ) -> dict[str, Eligibility]:
        record = Record(student, history, rules, symbols)
        return {course.code: eligibility(course, record) for course in courses}


def eligibility(course: Course, record: Record) -> Eligibility:
    passed = record.passed(course.code)
    if passed is not None:
        counts = (
            ""
            if passed.course_code == course.code
            else f", which counts as {course.code}"
        )
        return Eligibility(
            status="not_eligible",
            reason=f"You've already passed {passed.course_code}{counts}.",
        )
    pending = record.pending_line(course.code)
    if pending is not None:
        under = (
            pending.course_code
            if pending.course_code == course.code
            else f"{pending.course_code}, which counts as {course.code},"
        )
        return Eligibility(
            status="not_eligible",
            reason=f"Your result for {under} is still to come, and SAGE counts it as passed.",
        )
    verdict = evaluate(course.entry_rule, record)
    if verdict.value == "met":
        return Eligibility(status="eligible")
    if verdict.value == "not_met":
        words = in_words(verdict.rest)
        return Eligibility(
            status="not_eligible",
            reason=f"It needs {words}, which your record doesn't show yet.",
        )
    return Eligibility(status="check", reason=unchecked("It", verdict.rest))
