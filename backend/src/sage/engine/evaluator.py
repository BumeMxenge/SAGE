# Whether her record meets an entry rule: met, not met, or left open. A pass counts through its
# covers: the course itself, each course its equivalences say it counts as, and the same course's
# other semester offering at the same credits. What her record can't decide is left open: printed
# words only a person can judge, and a result still to come.
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Literal

from sage.shared.base import Row
from sage.shared.rules import (
    AllOf,
    AllOfGroup,
    AnyOf,
    CourseNeed,
    EntryRule,
    MinYearOfStudy,
    Outcome,
    Refer,
    ResultSymbol,
    RuleSet,
    StudentIn,
)
from sage.shared.students import CourseHistoryLine, Student, final_mark

# The outcomes that pass a course, and those whose result is still to come
PASSED: tuple[Outcome, ...] = ("pass", "credited")
PENDING: tuple[Outcome, ...] = ("in_progress", "supp_pending")

# What one leaf of a rule comes to
Value = Literal["met", "not_met", "unknown"]


class Record:
    # Her course history as one year's rules read it
    def __init__(
        self,
        student: Student,
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
    ) -> None:
        self.curriculum = student.curriculum_code
        self.members: dict[str, list[str]] = defaultdict(list)
        for member in rules.course_group_members:
            self.members[member.group_key].append(member.course_code)
        self._credits = {course.code: course.credits for course in rules.courses}
        self._counts_as: dict[str, set[str]] = defaultdict(set)
        for rule in rules.equivalences:
            self._counts_as[rule.course_code].add(rule.counts_as)
        self._outcomes = {line.result: symbols[line.result].outcome for line in history}
        # Each code her lines cover, with the lines that cover it, oldest first
        self._lines: dict[str, list[CourseHistoryLine]] = defaultdict(list)
        for line in sorted(history, key=lambda line: (line.academic_year, line.term)):
            for code in self.covers(line.course_code, line.credits):
                self._lines[code].append(line)
        # One more than the highest year whose own core she has done, practical training aside, as
        # FB5 sets her year by when she's expected to graduate
        done = [
            rule.year_of_study
            for rule in rules.curriculum_rules
            if rule.curriculum_code == self.curriculum
            and all(
                self.done(code)
                for part in rule.rule.all
                if isinstance(part, AllOfGroup)
                for code in self.members[part.all_of_group]
                if not code.endswith("X")
            )
        ]
        self.year = max(done, default=0) + 1

    def covers(self, code: str, credits: int) -> set[str]:
        # The codes a pass in this course counts for
        return (
            {code}
            | self._counts_as[code]
            | {
                other
                for other, worth in self._credits.items()
                if other[:7] == code[:7] and worth == credits
            }
        )

    def passed(self, code: str) -> CourseHistoryLine | None:
        # Her first line that passes this course, if any
        return next(
            (
                line
                for line in self._lines[code]
                if self._outcomes[line.result] in PASSED
            ),
            None,
        )

    def pending(self, code: str) -> bool:
        # Not passed, with a result still to come
        return self.passed(code) is None and any(
            self._outcomes[line.result] in PENDING for line in self._lines[code]
        )

    def done(self, code: str) -> bool:
        # Passed, or with a result still to come, which a plan assumes she passes
        return self.passed(code) is not None or self.pending(code)

    def meets(self, need: CourseNeed) -> Value:
        # Whether any of her attempts at the course, or at one that covers it, meets the leaf
        found = {self._meets(line, need) for line in self._lines[need.course]}
        if "met" in found:
            return "met"
        return "unknown" if "unknown" in found else "not_met"

    def _meets(self, line: CourseHistoryLine, need: CourseNeed) -> Value:
        outcome = self._outcomes[line.result]
        if need.need != "mark":
            if outcome in PASSED:
                return "met"
            return "unknown" if outcome in PENDING else "not_met"
        mark = final_mark(line)
        if outcome in ("pass", "fail") and mark is not None:
            return "met" if mark >= need.min_mark else "not_met"
        if outcome == "supp_pending":
            # A supplementary is taken to give 50 at most, as FB7.3 prints for an additional
            # assessment
            return "unknown" if need.min_mark <= 50 else "not_met"
        # A pass or credit printed with no mark, or a result still to come
        return (
            "unknown" if outcome in ("pass", "credited", "in_progress") else "not_met"
        )


class Verdict(Row):
    # A rule as her record leaves it, with the part that fails when it's not met, and the part still
    # open when it's open
    value: Literal["met", "not_met", "open"]
    rest: EntryRule | None = None


def evaluate(rule: EntryRule | None, record: Record) -> Verdict:
    # all is met when every part is and fails when any part does; any is met when any part is and
    # fails when every part does; anything else is open
    if rule is None:
        return Verdict(value="met")
    if isinstance(rule, AllOf):
        parts = [evaluate(child, record) for child in rule.all]
        failed = [part.rest for part in parts if part.value == "not_met"]
        if failed:
            return Verdict(value="not_met", rest=together(AllOf, failed))
        return still_open(AllOf, parts)
    if isinstance(rule, AnyOf):
        parts = [evaluate(child, record) for child in rule.any]
        if any(part.value == "met" for part in parts):
            return Verdict(value="met")
        if all(part.value == "not_met" for part in parts):
            return Verdict(value="not_met", rest=rule)
        return still_open(AnyOf, parts)
    value = leaf(rule, record)
    if value == "met":
        return Verdict(value="met")
    return Verdict(value="not_met" if value == "not_met" else "open", rest=rule)


def leaf(
    node: CourseNeed | StudentIn | MinYearOfStudy | Refer, record: Record
) -> Value:
    if isinstance(node, Refer):
        return "unknown"
    if isinstance(node, StudentIn):
        return "met" if record.curriculum in node.student_in else "not_met"
    if isinstance(node, MinYearOfStudy):
        return "met" if record.year >= node.min_year_of_study else "not_met"
    found = record.meets(node)
    # She could still take a co-requisite alongside
    if found == "not_met" and node.need == "concurrent":
        return "unknown"
    return found


def still_open(kind: type[AllOf] | type[AnyOf], parts: list[Verdict]) -> Verdict:
    # An all with nothing failed, or an any with nothing met, is open on its open parts
    rest = [part.rest for part in parts if part.value == "open"]
    if not rest:
        return Verdict(value="met")
    return Verdict(value="open", rest=together(kind, rest))


def together(kind: type[AllOf] | type[AnyOf], parts: list[EntryRule]) -> EntryRule:
    if len(parts) == 1:
        return parts[0]
    return AllOf(all=tuple(parts)) if kind is AllOf else AnyOf(any=tuple(parts))
