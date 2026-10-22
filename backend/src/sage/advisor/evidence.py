# What Luna sees for one question, built as E4's evidence.py built it, on SAGE's own stores, rules and
# engine: her slice of the handbook, chosen by key, the plan context, and the three tools that serve
# the engine's facts. Passages and plans reach Luna by short ids, P01 and V01 upwards, which cost a
# few tokens where a UUID costs about 25, and which map back to their UUIDs.
from collections import defaultdict
from typing import Any

from sage.shared.language_model import Tool, strict_object
from sage.shared.planning import EligibilityChecker
from sage.shared.repositories import StudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import Passage, RuleSet, TimetableSlot, meetings
from sage.shared.students import Chat, Plan, PlanCourse
from sage.shared.wording import in_words

DAYS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
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
        short = {plan.id: key for key, plan in self.plans.items()}
        # The plan she has open, or the pair she's comparing
        self.open = sorted(
            short[plan_id] for plan_id in (chat.plan_id, chat.other_plan_id) if plan_id
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
        # What her message carries before the question: who she is, the open plan or the pair, the
        # plan set's reasons that cover them, and the term on screen. Nothing that identifies her.
        student = self.student
        curriculum = next(
            row for row in self.rules.curricula if row.code == student.curriculum_code
        )
        open_ids = {self.plans[key].id for key in self.open}
        # The set's own reasons first, then the open plans'
        reasons = [
            f"- {reason.message}"
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
