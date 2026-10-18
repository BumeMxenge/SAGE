# The questionnaire that narrows a long plan set. Its questions are built from the set itself rather
# than typed in, and each option carries the plans it keeps, so the frontend can grey out options
# that would leave nothing. Answering hides the plans the answers don't keep, and never deletes one.
from collections import defaultdict
from collections.abc import Collection
from datetime import time
from typing import Any, Literal
from uuid import UUID

from sage.features.plans import service as plans
from sage.shared.base import Row
from sage.shared.errors import (
    NoPlanMatches,
    QuestionnaireAnswered,
    QuestionnaireNotNeeded,
    UnknownAnswer,
)
from sage.shared.repositories import StudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import RuleSet, TimetableSlot
from sage.shared.students import PlanSetRows, Student

QuestionId = Literal["course", "week"]
EIGHT = time(8, 0)
LUNCH = (time(13, 0), time(13, 45))


class Option(Row):
    id: str
    label: str
    hearted: bool = False
    keeps: tuple[UUID, ...]  # the plans this answer keeps


class Question(Row):
    id: QuestionId
    prompt: str
    hint: str | None = None
    options: tuple[Option, ...]


def current(
    students: StudentRepository, rulebook: Rulebook, student: Student
) -> tuple[Question, ...] | None:
    # Her questions, or None when her current set doesn't need them
    rows = students.current_plan_set(student.id)
    if rows is None or not plans.questionnaire_needed(rows):
        return None
    rules = rulebook.year(rows.plan_set.period)
    favourites = students.record(student.id).favourites
    return questions(rows, rules, student.curriculum_code, favourites)


def answer(
    students: StudentRepository,
    rulebook: Rulebook,
    student: Student,
    answers: dict[str, Any],
) -> None:
    rows = students.current_plan_set(student.id)
    if rows is not None and rows.plan_set.answers is not None:
        raise QuestionnaireAnswered()
    if rows is None or not plans.questionnaire_needed(rows):
        raise QuestionnaireNotNeeded()
    rules = rulebook.year(rows.plan_set.period)
    options = {
        question.id: {option.id: option.keeps for option in question.options}
        for question in questions(rows, rules, student.curriculum_code, ())
    }
    # The plans every answer keeps. A question left unanswered keeps them all.
    kept = {plan.id for plan in rows.plans}
    for question, option in answers.items():
        if option not in options[question]:
            raise UnknownAnswer(f"{option} isn't one of the options for {question}.")
        kept &= set(options[question][option])
    if not kept:
        raise NoPlanMatches()
    # The answers go last, so a failure after hiding leaves the questionnaire open to answer again
    students.hide_plans(student.id, rows.plan_set.id, keep=kept)
    students.save_answers(student.id, rows.plan_set.id, answers)


def questions(
    rows: PlanSetRows, rules: RuleSet, curriculum: str, favourites: Collection[str]
) -> tuple[Question, ...]:
    everyone = tuple(plan.id for plan in rows.plans)
    by_plan = plans.courses(rows, rules)
    holding: dict[str, list[UUID]] = defaultdict(list)
    for plan in rows.plans:
        for course in by_plan[plan.id]:
            holding[course.code].append(plan.id)
    names = {course.code: course.name for course in rules.courses}
    choosable = [code for code, ids in holding.items() if len(ids) < len(everyone)]
    course = Question(
        id="course",
        prompt="Is there a course you already know you want?",
        hint="Only plans that include it stay in.",
        options=(
            *(
                Option(
                    id=code,
                    label=names[code],
                    hearted=code in favourites,
                    keeps=tuple(holding[code]),
                )
                for code in sorted(
                    choosable, key=lambda code: (code not in favourites, code)
                )
            ),
            Option(id="no_preference", label="No strong preference", keeps=everyone),
        ),
    )

    weeks = {
        plan.id: known_meetings(rows, plan.id, rules, curriculum) for plan in rows.plans
    }
    eights = {
        plan_id: sum(meeting.start_time == EIGHT for meeting in week)
        for plan_id, week in weeks.items()
    }
    least = min(eights.values())
    fewest = tuple(plan_id for plan_id in everyone if eights[plan_id] == least)
    lunch_free = tuple(
        plan_id
        for plan_id in everyone
        if not any(
            meeting.start_time < LUNCH[1] and meeting.end_time > LUNCH[0]
            for meeting in weeks[plan_id]
        )
    )
    week = Question(
        id="week",
        prompt="How should the week feel?",
        options=(
            # Offered only when they'd narrow the set without emptying it
            *(
                Option(id=option_id, label=label, keeps=keeps)
                for option_id, label, keeps in (
                    ("fewest_8am", "Fewest 8am starts", fewest),
                    ("lunch_free", "Keep the 13:00 lunch hour free", lunch_free),
                )
                if 0 < len(keeps) < len(everyone)
            ),
            Option(id="no_preference", label="No preference", keeps=everyone),
        ),
    )
    return course, week


def known_meetings(
    rows: PlanSetRows, plan_id: UUID, rules: RuleSet, curriculum: str
) -> list[TimetableSlot]:
    # The plan's meetings that are certain and placed: an alternative not yet chosen, or a meeting
    # with no day or time printed, counts towards neither week option
    known = []
    for course in rows.plan_courses:
        if course.plan_id != plan_id:
            continue
        chosen = course.choices or {}
        known += [
            meeting
            for meeting in plans.meetings(course, rules, curriculum)
            if (meeting.choice_group is None or meeting.choice_group in chosen)
            and meeting.day is not None
            and meeting.start_time is not None
        ]
    return known
