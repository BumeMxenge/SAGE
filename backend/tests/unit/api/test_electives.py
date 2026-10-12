# Checks Explore Electives on Mbali's seeded set: whether she may take each course, as the
# eligibility stand-in decides until the engine does, and hearting, which changes nothing the
# second time
import pytest

from sage.domain.students import CourseHistoryLine
from tests.unit.api.accounts import MBALI


def electives(mbali) -> dict[str, dict]:
    # Every course on every tab, by code, as the page would read them now
    tabs = mbali.get("/v1/electives").json()["tabs"]
    return {course["code"]: course for tab in tabs for course in tab["courses"]}


def record_microeconomics(stores, result: str, mark: int) -> None:
    # Adds a line for ECO1010S to her record, as her transcript would
    students = stores[1]
    state = students.get(MBALI)
    line = CourseHistoryLine(
        student_id=MBALI,
        academic_year=2025,
        term="sem2",
        course_code="ECO1010S",
        course_name="Microeconomics",
        credits=18,
        nqf_level=5,
        result=result,
        mark=mark,
    )
    students.replace(
        state.model_copy(update={"course_history": (*state.course_history, line)})
    )


@pytest.mark.stub("engine")
def test_an_eligible_course_has_no_reason(mbali):
    reasons = {
        course["eligibility"]["reason"]
        for course in electives(mbali).values()
        if course["eligibility"]["status"] == "eligible"
    }
    assert reasons == {None}


@pytest.mark.stub("engine")
def test_a_course_with_a_printed_refer_shows_its_text(mbali):
    assert electives(mbali)["BIO1004S"]["eligibility"] == {
        "status": "check",
        "reason": "A pass at 60% in NSC Life Sciences or Physical Sciences or by permission of the Head of Department.",
    }


@pytest.mark.stub("engine")
def test_a_course_that_counts_as_a_passed_one_is_not_eligible_either(mbali, stores):
    # The 2026 equivalences say ECO1010S counts as ECO1010F
    record_microeconomics(stores, result="1", mark=80)
    assert electives(mbali)["ECO1010F"]["eligibility"] == {
        "status": "not_eligible",
        "reason": "You've already passed ECO1010S.",
    }


@pytest.mark.stub("engine")
def test_a_failed_course_doesnt_count(mbali, stores):
    record_microeconomics(stores, result="F", mark=40)
    assert electives(mbali)["ECO1010S"]["eligibility"]["status"] == "check"


def test_hearting_a_course_shows_on_its_card_and_can_be_repeated(mbali, stores):
    response = mbali.put("/v1/favourites/ECO1007S")
    assert (response.status_code, response.content) == (204, b"")
    assert electives(mbali)["ECO1007S"]["favourite"] is True
    assert mbali.put("/v1/favourites/ECO1007S").status_code == 204
    hearted = [row.course_code for row in stores[1].get(MBALI).favourites]
    assert hearted.count("ECO1007S") == 1


def test_unhearting_a_course_clears_its_card_and_can_be_repeated(mbali):
    mbali.put("/v1/favourites/ECO1007S")
    assert electives(mbali)["ECO1007S"]["favourite"] is True
    response = mbali.delete("/v1/favourites/ECO1007S")
    assert (response.status_code, response.content) == (204, b"")
    assert electives(mbali)["ECO1007S"]["favourite"] is False
    assert mbali.delete("/v1/favourites/ECO1007S").status_code == 204


@pytest.mark.parametrize("verb", ["put", "delete"])
def test_a_course_outside_the_handbook_cant_be_hearted_or_unhearted(mbali, verb):
    response = mbali.request(verb, "/v1/favourites/ZZZ9999Z")
    assert (response.status_code, response.json()["code"]) == (404, "course_not_found")
