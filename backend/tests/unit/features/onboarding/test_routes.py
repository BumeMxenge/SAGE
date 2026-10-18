# Checks the catalogue and Finish setup: the lines she confirmed are saved and plans attached, and
# anything the handbook doesn't know is refused before anything is written. That pressing it again
# makes no second set is checked in tests/unit/features/onboarding/test_service.py.
import pytest

from sage.shared.api import deps
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.rulebook import Rulebook
from sage.shared.seed import load_seed
from tests.unit.accounts import QRTILV


@pytest.fixture
def setup(seed_file) -> dict:
    # Finish setup as the review screen sends it, with Mbali's seeded history
    lines = load_seed(seed_file, QRTILV).course_history
    return {
        "curriculum_code": "EB011EEE05",
        "lines": [line.model_dump(exclude={"student_id"}) for line in lines],
    }


def test_the_catalogue_lists_the_current_handbook(
    signed_in, approved_2026, result_symbols
):
    catalogue = signed_in("qrtilv").get("/v1/catalogue").json()
    assert catalogue["year"] == 2026
    # The department's six curricula, printed on pp. 48, 50, 52, 54, 56 and 59, by code
    assert [row["code"] for row in catalogue["curricula"]] == [
        "EB009EEE01",
        "EB011EEE05",
        "EB022EEE02",
        "EB809EEE01",
        "EB811EEE05",
        "EB822EEE02",
    ]
    # Every course in the year, by code, and every result symbol
    assert [row["code"] for row in catalogue["courses"]] == sorted(
        row.code for row in approved_2026.courses
    )
    assert {row["symbol"] for row in catalogue["symbols"]} == {
        row.symbol for row in result_symbols
    }


def test_no_approved_year_means_the_rulebook_isnt_loaded(app, signed_in):
    empty = Rulebook(InMemoryRuleRepository())
    app.dependency_overrides[deps.rulebook] = lambda: empty
    response = signed_in("qrtilv").get("/v1/catalogue")
    assert response.status_code == 503
    assert response.json()["code"] == "rulebook_not_loaded"


def test_finish_setup_saves_her_lines_and_attaches_plans(signed_in, stores, setup):
    response = signed_in("qrtilv").post("/v1/onboarding/complete", json=setup)
    assert response.status_code == 200
    assert response.json()["onboarding_complete"] is True

    students = stores[1]
    profile = students.profile(QRTILV)
    # Her intake year is her record's first, 2023
    assert (profile.curriculum_code, profile.intake_year) == ("EB011EEE05", 2023)
    saved = students.get(QRTILV).course_history
    assert [line.model_dump(exclude={"student_id"}) for line in saved] == setup["lines"]
    assert students.current_plan_set(QRTILV) is not None


def another_curriculum(setup):
    setup["curriculum_code"] = "EB999XYZ99"


def an_unknown_result(setup):
    setup["lines"][0]["result"] = "ZZ"


def a_code_in_the_wrong_format(setup):
    setup["lines"][0]["course_code"] = "EEE 4113F"


def a_line_twice(setup):
    setup["lines"].append(dict(setup["lines"][0]))


def no_lines(setup):
    setup["lines"] = []


def an_extra_key(setup):
    setup["nickname"] = "Mbali"


def credits_too_large_to_store(setup):
    setup["lines"][0]["credits"] = 40000  # course_history.credits is a smallint


@pytest.mark.parametrize(
    ("edit", "code"),
    [
        (another_curriculum, "unknown_curriculum"),
        (an_unknown_result, "unknown_result"),
        (a_code_in_the_wrong_format, "invalid_request"),
        (a_line_twice, "invalid_request"),
        (no_lines, "invalid_request"),
        (an_extra_key, "invalid_request"),
        (credits_too_large_to_store, "invalid_request"),
    ],
)
def test_finish_setup_refuses_what_the_handbook_doesnt_know(
    signed_in, stores, setup, edit, code
):
    edit(setup)
    response = signed_in("qrtilv").post("/v1/onboarding/complete", json=setup)
    assert response.status_code == 422
    assert response.json()["code"] == code
    assert stores[1].profile(QRTILV) is None  # nothing written
