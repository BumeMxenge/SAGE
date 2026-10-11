# Checks the catalogue and Finish setup: the lines she confirmed are saved, an unanswered set of plans
# is attached once however often she presses it, and anything the handbook doesn't know is refused
import pytest

from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.api import deps
from sage.services.rulebook import Rulebook
from sage.services.seed import load_seed
from tests.unit.api.accounts import QRTILV


@pytest.fixture
def setup(seed_file) -> dict:
    # Finish setup as the review screen sends it, with Mbali's seeded history
    lines = load_seed(seed_file, QRTILV).student.course_history
    return {
        "curriculum_code": "EB011EEE05",
        "lines": [line.model_dump(exclude={"student_id"}) for line in lines],
    }


def test_the_catalogue_lists_the_current_handbook(signed_in):
    catalogue = signed_in("qrtilv").get("/v1/catalogue").json()
    assert catalogue["year"] == 2026
    assert [row["code"] for row in catalogue["curricula"]] == ["EB011EEE05"]
    assert len(catalogue["courses"]) == 52
    assert catalogue["courses"][0].keys() == {"code", "name", "credits", "term"}
    assert len(catalogue["symbols"]) == 26


def test_staff_are_refused_the_student_endpoints(signed_in):
    response = signed_in("staff").get("/v1/catalogue")
    assert response.status_code == 403
    assert response.json()["code"] == "students_only"


def test_no_approved_year_means_the_rulebook_isnt_loaded(app, signed_in):
    empty = Rulebook(InMemoryRuleRepository())
    app.dependency_overrides[deps.rulebook] = lambda: empty
    response = signed_in("qrtilv").get("/v1/catalogue")
    assert response.status_code == 503
    assert response.json()["code"] == "rulebook_not_loaded"


def test_finish_setup_saves_her_lines_and_attaches_unanswered_plans(
    signed_in, stores, setup
):
    response = signed_in("qrtilv").post("/v1/onboarding/complete", json=setup)
    assert response.status_code == 200
    assert response.json()["onboarding_complete"] is True

    students = stores[1]
    profile = students.profile(QRTILV)
    assert (profile.curriculum_code, profile.intake_year) == ("EB011EEE05", 2023)
    assert len(students.get(QRTILV).course_history) == 34
    plans = students.current_plan_set(QRTILV)
    assert plans.plan_set.answers is None
    assert len(plans.plans) == 10
    assert not any(plan.hidden for plan in plans.plans)


def test_finish_setup_twice_leaves_one_plan_set(signed_in, stores, setup):
    client = signed_in("qrtilv")
    client.post("/v1/onboarding/complete", json=setup)
    first = stores[1].get(QRTILV)
    client.post("/v1/onboarding/complete", json=setup)
    assert stores[1].get(QRTILV) == first
    assert len(first.plan_sets) == 1


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


@pytest.mark.parametrize(
    ("edit", "code"),
    [
        (another_curriculum, "unknown_curriculum"),
        (an_unknown_result, "unknown_result"),
        (a_code_in_the_wrong_format, "invalid_request"),
        (a_line_twice, "invalid_request"),
        (no_lines, "invalid_request"),
        (an_extra_key, "invalid_request"),
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
