# Checks the scorer's arithmetic and its one form per meaning, with every expected value worked out
# by hand in a comment, never taken from what the code returned
import pytest

from score import mcnemar, normal, to_correct, upper_bound


def course(code: str, need: str = "pass") -> dict:
    return {"course": code, "need": need}


def test_trees_that_mean_the_same_rule_compare_equal():
    # The same any, written with its children in another order, an any nested in it, a lone course
    # wrapped in an all, a repeated child and the refer leaf worded differently
    label = {
        "any": [course("EEE2045F"), course("EEE2046F"), {"refer": "or equivalent"}]
    }
    draft = {
        "any": [
            {"refer": "or an equivalent course"},
            {"any": [course("EEE2046F"), {"all": [course("EEE2045F")]}]},
            course("EEE2046F"),
        ]
    }
    assert normal(draft) == normal(label)


@pytest.mark.parametrize(
    "draft",
    [
        # A co-requisite's need where a pass is printed
        {"all": [course("EEE2045F", "concurrent"), course("EEE2047S")]},
        # Either course where both are needed
        {"any": [course("EEE2045F"), course("EEE2047S")]},
        # One of the two courses dropped
        course("EEE2045F"),
    ],
)
def test_a_tree_that_means_another_rule_differs(draft):
    label = {"all": [course("EEE2045F"), course("EEE2047S")]}
    assert normal(draft) != normal(label)


@pytest.mark.parametrize(
    ("draft", "fixes"),
    [
        # EEE2047S is missing and EEE2046F is extra: one leaf each way, so 2
        ({"all": [course("EEE2045F"), course("EEE2046F")]}, 2),
        # The right leaves under any instead of all: none differ, but a wrong draft costs 1
        ({"any": [course("EEE2045F"), course("EEE2047S")]}, 1),
    ],
)
def test_the_leaves_to_correct_in_a_wrong_draft(draft, fixes):
    label = {"all": [course("EEE2045F"), course("EEE2047S")]}
    assert to_correct(normal(draft), normal(label)) == fixes


@pytest.mark.parametrize(
    ("stored", "bound"),
    [
        # One string: 1 - 0.05 = 0.95
        (1, 0.95),
        # 60 strings: ln 0.05 / 60 = -0.049929, e to that is 0.951297, and 1 - 0.951297 = 0.048703
        (60, 0.048703),
    ],
)
def test_the_upper_bound_when_nothing_is_wrong(stored, bound):
    assert upper_bound(stored) == pytest.approx(bound, abs=1e-6)


@pytest.mark.parametrize(
    ("b", "c", "p"),
    [
        # Twice the binomial tail with n = b + c and a half chance each way:
        # no split at all: 2 × 1 / 1 = 2, capped at 1
        (0, 0, 1.0),
        # 0 and 5: 2 × 1 / 32 = 0.0625, just above 0.05, so the models aren't separated
        (0, 5, 0.0625),
        # 0 and 6: 2 × 1 / 64 = 0.03125, just below 0.05
        (0, 6, 0.03125),
        # 1 and 6: 2 × (1 + 7) / 128 = 0.125
        (1, 6, 0.125),
    ],
)
def test_mcnemars_exact_test(b, c, p):
    assert mcnemar(b, c) == pytest.approx(p)
