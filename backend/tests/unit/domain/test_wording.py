# Checks rule trees read in plain words as a reviewer compares them with print: the example the review
# walk was specified with, every leaf, and brackets where an all sits inside another node or a list
# sits in the middle of an all. Trees are canonical, so children read in sorted order.
import pytest

from sage.domain.rules import (
    AllOf,
    AllOfGroup,
    AnyOf,
    ChooseFromGroup,
    CourseNeed,
    CreditsFromGroups,
    MinYearOfStudy,
    Refer,
    StudentIn,
    TotalCredits,
    YearRules,
)
from sage.domain.wording import in_words


def needs(code, need="pass", min_mark=None):
    return CourseNeed(course=code, need=need, min_mark=min_mark)


def either(*codes):
    return AnyOf(any=tuple(needs(code) for code in codes))


@pytest.mark.parametrize(
    ("rule", "words"),
    [
        # The walk's specified example, MEC2045S's requirement
        (
            AllOf(
                all=(
                    either("MEC1009F", "MEC1009S"),
                    either("MEC2023F", "MEC2023S", "MEC2047F", "MEC2047S"),
                )
            ),
            "MEC1009F or MEC1009S, and one of MEC2023F, MEC2023S, MEC2047F or MEC2047S",
        ),
        (needs("MAM1020F", "concurrent"), "MAM1020F taken alongside"),
        (needs("CSC2001F", "mark", 45), "at least 45% in CSC2001F"),
        (MinYearOfStudy(min_year_of_study=4), "year of study 4 or later"),
        (Refer(refer="or equivalent"), 'a person\'s judgement of "or equivalent"'),
        (None, "no requirement"),
        # Leaves alone in an all need no comma, but a part with a list of its own does
        (
            AllOf(all=(needs("CSC2001F"), needs("CSC2002S"), needs("CSC2004Z"))),
            "CSC2001F, CSC2002S and CSC2004Z",
        ),
        (
            AllOf(
                all=(
                    needs("EEE3091F"),
                    StudentIn(student_in=("EB809EEE01", "EB009EEE01")),
                )
            ),
            "EEE3091F, and a student on EB009EEE01 or EB809EEE01",
        ),
        # An all inside an any is bracketed, and so is one of three in the middle of an all
        (
            AnyOf(
                any=(
                    AllOf(all=(needs("MAM1004F"), needs("MAM1008S"))),
                    needs("MAM1000W"),
                )
            ),
            "(MAM1004F and MAM1008S) or MAM1000W",
        ),
        (
            AllOf(
                all=(
                    either("ECO1010F", "ECO1010S", "ECO1110F"),
                    Refer(refer="or later"),
                )
            ),
            '(one of ECO1010F, ECO1010S or ECO1110F), and a person\'s judgement of "or later"',
        ),
        # A curriculum's rule for a year of study
        (
            YearRules(
                all=(
                    AllOfGroup(all_of_group="EB022EEE02-y2-core"),
                    ChooseFromGroup(choose=1, from_group="EB022EEE02-y4-group-1"),
                    CreditsFromGroups(credits=8, from_groups=("complementary",)),
                    TotalCredits(total_credits=136),
                )
            ),
            (
                "every course in EB022EEE02-y2-core, 1 course from EB022EEE02-y4-group-1, "
                "at least 8 credits from complementary, and 136 credits in total"
            ),
        ),
    ],
)
def test_a_rule_reads_in_plain_words(rule, words):
    assert in_words(rule) == words
