# Checks Explore Electives on Mbali's seeded set: the tabs and their courses, whether she may take
# each one, and hearting, which changes nothing the second time
from collections import Counter

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


def test_there_are_12_tabs_in_a_fixed_order(mbali):
    tabs = mbali.get("/v1/electives").json()["tabs"]
    assert [tab["key"] for tab in tabs] == [
        "arts",
        "business",
        "econ",
        "ethics",
        "history",
        "languages",
        "literature",
        "logic",
        "media",
        "religion",
        "science",
        "society",
    ]


def test_the_tabs_hold_41_courses_between_them(mbali):
    tabs = mbali.get("/v1/electives").json()["tabs"]
    counts = {tab["key"]: len(tab["courses"]) for tab in tabs}
    assert counts == {
        "arts": 3,
        "business": 2,
        "econ": 6,
        "ethics": 3,
        "history": 4,
        "languages": 4,
        "literature": 4,
        "logic": 4,
        "media": 2,
        "religion": 2,
        "science": 4,
        "society": 3,
    }
    assert sum(counts.values()) == 41


def test_every_course_has_the_fields_its_card_needs(mbali):
    for course in electives(mbali).values():
        assert set(course) == {
            "code",
            "name",
            "credits",
            "term",
            "summary",
            "convener",
            "favourite",
            "eligibility",
        }
        assert set(course["eligibility"]) == {"status", "reason"}


def test_20_courses_are_eligible_and_21_need_checking(mbali):
    statuses = Counter(
        course["eligibility"]["status"] for course in electives(mbali).values()
    )
    assert statuses == {"eligible": 20, "check": 21}  # so none is not_eligible


def test_an_eligible_course_has_no_reason(mbali):
    reasons = {
        course["eligibility"]["reason"]
        for course in electives(mbali).values()
        if course["eligibility"]["status"] == "eligible"
    }
    assert reasons == {None}


def test_a_course_with_a_printed_refer_shows_its_text(mbali):
    assert electives(mbali)["BIO1004S"]["eligibility"] == {
        "status": "check",
        "reason": "A pass at 60% in NSC Life Sciences or Physical Sciences or by permission of the Head of Department.",
    }


def test_a_course_she_passed_is_not_eligible(mbali, stores):
    record_microeconomics(stores, result="1", mark=80)
    assert electives(mbali)["ECO1010S"]["eligibility"] == {
        "status": "not_eligible",
        "reason": "You've already passed ECO1010S.",
    }


def test_a_course_that_counts_as_a_passed_one_is_not_eligible_either(mbali, stores):
    # The 2026 equivalences say ECO1010S counts as ECO1010F
    record_microeconomics(stores, result="1", mark=80)
    assert electives(mbali)["ECO1010F"]["eligibility"] == {
        "status": "not_eligible",
        "reason": "You've already passed ECO1010S.",
    }


def test_a_failed_course_doesnt_count(mbali, stores):
    record_microeconomics(stores, result="F", mark=40)
    assert electives(mbali)["ECO1010S"]["eligibility"]["status"] == "check"


def test_none_of_the_41_start_hearted(mbali):
    # Her 6 seeded hearts are fourth-year plan courses, which no tab lists
    hearts = {course["favourite"] for course in electives(mbali).values()}
    assert hearts == {False}


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


def test_staff_have_no_electives(signed_in):
    response = signed_in("staff").get("/v1/electives")
    assert (response.status_code, response.json()["code"]) == (403, "students_only")


def test_electives_wait_for_onboarding(signed_in):
    response = signed_in("qrtilv").get("/v1/electives")
    assert (response.status_code, response.json()["code"]) == (
        409,
        "onboarding_incomplete",
    )
