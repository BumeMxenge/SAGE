# ATP-3's three held-out students, each made ready as ask_advisor.py makes one for --seed: her record
# in the in-memory stores beside the approved 2026, her plans from the engine, as onboarding makes
# them, and, when she has more than five, the questionnaire answered "no preference", so every plan
# stays shown. Each turn then starts from a copy of that state in a store of its own, as turns run
# four at a time and the in-memory store isn't safe across threads.
import json
from pathlib import Path

from show_plans import ACCOUNT, SYMBOLS

from sage.engine.generator import ClingoPlanGenerator
from sage.features.onboarding import service as onboarding
from sage.features.plans import service as plans
from sage.features.questionnaire import service as questionnaire
from sage.ingestion.ingest import approved_snapshot
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.memory.students import InMemoryStudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import ResultSymbol
from sage.shared.seed import load_seed, seed
from sage.shared.students import Plan, StudentState

HERE = Path(__file__).resolve().parent
YEAR = 2026  # the year SAGE plans
# Each student by the code prompts.csv gives her
FILES = {
    "R1": HERE / "students" / "signals1-failed.json",
    "R4": HERE / "students" / "embedded1-failed.json",
    "R5": HERE / "students" / "aspect-final-supp.json",
}
NO_PREFERENCE = {"course": "no_preference", "week": "no_preference"}


def stores() -> tuple[InMemoryRuleRepository, Rulebook]:
    # The approved 2026 and the real result symbols, as ask_advisor.py loads them
    symbols = tuple(
        ResultSymbol.model_validate(row)
        for row in json.loads(SYMBOLS.read_text(encoding="utf-8"))
    )
    rules = InMemoryRuleRepository(symbols)
    rules.replace_year(approved_snapshot(YEAR).rules)
    return rules, Rulebook(rules)


def prepared(
    code: str, rules: InMemoryRuleRepository, rulebook: Rulebook
) -> StudentState:
    state = load_seed(FILES[code], ACCOUNT)
    if state.plan_sets:
        raise SystemExit(
            f"{FILES[code].name} holds plans of its own, where the engine should make them"
        )
    students = InMemoryStudentRepository()
    seed(rules, students, state)
    onboarding.complete(
        ACCOUNT,
        state.student.curriculum_code,
        state.course_history,
        students,
        rulebook,
        ClingoPlanGenerator(),
    )
    if plans.questionnaire_needed(students.current_plan_set(ACCOUNT)):
        questionnaire.answer(
            students, rulebook, students.get(ACCOUNT).student, NO_PREFERENCE
        )
    return students.get(ACCOUNT)


def store(state: StudentState) -> InMemoryStudentRepository:
    # A store of her own for one turn, holding a copy of her state
    students = InMemoryStudentRepository()
    students.replace(state)
    return students


def short_ids(state: StudentState) -> dict[str, Plan]:
    # Her plans by the short ids the advisor gives them, V01 upwards, from their positions
    return {f"V{plan.position:02d}": plan for plan in state.plans}
