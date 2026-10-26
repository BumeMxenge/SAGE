# Checks Explore Electives on Mbali's seeded set: hearting, which changes nothing the second time.
# Whether she can heart each offering is checked in test_service.py. Then, on Ziyela's, the plans
# each offering fits.
import pytest


def electives(student) -> dict[str, dict]:
    # Every offering on every card, by code, as the page would read them now
    tabs = student.get("/v1/electives").json()["tabs"]
    return {
        offering["code"]: offering
        for tab in tabs
        for card in tab["courses"]
        for offering in card["offerings"]
    }


def test_hearting_a_course_shows_on_its_card_and_can_be_repeated(mbali):
    # Greek IA, a language option, so it has a tab
    response = mbali.put("/v1/favourites/SLL1052F")
    assert (response.status_code, response.content) == (204, b"")
    assert electives(mbali)["SLL1052F"]["hearted"] is True
    assert mbali.put("/v1/favourites/SLL1052F").status_code == 204


def test_unhearting_a_course_clears_its_card_and_can_be_repeated(mbali):
    mbali.put("/v1/favourites/SLL1052F")
    assert electives(mbali)["SLL1052F"]["hearted"] is True
    response = mbali.delete("/v1/favourites/SLL1052F")
    assert (response.status_code, response.content) == (204, b"")
    assert electives(mbali)["SLL1052F"]["hearted"] is False
    assert mbali.delete("/v1/favourites/SLL1052F").status_code == 204


def test_an_offering_names_only_the_plans_whose_slots_list_it(ziyela):
    # The engine lists FAM2000F in the slots of her plans 3, 9 and 10 alone, and SLL1057F in those of
    # plans 1 and 6, which her answers hide
    plans = {plan["position"]: plan for plan in ziyela.get("/v1/plans").json()["plans"]}
    offered = electives(ziyela)
    assert offered["FAM2000F"]["plans"] == [plans[n]["id"] for n in (3, 9, 10)]
    assert offered["SLL1057F"]["plans"] == [plans[n]["id"] for n in (1, 6)]
    assert plans[1]["hidden"] and plans[6]["hidden"]


@pytest.mark.parametrize("verb", ["put", "delete"])
def test_a_course_outside_the_handbook_cant_be_hearted_or_unhearted(mbali, verb):
    response = mbali.request(verb, "/v1/favourites/ZZZ9999Z")
    assert (response.status_code, response.json()["code"]) == (404, "course_not_found")
