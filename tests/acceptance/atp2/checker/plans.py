# What SEMANTICS.md says the engine decides for one student, worked out by brute force: her year of
# study, her owed and excluded core, every valid plan as a set of course codes, each plan's slots
# and every course's status. It reads the approved year through shared/'s types alone and imports
# nothing from the engine, so the two can agree only by following the same specification.
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations

from checker.entry import Context, value
from checker.record import DONE, FAILED, PASSED, Covers, Record
from checker.week import Week, schedulable, weeks
from sage.shared.rules import (
    COMPLEMENTARY,
    AllOfGroup,
    ChooseFromGroup,
    CreditsFromGroups,
    ResultSymbol,
    RuleSet,
    TotalCredits,
    YearRule,
)
from sage.shared.students import CourseHistoryLine, Student

# The 576-credit curriculum's places for ASL1200S and CON2026S, by the year whose footnote marks
# each (576-credit places)
PLACES = {
    "EB009EEE01": {"ASL1200S": 1, "CON2026S": 1},
    "EB022EEE02": {"ASL1200S": 1, "CON2026S": 1},
    "EB011EEE05": {"ASL1200S": 2, "CON2026S": 2},
    "EB809EEE01": {"ASL1200S": 3, "CON2026S": 2},
    "EB811EEE05": {"ASL1200S": 3, "CON2026S": 2},
    "EB822EEE02": {"ASL1200S": 3, "CON2026S": 2},
}
PLACE_CREDITS = (
    8  # a place takes one approved complementary course of at least 8 credits
)
# Each curriculum's opening page gives 560 credits for a candidate who registers in 2025, and 576
# for one who registered before
FIRST_560 = 2025
STATUSES = {True: "eligible", None: "check", False: "not_eligible"}
NO_MEETINGS = Week()


@dataclass(frozen=True)
class Slot:
    credits: int
    owed: str | None  # the course a 576-credit place stands in for
    fits: frozenset[str]


@dataclass(frozen=True)
class Checked:
    year: int  # her year of study, past the final year once every year is complete
    statuses: dict[str, str]  # every course the year holds, judged outside a plan
    # Her outstanding core from her year and earlier, before any is left out
    outstanding: frozenset[str] = frozenset()
    owed: frozenset[str] = frozenset()  # her plans' core from earlier years
    excluded: frozenset[str] = frozenset()  # core left out by its entry rule
    dropped: frozenset[str] = frozenset()  # current-year core left out by FB3.4
    clash: bool = False  # core that clashes however its sections are chosen, so no plan
    plans: tuple[frozenset[str], ...] = ()
    slots: dict[frozenset[str], tuple[Slot, ...]] = field(default_factory=dict)
    judged: dict[frozenset[str], frozenset[str]] = field(default_factory=dict)
    groups: frozenset[str] = (
        frozenset()
    )  # the courses in the groups her year's rules name
    candidates: int = 0  # the subsets of her open choices tried


class Curriculum:
    # Her curriculum's tables in the year's rules
    def __init__(self, rules: RuleSet, code: str) -> None:
        self.members: dict[str, set[str]] = defaultdict(set)
        for member in rules.course_group_members:
            self.members[member.group_key].add(member.course_code)
        self.years = {
            row.year_of_study: row.rule.all
            for row in rules.curriculum_rules
            if row.curriculum_code == code
        }
        self.final = max(self.years)

    def named(self, rule: YearRule) -> set[str]:
        # The courses in the groups a year rule names
        match rule:
            case AllOfGroup():
                return self.members[rule.all_of_group]
            case ChooseFromGroup():
                return self.members[rule.from_group]
            case CreditsFromGroups():
                return set().union(*(self.members[g] for g in rule.from_groups))
        return set()

    def core(self, year: int) -> set[str]:
        # The year's core, less practical training (X courses), which is never a plan member and
        # doesn't count towards her year
        return {
            code
            for rule in self.years[year]
            if isinstance(rule, AllOfGroup)
            for code in self.members[rule.all_of_group]
            if not code.endswith("X")
        }


def year_of_study(core: Mapping[int, set[str]], done: Callable[[str], bool]) -> int:
    # FB5 (p. 14) as SEMANTICS.md reads it: the latest year from which she has passed at least
    # two core courses, or the year after it when that year's core is complete, and never earlier
    # than her lowest unfinished year. Nothing passed gives year 1.
    complete = {year: all(map(done, codes)) for year, codes in core.items()}
    latest = max(
        (year for year, codes in core.items() if sum(map(done, codes)) >= 2), default=0
    )
    reached = latest + 1 if latest and complete[latest] else max(latest, 1)
    lowest = min((year for year in core if not complete[year]), default=max(core) + 1)
    return max(reached, lowest)


def check(
    student: Student,
    history: Sequence[CourseHistoryLine],
    rules: RuleSet,
    symbols: Mapping[str, ResultSymbol],
) -> Checked:
    curriculum = student.curriculum_code
    tables = Curriculum(rules, curriculum)
    courses = {course.code: course for course in rules.courses}
    covers = Covers(rules)
    planned = {code: covers(code, course.credits) for code, course in courses.items()}
    record = Record(history, covers, symbols)
    week = weeks(rules, curriculum)

    def done(code: str) -> bool:
        return record.has(code, DONE)

    def credit(codes: Iterable[str]) -> int:
        return sum(courses[code].credits for code in codes)

    def holds(code: str, plan: set[str]) -> bool | None:
        # A course's rule inside a plan, whose other courses stand in for passes
        rule = courses[code].entry_rule
        if rule is None:
            return True
        others = tuple((planned[p], courses[p].term) for p in plan if p != code)
        return value(
            rule, Context(record, curriculum, year, courses[code].term, others)
        )

    def apart(codes: Iterable[str]) -> bool:
        return schedulable([week.get(code, NO_MEETINGS) for code in codes])

    core = {year: tables.core(year) for year in tables.years}
    year = year_of_study(core, done)
    outside = Context(record, curriculum, year)
    statuses = {
        code: "not_eligible" if done(code) else STATUSES[value(c.entry_rule, outside)]
        for code, c in courses.items()
    }
    if year > tables.final:
        return Checked(year=year, statuses=statuses)  # every year complete: no plan

    years = range(1, year + 1)
    outstanding = {code for y in years for code in core[y] if not done(code)}
    owed = {code for y in years if y < year for code in core[y] if not done(code)}

    # Her year's choose and credits rules, with each earlier year's she hasn't met (Owed rules).
    # Each holds what it asks for, its courses, and what her passes already give, each line once.
    choose: list[tuple[int, set[str], int]] = []
    credits: list[tuple[int, set[str], int]] = []
    lines: list[
        tuple[int, int]
    ] = []  # each complementary line, as its year and credits
    for y in years:
        for rule in tables.years[y]:
            group = tables.named(rule)
            if isinstance(rule, ChooseFromGroup):
                have = len(record.matched(group))
                if y == year or have < rule.choose:
                    choose.append((rule.choose, group, have))
            elif isinstance(rule, CreditsFromGroups):
                if rule.from_groups == (COMPLEMENTARY,):
                    lines.append((y, rule.credits))
                    continue
                have = credit(record.matched(group))
                if y == year or have < rule.credits:
                    credits.append((rule.credits, group, have))
    choices = sorted(
        {code for _, group, _ in choose + credits for code in group if not done(code)}
    )

    # Her passed approved complementary courses fill her lines first, one a line and earliest
    # first, and each one left over fills an owed 576-credit place, earliest place first
    taken = len(record.matched(tables.members[COMPLEMENTARY]))
    filled, unfilled = lines[:taken], lines[taken:]
    places = PLACES[curriculum] if student.intake_year < FIRST_560 else {}
    owing = sorted(
        (y, code) for code, y in places.items() if y <= year and not done(code)
    )
    owed_places = [code for _, code in owing[max(0, taken - len(lines)) :]]
    slot_credits = sum(c for _, c in unfilled) + PLACE_CREDITS * len(owed_places)

    # A core course whose rule no plan can meet is left out, and so is any course that then can't
    # be taken, until nothing changes. Then FB3.4 (pp. 13 and 14) leaves out each current-year
    # course that clashes with a repeated course (one with a failed line) or one in arrears, and
    # the exclusions run again.
    kept, excluded, dropped = set(outstanding), set(), set()
    while True:
        possible = set(choices)
        while True:
            plan = kept | possible
            out = {code for code in plan if holds(code, plan) is False}
            if not out:
                break
            excluded |= out & kept
            kept -= out
            possible -= out
        first = {code for code in kept if code in owed or record.has(code, FAILED)}
        clashing = {
            code
            for code in kept - first
            if any(not apart((code, other)) for other in first)
        }
        if not clashing:
            break
        dropped |= clashing
        kept -= clashing
    clash = not apart(kept)

    # The credit minimum: her year's printed total, less her courses of that year she has passed,
    # each of its complementary lines already filled and its core left out; at least the core's
    # credits; and in her final year at least the degree's total less the credits she has passed
    now = tables.years[year]
    printed = next(rule.total_credits for rule in now if isinstance(rule, TotalCredits))
    this_year = {code for rule in now for code in tables.named(rule)}
    this_year -= tables.members[COMPLEMENTARY]
    core_credits = credit(kept)
    minimum = max(
        printed
        - credit(code for code in this_year if done(code))
        - sum(c for y, c in filled if y == year)
        - credit((excluded | dropped) & core[year]),
        core_credits,
    )
    if year == tables.final:
        degree = 576 if student.intake_year < FIRST_560 else 560
        passed = sum(line.credits for line in record.lines if line.outcome in PASSED)
        minimum = max(minimum, degree - passed)

    def meets(electives: set[str]) -> bool:
        # Every joined choose and credits rule, and the credit minimum, which slots count towards
        return (
            all(have + len(electives & group) >= n for n, group, have in choose)
            and all(have + credit(electives & group) >= n for n, group, have in credits)
            and core_credits + credit(electives) + slot_credits >= minimum
        )

    def valid(electives: set[str]) -> bool:
        if not meets(electives) or any(meets(electives - {e}) for e in electives):
            return False  # a rule unmet, or a spare elective
        plan = kept | electives
        return all(holds(code, plan) is not False for code in plan) and apart(plan)

    plans, candidates = [], 0
    if not clash:
        for size in range(len(choices) + 1):
            for chosen in combinations(choices, size):
                candidates += 1
                if valid(set(chosen)):
                    plans.append(frozenset(kept.union(chosen)))

    # Each slot lists the approved complementary courses that fit the plan's timetable when that
    # one course is added, leaving out any she has passed or a pass covers, or whose rule she
    # doesn't meet (Slots)
    slots, judged = {}, {}
    for plan in plans:
        fits = frozenset()
        if unfilled or owed_places:
            fits = frozenset(
                code
                for code in tables.members[COMPLEMENTARY]
                if not record.has(code, PASSED)
                and holds(code, plan | {code}) is not False
                and apart(plan | {code})
            )
        slots[plan] = (
            *(Slot(c, None, fits) for _, c in unfilled),
            *(
                Slot(
                    PLACE_CREDITS,
                    code,
                    frozenset(f for f in fits if courses[f].credits >= PLACE_CREDITS),
                )
                for code in owed_places
            ),
        )
        judged[plan] = frozenset(
            code
            for code in plan
            if holds(code, plan) is None or week.get(code, NO_MEETINGS).untimed
        )
    return Checked(
        year=year,
        statuses=statuses,
        outstanding=frozenset(outstanding),
        owed=frozenset(owed & kept),
        excluded=frozenset(excluded),
        dropped=frozenset(dropped),
        clash=clash,
        plans=tuple(sorted(plans, key=sorted)),
        slots=slots,
        judged=judged,
        groups=frozenset(code for rule in now for code in tables.named(rule)),
        candidates=candidates,
    )
