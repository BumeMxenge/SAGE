# Checks the rule trees' shapes: a tree that doesn't fit is refused, an any needs a child, a rule
# printed in another order is the same tree, and so is one grouped differently within its own kind
import pytest
from pydantic import TypeAdapter, ValidationError

from sage.domain.rules import AnyOf, CourseNeed, EntryRule

ENTRY_RULE = TypeAdapter(EntryRule)


@pytest.mark.parametrize(
    "tree",
    [
        {"courses": "EEE3091F", "need": "pass"},  # a misspelt key
        {"any": ["EEE3091F", "EEE3092F"]},  # codes where leaves should be
        {"course": "EEE3091F", "need": "dp"},  # a need outside the set
        {"course": "EEE3091F", "need": "pass", "refer": "Or"},  # an extra key
        {"course": "CSC2001F", "need": "mark"},  # a mark leaf without its mark
        {"course": "EEE3091F", "need": "pass", "min_mark": 50},  # a pass leaf with one
    ],
)
def test_a_malformed_tree_is_refused(tree):
    with pytest.raises(ValidationError):
        ENTRY_RULE.validate_python(tree)


def test_an_any_needs_one_child_at_least():
    # Both sides of the boundary: an empty any could never hold, and one child is a valid any
    leaf = {"course": "EEE3091F", "need": "pass"}
    assert ENTRY_RULE.validate_python({"any": [leaf]}) == AnyOf(
        any=(CourseNeed(course="EEE3091F", need="pass"),)
    )
    with pytest.raises(ValidationError):
        ENTRY_RULE.validate_python({"any": []})


def test_a_rule_printed_in_another_order_is_the_same_tree():
    # EEE4113F's "EEE3097S or EEE3098S or EEE3099S", PHY2010S's co-requisite "MAM2084F/S",
    # CSC2002S's "At least 45% for CSC2001F" and two curricula, none of them in sorted order
    printed = {
        "all": [
            {"student_in": ["EB011EEE05", "EB009EEE01"]},
            {"course": "CSC2001F", "need": "mark", "min_mark": 45},
            {
                "any": [
                    {"course": "MAM2084S", "need": "concurrent"},
                    {"course": "MAM2084F", "need": "concurrent"},
                ]
            },
            {
                "any": [
                    {"course": "EEE3099S", "need": "pass"},
                    {"course": "EEE3097S", "need": "pass"},
                    {"course": "EEE3098S", "need": "pass"},
                ]
            },
        ]
    }
    # Sorted by hand on each node's JSON text: "any" before "course" before "student_in", the two
    # anys by their first code, and the codes alphabetically. Only the mark leaf has a min_mark.
    expected = {
        "all": [
            {
                "any": [
                    {"course": "EEE3097S", "need": "pass"},
                    {"course": "EEE3098S", "need": "pass"},
                    {"course": "EEE3099S", "need": "pass"},
                ]
            },
            {
                "any": [
                    {"course": "MAM2084F", "need": "concurrent"},
                    {"course": "MAM2084S", "need": "concurrent"},
                ]
            },
            {"course": "CSC2001F", "need": "mark", "min_mark": 45},
            {"student_in": ["EB009EEE01", "EB011EEE05"]},
        ]
    }
    tree = ENTRY_RULE.validate_python(printed)
    assert ENTRY_RULE.dump_python(tree, mode="json") == expected


def leaf(code, need="pass"):
    return {"course": code, "need": need}


def test_an_all_inside_an_all_is_the_same_tree_as_one_all():
    # PHY2010S's requirement joined to its co-requisite "MAM2084F/S", as the ingest joins them: an
    # all holding an all. E2's prompt.md rule 10 says to join them, and a model may group either way.
    requirement = {
        "all": [
            {"any": [leaf("PHY1012F"), leaf("PHY1012S")]},
            {"any": [leaf("MAM2083F"), leaf("MAM2083S")]},
        ]
    }
    corequisite = {
        "any": [leaf("MAM2084F", "concurrent"), leaf("MAM2084S", "concurrent")]
    }
    joined = ENTRY_RULE.validate_python({"all": [requirement, corequisite]})
    flat = ENTRY_RULE.validate_python({"all": [*requirement["all"], corequisite]})
    assert joined == flat
    # Sorted by hand as above: the three anys by their first code, MAM2083F, MAM2084F, PHY1012F
    assert ENTRY_RULE.dump_python(joined, mode="json") == {
        "all": [
            {"any": [leaf("MAM2083F"), leaf("MAM2083S")]},
            {"any": [leaf("MAM2084F", "concurrent"), leaf("MAM2084S", "concurrent")]},
            {"any": [leaf("PHY1012F"), leaf("PHY1012S")]},
        ]
    }


def test_an_any_inside_an_any_joins_however_deep():
    nested = {
        "any": [
            leaf("EEE3097S"),
            {"any": [leaf("EEE3098S"), {"any": [leaf("EEE3099S")]}]},
        ]
    }
    assert ENTRY_RULE.dump_python(ENTRY_RULE.validate_python(nested), mode="json") == {
        "any": [leaf("EEE3097S"), leaf("EEE3098S"), leaf("EEE3099S")]
    }


def test_an_all_and_an_any_inside_each_other_stay_apart():
    # Joining only holds within a kind: "A and (B or C)" is not "A and B and C", nor is
    # "A or (B and C)" "A or B or C". Each node's children are only sorted, "all" and "any" before
    # "course" by their JSON text.
    b_or_c = {"any": [leaf("EEE3098S"), leaf("EEE3099S")]}
    b_and_c = {"all": [leaf("EEE3098S"), leaf("EEE3099S")]}
    for kind, inner in (("all", b_or_c), ("any", b_and_c)):
        tree = ENTRY_RULE.validate_python({kind: [leaf("EEE3097S"), inner]})
        assert ENTRY_RULE.dump_python(tree, mode="json") == {
            kind: [inner, leaf("EEE3097S")]
        }
