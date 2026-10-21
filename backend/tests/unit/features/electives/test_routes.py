# Checks Explore Electives on Mbali's seeded set: hearting, which changes nothing the second time.
# Whether she may take each course is checked in tests/unit/engine/test_eligibility.py. In the
# approved 2026 only the language options have a tab, as the other tabs wait for M3's categories.
import pytest

from tests.unit.accounts import MBALI


def electives(mbali) -> dict[str, dict]:
    # Every course on every tab, by code, as the page would read them now
    tabs = mbali.get("/v1/electives").json()["tabs"]
    return {course["code"]: course for tab in tabs for course in tab["courses"]}


def test_hearting_a_course_shows_on_its_card_and_can_be_repeated(mbali, stores):
    # Greek IA, a language option, so it has a tab
    response = mbali.put("/v1/favourites/SLL1052F")
    assert (response.status_code, response.content) == (204, b"")
    assert electives(mbali)["SLL1052F"]["favourite"] is True
    assert mbali.put("/v1/favourites/SLL1052F").status_code == 204
    hearted = [row.course_code for row in stores[1].get(MBALI).favourites]
    assert hearted.count("SLL1052F") == 1


def test_unhearting_a_course_clears_its_card_and_can_be_repeated(mbali):
    mbali.put("/v1/favourites/SLL1052F")
    assert electives(mbali)["SLL1052F"]["favourite"] is True
    response = mbali.delete("/v1/favourites/SLL1052F")
    assert (response.status_code, response.content) == (204, b"")
    assert electives(mbali)["SLL1052F"]["favourite"] is False
    assert mbali.delete("/v1/favourites/SLL1052F").status_code == 204


@pytest.mark.parametrize("verb", ["put", "delete"])
def test_a_course_outside_the_handbook_cant_be_hearted_or_unhearted(mbali, verb):
    response = mbali.request(verb, "/v1/favourites/ZZZ9999Z")
    assert (response.status_code, response.json()["code"]) == (404, "course_not_found")
