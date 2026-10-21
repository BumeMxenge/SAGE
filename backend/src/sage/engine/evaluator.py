# Whether her record meets an entry rule: met, not met, or left open. A pass counts through its
# covers: the course itself, each course its equivalences say it counts as, and the same course's
# other semester offering at the same credits, one step of each, in either order. What her record
# can't decide is left open: printed words only a person can judge, a result still to come, and,
# when there's a plan, a course the plan itself might take.
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
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

# What one leaf of a rule comes to: decided by her record, unknown, or left to a plan whose courses
# meet it when taken (planned) or only make it possible (maybe)
Value = Literal["met", "not_met", "unknown", "planned", "maybe"]
# The plan's courses that could meet a leaf, each in a term that comes in time for the leaf's course
Plan = Callable[[CourseNeed], tuple[str, ...]]


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
        # Each code her lines cover, with the lines that cover it, oldest first, and the place in
        # that order of each line that passes it or has its result still to come
        self._lines: dict[str, list[CourseHistoryLine]] = defaultdict(list)
        self._done: dict[str, list[int]] = defaultdict(list)
        oldest_first = sorted(history, key=lambda line: (line.academic_year, line.term))
        for at, line in enumerate(oldest_first):
            for code in self.covers(line.course_code, line.credits):
                self._lines[code].append(line)
                if self._outcomes[line.result] in (*PASSED, *PENDING):
                    self._done[code].append(at)
        self.passed_credits = sum(
            line.credits for line in history if self._outcomes[line.result] in PASSED
        )
        # Each year's core, practical training aside, and the core courses she has done
        self.core = {
            rule.year_of_study: [
                code
                for part in rule.rule.all
                if isinstance(part, AllOfGroup)
                for code in self.members[part.all_of_group]
                if not code.endswith("X")
            ]
            for rule in rules.curriculum_rules
            if rule.curriculum_code == self.curriculum
        }
        self.core_done = set(
            self.counted(code for year in sorted(self.core) for code in self.core[year])
        )
        # Her year of study, which FB5 sets by when she's expected to graduate: the latest year from
        # which she has passed at least two core courses, or the year after it once its core is
        # complete, and never earlier than her lowest unfinished year. Two keeps one course taken
        # early, such as EEE4124C, from moving her up a year.
        done = {year: self.core_done & set(core) for year, core in self.core.items()}
        complete = {year for year, core in self.core.items() if done[year] == set(core)}
        latest = max((year for year in done if len(done[year]) >= 2), default=0)
        lowest = min(set(self.core) - complete, default=max(self.core, default=0) + 1)
        self.year = max(latest + 1 if latest in complete else latest, lowest)

    def covers(self, code: str, credits: int) -> set[str]:
        # The codes a pass in this course counts for: itself, and at most one step of each kind, in
        # either order, so PHY1014S reaches PHY1012F through PHY1014F
        counted = self._counts_as[code]
        offered = self._offered(code, credits)
        return (
            {code}
            | counted
            | offered
            | {far for near in counted for far in self._offered(near, credits)}
            | {far for near in offered for far in self._counts_as[near]}
        )

    def _offered(self, code: str, credits: int) -> set[str]:
        # The year's offerings of the same course at the same credits
        return {
            other
            for other, worth in self._credits.items()
            if other[:7] == code[:7] and worth == credits
        }

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

    def pending(self, code: str) -> Outcome | None:
        # A course not passed whose result is still to come, with what's to come
        if self.passed(code) is not None:
            return None
        found = [self._outcomes[line.result] for line in self._lines[code]]
        return next((outcome for outcome in found if outcome in PENDING), None)

    def done(self, code: str) -> bool:
        # Passed, or with a result still to come, which a plan assumes she passes
        return self.passed(code) is not None or self.pending(code) is not None

    def counted(self, codes: Iterable[str]) -> list[str]:
        # The codes she has done, each through a line of its own, as one pass counts for one course
        # however many codes it covers. A line already counted for one code moves to another code it
        # covers when that frees it for this one, so as many codes count as can.
        # Each line counted, by its place, and the code it counts for
        owner: dict[int, str] = {}

        def count(code: str, tried: set[int]) -> bool:
            for at in self._done[code]:
                if at in tried:
                    continue
                tried.add(at)
                if at not in owner or count(owner[at], tried):
                    owner[at] = code
                    return True
            return False

        return [code for code in dict.fromkeys(codes) if count(code, set())]

    def repeated(self, code: str) -> bool:
        # Taken before and not passed, so taking it again repeats it (FB3.4)
        return not self.done(code) and bool(self._lines[code])

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


def evaluate(
    rule: EntryRule | None, record: Record, plan: Plan | None = None
) -> Verdict:
    # all is met when every part is and fails when any part does; any is met when any part is and
    # fails when every part does; anything else is open
    if rule is None:
        return Verdict(value="met")
    if isinstance(rule, AllOf):
        parts = [evaluate(child, record, plan) for child in rule.all]
        failed = [part.rest for part in parts if part.value == "not_met"]
        if failed:
            return Verdict(value="not_met", rest=together(AllOf, failed))
        return still_open(AllOf, parts)
    if isinstance(rule, AnyOf):
        parts = [evaluate(child, record, plan) for child in rule.any]
        if any(part.value == "met" for part in parts):
            return Verdict(value="met")
        if all(part.value == "not_met" for part in parts):
            return Verdict(value="not_met", rest=rule)
        return still_open(AnyOf, parts)
    value = leaf(rule, record, plan)
    if value == "met":
        return Verdict(value="met")
    return Verdict(value="not_met" if value == "not_met" else "open", rest=rule)


def leaf(
    node: CourseNeed | StudentIn | MinYearOfStudy | Refer,
    record: Record,
    plan: Plan | None = None,
) -> Value:
    if isinstance(node, Refer):
        return "unknown"
    if isinstance(node, StudentIn):
        return "met" if record.curriculum in node.student_in else "not_met"
    if isinstance(node, MinYearOfStudy):
        return "met" if record.year >= node.min_year_of_study else "not_met"
    found = record.meets(node)
    if found != "not_met":
        return found
    if plan is None:
        # She could still take a co-requisite alongside
        return "unknown" if node.need == "concurrent" else "not_met"
    if not plan(node):
        return "not_met"
    # Passing a course the plan takes earlier gives her at least 50, so a higher mark is only
    # possible
    return "maybe" if node.need == "mark" and node.min_mark > 50 else "planned"


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
