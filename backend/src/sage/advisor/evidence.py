# What Luna sees for one question, built as E4's evidence.py built it, on SAGE's own stores, rules and
# engine: her slice of the handbook, chosen by key, the plan context, and the three tools that serve
# the engine's facts. Passages and plans reach Luna by short ids, P01 and V01 upwards, which cost a
# few tokens where a UUID costs about 25, and which map back to their UUIDs.
from collections import defaultdict
from collections.abc import Sequence
from datetime import time
from typing import Any

from sage.shared.language_model import Tool, strict_object
from sage.shared.planning import EligibilityChecker
from sage.shared.repositories import StudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import Passage, RuleSet, TimetableSlot, meetings
from sage.shared.students import Chat, Plan, PlanCourse, PlanReason
from sage.shared.wording import in_words

DAYS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
# The weeks a meeting's term shows in, as the plan view's tabs: a quarter in its semester, a
# full-year course in both, and practical training's "other" in none
WEEKS: dict[str, tuple[str, ...]] = {
    "q1": ("sem1",),
    "q2": ("sem1",),
    "sem1": ("sem1",),
    "q3": ("sem2",),
    "q4": ("sem2",),
    "sem2": ("sem2",),
    "full_year": ("sem1", "sem2"),
    "winter": ("winter",),
    "summer": ("summer",),
    "other": (),
}
CODE = {"type": "string", "description": "A course code, such as EEE4118F"}
CODES = {"type": "array", "items": {"type": "string"}}


class Evidence:
    def __init__(
        self,
        chat: Chat,
        term: str | None,
        students: StudentRepository,
        rulebook: Rulebook,
        checker: EligibilityChecker,
    ) -> None:
        # Her plan set holds the chat's plans until semester check-ins exist, and its year is the
        # approved year the set was built from
        self.student = students.profile(chat.student_id)
        self.plan_set = students.current_plan_set(chat.student_id)
        self.record = students.record(chat.student_id)
        self.year = self.plan_set.plan_set.period
        self.rules = rulebook.year(self.year)
        self.symbols = rulebook.symbols()
        self.checker = checker
        self.term = term
        self.courses = {course.code: course for course in self.rules.courses}
        # Her plans, shown and hidden, by short id from their positions
        self.plans: dict[str, Plan] = {
            f"V{plan.position:02d}": plan
            for plan in sorted(self.plan_set.plans, key=lambda plan: plan.position)
        }
        self.plan_courses: dict[str, list[PlanCourse]] = {
            key: [row for row in self.plan_set.plan_courses if row.plan_id == plan.id]
            for key, plan in self.plans.items()
        }
        self.short = {plan.id: key for key, plan in self.plans.items()}
        # The plan she has open, or the pair she's comparing
        self.open = sorted(
            self.short[plan_id]
            for plan_id in (chat.plan_id, chat.other_plan_id)
            if plan_id
        )
        self.passages = self._slice()

    def _slice(self) -> dict[str, Passage]:
        # Her slice, chosen by key: her curriculum's passages, the entry of every course in her plan
        # set and her favourites, and every passage that names no course or curriculum, in handbook
        # order
        curriculum = self.student.curriculum_code
        courses = {row.course_code for row in self.plan_set.plan_courses}
        courses |= set(self.record.favourites)
        chosen = [
            passage
            for passage in self.rules.passages
            if passage.curriculum_code == curriculum
            or passage.course_code in courses
            or (passage.curriculum_code is None and passage.course_code is None)
        ]
        chosen.sort(key=lambda passage: (passage.source, passage.position))
        return {f"P{n:02d}": passage for n, passage in enumerate(chosen, start=1)}

    def slice_text(self) -> str:
        # The slice as Luna reads it: each source's passages under its name, each headed by its short
        # id, section and page, with the line breaks the PDF printed
        parts, source = [], None
        for key, passage in self.passages.items():
            if passage.source != source:
                source = passage.source
                parts.append(f"## {source}")
            parts.append(
                f"### {key} · {passage.section} · page {passage.page}\n{passage.content}"
            )
        return "\n\n".join(parts)

    def context(self) -> str:
        # What her message carries before the question: who she is, the open plan or the pair, each
        # with its week, the plan set's reasons that cover them, and the term on screen. Nothing that
        # identifies her.
        student = self.student
        curriculum = next(
            row for row in self.rules.curricula if row.code == student.curriculum_code
        )
        open_ids = {self.plans[key].id for key in self.open}
        # The set's own reasons first, then the open plans'
        reasons = [
            self._reason(reason)
            for reason in sorted(
                self.plan_set.plan_reasons,
                key=lambda reason: reason.plan_id is not None,
            )
            if reason.plan_id is None or reason.plan_id in open_ids
        ]
        about = (
            "About the student\n"
            f"- Curriculum: {curriculum.code}, {curriculum.name}\n"
            f"- First registered: {student.intake_year}\n"
            f"- Planning for: {self.year}\n"
            f"- Term on screen: {self.term or 'none'}"
        )
        heading = (
            "Open plan" if len(self.open) == 1 else "Open plans, compared side by side"
        )
        return "\n\n".join(
            [
                about,
                f"{heading}\n" + "\n\n".join(self._plan(key) for key in self.open),
                "Reasons behind the plan set\n" + "\n".join(reasons),
            ]
        )

    def _reason(self, reason: PlanReason) -> str:
        # In a comparison, a plan's own reason is named with its plan, as each says "this plan". Only
        # a complementary slot's reason has details. Under it go the approved courses that fit the
        # plan's timetable, marked as its details mark them: the engine's facts, as the plan's
        # meetings are, so Luna may name them without a citation.
        owner = ""
        if len(self.open) == 2 and reason.plan_id is not None:
            key = self.short[reason.plan_id]
            owner = f"{key} {self.plans[key].name}: "
        lines = [f"- {owner}{reason.message}"]
        if reason.details:
            details = reason.details
            for code in details["fits"]:
                marks = []
                if code in details["untimed"]:
                    marks.append("a meeting with no printed time")
                if code in details["fewer_credits"]:
                    marks.append(f"worth fewer than {details['credits']} credits")
                course = f"  - {code} {self.courses[code].name}"
                lines.append(f"{course}: {', '.join(marks)}" if marks else course)
        return "\n".join(lines)

    def _plan(self, key: str) -> str:
        plan = self.plans[key]
        shown = "hidden from" if plan.hidden else "shown in"
        lines = [f"{key} {plan.name}, {shown} the plan list"]
        for row in self.plan_courses[key]:
            course = self.courses[row.course_code]
            meets = meeting_words(row, self.rules, self.student.curriculum_code)
            lines.append(
                f"- {course.code} {course.name}: {course.credits} credits, {course.term}. {meets}"
            )
        lines += week_words(
            self.plan_courses[key], self.rules, self.student.curriculum_code
        )
        return "\n".join(lines)

    def tools(self) -> list[Tool]:
        # The tools the engine serves, described as E4 described them
        year = self.year
        return [
            Tool(
                name="get_course",
                description=(
                    f"A course in the {year} handbook: its name, credits, NQF level, term, "
                    "convener and entry requirement, in plain words."
                ),
                parameters=strict_object(code=CODE),
            ),
            Tool(
                name="find_plan",
                description=(
                    f"The student's {year} plans, shown and hidden, that have every course in "
                    "have and none in avoid. Each comes with its id, its name, whether it's hidden "
                    "from their plan list, and its courses. When none matches, it gives the "
                    "reasons behind their plan set instead. Either list may be empty, but not both."
                ),
                parameters=strict_object(
                    have={**CODES, "description": "Course codes the plan must have"},
                    avoid={
                        **CODES,
                        "description": "Course codes the plan must not have",
                    },
                ),
            ),
            Tool(
                name="check_eligibility",
                description=(
                    f"Whether the student may take a course in {year}, from their record and the "
                    f"{year} rules: eligible, check (they must check with their advisor first) or "
                    "not_eligible, with what to tell them."
                ),
                parameters=strict_object(code=CODE),
            ),
        ]

    def run(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        # A tool call as Luna made it. Strict schemas hold its name and arguments to the tools'.
        tool = {
            "get_course": self.get_course,
            "find_plan": self.find_plan,
            "check_eligibility": self.check_eligibility,
        }[name]
        return tool(**arguments)

    def get_course(self, code: str) -> dict[str, Any]:
        course = self.courses.get(code.strip().upper())
        if course is None:
            return self._missing(code)
        return {
            "code": course.code,
            "name": course.name,
            "credits": course.credits,
            "nqf_level": course.nqf_level,
            "term": course.term,
            "convener": course.convener,
            "entry_requirement": in_words(course.entry_rule),
        }

    def find_plan(self, have: list[str], avoid: list[str]) -> dict[str, Any]:
        wanted = {code.strip().upper() for code in have}
        unwanted = {code.strip().upper() for code in avoid}
        if not wanted and not unwanted:
            return {"error": "Name at least one course to have or to avoid."}
        found = []
        for key, plan in self.plans.items():
            codes = [row.course_code for row in self.plan_courses[key]]
            if wanted <= set(codes) and not unwanted & set(codes):
                found.append(
                    {
                        "plan": key,
                        "name": plan.name,
                        "hidden": plan.hidden,
                        "courses": codes,
                    }
                )
        if found:
            return {"plans": found}
        reasons = [
            reason.message
            for reason in self.plan_set.plan_reasons
            if reason.plan_id is None
        ]
        return {"plans": [], "reasons": reasons}

    def check_eligibility(self, code: str) -> dict[str, Any]:
        course = self.courses.get(code.strip().upper())
        if course is None:
            return self._missing(code)
        verdicts = self.checker.check(
            [course], self.record.course_history, self.rules, self.symbols, self.student
        )
        return verdicts[course.code].model_dump(mode="json")

    def _missing(self, code: str) -> dict[str, Any]:
        return {"error": f"No course {code} in the {self.year} handbook."}


def meeting_words(course: PlanCourse, rules: RuleSet, curriculum: str) -> str:
    # A course's meetings in a plan, as the plan view shows them: those she attends, then each choice
    # group with more than one alternative left, of which she attends one. An alternative can meet
    # more than once, as CSC3002F's practical pairs of days do.
    slots = meetings(course, rules, curriculum)
    groups: dict[str, dict[str, list[TimetableSlot]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for slot in slots:
        if slot.choice_group is not None:
            groups[slot.choice_group][slot.choice or ""].append(slot)
    attended = [
        slot
        for slot in slots
        if slot.choice_group is None or len(groups[slot.choice_group]) == 1
    ]
    words = []
    if attended:
        words.append(f"Meets {', '.join(_labelled(slot) for slot in attended)}.")
    for group, alternatives in groups.items():
        if len(alternatives) > 1:
            listed = " or ".join(
                f"{choice} ({', '.join(_when(slot) for slot in met)})"
                for choice, met in alternatives.items()
            )
            words.append(f"Attends one {group}: {listed}.")
    return " ".join(words) or "No meetings in the timetable."


def week_words(
    courses: Sequence[PlanCourse], rules: RuleSet, curriculum: str
) -> list[str]:
    # A plan's week in each term it meets, as the plan view draws it: each day's meetings in time
    # order with their course codes, one with a day but no time last, and an alternative of a group
    # with more than one left marked as one of its choices. Meetings with no printed day follow.
    weeks: dict[str, dict[int | None, list[tuple[TimetableSlot, str]]]] = {
        week: defaultdict(list) for week in ("sem1", "sem2", "winter", "summer")
    }
    for course in courses:
        slots = meetings(course, rules, curriculum)
        groups: dict[str, set[str | None]] = defaultdict(set)
        for slot in slots:
            if slot.choice_group is not None:
                groups[slot.choice_group].add(slot.choice)
        for slot in slots:
            choices = (
                groups[slot.choice_group] if slot.choice_group is not None else set()
            )
            notes = []
            if len(choices) > 1:
                notes.append(
                    f"one of {len(choices)} {slot.choice_group} choices: {slot.choice}"
                )
            elif slot.kind:
                notes.append(slot.kind)
            if slot.term.startswith("q"):
                notes.append(slot.term.upper())
            hours = (
                f"{slot.start_time:%H:%M} to {slot.end_time:%H:%M}"
                if slot.start_time and slot.end_time
                else "at no printed time"
            )
            words = f"{course.course_code} {hours}"
            if notes:
                words += f" ({', '.join(notes)})"
            for week in WEEKS[slot.term]:
                weeks[week][slot.day].append((slot, words))
    lines = []
    for week, days in weeks.items():
        if not days:
            continue
        lines.append(f"Week in {week}, day by day")
        for day in sorted(day for day in days if day is not None):
            met = sorted(
                days[day],
                key=lambda item: (
                    item[0].start_time or time.max,
                    item[0].end_time or time.max,
                ),
            )
            lines.append(f"- {DAYS[day]}: {', '.join(words for _, words in met)}")
        if None in days:
            undated = ", ".join(words for _, words in days[None])
            lines.append(f"- No printed day: {undated}")
    return lines


def _labelled(slot: TimetableSlot) -> str:
    return f"{_when(slot)} ({slot.kind})" if slot.kind else _when(slot)


def _when(slot: TimetableSlot) -> str:
    # A meeting's day and hours, as far as the timetable or the handbook prints them
    day = DAYS[slot.day] if slot.day else None
    hours = (
        f"{slot.start_time:%H:%M} to {slot.end_time:%H:%M}"
        if slot.start_time and slot.end_time
        else None
    )
    if day and hours:
        return f"{day} {hours}"
    if day:
        return f"{day}, at no printed time"
    if hours:
        return f"{hours}, on no printed day"
    return "at no printed day or time"
