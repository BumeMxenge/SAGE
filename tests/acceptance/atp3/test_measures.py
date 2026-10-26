# Checks ATP-3's measures against hand calculations shown in each test. Nothing here reads a result
# or calls a model.
import pytest
from measures import allocation, cross_agreement, kappa, mode, pair_agrees, pass_k


@pytest.mark.parametrize(
    ("k", "expected"),
    [
        # Three prompts with 3, 2 and 0 of 3 tries right:
        # k = 1: (3/3 + 2/3 + 0/3) / 3 = 0.5556
        (1, (1 + 2 / 3 + 0) / 3),
        # k = 2: (C(3,2)/C(3,2) + C(2,2)/C(3,2) + 0) / 3 = (1 + 1/3) / 3 = 0.4444
        (2, (1 + 1 / 3) / 3),
        # k = 3: only the first prompt has all three right, so 1/3
        (3, 1 / 3),
    ],
)
def test_pass_k_is_the_chance_that_k_tries_all_succeed(k, expected):
    assert pass_k([3, 2, 0], 3, k) == pytest.approx(expected)


def test_one_success_in_three_gives_no_chance_that_two_tries_both_succeed():
    # C(1, 2) = 0: no two of its tries both succeeded
    assert pass_k([1], 3, 2) == 0


def test_kappa_counts_only_the_agreement_beyond_chance():
    # Ten replies: both say right 6 times and wrong twice, and differ once each way.
    # Observed 8/10 = 0.8. Each says right 7 times in 10, so chance is 0.7 x 0.7 + 0.3 x 0.3 = 0.58.
    # Kappa = (0.8 - 0.58) / (1 - 0.58) = 0.5238.
    pairs = (
        [("right", "right")] * 6
        + [("wrong", "wrong")] * 2
        + [("right", "wrong"), ("wrong", "right")]
    )
    assert kappa(pairs) == pytest.approx(0.22 / 0.42)


def test_kappa_has_no_value_when_chance_alone_always_agrees():
    assert kappa([("right", "right")] * 4) is None


def test_a_three_way_split_has_no_most_common_outcome_so_its_pair_disagrees():
    split = ["correct_answer", "wrong_safe", "over_referral"]
    assert mode(split) is None
    assert not pair_agrees(split, split)
    assert pair_agrees(
        ["correct_answer", "correct_answer", "wrong_safe"],
        ["correct_answer", "unsupported", "correct_answer"],
    )


def test_cross_agreement_counts_every_pair_of_tries():
    # Of the nine pairs, the two right tries of the first meet the one right try of the second, and
    # its wrong try meets the second's two wrong tries: 2 + 2 = 4 match
    assert cross_agreement(
        ["right", "right", "wrong"], ["right", "wrong", "wrong"]
    ) == (4, 9)


def test_the_sample_gives_every_stratum_its_floor_then_shares_the_rest_by_size():
    # 40 from strata of 100, 10 and 1. Floors: 2, 2 and the 1 there is, so 35 remain, shared over
    # 98 and 8 left: 32.36 and 2.64. Whole places give 32 and 2, and the one left over goes to the
    # larger remainder, 0.64, so 34, 5 and 1.
    assert allocation({"a": 100, "b": 10, "c": 1}, 40) == {"a": 34, "b": 5, "c": 1}
