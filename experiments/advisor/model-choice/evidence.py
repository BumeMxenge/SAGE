# The evidence both models get, built from Mbali's seed and the approved 2026 with no engine: her
# slice of the handbook, the plan context, and the three tools the engine will serve. Passages and
# plans reach the models by short ids, P01 upwards and V01 to V10, which cost a few tokens where a
# UUID costs about 25, and which the harness maps back.
from collections.abc import Mapping, Sequence
from uuid import UUID

from sage.engine.stubs import UNCHECKED
from sage.ingestion.ingest import approved_snapshot
from sage.shared.planning import Eligibility
from sage.shared.rules import Passage
from sage.shared.seed import SEED_FILE, load_seed
from sage.shared.students import Plan
from sage.shared.wording import in_words

YEAR = 2026
# A made-up account for the seed's ids, as no real account is involved
ACCOUNT = UUID(int=4)
DAYS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}

RULES = approved_snapshot(YEAR).rules
STUDENT = load_seed(SEED_FILE, ACCOUNT)
COURSES = {course.code: course for course in RULES.courses}

# Her plans by short id, from their positions, which match the seed's keys
PLANS: dict[str, Plan] = {
    f"V{plan.position:02d}": plan
    for plan in sorted(STUDENT.plans, key=lambda plan: plan.position)
}
PLAN_COURSES: dict[str, tuple[str, ...]] = {
    key: tuple(
        row.course_code for row in STUDENT.plan_courses if row.plan_id == plan.id
    )
    for key, plan in PLANS.items()
}
IN_PLANS = {code for codes in PLAN_COURSES.values() for code in codes}


def _slice() -> dict[str, Passage]:
    # Her slice, chosen by key: her curriculum's passages, the entry of every course in her plans
    # and favourites, and every passage that names no course or curriculum, in handbook order
    curriculum = STUDENT.student.curriculum_code
    courses = IN_PLANS | {row.course_code for row in STUDENT.favourites}
    chosen = [
        passage
        for passage in RULES.passages
        if passage.curriculum_code == curriculum
        or passage.course_code in courses
        or (passage.curriculum_code is None and passage.course_code is None)
    ]
    chosen.sort(key=lambda passage: (passage.source, passage.position))
    return {f"P{n:02d}": passage for n, passage in enumerate(chosen, start=1)}


PASSAGES = _slice()
# Each passage's short id by its section, which the labels name passages by
SECTIONS = {passage.section: key for key, passage in PASSAGES.items()}
if len(SECTIONS) != len(PASSAGES):
    raise ValueError(
        "Two passages in the slice share a section, so a label can't name one"
    )


def slice_text() -> str:
    # The slice as the models read it: each source's passages under its name, each headed by its
    # short id, section and page, with the line breaks the PDF printed
    parts, source = [], None
    for key, passage in PASSAGES.items():
        if passage.source != source:
            source = passage.source
            parts.append(f"## {source}")
        parts.append(
            f"### {key} · {passage.section} · page {passage.page}\n{passage.content}"
        )
    return "\n\n".join(parts)


# The curricula a meeting is only for, where the timetable names some
ONLY_FOR: dict[UUID, set[str]] = {}
for row in RULES.timetable_slot_curricula:
    ONLY_FOR.setdefault(row.slot_id, set()).add(row.curriculum_code)


def _meetings(code: str) -> str:
    # A course's meetings that her curriculum attends: a slot that names no curricula is for all
    curriculum = STUDENT.student.curriculum_code
    slots = sorted(
        (
            slot
            for slot in RULES.timetable_slots
            if slot.course_code == code
            and curriculum in ONLY_FOR.get(slot.id, {curriculum})
        ),
        key=lambda slot: (slot.day, slot.start_time),
    )
    if not slots:
        return "No meetings in the timetable."
    times = [f"{DAYS[s.day]} {s.start_time:%H:%M} to {s.end_time:%H:%M}" for s in slots]
    return f"Meets {', '.join(times)}."


def _plan(key: str) -> str:
    plan = PLANS[key]
    shown = "hidden from" if plan.hidden else "shown in"
    lines = [f"{key} {plan.name}, {shown} the plan list"]
    for code in PLAN_COURSES[key]:
        course = COURSES[code]
        lines.append(
            f"- {code} {course.name}: {course.credits} credits, {course.term}. {_meetings(code)}"
        )
    return "\n".join(lines)


def context(plans: Sequence[str], term: str) -> str:
    # What the student's message carries before the question: who she is, the open plan or the
    # pair, the plan set's reasons that cover them, and the term on screen
    student = STUDENT.student
    curriculum = next(
        row for row in RULES.curricula if row.code == student.curriculum_code
    )
    (plan_set,) = STUDENT.plan_sets
    open_ids = {PLANS[key].id for key in plans}
    reasons = [
        f"- {reason.message}"
        for reason in STUDENT.plan_reasons
        if reason.plan_id is None or reason.plan_id in open_ids
    ]
    about = (
        "About the student\n"
        f"- Curriculum: {curriculum.code}, {curriculum.name}\n"
        f"- First registered: {student.intake_year}\n"
        f"- Planning for: {plan_set.period}\n"
        f"- Term on screen: {term}"
    )
    heading = "Open plan" if len(plans) == 1 else "Open plans, compared side by side"
    return "\n\n".join(
        [
            about,
            f"{heading}\n" + "\n\n".join(_plan(key) for key in plans),
            "Reasons behind the plan set\n" + "\n".join(reasons),
        ]
    )


def strict_object(**properties: dict) -> dict:
    # An object with exactly these properties, all required, as strict tools need on both APIs
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


CODE = {"type": "string", "description": "A course code, such as EEE4118F"}
CODES = {"type": "array", "items": {"type": "string"}}
# The tools the engine will serve, in one form both adapters turn into their own
TOOLS = [
    {
        "name": "get_course",
        "description": (
            f"A course in the {YEAR} handbook: its name, credits, NQF level, term, convener "
            "and entry requirement, in plain words."
        ),
        "schema": strict_object(code=CODE),
    },
    {
        "name": "find_plan",
        "description": (
            f"The student's {YEAR} plans, shown and hidden, that have every course in have "
            "and none in avoid. Each comes with its id, its name, whether it's hidden from "
            "their plan list, and its courses. When none matches, it gives the reasons "
            "behind their plan set instead. Either list may be empty, but not both."
        ),
        "schema": strict_object(
            have={**CODES, "description": "Course codes the plan must have"},
            avoid={**CODES, "description": "Course codes the plan must not have"},
        ),
    },
    {
        "name": "check_eligibility",
        "description": (
            f"Whether the student may take a course in {YEAR}, from their record and the "
            f"{YEAR} rules: eligible, check (they must check with their advisor first) or "
            "not_eligible, with what to tell them."
        ),
        "schema": strict_object(code=CODE),
    },
]


def _missing(code: str) -> dict:
    return {"error": f"No course {code} in the {YEAR} handbook."}


def get_course(code: str) -> dict:
    course = COURSES.get(code.strip().upper())
    if course is None:
        return _missing(code)
    return {
        "code": course.code,
        "name": course.name,
        "credits": course.credits,
        "nqf_level": course.nqf_level,
        "term": course.term,
        "convener": course.convener,
        "entry_requirement": in_words(course.entry_rule),
    }


def find_plan(have: Sequence[str], avoid: Sequence[str]) -> dict:
    wanted = {code.strip().upper() for code in have}
    unwanted = {code.strip().upper() for code in avoid}
    if not wanted and not unwanted:
        return {"error": "Name at least one course to have or to avoid."}
    found = [
        {
            "plan": key,
            "name": plan.name,
            "hidden": plan.hidden,
            "courses": list(PLAN_COURSES[key]),
        }
        for key, plan in PLANS.items()
        if wanted <= set(PLAN_COURSES[key]) and not unwanted & set(PLAN_COURSES[key])
    ]
    if found:
        return {"plans": found}
    reasons = [
        reason.message for reason in STUDENT.plan_reasons if reason.plan_id is None
    ]
    return {"plans": [], "reasons": reasons}


def check_eligibility(code: str, verdicts: Mapping[str, Eligibility]) -> dict:
    # The stand-in for the engine's check: a course in a valid plan is eligible, and every other
    # course has the verdict I wrote from print, or else the interim stand-in's "check"
    code = code.strip().upper()
    if code in IN_PLANS:
        verdict = Eligibility(status="eligible")
    elif code in verdicts:
        verdict = verdicts[code]
    elif code in COURSES:
        verdict = Eligibility(status="check", reason=UNCHECKED)
    else:
        return _missing(code)
    return verdict.model_dump(mode="json")


def run_tool(name: str, arguments: dict, verdicts: Mapping[str, Eligibility]) -> dict:
    # A tool call as a model made it. Strict schemas hold its name and arguments to the tools'.
    if name == "check_eligibility":
        return check_eligibility(**arguments, verdicts=verdicts)
    return {"get_course": get_course, "find_plan": find_plan}[name](**arguments)
