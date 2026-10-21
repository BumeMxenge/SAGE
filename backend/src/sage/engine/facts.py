# The facts plans.lp reads for one student's year: the courses a plan may take, the year rules she
# still has to meet, each course's entry rule as her record leaves it, flattened into nodes, and her
# curriculum's meetings for those courses. Each requirement the solver may switch off, to trace a
# conflict, gets a switch.
from collections.abc import Iterable, Iterator
from datetime import time
from itertools import count
from typing import Literal

from sage.engine.evaluator import Plan, Record, Verdict, evaluate, leaf
from sage.shared.base import Row
from sage.shared.rules import (
    AllOf,
    AnyOf,
    CourseNeed,
    EntryRule,
    RuleSet,
    TimetableSlot,
    meetings_on,
)

# Where each term starts and ends in the year, so a course can follow one that ends before it starts.
# Winter falls between the semesters and summer after them. "Other", such as practical training, has
# no place in the year.
SPAN = {
    "q1": (1, 1),
    "q2": (2, 2),
    "sem1": (1, 2),
    "winter": (3, 3),
    "q3": (4, 4),
    "q4": (5, 5),
    "sem2": (4, 5),
    "full_year": (1, 5),
    "summer": (6, 6),
}


class Need(Row):
    # A year rule she still has to meet: so many more courses, or credits, from those that count
    kind: Literal["courses", "credits"]
    amount: int
    courses: tuple[str, ...]


class Problem(Row):
    # One student's year as the generator sets it out for the solver
    required: tuple[str, ...]  # the core she still owes and can take
    electives: tuple[str, ...] = ()
    needs: tuple[Need, ...] = ()
    floor: int = 0  # the credits the plan's courses must reach together


class Facts(Row):
    text: str
    switches: tuple[str, ...]  # each requirement's switch, as the facts name it


def take(code: str) -> str:
    # A required course's switch
    return f'take("{code}")'


def need(number: int) -> str:
    # A year rule's switch
    return f"rule({number})"


FLOOR = "floor"  # the credit minimum's switch


def facts(
    problem: Problem, rules: RuleSet, record: Record, extras: Iterable[str] = ()
) -> Facts:
    # The extras are courses to try beside a finished plan, for a slot's list
    credits = {course.code: course.credits for course in rules.courses}
    lines = [f'required("{code}").' for code in problem.required]
    lines += [f'elective("{code}").' for code in problem.electives]
    lines += [f'course("{code}", {credits[code]}).' for code in candidates(problem)]
    switches = [take(code) for code in problem.required]
    for number, rule in enumerate(problem.needs):
        lines.append(f"need({number}, {rule.kind}, {rule.amount}).")
        lines += [f'counts({number}, "{code}").' for code in rule.courses]
        switches.append(need(number))
    if problem.floor:
        lines.append(f"floor({problem.floor}).")
        switches.append(FLOOR)
    lines += [f"switch({switch})." for switch in switches]
    ids = count()
    for code, verdict in verdicts(problem, rules, record).items():
        if verdict.value == "open":
            node = next(ids)
            lines.append(f'entry("{code}", {node}).')
            plan = plan_for(code, problem, rules, record)
            lines += flatten(verdict.rest, node, ids, record, plan)
    for code in (*candidates(problem), *extras):
        lines += meetings(code, rules, record.curriculum)
    lines += [f'extra("{code}").' for code in extras]
    return Facts(text="\n".join(lines), switches=tuple(switches))


def candidates(problem: Problem) -> tuple[str, ...]:
    return (*problem.required, *problem.electives)


def verdicts(problem: Problem, rules: RuleSet, record: Record) -> dict[str, Verdict]:
    # Each candidate's entry rule as her record leaves it, where the plan's other courses can still
    # meet a leaf her record doesn't
    entry_rules = {course.code: course.entry_rule for course in rules.courses}
    return {
        code: evaluate(
            entry_rules[code], record, plan_for(code, problem, rules, record)
        )
        for code in candidates(problem)
    }


def plan_for(owner: str, problem: Problem, rules: RuleSet, record: Record) -> Plan:
    # The plan's courses that could meet a leaf of one course's rule: a co-requisite in a term that
    # starts no later than the course's, and a prerequisite in one that ends before it starts
    courses = {course.code: course for course in rules.courses}
    owner_span = SPAN.get(courses[owner].term)

    def plan(leaf_need: CourseNeed) -> tuple[str, ...]:
        if owner_span is None:
            return ()
        found = []
        for code in candidates(problem):
            span = SPAN.get(courses[code].term)
            if (
                code == owner
                or span is None
                or leaf_need.course not in record.covers(code, courses[code].credits)
            ):
                continue
            if leaf_need.need == "concurrent":
                in_time = span[0] <= owner_span[0]
            else:
                in_time = span[1] < owner_span[0]
            if in_time:
                found.append(code)
        return tuple(sorted(found))

    return plan


def flatten(
    rule: EntryRule, node: int, ids: Iterator[int], record: Record, plan: Plan
) -> Iterator[str]:
    # One node of a rule her record leaves open, and the nodes below it
    if isinstance(rule, AllOf | AnyOf):
        kind, children = (
            ("all", rule.all) if isinstance(rule, AllOf) else ("any", rule.any)
        )
        yield f"node({node}, {kind})."
        for child in children:
            below = next(ids)
            yield f"child({node}, {below})."
            yield from flatten(child, below, ids, record, plan)
        return
    # A leaf the plan may meet names the plan's courses that could. One her record decides only
    # comes in a failed branch of a list kept whole for its words, which can't hold either way, so
    # it writes nothing.
    value = leaf(rule, record, plan)
    if value == "unknown":
        yield f"unknown({node})."
    elif value in ("planned", "maybe"):
        for code in plan(rule):
            yield f'{value}({node}, "{code}").'


def meetings(code: str, rules: RuleSet, curriculum: str) -> Iterator[str]:
    # A course's meetings on her curriculum's timetable. A meeting with no printed day or time can't
    # clash, so only its alternative, if it has one, is written, and its course is untimed.
    for slot in meetings_on(rules, curriculum, code):
        if slot.choice_group:
            yield f'option("{code}", "{slot.choice_group}", "{slot.choice}").'
        if not placed(slot):
            yield f'untimed("{code}").'
            continue
        meeting = f'"{slot.id}"'
        yield (
            f'meeting({meeting}, "{code}", {slot.day}, {minutes(slot.start_time)}, '
            f"{minutes(slot.end_time)}, {slot.term})."
        )
        if slot.choice_group:
            yield f'alternative({meeting}, "{slot.choice_group}", "{slot.choice}").'


def untimed(code: str, rules: RuleSet, curriculum: str) -> bool:
    # Whether a meeting of the course on her timetable has no printed day or time
    return not all(placed(slot) for slot in meetings_on(rules, curriculum, code))


def placed(slot: TimetableSlot) -> bool:
    return None not in (slot.day, slot.start_time, slot.end_time)


def minutes(at: time) -> int:
    return at.hour * 60 + at.minute
