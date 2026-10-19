# Checks the average rule the history screen and the transcript check share: credit-weighted, SP as
# 50, lines without a mark left out, and rounded half up to two decimals
from decimal import Decimal

from sage.shared.base import Row
from sage.shared.students import average


class Line(Row):
    credits: int
    mark: int | None
    result: str


def test_marks_are_weighted_by_credits():
    lines = [
        Line(credits=8, mark=80, result="1"),
        Line(credits=24, mark=60, result="2-"),
    ]
    assert average(lines) == Decimal("65.00")


def test_a_supplementary_pass_counts_as_50_and_a_line_without_a_mark_is_left_out():
    lines = [
        Line(credits=16, mark=None, result="SP"),
        Line(credits=16, mark=70, result="2+"),
        Line(credits=0, mark=None, result="GIP"),
        Line(credits=16, mark=None, result="GIP"),
    ]
    assert average(lines) == Decimal("60.00")


def test_a_half_rounds_up():
    # 70.985 exactly, which rounding to even would make 70.98
    lines = [
        Line(credits=3, mark=70, result="2+"),
        Line(credits=197, mark=71, result="2+"),
    ]
    assert average(lines) == Decimal("70.99")


def test_nothing_to_average_is_none():
    assert average([Line(credits=16, mark=None, result="GIP")]) is None
    assert average([]) is None
