# The words of every reason a plan set gives, and the handbook passage each rests on: one of her
# curriculum's tables by its heading, a course by its own entry, a faculty rule by its number, and a
# footnote by the table that prints it. A reason with nothing to rest on cites none.
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sage.engine.facts import Need
from sage.engine.printed import Note, Place
from sage.shared.base import Row
from sage.shared.rules import EntryRule, Outcome, RuleSet
from sage.shared.students import ReasonKind
from sage.shared.wording import all_of, in_words

YEARS = ("first", "second", "third", "fourth", "fifth")


class Reason(Row):
    kind: ReasonKind
    message: str
    course_code: str | None = None
    passage_id: UUID | None = None
    details: dict[str, Any] | None = None


class Reasons:
    def __init__(self, rules: RuleSet, curriculum: str | None) -> None:
        self._passages = rules.passages
        self._curriculum = curriculum
        self._names = {course.code: course.name for course in rules.courses}

    def table(self, heading: str | None) -> UUID | None:
        # One of her curriculum's tables
        return next(
            (
                passage.id
                for passage in self._passages
                if passage.curriculum_code == self._curriculum
                and passage.section == heading
            ),
            None,
        )

    def entry(self, code: str) -> UUID | None:
        # A course's own entry
        return next(
            (passage.id for passage in self._passages if passage.course_code == code),
            None,
        )

    def faculty(self, rule: str) -> UUID | None:
        # A faculty rule, such as FB3.4
        return next(
            (
                passage.id
                for passage in self._passages
                if passage.section == rule and passage.curriculum_code is None
            ),
            None,
        )

    def core(self, codes: Sequence[str], table: str) -> Reason:
        return Reason(
            kind="included",
            message=f"Every plan holds the core courses you still need this year: "
            f"{listed(codes)}.",
            passage_id=self.table(table),
        )

    def arrears(self, codes: Sequence[str], year: int, table: str) -> Reason:
        return Reason(
            kind="included",
            message=f"Every plan holds {listed(codes)}, which you still owe from your "
            f"{YEARS[year - 1]} year.",
            passage_id=self.table(table),
        )

    def need(self, rule: Need, year: int | None, table: str | None) -> Reason:
        # A year rule with what she has passed taken off. One from an earlier year names it.
        owed = f" to finish your {YEARS[year - 1]} year" if year else ""
        return Reason(
            kind="included",
            message=f"Every plan takes {asked(rule)}{owed}.",
            passage_id=self.table(table),
        )

    def minimum(self, credits: int, table: str | None, slots: bool) -> Reason:
        counting = ", counting its complementary studies" if slots else ""
        return Reason(
            kind="included",
            message=f"Every plan comes to at least {credits} credits for the year{counting}.",
            passage_id=self.table(table),
        )

    def excluded(self, code: str, rest: EntryRule, core: bool) -> Reason:
        # A course she can't take yet, which leaves core credits for her advisor to settle
        where = "your plans" if core else "any plan"
        advice = " See your advisor about it." if core else ""
        return Reason(
            kind="excluded",
            message=f"{code} isn't in {where}, as it needs {in_words(rest)}, which your "
            f"record doesn't show yet.{advice}",
            course_code=code,
            passage_id=self.entry(code),
        )

    def unsure(self, code: str, rest: EntryRule) -> Reason:
        return Reason(
            kind="conditional",
            message=f"{code} needs {in_words(rest)}, which SAGE can't confirm from your "
            "record. Check with your advisor.",
            course_code=code,
            passage_id=self.entry(code),
        )

    def met_by_plan(self, code: str, rest: EntryRule, every: bool) -> Reason:
        holder = "every plan holds" if every else "this plan holds"
        return Reason(
            kind="included",
            message=f"{code} needs {in_words(rest)}, which {holder} in time.",
            course_code=code,
            passage_id=self.entry(code),
        )

    def untimed(self, code: str) -> Reason:
        return Reason(
            kind="conditional",
            message=f"{code} has a meeting with no printed day or time, so SAGE can't check "
            "it for clashes. Check its times with your advisor.",
            course_code=code,
            passage_id=self.faculty("FB3.4"),
        )

    def practical(self, code: str) -> Reason:
        return Reason(
            kind="conditional",
            message=f"Your record doesn't show {code}, {self._names[code]}, as complete yet. "
            "You need it to graduate, so check with your advisor when it will be signed off.",
            course_code=code,
            passage_id=self.entry(code),
        )

    def pending(self, code: str, outcome: Outcome) -> Reason:
        # A result still to come, which every plan assumes she passes
        if outcome == "supp_pending":
            return Reason(
                kind="conditional",
                message=f"Your supplementary exam for {code} is still to come. These plans "
                "assume you pass it, so see your advisor if you don't.",
                course_code=code,
                passage_id=self.faculty("FB7"),
            )
        return Reason(
            kind="conditional",
            message=f"Your result for {code} isn't out yet. These plans assume you pass it, "
            "so see your advisor if you don't.",
            course_code=code,
            passage_id=self.entry(code),
        )

    def more_electives(self, table: str, note: Note | None) -> Reason:
        noted = f' It notes: "{note.words}"' if note else ""
        return Reason(
            kind="excluded",
            message="Plans with more electives than the rules ask for aren't listed. The "
            f"handbook allows more, so ask your advisor if you want to add one.{noted}",
            passage_id=self.table(table),
        )

    def same_slots(self, note: Note) -> Reason:
        return Reason(
            kind="conditional",
            message=f'The handbook notes, without naming them: "{note.words}" Check your '
            "electives with your advisor.",
            passage_id=self.table(note.table),
        )

    def slot(
        self,
        credits: int,
        table: str | None,
        fits: Sequence[str],
        untimed: Sequence[str],
        place: Place | None = None,
    ) -> Reason:
        # Complementary credits, or a 576-credit place, the plan leaves to her, with the approved
        # complementary courses that fit its timetable
        if place:
            ask = (
                f"Your 576-credit curriculum still needs {place.code}. Take an approved "
                f"complementary studies course of at least {credits} credits in its place"
            )
            passage = self.table(place.table)
        else:
            ask = f"Add approved complementary studies courses worth at least {credits} credits"
            passage = self.table(table)
        if fits:
            marked = (
                f", {len(untimed)} of them with a meeting that has no printed time"
                if untimed
                else ""
            )
            message = f"{ask}: {len(fits)} fit this plan's timetable{marked}."
        else:
            message = (
                f"{ask}, though none fits this plan's timetable, so see your advisor."
            )
        details: dict[str, Any] = {
            "credits": credits,
            "fits": list(fits),
            "untimed": list(untimed),
        }
        if place:
            details["owed"] = place.code
        return Reason(
            kind="included" if fits else "conditional",
            message=message,
            passage_id=passage,
            details=details,
        )

    def unchecked(self) -> Reason:
        return Reason(
            kind="conditional",
            message="This year's rules have no timetable, so SAGE couldn't check these plans "
            "for clashes. Check them with your advisor.",
            passage_id=self.faculty("FB3.4"),
        )

    def precedence(self, dropped: str, kept: str, repeated: bool) -> Reason:
        why = (
            "which you're repeating"
            if repeated
            else "which you still owe from an earlier year"
        )
        return Reason(
            kind="conflict",
            message=f"{dropped} clashes with {kept}, {why}, so it isn't in your plans: a "
            "repeated or earlier year's course comes first (FB3.4). See your advisor.",
            course_code=dropped,
            passage_id=self.faculty("FB3.4"),
        )

    def conflict(
        self,
        courses: Sequence[str],
        rules: Sequence[Need],
        floor: int | None,
        table: str | None,
    ) -> Reason:
        # The smallest set of requirements no plan can meet together. Courses alone conflict through
        # the timetable (FB3.4); otherwise the table of the year rule they break says what it asks.
        parts = [listed(courses)] if courses else []
        parts += [asked(rule) for rule in rules]
        if floor:
            parts.append(f"at least {floor} credits")
        passage = self.table(table)
        if not rules and not floor:
            passage = self.faculty("FB3.4")
        return Reason(
            kind="conflict",
            message=f"No plan can hold {all_of(parts)} together, so see your advisor.",
            passage_id=passage,
        )

    def nothing(self) -> Reason:
        return Reason(
            kind="conflict",
            message="None of the courses your year still needs can be taken yet, so there's no "
            "plan to list. See your advisor.",
        )

    def finished(self) -> Reason:
        return Reason(
            kind="conflict",
            message="Your record shows every year's core courses done, so there's no year "
            "left to plan. See your advisor.",
        )


def listed(codes: Sequence[str]) -> str:
    return all_of(sorted(codes))


def asked(rule: Need) -> str:
    # What a year rule still asks of her
    if rule.kind == "courses":
        return f"at least {rule.amount} of {listed(rule.courses)}"
    return f"at least {rule.amount} credits from {listed(rule.courses)}"
