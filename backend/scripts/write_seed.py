# Writes data/synthetic/ziyela.json, the made-up student whose plans have a complementary slot. Ziyela
# Ontwe is in her fourth year of Mechatronics (4-year), on track as show_plans.py makes a student,
# except that she hasn't taken the complementary studies course her third year asks for, so each of
# her plans leaves an 18-credit slot. Her plans come from the engine through onboarding, as the app
# makes them, and she answers the questionnaire as Mbali did, which hides the plans without EEE4119F.
# tests/unit/shared/test_seed.py fails once the engine would build her plans differently: run this
# again then. From backend/: uv run python -m scripts.write_seed
import json
from typing import Any

from sage.engine.generator import ClingoPlanGenerator
from sage.features.onboarding import service as onboarding
from sage.features.questionnaire import service as questionnaire
from sage.ingestion.ingest import approved_snapshot
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.memory.students import InMemoryStudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import COMPLEMENTARY, ResultSymbol
from sage.shared.seed import SEED_FILE
from sage.shared.students import StudentState
from scripts.show_plans import ACCOUNT, SYMBOLS, on_track

FILE = SEED_FILE.with_name("ziyela.json")
EMAIL = "ntwziy999@myuct.ac.za"  # made up, ending in 999 as every invented student number does
CURRICULUM = "EB011EEE05"
YEAR = 4  # her year of study in 2026
ANSWERS = {"course": "EEE4119F", "week": "no_preference"}  # Mbali's
# Word Power fits every plan, Writing & Editing in the Media three that her answers keep, and Ancient
# Egypt only two that they hide
FAVOURITES = ("SLL1002S", "FAM2000F", "SLL1057F")
README = [
    (
        "Ziyela's seed for 2026: a made-up student, with no real person's data. "
        "scripts/write_seed.py writes this file, so run it again rather than editing it."
    ),
    (
        "She is in her fourth year of Mechatronics (4-year) and has passed every course of her "
        "first three years except a complementary studies course, so each of her plans leaves an "
        "18-credit complementary slot."
    ),
    (
        "Her plans, their courses and their reasons are the engine's, as onboarding makes them. "
        "Her questionnaire answers are Mbali's, which hide the plans without EEE4119F."
    ),
    (
        "As in mbali.json, each key is a table, rows carry no uuids or student_id, and rows that "
        "point at other rows use local keys. Her reasons cite no passage, so approving a year "
        "again never breaks a link."
    ),
    (
        "fake_account holds her made-up email, which the tests' fake sign-in uses. sage seed "
        "never writes it: a real account brings its own email."
    ),
]


def build() -> StudentState:
    # Her record, plans, hearts and answers, as the app would store them
    symbols = tuple(
        ResultSymbol.model_validate(row)
        for row in json.loads(SYMBOLS.read_text(encoding="utf-8"))
    )
    rules, students = InMemoryRuleRepository(symbols), InMemoryStudentRepository()
    rules.replace_year(approved_snapshot(2026).rules)
    rulebook = Rulebook(rules)
    year = rulebook.current()
    _, history = on_track(year, CURRICULUM, YEAR)
    complementary = {
        member.course_code
        for member in year.course_group_members
        if member.group_key == COMPLEMENTARY
    }
    history = [line for line in history if line.course_code not in complementary]
    profile = onboarding.complete(
        ACCOUNT, CURRICULUM, history, students, rulebook, ClingoPlanGenerator()
    )
    for code in FAVOURITES:
        students.add_favourite(ACCOUNT, code)
    questionnaire.answer(students, rulebook, profile, ANSWERS)
    return students.get(ACCOUNT)


def seed_file(state: StudentState) -> dict[str, Any]:
    # Her rows in mbali.json's shape: local keys in place of ids, and no student_id
    (plan_set,) = state.plan_sets
    set_key = f"{plan_set.period}-v{plan_set.version}"
    plan_key = {plan.id: f"P{plan.position:02d}" for plan in state.plans}
    return {
        "_readme": README,
        "fake_account": {"email": EMAIL},
        "students": [
            state.student.model_dump(
                include={"curriculum_code", "intake_year", "onboarding_complete"}
            )
        ],
        "course_history": [
            line.model_dump(mode="json", exclude={"student_id"})
            for line in state.course_history
        ],
        "favourites": [{"course_code": row.course_code} for row in state.favourites],
        "plan_sets": [
            {
                "key": set_key,
                **plan_set.model_dump(
                    include={"period", "version", "complete", "answers"}
                ),
            }
        ],
        "plans": [
            {
                "key": plan_key[plan.id],
                "plan_set": set_key,
                **plan.model_dump(
                    include={"position", "name", "combination", "hidden"}
                ),
            }
            for plan in state.plans
        ],
        "plan_courses": [
            {
                "plan": plan_key[row.plan_id],
                **row.model_dump(include={"course_code", "handbook_year", "choices"}),
            }
            for row in state.plan_courses
        ],
        "plan_reasons": [
            {
                "key": f"r{number}",
                "plan_set": set_key,
                "plan": plan_key.get(row.plan_id),
                **row.model_dump(include={"course_code", "kind", "message", "details"}),
                "passage_id": None,
            }
            for number, row in enumerate(state.plan_reasons, start=1)
        ],
        "chats": [],
        "messages": [],
        "message_citations": [],
    }


def main() -> None:
    FILE.write_text(json.dumps(seed_file(build()), indent=2) + "\n", encoding="utf-8")
    print(FILE)


if __name__ == "__main__":
    main()
