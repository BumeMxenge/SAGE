# Checks her course history: her years newest first, each with its year of study, credits, average
# and lines, and the cumulative average, all matching the planner prototype's figures
import pytest


@pytest.fixture
def history(signed_in) -> dict:
    return signed_in("mbali").get("/v1/history").json()


def test_her_years_come_newest_first_with_their_totals(history):
    years = [
        (
            year["academic_year"],
            year["year_of_study"],
            len(year["lines"]),
            year["credits"],
            year["average"],
        )
        for year in history["years"]
    ]
    assert years == [
        (2025, 3, 12, 146, 63.19),
        (2024, 2, 11, 144, 71.50),
        (2023, 1, 11, 148, 71.38),
    ]


def test_her_cumulative_average(history):
    assert history["cumulative_average"] == 68.69


def test_each_line_is_as_she_confirmed_it(history):
    (supplementary,) = [
        line for line in history["years"][1]["lines"] if line["code"] == "PHY2010S"
    ]
    assert supplementary == {
        "code": "PHY2010S",
        "name": "Electromagnetism for Engineers",
        "term": "sem2",
        "credits": 16,
        "nqf_level": 6,
        "result": "SP",
        "mark": None,
    }


def test_history_waits_for_onboarding(signed_in):
    response = signed_in("qrtilv").get("/v1/history")
    assert (response.status_code, response.json()["code"]) == (
        409,
        "onboarding_incomplete",
    )
